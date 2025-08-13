import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.event_task import EventTask, EventTaskStatus
from models.ai_algorithm import AIService
from task_queue_manager import task_queue_manager
from event_task_executor import EventTaskExecutor

logger = logging.getLogger(__name__)

class RabbitMQEventTaskManager:
    """基于RabbitMQ的事件任务管理器"""
    
    def __init__(self):
        self.running = False
        self.executor = EventTaskExecutor()
        self.check_interval = 30  # 检查间隔30秒
        self.task_timeout = 1800  # 30分钟超时
        
    async def start(self):
        """启动事件任务管理器"""
        if self.running:
            return
            
        self.running = True
        logger.info("Starting RabbitMQ Event Task Manager")
        
        # 确保RabbitMQ连接
        if not task_queue_manager.connection:
            await task_queue_manager.connect()
        
        # 启动事件任务消费者
        await self._start_consumers()
        
        # 启动监控循环
        asyncio.create_task(self._monitor_loop())
        
        logger.info("RabbitMQ Event Task Manager started")
    
    async def stop(self):
        """停止事件任务管理器"""
        self.running = False
        logger.info("RabbitMQ Event Task Manager stopped")
    
    async def _start_consumers(self):
        """启动事件任务消费者"""
        # 启动事件任务消费者
        await task_queue_manager.consume_tasks(
            'event', self._process_event_task
        )
        
        logger.info("Event task consumers started")
    
    async def _monitor_loop(self):
        """监控循环 - 检查卡住的任务和需要重试的任务"""
        while self.running:
            try:
                await self._recover_stuck_tasks()
                await self._check_retry_tasks()
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Error in monitor loop: {e}")
                await asyncio.sleep(5)
    
    async def create_task_from_service(self, service_id: int, event_data: Dict[str, Any]) -> Optional[int]:
        """从AI服务创建事件任务并发布到队列"""
        async for db in get_db():
            try:
                # 获取AI服务信息
                service = await db.get(AIService, service_id)
                if not service or not service.enabled:
                    logger.warning(f"AI service {service_id} not found or disabled")
                    return None
                
                # 检查是否有相同服务的RUNNING任务，如果有则重置
                result = await db.execute(
                    select(EventTask).where(
                        and_(
                            EventTask.service_id == service_id,
                            EventTask.status == EventTaskStatus.RUNNING
                        )
                    )
                )
                running_tasks = result.scalars().all()
                
                for running_task in running_tasks:
                    # 检查任务是否真的卡住了（没有worker心跳或心跳超时）
                    if (not running_task.assigned_worker or 
                        not running_task.worker_heartbeat or
                        (datetime.now(timezone.utc) - running_task.worker_heartbeat).total_seconds() > 300):
                        
                        logger.warning(f"Resetting stuck RUNNING task {running_task.id} for service {service_id}")
                        running_task.status = EventTaskStatus.PENDING
                        running_task.assigned_worker = None
                        running_task.worker_heartbeat = None
                        running_task.error_message = "Reset due to stuck state"
                
                # 创建新的事件任务
                event_task = EventTask(
                    service_id=service_id,
                    event_data=event_data,
                    status=EventTaskStatus.PENDING,
                    created_at=datetime.now(timezone.utc),
                    priority=event_data.get('priority', 5)
                )
                
                db.add(event_task)
                await db.flush()  # 获取任务ID
                
                # 发布任务到RabbitMQ队列
                task_data = {
                    'task_id': event_task.id,
                    'service_id': service_id,
                    'event_data': event_data,
                    'created_at': event_task.created_at.isoformat(),
                    'priority': event_task.priority
                }
                
                success = await task_queue_manager.publish_task(
                    'event', task_data, priority=event_task.priority
                )
                
                if success:
                    await db.commit()
                    logger.info(f"Created and published event task {event_task.id} for service {service_id}")
                    return event_task.id
                else:
                    await db.rollback()
                    logger.error(f"Failed to publish event task for service {service_id}")
                    return None
                    
            except Exception as e:
                logger.error(f"Error creating event task for service {service_id}: {e}")
                await db.rollback()
                return None
            finally:
                await db.close()
    
    async def _process_event_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理事件任务"""
        task_id = task_data.get('task_id')
        logger.info(f"Processing event task {task_id}")
        
        async for db in get_db():
            try:
                # 获取任务
                task = await db.get(EventTask, task_id)
                if not task:
                    logger.error(f"Event task {task_id} not found")
                    return {'success': False, 'error': 'Task not found'}
                
                # 更新任务状态为RUNNING
                task.status = EventTaskStatus.RUNNING
                task.started_at = datetime.now(timezone.utc)
                task.assigned_worker = f"rabbitmq-worker-{task_id}"  # 临时worker标识
                task.worker_heartbeat = datetime.now(timezone.utc)
                await db.commit()
                
                # 执行任务
                result = await self.executor.execute_task(task_id)
                
                # 更新任务状态
                if result.get('success', False):
                    task.status = EventTaskStatus.COMPLETED
                    task.result = result.get('result')
                else:
                    task.status = EventTaskStatus.FAILED
                    task.error_message = result.get('error', 'Unknown error')
                    
                    # 检查是否需要重试
                    if task.retry_count < 3:  # 最多重试3次
                        task.retry_count += 1
                        task.status = EventTaskStatus.PENDING
                        task.next_retry_at = datetime.now(timezone.utc) + timedelta(minutes=5 * task.retry_count)
                        logger.info(f"Event task {task_id} will be retried (attempt {task.retry_count})")
                
                task.completed_at = datetime.now(timezone.utc)
                await db.commit()
                
                logger.info(f"Event task {task_id} completed with status: {task.status}")
                return result
                
            except Exception as e:
                logger.error(f"Error processing event task {task_id}: {e}")
                
                # 更新任务状态为失败
                try:
                    task = await db.get(EventTask, task_id)
                    if task:
                        task.status = EventTaskStatus.FAILED
                        task.error_message = str(e)
                        task.completed_at = datetime.now(timezone.utc)
                        
                        # 检查是否需要重试
                        if task.retry_count < 3:
                            task.retry_count += 1
                            task.status = EventTaskStatus.PENDING
                            task.next_retry_at = datetime.now(timezone.utc) + timedelta(minutes=5 * task.retry_count)
                        
                        await db.commit()
                except Exception as update_error:
                    logger.error(f"Error updating event task status: {update_error}")
                
                return {'success': False, 'error': str(e)}
            finally:
                await db.close()
    
    async def _recover_stuck_tasks(self):
        """恢复卡住的事件任务"""
        async for db in get_db():
            try:
                current_time = datetime.now(timezone.utc)
                timeout_time = current_time - timedelta(seconds=self.task_timeout)
                
                # 查找运行时间过长的任务
                result = await db.execute(
                    select(EventTask)
                    .where(
                        and_(
                            EventTask.status == EventTaskStatus.RUNNING,
                            EventTask.started_at < timeout_time
                        )
                    )
                )
                
                stuck_tasks = result.scalars().all()
                
                for task in stuck_tasks:
                    logger.warning(f"Recovering stuck event task {task.id}")
                    
                    # 检查是否需要重试
                    if task.retry_count < 3:
                        task.retry_count += 1
                        task.status = EventTaskStatus.PENDING
                        task.next_retry_at = current_time + timedelta(minutes=5 * task.retry_count)
                        task.error_message = f"Task timeout - retry attempt {task.retry_count}"
                        
                        # 重新发布到队列
                        task_data = {
                            'task_id': task.id,
                            'service_id': task.service_id,
                            'event_data': task.event_data,
                            'retry_attempt': task.retry_count
                        }
                        
                        await task_queue_manager.publish_task(
                            'event', task_data, priority=task.priority + 2  # 提高重试任务优先级
                        )
                    else:
                        task.status = EventTaskStatus.FAILED
                        task.error_message = "Task timeout - max retries exceeded"
                        task.completed_at = current_time
                    
                    task.assigned_worker = None
                    task.worker_heartbeat = None
                
                if stuck_tasks:
                    await db.commit()
                    logger.info(f"Recovered {len(stuck_tasks)} stuck event tasks")
                    
            except Exception as e:
                logger.error(f"Error recovering stuck event tasks: {e}")
            finally:
                await db.close()
    
    async def _check_retry_tasks(self):
        """检查需要重试的任务"""
        async for db in get_db():
            try:
                current_time = datetime.now(timezone.utc)
                
                # 查找需要重试的任务
                result = await db.execute(
                    select(EventTask)
                    .where(
                        and_(
                            EventTask.status == EventTaskStatus.PENDING,
                            EventTask.next_retry_at.isnot(None),
                            EventTask.next_retry_at <= current_time
                        )
                    )
                )
                
                retry_tasks = result.scalars().all()
                
                for task in retry_tasks:
                    logger.info(f"Retrying event task {task.id} (attempt {task.retry_count})")
                    
                    # 重新发布到队列
                    task_data = {
                        'task_id': task.id,
                        'service_id': task.service_id,
                        'event_data': task.event_data,
                        'retry_attempt': task.retry_count
                    }
                    
                    success = await task_queue_manager.publish_task(
                        'event', task_data, priority=task.priority + 2
                    )
                    
                    if success:
                        task.next_retry_at = None  # 清除重试时间
                    else:
                        logger.error(f"Failed to republish retry task {task.id}")
                
                if retry_tasks:
                    await db.commit()
                    logger.info(f"Republished {len(retry_tasks)} retry event tasks")
                    
            except Exception as e:
                logger.error(f"Error checking retry tasks: {e}")
            finally:
                await db.close()
    
    async def schedule_immediate_task(self, service_id: int, event_data: Dict[str, Any], priority: int = 8) -> Optional[int]:
        """立即调度事件任务"""
        event_data['priority'] = priority
        return await self.create_task_from_service(service_id, event_data)
    
    async def get_queue_status(self) -> Dict[str, Any]:
        """获取事件任务队列状态"""
        try:
            queue_info = await task_queue_manager.get_queue_info('event_tasks')
            
            # 获取数据库中的任务统计
            async for db in get_db():
                try:
                    # 统计各状态的任务数量
                    pending_count = await db.scalar(
                        select(EventTask).where(EventTask.status == EventTaskStatus.PENDING).count()
                    )
                    running_count = await db.scalar(
                        select(EventTask).where(EventTask.status == EventTaskStatus.RUNNING).count()
                    )
                    completed_count = await db.scalar(
                        select(EventTask).where(EventTask.status == EventTaskStatus.COMPLETED).count()
                    )
                    failed_count = await db.scalar(
                        select(EventTask).where(EventTask.status == EventTaskStatus.FAILED).count()
                    )
                    
                    return {
                        'queue_info': queue_info,
                        'task_counts': {
                            'pending': pending_count,
                            'running': running_count,
                            'completed': completed_count,
                            'failed': failed_count
                        },
                        'manager_running': self.running
                    }
                finally:
                    await db.close()
                    
        except Exception as e:
            logger.error(f"Error getting event queue status: {e}")
            return {'error': str(e)}
    
    async def cancel_task(self, task_id: int) -> bool:
        """取消事件任务"""
        async for db in get_db():
            try:
                task = await db.get(EventTask, task_id)
                if not task:
                    return False
                
                if task.status in [EventTaskStatus.PENDING, EventTaskStatus.RUNNING]:
                    task.status = EventTaskStatus.FAILED
                    task.error_message = "Task cancelled by user"
                    task.completed_at = datetime.now(timezone.utc)
                    await db.commit()
                    
                    logger.info(f"Cancelled event task {task_id}")
                    return True
                
                return False
                
            except Exception as e:
                logger.error(f"Error cancelling event task {task_id}: {e}")
                return False
            finally:
                await db.close()

# 全局事件任务管理器实例
rabbitmq_event_task_manager = RabbitMQEventTaskManager()