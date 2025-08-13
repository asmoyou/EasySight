#!/usr/bin/env python3
"""
RabbitMQ版本的分布式Worker启动脚本

使用方法:
    python start_rabbitmq_worker.py [worker_id]

参数:
    worker_id: 可选，Worker的唯一标识符，默认自动生成

功能:
    - 启动基于RabbitMQ的分布式Worker
    - 实时接收任务
    - 自动负载均衡
    - 心跳监控
"""

import sys
import os
import asyncio
import uuid
import socket
from pathlib import Path
from datetime import datetime

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def get_local_ip():
    """获取本机IP地址"""
    try:
        # 连接到一个远程地址来获取本机IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def check_rabbitmq_connection():
    """检查RabbitMQ连接"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex(('127.0.0.1', 5672))
        sock.close()
        return result == 0
    except Exception:
        return False

def check_main_service():
    """检查主服务连接"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex(('127.0.0.1', 8000))
        sock.close()
        return result == 0
    except Exception:
        return False

async def main():
    """主函数"""
    print("="*60)
    print("🤖 启动 EasySight 分布式Worker (RabbitMQ版)")
    print("="*60)
    
    # 获取Worker ID
    worker_id = sys.argv[1] if len(sys.argv) > 1 else f"worker-{uuid.uuid4().hex[:8]}"
    local_ip = get_local_ip()
    
    print(f"🆔 Worker ID: {worker_id}")
    print(f"🌐 本机IP: {local_ip}")
    print(f"⏰ 启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 检查依赖服务
    print("\n🔍 检查依赖服务...")
    
    if not check_rabbitmq_connection():
        print("❌ RabbitMQ连接失败！")
        print("请确保RabbitMQ服务正在运行在 127.0.0.1:5672")
        sys.exit(1)
    else:
        print("✅ RabbitMQ连接正常")
    
    if not check_main_service():
        print("❌ 主服务连接失败！")
        print("请确保主服务正在运行在 127.0.0.1:8000")
        print("启动命令: python start_rabbitmq.py")
        sys.exit(1)
    else:
        print("✅ 主服务连接正常")
    
    print("\n🔧 Worker配置:")
    print(f"   - Worker ID: {worker_id}")
    print(f"   - 主机地址: {local_ip}")
    print(f"   - 最大并发任务: 3")
    print(f"   - 支持的任务类型: 诊断任务, 事件任务, AI服务任务")
    
    print("\n🌟 新功能特性:")
    print("   ✨ RabbitMQ消息队列")
    print("   ✨ 实时任务接收")
    print("   ✨ 自动负载均衡")
    print("   ✨ 心跳监控")
    print("   ✨ 故障自动恢复")
    
    print("\n" + "="*60)
    print("🚀 正在启动Worker...")
    print("="*60)
    
    try:
        # 导入并启动RabbitMQ Worker
        from rabbitmq_distributed_worker import RabbitMQDistributedWorker
        from task_queue_manager import TaskQueueManager
        
        # 创建任务队列管理器
        task_queue_manager = TaskQueueManager()
        
        # 创建Worker配置
        from worker_config import WorkerConfig
        config = WorkerConfig()
        config.max_concurrent_tasks = 3
        config.master_host = "127.0.0.1"
        config.master_port = 8000
        
        # 创建Worker实例
        worker = RabbitMQDistributedWorker(
            worker_id=worker_id,
            config=config
        )
        
        print(f"✅ Worker {worker_id} 已创建")
        
        # 启动Worker
        await worker.start()
        
        print(f"🎉 Worker {worker_id} 启动成功！")
        print("\n📊 Worker状态:")
        print(f"   - 状态: 运行中")
        print(f"   - 当前任务数: 0")
        print(f"   - 等待任务分配...")
        
        # 保持运行
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print(f"\n\n🛑 正在停止Worker {worker_id}...")
            await worker.stop()
            print(f"✅ Worker {worker_id} 已停止")
            
    except Exception as e:
        print(f"\n\n❌ Worker启动失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    # 配置日志
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n🛑 Worker已停止")
    except Exception as e:
        print(f"\n\n❌ 启动失败: {e}")
        sys.exit(1)