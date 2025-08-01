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

async def debug_status_comparison():
    """调试状态比较问题"""
    logger.info("开始调试状态比较问题")
    success = False
    
    async for db in get_db():
        try:
            # 创建测试任务
            task = DiagnosisTask(
                name="调试状态比较",
                description="用于调试状态比较的测试任务",
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
            logger.info(f"状态类型: {type(task.status)}")
            logger.info(f"状态repr: {repr(task.status)}")
            
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
                logger.info(f"状态repr: {repr(updated_task.status)}")
                
                # 详细的比较测试
                logger.info(f"== TaskStatus.PENDING: {updated_task.status == TaskStatus.PENDING}")
                logger.info(f"== 'PENDING': {updated_task.status == 'PENDING'}")
                logger.info(f"TaskStatus.PENDING repr: {repr(TaskStatus.PENDING)}")
                
                # 检查是否相等
                if updated_task.status == TaskStatus.PENDING:
                    logger.info("✅ 状态比较成功！")
                    success = True
                else:
                    logger.error(f"❌ 状态比较失败！期望: {TaskStatus.PENDING}, 实际: {updated_task.status}")
                    success = False
            else:
                logger.error("❌ 找不到任务")
                success = False
                
            # 清理
            if updated_task:
                await db.delete(updated_task)
                await db.commit()
                logger.info("清理测试数据完成")
                
        except Exception as e:
            logger.error(f"调试过程中发生错误: {str(e)}")
            await db.rollback()
            success = False
        finally:
            break
    
    return success

if __name__ == "__main__":
    result = asyncio.run(debug_status_comparison())
    print(f"\n调试结果: {'✅ 成功' if result else '❌ 失败'}")