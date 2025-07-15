#!/usr/bin/env python3
"""
独立Worker节点启动脚本

支持两种模式：
1. 分布式模式：连接到主节点，自动拉取任务
2. 独立模式：仅启动Worker池，通过API接收任务

使用示例：
  # 分布式模式
  python start_worker.py --mode distributed --master-host 192.168.1.100 --pool-size 5
  
  # 独立模式
  python start_worker.py --mode standalone --pool-size 3
  
  # 使用配置文件
  python start_worker.py --config worker.env
"""

import asyncio
import argparse
import logging
import signal
import sys
import os
from pathlib import Path
from typing import Optional

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from worker_config import WorkerConfig, worker_config
from distributed_worker import DistributedWorkerClient, StandaloneWorkerNode

# 配置日志
def setup_logging(level: str = "INFO", log_file: Optional[str] = None):
    """配置日志系统"""
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    handlers = [logging.StreamHandler(sys.stdout)]
    if log_file:
        handlers.append(logging.FileHandler(log_file))
    
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format=log_format,
        handlers=handlers
    )

class WorkerNodeManager:
    """Worker节点管理器"""
    
    def __init__(self, config: WorkerConfig, mode: str = "distributed"):
        self.config = config
        self.mode = mode
        self.worker_node = None
        self.shutdown_event = asyncio.Event()
        
    async def start(self):
        """启动Worker节点"""
        logger = logging.getLogger(__name__)
        
        try:
            # 根据模式创建Worker节点
            if self.mode == "distributed":
                self.worker_node = DistributedWorkerClient(self.config)
                logger.info(f"启动分布式Worker节点，连接到主节点: {self.config.master_host}:{self.config.master_port}")
            elif self.mode == "standalone":
                self.worker_node = StandaloneWorkerNode(self.config)
                logger.info("启动独立Worker节点")
            else:
                raise ValueError(f"不支持的模式: {self.mode}")
            
            # 启动Worker节点
            await self.worker_node.start()
            
            # 等待关闭信号
            await self.shutdown_event.wait()
            
        except Exception as e:
            logger.error(f"Worker节点启动失败: {str(e)}")
            raise
        finally:
            await self.stop()
            
    async def stop(self):
        """停止Worker节点"""
        logger = logging.getLogger(__name__)
        
        if self.worker_node:
            logger.info("正在停止Worker节点...")
            await self.worker_node.stop()
            logger.info("Worker节点已停止")
            
    def shutdown(self):
        """触发关闭"""
        self.shutdown_event.set()

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="EasySight 分布式Worker节点启动器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s --mode distributed --master-host 192.168.1.100 --pool-size 5
  %(prog)s --mode standalone --pool-size 3 --log-level DEBUG
  %(prog)s --config /path/to/worker.env
        """
    )
    
    # 基本参数
    parser.add_argument(
        "--mode", 
        choices=["distributed", "standalone"],
        default="distributed",
        help="Worker运行模式 (默认: distributed)"
    )
    
    parser.add_argument(
        "--config",
        type=str,
        help="配置文件路径"
    )
    
    # Worker配置
    parser.add_argument(
        "--node-id",
        type=str,
        help="节点ID（默认自动生成）"
    )
    
    parser.add_argument(
        "--node-name",
        type=str,
        default="worker-node",
        help="节点名称 (默认: worker-node)"
    )
    
    parser.add_argument(
        "--pool-size",
        type=int,
        default=3,
        help="Worker池大小 (默认: 3)"
    )
    
    parser.add_argument(
        "--max-concurrent-tasks",
        type=int,
        default=3,
        help="每个Worker最大并发任务数 (默认: 3)"
    )
    
    # 主节点连接配置
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
    
    parser.add_argument(
        "--api-token",
        type=str,
        help="API认证令牌"
    )
    
    # 日志配置
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="日志级别 (默认: INFO)"
    )
    
    parser.add_argument(
        "--log-file",
        type=str,
        help="日志文件路径"
    )
    
    # 任务配置
    parser.add_argument(
        "--task-poll-interval",
        type=int,
        default=5,
        help="任务轮询间隔（秒） (默认: 5)"
    )
    
    parser.add_argument(
        "--heartbeat-interval",
        type=int,
        default=30,
        help="心跳间隔（秒） (默认: 30)"
    )
    
    return parser.parse_args()

def load_config_from_args(args) -> WorkerConfig:
    """从命令行参数加载配置"""
    config_dict = {}
    
    # 如果指定了配置文件，先加载配置文件
    if args.config:
        if os.path.exists(args.config):
            # 简单的.env文件解析
            with open(args.config, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        config_dict[key.strip()] = value.strip()
    
    # 命令行参数覆盖配置文件
    if args.node_id:
        config_dict['node_id'] = args.node_id
    if args.node_name:
        config_dict['node_name'] = args.node_name
    if args.pool_size:
        config_dict['worker_pool_size'] = args.pool_size
    if args.max_concurrent_tasks:
        config_dict['max_concurrent_tasks'] = args.max_concurrent_tasks
    if args.master_host:
        config_dict['master_host'] = args.master_host
    if args.master_port:
        config_dict['master_port'] = args.master_port
    if args.api_token:
        config_dict['api_token'] = args.api_token
    if args.log_level:
        config_dict['log_level'] = args.log_level
    if args.log_file:
        config_dict['log_file'] = args.log_file
    if args.task_poll_interval:
        config_dict['task_poll_interval'] = args.task_poll_interval
    if args.heartbeat_interval:
        config_dict['heartbeat_interval'] = args.heartbeat_interval
    
    return WorkerConfig(**config_dict)

async def main():
    """主函数"""
    args = parse_args()
    
    # 加载配置
    config = load_config_from_args(args)
    
    # 配置日志
    setup_logging(config.log_level, config.log_file)
    
    logger = logging.getLogger(__name__)
    logger.info(f"启动EasySight Worker节点 - 模式: {args.mode}")
    logger.info(f"节点ID: {config.node_id}")
    logger.info(f"Worker池大小: {config.worker_pool_size}")
    
    if args.mode == "distributed":
        logger.info(f"主节点地址: {config.master_host}:{config.master_port}")
    
    # 创建Worker节点管理器
    manager = WorkerNodeManager(config, args.mode)
    
    # 设置信号处理
    def signal_handler(signum, frame):
        logger.info(f"收到信号 {signum}，正在关闭...")
        manager.shutdown()
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # 启动Worker节点
        await manager.start()
    except KeyboardInterrupt:
        logger.info("收到键盘中断，正在关闭...")
    except Exception as e:
        logger.error(f"Worker节点运行异常: {str(e)}")
        sys.exit(1)
    
    logger.info("Worker节点已退出")

if __name__ == "__main__":
    # 检查Python版本
    if sys.version_info < (3, 7):
        print("错误: 需要Python 3.7或更高版本")
        sys.exit(1)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n程序被用户中断")
        sys.exit(0)