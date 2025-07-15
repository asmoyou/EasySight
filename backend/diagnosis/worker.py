import asyncio
import logging
import json
import time
from typing import Dict, Any, Optional
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import threading

from diagnosis.executor import diagnosis_executor
from database import get_db

logger = logging.getLogger(__name__)

class DiagnosisWorker:
    """诊断任务Worker"""
    
    def __init__(self, worker_id: str, max_concurrent_tasks: int = 3):
        self.worker_id = worker_id
        self.max_concurrent_tasks = max_concurrent_tasks
        self.running = False
        self.current_tasks = {}
        self.task_semaphore = asyncio.Semaphore(max_concurrent_tasks)
        self.executor = ThreadPoolExecutor(max_workers=max_concurrent_tasks)
        self.stats = {
            'tasks_completed': 0,
            'tasks_failed': 0,
            'total_processing_time': 0,
            'start_time': None
        }
        
    async def start(self):
        """启动Worker"""
        if self.running:
            return
            
        self.running = True
        self.stats['start_time'] = datetime.utcnow()
        logger.info(f"诊断Worker {self.worker_id} 启动")
        
        # 启动任务监听循环
        asyncio.create_task(self._task_listener())
        
    async def stop(self):
        """停止Worker"""
        self.running = False
        
        # 等待当前任务完成
        while self.current_tasks:
            await asyncio.sleep(1)
            
        # 关闭线程池
        self.executor.shutdown(wait=True)
        
        logger.info(f"诊断Worker {self.worker_id} 停止")
        
    async def _task_listener(self):
        """任务监听循环"""
        while self.running:
            try:
                # 这里可以从消息队列中获取任务
                # 目前使用简单的轮询方式
                await asyncio.sleep(5)
                
            except Exception as e:
                logger.error(f"Worker {self.worker_id} 任务监听错误: {str(e)}")
                await asyncio.sleep(5)
                
    async def execute_task(self, task_id: int) -> Dict[str, Any]:
        """执行诊断任务"""
        if not self.running:
            return {"error": "Worker未运行"}
            
        # 检查并发限制
        if len(self.current_tasks) >= self.max_concurrent_tasks:
            return {"error": "Worker任务队列已满"}
            
        async with self.task_semaphore:
            task_start_time = time.time()
            self.current_tasks[task_id] = {
                'start_time': datetime.utcnow(),
                'status': 'running'
            }
            
            try:
                logger.info(f"Worker {self.worker_id} 开始执行任务 {task_id}")
                
                # 执行任务
                async for db in get_db():
                    result = await diagnosis_executor.execute_task(task_id, db)
                    break
                    
                # 更新统计信息
                processing_time = time.time() - task_start_time
                self.stats['total_processing_time'] += processing_time
                
                if result.get('success'):
                    self.stats['tasks_completed'] += 1
                    self.current_tasks[task_id]['status'] = 'completed'
                else:
                    self.stats['tasks_failed'] += 1
                    self.current_tasks[task_id]['status'] = 'failed'
                    
                logger.info(f"Worker {self.worker_id} 完成任务 {task_id}, 耗时: {processing_time:.2f}s")
                
                return result
                
            except Exception as e:
                logger.error(f"Worker {self.worker_id} 执行任务 {task_id} 失败: {str(e)}")
                self.stats['tasks_failed'] += 1
                self.current_tasks[task_id]['status'] = 'failed'
                return {"error": str(e)}
                
            finally:
                # 清理任务记录
                self.current_tasks.pop(task_id, None)
                
    def get_status(self) -> Dict[str, Any]:
        """获取Worker状态"""
        uptime = None
        if self.stats['start_time']:
            uptime = (datetime.utcnow() - self.stats['start_time']).total_seconds()
            
        avg_processing_time = 0
        if self.stats['tasks_completed'] > 0:
            avg_processing_time = self.stats['total_processing_time'] / self.stats['tasks_completed']
            
        return {
            'worker_id': self.worker_id,
            'running': self.running,
            'current_tasks': len(self.current_tasks),
            'max_concurrent_tasks': self.max_concurrent_tasks,
            'available_slots': self.max_concurrent_tasks - len(self.current_tasks),
            'stats': {
                'tasks_completed': self.stats['tasks_completed'],
                'tasks_failed': self.stats['tasks_failed'],
                'uptime_seconds': uptime,
                'avg_processing_time': avg_processing_time
            },
            'current_task_details': {
                task_id: {
                    'start_time': task_info['start_time'].isoformat(),
                    'status': task_info['status'],
                    'duration': (datetime.utcnow() - task_info['start_time']).total_seconds()
                }
                for task_id, task_info in self.current_tasks.items()
            }
        }

class WorkerPool:
    """Worker池管理器"""
    
    def __init__(self, pool_size: int = 3):
        self.pool_size = pool_size
        self.workers: Dict[str, DiagnosisWorker] = {}
        self.running = False
        self.task_queue = asyncio.Queue()
        self.round_robin_index = 0
        
    async def start(self):
        """启动Worker池"""
        if self.running:
            return
            
        self.running = True
        
        # 创建并启动Workers
        for i in range(self.pool_size):
            worker_id = f"worker-{i+1}"
            worker = DiagnosisWorker(worker_id)
            await worker.start()
            self.workers[worker_id] = worker
            
        # 启动任务分发器
        asyncio.create_task(self._task_dispatcher())
        
        logger.info(f"Worker池启动，包含 {self.pool_size} 个Worker")
        
    async def stop(self):
        """停止Worker池"""
        self.running = False
        
        # 停止所有Workers
        for worker in self.workers.values():
            await worker.stop()
            
        self.workers.clear()
        logger.info("Worker池停止")
        
    async def _task_dispatcher(self):
        """任务分发器"""
        while self.running:
            try:
                # 从队列中获取任务
                task_id = await asyncio.wait_for(self.task_queue.get(), timeout=1.0)
                
                # 选择可用的Worker
                worker = self._select_worker()
                if worker:
                    # 异步执行任务
                    asyncio.create_task(worker.execute_task(task_id))
                else:
                    # 没有可用Worker，重新放回队列
                    await self.task_queue.put(task_id)
                    await asyncio.sleep(1)
                    
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"任务分发器错误: {str(e)}")
                await asyncio.sleep(1)
                
    def _select_worker(self) -> Optional[DiagnosisWorker]:
        """选择可用的Worker（轮询策略）"""
        if not self.workers:
            return None
            
        worker_list = list(self.workers.values())
        
        # 轮询选择
        for _ in range(len(worker_list)):
            worker = worker_list[self.round_robin_index % len(worker_list)]
            self.round_robin_index += 1
            
            # 检查Worker是否有可用槽位
            if len(worker.current_tasks) < worker.max_concurrent_tasks:
                return worker
                
        return None
        
    async def submit_task(self, task_id: int) -> bool:
        """提交任务到队列"""
        if not self.running:
            return False
            
        try:
            await self.task_queue.put(task_id)
            return True
        except Exception as e:
            logger.error(f"提交任务 {task_id} 失败: {str(e)}")
            return False
            
    def get_pool_status(self) -> Dict[str, Any]:
        """获取Worker池状态"""
        worker_statuses = {}
        total_tasks = 0
        total_completed = 0
        total_failed = 0
        
        for worker_id, worker in self.workers.items():
            status = worker.get_status()
            worker_statuses[worker_id] = status
            total_tasks += len(worker.current_tasks)
            total_completed += status['stats']['tasks_completed']
            total_failed += status['stats']['tasks_failed']
            
        return {
            'pool_size': self.pool_size,
            'running': self.running,
            'queue_size': self.task_queue.qsize(),
            'total_current_tasks': total_tasks,
            'total_completed_tasks': total_completed,
            'total_failed_tasks': total_failed,
            'workers': worker_statuses
        }

class DistributedWorkerNode:
    """分布式Worker节点"""
    
    def __init__(self, node_id: str, worker_pool_size: int = 3):
        self.node_id = node_id
        self.worker_pool = WorkerPool(worker_pool_size)
        self.running = False
        self.heartbeat_interval = 30
        
    async def start(self):
        """启动分布式Worker节点"""
        if self.running:
            return
            
        self.running = True
        
        # 启动Worker池
        await self.worker_pool.start()
        
        # 启动心跳
        asyncio.create_task(self._heartbeat_loop())
        
        logger.info(f"分布式Worker节点 {self.node_id} 启动")
        
    async def stop(self):
        """停止分布式Worker节点"""
        self.running = False
        
        # 停止Worker池
        await self.worker_pool.stop()
        
        logger.info(f"分布式Worker节点 {self.node_id} 停止")
        
    async def _heartbeat_loop(self):
        """心跳循环"""
        while self.running:
            try:
                # 发送心跳到调度中心
                await self._send_heartbeat()
                await asyncio.sleep(self.heartbeat_interval)
            except Exception as e:
                logger.error(f"心跳发送失败: {str(e)}")
                await asyncio.sleep(self.heartbeat_interval)
                
    async def _send_heartbeat(self):
        """发送心跳"""
        # 这里可以实现向调度中心发送心跳的逻辑
        # 例如通过HTTP API或消息队列
        heartbeat_data = {
            'node_id': self.node_id,
            'timestamp': datetime.utcnow().isoformat(),
            'status': self.get_node_status()
        }
        
        # 发送心跳数据
        logger.debug(f"发送心跳: {heartbeat_data}")
        
    def get_node_status(self) -> Dict[str, Any]:
        """获取节点状态"""
        return {
            'node_id': self.node_id,
            'running': self.running,
            'worker_pool': self.worker_pool.get_pool_status()
        }
        
    async def execute_task(self, task_id: int) -> bool:
        """执行任务"""
        return await self.worker_pool.submit_task(task_id)

# 全局Worker池实例
worker_pool = WorkerPool()

# 启动函数
async def start_worker_pool(pool_size: int = 3):
    """启动Worker池"""
    global worker_pool
    worker_pool = WorkerPool(pool_size)
    await worker_pool.start()
    
async def stop_worker_pool():
    """停止Worker池"""
    global worker_pool
    if worker_pool:
        await worker_pool.stop()