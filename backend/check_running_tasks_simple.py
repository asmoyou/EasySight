#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单检查和修复运行中的诊断任务
"""

import asyncio
import logging
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from database import get_db
from models.diagnosis import DiagnosisTask, TaskStatus
from diagnosis.executor import diagnosis_executor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def check_and_fix_running_tasks():
    """检查并修复处于运行状态的任务"""
    async for db in get_db():
        try:
            print("=== 检查数据库中处于运行状态的任务 ===")
            
            # 查询所有处于运行状态的任务
            result = await db.execute(
                select(DiagnosisTask).where(
                    DiagnosisTask.status == 'running'
                )
            )
            running_tasks = result.scalars().all()
            
            print(f"\n发现 {len(running_tasks)} 个处于运行状态的任务")
            
            if len(running_tasks) == 0:
                print("✅ 没有发现运行中的任务")
                return
            
            reset_count = 0
            
            for task in running_tasks:
                print(f"\n--- 任务 {task.id}: {task.name} ---")
                print(f"状态: {task.status.value}")
                print(f"最后运行时间: {task.last_run_time}")
                print(f"是否启用: {task.is_active}")
                
                # 检查任务是否真的在运行
                is_actually_running = task.id in diagnosis_executor.running_tasks
                print(f"实际运行状态: {'运行中' if is_actually_running else '未运行'}")
                
                should_reset = False
                reset_reason = ""
                
                # 检查是否需要重置
                if not is_actually_running:
                    should_reset = True
                    reset_reason = "任务不在执行器运行列表中"
                elif task.last_run_time:
                    # 检查运行时间是否过长（超过30分钟认为异常）
                    time_diff = datetime.utcnow() - task.last_run_time.replace(tzinfo=None)
                    print(f"运行时长: {time_diff}")
                    
                    if time_diff > timedelta(minutes=30):
                        should_reset = True
                        reset_reason = f"任务运行时间过长 ({time_diff})"
                else:
                    should_reset = True
                    reset_reason = "任务无最后运行时间记录"
                
                if should_reset:
                    print(f"⚠️  需要重置: {reset_reason}")
                    
                    # 重置任务状态
                    task.status = 'pending'
                    
                    # 从执行器运行列表中移除
                    diagnosis_executor.running_tasks.discard(task.id)
                    
                    reset_count += 1
                    print(f"✅ 已重置任务状态为 PENDING")
                else:
                    print(f"✅ 任务状态正常")
            
            if reset_count > 0:
                await db.commit()
                print(f"\n🎉 成功重置 {reset_count} 个任务的状态")
            else:
                print(f"\n✅ 所有任务状态正常，无需重置")
                
        except Exception as e:
            logger.error(f"检查任务失败: {str(e)}")
            await db.rollback()
        finally:
            break

if __name__ == "__main__":
    asyncio.run(check_and_fix_running_tasks())