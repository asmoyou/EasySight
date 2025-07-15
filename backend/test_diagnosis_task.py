#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试实际诊断任务执行
"""

import asyncio
from diagnosis.executor import diagnosis_executor
from database import get_db

async def test_diagnosis_task():
    """测试诊断任务执行"""
    print('测试实际诊断任务执行...')
    
    try:
        async for db in get_db():
            # 执行任务ID为1的诊断任务
            result = await diagnosis_executor.execute_task(1, db)
            print(f'诊断任务执行结果: {result}')
            break
    except Exception as e:
        print(f'执行失败: {str(e)}')
        print('这可能是因为任务ID 1不存在或数据库连接问题')

if __name__ == '__main__':
    asyncio.run(test_diagnosis_task())