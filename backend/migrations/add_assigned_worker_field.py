#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
添加assigned_worker字段到diagnosis_tasks表
"""

import asyncio
import sys
import os
from pathlib import Path
from sqlalchemy import text
import logging

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from database import AsyncSessionLocal

logger = logging.getLogger(__name__)

async def add_assigned_worker_field():
    """添加assigned_worker字段到diagnosis_tasks表"""
    try:
        async with AsyncSessionLocal() as db:
            # 检查字段是否已存在
            check_query = text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'diagnosis_tasks' 
                AND column_name = 'assigned_worker'
            """)
            
            result = await db.execute(check_query)
            existing_column = result.fetchone()
            
            if existing_column:
                logger.info("assigned_worker字段已存在，跳过添加")
                print("assigned_worker字段已存在，跳过添加")
                return
            
            # 添加字段
            alter_query = text("""
                ALTER TABLE diagnosis_tasks 
                ADD COLUMN assigned_worker VARCHAR(255) NULL
            """)
            
            await db.execute(alter_query)
            
            # 添加字段注释
            comment_query = text("""
                COMMENT ON COLUMN diagnosis_tasks.assigned_worker IS '分配的Worker节点ID'
            """)
            
            await db.execute(comment_query)
            await db.commit()
            
            logger.info("成功添加assigned_worker字段到diagnosis_tasks表")
            print("成功添加assigned_worker字段到diagnosis_tasks表")
            
    except Exception as e:
        logger.error(f"添加assigned_worker字段失败: {e}")
        print(f"添加assigned_worker字段失败: {e}")
        raise

async def main():
    """主函数"""
    logging.basicConfig(level=logging.INFO)
    print("开始添加assigned_worker字段...")
    await add_assigned_worker_field()
    print("迁移完成")

if __name__ == "__main__":
    asyncio.run(main())