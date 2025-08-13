#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
人脸检测算法主程序

这是一个示例算法包，展示了如何实现EasySight兼容的算法插件。
"""

import cv2
import numpy as np
import json
import time
from typing import Dict, List, Any, Tuple
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FaceDetectionAlgorithm:
    """人脸检测算法类"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化算法
        
        Args:
            config: 算法配置参数
        """
        self.config = config
        self.confidence_threshold = config.get('confidence_threshold', 0.5)
        self.max_faces = config.get('max_faces', 10)
        self.input_size = tuple(config.get('input_size', [640, 480]))
        
        # 初始化人脸检测器（使用OpenCV的Haar级联分类器作为示例）
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        
        logger.info(f"算法初始化完成，配置: {self.config}")
    
    def preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """
        图像预处理
        
        Args:
            image: 输入图像
            
        Returns:
            预处理后的图像
        """
        # 转换为灰度图
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        # 调整图像尺寸
        if gray.shape[:2] != self.input_size[::-1]:  # OpenCV使用(height, width)
            gray = cv2.resize(gray, self.input_size)
        
        return gray
    
    def detect_faces(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """
        检测人脸
        
        Args:
            image: 输入图像
            
        Returns:
            检测结果列表
        """
        # 预处理图像
        gray = self.preprocess_image(image)
        
        # 检测人脸
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30)
        )
        
        results = []
        for i, (x, y, w, h) in enumerate(faces[:self.max_faces]):
            # 计算置信度（这里使用简单的面积比例作为示例）
            confidence = min(1.0, (w * h) / (gray.shape[0] * gray.shape[1]) * 10)
            
            if confidence >= self.confidence_threshold:
                # 生成简单的关键点（眼睛、鼻子、嘴巴位置的估计）
                landmarks = [
                    [x + w * 0.3, y + h * 0.3],  # 左眼
                    [x + w * 0.7, y + h * 0.3],  # 右眼
                    [x + w * 0.5, y + h * 0.5],  # 鼻子
                    [x + w * 0.3, y + h * 0.7],  # 嘴巴左
                    [x + w * 0.7, y + h * 0.7],  # 嘴巴右
                ]
                
                results.append({
                    'bbox': [int(x), int(y), int(w), int(h)],
                    'confidence': float(confidence),
                    'landmarks': landmarks
                })
        
        return results
    
    def process(self, image_data: bytes) -> Dict[str, Any]:
        """
        处理图像数据
        
        Args:
            image_data: 图像字节数据
            
        Returns:
            处理结果
        """
        start_time = time.time()
        
        try:
            # 解码图像
            nparr = np.frombuffer(image_data, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if image is None:
                raise ValueError("无法解码图像数据")
            
            # 检测人脸
            faces = self.detect_faces(image)
            
            # 计算处理时间
            processing_time = (time.time() - start_time) * 1000
            
            result = {
                'faces': faces,
                'processing_time': processing_time
            }
            
            logger.info(f"检测到 {len(faces)} 个人脸，处理时间: {processing_time:.2f}ms")
            return result
            
        except Exception as e:
            logger.error(f"图像处理失败: {e}")
            raise


def create_algorithm(config: Dict[str, Any]) -> FaceDetectionAlgorithm:
    """
    创建算法实例（EasySight插件接口）
    
    Args:
        config: 算法配置
        
    Returns:
        算法实例
    """
    return FaceDetectionAlgorithm(config)


def get_algorithm_info() -> Dict[str, Any]:
    """
    获取算法信息（EasySight插件接口）
    
    Returns:
        算法信息
    """
    return {
        'name': '人脸检测算法',
        'version': '1.0.0',
        'type': 'face_recognition',
        'description': '基于深度学习的人脸检测算法，支持实时检测和识别',
        'author': 'EasySight Team'
    }


if __name__ == '__main__':
    # 测试代码
    import sys
    
    if len(sys.argv) < 2:
        print("用法: python main.py <image_path>")
        sys.exit(1)
    
    # 默认配置
    config = {
        'confidence_threshold': 0.5,
        'max_faces': 10,
        'input_size': [640, 480]
    }
    
    # 创建算法实例
    algorithm = create_algorithm(config)
    
    # 读取测试图像
    image_path = sys.argv[1]
    with open(image_path, 'rb') as f:
        image_data = f.read()
    
    # 处理图像
    result = algorithm.process(image_data)
    
    # 输出结果
    print(json.dumps(result, indent=2, ensure_ascii=False))