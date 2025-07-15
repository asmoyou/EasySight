# 诊断算法评分标准化文档

## 概述

本文档详细说明了EasySight系统中所有诊断算法评分逻辑的标准化更新。所有算法的评分现在统一使用0-100分制，提供更直观和一致的用户体验。

## 标准化原则

### 评分范围
- **0-100分**: 统一评分范围
- **分数越高越好**: 100分表示最佳状态，0分表示最差状态
- **分级标准**: 
  - 0-60分: 异常/问题状态
  - 60-100分: 正常状态，分数越高质量越好

### 状态映射
- **CRITICAL**: 严重问题（通常0-40分）
- **WARNING**: 警告状态（通常40-70分）
- **NORMAL**: 正常状态（通常70-100分）

## 各算法详细说明

### 1. 亮度检测算法 (BrightnessAlgorithm)

**修改前问题**: 直接返回亮度值（0-255），用户难以理解评分含义

**修改后逻辑**:
- **过低亮度** (< min_threshold): 线性映射到0-60分
- **过高亮度** (> max_threshold): 线性映射到0-60分  
- **正常范围**: 根据距离最佳亮度值的偏差计算60-100分

**配置参数**:
- `brightness_min`: 最低亮度阈值（默认30）
- `brightness_max`: 最高亮度阈值（默认220）

**评分公式**:
```python
# 正常范围内
optimal_brightness = (min_threshold + max_threshold) / 2
distance_from_optimal = abs(mean_brightness - optimal_brightness)
max_distance = (max_threshold - min_threshold) / 2
score = 100 - (distance_from_optimal / max_distance) * 40
```

### 2. 清晰度检测算法 (ClarityAlgorithm)

**修改前问题**: 返回Laplacian方差值，数值范围不固定，难以理解

**修改后逻辑**:
- **模糊图像** (< min_threshold): 线性映射到0-60分
- **正常清晰度** (min_threshold ~ excellent_threshold): 线性映射到60-95分
- **优秀清晰度** (>= excellent_threshold): 95-100分

**配置参数**:
- `clarity_min`: 最低清晰度阈值（默认100）
- `clarity_excellent`: 优秀清晰度阈值（默认500）

**评分公式**:
```python
# 正常范围内
score = 60 + ((clarity_score - min_threshold) / (excellent_threshold - min_threshold)) * 35
```

### 3. 蓝屏检测算法 (BlueScreenAlgorithm)

**修改前问题**: 返回蓝色像素比例（0-1），0.08分看起来很低但实际正常

**修改后逻辑**:
- **正常情况** (蓝色比例 <= 阈值): 线性映射到60-100分
- **异常情况** (蓝色比例 > 阈值): 映射到0-60分
- **警告级别**: 蓝色比例超过阈值50%时显示警告

**配置参数**:
- `blue_screen_ratio`: 蓝屏检测阈值（默认0.8）

**评分公式**:
```python
# 正常情况
score = 100 - (blue_ratio / threshold) * 40
# 异常情况
excess_ratio = min(blue_ratio - threshold, threshold)
score = 60 - (excess_ratio / threshold) * 60
```

### 4. 噪声检测算法 (NoiseAlgorithm)

**修改前问题**: 返回噪声水平原始值，噪声越低越好但评分看起来越低

**修改后逻辑**:
- **优秀噪声水平** (<= excellent_threshold): 95-100分
- **正常噪声水平** (excellent_threshold ~ max_threshold): 60-95分
- **噪声过高** (> max_threshold): 0-60分

**配置参数**:
- `noise_max`: 最大可接受噪声水平（默认15）
- `noise_excellent`: 优秀噪声水平阈值（默认3）

**评分公式**:
```python
# 正常范围内（噪声越低分数越高）
score = 95 - ((noise_level - excellent_threshold) / (max_threshold - excellent_threshold)) * 35
```

### 5. 对比度检测算法 (ContrastAlgorithm)

**修改前问题**: 返回标准差值，用户难以理解对比度质量

**修改后逻辑**:
- **对比度过低** (< min_threshold): 线性映射到0-60分
- **正常对比度** (min_threshold ~ excellent_threshold): 线性映射到60-95分
- **优秀对比度** (>= excellent_threshold): 95-100分

**配置参数**:
- `contrast_min`: 最低对比度阈值（默认20）
- `contrast_excellent`: 优秀对比度阈值（默认60）

**评分公式**:
```python
# 正常范围内
score = 60 + ((contrast - min_threshold) / (excellent_threshold - min_threshold)) * 35
```

## 兼容性保证

### API兼容性
- 所有API接口保持不变
- 返回结果结构保持一致
- 新增字段不影响现有功能

### 数据保留
每个算法在`metrics`中同时提供：
- `raw_score`: 原始算法计算值
- `normalized_score`: 标准化后的0-100评分

### 配置灵活性
- 支持自定义所有阈值参数
- 可根据实际场景调整严格程度
- 向后兼容现有配置

## 测试验证

### 测试覆盖
- ✅ 所有算法评分都在0-100范围内
- ✅ 异常情况正确映射到低分区间
- ✅ 正常情况正确映射到高分区间
- ✅ 边界条件处理正确

### 测试结果示例
```
亮度检测: 正常图像 91.7分 (优秀)
清晰度检测: 模糊图像 0.0分 (需要改善)
蓝屏检测: 蓝屏图像 45.0分 (严重问题)
噪声检测: 低噪声图像 93.3分 (很好)
对比度检测: 高对比度图像 100.0分 (完美)
```

## 使用建议

### 评分解读
- **90-100分**: 优秀，无需改善
- **75-89分**: 良好，可接受
- **60-74分**: 一般，建议优化
- **40-59分**: 较差，需要改善
- **0-39分**: 严重问题，必须处理

### 配置调优
1. **严格模式**: 提高所有阈值，适用于高质量要求场景
2. **标准模式**: 使用默认阈值，适用于一般应用
3. **宽松模式**: 降低阈值，适用于容错性要求高的场景

### 监控建议
- 关注评分趋势变化
- 设置评分告警阈值
- 定期审查和调整配置参数

## 更新日志

### v1.1.0 (当前版本)
- ✅ 统一所有算法评分到0-100分制
- ✅ 优化评分计算逻辑
- ✅ 增加分级状态判断
- ✅ 保留原始数据兼容性
- ✅ 完善配置参数支持

### v1.0.0 (原始版本)
- 各算法使用不同的评分范围
- 用户体验不一致
- 评分含义不够直观

---

**注意**: 此更新完全向后兼容，不会影响现有系统的正常运行。建议在生产环境部署前进行充分测试。