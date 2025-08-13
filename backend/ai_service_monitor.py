import asyncio
import logging
import json
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from sqlalchemy import select, update, func, case
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from models.ai_algorithm import AIService, ServiceStatus
from models.camera import Camera
from rabbitmq_event_task_manager import rabbitmq_event_task_manager as event_task_manager
import aiohttp

logger = logging.getLogger(__name__)

class AIServiceMonitor:
    """AI服务监控器 - 负责管理AI服务的生命周期和任务分发"""
    
    def __init__(self):
        self.running = False
        self.active_services: Dict[int, Dict] = {}
        self.monitor_interval = 10  # 监控间隔(秒)
        
    async def start(self):
        """启动AI服务监控器"""
        if self.running:
            return
            
        self.running = True
        logger.info("AI服务监控器启动")
        
        # 启动监控任务
        asyncio.create_task(self._monitor_services())
        
    async def stop(self):
        """停止AI服务监控器"""
        self.running = False
        logger.info("AI服务监控器停止")
        
    async def _monitor_services(self):
        """监控AI服务状态"""
        while self.running:
            try:
                async for db in get_db():
                    await self._check_service_status(db)
                    break
            except Exception as e:
                logger.error(f"监控AI服务异常: {str(e)}")
                
            await asyncio.sleep(self.monitor_interval)
            
    async def _check_service_status(self, db: AsyncSession):
        """检查服务状态"""
        try:
            # 获取所有运行中的服务
            result = await db.execute(
                select(AIService).where(
                    AIService.status == ServiceStatus.RUNNING,
                    AIService.is_active == True
                )
            )
            services = result.scalars().all()
            
            for service in services:
                # 更新服务心跳
                service.last_heartbeat = datetime.now(timezone.utc)
                
                # 检查摄像头状态
                camera_result = await db.execute(
                    select(Camera).where(Camera.id == service.camera_id)
                )
                camera = camera_result.scalar_one_or_none()
                
                if not camera or not camera.is_active:
                    logger.warning(f"服务 {service.name} 关联的摄像头不可用")
                    continue
                    
                # 更新活跃服务列表
                self.active_services[service.id] = {
                    'service': service,
                    'camera': camera,
                    'last_check': datetime.now(timezone.utc)
                }
                
            await db.commit()
            logger.debug(f"检查了 {len(services)} 个运行中的AI服务")
            
        except Exception as e:
            logger.error(f"检查服务状态异常: {str(e)}")
            

            

            
    async def start_service(self, service_id: int, user_id: str = None) -> bool:
        """启动指定的AI服务"""
        try:
            async for db in get_db():
                 # 获取服务信息
                 result = await db.execute(
                     select(AIService, Camera)
                     .join(Camera, AIService.camera_id == Camera.id)
                     .where(AIService.id == service_id)
                 )
                 service_data = result.first()
                 
                 if not service_data:
                     logger.error(f"服务 {service_id} 不存在")
                     return False
                 
                 service, camera = service_data
                 
                 # 检查摄像头是否在线
                 if not camera.is_active:
                     logger.error(f"摄像头 {camera.id} 不在线，无法启动服务")
                     return False
                 
                 # 更新服务状态为运行中
                 service.status = ServiceStatus.RUNNING
                 service.last_heartbeat = datetime.now(timezone.utc)
                 await db.commit()
                 
                 # 将服务添加到活跃服务列表
                 self.active_services[service_id] = {
                     'service': service,
                     'camera': camera,
                     'last_detection': None,
                     'detection_count': 0,
                     'error_count': 0
                 }
                 
                 # 使用事件任务管理器创建事件任务
                 task_id = await event_task_manager.create_task_from_service(service_id, user_id)
                 if task_id:
                     # 不立即启动事件任务，让Worker来认领PENDING状态的任务
                     logger.info(f"AI服务 {service_id} 启动成功，创建事件任务 {task_id}，等待Worker认领")
                 else:
                     logger.warning(f"AI服务 {service_id} 启动成功，但创建事件任务失败")
                 
                 logger.info(f"AI服务 {service_id} 启动成功")
                 return True
                 break
                
        except Exception as e:
            logger.error(f"启动AI服务 {service_id} 失败: {e}")
            return False
    
    async def stop_service(self, service_id: int) -> bool:
        """停止指定的AI服务"""
        try:
            async for db in get_db():
                # 更新服务状态
                result = await db.execute(
                    select(AIService).where(AIService.id == service_id)
                )
                service = result.scalar_one_or_none()
                
                if service:
                    service.status = ServiceStatus.STOPPED
                    service.last_heartbeat = datetime.now(timezone.utc)
                    await db.commit()
                
                # 停止相关的事件任务
                from models.event_task import EventTask, EventTaskStatus
                task_result = await db.execute(
                    select(EventTask).where(
                        EventTask.ai_service_id == service_id,
                        EventTask.status == EventTaskStatus.RUNNING
                    )
                )
                running_tasks = task_result.scalars().all()
                
                for task in running_tasks:
                    await event_task_manager.stop_task(task.id, "AI服务停止")
                    
                # 从活跃服务列表中移除
                if service_id in self.active_services:
                    del self.active_services[service_id]
                    
                logger.info(f"AI服务 {service_id} 停止成功")
                return True
                
        except Exception as e:
            logger.error(f"停止AI服务 {service_id} 失败: {e}")
            return False
    
    async def get_service_stats(self) -> Dict[str, Any]:
        """获取服务统计信息"""
        try:
            async for db in get_db():
                # 获取服务统计
                total_services = await db.execute(select(AIService))
                total_count = len(total_services.scalars().all())
                
                running_services = await db.execute(
                    select(AIService).where(AIService.status == ServiceStatus.RUNNING)
                )
                running_count = len(running_services.scalars().all())
                
                return {
                    'total_services': total_count,
                    'running_services': running_count,
                    'active_services': len(self.active_services),
                    'monitor_status': 'running' if self.running else 'stopped'
                }
                
        except Exception as e:
            logger.error(f"获取服务统计异常: {str(e)}")
            return {
                'total_services': 0,
                'running_services': 0,
                'active_services': 0,
                'monitor_status': 'error'
            }

# 全局AI服务监控器实例
ai_service_monitor = AIServiceMonitor()