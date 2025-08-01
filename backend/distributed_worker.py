import asyncio
import logging
import json
import aiohttp
import time
import socket
import uuid
import psutil
import sys
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from contextlib import asynccontextmanager 
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent))

from diagnosis.executor import DiagnosisExecutor
from database import get_db
from models.diagnosis import TaskStatus

logger = logging.getLogger(__name__)

class DistributedWorkerClient:
    """分布式Worker客户端"""
    
    def __init__(self, 
                 server_url: str = "http://localhost:8000",
                 worker_pool_size: int = 3,
                 max_concurrent_tasks: int = 2,
                 node_name: Optional[str] = None):
        
        self.server_url = server_url.rstrip('/')
        self.worker_pool_size = worker_pool_size
        self.max_concurrent_tasks = max_concurrent_tasks
        
        # 生成节点信息
        self.node_id = self._generate_node_id()
        self.node_name = node_name or f"Worker-{socket.gethostname()}"
        
        # 运行状态
        self.session: Optional[aiohttp.ClientSession] = None
        self.running = False
        self.current_tasks: Dict[int, Dict] = {}
        self.last_heartbeat = None
        
        # 统计信息
        self.stats = {
            "total_tasks_executed": 0,
            "tasks_completed": 0,
            "tasks_failed": 0,
            "start_time": None
        }
        
        # 诊断执行器
        self.diagnosis_executor = DiagnosisExecutor()
        
        # 配置参数
        self.heartbeat_interval = 30  # 心跳间隔（秒）
        self.task_fetch_interval = 5  # 任务获取间隔（秒）
        self.max_retry_attempts = 3   # 最大重试次数
        
    def _generate_node_id(self) -> str:
        """生成节点ID"""
        hostname = socket.gethostname()
        return f"{hostname}-{str(uuid.uuid4())[:8]}"
    
    def _get_system_info(self) -> Dict:
        """获取系统信息"""
        try:
            return {
                "hostname": socket.gethostname(),
                "cpu_count": psutil.cpu_count(),
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory_total": psutil.virtual_memory().total,
                "memory_available": psutil.virtual_memory().available,
                "memory_percent": psutil.virtual_memory().percent,
                "disk_usage": psutil.disk_usage('/').percent if sys.platform != 'win32' else psutil.disk_usage('C:').percent
            }
        except Exception as e:
            logger.warning(f"获取系统信息失败: {str(e)}")
            return {}
        
    async def start(self):
        """启动分布式Worker节点"""
        if self.running:
            return
            
        self.running = True
        self.stats["start_time"] = datetime.now(timezone.utc)
        logger.info(f"启动分布式Worker节点: {self.node_id}")
        
        # 创建HTTP会话
        timeout = aiohttp.ClientTimeout(total=30, connect=5)
        connector = aiohttp.TCPConnector(
            limit=10,
            limit_per_host=5,
            enable_cleanup_closed=True,
            force_close=True,  # 强制关闭连接，避免Windows下的连接复用问题
            ttl_dns_cache=300
        )
            
        self.session = aiohttp.ClientSession(
            timeout=timeout,
            connector=connector
        )
        
        # 注册节点
        await self._register_node()
        
        # 启动后台任务
        asyncio.create_task(self._heartbeat_loop())
        asyncio.create_task(self._task_polling_loop())
        
        logger.info(f"分布式Worker节点 {self.node_id} 启动完成")
        
    async def stop(self):
        """停止分布式Worker节点"""
        self.running = False
        
        # 等待任务轮询循环退出
        await asyncio.sleep(1)
        
        # 注销节点
        await self._unregister_node()
            
        # 关闭HTTP会话
        if self.session:
            await self.session.close()
            
        logger.info(f"分布式Worker节点 {self.node_id} 已停止")
        
    async def _register_node(self):
        """注册Worker节点到主节点"""
        max_retries = 3
        retry_delay = 5  # 秒
        
        for attempt in range(max_retries):
            try:
                node_info = {
                    'node_id': self.node_id,
                    'node_name': self.node_name,
                    'max_concurrent_tasks': self.max_concurrent_tasks,
                    'capabilities': ['image_diagnosis', 'brightness_check', 'clarity_check'],
                    'system_info': self._get_system_info(),
                    'status': 'online',
                    'registered_at': datetime.now(timezone.utc).isoformat()
                }
                
                async with self.session.post(
                    f"{self.server_url}/api/v1/diagnosis/worker/register",
                    json=node_info
                ) as response:
                    if response.status == 200:
                        logger.info(f"节点 {self.node_id} 注册成功")
                        return True
                    else:
                        logger.error(f"节点注册失败: {response.status}")
                        
            except Exception as e:
                logger.error(f"节点注册异常 (尝试 {attempt + 1}/{max_retries}): {str(e)}")
                
            # 如果不是最后一次尝试，等待后重试
            if attempt < max_retries - 1:
                logger.info(f"等待 {retry_delay} 秒后重试注册...")
                await asyncio.sleep(retry_delay)
                
        logger.error(f"节点 {self.node_id} 注册失败，已达到最大重试次数")
        return False
            
    async def _unregister_node(self):
        """注销Worker节点"""
        try:
            async with self.session.delete(
                f"{self.server_url}/api/v1/diagnosis/worker/{self.node_id}"
            ) as response:
                if response.status == 200:
                    logger.info(f"节点 {self.node_id} 注销成功")
                else:
                    logger.warning(f"节点注销失败: {response.status}")
                    
        except Exception as e:
            logger.error(f"节点注销异常: {str(e)}")
            
    async def _heartbeat_loop(self):
        """心跳循环"""
        while self.running:
            try:
                await self._send_heartbeat()
                await asyncio.sleep(self.heartbeat_interval)
            except Exception as e:
                logger.error(f"心跳发送失败: {str(e)}")
                await asyncio.sleep(self.heartbeat_interval)
                
    async def _send_heartbeat(self):
        """发送心跳"""
        try:
            heartbeat_data = {
                'node_id': self.node_id,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'status': 'online',
                'current_tasks': len(self.current_tasks),
                'current_task_ids': list(self.current_tasks.keys()),
                'total_tasks_executed': self.stats['total_tasks_executed'],
                'system_info': self._get_system_info()
            }
            
            async with self.session.post(
                f"{self.server_url}/api/v1/diagnosis/worker/{self.node_id}/heartbeat",
                json=heartbeat_data
            ) as response:
                if response.status == 200:
                    self.last_heartbeat = datetime.now(timezone.utc)
                    logger.info(f"心跳发送成功: {self.node_id}")
                elif response.status == 404:
                    # 主服务重启导致节点未注册，自动重新注册
                    logger.warning(f"节点未注册(404)，尝试重新注册: {self.node_id}")
                    await self._register_node()
                else:
                    logger.warning(f"心跳发送失败: {response.status}")
                    
        except Exception as e:
            logger.error(f"心跳发送异常: {str(e)}")
            
    async def _task_polling_loop(self):
        """任务轮询循环"""
        while self.running:
            try:
                await self._poll_and_execute_tasks()
                await asyncio.sleep(self.task_fetch_interval)
            except Exception as e:
                logger.error(f"任务轮询失败: {str(e)}")
                await asyncio.sleep(self.task_fetch_interval)
                
    async def _poll_and_execute_tasks(self):
        """轮询并执行任务"""
        try:
            # 检查是否有可用的槽位
            if len(self.current_tasks) >= self.max_concurrent_tasks:
                return
                
            # 从主节点拉取任务
            tasks = await self._fetch_tasks()
            
            for task_data in tasks:
                task_id = task_data.get('id')
                if task_id and len(self.current_tasks) < self.max_concurrent_tasks:
                    # 异步执行任务
                    asyncio.create_task(self._execute_task(task_data))
                        
        except Exception as e:
            logger.error(f"任务轮询执行异常: {str(e)}")
    
    async def _execute_task(self, task_data: Dict):
        """执行单个任务"""
        task_id = task_data.get('id')
        if not task_id:
            return
            
        # 记录任务开始
        self.current_tasks[task_id] = {
            'start_time': datetime.now(timezone.utc),
            'task_data': task_data
        }
        self.stats['total_tasks_executed'] += 1
        
        logger.info(f"开始执行任务 {task_id}")
        
        try:
            # 获取数据库会话并执行诊断任务
            async for db in get_db():
                result = await self.diagnosis_executor.execute_task(task_id, db)
                break
            
            # 报告任务完成
            await self._report_task_completion(task_id, True, result)
            self.stats['tasks_completed'] += 1
            logger.info(f"任务 {task_id} 执行成功")
            
        except Exception as e:
            logger.error(f"任务 {task_id} 执行失败: {str(e)}")
            await self._report_task_completion(task_id, False, str(e))
            self.stats['tasks_failed'] += 1
            
        finally:
            # 清理任务记录
            if task_id in self.current_tasks:
                del self.current_tasks[task_id]
        
    async def _fetch_tasks(self) -> List[Dict[str, Any]]:
        """从主节点获取待执行的任务"""
        try:
            # 计算可获取的任务数量
            available_slots = self.max_concurrent_tasks - len(self.current_tasks)
            if available_slots <= 0:
                return []
            
            params = {
                'node_id': self.node_id,
                'max_tasks': min(available_slots, 5)  # 一次最多获取5个任务
            }
            
            async with self.session.get(
                f"{self.server_url}/api/v1/diagnosis/worker/tasks/fetch",
                params=params
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('tasks', [])
                elif response.status == 404:
                    # 主服务重启导致节点未注册，自动重新注册
                    logger.warning(f"节点未注册(404)，尝试重新注册: {self.node_id}")
                    await self._register_node()
                    return []
                else:
                    logger.warning(f"任务获取失败: {response.status}")
                    return []
                    
        except aiohttp.ServerDisconnectedError:
            # 服务器断开连接，静默处理
            if self.running:
                logger.debug("服务器连接断开，将在下次轮询时重连")
            return []
        except Exception as e:
            # 如果Worker正在停止，不记录连接错误
            if not self.running and "disconnected" in str(e).lower():
                return []
            logger.error(f"任务获取异常: {str(e)}")
            return []
    
    async def _report_task_completion(self, task_id: int, success: bool, result: Any = None):
        """报告任务完成状态"""
        try:
            completion_data = {
                'success': success,
                'result': result if success else None,
                'error': result if not success else None,
                'completed_at': datetime.now(timezone.utc).isoformat(),
                'worker_id': self.node_id
            }
            
            async with self.session.post(
                f"{self.server_url}/api/v1/diagnosis/worker/tasks/{task_id}/complete",
                json=completion_data
            ) as response:
                if response.status == 200:
                    logger.debug(f"任务 {task_id} 完成状态报告成功")
                else:
                    logger.warning(f"任务 {task_id} 完成状态报告失败: {response.status}")
                    
        except Exception as e:
            logger.error(f"报告任务 {task_id} 完成状态异常: {str(e)}")
            
async def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='分布式Worker节点')
    parser.add_argument('--server-url', default='http://localhost:8000', help='主服务器URL')
    parser.add_argument('--worker-pool-size', type=int, default=3, help='Worker池大小')
    parser.add_argument('--max-concurrent-tasks', type=int, default=2, help='最大并发任务数')
    parser.add_argument('--node-name', help='节点名称')
    parser.add_argument('--log-level', default='INFO', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], help='日志级别')
    
    args = parser.parse_args()
    
    # 配置日志
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 创建Worker客户端
    worker = DistributedWorkerClient(
        server_url=args.server_url,
        worker_pool_size=args.worker_pool_size,
        max_concurrent_tasks=args.max_concurrent_tasks,
        node_name=args.node_name
    )
    
    try:
        # 启动Worker
        await worker.start()
        
        # 保持运行
        logger.info("Worker节点正在运行，按Ctrl+C停止...")
        while worker.running:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("收到停止信号，正在关闭Worker节点...")
    except Exception as e:
        logger.error(f"Worker节点运行异常: {str(e)}")
    finally:
        await worker.stop()
        logger.info("Worker节点已停止")

if __name__ == '__main__':
    asyncio.run(main())