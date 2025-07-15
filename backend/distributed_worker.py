import asyncio
import logging
import json
import aiohttp
import time
from datetime import datetime
from typing import Dict, Any, Optional, List
from contextlib import asynccontextmanager 

from worker_config import worker_config
from diagnosis.worker import WorkerPool
from database import get_db

logger = logging.getLogger(__name__)

class DistributedWorkerClient:
    """分布式Worker客户端"""
    
    def __init__(self, config):
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None
        self.worker_pool: Optional[WorkerPool] = None
        self.running = False
        self.last_heartbeat = None
        self.master_url = f"http://{config.master_host}:{config.master_port}{config.master_api_base}"
        
    async def start(self):
        """启动分布式Worker节点"""
        if self.running:
            return
            
        self.running = True
        logger.info(f"启动分布式Worker节点: {self.config.node_id}")
        
        # 创建HTTP会话
        timeout = aiohttp.ClientTimeout(total=30)
        headers = {}
        if self.config.api_token:
            headers['Authorization'] = f'Bearer {self.config.api_token}'
            
        self.session = aiohttp.ClientSession(
            timeout=timeout,
            headers=headers
        )
        
        # 启动Worker池
        self.worker_pool = WorkerPool(self.config.worker_pool_size)
        await self.worker_pool.start()
        
        # 注册节点
        await self._register_node()
        
        # 启动后台任务
        asyncio.create_task(self._heartbeat_loop())
        asyncio.create_task(self._task_polling_loop())
        
        logger.info(f"分布式Worker节点 {self.config.node_id} 启动完成")
        
    async def stop(self):
        """停止分布式Worker节点"""
        self.running = False
        
        # 注销节点
        await self._unregister_node()
        
        # 停止Worker池
        if self.worker_pool:
            await self.worker_pool.stop()
            
        # 关闭HTTP会话
        if self.session:
            await self.session.close()
            
        logger.info(f"分布式Worker节点 {self.config.node_id} 已停止")
        
    async def _register_node(self):
        """注册Worker节点到主节点"""
        try:
            node_info = {
                'node_id': self.config.node_id,
                'node_name': self.config.node_name,
                'worker_pool_size': self.config.worker_pool_size,
                'max_concurrent_tasks': self.config.max_concurrent_tasks,
                'capabilities': ['diagnosis'],
                'status': 'online',
                'registered_at': datetime.utcnow().isoformat()
            }
            
            async with self.session.post(
                f"{self.master_url}/diagnosis/workers/register",
                json=node_info
            ) as response:
                if response.status == 200:
                    logger.info(f"节点 {self.config.node_id} 注册成功")
                else:
                    logger.error(f"节点注册失败: {response.status}")
                    
        except Exception as e:
            logger.error(f"节点注册异常: {str(e)}")
            
    async def _unregister_node(self):
        """注销Worker节点"""
        try:
            async with self.session.delete(
                f"{self.master_url}/diagnosis/workers/{self.config.node_id}"
            ) as response:
                if response.status == 200:
                    logger.info(f"节点 {self.config.node_id} 注销成功")
                    
        except Exception as e:
            logger.error(f"节点注销异常: {str(e)}")
            
    async def _heartbeat_loop(self):
        """心跳循环"""
        while self.running:
            try:
                await self._send_heartbeat()
                await asyncio.sleep(self.config.heartbeat_interval)
            except Exception as e:
                logger.error(f"心跳发送失败: {str(e)}")
                await asyncio.sleep(self.config.heartbeat_interval)
                
    async def _send_heartbeat(self):
        """发送心跳"""
        try:
            heartbeat_data = {
                'node_id': self.config.node_id,
                'timestamp': datetime.utcnow().isoformat(),
                'status': 'online',
                'worker_status': self.worker_pool.get_pool_status() if self.worker_pool else {},
                'system_info': await self._get_system_info()
            }
            
            async with self.session.post(
                f"{self.master_url}/diagnosis/workers/{self.config.node_id}/heartbeat",
                json=heartbeat_data
            ) as response:
                if response.status == 200:
                    self.last_heartbeat = datetime.utcnow()
                    logger.debug(f"心跳发送成功: {self.config.node_id}")
                else:
                    logger.warning(f"心跳发送失败: {response.status}")
                    
        except Exception as e:
            logger.error(f"心跳发送异常: {str(e)}")
            
    async def _get_system_info(self) -> Dict[str, Any]:
        """获取系统信息"""
        import psutil
        
        return {
            'cpu_percent': psutil.cpu_percent(),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_percent': psutil.disk_usage('/').percent,
            'load_average': psutil.getloadavg() if hasattr(psutil, 'getloadavg') else [0, 0, 0]
        }
        
    async def _task_polling_loop(self):
        """任务轮询循环"""
        while self.running:
            try:
                await self._poll_and_execute_tasks()
                await asyncio.sleep(self.config.task_poll_interval)
            except Exception as e:
                logger.error(f"任务轮询失败: {str(e)}")
                await asyncio.sleep(self.config.task_poll_interval)
                
    async def _poll_and_execute_tasks(self):
        """轮询并执行任务"""
        try:
            # 检查是否有可用的Worker槽位
            if not self.worker_pool or not self._has_available_slots():
                return
                
            # 从主节点拉取任务
            tasks = await self._fetch_tasks()
            
            for task_data in tasks:
                task_id = task_data.get('task_id')
                if task_id:
                    # 提交任务到本地Worker池
                    success = await self.worker_pool.submit_task(task_id)
                    if success:
                        logger.info(f"任务 {task_id} 已提交到本地Worker池")
                    else:
                        logger.warning(f"任务 {task_id} 提交失败")
                        
        except Exception as e:
            logger.error(f"任务轮询执行异常: {str(e)}")
            
    def _has_available_slots(self) -> bool:
        """检查是否有可用的Worker槽位"""
        if not self.worker_pool:
            return False
            
        status = self.worker_pool.get_pool_status()
        total_slots = status.get('pool_size', 0) * self.config.max_concurrent_tasks
        current_tasks = status.get('total_current_tasks', 0)
        
        return current_tasks < total_slots
        
    async def _fetch_tasks(self) -> List[Dict[str, Any]]:
        """从主节点获取待执行的任务"""
        try:
            params = {
                'node_id': self.config.node_id,
                'batch_size': self.config.task_batch_size
            }
            
            async with self.session.get(
                f"{self.master_url}/diagnosis/tasks/fetch",
                params=params
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('tasks', [])
                else:
                    logger.warning(f"任务获取失败: {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"任务获取异常: {str(e)}")
            return []

class StandaloneWorkerNode:
    """独立Worker节点（不依赖主节点API）"""
    
    def __init__(self, config):
        self.config = config
        self.worker_pool: Optional[WorkerPool] = None
        self.running = False
        
    async def start(self):
        """启动独立Worker节点"""
        if self.running:
            return
            
        self.running = True
        logger.info(f"启动独立Worker节点: {self.config.node_id}")
        
        # 启动Worker池
        self.worker_pool = WorkerPool(self.config.worker_pool_size)
        await self.worker_pool.start()
        
        logger.info(f"独立Worker节点 {self.config.node_id} 启动完成")
        
    async def stop(self):
        """停止独立Worker节点"""
        self.running = False
        
        if self.worker_pool:
            await self.worker_pool.stop()
            
        logger.info(f"独立Worker节点 {self.config.node_id} 已停止")
        
    async def execute_task(self, task_id: int) -> bool:
        """执行任务"""
        if not self.worker_pool:
            return False
            
        return await self.worker_pool.submit_task(task_id)
        
    def get_status(self) -> Dict[str, Any]:
        """获取节点状态"""
        return {
            'node_id': self.config.node_id,
            'node_name': self.config.node_name,
            'running': self.running,
            'worker_pool': self.worker_pool.get_pool_status() if self.worker_pool else {}
        }