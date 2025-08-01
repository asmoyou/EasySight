#!/usr/bin/env python3

import asyncio
from database import get_db
from models.diagnosis import DiagnosisTask
from sqlalchemy import select, update

async def enable_task():
    async for db in get_db():
        try:
            # 查看所有任务状态
            result = await db.execute(select(DiagnosisTask))
            tasks = result.scalars().all()
            print("所有任务状态:")
            for task in tasks:
                print(f"ID: {task.id}, 名称: {task.name}, 状态: {task.status}, 启用: {task.is_active}")
            
            # 启用任务3
            result = await db.execute(select(DiagnosisTask).where(DiagnosisTask.id == 3))
            task = result.scalar_one_or_none()
            if task:
                print(f"\n启用前 - 任务3: 状态={task.status}, 启用={task.is_active}")
                task.is_active = True
                task.status = 'PENDING'  # 设置为待处理状态
                await db.commit()
                print(f"启用后 - 任务3: 状态={task.status}, 启用={task.is_active}")
            else:
                print("未找到任务3")
            break
        except Exception as e:
            print(f"错误: {e}")
            break

if __name__ == "__main__":
    asyncio.run(enable_task())