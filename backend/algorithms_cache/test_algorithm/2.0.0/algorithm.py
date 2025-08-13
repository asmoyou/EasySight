#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
示例算法实现

这是一个用于测试动态加载功能的示例算法实现
"""

import numpy as np
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

class ExampleAlgorithm:
    """示例算法类"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化算法
        
        Args:
            config: 算法配置参数
        """
        self.config = config or {}
        self.name = "示例算法"
        self.version = "1.0.0"
        self.description = "这是一个用于测试动态加载功能的示例算法"
        
        # 算法参数
        self.threshold = self.config.get('threshold', 0.5)
        self.max_iterations = self.config.get('max_iterations', 100)
        
        logger.info(f"初始化 {self.name} v{self.version}")
    
    def preprocess(self, data: Any) -> Any:
        """数据预处理
        
        Args:
            data: 输入数据
            
        Returns:
            预处理后的数据
        """
        logger.info("执行数据预处理")
        
        if isinstance(data, (list, tuple)):
            return np.array(data)
        elif isinstance(data, np.ndarray):
            return data
        else:
            # 对于其他类型的数据，尝试转换为numpy数组
            try:
                return np.array(data)
            except Exception as e:
                logger.error(f"数据预处理失败: {str(e)}")
                raise ValueError(f"无法处理的数据类型: {type(data)}")
    
    def process(self, data: Any) -> Dict[str, Any]:
        """主要处理逻辑
        
        Args:
            data: 输入数据
            
        Returns:
            处理结果
        """
        logger.info("开始执行算法处理")
        
        try:
            # 预处理数据
            processed_data = self.preprocess(data)
            
            # 模拟算法处理
            if isinstance(processed_data, np.ndarray):
                # 计算一些统计信息
                mean_value = float(np.mean(processed_data))
                std_value = float(np.std(processed_data))
                max_value = float(np.max(processed_data))
                min_value = float(np.min(processed_data))
                
                # 模拟分类或检测结果
                confidence = min(1.0, max(0.0, mean_value / (std_value + 1e-6)))
                prediction = "正常" if confidence > self.threshold else "异常"
                
                result = {
                    'prediction': prediction,
                    'confidence': confidence,
                    'statistics': {
                        'mean': mean_value,
                        'std': std_value,
                        'max': max_value,
                        'min': min_value
                    },
                    'algorithm_info': {
                        'name': self.name,
                        'version': self.version,
                        'threshold': self.threshold
                    },
                    'status': 'success'
                }
            else:
                # 对于非数值数据，返回基本信息
                result = {
                    'prediction': '未知',
                    'confidence': 0.0,
                    'message': f'处理了 {type(processed_data)} 类型的数据',
                    'algorithm_info': {
                        'name': self.name,
                        'version': self.version
                    },
                    'status': 'success'
                }
            
            logger.info(f"算法处理完成，结果: {result['prediction']}")
            return result
            
        except Exception as e:
            logger.error(f"算法处理失败: {str(e)}")
            return {
                'prediction': '错误',
                'confidence': 0.0,
                'error': str(e),
                'algorithm_info': {
                    'name': self.name,
                    'version': self.version
                },
                'status': 'error'
            }
    
    def postprocess(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """后处理
        
        Args:
            result: 处理结果
            
        Returns:
            后处理后的结果
        """
        logger.info("执行后处理")
        
        # 添加时间戳
        from datetime import datetime
        result['timestamp'] = datetime.now().isoformat()
        
        # 添加处理器信息
        result['processor'] = {
            'algorithm': self.name,
            'version': self.version,
            'config': self.config
        }
        
        return result
    
    def run(self, data: Any) -> Dict[str, Any]:
        """运行完整的算法流程
        
        Args:
            data: 输入数据
            
        Returns:
            最终结果
        """
        logger.info(f"运行 {self.name} 算法")
        
        # 执行主要处理
        result = self.process(data)
        
        # 执行后处理
        final_result = self.postprocess(result)
        
        logger.info("算法运行完成")
        return final_result
    
    def get_info(self) -> Dict[str, Any]:
        """获取算法信息
        
        Returns:
            算法信息
        """
        return {
            'name': self.name,
            'version': self.version,
            'description': self.description,
            'config': self.config,
            'parameters': {
                'threshold': self.threshold,
                'max_iterations': self.max_iterations
            }
        }
    
    def update_config(self, new_config: Dict[str, Any]):
        """更新配置
        
        Args:
            new_config: 新的配置参数
        """
        logger.info(f"更新算法配置: {new_config}")
        
        self.config.update(new_config)
        
        # 更新相关参数
        self.threshold = self.config.get('threshold', self.threshold)
        self.max_iterations = self.config.get('max_iterations', self.max_iterations)
        
        logger.info("配置更新完成")

# 算法工厂函数
def create_algorithm(config: Optional[Dict[str, Any]] = None) -> ExampleAlgorithm:
    """创建算法实例
    
    Args:
        config: 算法配置
        
    Returns:
        算法实例
    """
    return ExampleAlgorithm(config)

# 算法元数据
ALGORITHM_METADATA = {
    'name': '示例算法',
    'version': '1.0.0',
    'description': '用于测试动态加载功能的示例算法',
    'author': 'EasySight Team',
    'input_types': ['array', 'list', 'number'],
    'output_type': 'dict',
    'parameters': {
        'threshold': {
            'type': 'float',
            'default': 0.5,
            'description': '分类阈值'
        },
        'max_iterations': {
            'type': 'int',
            'default': 100,
            'description': '最大迭代次数'
        }
    }
}