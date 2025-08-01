#!/usr/bin/env python3

import asyncio
from database import get_db
from models.diagnosis import DiagnosisTask
from sqlalchemy import select
import json
from datetime import datetime, timezone

async def create_test_task():
    async for db in get_db():
        try:
            # 创建一个简单的测试任务
            test_task = DiagnosisTask(
                name="Worker测试任务",
                description="用于测试分布式Worker功能的任务",
                template_id=1,  # 假设存在模板ID 1
                camera_ids=[],
                camera_groups=[],
                diagnosis_types=["clarity"],
                diagnosis_config={"test": True},
                schedule_type="manual",
                schedule_config={},
                threshold_config={},
                status="PENDING",
                is_active=True,
                created_by="1",  # 假设用户ID 1
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            
            db.add(test_task)
            await db.commit()
            await db.refresh(test_task)
            
            print(f"测试任务创建成功: ID={test_task.id}, 名称={test_task.name}, 状态={test_task.status}")
            
            # 查看当前所有PENDING任务
            result = await db.execute(select(DiagnosisTask).where(
                DiagnosisTask.is_active == True,
                DiagnosisTask.status == 'PENDING'
            ))
            pending_tasks = result.scalars().all()
            print(f"\n当前PENDING任务数量: {len(pending_tasks)}")
            for task in pending_tasks:
                print(f"- ID: {task.id}, 名称: {task.name}, 分配给: {task.assigned_worker}")
            
            break
        except Exception as e:
            print(f"错误: {e}")
            import traceback
            traceback.print_exc()
            break

if __name__ == "__main__":
    asyncio.run(create_test_task())