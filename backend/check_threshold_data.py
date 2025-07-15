#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from database import get_db
from models.diagnosis import DiagnosisResult, DiagnosisTask

async def check_threshold_data():
    """检查诊断结果中的阈值数据"""
    async for db in get_db():
        try:
            # 查询诊断结果中的阈值数据
            result = await db.execute(
                select(
                    DiagnosisResult.id,
                    DiagnosisResult.task_id,
                    DiagnosisResult.diagnosis_type,
                    DiagnosisResult.score,
                    DiagnosisResult.threshold,
                    DiagnosisResult.created_at
                ).order_by(DiagnosisResult.created_at.desc()).limit(10)
            )
            
            results = result.all()
            
            print("最近10条诊断结果的阈值数据:")
            print("=" * 80)
            print(f"{'ID':<5} {'任务ID':<8} {'诊断类型':<15} {'分数':<8} {'阈值':<8} {'创建时间':<20}")
            print("-" * 80)
            
            for row in results:
                score_str = f"{row.score:.2f}" if row.score is not None else "None"
                threshold_str = f"{row.threshold:.2f}" if row.threshold is not None else "None"
                print(f"{row.id:<5} {row.task_id:<8} {row.diagnosis_type or 'None':<15} {score_str:<8} {threshold_str:<8} {str(row.created_at)[:19]:<20}")
            
            # 统计阈值数据
            count_result = await db.execute(
                select(
                    func.count(DiagnosisResult.id).label('total'),
                    func.count(DiagnosisResult.threshold).label('with_threshold')
                )
            )
            
            count_row = count_result.first()
            total_count = count_row.total
            threshold_count = count_row.with_threshold
            
            print("\n阈值数据统计:")
            print("=" * 40)
            print(f"总诊断结果数: {total_count}")
            print(f"有阈值数据的结果数: {threshold_count}")
            print(f"阈值数据覆盖率: {threshold_count/total_count*100:.1f}%" if total_count > 0 else "无数据")
            
            # 查看诊断任务的阈值配置
            task_result = await db.execute(
                select(
                    DiagnosisTask.id,
                    DiagnosisTask.name,
                    DiagnosisTask.diagnosis_types,
                    DiagnosisTask.threshold_config
                ).limit(5)
            )
            
            tasks = task_result.all()
            print("\n诊断任务的阈值配置:")
            print("=" * 60)
            for task in tasks:
                print(f"任务ID: {task.id}, 名称: {task.name}")
                print(f"诊断类型: {task.diagnosis_types}")
                print(f"阈值配置: {task.threshold_config}")
                print("-" * 40)
                
        except Exception as e:
            print(f"查询出错: {e}")
        finally:
            await db.close()
            break

if __name__ == "__main__":
    asyncio.run(check_threshold_data())