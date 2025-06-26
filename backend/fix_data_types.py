#!/usr/bin/env python3
"""
修复系统配置表中data_type字段为NULL的问题
"""

import asyncio
from sqlalchemy import text
from database import async_engine

async def fix_data_types():
    """修复系统配置表中的data_type字段"""
    async with async_engine.begin() as conn:
        # 更新data_type字段
        update_sql = """
        UPDATE system_configs 
        SET data_type = CASE 
            WHEN key IN ('auth.session_timeout', 'auth.max_login_attempts', 'auth.password_min_length', 
                        'storage.max_file_size', 'ai.max_concurrent_tasks', 'log.retention_days') THEN 'int'
            WHEN key IN ('auth.require_strong_password', 'notification.email_enabled', 'notification.sms_enabled') THEN 'bool'
            WHEN key IN ('ai.detection_confidence') THEN 'float'
            WHEN key IN ('storage.allowed_file_types') THEN 'json'
            ELSE 'string'
        END 
        WHERE data_type IS NULL;
        """
        
        result = await conn.execute(text(update_sql))
        print(f"已更新 {result.rowcount} 条记录的data_type字段")
        
        # 验证更新结果
        check_sql = "SELECT COUNT(*) as null_count FROM system_configs WHERE data_type IS NULL;"
        result = await conn.execute(text(check_sql))
        null_count = result.scalar()
        print(f"剩余data_type为NULL的记录数: {null_count}")
        
        if null_count == 0:
            print("✅ 所有系统配置的data_type字段已修复")
        else:
            print("❌ 仍有记录的data_type字段为NULL")

if __name__ == "__main__":
    asyncio.run(fix_data_types())