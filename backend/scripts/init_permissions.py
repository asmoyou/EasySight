#!/usr/bin/env python3
"""
初始化系统权限和角色数据
"""

import asyncio
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import AsyncSessionLocal
from models.role import Role, Permission, UserRole
from models.user import User

# 系统权限定义
SYSTEM_PERMISSIONS = [
    # 用户管理权限
    {
        "name": "user:list",
        "display_name": "查看用户列表",
        "description": "查看系统用户列表",
        "category": "用户管理",
        "module": "system",
        "permission_type": "action",
        "is_system": False
    },
    {
        "name": "user:create",
        "display_name": "创建用户",
        "description": "创建新用户",
        "category": "用户管理",
        "module": "system",
        "permission_type": "action",
        "is_system": False
    },
    {
        "name": "user:update",
        "display_name": "编辑用户",
        "description": "编辑用户信息",
        "category": "用户管理",
        "module": "system",
        "permission_type": "action",
        "is_system": False
    },
    {
        "name": "user:delete",
        "display_name": "删除用户",
        "description": "删除用户",
        "category": "用户管理",
        "module": "system",
        "permission_type": "action",
        "is_system": False
    },
    
    # 角色管理权限
    {
        "name": "role:list",
        "display_name": "查看角色列表",
        "description": "查看系统角色列表",
        "category": "角色管理",
        "module": "system",
        "permission_type": "action",
        "is_system": False
    },
    {
        "name": "role:create",
        "display_name": "创建角色",
        "description": "创建新角色",
        "category": "角色管理",
        "module": "system",
        "permission_type": "action",
        "is_system": False
    },
    {
        "name": "role:update",
        "display_name": "编辑角色",
        "description": "编辑角色信息和权限",
        "category": "角色管理",
        "module": "system",
        "permission_type": "action",
        "is_system": False
    },
    {
        "name": "role:delete",
        "display_name": "删除角色",
        "description": "删除角色",
        "category": "角色管理",
        "module": "system",
        "permission_type": "action",
        "is_system": False
    },
    
    # 摄像头管理权限
    {
        "name": "camera:list",
        "display_name": "查看摄像头列表",
        "description": "查看摄像头列表",
        "category": "摄像头管理",
        "module": "camera",
        "permission_type": "action",
        "is_system": False
    },
    {
        "name": "camera:create",
        "display_name": "添加摄像头",
        "description": "添加新摄像头",
        "category": "摄像头管理",
        "module": "camera",
        "permission_type": "action",
        "is_system": False
    },
    {
        "name": "camera:update",
        "display_name": "编辑摄像头",
        "description": "编辑摄像头配置",
        "category": "摄像头管理",
        "module": "camera",
        "permission_type": "action",
        "is_system": False
    },
    {
        "name": "camera:delete",
        "display_name": "删除摄像头",
        "description": "删除摄像头",
        "category": "摄像头管理",
        "module": "camera",
        "permission_type": "action",
        "is_system": False
    },
    {
        "name": "camera:control",
        "display_name": "控制摄像头",
        "description": "控制摄像头（PTZ等）",
        "category": "摄像头管理",
        "module": "camera",
        "permission_type": "action",
        "is_system": False
    },
    
    # AI管理权限
    {
        "name": "ai:list",
        "display_name": "查看AI算法",
        "description": "查看AI算法列表",
        "category": "AI管理",
        "module": "ai",
        "permission_type": "action",
        "is_system": False
    },
    {
        "name": "ai:create",
        "display_name": "创建AI算法",
        "description": "创建AI算法配置",
        "category": "AI管理",
        "module": "ai",
        "permission_type": "action",
        "is_system": False
    },
    {
        "name": "ai:update",
        "display_name": "编辑AI算法",
        "description": "编辑AI算法配置",
        "category": "AI管理",
        "module": "ai",
        "permission_type": "action",
        "is_system": False
    },
    {
        "name": "ai:delete",
        "display_name": "删除AI算法",
        "description": "删除AI算法",
        "category": "AI管理",
        "module": "ai",
        "permission_type": "action",
        "is_system": False
    },
    
    # 事件管理权限
    {
        "name": "event:list",
        "display_name": "查看事件列表",
        "description": "查看事件告警列表",
        "category": "事件管理",
        "module": "event",
        "permission_type": "action",
        "is_system": False
    },
    {
        "name": "event:handle",
        "display_name": "处理事件",
        "description": "处理事件告警",
        "category": "事件管理",
        "module": "event",
        "permission_type": "action",
        "is_system": False
    },
    {
        "name": "event:rule",
        "display_name": "管理事件规则",
        "description": "管理事件规则配置",
        "category": "事件管理",
        "module": "event",
        "permission_type": "action",
        "is_system": False
    },
    
    # 诊断管理权限
    {
        "name": "diagnosis:list",
        "display_name": "查看诊断任务",
        "description": "查看诊断任务列表",
        "category": "诊断管理",
        "module": "diagnosis",
        "permission_type": "action",
        "is_system": False
    },
    {
        "name": "diagnosis:create",
        "display_name": "创建诊断任务",
        "description": "创建诊断任务",
        "category": "诊断管理",
        "module": "diagnosis",
        "permission_type": "action",
        "is_system": False
    },
    {
        "name": "diagnosis:result",
        "display_name": "查看诊断结果",
        "description": "查看诊断结果",
        "category": "诊断管理",
        "module": "diagnosis",
        "permission_type": "action",
        "is_system": False
    },
    
    # 系统配置权限
    {
        "name": "system:config",
        "display_name": "系统配置",
        "description": "管理系统配置",
        "category": "系统管理",
        "module": "system",
        "permission_type": "action",
        "is_system": False
    },
    {
        "name": "system:log",
        "display_name": "查看系统日志",
        "description": "查看系统日志",
        "category": "系统管理",
        "module": "system",
        "permission_type": "action",
        "is_system": False
    },
    {
        "name": "system:monitor",
        "display_name": "系统监控",
        "description": "查看系统监控信息",
        "category": "系统管理",
        "module": "system",
        "permission_type": "action",
        "is_system": False
    },
    
    # 页面权限
    {
        "name": "page:dashboard",
        "display_name": "仪表盘页面",
        "description": "访问仪表盘页面",
        "category": "页面权限",
        "module": "page",
        "permission_type": "page",
        "is_system": False
    },
    {
        "name": "page:camera",
        "display_name": "摄像头管理页面",
        "description": "访问摄像头管理页面",
        "category": "页面权限",
        "module": "page",
        "permission_type": "page",
        "is_system": False
    },
    {
        "name": "page:ai",
        "display_name": "AI应用中心页面",
        "description": "访问AI应用中心页面",
        "category": "页面权限",
        "module": "page",
        "permission_type": "page",
        "is_system": False
    },
    {
        "name": "page:event",
        "display_name": "事件告警中心页面",
        "description": "访问事件告警中心页面",
        "category": "页面权限",
        "module": "page",
        "permission_type": "page",
        "is_system": False
    },
    {
        "name": "page:diagnosis",
        "display_name": "智能诊断页面",
        "description": "访问智能诊断页面",
        "category": "页面权限",
        "module": "page",
        "permission_type": "page",
        "is_system": False
    },
    {
        "name": "page:system",
        "display_name": "系统配置页面",
        "description": "访问系统配置页面",
        "category": "页面权限",
        "module": "page",
        "permission_type": "page",
        "is_system": False
    }
]

# 系统角色定义
SYSTEM_ROLES = [
    {
        "name": "admin",
        "display_name": "系统管理员",
        "description": "拥有系统所有权限的管理员角色",
        "permissions": [perm["name"] for perm in SYSTEM_PERMISSIONS],
        "page_permissions": {
            "/dashboard": True,
            "/cameras": True,
            "/ai": True,
            "/events": True,
            "/diagnosis": True,
            "/system": True
        },
        "is_system": True
    },
    {
        "name": "operator",
        "display_name": "操作员",
        "description": "负责日常操作的角色，可以管理摄像头、查看事件等",
        "permissions": [
            "camera:list", "camera:create", "camera:update", "camera:control",
            "event:list", "event:handle",
            "ai:list", "ai:create", "ai:update",
            "diagnosis:list", "diagnosis:create", "diagnosis:result",
            "page:dashboard", "page:camera", "page:ai", "page:event", "page:diagnosis"
        ],
        "page_permissions": {
            "/dashboard": True,
            "/cameras": True,
            "/ai": True,
            "/events": True,
            "/diagnosis": True,
            "/system": False
        },
        "is_system": True
    },
    {
        "name": "viewer",
        "display_name": "观察员",
        "description": "只能查看信息，不能进行操作的角色",
        "permissions": [
            "camera:list", "event:list", "ai:list", "diagnosis:list", "diagnosis:result",
            "page:dashboard", "page:camera", "page:ai", "page:event", "page:diagnosis"
        ],
        "page_permissions": {
            "/dashboard": True,
            "/cameras": True,
            "/ai": True,
            "/events": True,
            "/diagnosis": True,
            "/system": False
        },
        "is_system": True
    },
    {
        "name": "user",
        "display_name": "普通用户",
        "description": "基础用户角色，只能访问仪表盘",
        "permissions": ["page:dashboard"],
        "page_permissions": {
            "/dashboard": True,
            "/cameras": False,
            "/ai": False,
            "/events": False,
            "/diagnosis": False,
            "/system": False
        },
        "is_system": True
    }
]

async def init_permissions(db: AsyncSession):
    """初始化系统权限"""
    print("开始初始化权限...")
    
    # 删除所有现有权限
    from sqlalchemy import text
    await db.execute(text("DELETE FROM permissions"))
    await db.commit()
    print("已清除现有权限数据")
    print("正在初始化系统权限...")
    
    for perm_data in SYSTEM_PERMISSIONS:
        # 检查权限是否已存在
        result = await db.execute(
            select(Permission).where(Permission.name == perm_data["name"])
        )
        existing_perm = result.scalar_one_or_none()
        
        if not existing_perm:
            permission = Permission(**perm_data)
            db.add(permission)
            print(f"  创建权限: {perm_data['display_name']} ({perm_data['name']})")
        else:
            print(f"  权限已存在: {perm_data['display_name']} ({perm_data['name']})")
    
    await db.commit()
    print(f"权限初始化完成，共处理 {len(SYSTEM_PERMISSIONS)} 个权限")

async def init_roles(db: AsyncSession):
    """初始化系统角色"""
    print("正在初始化系统角色...")
    
    for role_data in SYSTEM_ROLES:
        # 检查角色是否已存在
        result = await db.execute(
            select(Role).where(Role.name == role_data["name"])
        )
        existing_role = result.scalar_one_or_none()
        
        if not existing_role:
            role = Role(
                name=role_data["name"],
                display_name=role_data["display_name"],
                description=role_data["description"],
                permissions=role_data["permissions"],
                page_permissions=role_data["page_permissions"],
                is_system=role_data["is_system"]
            )
            db.add(role)
            print(f"  创建角色: {role_data['display_name']} ({role_data['name']})")
        else:
            # 更新现有角色的权限
            existing_role.permissions = role_data["permissions"]
            existing_role.page_permissions = role_data["page_permissions"]
            print(f"  更新角色权限: {role_data['display_name']} ({role_data['name']})")
    
    await db.commit()
    print(f"角色初始化完成，共处理 {len(SYSTEM_ROLES)} 个角色")

async def assign_admin_role(db: AsyncSession):
    """为超级管理员分配admin角色"""
    print("正在为超级管理员分配角色...")
    
    # 查找超级管理员
    result = await db.execute(
        select(User).where(User.is_superuser == True)
    )
    superusers = result.scalars().all()
    
    # 查找admin角色
    admin_role_result = await db.execute(
        select(Role).where(Role.name == "admin")
    )
    admin_role = admin_role_result.scalar_one_or_none()
    
    if not admin_role:
        print("  错误: 未找到admin角色")
        return
    
    for user in superusers:
        # 检查是否已分配角色
        existing_assignment = await db.execute(
            select(UserRole).where(
                UserRole.user_id == user.id,
                UserRole.role_id == admin_role.id,
                UserRole.is_active == True
            )
        )
        
        if not existing_assignment.scalar_one_or_none():
            user_role = UserRole(
                user_id=user.id,
                role_id=admin_role.id,
                assigned_by=user.id  # 自己分配给自己
            )
            db.add(user_role)
            print(f"  为用户 {user.username} 分配admin角色")
        else:
            print(f"  用户 {user.username} 已有admin角色")
    
    await db.commit()
    print("超级管理员角色分配完成")

async def main():
    """主函数"""
    print("开始初始化系统权限和角色数据...")
    print("=" * 50)
    
    try:
        async with AsyncSessionLocal() as db:
            await init_permissions(db)
            print()
            await init_roles(db)
            print()
            await assign_admin_role(db)
            
        print("=" * 50)
        print("系统权限和角色数据初始化完成！")
        
    except Exception as e:
        print(f"初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)