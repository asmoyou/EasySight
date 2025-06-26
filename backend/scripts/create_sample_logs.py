#!/usr/bin/env python3
"""
创建示例系统日志数据
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta
import random

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db, AsyncSessionLocal
from models.system import SystemLog
from models.user import User
from sqlalchemy import select

# 示例日志数据
SAMPLE_LOGS = [
    {
        "level": "info",
        "module": "user",
        "action": "login",
        "message": "用户登录成功",
        "ip_address": "192.168.1.100",
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    },
    {
        "level": "info",
        "module": "user",
        "action": "create",
        "message": "创建新用户",
        "ip_address": "192.168.1.101",
        "extra_data": {"username": "testuser", "role": "operator"}
    },
    {
        "level": "warning",
        "module": "camera",
        "action": "connection_failed",
        "message": "摄像头连接失败",
        "ip_address": "192.168.1.102",
        "extra_data": {"camera_id": 1, "error": "timeout"}
    },
    {
        "level": "error",
        "module": "ai",
        "action": "algorithm_error",
        "message": "AI算法处理异常",
        "ip_address": "192.168.1.103",
        "extra_data": {"algorithm_id": 2, "error_code": "E001"}
    },
    {
        "level": "info",
        "module": "role",
        "action": "update",
        "message": "更新角色权限",
        "ip_address": "192.168.1.104",
        "extra_data": {"role_id": 1, "permissions": ["user:read", "user:write"]}
    },
    {
        "level": "critical",
        "module": "system",
        "action": "database_error",
        "message": "数据库连接异常",
        "ip_address": "192.168.1.105",
        "extra_data": {"error": "connection timeout", "retry_count": 3}
    },
    {
        "level": "info",
        "module": "event",
        "action": "handle",
        "message": "处理事件通知",
        "ip_address": "192.168.1.106",
        "extra_data": {"event_type": "motion_detection", "camera_id": 3}
    },
    {
        "level": "debug",
        "module": "system",
        "action": "config_load",
        "message": "加载系统配置",
        "ip_address": "192.168.1.107",
        "extra_data": {"config_count": 25}
    },
    {
        "level": "warning",
        "module": "user",
        "action": "login_failed",
        "message": "用户登录失败",
        "ip_address": "192.168.1.108",
        "extra_data": {"username": "admin", "reason": "invalid_password"}
    },
    {
        "level": "info",
        "module": "camera",
        "action": "create",
        "message": "添加新摄像头",
        "ip_address": "192.168.1.109",
        "extra_data": {"camera_name": "前门摄像头", "rtsp_url": "rtsp://192.168.1.200:554/stream"}
    }
]

async def create_sample_logs():
    """创建示例日志数据"""
    async with AsyncSessionLocal() as session:
        try:
            # 获取第一个用户作为示例用户
            result = await session.execute(select(User).limit(1))
            user = result.scalar_one_or_none()
            
            if not user:
                print("未找到用户，请先创建用户")
                return
            
            # 创建日志数据
            for i, log_data in enumerate(SAMPLE_LOGS):
                # 随机生成过去7天内的时间
                days_ago = random.randint(0, 7)
                hours_ago = random.randint(0, 23)
                minutes_ago = random.randint(0, 59)
                
                created_time = datetime.now() - timedelta(
                    days=days_ago, 
                    hours=hours_ago, 
                    minutes=minutes_ago
                )
                
                log = SystemLog(
                    level=log_data["level"],
                    module=log_data["module"],
                    action=log_data["action"],
                    message=log_data["message"],
                    user_id=user.id if random.choice([True, False]) else None,
                    username=user.username if random.choice([True, False]) else None,
                    ip_address=log_data["ip_address"],
                    user_agent=log_data.get("user_agent"),
                    request_id=f"req_{i+1:03d}_{int(created_time.timestamp())}",
                    extra_data=log_data.get("extra_data", {}),
                    created_at=created_time
                )
                
                session.add(log)
            
            await session.commit()
            print(f"成功创建 {len(SAMPLE_LOGS)} 条示例日志")
            
        except Exception as e:
            await session.rollback()
            print(f"创建示例日志失败: {e}")
            raise
        finally:
            await session.close()

if __name__ == "__main__":
    asyncio.run(create_sample_logs())