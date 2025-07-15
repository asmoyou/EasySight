#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复数据库中枚举值大小写不匹配的问题
将小写的枚举值更新为大写格式以匹配代码中的定义
"""

import asyncio
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from database import AsyncSessionLocal
from sqlalchemy import text

async def fix_enum_values():
    """修复枚举值大小写不匹配问题"""
    print("=== 修复数据库枚举值大小写不匹配问题 ===")
    
    async with AsyncSessionLocal() as session:
        try:
            # 检查当前的枚举值
            print("\n检查当前任务状态值...")
            result = await session.execute(
                text("SELECT DISTINCT status FROM diagnosis_tasks ORDER BY status")
            )
            current_statuses = [row[0] for row in result.fetchall()]
            print(f"当前状态值: {current_statuses}")
            
            # 修复任务状态枚举值
            status_mapping = {
                'pending': 'PENDING',
                'running': 'RUNNING', 
                'completed': 'COMPLETED',
                'failed': 'FAILED',
                'cancelled': 'CANCELLED'
            }
            
            updated_count = 0
            for old_status, new_status in status_mapping.items():
                result = await session.execute(
                    text(f"UPDATE diagnosis_tasks SET status = '{new_status}' WHERE status = '{old_status}'")
                )
                if result.rowcount > 0:
                    print(f"✅ 更新了 {result.rowcount} 个任务状态: {old_status} -> {new_status}")
                    updated_count += result.rowcount
            
            # 检查诊断结果状态
            print("\n检查诊断结果状态值...")
            result = await session.execute(
                text("SELECT DISTINCT diagnosis_status FROM diagnosis_results ORDER BY diagnosis_status")
            )
            current_diagnosis_statuses = [row[0] for row in result.fetchall()]
            print(f"当前诊断状态值: {current_diagnosis_statuses}")
            
            # 修复诊断结果状态枚举值
            diagnosis_status_mapping = {
                'normal': 'NORMAL',
                'warning': 'WARNING',
                'error': 'ERROR', 
                'critical': 'CRITICAL'
            }
            
            for old_status, new_status in diagnosis_status_mapping.items():
                result = await session.execute(
                    text(f"UPDATE diagnosis_results SET diagnosis_status = '{new_status}' WHERE diagnosis_status = '{old_status}'")
                )
                if result.rowcount > 0:
                    print(f"✅ 更新了 {result.rowcount} 个诊断结果状态: {old_status} -> {new_status}")
                    updated_count += result.rowcount
            
            await session.commit()
            
            # 验证修复结果
            print("\n验证修复结果...")
            result = await session.execute(
                text("SELECT DISTINCT status FROM diagnosis_tasks ORDER BY status")
            )
            new_statuses = [row[0] for row in result.fetchall()]
            print(f"修复后任务状态值: {new_statuses}")
            
            result = await session.execute(
                text("SELECT DISTINCT diagnosis_status FROM diagnosis_results ORDER BY diagnosis_status")
            )
            new_diagnosis_statuses = [row[0] for row in result.fetchall()]
            print(f"修复后诊断状态值: {new_diagnosis_statuses}")
            
            if updated_count > 0:
                print(f"\n✅ 总共更新了 {updated_count} 条记录")
            else:
                print("\n✅ 所有枚举值已经是正确格式，无需更新")
            
        except Exception as e:
            print(f"❌ 修复枚举值时发生错误: {e}")
            await session.rollback()
            raise

if __name__ == "__main__":
    asyncio.run(fix_enum_values())