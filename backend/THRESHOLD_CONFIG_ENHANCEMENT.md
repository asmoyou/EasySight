# 诊断模板阈值配置增强

## 问题描述

之前的系统中，诊断任务创建时无法正确从诊断模板获取阈值配置参数。具体表现为：

1. 前端模板中设置的阈值（如清晰度检测阈值80）无法传递到算法实例
2. 诊断结果中显示的阈值始终是算法默认值（如清晰度检测默认100）
3. 用户在模板中配置的自定义阈值不生效

## 解决方案

### 1. 修改执行器配置传递逻辑

在 `diagnosis/executor.py` 中增强了算法配置合并逻辑：

```python
# 合并阈值配置到算法配置中
if task.threshold_config:
    # 将threshold_config中的配置合并到algorithm_config的thresholds字段中
    if 'thresholds' not in algorithm_config:
        algorithm_config['thresholds'] = {}
    
    # 合并通用阈值配置
    algorithm_config['thresholds'].update(task.threshold_config)
    
    # 特殊处理：将前端的threshold配置映射到算法期望的参数名
    if 'threshold' in task.threshold_config:
        threshold_value = task.threshold_config['threshold']
        # 根据诊断类型映射到对应的算法参数
        if diagnosis_type_str == 'clarity':
            # 前端threshold是0-1的小数，需要转换为算法期望的数值
            algorithm_config['thresholds']['clarity_min'] = threshold_value * 100
        elif diagnosis_type_str == 'brightness':
            algorithm_config['thresholds']['brightness_min'] = threshold_value
        elif diagnosis_type_str == 'contrast':
            algorithm_config['thresholds']['contrast_min'] = threshold_value
        elif diagnosis_type_str == 'noise':
            algorithm_config['thresholds']['noise_max'] = threshold_value
```

### 2. 配置映射规则

| 诊断类型 | 前端字段 | 算法参数 | 转换规则 |
|---------|---------|---------|----------|
| clarity | threshold (0-1) | clarity_min | 乘以100 |
| brightness | threshold (0-1) | brightness_min | 直接使用 |
| contrast | threshold (0-1) | contrast_min | 直接使用 |
| noise | threshold (0-1) | noise_max | 直接使用 |

### 3. 配置流程

1. **前端模板配置**：用户在诊断模板中设置阈值百分比（0-100%）
2. **数据存储**：前端将百分比转换为小数（0-1）存储在 `threshold_config.threshold` 中
3. **任务创建**：从模板复制 `threshold_config` 到诊断任务
4. **执行时配置**：执行器将 `threshold_config` 合并到算法配置的 `thresholds` 字段
5. **参数映射**：根据诊断类型将通用的 `threshold` 映射到具体的算法参数
6. **算法使用**：算法通过 `get_threshold()` 方法获取配置的阈值

## 测试验证

### 1. 单元测试

运行 `test_threshold_mapping.py` 验证配置映射逻辑：

```bash
python test_threshold_mapping.py
```

### 2. 端到端测试

运行 `test_template_to_task.py` 验证完整流程：

```bash
python test_template_to_task.py
```

### 3. 测试结果

所有测试均通过，验证了：
- ✓ 阈值配置正确映射到算法参数
- ✓ 清晰度检测阈值从默认100变为用户设置的80
- ✓ 诊断结果中显示正确的阈值
- ✓ 多种诊断类型的阈值配置都正常工作

## 使用示例

### 1. 创建诊断模板

```python
template = DiagnosisTemplate(
    name="清晰度检测模板-阈值80",
    diagnosis_types=["clarity"],
    threshold_config={
        "threshold": 0.8,  # 前端80%对应0.8
        "enabled": True,
        "level": "medium"
    }
)
```

### 2. 基于模板创建任务

```python
task = DiagnosisTask(
    name="清晰度检测任务",
    template_id=template.id,
    diagnosis_types=["clarity"],
    threshold_config=template.threshold_config  # 从模板复制阈值配置
)
```

### 3. 执行诊断

执行器会自动将模板中的阈值配置传递给算法实例，算法将使用用户配置的阈值而不是默认值。

## 影响范围

- **修改文件**：`diagnosis/executor.py`
- **新增测试**：`test_threshold_mapping.py`, `test_template_to_task.py`
- **兼容性**：向后兼容，不影响现有功能
- **性能影响**：微小的配置合并开销，可忽略

## 注意事项

1. 前端需要确保阈值配置保存在 `threshold_config.threshold` 字段中
2. 不同诊断类型的阈值参数名不同，需要正确映射
3. 清晰度检测需要特殊处理：前端0-1的小数需要乘以100转换为算法期望的数值
4. 如果模板中没有配置阈值，算法将使用默认值