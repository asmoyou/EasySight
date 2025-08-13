#!/usr/bin/env python3
"""
RabbitMQ版本的EasySight智能安防平台启动脚本

使用方法:
    python start_rabbitmq.py

功能:
    - 启动基于RabbitMQ的任务调度系统
    - 实时任务分发
    - 事件驱动架构
    - 高可用性和稳定性
"""

import sys
import os
import asyncio
import uvicorn
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def check_rabbitmq_connection():
    """检查RabbitMQ连接"""
    import socket
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex(('127.0.0.1', 5672))
        sock.close()
        return result == 0
    except Exception:
        return False

def main():
    """主函数"""
    print("="*60)
    print("🚀 启动 EasySight 智能安防平台 (RabbitMQ版)")
    print("="*60)
    
    # 检查RabbitMQ连接
    print("🔍 检查RabbitMQ连接...")
    if not check_rabbitmq_connection():
        print("❌ RabbitMQ连接失败！")
        print("请确保RabbitMQ服务正在运行在 127.0.0.1:5672")
        print("启动命令: rabbitmq-server")
        sys.exit(1)
    else:
        print("✅ RabbitMQ连接正常")
    
    print("\n🔧 配置信息:")
    print(f"   - 项目根目录: {project_root}")
    print(f"   - 主服务文件: main_rabbitmq.py")
    print(f"   - 监听地址: 0.0.0.0:8000")
    print(f"   - RabbitMQ地址: 127.0.0.1:5672")
    
    print("\n🌟 新功能特性:")
    print("   ✨ RabbitMQ任务队列")
    print("   ✨ 实时任务分发")
    print("   ✨ 事件驱动架构")
    print("   ✨ 高可用性和稳定性")
    print("   ✨ Worker负载均衡")
    
    print("\n🔗 API接口:")
    print("   - 主页: http://localhost:8000")
    print("   - API文档: http://localhost:8000/docs")
    print("   - 健康检查: http://localhost:8000/health")
    print("   - RabbitMQ状态: http://localhost:8000/api/v1/rabbitmq/status")
    print("   - 队列状态: http://localhost:8000/api/v1/diagnosis/queue/status")
    
    print("\n🎯 管理员账号:")
    print("   - 用户名: admin")
    print("   - 密码: admin123")
    
    print("\n" + "="*60)
    print("🚀 正在启动服务...")
    print("="*60)
    
    try:
        # 启动服务
        uvicorn.run(
            "main_rabbitmq:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info",
            access_log=True
        )
    except KeyboardInterrupt:
        print("\n\n🛑 服务已停止")
    except Exception as e:
        print(f"\n\n❌ 服务启动失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()