#!/usr/bin/env python3
"""
EasySight 分布式Worker节点测试脚本

用于测试worker节点的各项功能，包括：
1. 配置加载
2. 节点注册
3. 心跳发送
4. 任务拉取和执行
5. 状态监控

使用示例：
  python test_worker.py --test-config
  python test_worker.py --test-connection --master-host localhost
  python test_worker.py --test-all
"""

import asyncio
import argparse
import logging
import sys
import json
import aiohttp
from datetime import datetime
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from worker_config import WorkerConfig
from distributed_worker import DistributedWorkerClient, StandaloneWorkerNode

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class WorkerTester:
    """Worker节点测试器"""
    
    def __init__(self, master_host="localhost", master_port=8000):
        self.master_host = master_host
        self.master_port = master_port
        self.master_url = f"http://{master_host}:{master_port}/api/v1"
        
    async def test_config_loading(self):
        """测试配置加载"""
        logger.info("测试配置加载...")
        
        try:
            # 测试默认配置
            config = WorkerConfig()
            logger.info(f"默认配置加载成功: {config.node_id}")
            
            # 测试自定义配置
            custom_config = WorkerConfig(
                node_name="test-worker",
                worker_pool_size=2,
                master_host=self.master_host,
                master_port=self.master_port
            )
            logger.info(f"自定义配置加载成功: {custom_config.node_name}")
            
            return True
            
        except Exception as e:
            logger.error(f"配置加载失败: {str(e)}")
            return False
    
    async def test_master_connection(self):
        """测试主节点连接"""
        logger.info(f"测试主节点连接: {self.master_url}")
        
        try:
            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                # 测试健康检查接口
                async with session.get(f"http://{self.master_host}:{self.master_port}/health") as response:
                    if response.status == 200:
                        logger.info("主节点连接成功")
                        return True
                    else:
                        logger.error(f"主节点响应异常: {response.status}")
                        return False
                        
        except Exception as e:
            logger.error(f"主节点连接失败: {str(e)}")
            return False
    
    async def test_worker_registration(self):
        """测试Worker节点注册"""
        logger.info("测试Worker节点注册...")
        
        try:
            config = WorkerConfig(
                node_name="test-worker",
                master_host=self.master_host,
                master_port=self.master_port
            )
            
            # 创建测试用的注册数据
            node_info = {
                "node_id": config.node_id,
                "node_name": config.node_name,
                "worker_pool_size": config.worker_pool_size,
                "max_concurrent_tasks": config.max_concurrent_tasks,
                "capabilities": ["diagnosis"],
                "status": "online",
                "registered_at": datetime.utcnow().isoformat()
            }
            
            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                # 尝试注册节点
                async with session.post(
                    f"{self.master_url}/diagnosis/workers/register",
                    json=node_info
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info(f"节点注册成功: {result}")
                        
                        # 测试注销
                        async with session.delete(
                            f"{self.master_url}/diagnosis/workers/{config.node_id}"
                        ) as del_response:
                            if del_response.status == 200:
                                logger.info("节点注销成功")
                                return True
                            else:
                                logger.warning(f"节点注销失败: {del_response.status}")
                                return True  # 注册成功就算通过
                    else:
                        logger.error(f"节点注册失败: {response.status}")
                        return False
                        
        except Exception as e:
            logger.error(f"节点注册测试失败: {str(e)}")
            return False
    
    async def test_heartbeat(self):
        """测试心跳发送"""
        logger.info("测试心跳发送...")
        
        try:
            config = WorkerConfig(
                node_name="test-worker",
                master_host=self.master_host,
                master_port=self.master_port
            )
            
            # 先注册节点
            node_info = {
                "node_id": config.node_id,
                "node_name": config.node_name,
                "worker_pool_size": config.worker_pool_size,
                "max_concurrent_tasks": config.max_concurrent_tasks,
                "capabilities": ["diagnosis"],
                "status": "online",
                "registered_at": datetime.utcnow().isoformat()
            }
            
            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                # 注册节点
                async with session.post(
                    f"{self.master_url}/diagnosis/workers/register",
                    json=node_info
                ) as response:
                    if response.status != 200:
                        logger.error("节点注册失败，无法测试心跳")
                        return False
                
                # 发送心跳
                heartbeat_data = {
                    "node_id": config.node_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "status": "online",
                    "worker_status": {"active_workers": 3, "current_tasks": 0},
                    "system_info": {"cpu_percent": 25.5, "memory_percent": 60.2}
                }
                
                async with session.post(
                    f"{self.master_url}/diagnosis/workers/{config.node_id}/heartbeat",
                    json=heartbeat_data
                ) as response:
                    if response.status == 200:
                        logger.info("心跳发送成功")
                        
                        # 清理：注销节点
                        await session.delete(
                            f"{self.master_url}/diagnosis/workers/{config.node_id}"
                        )
                        return True
                    else:
                        logger.error(f"心跳发送失败: {response.status}")
                        return False
                        
        except Exception as e:
            logger.error(f"心跳测试失败: {str(e)}")
            return False
    
    async def test_standalone_worker(self):
        """测试独立Worker节点"""
        logger.info("测试独立Worker节点...")
        
        try:
            config = WorkerConfig(
                node_name="test-standalone-worker",
                worker_pool_size=1
            )
            
            # 创建独立Worker节点
            worker_node = StandaloneWorkerNode(config)
            
            # 启动Worker节点
            await worker_node.start()
            logger.info("独立Worker节点启动成功")
            
            # 检查状态
            status = worker_node.get_status()
            logger.info(f"Worker状态: {status}")
            
            # 停止Worker节点
            await worker_node.stop()
            logger.info("独立Worker节点停止成功")
            
            return True
            
        except Exception as e:
            logger.error(f"独立Worker测试失败: {str(e)}")
            return False
    
    async def test_distributed_worker_basic(self):
        """测试分布式Worker节点基本功能"""
        logger.info("测试分布式Worker节点基本功能...")
        
        try:
            config = WorkerConfig(
                node_name="test-distributed-worker",
                master_host=self.master_host,
                master_port=self.master_port,
                worker_pool_size=1
            )
            
            # 创建分布式Worker客户端
            worker_client = DistributedWorkerClient(config)
            
            # 测试启动（不实际运行循环）
            worker_client.running = True
            
            # 创建HTTP会话
            timeout = aiohttp.ClientTimeout(total=10)
            worker_client.session = aiohttp.ClientSession(timeout=timeout)
            
            # 测试注册
            await worker_client._register_node()
            logger.info("分布式Worker注册测试完成")
            
            # 测试心跳
            await worker_client._send_heartbeat()
            logger.info("分布式Worker心跳测试完成")
            
            # 清理
            await worker_client._unregister_node()
            await worker_client.session.close()
            
            return True
            
        except Exception as e:
            logger.error(f"分布式Worker测试失败: {str(e)}")
            return False
    
    async def run_all_tests(self):
        """运行所有测试"""
        logger.info("开始运行所有测试...")
        
        tests = [
            ("配置加载", self.test_config_loading),
            ("主节点连接", self.test_master_connection),
            ("Worker注册", self.test_worker_registration),
            ("心跳发送", self.test_heartbeat),
            ("独立Worker", self.test_standalone_worker),
            ("分布式Worker", self.test_distributed_worker_basic),
        ]
        
        results = []
        for test_name, test_func in tests:
            logger.info(f"\n{'='*50}")
            logger.info(f"运行测试: {test_name}")
            logger.info(f"{'='*50}")
            
            try:
                result = await test_func()
                results.append((test_name, result))
                
                if result:
                    logger.info(f"✅ {test_name} - 通过")
                else:
                    logger.error(f"❌ {test_name} - 失败")
                    
            except Exception as e:
                logger.error(f"❌ {test_name} - 异常: {str(e)}")
                results.append((test_name, False))
        
        # 输出测试结果摘要
        logger.info(f"\n{'='*50}")
        logger.info("测试结果摘要")
        logger.info(f"{'='*50}")
        
        passed = 0
        total = len(results)
        
        for test_name, result in results:
            status = "✅ 通过" if result else "❌ 失败"
            logger.info(f"{test_name}: {status}")
            if result:
                passed += 1
        
        logger.info(f"\n总计: {passed}/{total} 个测试通过")
        
        if passed == total:
            logger.info("🎉 所有测试都通过了！")
            return True
        else:
            logger.warning(f"⚠️  有 {total - passed} 个测试失败")
            return False

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="EasySight Worker节点测试工具",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "--master-host",
        type=str,
        default="localhost",
        help="主节点主机地址 (默认: localhost)"
    )
    
    parser.add_argument(
        "--master-port",
        type=int,
        default=8000,
        help="主节点端口 (默认: 8000)"
    )
    
    # 测试选项
    parser.add_argument(
        "--test-config",
        action="store_true",
        help="仅测试配置加载"
    )
    
    parser.add_argument(
        "--test-connection",
        action="store_true",
        help="仅测试主节点连接"
    )
    
    parser.add_argument(
        "--test-registration",
        action="store_true",
        help="仅测试节点注册"
    )
    
    parser.add_argument(
        "--test-heartbeat",
        action="store_true",
        help="仅测试心跳发送"
    )
    
    parser.add_argument(
        "--test-standalone",
        action="store_true",
        help="仅测试独立Worker"
    )
    
    parser.add_argument(
        "--test-distributed",
        action="store_true",
        help="仅测试分布式Worker"
    )
    
    parser.add_argument(
        "--test-all",
        action="store_true",
        help="运行所有测试"
    )
    
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="日志级别 (默认: INFO)"
    )
    
    return parser.parse_args()

async def main():
    """主函数"""
    args = parse_args()
    
    # 设置日志级别
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    
    # 创建测试器
    tester = WorkerTester(args.master_host, args.master_port)
    
    # 根据参数运行相应的测试
    if args.test_config:
        success = await tester.test_config_loading()
    elif args.test_connection:
        success = await tester.test_master_connection()
    elif args.test_registration:
        success = await tester.test_worker_registration()
    elif args.test_heartbeat:
        success = await tester.test_heartbeat()
    elif args.test_standalone:
        success = await tester.test_standalone_worker()
    elif args.test_distributed:
        success = await tester.test_distributed_worker_basic()
    elif args.test_all:
        success = await tester.run_all_tests()
    else:
        # 默认运行所有测试
        success = await tester.run_all_tests()
    
    # 返回适当的退出码
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"测试运行异常: {str(e)}")
        sys.exit(1)