import asyncio
from sqlalchemy import select, update, insert
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone
import config
from utils import logTool
from utils.systemMonitor import system_monitor
from database import AsyncSessionLocal
from models import Camera, MediaProxy

# 设置日志
logger = logTool.StandardLogger('utils.dataModel')

class MediaNodeManager:
    """媒体节点管理器"""
    
    def __init__(self):
        self.node_info = {
            'name': config.MEDIA_NODE_NAME,
            'ip_address': config.MEDIA_NODE_IP,
            'port': config.MEDIA_NODE_PORT,
            'secret_key': config.MEDIA_NODE_SECRET,
            'max_connections': config.MEDIA_NODE_MAX_CONNECTIONS
        }
    
    async def register_node(self):
        """注册媒体节点到数据库"""
        try:
            async with AsyncSessionLocal() as session:
                # 检查节点是否已存在
                stmt = select(MediaProxy).where(
                    MediaProxy.ip_address == self.node_info['ip_address'],
                    MediaProxy.port == self.node_info['port']
                )
                result = await session.execute(stmt)
                existing_node = result.scalar_one_or_none()
                
                if existing_node:
                    # 更新现有节点
                    stmt = update(MediaProxy).where(
                        MediaProxy.id == existing_node.id
                    ).values(
                        name=self.node_info['name'],
                        secret_key=self.node_info['secret_key'],
                        max_connections=self.node_info['max_connections'],
                        is_online=True,
                        last_heartbeat=datetime.now(timezone.utc)
                    )
                    await session.execute(stmt)
                    logger.info(f"Updated existing media node: {self.node_info['name']}")
                    node_id = existing_node.id
                else:
                    # 创建新节点
                    new_node = MediaProxy(
                        name=self.node_info['name'],
                        ip_address=self.node_info['ip_address'],
                        port=self.node_info['port'],
                        secret_key=self.node_info['secret_key'],
                        max_connections=self.node_info['max_connections'],
                        is_online=True,
                        last_heartbeat=datetime.now(timezone.utc)
                    )
                    session.add(new_node)
                    await session.flush()
                    logger.info(f"Registered new media node: {self.node_info['name']}")
                    node_id = new_node.id
                
                await session.commit()
                return node_id
                
        except Exception as e:
            logger.error(f"Failed to register media node: {e}")
            return None
    
    async def update_node_status(self, cpu_usage=None, memory_usage=None, bandwidth_usage=None, current_connections=None):
        """更新节点状态信息"""
        try:
            async with AsyncSessionLocal() as session:
                stmt = update(MediaProxy).where(
                    MediaProxy.ip_address == self.node_info['ip_address'],
                    MediaProxy.port == self.node_info['port']
                ).values(
                    is_online=True,
                    last_heartbeat=datetime.now(timezone.utc),
                    cpu_usage=cpu_usage,
                    memory_usage=memory_usage,
                    bandwidth_usage=bandwidth_usage,
                    current_connections=current_connections
                )
                await session.execute(stmt)
                await session.commit()
                logger.debug(f"Updated node status for {self.node_info['name']}")
                
        except Exception as e:
            logger.error(f"Failed to update node status: {e}")
    
    async def collect_and_report_system_metrics(self):
        """收集系统资源信息并上报到数据库"""
        try:
            logger.info("=== Starting to collect system metrics ===")
            logger.debug("Starting to collect system metrics...")
            
            # 收集系统指标
            metrics = await system_monitor.get_all_metrics()
            
            if not metrics:
                logger.warning("Failed to collect system metrics")
                return
            
            logger.debug(f"Collected metrics: {metrics}")
            
            # 提取关键指标
            cpu_usage = metrics.get('cpu', {}).get('usage_percent', 0)
            memory_usage = metrics.get('memory', {}).get('percent', 0)
            bandwidth_usage = metrics.get('network', {}).get('send_rate', 0) + metrics.get('network', {}).get('recv_rate', 0)
            
            logger.debug(f"Extracted metrics - CPU: {cpu_usage}, Memory: {memory_usage}, Bandwidth: {bandwidth_usage}")
            
            # 获取当前连接数（这里可以根据实际情况获取，暂时使用0）
            current_connections = 0  # TODO: 实现获取实际连接数的逻辑
            
            # 更新节点状态
            await self.update_node_status(
                cpu_usage=cpu_usage,
                memory_usage=memory_usage,
                bandwidth_usage=bandwidth_usage,
                current_connections=current_connections
            )
            
            logger.info(f"System metrics reported - CPU: {cpu_usage:.1f}%, Memory: {memory_usage:.1f}%, Bandwidth: {bandwidth_usage:.2f}MB/s")
            
        except Exception as e:
            logger.error(f"Failed to collect and report system metrics: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
    
    async def unregister_node(self):
        """注销媒体节点"""
        try:
            async with AsyncSessionLocal() as session:
                stmt = update(MediaProxy).where(
                    MediaProxy.ip_address == self.node_info['ip_address'],
                    MediaProxy.port == self.node_info['port']
                ).values(
                    is_online=False,
                    last_heartbeat=datetime.now(timezone.utc)
                )
                await session.execute(stmt)
                await session.commit()
                logger.info(f"Unregistered media node: {self.node_info['name']}")
                
        except Exception as e:
            logger.error(f"Failed to unregister media node: {e}")

class CameraManager:
    """摄像头管理器"""
    
    async def get_camera_list(self):
        """获取摄像头列表"""
        try:
            async with AsyncSessionLocal() as session:
                stmt = select(Camera).where(Camera.is_active == True)
                result = await session.execute(stmt)
                cameras = result.scalars().all()
                
                camera_list = []
                for camera in cameras:
                    camera_dict = {
                        'id': camera.id,
                        'code': camera.code,
                        'name': camera.name,
                        'stream_url': camera.stream_url,
                        'backup_stream_url': camera.backup_stream_url,
                        'camera_type': camera.camera_type.value if camera.camera_type else None,
                        'media_proxy_id': camera.media_proxy_id,
                        'media_proxy_name': camera.media_proxy_name,
                        'location': camera.location,
                        'status': camera.status.value if camera.status else None,
                        'is_recording': camera.is_recording,
                        'resolution': camera.resolution,
                        'frame_rate': camera.frame_rate,
                        'bitrate': camera.bitrate
                    }
                    camera_list.append(camera_dict)
                
                logger.debug(f"Retrieved {len(camera_list)} cameras")
                return camera_list
                
        except Exception as e:
            logger.error(f"Failed to get camera list: {e}")
            return []
    
    async def get_camera_by_id(self, camera_id):
        """根据ID获取摄像头信息"""
        try:
            async with AsyncSessionLocal() as session:
                stmt = select(Camera).where(Camera.id == camera_id)
                result = await session.execute(stmt)
                camera = result.scalar_one_or_none()
                
                if camera:
                    camera_dict = {
                        'id': camera.id,
                        'code': camera.code,
                        'name': camera.name,
                        'stream_url': camera.stream_url,
                        'backup_stream_url': camera.backup_stream_url,
                        'camera_type': camera.camera_type.value if camera.camera_type else None,
                        'media_proxy_id': camera.media_proxy_id,
                        'media_proxy_name': camera.media_proxy_name,
                        'location': camera.location,
                        'status': camera.status.value if camera.status else None,
                        'is_recording': camera.is_recording,
                        'resolution': camera.resolution,
                        'frame_rate': camera.frame_rate,
                        'bitrate': camera.bitrate,
                        'ip_address': camera.ip_address,
                        'port': camera.port,
                        'username': camera.username,
                        'password': camera.password
                    }
                    logger.debug(f"Retrieved camera: {camera.code}")
                    return camera_dict
                else:
                    logger.warning(f"Camera not found: {camera_id}")
                    return None
                    
        except Exception as e:
            logger.error(f"Failed to get camera by id {camera_id}: {e}")
            return None
    
    async def get_camera_by_code(self, camera_code):
        """根据编码获取摄像头信息"""
        try:
            async with AsyncSessionLocal() as session:
                stmt = select(Camera).where(Camera.code == camera_code)
                result = await session.execute(stmt)
                camera = result.scalar_one_or_none()
                
                if camera:
                    camera_dict = {
                        'id': camera.id,
                        'code': camera.code,
                        'name': camera.name,
                        'stream_url': camera.stream_url,
                        'backup_stream_url': camera.backup_stream_url,
                        'camera_type': camera.camera_type.value if camera.camera_type else None,
                        'media_proxy_id': camera.media_proxy_id,
                        'media_proxy_name': camera.media_proxy_name,
                        'location': camera.location,
                        'status': camera.status.value if camera.status else None,
                        'is_recording': camera.is_recording,
                        'resolution': camera.resolution,
                        'frame_rate': camera.frame_rate,
                        'bitrate': camera.bitrate,
                        'ip_address': camera.ip_address,
                        'port': camera.port,
                        'username': camera.username,
                        'password': camera.password
                    }
                    logger.debug(f"Retrieved camera: {camera.code}")
                    return camera_dict
                else:
                    logger.warning(f"Camera not found: {camera_code}")
                    return None
                    
        except Exception as e:
            logger.error(f"Failed to get camera by code {camera_code}: {e}")
            return None

    async def update_camera_status(self, camera_id, status, is_recording=None):
        """更新摄像头状态"""
        try:
            async with AsyncSessionLocal() as session:
                update_values = {
                    'status': status,
                    'last_heartbeat': datetime.now(timezone.utc)
                }
                if is_recording is not None:
                    update_values['is_recording'] = is_recording
                
                stmt = update(Camera).where(Camera.id == camera_id).values(**update_values)
                await session.execute(stmt)
                await session.commit()
                logger.debug(f"Updated camera {camera_id} status to {status}")
                
        except Exception as e:
            logger.error(f"Failed to update camera status: {e}")

class MediaProxyManager:
    """媒体代理管理器"""
    
    async def get_media_proxy_list(self):
        """获取媒体代理列表"""
        try:
            async with AsyncSessionLocal() as session:
                stmt = select(MediaProxy)
                result = await session.execute(stmt)
                proxies = result.scalars().all()
                
                proxy_list = []
                for proxy in proxies:
                    proxy_dict = {
                        'id': proxy.id,
                        'name': proxy.name,
                        'ip_address': proxy.ip_address,
                        'port': proxy.port,
                        'is_online': proxy.is_online,
                        'cpu_usage': proxy.cpu_usage,
                        'memory_usage': proxy.memory_usage,
                        'bandwidth_usage': proxy.bandwidth_usage,
                        'max_connections': proxy.max_connections,
                        'current_connections': proxy.current_connections,
                        'last_heartbeat': proxy.last_heartbeat.isoformat() if proxy.last_heartbeat else None
                    }
                    proxy_list.append(proxy_dict)
                
                logger.debug(f"Retrieved {len(proxy_list)} media proxies")
                return proxy_list
                
        except Exception as e:
            logger.error(f"Failed to get media proxy list: {e}")
            return []
    
    async def get_media_proxy_info(self, proxy_id):
        """获取媒体代理信息"""
        try:
            async with AsyncSessionLocal() as session:
                stmt = select(MediaProxy).where(MediaProxy.id == proxy_id)
                result = await session.execute(stmt)
                proxy = result.scalar_one_or_none()
                
                if proxy:
                    proxy_dict = {
                        'id': proxy.id,
                        'name': proxy.name,
                        'ip_address': proxy.ip_address,
                        'port': proxy.port,
                        'is_online': proxy.is_online,
                        'cpu_usage': proxy.cpu_usage,
                        'memory_usage': proxy.memory_usage,
                        'bandwidth_usage': proxy.bandwidth_usage,
                        'max_connections': proxy.max_connections,
                        'current_connections': proxy.current_connections,
                        'last_heartbeat': proxy.last_heartbeat.isoformat() if proxy.last_heartbeat else None,
                        'description': proxy.description
                    }
                    logger.debug(f"Retrieved media proxy: {proxy.name}")
                    return proxy_dict
                else:
                    logger.warning(f"Media proxy not found: {proxy_id}")
                    return None
                    
        except Exception as e:
            logger.error(f"Failed to get media proxy info: {e}")
            return None

# 全局管理器实例
media_node_manager = MediaNodeManager()
camera_manager = CameraManager()
media_proxy_manager = MediaProxyManager()

# 兼容性函数
async def get_camera_by_id(camera_id: str):
    """根据摄像头ID获取摄像头信息"""
    return await camera_manager.get_camera_info(camera_id)

# 兼容性函数（保持原有接口）
async def get_camera_list():
    """获取摄像头列表"""
    return await camera_manager.get_camera_list()

async def get_camera_by_id(camera_id):
    """根据ID获取摄像头信息"""
    return await camera_manager.get_camera_by_id(camera_id)

async def get_camera_by_code(camera_code):
    """根据编码获取摄像头信息"""
    return await camera_manager.get_camera_by_code(camera_code)

async def update_media_worker_online(status_info=None):
    """更新媒体工作节点在线状态并上报系统指标"""
    logger.info("=== update_media_worker_online called ===")
    if status_info:
        await media_node_manager.update_node_status(
            cpu_usage=status_info.get('cpu_usage'),
            memory_usage=status_info.get('memory_usage'),
            bandwidth_usage=status_info.get('bandwidth_usage'),
            current_connections=status_info.get('current_connections')
        )
    else:
        # 调用系统监控数据收集和上报
        await media_node_manager.collect_and_report_system_metrics()
    logger.info("=== update_media_worker_online completed ===")

async def get_media_worker_info():
    """获取媒体工作节点信息"""
    return media_node_manager.node_info

async def get_media_worker_list():
    """获取媒体工作节点列表"""
    return await media_proxy_manager.get_media_proxy_list()
