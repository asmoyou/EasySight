#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用原生SQL检查和修复运行中的诊断任务
"""

import asyncio
import logging
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from database import get_db
from diagnosis.executor import diagnosis_executor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def check_and_fix_running_tasks():
    """检查并修复处于运行状态的任务"""
    async for db in get_db():
        try:
            print("=== 检查数据库中处于运行状态的任务 ===")
            
            # 使用原生SQL查询所有处于运行状态的任务
            result = await db.execute(
                text("SELECT * FROM diagnosis_tasks WHERE status = 'running'")
            )
            running_tasks = result.fetchall()
            
            print(f"\n发现 {len(running_tasks)} 个处于运行状态的任务")
            
            if len(running_tasks) == 0:
                print("✅ 没有发现运行中的任务")
                return
            
            reset_count = 0
            
            for task_row in running_tasks:
                task_id = task_row[0]  # id字段
                task_name = task_row[1]  # name字段
                task_status = task_row[13]  # status字段
                last_run_time = task_row[16]  # last_run_time字段
                is_active = task_row[15]  # is_active字段
                
                print(f"\n--- 任务 {task_id}: {task_name} ---")
                print(f"状态: {task_status}")
                print(f"最后运行时间: {last_run_time}")
                print(f"是否启用: {is_active}")
                
                # 检查任务是否真的在运行
                is_actually_running = task_id in diagnosis_executor.running_tasks
                print(f"实际运行状态: {'运行中' if is_actually_running else '未运行'}")
                
                should_reset = False
                reset_reason = ""
                
                # 检查是否需要重置
                if not is_actually_running:
                    should_reset = True
                    reset_reason = "任务不在执行器运行列表中"
                elif last_run_time:
                    # 检查运行时间是否过长（超过30分钟认为异常）
                    if isinstance(last_run_time, str):
                        last_run_time = datetime.fromisoformat(last_run_time.replace('Z', '+00:00'))
                    
                    time_diff = datetime.now(last_run_time.tzinfo) - last_run_time
                    print(f"运行时长: {time_diff}")
                    
                    if time_diff > timedelta(minutes=30):
                        should_reset = True
                        reset_reason = f"任务运行时间过长 ({time_diff})"
                else:
                    should_reset = True
                    reset_reason = "任务无最后运行时间记录"
                
                if should_reset:
                    print(f"⚠️  需要重置: {reset_reason}")
                    
                    # 使用原生SQL重置任务状态
                    await db.execute(
                        text("UPDATE diagnosis_tasks SET status = 'pending' WHERE id = :task_id"),
                        {"task_id": task_id}
                    )
                    
                    # 从执行器运行列表中移除
                    diagnosis_executor.running_tasks.discard(task_id)
                    
                    reset_count += 1
                    print(f"✅ 已重置任务状态为 pending")
                else:
                    print(f"✅ 任务状态正常")
            
            if reset_count > 0:
                await db.commit()
                print(f"\n🎉 成功重置 {reset_count} 个任务的状态")
            else:
                print(f"\n✅ 所有任务状态正常，无需重置")
                
        except Exception as e:
            logger.error(f"检查任务失败: {str(e)}")
            import traceback
            traceback.print_exc()
            await db.rollback()
        finally:
            break

if __name__ == "__main__":
    asyncio.run(check_and_fix_running_tasks())