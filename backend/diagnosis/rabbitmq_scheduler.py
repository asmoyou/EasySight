import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.diagnosis import DiagnosisTask, TaskStatus
from models.ai_algorithm import AIService
from task_queue_manager import task_queue_manager
from diagnosis.executor import DiagnosisExecutor
from croniter import croniter

logger = logging.getLogger(__name__)

class RabbitMQTaskScheduler:
    """基于RabbitMQ的任务调度器"""
    
    def __init__(self):
        self.running = False
        self.executor = DiagnosisExecutor()
        self.check_interval = 30  # 检查间隔缩短到30秒
        self.task_timeout = 1800  # 30分钟超时
        
    async def start(self):
        """启动调度器"""
        if self.running:
            return
            
        self.running = True
        logger.info("Starting RabbitMQ Task Scheduler")
        
        # 连接RabbitMQ
        await task_queue_manager.connect()
        
        # 启动任务消费者
        await self._start_consumers()
        
        # 启动调度循环
        asyncio.create_task(self._schedule_loop())
        
        logger.info("RabbitMQ Task Scheduler started")
    
    async def stop(self):
        """停止调度器"""
        self.running = False
        await task_queue_manager.close()
        logger.info("RabbitMQ Task Scheduler stopped")
    
    async def _start_consumers(self):
        """启动任务消费者"""
        # 启动诊断任务消费者
        await task_queue_manager.consume_tasks(
            'diagnosis', self._process_diagnosis_task
        )
        
        logger.info("Task consumers started")
    
    async def _schedule_loop(self):
        """主调度循环 - 负责检查需要调度的任务并发布到队列"""
        while self.running:
            try:
                await self._check_and_schedule_tasks()
                await self._recover_stuck_tasks()
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Error in schedule loop: {e}")
                await asyncio.sleep(5)
    
    async def _check_and_schedule_tasks(self):
        """检查并调度需要执行的任务"""
        async for db in get_db():
            try:
                # 查询需要执行的任务
                current_time = datetime.now(timezone.utc)
                
                # 查询启用的、未在运行的任务
                result = await db.execute(
                    select(DiagnosisTask)
                    .where(
                        and_(
                            DiagnosisTask.enabled == True,
                            DiagnosisTask.status != TaskStatus.RUNNING,
                            or_(
                                DiagnosisTask.next_run_time <= current_time,
                                DiagnosisTask.next_run_time.is_(None)
                            )
                        )
                    )
                )
                
                tasks = result.scalars().all()
                
                for task in tasks:
                    if await self._should_execute_task(task, current_time):
                        await self._schedule_task_execution(task, db)
                        
            except Exception as e:
                logger.error(f"Error checking tasks: {e}")
            finally:
                await db.close()
    
    async def _should_execute_task(self, task: DiagnosisTask, current_time: datetime) -> bool:
        """判断任务是否应该执行"""
        # 检查任务是否已在运行
        if task.status == TaskStatus.RUNNING:
            return False
        
        # 如果没有cron表达式，只执行一次
        if not task.cron_expression:
            return task.status == TaskStatus.PENDING
        
        # 检查cron表达式
        try:
            cron = croniter(task.cron_expression, current_time)
            
            # 如果从未运行过，或者到了下次运行时间
            if not task.last_run_time:
                return True
                
            # 计算下次应该运行的时间
            next_time = cron.get_next(datetime)
            if task.next_run_time and current_time >= task.next_run_time:
                return True
                
        except Exception as e:
            logger.error(f"Invalid cron expression for task {task.id}: {e}")
            
        return False
    
    async def _schedule_task_execution(self, task: DiagnosisTask, db: AsyncSession):
        """调度任务执行 - 发布到RabbitMQ队列"""
        try:
            # 更新任务状态为PENDING（如果不是的话）
            if task.status != TaskStatus.PENDING:
                task.status = TaskStatus.PENDING
                await db.commit()
            
            # 计算任务优先级
            priority = self._calculate_task_priority(task)
            
            # 准备任务数据
            task_data = {
                'task_id': task.id,
                'task_type': 'diagnosis',
                'algorithm_id': task.algorithm_id,
                'camera_id': task.camera_id,
                'parameters': task.parameters or {},
                'scheduled_at': datetime.now(timezone.utc).isoformat()
            }
            
            # 发布任务到RabbitMQ队列
            success = await task_queue_manager.publish_task(
                'diagnosis', task_data, priority=priority
            )
            
            if success:
                # 更新下次运行时间
                if task.cron_expression:
                    try:
                        cron = croniter(task.cron_expression, datetime.now(timezone.utc))
                        task.next_run_time = cron.get_next(datetime)
                    except Exception as e:
                        logger.error(f"Error calculating next run time: {e}")
                
                await db.commit()
                logger.info(f"Scheduled task {task.id} for execution")
            else:
                logger.error(f"Failed to schedule task {task.id}")
                
        except Exception as e:
            logger.error(f"Error scheduling task {task.id}: {e}")
            await db.rollback()
    
    def _calculate_task_priority(self, task: DiagnosisTask) -> int:
        """计算任务优先级"""
        # 基础优先级
        priority = 5
        
        # 如果任务延迟了，提高优先级
        if task.next_run_time and task.next_run_time < datetime.now(timezone.utc):
            delay_minutes = (datetime.now(timezone.utc) - task.next_run_time).total_seconds() / 60
            if delay_minutes > 60:  # 延迟超过1小时
                priority = 9
            elif delay_minutes > 30:  # 延迟超过30分钟
                priority = 7
            elif delay_minutes > 10:  # 延迟超过10分钟
                priority = 6
        
        return min(priority, 10)  # 最高优先级为10
    
    async def _process_diagnosis_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理诊断任务"""
        task_id = task_data.get('task_id')
        logger.info(f"Processing diagnosis task {task_id}")
        
        async for db in get_db():
            try:
                # 获取任务
                task = await db.get(DiagnosisTask, task_id)
                if not task:
                    logger.error(f"Task {task_id} not found")
                    return {'success': False, 'error': 'Task not found'}
                
                # 更新任务状态为RUNNING
                task.status = TaskStatus.RUNNING
                task.started_at = datetime.now(timezone.utc)
                task.last_run_time = task.started_at
                await db.commit()
                
                # 执行任务
                result = await self.executor.execute_task(task_id)
                
                # 更新任务状态
                if result.get('success', False):
                    task.status = TaskStatus.COMPLETED
                    task.result = result.get('result')
                else:
                    task.status = TaskStatus.FAILED
                    task.error_message = result.get('error', 'Unknown error')
                
                task.completed_at = datetime.now(timezone.utc)
                await db.commit()
                
                logger.info(f"Task {task_id} completed with status: {task.status}")
                return result
                
            except Exception as e:
                logger.error(f"Error processing task {task_id}: {e}")
                
                # 更新任务状态为失败
                try:
                    task = await db.get(DiagnosisTask, task_id)
                    if task:
                        task.status = TaskStatus.FAILED
                        task.error_message = str(e)
                        task.completed_at = datetime.now(timezone.utc)
                        await db.commit()
                except Exception as update_error:
                    logger.error(f"Error updating task status: {update_error}")
                
                return {'success': False, 'error': str(e)}
            finally:
                await db.close()
    
    async def _recover_stuck_tasks(self):
        """恢复卡住的任务"""
        async for db in get_db():
            try:
                current_time = datetime.now(timezone.utc)
                timeout_time = current_time - timedelta(seconds=self.task_timeout)
                
                # 查找运行时间过长的任务
                result = await db.execute(
                    select(DiagnosisTask)
                    .where(
                        and_(
                            DiagnosisTask.status == TaskStatus.RUNNING,
                            DiagnosisTask.started_at < timeout_time
                        )
                    )
                )
                
                stuck_tasks = result.scalars().all()
                
                for task in stuck_tasks:
                    logger.warning(f"Recovering stuck task {task.id}")
                    task.status = TaskStatus.FAILED
                    task.error_message = "Task timeout - recovered by scheduler"
                    task.completed_at = current_time
                    
                    # 如果是周期性任务，重新调度
                    if task.cron_expression:
                        try:
                            cron = croniter(task.cron_expression, current_time)
                            task.next_run_time = cron.get_next(datetime)
                        except Exception as e:
                            logger.error(f"Error calculating next run time for recovered task: {e}")
                
                if stuck_tasks:
                    await db.commit()
                    logger.info(f"Recovered {len(stuck_tasks)} stuck tasks")
                    
            except Exception as e:
                logger.error(f"Error recovering stuck tasks: {e}")
            finally:
                await db.close()
    
    async def schedule_immediate_task(self, task_id: int, priority: int = 8) -> bool:
        """立即调度任务执行"""
        async for db in get_db():
            try:
                task = await db.get(DiagnosisTask, task_id)
                if not task:
                    logger.error(f"Task {task_id} not found")
                    return False
                
                # 准备任务数据
                task_data = {
                    'task_id': task.id,
                    'task_type': 'diagnosis',
                    'camera_ids': task.camera_ids or [],
                    'diagnosis_types': task.diagnosis_types or [],
                    'diagnosis_config': task.diagnosis_config or {},
                    'threshold_config': task.threshold_config or {},
                    'scheduled_at': datetime.now(timezone.utc).isoformat(),
                    'immediate': True
                }
                
                # 发布到队列
                success = await task_queue_manager.publish_task(
                    'diagnosis', task_data, priority=priority
                )
                
                if success:
                    task.status = TaskStatus.PENDING
                    await db.commit()
                    logger.info(f"Immediately scheduled task {task_id}")
                
                return success
                
            except Exception as e:
                logger.error(f"Error scheduling immediate task {task_id}: {e}")
                return False
            finally:
                await db.close()
    
    async def get_queue_status(self) -> Dict[str, Any]:
        """获取队列状态"""
        try:
            diagnosis_info = await task_queue_manager.get_queue_info('diagnosis_tasks')
            event_info = await task_queue_manager.get_queue_info('event_tasks')
            ai_service_info = await task_queue_manager.get_queue_info('ai_service_tasks')
            
            return {
                'diagnosis_queue': diagnosis_info,
                'event_queue': event_info,
                'ai_service_queue': ai_service_info,
                'scheduler_running': self.running
            }
        except Exception as e:
            logger.error(f"Error getting queue status: {e}")
            return {}

# 全局调度器实例
rabbitmq_scheduler = RabbitMQTaskScheduler()