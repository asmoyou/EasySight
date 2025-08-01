#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import logging
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database import get_db
from models.diagnosis import DiagnosisTask, TaskStatus
from diagnosis.scheduler import task_scheduler

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def debug_stuck_task_recovery():
    """调试卡住任务恢复机制"""
    logger.info("开始调试卡住任务恢复机制")
    
    success = False
    async for db in get_db():
        try:
            # 1. 创建一个卡住的测试任务
            logger.info("创建测试任务...")
            test_task = DiagnosisTask(
                name="调试卡住任务",
                diagnosis_types=["clarity"],
                camera_ids=[1],
                schedule_type="manual",
                status=TaskStatus.RUNNING,
                last_run_time=datetime.utcnow() - timedelta(minutes=45),
                is_active=True,
                created_by="1"
            )
            
            db.add(test_task)
            await db.commit()
            await db.refresh(test_task)
            
            task_id = test_task.id
            logger.info(f"创建的测试任务ID: {task_id}")
            logger.info(f"任务初始状态: {test_task.status}")
            logger.info(f"任务最后运行时间: {test_task.last_run_time}")
            
            # 2. 检查任务状态
            result = await db.execute(
                select(DiagnosisTask).where(DiagnosisTask.id == task_id)
            )
            task_before = result.scalar_one_or_none()
            logger.info(f"恢复前任务状态: {task_before.status}")
            logger.info(f"状态类型: {type(task_before.status)}")
            logger.info(f"TaskStatus.RUNNING: {TaskStatus.RUNNING}")
            logger.info(f"TaskStatus.PENDING: {TaskStatus.PENDING}")
            logger.info(f"状态比较 (== RUNNING): {task_before.status == TaskStatus.RUNNING}")
            
            # 3. 调用恢复方法
            logger.info("调用恢复方法...")
            await task_scheduler._check_and_recover_stuck_tasks(db)
            
            # 4. 检查恢复后的状态
            result = await db.execute(
                select(DiagnosisTask).where(DiagnosisTask.id == task_id)
            )
            task_after = result.scalar_one_or_none()
            
            if task_after:
                logger.info(f"恢复后任务状态: {task_after.status}")
                logger.info(f"状态类型: {type(task_after.status)}")
                logger.info(f"状态比较 (== PENDING): {task_after.status == TaskStatus.PENDING}")
                
                if task_after.status == TaskStatus.PENDING:
                    logger.info("✅ 恢复成功！")
                    success = True
                else:
                    logger.error(f"❌ 恢复失败，状态仍为: {task_after.status}")
                    success = False
            else:
                logger.error("❌ 找不到任务")
                success = False
            
            # 5. 清理测试数据
            await db.delete(test_task)
            await db.commit()
            logger.info("清理测试数据完成")
            
            return success
            
        except Exception as e:
            logger.error(f"调试过程中发生错误: {str(e)}")
            import traceback
            traceback.print_exc()
            success = False
        finally:
            break
    
    return success

if __name__ == "__main__":
    result = asyncio.run(debug_stuck_task_recovery())
    print(f"\n调试结果: {'✅ 成功' if result else '❌ 失败'}")