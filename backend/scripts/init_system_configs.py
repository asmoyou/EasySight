#!/usr/bin/env python3
"""
初始化系统配置脚本
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db, init_db
from models.system import SystemConfig
from sqlalchemy import select

# 默认系统配置
DEFAULT_CONFIGS = [
    {
        "key": "system.name",
        "value": "EasySight 智能安防平台",
        "data_type": "string",
        "category": "基础设置",
        "description": "系统名称",
        "is_public": True,
        "is_editable": True,
        "requires_restart": False
    },
    {
        "key": "system.version",
        "value": "1.0.0",
        "data_type": "string",
        "category": "基础设置",
        "description": "系统版本号",
        "is_public": True,
        "is_editable": False,
        "requires_restart": False
    },
    {
        "key": "system.logo",
        "value": "/static/logo.png",
        "data_type": "string",
        "category": "基础设置",
        "description": "系统Logo路径",
        "is_public": True,
        "is_editable": True,
        "requires_restart": False
    },
    {
        "key": "system.description",
        "value": "通用分布式智能安防平台",
        "data_type": "string",
        "category": "基础设置",
        "description": "系统描述",
        "is_public": True,
        "is_editable": True,
        "requires_restart": False
    },
    {
        "key": "auth.session_timeout",
        "value": "3600",
        "data_type": "int",
        "category": "认证设置",
        "description": "会话超时时间（秒）",
        "is_public": False,
        "is_editable": True,
        "requires_restart": True
    },
    {
        "key": "auth.max_login_attempts",
        "value": "5",
        "data_type": "int",
        "category": "认证设置",
        "description": "最大登录尝试次数",
        "is_public": False,
        "is_editable": True,
        "requires_restart": False
    },
    {
        "key": "auth.password_min_length",
        "value": "8",
        "data_type": "int",
        "category": "认证设置",
        "description": "密码最小长度",
        "is_public": True,
        "is_editable": True,
        "requires_restart": False
    },
    {
        "key": "auth.require_strong_password",
        "value": "true",
        "data_type": "bool",
        "category": "认证设置",
        "description": "是否要求强密码",
        "is_public": True,
        "is_editable": True,
        "requires_restart": False
    },
    {
        "key": "notification.email_enabled",
        "value": "false",
        "data_type": "bool",
        "category": "通知设置",
        "description": "是否启用邮件通知",
        "is_public": False,
        "is_editable": True,
        "requires_restart": False
    },
    {
        "key": "notification.sms_enabled",
        "value": "false",
        "data_type": "bool",
        "category": "通知设置",
        "description": "是否启用短信通知",
        "is_public": False,
        "is_editable": True,
        "requires_restart": False
    },
    {
        "key": "storage.max_file_size",
        "value": "10485760",
        "data_type": "int",
        "category": "存储设置",
        "description": "最大文件上传大小（字节）",
        "is_public": True,
        "is_editable": True,
        "requires_restart": False
    },
    {
        "key": "storage.allowed_file_types",
        "value": '["jpg", "jpeg", "png", "gif", "mp4", "avi", "mov"]',
        "data_type": "json",
        "category": "存储设置",
        "description": "允许的文件类型",
        "is_public": True,
        "is_editable": True,
        "requires_restart": False
    },
    {
        "key": "ai.detection_confidence",
        "value": "0.7",
        "data_type": "float",
        "category": "AI设置",
        "description": "AI检测置信度阈值",
        "is_public": False,
        "is_editable": True,
        "requires_restart": False
    },
    {
        "key": "ai.max_concurrent_tasks",
        "value": "10",
        "data_type": "int",
        "category": "AI设置",
        "description": "最大并发AI任务数",
        "is_public": False,
        "is_editable": True,
        "requires_restart": True
    },
    {
        "key": "log.retention_days",
        "value": "30",
        "data_type": "int",
        "category": "日志设置",
        "description": "日志保留天数",
        "is_public": False,
        "is_editable": True,
        "requires_restart": False
    },
    {
        "key": "log.level",
        "value": "INFO",
        "data_type": "string",
        "category": "日志设置",
        "description": "日志级别",
        "is_public": False,
        "is_editable": True,
        "requires_restart": True
    }
]

async def init_system_configs():
    """初始化系统配置"""
    print("开始初始化系统配置...")
    
    # 初始化数据库
    await init_db()
    
    # 获取数据库会话
    async for db in get_db():
        try:
            for config_data in DEFAULT_CONFIGS:
                # 检查配置是否已存在
                result = await db.execute(
                    select(SystemConfig).where(SystemConfig.key == config_data["key"])
                )
                existing_config = result.scalar_one_or_none()
                
                if existing_config:
                    print(f"配置 {config_data['key']} 已存在，跳过")
                    continue
                
                # 创建新配置
                config = SystemConfig(**config_data)
                db.add(config)
                print(f"创建配置: {config_data['key']}")
            
            # 提交事务
            await db.commit()
            print("系统配置初始化完成！")
            
        except Exception as e:
            await db.rollback()
            print(f"初始化系统配置失败: {e}")
            raise
        finally:
            await db.close()
        break

if __name__ == "__main__":
    asyncio.run(init_system_configs())