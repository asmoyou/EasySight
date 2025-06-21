#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建默认管理员用户
"""

import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import get_db, async_engine
from models.user import User
from config import settings

async def create_default_admin():
    """创建默认管理员用户"""
    try:
        # 创建数据库会话
        async with AsyncSession(async_engine) as db:
            # 检查是否已存在admin用户
            result = await db.execute(select(User).where(User.username == "admin"))
            existing_user = result.scalar_one_or_none()
            
            if existing_user:
                print("管理员用户已存在")
                print(f"用户名: admin")
                print(f"如需重置密码，请使用系统管理功能")
                return
            
            # 创建默认管理员用户
            admin_user = User(
                username="admin",
                email="admin@easysight.com",
                full_name="系统管理员",
                is_active=True,
                is_superuser=True,
                is_verified=True,
                roles=["admin", "superuser"],
                permissions=["*"],  # 所有权限
                language="zh-CN",
                description="系统默认管理员账户"
            )
            
            # 设置默认密码
            default_password = "admin123"
            admin_user.set_password(default_password)
            
            # 保存到数据库
            db.add(admin_user)
            await db.commit()
            await db.refresh(admin_user)
            
            print("默认管理员用户创建成功！")
            print(f"用户名: admin")
            print(f"密码: {default_password}")
            print("请登录后立即修改密码！")
            
    except Exception as e:
        print(f"创建管理员用户失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(create_default_admin())