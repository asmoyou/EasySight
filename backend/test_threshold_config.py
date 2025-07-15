#!/usr/bin/env python3
"""
测试阈值配置的保存和传递
"""

import asyncio
import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import get_db
from models.diagnosis import DiagnosisTask, DiagnosisResult

async def test_threshold_config():
    """测试阈值配置的保存和传递"""
    async for db in get_db():
        try:
            # 1. 查询现有任务的阈值配置
            print("=== 检查现有任务的阈值配置 ===")
            result = await db.execute(
                select(DiagnosisTask.id, DiagnosisTask.name, DiagnosisTask.threshold_config)
                .order_by(DiagnosisTask.created_at.desc())
                .limit(5)
            )
            tasks = result.all()
            
            for task in tasks:
                print(f"任务ID: {task.id}")
                print(f"任务名称: {task.name}")
                print(f"阈值配置: {task.threshold_config}")
                print("-" * 50)
            
            # 2. 创建一个测试任务，包含阈值配置
            print("\n=== 创建测试任务 ===")
            test_threshold_config = {
                "brightness": {
                    "min_threshold": 30,
                    "max_threshold": 200,
                    "warning_threshold": 50
                },
                "alarm_settings": {
                    "enable_alarm": True,
                    "severity": "warning"
                }
            }
            
            new_task = DiagnosisTask(
                name="阈值配置测试任务",
                description="测试阈值配置的保存和传递",
                diagnosis_types=["brightness"],
                camera_ids=[1],  # 假设存在ID为1的摄像头
                diagnosis_config={"test": "config"},
                threshold_config=test_threshold_config,
                schedule_config={},
                status="pending",
                is_active=True,
                created_by=1  # 假设存在ID为1的用户
            )
            
            db.add(new_task)
            await db.commit()
            await db.refresh(new_task)
            
            print(f"创建的任务ID: {new_task.id}")
            print(f"保存的阈值配置: {json.dumps(new_task.threshold_config, indent=2, ensure_ascii=False)}")
            
            # 3. 查询刚创建的任务，验证阈值配置是否正确保存
            print("\n=== 验证任务保存 ===")
            result = await db.execute(
                select(DiagnosisTask).where(DiagnosisTask.id == new_task.id)
            )
            saved_task = result.scalar_one_or_none()
            
            if saved_task:
                print(f"查询到的任务: {saved_task.name}")
                print(f"查询到的阈值配置: {json.dumps(saved_task.threshold_config, indent=2, ensure_ascii=False)}")
                
                # 验证阈值配置是否一致
                if saved_task.threshold_config == test_threshold_config:
                    print("✅ 阈值配置保存成功！")
                else:
                    print("❌ 阈值配置保存失败！")
                    print(f"期望: {test_threshold_config}")
                    print(f"实际: {saved_task.threshold_config}")
            else:
                print("❌ 未找到保存的任务")
            
            # 4. 检查诊断结果中的阈值数据
            print("\n=== 检查诊断结果中的阈值数据 ===")
            result = await db.execute(
                select(
                    DiagnosisResult.id,
                    DiagnosisResult.task_id,
                    DiagnosisResult.threshold,
                    DiagnosisResult.result_data
                ).order_by(DiagnosisResult.created_at.desc()).limit(3)
            )
            
            results = result.all()
            for res in results:
                print(f"结果ID: {res.id}, 任务ID: {res.task_id}")
                print(f"阈值: {res.threshold}")
                if res.result_data and 'threshold_config' in res.result_data:
                    print(f"结果数据中的阈值配置: {res.result_data['threshold_config']}")
                print("-" * 30)
            
        except Exception as e:
            print(f"测试过程中出现错误: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await db.close()
            break

if __name__ == "__main__":
    asyncio.run(test_threshold_config())