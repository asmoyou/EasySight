#!/usr/bin/env python3
"""
测试Worker重连机制

这个脚本用于测试当主服务重启时，Worker节点是否能够自动重新连接和注册。
"""

import asyncio
import logging
import time
from datetime import datetime

from distributed_worker import DistributedWorkerClient
from worker_config import WorkerConfig

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_worker_reconnect():
    """测试Worker重连机制"""
    
    # 创建测试配置
    config = WorkerConfig(
        node_id="test-worker-001",
        node_name="测试Worker节点",
        worker_pool_size=2,
        max_concurrent_tasks=2,
        master_host="localhost",
        master_port=8000,
        heartbeat_interval=10,  # 缩短心跳间隔用于测试
        task_poll_interval=5
    )
    
    # 创建Worker客户端
    worker_client = DistributedWorkerClient(config)
    
    try:
        logger.info("启动Worker客户端...")
        await worker_client.start()
        
        logger.info("Worker客户端已启动，开始监控连接状态...")
        logger.info("请在另一个终端中重启主服务来测试重连机制")
        logger.info("观察日志中是否出现自动重新注册的信息")
        
        # 运行一段时间来观察重连行为
        start_time = time.time()
        while time.time() - start_time < 300:  # 运行5分钟
            await asyncio.sleep(10)
            
            # 显示当前状态
            if worker_client.last_heartbeat:
                last_heartbeat_ago = (datetime.now().replace(tzinfo=None) - 
                                    worker_client.last_heartbeat.replace(tzinfo=None)).total_seconds()
                logger.info(f"最后心跳: {last_heartbeat_ago:.1f}秒前")
            else:
                logger.info("尚未收到心跳响应")
                
    except KeyboardInterrupt:
        logger.info("收到中断信号，停止测试...")
    except Exception as e:
        logger.error(f"测试过程中发生错误: {str(e)}")
    finally:
        logger.info("停止Worker客户端...")
        await worker_client.stop()
        logger.info("测试完成")

if __name__ == "__main__":
    print("Worker重连机制测试")
    print("=" * 50)
    print("测试步骤:")
    print("1. 确保主服务正在运行 (python main.py)")
    print("2. 启动此测试脚本")
    print("3. 在另一个终端中重启主服务")
    print("4. 观察Worker是否自动重新连接")
    print("=" * 50)
    
    asyncio.run(test_worker_reconnect())