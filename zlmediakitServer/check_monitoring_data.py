#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查数据库中的系统监控数据
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 直接导入需要的模块，避免循环导入
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
import config
from models import MediaProxy

async def check_monitoring_data():
    """检查数据库中的系统监控数据"""
    print("=== 检查数据库中的系统监控数据 ===")
    
    try:
        # 创建数据库引擎和会话（使用异步驱动）
        async_database_url = config.DATABASE_URL.replace('postgresql://', 'postgresql+asyncpg://')
        engine = create_async_engine(async_database_url)
        AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        
        async with AsyncSessionLocal() as session:
            # 查询媒体节点信息
            stmt = select(MediaProxy).where(
                MediaProxy.ip_address == '127.0.0.1',
                MediaProxy.port == config.MEDIA_NODE_PORT
            )
            result = await session.execute(stmt)
            proxy = result.scalar_one_or_none()
            
            if proxy:
                print(f"\n节点信息:")
                print(f"  节点名称: {proxy.name}")
                print(f"  IP地址: {proxy.ip_address}")
                print(f"  端口: {proxy.port}")
                print(f"  在线状态: {proxy.is_online}")
                print(f"  CPU使用率: {proxy.cpu_usage}%" if proxy.cpu_usage is not None else "  CPU使用率: 未设置")
                print(f"  内存使用率: {proxy.memory_usage}%" if proxy.memory_usage is not None else "  内存使用率: 未设置")
                print(f"  带宽使用率: {proxy.bandwidth_usage}MB/s" if proxy.bandwidth_usage is not None else "  带宽使用率: 未设置")
                print(f"  最大连接数: {proxy.max_connections}")
                print(f"  当前连接数: {proxy.current_connections}" if proxy.current_connections is not None else "  当前连接数: 未设置")
                print(f"  最后心跳: {proxy.last_heartbeat}")
                
                # 检查系统监控数据是否已更新
                if proxy.cpu_usage is not None and proxy.memory_usage is not None:
                    print("\n✓ 系统监控数据已正确更新")
                    return True
                else:
                    print("\n✗ 系统监控数据未更新")
                    return False
            else:
                print("\n✗ 未找到媒体节点")
                return False
                
    except Exception as e:
        print(f"\n✗ 检查失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(check_monitoring_data())
    if result:
        print("\n=== 系统监控数据检查通过 ===")
    else:
        print("\n=== 系统监控数据检查失败 ===")
        sys.exit(1)