#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试卡住任务自动恢复机制

该脚本用于测试调度器中新增的自动检测和恢复卡住任务的功能。
"""

import asyncio
import logging
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database import get_db
from models.diagnosis import DiagnosisTask, TaskStatus
from diagnosis.scheduler import task_scheduler
from diagnosis.executor import diagnosis_executor

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def create_stuck_task_scenario():
    """创建卡住任务的测试场景"""
    result = None
    async for db in get_db():
        try:
            # 创建一个测试任务
            test_task = DiagnosisTask(
                name="测试卡住任务",
                diagnosis_types=["clarity"],
                camera_ids=[1],
                schedule_type="manual",
                status=TaskStatus.RUNNING,  # 设置为运行状态
                last_run_time=datetime.utcnow() - timedelta(minutes=45),  # 45分钟前开始运行
                is_active=True,
                created_by="1"
            )
            
            db.add(test_task)
            await db.commit()
            await db.refresh(test_task)
            
            logger.info(f"创建测试任务: {test_task.name} (ID: {test_task.id})")
            logger.info(f"任务状态: {test_task.status}")
            logger.info(f"最后运行时间: {test_task.last_run_time}")
            
            # 故意不将任务添加到执行器的运行列表中，模拟卡住状态
            logger.info(f"执行器运行任务列表: {diagnosis_executor.running_tasks}")
            logger.info(f"任务 {test_task.id} 是否在执行器中: {test_task.id in diagnosis_executor.running_tasks}")
            
            result = test_task.id
            
        except Exception as e:
            logger.error(f"创建测试任务失败: {str(e)}")
            await db.rollback()
            result = None
        finally:
            break
    
    return result

async def test_stuck_task_detection():
    """测试卡住任务检测"""
    logger.info("\n=== 测试卡住任务检测 ===")
    
    # 创建卡住任务场景
    task_id = await create_stuck_task_scenario()
    if not task_id:
        logger.error("无法创建测试任务")
        return False
    
    # 等待一下，然后手动调用检测方法
    await asyncio.sleep(2)
    
    result = False
    async for db in get_db():
        try:
            # 手动调用卡住任务检测方法
            logger.info("手动调用卡住任务检测方法...")
            await task_scheduler._check_and_recover_stuck_tasks(db)
            
            # 检查任务状态是否已恢复
            query_result = await db.execute(
                select(DiagnosisTask).where(DiagnosisTask.id == task_id)
            )
            task = query_result.scalar_one_or_none()
            
            if task:
                logger.info(f"检测后任务状态: {task.status}")
                if task.status == TaskStatus.PENDING:
                    logger.info("✅ 卡住任务检测和恢复成功！")
                    result = True
                else:
                    logger.error(f"❌ 任务状态未恢复，当前状态: {task.status}")
                    result = False
            else:
                logger.error("❌ 找不到测试任务")
                result = False
                
        except Exception as e:
            logger.error(f"测试卡住任务检测失败: {str(e)}")
            result = False
        finally:
            break
    
    return result

async def test_scheduler_integration():
    """测试调度器集成"""
    logger.info("\n=== 测试调度器集成 ===")
    
    # 创建另一个卡住任务
    task_id = await create_stuck_task_scenario()
    if not task_id:
        logger.error("无法创建测试任务")
        return False
    
    result = False
    async for db in get_db():
        try:
            # 调用调度器的检查方法（包含自动恢复）
            logger.info("调用调度器检查方法...")
            await task_scheduler._check_and_schedule_tasks(db)
            
            # 检查任务状态
            query_result = await db.execute(
                select(DiagnosisTask).where(DiagnosisTask.id == task_id)
            )
            task = query_result.scalar_one_or_none()
            
            if task and task.status == TaskStatus.PENDING:
                logger.info("✅ 调度器自动恢复机制工作正常！")
                result = True
            else:
                logger.error(f"❌ 调度器自动恢复失败，任务状态: {task.status if task else 'None'}")
                result = False
                
        except Exception as e:
            logger.error(f"测试调度器集成失败: {str(e)}")
            result = False
        finally:
            break
    
    return result

async def test_normal_running_task():
    """测试正常运行的任务不会被误恢复"""
    logger.info("\n=== 测试正常运行任务保护 ===")
    
    result = False
    async for db in get_db():
        try:
            # 创建一个正常运行的任务
            test_task = DiagnosisTask(
                name="正常运行任务",
                diagnosis_types=["brightness"],
                camera_ids=[1],
                schedule_type="manual",
                status=TaskStatus.RUNNING,
                last_run_time=datetime.utcnow() - timedelta(minutes=5),  # 5分钟前开始
                is_active=True,
                created_by="1"
            )
            
            db.add(test_task)
            await db.commit()
            await db.refresh(test_task)
            
            # 将任务添加到执行器运行列表中，模拟正常运行
            diagnosis_executor.running_tasks.add(test_task.id)
            
            logger.info(f"创建正常运行任务: {test_task.name} (ID: {test_task.id})")
            logger.info(f"任务在执行器中: {test_task.id in diagnosis_executor.running_tasks}")
            
            # 调用检测方法
            await task_scheduler._check_and_recover_stuck_tasks(db)
            
            # 检查任务状态是否保持运行
            await db.refresh(test_task)
            
            if test_task.status == TaskStatus.RUNNING:
                logger.info("✅ 正常运行的任务未被误恢复！")
                # 清理
                diagnosis_executor.running_tasks.discard(test_task.id)
                result = True
            else:
                logger.error(f"❌ 正常运行的任务被误恢复，状态: {test_task.status}")
                result = False
                
        except Exception as e:
            logger.error(f"测试正常运行任务保护失败: {str(e)}")
            result = False
        finally:
            break
    
    return result

async def cleanup_test_tasks():
    """清理测试任务"""
    async for db in get_db():
        try:
            # 删除所有测试任务
            result = await db.execute(
                select(DiagnosisTask).where(
                    DiagnosisTask.name.in_(["测试卡住任务", "正常运行任务"])
                )
            )
            test_tasks = result.scalars().all()
            
            for task in test_tasks:
                await db.delete(task)
                # 从执行器中移除
                diagnosis_executor.running_tasks.discard(task.id)
            
            await db.commit()
            logger.info(f"清理了 {len(test_tasks)} 个测试任务")
            
        except Exception as e:
            logger.error(f"清理测试任务失败: {str(e)}")
        finally:
            break

async def main():
    """主测试函数"""
    logger.info("开始测试卡住任务自动恢复机制")
    
    try:
        # 运行测试
        test1_result = await test_stuck_task_detection()
        test2_result = await test_scheduler_integration()
        test3_result = await test_normal_running_task()
        
        # 清理测试数据
        await cleanup_test_tasks()
        
        # 总结结果
        logger.info("\n=== 测试结果总结 ===")
        logger.info(f"卡住任务检测: {'✅ 通过' if test1_result else '❌ 失败'}")
        logger.info(f"调度器集成: {'✅ 通过' if test2_result else '❌ 失败'}")
        logger.info(f"正常任务保护: {'✅ 通过' if test3_result else '❌ 失败'}")
        
        all_passed = test1_result and test2_result and test3_result
        logger.info(f"\n总体结果: {'✅ 所有测试通过' if all_passed else '❌ 部分测试失败'}")
        
        if all_passed:
            logger.info("\n🎉 卡住任务自动恢复机制工作正常！")
            logger.info("调度器现在会每分钟自动检测和恢复卡住的任务。")
        else:
            logger.error("\n⚠️  部分功能存在问题，请检查日志。")
            
    except Exception as e:
        logger.error(f"测试过程中发生错误: {str(e)}")
        await cleanup_test_tasks()

if __name__ == "__main__":
    asyncio.run(main())