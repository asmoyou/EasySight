#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试真实诊断任务中的算法评分
"""

import asyncio
import numpy as np
from diagnosis.executor import DiagnosisExecutor
from diagnosis.algorithms import get_algorithm
from models.diagnosis import DiagnosisType

def create_sample_image():
    """创建一个示例图像"""
    # 创建一个正常的测试图像
    image = np.random.randint(80, 180, (480, 640, 3), dtype=np.uint8)
    return image

def test_individual_algorithms():
    """测试各个算法的评分"""
    print("=== 单独测试各算法的标准化评分 ===")
    
    image = create_sample_image()
    
    # 测试所有算法类型
    algorithm_types = [
        (DiagnosisType.BRIGHTNESS, "亮度检测"),
        (DiagnosisType.CLARITY, "清晰度检测"),
        (DiagnosisType.BLUE_SCREEN, "蓝屏检测"),
        (DiagnosisType.NOISE, "噪声检测"),
        (DiagnosisType.CONTRAST, "对比度检测")
    ]
    
    results = {}
    
    for diagnosis_type, name in algorithm_types:
        try:
            algorithm = get_algorithm(diagnosis_type)
            result = algorithm.diagnose(image)
            
            score = result['score']
            status = result['status']
            message = result['message']
            metrics = result.get('metrics', {})
            
            results[name] = {
                'score': score,
                'status': status.value,
                'message': message,
                'raw_score': metrics.get('raw_score', 'N/A'),
                'normalized_score': metrics.get('normalized_score', score)
            }
            
            print(f"\n{name}:")
            print(f"  标准化评分: {score:.1f}/100")
            print(f"  状态: {status.value}")
            print(f"  消息: {message}")
            print(f"  原始值: {metrics.get('raw_score', 'N/A')}")
            
            # 验证评分范围
            if 0 <= score <= 100:
                print(f"  ✅ 评分在有效范围内")
            else:
                print(f"  ❌ 评分超出范围: {score}")
                
        except Exception as e:
            print(f"\n{name}: ❌ 错误 - {str(e)}")
            results[name] = {'error': str(e)}
    
    return results

def test_score_consistency():
    """测试评分一致性"""
    print("\n=== 评分一致性测试 ===")
    
    # 创建不同质量的图像
    test_cases = {
        '高质量图像': np.random.randint(100, 150, (480, 640, 3), dtype=np.uint8),
        '低质量图像': np.random.randint(20, 60, (480, 640, 3), dtype=np.uint8),
        '蓝屏图像': np.full((480, 640, 3), [255, 0, 0], dtype=np.uint8)  # BGR蓝色
    }
    
    for case_name, image in test_cases.items():
        print(f"\n{case_name}:")
        
        # 测试亮度算法
        brightness_algo = get_algorithm(DiagnosisType.BRIGHTNESS)
        brightness_result = brightness_algo.diagnose(image)
        print(f"  亮度评分: {brightness_result['score']:.1f}")
        
        # 测试蓝屏算法
        blue_screen_algo = get_algorithm(DiagnosisType.BLUE_SCREEN)
        blue_screen_result = blue_screen_algo.diagnose(image)
        print(f"  蓝屏评分: {blue_screen_result['score']:.1f}")
        
        # 验证蓝屏图像的评分逻辑
        if case_name == '蓝屏图像':
            if blue_screen_result['score'] < 60:
                print(f"  ✅ 蓝屏正确识别为低分")
            else:
                print(f"  ❌ 蓝屏评分异常: {blue_screen_result['score']}")

def main():
    """主测试函数"""
    print("诊断算法标准化评分验证")
    print("=" * 50)
    
    # 测试各个算法
    results = test_individual_algorithms()
    
    # 测试评分一致性
    test_score_consistency()
    
    # 总结
    print("\n" + "=" * 50)
    print("测试总结:")
    
    all_valid = True
    for name, result in results.items():
        if 'error' in result:
            print(f"❌ {name}: 测试失败")
            all_valid = False
        elif 0 <= result['score'] <= 100:
            print(f"✅ {name}: 评分标准化成功 ({result['score']:.1f}/100)")
        else:
            print(f"❌ {name}: 评分超出范围 ({result['score']:.1f})")
            all_valid = False
    
    if all_valid:
        print("\n🎉 所有算法评分已成功标准化到0-100分制！")
    else:
        print("\n⚠️  部分算法需要进一步调整")
    
    print("\n评分标准:")
    print("- 90-100分: 优秀")
    print("- 75-89分: 良好")
    print("- 60-74分: 一般")
    print("- 40-59分: 较差")
    print("- 0-39分: 严重问题")

if __name__ == "__main__":
    main()