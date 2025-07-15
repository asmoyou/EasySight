#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查诊断结果数据
"""

import asyncio
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from database import async_engine
from models.diagnosis import DiagnosisResult

async def check_diagnosis_results():
    """检查诊断结果"""
    try:
        async with AsyncSession(async_engine) as db:
            # 查询最新的诊断结果
            result = await db.execute(
                select(DiagnosisResult)
                .order_by(DiagnosisResult.created_at.desc())
                .limit(5)
            )
            results = result.scalars().all()
            
            print(f"最新的5条诊断结果:")
            for i, diagnosis_result in enumerate(results, 1):
                print(f"\n{i}. ID: {diagnosis_result.id}")
                print(f"   任务ID: {diagnosis_result.task_id}")
                print(f"   摄像头ID: {diagnosis_result.camera_id}")
                print(f"   诊断类型: {diagnosis_result.diagnosis_type}")
                print(f"   状态: {diagnosis_result.diagnosis_status}")
                print(f"   阈值: {diagnosis_result.threshold}")
                print(f"   结果数据: {diagnosis_result.result_data}")
                print(f"   创建时间: {diagnosis_result.created_at}")
                
            # 统计总数
            count_result = await db.execute(
                select(text("COUNT(*)")).select_from(DiagnosisResult)
            )
            total_count = count_result.scalar()
            print(f"\n诊断结果总数: {total_count}")
            
    except Exception as e:
        print(f"❌ 查询诊断结果失败: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(check_diagnosis_results())