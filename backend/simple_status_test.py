import asyncio
import logging
from datetime import datetime, timedelta
from sqlalchemy import select
from models.diagnosis import DiagnosisTask, TaskStatus
from database import get_db
from diagnosis.scheduler import TaskScheduler

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def simple_test():
    """简单的状态测试"""
    logger.info("开始简单状态测试")
    success = False
    
    async for db in get_db():
        try:
            # 创建测试任务
            task = DiagnosisTask(
                name="简单测试任务",
                description="用于简单测试的任务",
                template_id=1,
                camera_ids=[],
                camera_groups=[],
                diagnosis_types=["connectivity"],
                diagnosis_config={},
                schedule_type="manual",
                schedule_config={},
                threshold_config={},
                status=TaskStatus.RUNNING,
                is_active=True,
                last_run_time=datetime.now() - timedelta(hours=1),  # 1小时前
                created_by="test_user"
            )
            
            db.add(task)
            await db.commit()
            await db.refresh(task)
            task_id = task.id
            
            logger.info(f"创建任务 ID: {task_id}")
            logger.info(f"初始状态: {task.status}")
            
            # 调用恢复方法
            task_scheduler = TaskScheduler()
            await task_scheduler._check_and_recover_stuck_tasks(db)
            
            # 重新查询任务状态
            result = await db.execute(
                select(DiagnosisTask).where(DiagnosisTask.id == task_id)
            )
            updated_task = result.scalar_one_or_none()
            
            if updated_task:
                logger.info(f"恢复后状态: {updated_task.status}")
                logger.info(f"状态类型: {type(updated_task.status)}")
                logger.info(f"TaskStatus.PENDING: {TaskStatus.PENDING}")
                logger.info(f"状态相等性检查: {updated_task.status == TaskStatus.PENDING}")
                
                # 测试条件判断
                if updated_task.status == TaskStatus.PENDING:
                    logger.info("✅ 状态检查成功！")
                    success = True
                else:
                    logger.error(f"❌ 状态检查失败！期望: {TaskStatus.PENDING}, 实际: {updated_task.status}")
                    success = False
            else:
                logger.error("❌ 找不到任务")
                success = False
                
            # 清理
            if updated_task:
                await db.delete(updated_task)
                await db.commit()
                logger.info("清理完成")
            
        except Exception as e:
            logger.error(f"测试过程中发生错误: {str(e)}")
            await db.rollback()
            success = False
        finally:
            break
    
    return success

if __name__ == "__main__":
    result = asyncio.run(simple_test())
    print(f"\n测试结果: {'✅ 成功' if result else '❌ 失败'}")