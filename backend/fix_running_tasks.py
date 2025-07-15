#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
诊断任务状态恢复脚本
用于修复处于运行状态但实际已停止的诊断任务
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

async def check_running_tasks():
    """检查数据库中处于运行状态的任务"""
    async for db in get_db():
        try:
            # 查询所有处于运行状态的任务
            result = await db.execute(
                select(DiagnosisTask).where(
                    DiagnosisTask.status == TaskStatus.RUNNING
                )
            )
            running_tasks = result.scalars().all()
            
            print(f"\n=== 发现 {len(running_tasks)} 个处于运行状态的任务 ===")
            
            for task in running_tasks:
                print(f"\n任务ID: {task.id}")
                print(f"任务名称: {task.name}")
                print(f"状态: {task.status.value}")
                print(f"最后运行时间: {task.last_run_time}")
                print(f"创建时间: {task.created_at}")
                print(f"是否启用: {task.is_active}")
                
                # 检查任务是否真的在运行
                is_actually_running = task.id in diagnosis_executor.running_tasks
                print(f"实际运行状态: {'运行中' if is_actually_running else '未运行'}")
                
                # 检查任务运行时间是否过长（超过30分钟认为异常）
                if task.last_run_time:
                    time_diff = datetime.utcnow() - task.last_run_time.replace(tzinfo=None)
                    print(f"运行时长: {time_diff}")
                    
                    if time_diff > timedelta(minutes=30):
                        print("⚠️  任务运行时间过长，可能已异常停止")
                else:
                    print("⚠️  任务无最后运行时间记录")
                    
            return running_tasks
            
        except Exception as e:
            logger.error(f"检查运行任务失败: {str(e)}")
            return []
        finally:
            break

async def reset_stuck_tasks(force_reset: bool = False):
    """重置卡住的任务状态"""
    async for db in get_db():
        try:
            # 查询所有处于运行状态的任务
            result = await db.execute(
                select(DiagnosisTask).where(
                    DiagnosisTask.status == TaskStatus.RUNNING
                )
            )
            running_tasks = result.scalars().all()
            
            reset_count = 0
            
            for task in running_tasks:
                should_reset = False
                reset_reason = ""
                
                # 检查是否真的在运行
                is_actually_running = task.id in diagnosis_executor.running_tasks
                
                if not is_actually_running:
                    should_reset = True
                    reset_reason = "任务不在执行器运行列表中"
                elif task.last_run_time:
                    # 检查运行时间是否过长
                    time_diff = datetime.utcnow() - task.last_run_time.replace(tzinfo=None)
                    if time_diff > timedelta(minutes=30):
                        should_reset = True
                        reset_reason = f"任务运行时间过长 ({time_diff})"
                else:
                    should_reset = True
                    reset_reason = "任务无最后运行时间记录"
                
                if should_reset or force_reset:
                    print(f"\n重置任务 {task.id} ({task.name})")
                    print(f"重置原因: {reset_reason if not force_reset else '强制重置'}")
                    
                    # 更新任务状态为待执行
                    task.status = TaskStatus.PENDING
                    
                    # 从执行器运行列表中移除（如果存在）
                    diagnosis_executor.running_tasks.discard(task.id)
                    
                    reset_count += 1
                    
            if reset_count > 0:
                await db.commit()
                print(f"\n✅ 成功重置 {reset_count} 个任务的状态")
            else:
                print("\n✅ 没有需要重置的任务")
                
        except Exception as e:
            logger.error(f"重置任务状态失败: {str(e)}")
            await db.rollback()
        finally:
            break

async def add_task_recovery_mechanism():
    """添加任务恢复机制到路由中"""
    print("\n=== 任务恢复机制建议 ===")
    print("1. 在诊断任务路由中添加任务状态检查和恢复功能")
    print("2. 在任务执行前检查是否有卡住的任务")
    print("3. 添加定时清理机制")
    print("4. 在手动执行任务时先检查任务状态")
    
    recovery_code = '''
# 在 routers/diagnosis.py 中添加以下路由

@router.post("/tasks/recovery")
async def recover_stuck_tasks(
    force_reset: bool = Query(False, description="是否强制重置所有运行中的任务"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """恢复卡住的诊断任务"""
    from diagnosis.executor import diagnosis_executor
    from datetime import datetime, timedelta
    
    # 查询所有处于运行状态的任务
    result = await db.execute(
        select(DiagnosisTask).where(
            DiagnosisTask.status == TaskStatus.RUNNING
        )
    )
    running_tasks = result.scalars().all()
    
    reset_tasks = []
    
    for task in running_tasks:
        should_reset = False
        reset_reason = ""
        
        # 检查是否真的在运行
        is_actually_running = task.id in diagnosis_executor.running_tasks
        
        if not is_actually_running:
            should_reset = True
            reset_reason = "任务不在执行器运行列表中"
        elif task.last_run_time:
            # 检查运行时间是否过长（超过30分钟）
            time_diff = datetime.utcnow() - task.last_run_time.replace(tzinfo=None)
            if time_diff > timedelta(minutes=30):
                should_reset = True
                reset_reason = f"任务运行时间过长 ({time_diff})"
        else:
            should_reset = True
            reset_reason = "任务无最后运行时间记录"
        
        if should_reset or force_reset:
            task.status = TaskStatus.PENDING
            diagnosis_executor.running_tasks.discard(task.id)
            reset_tasks.append({
                "id": task.id,
                "name": task.name,
                "reason": reset_reason if not force_reset else "强制重置"
            })
    
    if reset_tasks:
        await db.commit()
    
    return {
        "success": True,
        "message": f"成功恢复 {len(reset_tasks)} 个任务",
        "reset_tasks": reset_tasks
    }

@router.get("/tasks/status-check")
async def check_tasks_status(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """检查任务状态"""
    from diagnosis.executor import diagnosis_executor
    
    # 查询所有处于运行状态的任务
    result = await db.execute(
        select(DiagnosisTask).where(
            DiagnosisTask.status == TaskStatus.RUNNING
        )
    )
    running_tasks = result.scalars().all()
    
    task_status = []
    
    for task in running_tasks:
        is_actually_running = task.id in diagnosis_executor.running_tasks
        
        time_diff = None
        if task.last_run_time:
            time_diff = datetime.utcnow() - task.last_run_time.replace(tzinfo=None)
        
        task_status.append({
            "id": task.id,
            "name": task.name,
            "status": task.status.value,
            "is_actually_running": is_actually_running,
            "last_run_time": task.last_run_time,
            "running_duration": str(time_diff) if time_diff else None,
            "is_stuck": (
                not is_actually_running or 
                (time_diff and time_diff > timedelta(minutes=30))
            )
        })
    
    return {
        "total_running_tasks": len(running_tasks),
        "tasks": task_status
    }
'''
    
    print("\n建议添加的恢复机制代码:")
    print(recovery_code)

async def main():
    """主函数"""
    print("=== EasySight 诊断任务状态检查和恢复工具 ===")
    
    while True:
        print("\n请选择操作:")
        print("1. 检查运行中的任务")
        print("2. 重置卡住的任务")
        print("3. 强制重置所有运行中的任务")
        print("4. 显示恢复机制建议")
        print("5. 退出")
        
        choice = input("\n请输入选择 (1-5): ").strip()
        
        if choice == '1':
            await check_running_tasks()
        elif choice == '2':
            await reset_stuck_tasks(force_reset=False)
        elif choice == '3':
            confirm = input("确认要强制重置所有运行中的任务吗? (y/N): ").strip().lower()
            if confirm == 'y':
                await reset_stuck_tasks(force_reset=True)
            else:
                print("操作已取消")
        elif choice == '4':
            await add_task_recovery_mechanism()
        elif choice == '5':
            print("退出程序")
            break
        else:
            print("无效选择，请重新输入")

if __name__ == "__main__":
    asyncio.run(main())