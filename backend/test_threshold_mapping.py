#!/usr/bin/env python3
"""
测试阈值配置映射功能
验证从诊断模板的threshold_config正确传递到算法实例
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from models.diagnosis import DiagnosisTask, DiagnosisType, TaskStatus
from diagnosis.executor import DiagnosisExecutor
from diagnosis.algorithms import get_algorithm
import json

async def test_threshold_mapping():
    """测试阈值配置映射"""
    print("=== 测试阈值配置映射 ===")
    
    # 测试1: 直接测试算法配置传递
    print("\n1. 测试算法配置传递:")
    
    # 模拟前端传递的threshold_config
    threshold_config = {
        'threshold': 0.8,  # 前端80%对应0.8
        'enabled': True,
        'level': 'medium'
    }
    
    # 模拟executor中的配置合并逻辑
    algorithm_config = {}
    diagnosis_type_str = 'clarity'
    
    # 合并阈值配置到算法配置中
    if threshold_config:
        if 'thresholds' not in algorithm_config:
            algorithm_config['thresholds'] = {}
        
        # 合并通用阈值配置
        algorithm_config['thresholds'].update(threshold_config)
        
        # 特殊处理：将前端的threshold配置映射到算法期望的参数名
        if 'threshold' in threshold_config:
            threshold_value = threshold_config['threshold']
            # 根据诊断类型映射到对应的算法参数
            if diagnosis_type_str == 'clarity':
                # 前端threshold是0-1的小数，需要转换为算法期望的数值
                # 假设前端0.8对应算法的80（基于100的比例）
                algorithm_config['thresholds']['clarity_min'] = threshold_value * 100
            elif diagnosis_type_str == 'brightness':
                algorithm_config['thresholds']['brightness_min'] = threshold_value
            elif diagnosis_type_str == 'contrast':
                algorithm_config['thresholds']['contrast_min'] = threshold_value
            elif diagnosis_type_str == 'noise':
                algorithm_config['thresholds']['noise_max'] = threshold_value
    
    print(f"原始threshold_config: {json.dumps(threshold_config, indent=2)}")
    print(f"合并后algorithm_config: {json.dumps(algorithm_config, indent=2)}")
    
    # 测试2: 创建算法实例并验证阈值获取
    print("\n2. 测试算法实例阈值获取:")
    
    algorithm = get_algorithm(DiagnosisType.CLARITY, algorithm_config)
    clarity_min = algorithm.get_threshold('clarity_min', 100)
    
    print(f"算法获取的clarity_min阈值: {clarity_min}")
    print(f"期望值: 80.0")
    print(f"测试结果: {'✓ 通过' if clarity_min == 80.0 else '✗ 失败'}")
    
    # 测试3: 测试其他诊断类型的映射
    print("\n3. 测试其他诊断类型的映射:")
    
    test_cases = [
        ('brightness', 'brightness_min', 0.6),
        ('contrast', 'contrast_min', 0.7),
        ('noise', 'noise_max', 0.3)
    ]
    
    for diagnosis_type, param_name, threshold_value in test_cases:
        test_config = {'threshold': threshold_value}
        algo_config = {'thresholds': {}}
        
        # 应用映射逻辑
        if diagnosis_type == 'clarity':
            algo_config['thresholds']['clarity_min'] = threshold_value * 100
        elif diagnosis_type == 'brightness':
            algo_config['thresholds']['brightness_min'] = threshold_value
        elif diagnosis_type == 'contrast':
            algo_config['thresholds']['contrast_min'] = threshold_value
        elif diagnosis_type == 'noise':
            algo_config['thresholds']['noise_max'] = threshold_value
        
        print(f"  {diagnosis_type}: {param_name} = {algo_config['thresholds'].get(param_name, 'N/A')}")
    
    print("\n=== 测试完成 ===")

async def test_database_task():
    """测试数据库中的诊断任务配置"""
    print("\n=== 测试数据库任务配置 ===")
    
    async for db in get_db():
        try:
            # 创建测试任务
            test_task = DiagnosisTask(
                name="阈值映射测试任务",
                diagnosis_types=["clarity"],
                camera_ids=[1],  # 假设存在camera id=1
                diagnosis_config={
                    "clarity": {
                        "sample_interval": 30
                    }
                },
                threshold_config={
                    "threshold": 0.8,  # 前端80%
                    "enabled": True,
                    "level": "medium"
                },
                status=TaskStatus.PENDING
            )
            
            print(f"测试任务threshold_config: {json.dumps(test_task.threshold_config, indent=2)}")
            
            # 模拟executor中的配置处理
            diagnosis_type_str = "clarity"
            algorithm_config = test_task.diagnosis_config.get(diagnosis_type_str, {})
            
            # 合并阈值配置
            if test_task.threshold_config:
                if 'thresholds' not in algorithm_config:
                    algorithm_config['thresholds'] = {}
                
                algorithm_config['thresholds'].update(test_task.threshold_config)
                
                if 'threshold' in test_task.threshold_config:
                    threshold_value = test_task.threshold_config['threshold']
                    if diagnosis_type_str == 'clarity':
                        algorithm_config['thresholds']['clarity_min'] = threshold_value * 100
            
            print(f"处理后algorithm_config: {json.dumps(algorithm_config, indent=2)}")
            
            # 创建算法实例测试
            algorithm = get_algorithm(DiagnosisType.CLARITY, algorithm_config)
            clarity_min = algorithm.get_threshold('clarity_min', 100)
            
            print(f"算法实例获取的clarity_min: {clarity_min}")
            print(f"配置传递: {'✓ 成功' if clarity_min == 80.0 else '✗ 失败'}")
            
        except Exception as e:
            print(f"测试过程中出现错误: {e}")
        finally:
            await db.close()
        break

if __name__ == "__main__":
    # 运行测试
    asyncio.run(test_threshold_mapping())
    asyncio.run(test_database_task())