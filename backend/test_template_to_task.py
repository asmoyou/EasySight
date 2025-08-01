#!/usr/bin/env python3
"""
端到端测试：从诊断模板创建任务并执行诊断
验证阈值配置从模板正确传递到诊断结果
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import get_db
from models.diagnosis import DiagnosisTemplate, DiagnosisTask, DiagnosisType, TaskStatus
from routers.diagnosis import DiagnosisTaskCreate
import json
import numpy as np
from diagnosis.algorithms import get_algorithm

async def test_template_to_task_flow():
    """测试从模板创建任务的完整流程"""
    print("=== 端到端测试：模板 -> 任务 -> 诊断 ===")
    
    async for db in get_db():
        try:
            # 1. 创建测试模板
            print("\n1. 创建测试诊断模板:")
            
            template = DiagnosisTemplate(
                name="清晰度检测模板-阈值80",
                diagnosis_types=["clarity"],  # 修正字段名
                description="用于测试阈值配置传递的清晰度检测模板",
                default_config={  # 修正字段名
                    "sample_interval": 30,
                    "detection_area": "full"
                },
                threshold_config={
                    "threshold": 0.8,  # 前端80%对应0.8
                    "enabled": True,
                    "level": "medium"
                },
                default_schedule={},
                is_active=True
            )
            
            db.add(template)
            await db.commit()
            await db.refresh(template)
            
            print(f"创建模板ID: {template.id}")
            print(f"模板threshold_config: {json.dumps(template.threshold_config, indent=2)}")
            
            # 2. 基于模板创建诊断任务
            print("\n2. 基于模板创建诊断任务:")
            
            task = DiagnosisTask(
                name="基于模板的清晰度检测任务",
                template_id=template.id,
                diagnosis_types=["clarity"],
                camera_ids=[1],  # 假设存在camera id=1
                diagnosis_config=template.default_config,  # 从模板复制配置
                threshold_config=template.threshold_config,  # 从模板复制阈值配置
                status=TaskStatus.PENDING
            )
            
            db.add(task)
            await db.commit()
            await db.refresh(task)
            
            print(f"创建任务ID: {task.id}")
            print(f"任务diagnosis_config: {json.dumps(task.diagnosis_config, indent=2)}")
            print(f"任务threshold_config: {json.dumps(task.threshold_config, indent=2)}")
            
            # 3. 模拟executor中的配置处理
            print("\n3. 模拟executor配置处理:")
            
            diagnosis_type_str = "clarity"
            algorithm_config = task.diagnosis_config.get(diagnosis_type_str, {})
            
            # 应用我们修改的配置合并逻辑
            if task.threshold_config:
                if 'thresholds' not in algorithm_config:
                    algorithm_config['thresholds'] = {}
                
                # 合并通用阈值配置
                algorithm_config['thresholds'].update(task.threshold_config)
                
                # 特殊处理：将前端的threshold配置映射到算法期望的参数名
                if 'threshold' in task.threshold_config:
                    threshold_value = task.threshold_config['threshold']
                    if diagnosis_type_str == 'clarity':
                        algorithm_config['thresholds']['clarity_min'] = threshold_value * 100
            
            print(f"处理后algorithm_config: {json.dumps(algorithm_config, indent=2)}")
            
            # 4. 创建算法实例并测试
            print("\n4. 创建算法实例并测试:")
            
            algorithm = get_algorithm(DiagnosisType.CLARITY, algorithm_config)
            clarity_min = algorithm.get_threshold('clarity_min', 100)
            
            print(f"算法获取的clarity_min阈值: {clarity_min}")
            print(f"期望值: 80.0 (来自模板配置)")
            print(f"阈值传递: {'✓ 成功' if clarity_min == 80.0 else '✗ 失败'}")
            
            # 5. 模拟诊断执行
            print("\n5. 模拟诊断执行:")
            
            # 创建测试图像（模糊图像）
            test_image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
            # 添加高斯模糊使图像变模糊
            import cv2
            blurred_image = cv2.GaussianBlur(test_image, (15, 15), 0)
            
            # 执行诊断
            diagnosis_result = algorithm.diagnose(blurred_image)
            
            print(f"诊断结果:")
            print(f"  状态: {diagnosis_result['status']}")
            print(f"  评分: {diagnosis_result['score']:.1f}")
            print(f"  阈值: {diagnosis_result['threshold']}")
            print(f"  消息: {diagnosis_result['message']}")
            
            # 验证阈值是否正确
            expected_threshold = 80.0
            actual_threshold = diagnosis_result['threshold']
            
            print(f"\n阈值验证:")
            print(f"  期望阈值: {expected_threshold}")
            print(f"  实际阈值: {actual_threshold}")
            print(f"  验证结果: {'✓ 通过' if actual_threshold == expected_threshold else '✗ 失败'}")
            
            # 6. 清理测试数据
            print("\n6. 清理测试数据:")
            await db.delete(task)
            await db.delete(template)
            await db.commit()
            print("测试数据已清理")
            
        except Exception as e:
            print(f"测试过程中出现错误: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await db.close()
        break

async def test_multiple_diagnosis_types():
    """测试多种诊断类型的阈值配置"""
    print("\n=== 测试多种诊断类型的阈值配置 ===")
    
    test_cases = [
        {
            'type': 'clarity',
            'threshold': 0.8,
            'expected_param': 'clarity_min',
            'expected_value': 80.0
        },
        {
            'type': 'brightness', 
            'threshold': 0.6,
            'expected_param': 'brightness_min',
            'expected_value': 0.6
        },
        {
            'type': 'contrast',
            'threshold': 0.7,
            'expected_param': 'contrast_min', 
            'expected_value': 0.7
        },
        {
            'type': 'noise',
            'threshold': 0.3,
            'expected_param': 'noise_max',
            'expected_value': 0.3
        }
    ]
    
    for case in test_cases:
        print(f"\n测试 {case['type']} 类型:")
        
        # 模拟配置处理
        threshold_config = {'threshold': case['threshold']}
        algorithm_config = {'thresholds': {}}
        
        # 应用映射逻辑
        algorithm_config['thresholds'].update(threshold_config)
        
        if 'threshold' in threshold_config:
            threshold_value = threshold_config['threshold']
            if case['type'] == 'clarity':
                algorithm_config['thresholds']['clarity_min'] = threshold_value * 100
            elif case['type'] == 'brightness':
                algorithm_config['thresholds']['brightness_min'] = threshold_value
            elif case['type'] == 'contrast':
                algorithm_config['thresholds']['contrast_min'] = threshold_value
            elif case['type'] == 'noise':
                algorithm_config['thresholds']['noise_max'] = threshold_value
        
        # 验证配置
        actual_value = algorithm_config['thresholds'].get(case['expected_param'])
        expected_value = case['expected_value']
        
        print(f"  配置: threshold={case['threshold']}")
        print(f"  映射: {case['expected_param']}={actual_value}")
        print(f"  期望: {expected_value}")
        print(f"  结果: {'✓ 通过' if actual_value == expected_value else '✗ 失败'}")

if __name__ == "__main__":
    # 运行测试
    asyncio.run(test_template_to_task_flow())
    asyncio.run(test_multiple_diagnosis_types())