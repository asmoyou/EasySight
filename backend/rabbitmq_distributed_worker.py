import asyncio
import logging
import json
import aiohttp
import time
import socket
import uuid
import psutil
import sys
import os
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from contextlib import asynccontextmanager 
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent))

from diagnosis.executor import DiagnosisExecutor
from event_task_executor import EventTaskExecutor
from task_queue_manager import TaskQueueManager
from database import get_db
from models.diagnosis import TaskStatus
from models.event_task import EventTask, EventTaskStatus
from worker_config import WorkerConfig

logger = logging.getLogger(__name__)

class RabbitMQDistributedWorker:
    """基于RabbitMQ的分布式Worker"""
    
    def __init__(self, worker_id: Optional[str] = None, config: Optional[WorkerConfig] = None):
        self.worker_id = worker_id or f"worker-{socket.gethostname()}-{uuid.uuid4().hex[:8]}"
        self.config = config or WorkerConfig()
        
        # 任务执行器
        self.diagnosis_executor = DiagnosisExecutor()
        self.event_executor = EventTaskExecutor()
        
        # RabbitMQ管理器
        self.task_queue_manager = TaskQueueManager()
        
        # Worker状态
        self.running = False
        self.registered = False
        self.current_tasks: Dict[str, asyncio.Task] = {}
        self.max_concurrent_tasks = self.config.max_concurrent_tasks
        
        # 统计信息
        self.stats = {
            'tasks_completed': 0,
            'tasks_failed': 0,
            'start_time': None,
            'last_heartbeat': None
        }
        
        # 主服务连接信息
        self.main_service_url = f"http://{self.config.master_host}:{self.config.master_port}"
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def start(self):
        """启动Worker"""
        if self.running:
            return
            
        self.running = True
        self.stats['start_time'] = datetime.now(timezone.utc)
        
        logger.info(f"Starting RabbitMQ Distributed Worker: {self.worker_id}")
        
        # 创建HTTP会话
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30)
        )
        
        try:
            # 连接RabbitMQ
            await self.task_queue_manager.connect()
            
            # 注册到主服务
            await self._register_worker()
            
            # 启动任务消费者
            await self._start_consumers()
            
            # 启动心跳发送
            asyncio.create_task(self._heartbeat_loop())
            
            logger.info(f"Worker {self.worker_id} started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start worker: {e}")
            await self.stop()
            raise
    
    async def stop(self):
        """停止Worker"""
        self.running = False
        
        logger.info(f"Stopping worker {self.worker_id}")
        
        # 等待当前任务完成
        if self.current_tasks:
            logger.info(f"Waiting for {len(self.current_tasks)} tasks to complete")
            await asyncio.gather(*self.current_tasks.values(), return_exceptions=True)
        
        # 注销Worker（在关闭会话之前）
        if self.registered and self.session and not self.session.closed:
            await self._unregister_worker()
        
        # 关闭连接
        if self.task_queue_manager:
            await self.task_queue_manager.close()
        
        if self.session and not self.session.closed:
            await self.session.close()
        
        logger.info(f"Worker {self.worker_id} stopped")
    
    async def _register_worker(self):
        """注册Worker到主服务"""
        try:
            worker_info = {
                'worker_id': self.worker_id,
                'host': socket.gethostname(),
                'port': 8001,  # Worker端口
                'max_concurrent_tasks': self.max_concurrent_tasks,
                'capabilities': ['diagnosis', 'event', 'ai_service']
            }
            
            async with self.session.post(
                f"{self.main_service_url}/api/v1/diagnosis/worker/register",
                json=worker_info
            ) as response:
                if response.status == 200:
                    self.registered = True
                    logger.info(f"✅ Worker {self.worker_id} registered successfully")
                else:
                    response_text = await response.text()
                    logger.error(f"❌ Failed to register worker: {response.status}, response: {response_text}")
                    
        except Exception as e:
            logger.error(f"Error registering worker: {e}")
    
    async def _unregister_worker(self):
        """注销Worker"""
        try:
            logger.info(f"🔄 Attempting to unregister worker {self.worker_id}")
            async with self.session.post(
                f"{self.main_service_url}/api/v1/diagnosis/worker/unregister",
                params={'worker_id': self.worker_id}
            ) as response:
                response_text = await response.text()
                if response.status == 200:
                    logger.info(f"✅ Worker {self.worker_id} unregistered successfully")
                else:
                    logger.error(f"❌ Failed to unregister worker: {response.status}, response: {response_text}")
                    
        except Exception as e:
            logger.error(f"❌ Error unregistering worker: {e}")
    
    async def _start_consumers(self):
        """启动任务消费者"""
        # 启动诊断任务消费者
        await self.task_queue_manager.consume_tasks(
            'diagnosis', self._process_diagnosis_task
        )
        
        # 启动事件任务消费者
        await self.task_queue_manager.consume_tasks(
            'event', self._process_event_task
        )
        
        # 启动AI服务任务消费者
        await self.task_queue_manager.consume_tasks(
            'ai_service', self._process_ai_service_task
        )
        
        logger.info("Task consumers started")
    
    async def _process_diagnosis_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理诊断任务"""
        task_id = task_data.get('task_id')
        
        # 检查并发限制
        if len(self.current_tasks) >= self.max_concurrent_tasks:
            logger.warning(f"Worker {self.worker_id} at max capacity, rejecting task {task_id}")
            # 不抛出异常，而是返回拒绝结果，让消息被确认但不处理
            return {'success': False, 'error': 'Worker at max capacity', 'rejected': True}
        
        logger.info(f"Worker {self.worker_id} processing diagnosis task {task_id}")
        
        try:
            # 创建任务协程
            task_coro = self._execute_diagnosis_task(task_id, task_data)
            task_future = asyncio.create_task(task_coro)
            
            # 添加到当前任务列表
            self.current_tasks[str(task_id)] = task_future
            
            # 等待任务完成
            result = await task_future
            
            # 更新统计
            if result.get('success', False):
                self.stats['tasks_completed'] += 1
            else:
                self.stats['tasks_failed'] += 1
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing diagnosis task {task_id}: {e}")
            self.stats['tasks_failed'] += 1
            return {'success': False, 'error': str(e)}
        finally:
            # 从当前任务列表中移除
            self.current_tasks.pop(str(task_id), None)
    
    async def _execute_diagnosis_task(self, task_id: int, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行诊断任务"""
        try:
            # 更新任务状态为RUNNING
            await self._update_task_status(task_id, 'diagnosis', TaskStatus.RUNNING)
            
            # 获取数据库会话并执行任务
            async for db in get_db():
                try:
                    result = await self.diagnosis_executor.execute_task(task_id, db)
                    break
                except Exception as e:
                    await db.rollback()
                    raise e
                finally:
                    await db.close()
            
            # 更新任务状态
            if result.get('success', False):
                await self._update_task_status(task_id, 'diagnosis', TaskStatus.COMPLETED, result)
            else:
                await self._update_task_status(task_id, 'diagnosis', TaskStatus.FAILED, result)
            
            logger.info(f"Diagnosis task {task_id} completed by worker {self.worker_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error executing diagnosis task {task_id}: {e}")
            await self._update_task_status(task_id, 'diagnosis', TaskStatus.FAILED, {'error': str(e)})
            return {'success': False, 'error': str(e)}
    
    async def _process_event_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理事件任务"""
        task_id = task_data.get('task_id')
        
        # 检查并发限制
        if len(self.current_tasks) >= self.max_concurrent_tasks:
            logger.warning(f"Worker {self.worker_id} at max capacity, rejecting event task {task_id}")
            # 不抛出异常，而是返回拒绝结果，让消息被确认但不处理
            return {'success': False, 'error': 'Worker at max capacity', 'rejected': True}
        
        logger.info(f"Worker {self.worker_id} processing event task {task_id}")
        
        try:
            # 创建任务协程
            task_coro = self._execute_event_task(task_id, task_data)
            task_future = asyncio.create_task(task_coro)
            
            # 添加到当前任务列表
            self.current_tasks[f"event_{task_id}"] = task_future
            
            # 等待任务完成
            result = await task_future
            
            # 更新统计
            if result.get('success', False):
                self.stats['tasks_completed'] += 1
            else:
                self.stats['tasks_failed'] += 1
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing event task {task_id}: {e}")
            self.stats['tasks_failed'] += 1
            return {'success': False, 'error': str(e)}
        finally:
            # 从当前任务列表中移除
            self.current_tasks.pop(f"event_{task_id}", None)
    
    async def _execute_event_task(self, task_id: int, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行事件任务"""
        try:
            # 更新任务状态为RUNNING
            await self._update_event_task_status(task_id, EventTaskStatus.RUNNING)
            
            # 执行任务
            result = await self.event_executor.execute_task(task_id)
            
            # 更新任务状态
            if result.get('success', False):
                await self._update_event_task_status(task_id, EventTaskStatus.COMPLETED, result)
            else:
                await self._update_event_task_status(task_id, EventTaskStatus.FAILED, result)
            
            logger.info(f"Event task {task_id} completed by worker {self.worker_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error executing event task {task_id}: {e}")
            await self._update_event_task_status(task_id, EventTaskStatus.FAILED, {'error': str(e)})
            return {'success': False, 'error': str(e)}
    
    async def _process_ai_service_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理AI服务任务"""
        # AI服务任务处理逻辑
        task_id = task_data.get('task_id')
        logger.info(f"Worker {self.worker_id} processing AI service task {task_id}")
        
        # 这里可以添加AI服务任务的具体处理逻辑
        # 暂时返回成功
        return {'success': True, 'message': 'AI service task processed'}
    
    async def _update_task_status(self, task_id: int, task_type: str, status: TaskStatus, result: Optional[Dict] = None):
        """更新任务状态"""
        try:
            update_data = {
                'task_id': task_id,
                'status': status.value,
                'worker_id': self.worker_id,
                'updated_at': datetime.now(timezone.utc).isoformat()
            }
            
            if result:
                update_data['result'] = result
            
            async with self.session.post(
                f"{self.main_service_url}/api/v1/diagnosis/tasks/{task_id}/status",
                json=update_data
            ) as response:
                if response.status != 200:
                    logger.error(f"Failed to update task status: {response.status}")
                    
        except Exception as e:
            logger.error(f"Error updating task status: {e}")
    
    async def _update_event_task_status(self, task_id: int, status: EventTaskStatus, result: Optional[Dict] = None):
        """更新事件任务状态"""
        try:
            update_data = {
                'task_id': task_id,
                'status': status.value,
                'worker_id': self.worker_id,
                'updated_at': datetime.now(timezone.utc).isoformat()
            }
            
            if result:
                update_data['result'] = result
            
            async with self.session.post(
                f"{self.main_service_url}/api/v1/event-tasks/{task_id}/status",
                json=update_data
            ) as response:
                if response.status != 200:
                    logger.error(f"Failed to update event task status: {response.status}")
                    
        except Exception as e:
            logger.error(f"Error updating event task status: {e}")
    
    async def _heartbeat_loop(self):
        """心跳循环"""
        logger.info(f"🔄 Starting heartbeat loop for worker {self.worker_id}")
        while self.running:
            try:
                logger.info(f"💓 Sending heartbeat for worker {self.worker_id}")
                await self._send_heartbeat()
                logger.info(f"⏰ Waiting {self.config.heartbeat_interval} seconds for next heartbeat")
                await asyncio.sleep(self.config.heartbeat_interval)
            except Exception as e:
                logger.error(f"❌ Error in heartbeat loop: {e}")
                await asyncio.sleep(5)
    
    async def _send_heartbeat(self):
        """发送心跳"""
        try:
            # 获取系统信息
            cpu_percent = psutil.cpu_percent()
            memory = psutil.virtual_memory()
            
            # 准备stats数据，确保datetime对象被序列化
            stats_data = self.stats.copy()
            if stats_data.get('start_time'):
                stats_data['start_time'] = stats_data['start_time'].isoformat()
            if stats_data.get('last_heartbeat'):
                stats_data['last_heartbeat'] = stats_data['last_heartbeat'].isoformat()
                
            # 完整的心跳数据（用于RabbitMQ）
            full_heartbeat_data = {
                'worker_id': self.worker_id,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'status': 'running' if self.running else 'stopped',
                'current_tasks': len(self.current_tasks),
                'max_tasks': self.max_concurrent_tasks,
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'stats': stats_data
            }
            
            # 简化的心跳数据（用于HTTP API）
            api_heartbeat_data = {
                'worker_id': self.worker_id,
                'current_tasks': len(self.current_tasks),
                'status': 'online' if self.running else 'offline'
            }
            
            # 发送到RabbitMQ心跳队列
            await self.task_queue_manager.publish_heartbeat(self.worker_id, full_heartbeat_data)
            
            # 同时发送到主服务（兼容性）
            async with self.session.post(
                f"{self.main_service_url}/api/v1/diagnosis/worker/heartbeat",
                json=api_heartbeat_data
            ) as response:
                if response.status == 200:
                    self.stats['last_heartbeat'] = datetime.now(timezone.utc)
                    logger.info(f"✅ Heartbeat sent successfully for worker {self.worker_id}")
                elif response.status == 404:
                    # Worker未注册，尝试重新注册
                    logger.warning("Worker not registered, attempting to re-register")
                    self.registered = False
                    await self._register_worker()
                else:
                    logger.error(f"Heartbeat failed with status: {response.status}")
                    
        except Exception as e:
            logger.error(f"Error sending heartbeat: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """获取Worker状态"""
        return {
            'worker_id': self.worker_id,
            'running': self.running,
            'registered': self.registered,
            'current_tasks': len(self.current_tasks),
            'max_tasks': self.max_concurrent_tasks,
            'stats': self.stats
        }

async def main():
    """主函数"""
    import signal
    
    # 创建Worker
    worker = RabbitMQDistributedWorker()
    
    # 信号处理
    shutdown_event = asyncio.Event()
    
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, shutting down...")
        shutdown_event.set()
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # 启动Worker
        await worker.start()
        
        # 保持运行，直到收到停止信号
        while worker.running and not shutdown_event.is_set():
            try:
                await asyncio.wait_for(shutdown_event.wait(), timeout=1.0)
                break
            except asyncio.TimeoutError:
                continue
            
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    finally:
        await worker.stop()

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    asyncio.run(main())