import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, text
from config import Settings

settings = Settings()

# 创建异步数据库引擎
engine = create_async_engine(
    settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"),
    echo=True
)

AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

async def check_database_roles():
    """检查数据库中的角色和用户角色关联数据"""
    async with AsyncSessionLocal() as db:
        try:
            # 检查所有角色
            print("=== 检查所有角色 ===")
            result = await db.execute(text("SELECT id, name, display_name, is_active, page_permissions FROM roles"))
            roles = result.fetchall()
            
            if not roles:
                print("数据库中没有角色数据!")
            else:
                for role in roles:
                    print(f"角色ID: {role[0]}, 名称: {role[1]}, 显示名: {role[2]}, 激活: {role[3]}")
                    print(f"页面权限: {role[4]}")
                    print("-" * 50)
            
            # 检查用户
            print("\n=== 检查用户 ===")
            result = await db.execute(text("SELECT id, username, is_active FROM users"))
            users = result.fetchall()
            
            if not users:
                print("数据库中没有用户数据!")
            else:
                for user in users:
                    print(f"用户ID: {user[0]}, 用户名: {user[1]}, 激活: {user[2]}")
            
            # 检查用户角色关联
            print("\n=== 检查用户角色关联 ===")
            result = await db.execute(text("""
                SELECT ur.user_id, ur.role_id, ur.is_active, u.username, r.name as role_name
                FROM user_roles ur
                JOIN users u ON ur.user_id = u.id
                JOIN roles r ON ur.role_id = r.id
            """))
            user_roles = result.fetchall()
            
            if not user_roles:
                print("数据库中没有用户角色关联数据!")
            else:
                for ur in user_roles:
                    print(f"用户: {ur[3]} (ID: {ur[0]}) -> 角色: {ur[4]} (ID: {ur[1]}), 激活: {ur[2]}")
            
            # 检查admin用户的具体情况
            print("\n=== 检查admin用户的角色权限 ===")
            result = await db.execute(text("""
                SELECT r.name, r.page_permissions, ur.is_active
                FROM users u
                JOIN user_roles ur ON u.id = ur.user_id
                JOIN roles r ON ur.role_id = r.id
                WHERE u.username = 'admin'
            """))
            admin_roles = result.fetchall()
            
            if not admin_roles:
                print("admin用户没有分配角色!")
            else:
                for role in admin_roles:
                    print(f"角色: {role[0]}, 关联激活: {role[2]}")
                    print(f"页面权限: {role[1]}")
                    
        except Exception as e:
            print(f"检查失败: {e}")
        finally:
            await db.close()

if __name__ == "__main__":
    asyncio.run(check_database_roles())