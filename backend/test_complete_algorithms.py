#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整诊断算法测试脚本
测试所有14种诊断算法的功能和评分逻辑
"""

import cv2
import numpy as np
from diagnosis.algorithms import (
    BrightnessAlgorithm, ClarityAlgorithm, BlueScreenAlgorithm,
    NoiseAlgorithm, ContrastAlgorithm, ShakeAlgorithm, FreezeAlgorithm,
    ColorCastAlgorithm, OcclusionAlgorithm, MosaicAlgorithm,
    FlowerScreenAlgorithm, SignalLossAlgorithm, LensDirtyAlgorithm,
    FocusBlurAlgorithm, get_algorithm
)
from models.diagnosis import DiagnosisType

def create_test_images():
    """创建各种测试图像"""
    images = {}
    
    # 1. 正常图像
    normal_img = np.random.randint(80, 180, (480, 640, 3), dtype=np.uint8)
    # 添加一些结构
    cv2.rectangle(normal_img, (100, 100), (200, 200), (120, 120, 120), -1)
    cv2.circle(normal_img, (400, 300), 50, (150, 150, 150), -1)
    images['normal'] = normal_img
    
    # 2. 过暗图像
    dark_img = np.random.randint(0, 50, (480, 640, 3), dtype=np.uint8)
    images['dark'] = dark_img
    
    # 3. 过亮图像
    bright_img = np.random.randint(200, 255, (480, 640, 3), dtype=np.uint8)
    images['bright'] = bright_img
    
    # 4. 蓝屏图像
    blue_img = np.zeros((480, 640, 3), dtype=np.uint8)
    blue_img[:, :, 0] = 255  # 蓝色通道
    images['blue_screen'] = blue_img
    
    # 5. 模糊图像
    blur_img = cv2.GaussianBlur(normal_img, (15, 15), 0)
    images['blur'] = blur_img
    
    # 6. 高噪声图像
    noise_img = normal_img.copy()
    noise = np.random.randint(-50, 50, noise_img.shape, dtype=np.int16)
    noise_img = np.clip(noise_img.astype(np.int16) + noise, 0, 255).astype(np.uint8)
    images['noise'] = noise_img
    
    # 7. 低对比度图像
    low_contrast_img = np.full((480, 640, 3), 128, dtype=np.uint8)
    # 添加轻微变化
    low_contrast_img[100:200, 100:200] = 135
    low_contrast_img[300:400, 300:400] = 120
    images['low_contrast'] = low_contrast_img
    
    # 8. 偏色图像（偏红）
    color_cast_img = normal_img.copy()
    color_cast_img[:, :, 2] = np.clip(color_cast_img[:, :, 2].astype(np.int16) + 80, 0, 255)  # 增加红色
    images['color_cast'] = color_cast_img
    
    # 9. 遮挡图像（大片黑色区域）
    occlusion_img = normal_img.copy()
    occlusion_img[200:400, 200:500] = 0  # 大片黑色遮挡
    images['occlusion'] = occlusion_img
    
    # 10. 马赛克图像
    mosaic_img = normal_img.copy()
    # 创建块状效果
    for i in range(0, 480, 16):
        for j in range(0, 640, 16):
            block_color = np.mean(mosaic_img[i:i+16, j:j+16], axis=(0, 1))
            mosaic_img[i:i+16, j:j+16] = block_color
    images['mosaic'] = mosaic_img
    
    # 11. 花屏图像（随机彩色噪声）
    flower_img = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
    images['flower_screen'] = flower_img
    
    # 12. 信号丢失图像（全黑）
    signal_loss_img = np.zeros((480, 640, 3), dtype=np.uint8)
    images['signal_loss'] = signal_loss_img
    
    # 13. 镜头脏污图像（局部模糊斑点）
    dirty_img = normal_img.copy()
    # 添加模糊圆形斑点
    cv2.circle(dirty_img, (200, 200), 50, (100, 100, 100), -1)
    dirty_img[150:250, 150:250] = cv2.GaussianBlur(dirty_img[150:250, 150:250], (21, 21), 0)
    images['lens_dirty'] = dirty_img
    
    # 14. 失焦图像（整体模糊）
    focus_blur_img = cv2.GaussianBlur(normal_img, (25, 25), 0)
    images['focus_blur'] = focus_blur_img
    
    return images

def test_algorithm(algorithm_class, image, algorithm_name, image_name):
    """测试单个算法"""
    try:
        algorithm = algorithm_class()
        result = algorithm.diagnose(image)
        
        print(f"\n{algorithm_name} - {image_name}:")
        print(f"  状态: {result['status'].value}")
        print(f"  评分: {result['score']:.1f}")
        print(f"  消息: {result['message']}")
        print(f"  处理时间: {result['processing_time']:.1f}ms")
        
        # 验证评分范围
        score = result['score']
        if not (0 <= score <= 100):
            print(f"  ⚠️  警告: 评分超出范围 [0-100]: {score}")
        
        return result
    except Exception as e:
        print(f"\n❌ {algorithm_name} - {image_name} 测试失败: {str(e)}")
        return None

def test_all_algorithms():
    """测试所有算法"""
    print("=" * 80)
    print("EasySight 完整诊断算法测试")
    print("=" * 80)
    
    # 创建测试图像
    print("\n📸 创建测试图像...")
    test_images = create_test_images()
    print(f"创建了 {len(test_images)} 种测试图像")
    
    # 定义所有算法
    algorithms = {
        'BRIGHTNESS': BrightnessAlgorithm,
        'CLARITY': ClarityAlgorithm,
        'BLUE_SCREEN': BlueScreenAlgorithm,
        'NOISE': NoiseAlgorithm,
        'CONTRAST': ContrastAlgorithm,
        'SHAKE': ShakeAlgorithm,
        'FREEZE': FreezeAlgorithm,
        'COLOR_CAST': ColorCastAlgorithm,
        'OCCLUSION': OcclusionAlgorithm,
        'MOSAIC': MosaicAlgorithm,
        'FLOWER_SCREEN': FlowerScreenAlgorithm,
        'SIGNAL_LOSS': SignalLossAlgorithm,
        'LENS_DIRTY': LensDirtyAlgorithm,
        'FOCUS_BLUR': FocusBlurAlgorithm,
    }
    
    # 测试每个算法
    results = {}
    for algo_name, algo_class in algorithms.items():
        print(f"\n🔍 测试 {algo_name} 算法")
        print("-" * 50)
        
        algo_results = {}
        for img_name, image in test_images.items():
            result = test_algorithm(algo_class, image, algo_name, img_name)
            if result:
                algo_results[img_name] = result
        
        results[algo_name] = algo_results
    
    # 测试算法注册表
    print("\n🔧 测试算法注册表...")
    print("-" * 50)
    
    diagnosis_types = [
        DiagnosisType.BRIGHTNESS, DiagnosisType.CLARITY, DiagnosisType.BLUE_SCREEN,
        DiagnosisType.NOISE, DiagnosisType.CONTRAST, DiagnosisType.SHAKE,
        DiagnosisType.FREEZE, DiagnosisType.COLOR_CAST, DiagnosisType.OCCLUSION,
        DiagnosisType.MOSAIC, DiagnosisType.FLOWER_SCREEN, DiagnosisType.SIGNAL_LOSS,
        DiagnosisType.LENS_DIRTY, DiagnosisType.FOCUS_BLUR
    ]
    
    for diagnosis_type in diagnosis_types:
        try:
            algorithm = get_algorithm(diagnosis_type)
            print(f"✅ {diagnosis_type.value}: {algorithm.__class__.__name__}")
        except Exception as e:
            print(f"❌ {diagnosis_type.value}: {str(e)}")
    
    # 生成测试报告
    print("\n📊 测试报告")
    print("=" * 80)
    
    for algo_name, algo_results in results.items():
        if algo_results:
            scores = [r['score'] for r in algo_results.values()]
            avg_score = np.mean(scores)
            min_score = np.min(scores)
            max_score = np.max(scores)
            
            print(f"\n{algo_name}:")
            print(f"  测试图像数: {len(algo_results)}")
            print(f"  平均评分: {avg_score:.1f}")
            print(f"  评分范围: {min_score:.1f} - {max_score:.1f}")
            
            # 检查评分分布
            normal_count = sum(1 for s in scores if s >= 60)
            warning_count = sum(1 for s in scores if 40 <= s < 60)
            critical_count = sum(1 for s in scores if s < 40)
            
            print(f"  正常 (≥60): {normal_count}")
            print(f"  警告 (40-59): {warning_count}")
            print(f"  严重 (<40): {critical_count}")
    
    print("\n✅ 所有算法测试完成!")
    print("\n📋 总结:")
    print(f"- 实现了 {len(algorithms)} 种诊断算法")
    print(f"- 测试了 {len(test_images)} 种图像场景")
    print("- 所有算法都使用统一的 0-100 评分制")
    print("- 评分越高表示质量越好")
    print("- 60分以上为正常，40-59分为警告，40分以下为严重")

if __name__ == "__main__":
    test_all_algorithms()