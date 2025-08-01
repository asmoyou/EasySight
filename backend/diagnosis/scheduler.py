import asyncio
import logging
from datetime import datetime, timezone, timedelta
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
            # 首先检查并恢复卡住的任务
            await self._check_and_recover_stuck_tasks(db)
            
            # 获取所有启用的定时任务
            result = await db.execute(
                select(DiagnosisTask).where(
                    and_(
                        DiagnosisTask.schedule_type == 'cron',
                        DiagnosisTask.is_active == True,
                        DiagnosisTask.status.in_([TaskStatus.PENDING, TaskStatus.RUNNING, TaskStatus.COMPLETED, TaskStatus.FAILED])
                    )
                )
            )
            tasks = result.scalars().all()
            
            current_time = datetime.utcnow()
            logger.info(f"检查到 {len(tasks)} 个定时任务，当前时间: {current_time}")
            
            for task in tasks:
                logger.info(f"检查任务: {task.name} (ID: {task.id}), cron: {task.cron_expression}, 状态: {task.status}, 激活: {task.is_active}")
                logger.info(f"任务上次运行时间: {task.last_run_time}, 下次运行时间: {task.next_run_time}")
                
                # 检查是否需要执行
                should_execute = await self._should_execute_task(task, current_time)
                logger.info(f"任务 {task.name} 是否应该执行: {should_execute}")
                
                if should_execute:
                    logger.info(f"开始调度任务执行: {task.name} (ID: {task.id})")
                    await self._schedule_task_execution(task, db)
                    
        except Exception as e:
            logger.error(f"检查任务调度失败: {str(e)}")
            import traceback
            logger.error(f"调度错误详情: {traceback.format_exc()}")
    
    async def _check_and_recover_stuck_tasks(self, db: AsyncSession):
        """检查并恢复卡住的任务"""
        try:
            # 查询所有处于运行状态的任务
            result = await db.execute(
                select(DiagnosisTask).where(
                    DiagnosisTask.status == TaskStatus.RUNNING
                )
            )
            running_tasks = result.scalars().all()
            
            if not running_tasks:
                return
            
            current_time = datetime.utcnow()
            recovered_count = 0
            
            for task in running_tasks:
                should_recover = False
                recover_reason = ""
                
                logger.info(f"检查任务: {task.name} (ID: {task.id})")
                logger.info(f"任务状态: {task.status}")
                logger.info(f"最后运行时间: {task.last_run_time}")
                
                # 检查任务是否真的在执行器中运行
                is_actually_running = task.id in diagnosis_executor.running_tasks
                logger.info(f"任务是否在执行器中运行: {is_actually_running}")
                logger.info(f"执行器运行任务列表: {diagnosis_executor.running_tasks}")
                
                if not is_actually_running:
                    should_recover = True
                    recover_reason = "任务不在执行器运行列表中"
                    logger.info(f"检查结果: {recover_reason}")
                elif task.last_run_time:
                    # 检查运行时间是否过长（超过30分钟认为卡住）
                    # 确保时间比较的一致性 - 都转换为UTC naive datetime
                    last_run_time = task.last_run_time
                    if last_run_time.tzinfo is not None:
                        # 如果有时区信息，转换为UTC时间然后移除时区信息
                        last_run_time = last_run_time.astimezone(timezone.utc).replace(tzinfo=None)
                    
                    time_diff = current_time - last_run_time
                    logger.info(f"当前时间: {current_time}")
                    logger.info(f"任务最后运行时间: {task.last_run_time}")
                    logger.info(f"处理后的最后运行时间: {last_run_time}")
                    logger.info(f"时间差: {time_diff}")
                    logger.info(f"时间差是否超过30分钟: {time_diff > timedelta(minutes=30)}")
                    if time_diff > timedelta(minutes=30):
                        should_recover = True
                        recover_reason = f"任务运行时间过长 ({time_diff})"
                        logger.info(f"检查结果: {recover_reason}")
                    else:
                        logger.info("检查结果: 任务运行时间正常，不需要恢复")
                else:
                    should_recover = True
                    recover_reason = "任务无最后运行时间记录"
                    logger.info(f"检查结果: {recover_reason}")
                
                logger.info(f"最终决定 - 是否应该恢复: {should_recover}, 原因: {recover_reason}")
                
                if should_recover:
                    logger.warning(f"检测到卡住的任务: {task.name} (ID: {task.id}) - {recover_reason}")
                    
                    # 重置任务状态为待执行
                    task.status = TaskStatus.PENDING
                    
                    # 从执行器运行列表中移除（如果存在）
                    diagnosis_executor.running_tasks.discard(task.id)
                    
                    # 从调度器的任务列表中移除（如果存在）
                    if task.id in self.scheduled_tasks:
                        scheduled_task = self.scheduled_tasks.pop(task.id)
                        if not scheduled_task.done():
                            scheduled_task.cancel()
                    
                    recovered_count += 1
                    logger.info(f"已恢复卡住的任务: {task.name} (ID: {task.id})")
            
            if recovered_count > 0:
                await db.commit()
                logger.info(f"自动恢复了 {recovered_count} 个卡住的任务")
                
        except Exception as e:
            logger.error(f"检查和恢复卡住任务失败: {str(e)}")
            await db.rollback()
            
    async def _should_execute_task(self, task: DiagnosisTask, current_time: datetime) -> bool:
        """判断任务是否应该执行"""
        # 如果任务正在运行，检查是否真的在运行
        if task.status == TaskStatus.RUNNING:
            # 检查任务是否真的在执行器中运行
            is_actually_running = task.id in diagnosis_executor.running_tasks
            if is_actually_running:
                return False  # 真的在运行，跳过
            else:
                # 任务状态显示运行但实际未运行，可能已经被自动恢复机制处理
                # 这里不直接返回True，而是继续后续的时间检查逻辑
                logger.warning(f"任务 {task.name} (ID: {task.id}) 状态为运行但实际未在执行器中运行")
            
        # 确保current_time有时区信息
        if current_time.tzinfo is None:
            current_time = current_time.replace(tzinfo=timezone.utc)
            
        # 检查下次执行时间
        if task.next_run_time:
            next_run_time = task.next_run_time
            if next_run_time.tzinfo is None:
                next_run_time = next_run_time.replace(tzinfo=timezone.utc)
            if next_run_time > current_time:
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
                
            last_run_time = task.last_run_time
            if last_run_time.tzinfo is None:
                last_run_time = last_run_time.replace(tzinfo=timezone.utc)
                
            interval_minutes = task.interval_minutes or 60
            next_run = last_run_time + timedelta(minutes=interval_minutes)
            return current_time >= next_run
            
        elif schedule_type == "cron":
            # Cron表达式
            if not task.cron_expression:
                return False
                
            try:
                # 确保时间都是UTC时区
                base_time = task.last_run_time or current_time
                if base_time.tzinfo is None:
                    base_time = base_time.replace(tzinfo=timezone.utc)
                if current_time.tzinfo is None:
                    current_time = current_time.replace(tzinfo=timezone.utc)
                    
                cron = croniter(task.cron_expression, base_time)
                next_run = cron.get_next(datetime)
                if next_run.tzinfo is None:
                    next_run = next_run.replace(tzinfo=timezone.utc)
                    
                return current_time >= next_run
            except Exception as e:
                logger.error(f"解析Cron表达式失败: {task.cron_expression}, {str(e)}")
                return False
                
        elif schedule_type == "manual":
            # 手动执行，不自动调度
            return False
            
        return False
        
    async def _schedule_task_execution(self, task: DiagnosisTask, db: AsyncSession):
        """调度任务执行 - 优先分配给worker节点"""
        task_id = task.id
        
        # 避免重复调度
        if task_id in self.scheduled_tasks:
            return
            
        # 更新下次执行时间
        await self._update_next_run_time(task, db)
        
        try:
            # 检查是否有可用的分布式worker节点
            available_worker = await self._find_available_worker()
            
            if available_worker:
                # 分配给分布式worker节点
                success = await self._assign_task_to_worker(task, available_worker, db)
                if success:
                    logger.info(f"任务 {task.name} (ID: {task.id}) 已分配给worker节点 {available_worker}")
                    return
                else:
                    logger.warning(f"分配任务 {task.name} (ID: {task.id}) 给worker节点 {available_worker} 失败，回退到主服务执行")
            
            # 没有可用worker或分配失败，在主服务执行
            logger.info(f"任务 {task.name} (ID: {task.id}) 将在主服务执行（无可用worker节点）")
            
            # 创建执行任务
            execution_task = asyncio.create_task(
                self._execute_task_with_semaphore(task_id)
            )
            
            self.scheduled_tasks[task_id] = execution_task
            
            # 任务完成后清理
            execution_task.add_done_callback(
                lambda t: self.scheduled_tasks.pop(task_id, None)
            )
            
        except Exception as e:
            logger.error(f"调度任务 {task.name} (ID: {task.id}) 失败: {str(e)}")
            # 更新任务状态为失败
            task.status = TaskStatus.FAILED
            task.last_run_time = datetime.now(timezone.utc)
            await db.commit()
        
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
                    # 确保时间都是UTC时区
                    if current_time.tzinfo is None:
                        current_time = current_time.replace(tzinfo=timezone.utc)
                    cron = croniter(task.cron_expression, current_time)
                    next_run_time = cron.get_next(datetime)
                    if next_run_time.tzinfo is None:
                        next_run_time = next_run_time.replace(tzinfo=timezone.utc)
                except Exception as e:
                    logger.error(f"计算Cron下次执行时间失败: {str(e)}")
                    
            if next_run_time:
                task.next_run_time = next_run_time
                await db.commit()
                
        except Exception as e:
            logger.error(f"更新下次执行时间失败: {str(e)}")
            
    async def _find_available_worker(self) -> Optional[str]:
        """查找可用的worker节点"""
        try:
            from routers.diagnosis import distributed_workers
            from datetime import datetime, timezone
            
            current_time = datetime.now(timezone.utc)
            
            # 查找在线且有可用容量的worker节点
            for node_id, node_data in distributed_workers.items():
                # 检查节点是否在线（3分钟内有心跳）
                last_heartbeat = node_data.get("last_heartbeat")
                if not last_heartbeat:
                    continue
                    
                if last_heartbeat.tzinfo is None:
                    last_heartbeat = last_heartbeat.replace(tzinfo=timezone.utc)
                    
                if (current_time - last_heartbeat).total_seconds() > 180:
                    continue
                    
                # 检查节点是否有可用容量
                current_tasks = node_data.get("current_tasks", 0)
                max_concurrent = node_data.get("max_concurrent_tasks", 1)
                
                if current_tasks < max_concurrent:
                    return node_id
                    
            return None
            
        except Exception as e:
            logger.error(f"查找可用worker节点时发生错误: {str(e)}")
            return None
    
    async def _assign_task_to_worker(self, task: DiagnosisTask, worker_node_id: str, db: AsyncSession) -> bool:
        """分配任务给指定的worker节点"""
        try:
            from routers.diagnosis import distributed_workers
            
            # 更新任务状态为PENDING，等待worker获取
            task.status = TaskStatus.PENDING
            task.assigned_worker = worker_node_id
            await db.commit()
            
            # 更新worker节点的当前任务数
            if worker_node_id in distributed_workers:
                distributed_workers[worker_node_id]["current_tasks"] = distributed_workers[worker_node_id].get("current_tasks", 0) + 1
                current_task_ids = distributed_workers[worker_node_id].get("current_task_ids", [])
                current_task_ids.append(task.id)
                distributed_workers[worker_node_id]["current_task_ids"] = current_task_ids
            
            logger.info(f"任务 {task.name} (ID: {task.id}) 已分配给worker节点 {worker_node_id}")
            return True
            
        except Exception as e:
            logger.error(f"分配任务给worker节点 {worker_node_id} 时发生错误: {str(e)}")
            return False

    async def execute_task_immediately(self, task_id: int) -> Dict[str, any]:
        """立即执行任务 - 优先分配给worker节点"""
        try:
            async for db in get_db():
                # 获取任务信息
                result = await db.execute(
                    select(DiagnosisTask).where(DiagnosisTask.id == task_id)
                )
                task = result.scalar_one_or_none()
                
                if not task:
                    return {
                        "success": False,
                        "message": f"任务 ID {task_id} 不存在"
                    }
                    
                if not task.is_active:
                    return {
                        "success": False,
                        "message": f"任务 {task.name} (ID: {task_id}) 未激活"
                    }
                
                # 检查任务是否正在运行
                if task.status == TaskStatus.RUNNING:
                    return {
                        "success": False,
                        "message": f"任务 {task.name} (ID: {task_id}) 正在运行中"
                    }
                
                logger.info(f"开始立即执行任务: {task.name} (ID: {task_id})")
                
                # 检查是否有可用的分布式worker节点
                available_worker = await self._find_available_worker()
                
                if available_worker:
                    # 分配给分布式worker节点
                    success = await self._assign_task_to_worker(task, available_worker, db)
                    if success:
                        logger.info(f"任务 {task.name} (ID: {task_id}) 已分配给worker节点 {available_worker}，等待执行")
                        return {
                            "success": True,
                            "message": f"任务 {task.name} (ID: {task_id}) 已分配给worker节点 {available_worker}，等待执行"
                        }
                    else:
                        logger.warning(f"分配任务 {task.name} (ID: {task_id}) 给worker节点 {available_worker} 失败，回退到主服务执行")
                
                # 没有可用worker或分配失败，在主服务执行
                logger.info(f"任务 {task.name} (ID: {task_id}) 将在主服务执行（无可用worker节点）")
                
                # 使用信号量限制并发执行
                async with self.worker_semaphore:
                    result = await diagnosis_executor.execute_task(task_id, db)
                    
                    # 如果任务执行成功，更新下次运行时间
                    if result.get('success'):
                        if task.schedule_type == 'cron':
                            await self._update_next_run_time(task, db)
                            logger.info(f"任务 {task_id} 执行完成，已更新下次运行时间为: {task.next_run_time}")
                    
                    return result
                break
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
        self.last_heartbeat = datetime.now(timezone.utc)
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