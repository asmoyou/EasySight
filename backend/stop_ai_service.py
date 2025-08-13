#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
停止AI服务
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import get_db
from models.ai_algorithm import AIService, ServiceStatus
from sqlalchemy import select

async def stop_ai_service_by_id(service_id: int):
    """停止指定ID的AI服务"""
    try:
        async for db in get_db():
            # 获取服务信息
            result = await db.execute(
                select(AIService).where(AIService.id == service_id)
            )
            service = result.scalar_one_or_none()
            
            if not service:
                print(f"服务 {service_id} 不存在")
                return False
            
            print(f"当前服务状态: {service.status}")
            
            if service.status == ServiceStatus.STOPPED:
                print(f"服务 {service_id} 已经停止")
                return True
            
            # 更新服务状态为停止
            service.status = ServiceStatus.STOPPED
            service.is_running = False
            service.is_active = False
            
            await db.commit()
            
            print(f"✓ AI服务 {service_id} ({service.name}) 已停止")
            return True
            
    except Exception as e:
        print(f"停止AI服务时发生错误: {str(e)}")
        return False

async def list_ai_services():
    """列出所有AI服务"""
    try:
        async for db in get_db():
            result = await db.execute(select(AIService))
            services = result.scalars().all()
            
            print(f"找到 {len(services)} 个AI服务:")
            for service in services:
                print(f"  ID: {service.id}, 名称: {service.name}, 状态: {service.status}")
            
            break
            
    except Exception as e:
        print(f"获取AI服务列表时发生错误: {str(e)}")

async def main():
    """主函数"""
    print("=== AI服务停止工具 ===")
    
    # 列出所有服务
    await list_ai_services()
    
    # 停止第一个找到的服务（通常是ID=4的test服务）
    service_id = 4
    print(f"\n正在停止服务 ID: {service_id}")
    
    success = await stop_ai_service_by_id(service_id)
    
    if success:
        print("\n服务停止成功！")
    else:
        print("\n服务停止失败！")

if __name__ == "__main__":
    asyncio.run(main())