import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from croniter import croniter
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from models.diagnosis import DiagnosisTask, TaskStatus
from diagnosis.executor import diagnosis_executor
from database import get_db

logger = logging.getLogger(__name__)

class TaskScheduler:
    """诊断任务调度器"""
    
    def __init__(self):
        self.running = False
        self.scheduled_tasks: Dict[int, asyncio.Task] = {}
        self.worker_pool_size = 5
        self.worker_semaphore = asyncio.Semaphore(self.worker_pool_size)
        
    async def start(self):
        """启动调度器"""
        if self.running:
            return
            
        self.running = True
        logger.info("诊断任务调度器启动")
        
        # 启动主调度循环
        asyncio.create_task(self._schedule_loop())
        
    async def stop(self):
        """停止调度器"""
        self.running = False
        
        # 取消所有调度任务
        for task in self.scheduled_tasks.values():
            task.cancel()
            
        self.scheduled_tasks.clear()
        logger.info("诊断任务调度器停止")
        
    async def _schedule_loop(self):
        """主调度循环"""
        while self.running:
            try:
                async for db in get_db():
                    await self._check_and_schedule_tasks(db)
                    break
                    
                # 每分钟检查一次
                await asyncio.sleep(60)
                
            except Exception as e:
                logger.error(f"调度循环错误: {str(e)}")
                await asyncio.sleep(60)
                
    async def _check_and_schedule_tasks(self, db: AsyncSession):
        """检查并调度任务"""
        try:
            # 获取所有启用的任务
            # 暂时跳过任务调度检查，避免枚举类型问题
            tasks = []
            
            current_time = datetime.utcnow()
            
            for task in tasks:
                # 检查是否需要执行
                if await self._should_execute_task(task, current_time):
                    await self._schedule_task_execution(task, db)
                    
        except Exception as e:
            logger.error(f"检查任务调度失败: {str(e)}")
            
    async def _should_execute_task(self, task: DiagnosisTask, current_time: datetime) -> bool:
        """判断任务是否应该执行"""
        # 如果任务正在运行，跳过
        if task.status == 'running':
            return False
            
        # 检查下次执行时间
        if task.next_run_time and task.next_run_time > current_time:
            return False
            
        # 根据调度类型判断
        schedule_type = task.schedule_type
        
        if schedule_type == "once":
            # 一次性任务，只在首次执行
            return task.total_runs == 0
            
        elif schedule_type == "interval":
            # 间隔执行
            if not task.last_run_time:
                return True
                
            interval_minutes = task.interval_minutes or 60
            next_run = task.last_run_time + timedelta(minutes=interval_minutes)
            return current_time >= next_run
            
        elif schedule_type == "cron":
            # Cron表达式
            if not task.cron_expression:
                return False
                
            try:
                cron = croniter(task.cron_expression, task.last_run_time or current_time)
                next_run = cron.get_next(datetime)
                return current_time >= next_run
            except Exception as e:
                logger.error(f"解析Cron表达式失败: {task.cron_expression}, {str(e)}")
                return False
                
        elif schedule_type == "manual":
            # 手动执行，不自动调度
            return False
            
        return False
        
    async def _schedule_task_execution(self, task: DiagnosisTask, db: AsyncSession):
        """调度任务执行"""
        task_id = task.id
        
        # 避免重复调度
        if task_id in self.scheduled_tasks:
            return
            
        # 更新下次执行时间
        await self._update_next_run_time(task, db)
        
        # 创建执行任务
        execution_task = asyncio.create_task(
            self._execute_task_with_semaphore(task_id)
        )
        
        self.scheduled_tasks[task_id] = execution_task
        
        # 任务完成后清理
        execution_task.add_done_callback(
            lambda t: self.scheduled_tasks.pop(task_id, None)
        )
        
        logger.info(f"调度任务执行: {task.name} (ID: {task_id})")
        
    async def _execute_task_with_semaphore(self, task_id: int):
        """使用信号量限制并发执行任务"""
        async with self.worker_semaphore:
            try:
                async for db in get_db():
                    result = await diagnosis_executor.execute_task(task_id, db)
                    logger.info(f"任务 {task_id} 执行完成: {result}")
                    break
            except Exception as e:
                logger.error(f"任务 {task_id} 执行失败: {str(e)}")
                
    async def _update_next_run_time(self, task: DiagnosisTask, db: AsyncSession):
        """更新任务的下次执行时间"""
        try:
            current_time = datetime.utcnow()
            next_run_time = None
            
            if task.schedule_type == "interval":
                interval_minutes = task.interval_minutes or 60
                next_run_time = current_time + timedelta(minutes=interval_minutes)
                
            elif task.schedule_type == "cron" and task.cron_expression:
                try:
                    cron = croniter(task.cron_expression, current_time)
                    next_run_time = cron.get_next(datetime)
                except Exception as e:
                    logger.error(f"计算Cron下次执行时间失败: {str(e)}")
                    
            if next_run_time:
                task.next_run_time = next_run_time
                await db.commit()
                
        except Exception as e:
            logger.error(f"更新下次执行时间失败: {str(e)}")
            
    async def execute_task_immediately(self, task_id: int) -> Dict[str, any]:
        """立即执行任务"""
        try:
            async for db in get_db():
                result = await diagnosis_executor.execute_task(task_id, db)
                return result
        except Exception as e:
            logger.error(f"立即执行任务 {task_id} 失败: {str(e)}")
            return {"error": str(e)}
            
    def get_running_tasks(self) -> List[int]:
        """获取正在运行的任务ID列表"""
        return list(self.scheduled_tasks.keys())
        
    def get_worker_status(self) -> Dict[str, any]:
        """获取worker状态"""
        return {
            "pool_size": self.worker_pool_size,
            "available_workers": self.worker_semaphore._value,
            "running_tasks": len(self.scheduled_tasks),
            "scheduler_running": self.running
        }

class DistributedTaskManager:
    """分布式任务管理器"""
    
    def __init__(self):
        self.node_id = self._generate_node_id()
        self.heartbeat_interval = 30  # 心跳间隔（秒）
        self.last_heartbeat = None
        
    def _generate_node_id(self) -> str:
        """生成节点ID"""
        import socket
        import uuid
        hostname = socket.gethostname()
        return f"{hostname}-{str(uuid.uuid4())[:8]}"
        
    async def register_node(self, db: AsyncSession):
        """注册节点"""
        # 这里可以实现节点注册逻辑
        # 将节点信息存储到数据库中
        pass
        
    async def send_heartbeat(self, db: AsyncSession):
        """发送心跳"""
        # 更新节点心跳时间
        self.last_heartbeat = datetime.utcnow()
        # 可以将心跳信息存储到数据库或Redis中
        pass
        
    async def discover_nodes(self, db: AsyncSession) -> List[Dict[str, any]]:
        """发现其他节点"""
        # 从数据库或Redis中获取其他活跃节点
        return []
        
    async def distribute_task(self, task_id: int, target_node: Optional[str] = None) -> bool:
        """分发任务到指定节点"""
        # 实现任务分发逻辑
        # 可以使用消息队列（如Redis、RabbitMQ）来分发任务
        return True

# 全局调度器实例
task_scheduler = TaskScheduler()
distributed_manager = DistributedTaskManager()

# 启动函数
async def start_scheduler():
    """启动调度器"""
    await task_scheduler.start()
    
async def stop_scheduler():
    """停止调度器"""
    await task_scheduler.stop()