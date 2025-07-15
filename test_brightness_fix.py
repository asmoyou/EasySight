#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试亮度诊断修复
"""

import asyncio
import sys
import os

# 添加后端路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from sqlalchemy.ext.asyncio import AsyncSession
from database import async_engine
from diagnosis.executor import diagnosis_executor

async def test_brightness_diagnosis():
    """测试亮度诊断任务执行"""
    async with AsyncSession(async_engine) as db:
        try:
            print("开始测试亮度诊断任务...")
            
            # 执行任务ID为1的诊断任务
            result = await diagnosis_executor.execute_task(1, db)
            
            print(f"任务执行结果: {result}")
            
            if result.get('success'):
                print("✅ 任务执行成功！")
                print(f"结果数量: {result.get('results_count', 0)}")
                print(f"成功数量: {result.get('success_count', 0)}")
                print(f"失败数量: {result.get('error_count', 0)}")
            else:
                print(f"❌ 任务执行失败: {result.get('error', '未知错误')}")
                
        except Exception as e:
            print(f"❌ 测试过程中发生错误: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_brightness_diagnosis())