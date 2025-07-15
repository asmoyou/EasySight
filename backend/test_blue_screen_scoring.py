#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
蓝屏检测算法评分测试
"""

from diagnosis.algorithms import BlueScreenAlgorithm
import numpy as np
import cv2

def test_blue_screen_scoring():
    """测试蓝屏检测算法的评分逻辑"""
    print('=== 蓝屏检测算法评分测试 ===')
    algo = BlueScreenAlgorithm()
    
    # 测试1: 正常图像（随机颜色）
    print('\n测试1: 随机颜色图像')
    test_image1 = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
    result1 = algo.diagnose(test_image1)
    print(f'蓝色比例: {result1["metrics"]["blue_ratio"]:.3f}')
    print(f'评分: {result1["score"]:.1f}')
    print(f'状态: {result1["status"].value}')
    print(f'消息: {result1["message"]}')
    
    # 测试2: 纯蓝色图像（模拟蓝屏）
    print('\n测试2: 纯蓝色图像（模拟蓝屏）')
    test_image2 = np.full((480, 640, 3), [255, 0, 0], dtype=np.uint8)  # BGR格式的蓝色
    result2 = algo.diagnose(test_image2)
    print(f'蓝色比例: {result2["metrics"]["blue_ratio"]:.3f}')
    print(f'评分: {result2["score"]:.1f}')
    print(f'状态: {result2["status"].value}')
    print(f'消息: {result2["message"]}')
    
    # 测试3: 部分蓝色图像（警告级别）
    print('\n测试3: 半蓝色图像（警告级别）')
    test_image3 = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
    test_image3[:240, :] = [255, 0, 0]  # 上半部分设为蓝色
    result3 = algo.diagnose(test_image3)
    print(f'蓝色比例: {result3["metrics"]["blue_ratio"]:.3f}')
    print(f'评分: {result3["score"]:.1f}')
    print(f'状态: {result3["status"].value}')
    print(f'消息: {result3["message"]}')
    
    # 测试4: 纯黑色图像
    print('\n测试4: 纯黑色图像')
    test_image4 = np.zeros((480, 640, 3), dtype=np.uint8)
    result4 = algo.diagnose(test_image4)
    print(f'蓝色比例: {result4["metrics"]["blue_ratio"]:.3f}')
    print(f'评分: {result4["score"]:.1f}')
    print(f'状态: {result4["status"].value}')
    print(f'消息: {result4["message"]}')
    
    # 测试5: 纯白色图像
    print('\n测试5: 纯白色图像')
    test_image5 = np.full((480, 640, 3), [255, 255, 255], dtype=np.uint8)
    result5 = algo.diagnose(test_image5)
    print(f'蓝色比例: {result5["metrics"]["blue_ratio"]:.3f}')
    print(f'评分: {result5["score"]:.1f}')
    print(f'状态: {result5["status"].value}')
    print(f'消息: {result5["message"]}')
    
    print('\n=== 评分逻辑说明 ===')
    print('- 评分范围: 0-100分')
    print('- 100分: 完全正常（无蓝色）')
    print('- 60-100分: 正常范围')
    print('- 0-60分: 异常范围')
    print('- 蓝色比例阈值: 80%（可配置）')
    print('- 警告阈值: 40%（阈值的一半）')
    
    print('\n=== 测试完成 ===')

if __name__ == '__main__':
    test_blue_screen_scoring()