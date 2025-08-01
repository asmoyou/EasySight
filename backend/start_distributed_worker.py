#!/usr/bin/env python3
"""
EasySight 分布式Worker节点启动脚本

这是一个功能完整的分布式Worker启动器，支持：
- 灵活的命令行参数配置
- 环境变量和配置文件支持
- 完善的日志系统
- 优雅的关闭处理
- 错误恢复机制

使用示例:
    # 基本启动
    python start_distributed_worker.py
    
    # 连接远程服务器
    python start_distributed_worker.py --server-url http://192.168.1.100:8000
    
    # 自定义配置
    python start_distributed_worker.py --worker-pool-size 5 --max-concurrent-tasks 4 --node-name MyWorker
    
    # 使用配置文件
    python start_distributed_worker.py --config worker.env
    
    # 调试模式
    python start_distributed_worker.py --log-level DEBUG --log-file worker.log
"""

import asyncio
import logging
import argparse
import signal
import sys
import os
from pathlib import Path
from typing import Optional

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from distributed_worker import DistributedWorkerClient

def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None):
    """配置日志系统"""
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    handlers = [logging.StreamHandler(sys.stdout)]
    if log_file:
        handlers.append(logging.FileHandler(log_file, encoding='utf-8'))
    
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format=log_format,
        handlers=handlers,
        force=True  # 强制重新配置
    )

def load_config_from_file(config_file: str) -> dict:
    """从配置文件加载配置"""
    config = {}
    if os.path.exists(config_file):
        with open(config_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    config[key.strip()] = value.strip()
    return config

class WorkerManager:
    """Worker节点管理器"""
    
    def __init__(self):
        self.worker = None
        self.shutdown_event = asyncio.Event()
        self.logger = logging.getLogger(__name__)
        
    async def start_worker(self, **kwargs):
        """启动Worker节点"""
        try:
            # 只传递 DistributedWorkerClient 支持的参数
            client_kwargs = {
                'server_url': kwargs.get('server_url', 'http://localhost:8000'),
                'worker_pool_size': kwargs.get('worker_pool_size', 3),
                'max_concurrent_tasks': kwargs.get('max_concurrent_tasks', 2),
                'node_name': kwargs.get('node_name')
            }
            
            # 移除None值
            client_kwargs = {k: v for k, v in client_kwargs.items() if v is not None}
            
            self.worker = DistributedWorkerClient(**client_kwargs)
            
            # 如果有额外的配置参数，可以在这里设置到worker实例上
            if 'task_poll_interval' in kwargs:
                self.worker.task_fetch_interval = kwargs['task_poll_interval']
            if 'heartbeat_interval' in kwargs:
                self.worker.heartbeat_interval = kwargs['heartbeat_interval']
            if 'max_retries' in kwargs:
                self.worker.max_retry_attempts = kwargs['max_retries']
                
            await self.worker.start()
            self.logger.info("Worker节点启动成功")
            
            # 等待关闭信号
            await self.shutdown_event.wait()
            
        except Exception as e:
            self.logger.error(f"Worker节点启动失败: {str(e)}")
            raise
        finally:
            await self.stop_worker()
            
    async def stop_worker(self):
        """停止Worker节点"""
        if self.worker:
            self.logger.info("正在停止Worker节点...")
            try:
                await self.worker.stop()
                self.logger.info("Worker节点已停止")
            except Exception as e:
                self.logger.error(f"停止Worker节点时出错: {str(e)}")
                
    def shutdown(self):
        """触发关闭"""
        self.logger.info("收到关闭信号")
        self.shutdown_event.set()

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description='EasySight 分布式Worker节点启动器',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  基本启动:
    %(prog)s
    
  连接到远程服务器:
    %(prog)s --server-url http://192.168.1.100:8000
    
  自定义配置:
    %(prog)s --worker-pool-size 5 --max-concurrent-tasks 4 --node-name MyWorker
    
  使用配置文件:
    %(prog)s --config worker.env
    
  调试模式:
    %(prog)s --log-level DEBUG --log-file worker.log
    
  完整配置示例:
    %(prog)s --server-url http://192.168.1.100:8000 \\
             --worker-pool-size 5 \\
             --max-concurrent-tasks 3 \\
             --node-name ProductionWorker \\
             --heartbeat-interval 30 \\
             --task-poll-interval 5 \\
             --log-level INFO \\
             --log-file /var/log/worker.log
        """
    )
    
    # 基本配置
    parser.add_argument(
        '--config',
        type=str,
        help='配置文件路径 (.env格式)'
    )
    
    # 服务器连接配置
    parser.add_argument(
        '--server-url', 
        default='http://localhost:8000', 
        help='主服务器URL (默认: http://localhost:8000)'
    )
    
    parser.add_argument(
        '--api-token',
        type=str,
        help='API认证令牌'
    )
    
    # Worker配置
    parser.add_argument(
        '--worker-pool-size', 
        type=int, 
        default=3, 
        help='Worker池大小 (默认: 3)'
    )
    
    parser.add_argument(
        '--max-concurrent-tasks', 
        type=int, 
        default=2, 
        help='每个Worker最大并发任务数 (默认: 2)'
    )
    
    parser.add_argument(
        '--node-name', 
        help='节点名称 (默认: Worker-<hostname>)'
    )
    
    parser.add_argument(
        '--node-id',
        type=str,
        help='节点ID (默认自动生成)'
    )
    
    # 任务配置
    parser.add_argument(
        '--task-poll-interval',
        type=int,
        default=5,
        help='任务轮询间隔（秒） (默认: 5)'
    )
    
    parser.add_argument(
        '--heartbeat-interval',
        type=int,
        default=30,
        help='心跳间隔（秒） (默认: 30)'
    )
    
    parser.add_argument(
        '--max-retries',
        type=int,
        default=3,
        help='最大重试次数 (默认: 3)'
    )
    
    # 日志配置
    parser.add_argument(
        '--log-level', 
        default='INFO', 
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], 
        help='日志级别 (默认: INFO)'
    )
    
    parser.add_argument(
        '--log-file',
        type=str,
        help='日志文件路径 (默认: 仅控制台输出)'
    )
    
    # 性能配置
    parser.add_argument(
        '--enable-metrics',
        action='store_true',
        help='启用性能指标收集'
    )
    
    parser.add_argument(
        '--metrics-port',
        type=int,
        default=9090,
        help='指标服务端口 (默认: 9090)'
    )
    
    return parser.parse_args()

async def main():
    """主函数"""
    args = parse_args()
    
    # 从配置文件加载配置
    config = {}
    if args.config:
        config = load_config_from_file(args.config)
        
    # 命令行参数覆盖配置文件
    worker_config = {
        'server_url': args.server_url,
        'worker_pool_size': args.worker_pool_size,
        'max_concurrent_tasks': args.max_concurrent_tasks,
        'node_name': args.node_name,
        'node_id': getattr(args, 'node_id', None),
        'task_poll_interval': getattr(args, 'task_poll_interval', 5),
        'heartbeat_interval': getattr(args, 'heartbeat_interval', 30),
        'max_retries': getattr(args, 'max_retries', 3),
        'api_token': getattr(args, 'api_token', None),
        'enable_metrics': getattr(args, 'enable_metrics', False),
        'metrics_port': getattr(args, 'metrics_port', 9090)
    }
    
    # 应用配置文件中的设置
    for key, value in config.items():
        if key in worker_config and value:
            # 类型转换
            if key in ['worker_pool_size', 'max_concurrent_tasks', 'task_poll_interval', 
                      'heartbeat_interval', 'max_retries', 'metrics_port']:
                worker_config[key] = int(value)
            elif key == 'enable_metrics':
                worker_config[key] = value.lower() in ('true', '1', 'yes')
            else:
                worker_config[key] = value
    
    # 移除None值
    worker_config = {k: v for k, v in worker_config.items() if v is not None}
    
    # 配置日志
    setup_logging(args.log_level, args.log_file)
    logger = logging.getLogger(__name__)
    
    # 显示启动信息
    logger.info("=" * 70)
    logger.info("EasySight 分布式Worker节点启动器")
    logger.info("=" * 70)
    logger.info(f"服务器URL: {worker_config['server_url']}")
    logger.info(f"Worker池大小: {worker_config['worker_pool_size']}")
    logger.info(f"最大并发任务数: {worker_config['max_concurrent_tasks']}")
    logger.info(f"节点名称: {worker_config.get('node_name', 'Worker-<hostname>')}")
    logger.info(f"任务轮询间隔: {worker_config.get('task_poll_interval', 5)}秒")
    logger.info(f"心跳间隔: {worker_config.get('heartbeat_interval', 30)}秒")
    logger.info(f"最大重试次数: {worker_config.get('max_retries', 3)}")
    logger.info(f"日志级别: {args.log_level}")
    if args.log_file:
        logger.info(f"日志文件: {args.log_file}")
    if args.config:
        logger.info(f"配置文件: {args.config}")
    logger.info("=" * 70)
    
    # 创建Worker管理器
    manager = WorkerManager()
    
    # 设置信号处理
    def signal_handler(signum, frame):
        logger.info(f"收到信号 {signum}，正在关闭...")
        manager.shutdown()
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # 启动Worker
        logger.info("正在启动Worker节点...")
        await manager.start_worker(**worker_config)
        
    except KeyboardInterrupt:
        logger.info("收到键盘中断，正在关闭...")
    except Exception as e:
        logger.error(f"Worker节点运行异常: {str(e)}")
        raise
    finally:
        logger.info("Worker节点已退出")
        logger.info("=" * 70)

if __name__ == '__main__':
    # 检查Python版本
    if sys.version_info < (3, 7):
        print("错误: 需要Python 3.7或更高版本")
        sys.exit(1)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n程序被用户中断")
        sys.exit(0)
    except Exception as e:
        print(f"启动失败: {str(e)}")
        sys.exit(1)