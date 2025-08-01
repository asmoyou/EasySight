# 人脸检测算法包

这是一个示例算法包，展示了如何为EasySight智能视频监控系统开发兼容的算法插件。

## 功能特性

- 实时人脸检测
- 人脸边界框定位
- 人脸关键点检测
- 置信度评估
- 可配置参数

## 算法信息

- **名称**: 人脸检测算法
- **版本**: 1.0.0
- **类型**: face_recognition
- **作者**: EasySight Team
- **许可证**: MIT

## 依赖要求

- Python >= 3.7
- OpenCV >= 4.5.0
- NumPy >= 1.21.0
- PyTorch >= 1.9.0 (可选，用于深度学习模型)
- Pillow >= 8.3.0

## 配置参数

### confidence_threshold
- **类型**: float
- **范围**: 0.0 - 1.0
- **默认值**: 0.5
- **描述**: 人脸检测的置信度阈值，低于此值的检测结果将被过滤

### max_faces
- **类型**: integer
- **范围**: 1 - 100
- **默认值**: 10
- **描述**: 单张图像中最大检测人脸数量

### input_size
- **类型**: array[integer, integer]
- **默认值**: [640, 480]
- **描述**: 输入图像的处理尺寸 [width, height]

## 输入格式

- **类型**: 图像文件
- **支持格式**: JPG, JPEG, PNG, BMP
- **最大尺寸**: 10MB

## 输出格式

```json
{
  "faces": [
    {
      "bbox": [x, y, width, height],
      "confidence": 0.95,
      "landmarks": [
        [x1, y1],  // 左眼
        [x2, y2],  // 右眼
        [x3, y3],  // 鼻子
        [x4, y4],  // 嘴巴左
        [x5, y5]   // 嘴巴右
      ]
    }
  ],
  "processing_time": 50.2
}
```

## 性能指标

- **准确率**: 95%
- **推理时间**: ~50ms (CPU)
- **内存占用**: ~512MB
- **GPU要求**: 否

## 支持平台

- Linux
- Windows
- macOS

## 安装说明

1. 将算法包文件打包为ZIP格式
2. 在EasySight管理界面中选择"AI统一管理"
3. 点击"上传算法包"按钮
4. 选择打包的ZIP文件
5. 系统将自动解析并安装算法包

## 使用示例

### 命令行测试

```bash
python main.py test_image.jpg
```

### 在EasySight中使用

1. 安装算法包后，在算法列表中找到"人脸检测算法"
2. 点击"配置"按钮设置参数
3. 创建AI服务并关联此算法
4. 将服务应用到摄像头或视频流

## 开发说明

### 必需文件

- `algorithm.json`: 算法配置文件
- `main.py`: 算法主程序
- `README.md`: 说明文档

### 接口规范

算法主程序必须实现以下接口：

```python
def create_algorithm(config: Dict[str, Any]) -> Algorithm:
    """创建算法实例"""
    pass

def get_algorithm_info() -> Dict[str, Any]:
    """获取算法信息"""
    pass
```

算法类必须实现：

```python
def process(self, image_data: bytes) -> Dict[str, Any]:
    """处理图像数据"""
    pass
```

## 故障排除

### 常见问题

1. **导入错误**: 确保所有依赖包已正确安装
2. **内存不足**: 调整input_size参数减少内存占用
3. **检测效果差**: 调整confidence_threshold参数

### 日志查看

算法运行日志可在EasySight系统日志中查看，日志级别为INFO。

## 更新历史

### v1.0.0 (2024-01-01)
- 初始版本发布
- 支持基础人脸检测功能
- 支持配置参数调整

## 联系方式

如有问题或建议，请联系EasySight开发团队。