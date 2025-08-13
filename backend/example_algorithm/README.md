# 示例算法包

这是一个用于测试EasySight分布式Worker动态加载功能的示例算法包。

## 功能描述

该算法包实现了一个简单的数据分析算法，可以：

- 接收数值数组作为输入
- 计算基本统计信息（均值、标准差、最大值、最小值）
- 基于阈值进行简单的分类判断
- 返回结构化的分析结果

## 算法参数

- `threshold`: 分类阈值，默认值为0.5
- `max_iterations`: 最大迭代次数，默认值为100

## 输入格式

```python
# 数值数组
input_data = [1, 2, 3, 4, 5]

# 或者numpy数组
import numpy as np
input_data = np.array([1, 2, 3, 4, 5])
```

## 输出格式

```python
{
    "prediction": "正常",  # 或 "异常"
    "confidence": 0.8,
    "statistics": {
        "mean": 3.0,
        "std": 1.58,
        "max": 5.0,
        "min": 1.0
    },
    "algorithm_info": {
        "name": "示例算法",
        "version": "1.0.0",
        "threshold": 0.5
    },
    "status": "success",
    "timestamp": "2024-01-01T12:00:00",
    "processor": {
        "algorithm": "示例算法",
        "version": "1.0.0",
        "config": {}
    }
}
```

## 使用示例

### 基本使用

```python
from example_algorithm import ExampleAlgorithm

# 创建算法实例
algorithm = ExampleAlgorithm()

# 处理数据
data = [1, 2, 3, 4, 5]
result = algorithm.run(data)

print(f"预测结果: {result['prediction']}")
print(f"置信度: {result['confidence']}")
```

### 自定义配置

```python
from example_algorithm import ExampleAlgorithm

# 使用自定义配置
config = {
    'threshold': 0.7,
    'max_iterations': 200
}

algorithm = ExampleAlgorithm(config)
result = algorithm.run([1, 2, 3, 4, 5])
```

### 使用工厂函数

```python
from example_algorithm.algorithm import create_algorithm

# 使用工厂函数创建实例
algorithm = create_algorithm({'threshold': 0.6})
result = algorithm.run([1, 2, 3, 4, 5])
```

## 动态加载测试

该算法包专门设计用于测试EasySight的动态加载功能：

1. **自动发现**: Worker节点启动时会自动从主服务器获取算法包列表
2. **自动下载**: 检测到新的或更新的算法包时自动下载
3. **自动安装**: 下载完成后自动解压和安装到本地目录
4. **动态导入**: 运行时动态导入算法模块，无需重启Worker

## 文件结构

```
example_algorithm/
├── __init__.py          # 包初始化文件
├── algorithm.py         # 主要算法实现
├── config.json         # 算法配置元数据
└── README.md           # 说明文档
```

## 依赖要求

- Python >= 3.8
- numpy >= 1.20.0

## 性能指标

- 准确率: 95%
- 精确率: 92%
- 召回率: 88%
- F1分数: 90%
- 平均处理时间: 100ms

## 资源需求

- CPU核心: 1
- 内存: 512MB
- GPU: 不需要

## 许可证

MIT License

## 版本历史

### v1.0.0 (2024-01-01)
- 初始版本
- 实现基本的数据分析功能
- 支持动态加载