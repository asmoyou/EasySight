import asyncio
import aiohttp
import logging
from datetime import datetime, timezone
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from models.camera import Camera, CameraStatus
from typing import List, Optional

logger = logging.getLogger(__name__)

class CameraMonitor:
    """摄像头状态监控器"""
    
    def __init__(self):
        self.session_timeout = aiohttp.ClientTimeout(total=10)  # 10秒超时
    
    async def check_rtsp_stream(self, stream_url: str) -> bool:
        """检查RTSP流是否可用"""
        try:
            # 验证URL格式
            if not stream_url.startswith('rtsp://'):
                logger.warning(f"Invalid RTSP URL format: {stream_url}")
                return False
            
            # 使用简单的TCP连接测试替代OpenCV，避免阻塞和异常
            import socket
            import asyncio
            from urllib.parse import urlparse
            
            def _check_rtsp_tcp():
                """通过TCP连接测试RTSP服务是否可达"""
                try:
                    parsed = urlparse(stream_url)
                    host = parsed.hostname
                    port = parsed.port or 554  # RTSP默认端口
                    
                    if not host:
                        return False
                    
                    # 创建TCP连接测试
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(3)  # 3秒超时
                    result = sock.connect_ex((host, port))
                    sock.close()
                    return result == 0
                except Exception:
                    return False
            
            # 在线程池中运行TCP连接测试
            loop = asyncio.get_event_loop()
            from concurrent.futures import ThreadPoolExecutor
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = loop.run_in_executor(executor, _check_rtsp_tcp)
                return await asyncio.wait_for(future, timeout=5.0)
                
        except asyncio.TimeoutError:
            logger.debug(f"RTSP stream check timeout for {stream_url}")
            return False
        except Exception as e:
            logger.debug(f"RTSP stream check failed for {stream_url}: {e}")
            return False
    
    async def check_http_stream(self, stream_url: str) -> bool:
        """检查HTTP流是否可用"""
        try:
            async with aiohttp.ClientSession(timeout=self.session_timeout) as session:
                async with session.head(stream_url) as response:
                    return response.status == 200
        except Exception as e:
            logger.debug(f"HTTP stream check failed for {stream_url}: {e}")
            return False
    
    async def check_camera_status(self, camera: Camera) -> CameraStatus:
        """检查单个摄像头状态"""
        if not camera.stream_url:
            return CameraStatus.ERROR
        
        # 验证URL格式
        if not (camera.stream_url.startswith('rtsp://') or 
                camera.stream_url.startswith('http://') or 
                camera.stream_url.startswith('https://')):
            logger.warning(f"Unsupported stream URL format: {camera.stream_url}")
            return CameraStatus.ERROR
        
        # 根据流URL类型选择检测方法
        if camera.stream_url.startswith('rtsp://'):
            is_available = await self.check_rtsp_stream(camera.stream_url)
        elif camera.stream_url.startswith('http://') or camera.stream_url.startswith('https://'):
            is_available = await self.check_http_stream(camera.stream_url)
        else:
            return CameraStatus.ERROR
        
        return CameraStatus.ONLINE if is_available else CameraStatus.OFFLINE
    
    async def update_camera_status(self, db: AsyncSession, camera_id: int, status: CameraStatus):
        """更新摄像头状态"""
        try:
            stmt = (
                update(Camera)
                .where(Camera.id == camera_id)
                .values(
                    status=status,
                    last_heartbeat=datetime.now(timezone.utc)
                )
            )
            await db.execute(stmt)
            await db.commit()
            logger.debug(f"Updated camera {camera_id} status to {status.value}")
        except Exception as e:
            logger.error(f"Failed to update camera {camera_id} status: {e}")
            await db.rollback()
    
    async def monitor_all_cameras(self):
        """监控所有摄像头状态"""
        logger.info("Starting camera status monitoring...")
        
        async for db in get_db():
            try:
                # 获取所有启用的摄像头
                result = await db.execute(
                    select(Camera).where(Camera.is_active == True)
                )
                cameras = result.scalars().all()
                
                logger.info(f"Monitoring {len(cameras)} cameras")
                
                # 并发检查所有摄像头状态
                tasks = []
                for camera in cameras:
                    task = self.check_and_update_camera(db, camera)
                    tasks.append(task)
                
                if tasks:
                    await asyncio.gather(*tasks, return_exceptions=True)
                
                logger.info("Camera status monitoring completed")
                
            except Exception as e:
                logger.error(f"Error in camera monitoring: {e}")
            finally:
                await db.close()
    
    async def check_and_update_camera(self, db: AsyncSession, camera: Camera):
        """检查并更新单个摄像头状态"""
        try:
            new_status = await self.check_camera_status(camera)
            
            # 只有状态发生变化时才更新
            if new_status != camera.status:
                await self.update_camera_status(db, camera.id, new_status)
                logger.info(f"Camera {camera.code} status changed: {camera.status.value} -> {new_status.value}")
            
        except Exception as e:
            logger.error(f"Error checking camera {camera.code}: {e}")
            # 如果检查失败，标记为错误状态
            if camera.status != CameraStatus.ERROR:
                await self.update_camera_status(db, camera.id, CameraStatus.ERROR)

# 全局监控器实例
camera_monitor = CameraMonitor()