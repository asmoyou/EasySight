#!/usr/bin/env python3
"""
数据库迁移脚本：将 AlarmRule 表的 severity_levels 字段改为 severity_level

执行方式：
python migrations/update_severity_levels_to_level.py
"""

import asyncio
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from database import AsyncSessionLocal

async def migrate_severity_levels():
    """迁移 severity_levels 字段到 severity_level"""
    async with AsyncSessionLocal() as db:
        try:
            # 1. 添加新的 severity_level 字段
            await db.execute(text("""
                ALTER TABLE alarm_rules 
                ADD COLUMN severity_level VARCHAR(20)
            """))
            
            # 添加字段注释
            await db.execute(text("""
                COMMENT ON COLUMN alarm_rules.severity_level IS '触发的严重程度级别'
            """))
            print("✓ 添加 severity_level 字段成功")
            
            # 2. 将 severity_levels 数组的第一个值迁移到 severity_level
            await db.execute(text("""
                UPDATE alarm_rules 
                SET severity_level = CASE 
                    WHEN jsonb_array_length(severity_levels::jsonb) > 0 
                    THEN severity_levels::jsonb->>0
                    ELSE 'medium'
                END
                WHERE severity_levels IS NOT NULL
            """))
            print("✓ 数据迁移成功")
            
            # 3. 删除旧的 severity_levels 字段
            await db.execute(text("""
                ALTER TABLE alarm_rules 
                DROP COLUMN severity_levels
            """))
            print("✓ 删除旧字段成功")
            
            await db.commit()
            print("\n🎉 数据库迁移完成！")
            
        except Exception as e:
            await db.rollback()
            print(f"❌ 迁移失败: {e}")
            raise

if __name__ == "__main__":
    asyncio.run(migrate_severity_levels())