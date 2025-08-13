# EasySight 智能安防平台 - 完整项目说明书

## 📖 项目概述

### 项目简介
EasySight 是一个通用的分布式智能安防平台，致力于提供商业项目所需的所有基础能力。在此基础上，开发者可以专注于业务算法的开发，从而快速实现自己的业务需求，减少重复造轮子的时间，提高开发效率，进一步推动AI技术的应用和发展。

### 项目特色
- **通用性强**: 提供完整的智能安防基础设施
- **分布式架构**: 支持多节点部署和负载均衡
- **算法可扩展**: 支持动态加载和管理AI算法包
- **容器化部署**: 基于Docker的微服务架构
- **现代化UI**: 简洁优雅的用户界面设计

## 🏗️ 技术架构

### 前端技术栈
- **框架**: Vue 3.3.8
- **UI组件库**: Element Plus 2.4.2
- **构建工具**: Vite 4.5.0
- **包管理**: Yarn
- **开发语言**: TypeScript 5.2.0
- **状态管理**: Pinia 2.1.7
- **路由**: Vue Router 4.2.5
- **图表**: ECharts 5.6.0
- **视频播放**: Video.js 8.6.1

### 后端技术栈
- **框架**: FastAPI 0.104.1
- **ASGI服务器**: Uvicorn 0.24.0
- **开发语言**: Python 3.8+
- **数据库**: PostgreSQL 15
- **缓存**: Redis 7.2.5
- **对象存储**: MinIO
- **消息队列**: RabbitMQ
- **ORM**: SQLAlchemy 2.0.23
- **数据库迁移**: Alembic 1.12.1
- **图像处理**: OpenCV 4.8.1.78, Pillow 10.1.0
- **认证**: JWT (python-jose)

### 流媒体服务
- **媒体服务器**: ZLMediaKit
- **协议支持**: RTSP, RTMP, WebRTC, SRT
- **API端口**: 18080 (流媒体服务), 8060 (ZLMediaKit)
- **流媒体端口**: 554 (RTSP), 1935 (RTMP), 10000 (RTP)

### 部署架构
- **容器化**: Docker + Docker Compose
- **微服务**: 前后端分离 + 流媒体服务
- **数据持久化**: PostgreSQL + MinIO + Redis
- **负载均衡**: 支持多Worker节点分布式部署

## ✨ 核心功能特性

### 1. 用户管理系统
- **多租户支持**: 支持多租户架构
- **角色权限**: 基于RBAC的权限管理
- **用户认证**: JWT令牌认证机制
- **会话管理**: 支持令牌刷新和过期管理

### 2. 摄像头管理
- **设备管理**: 摄像头的增删改查
- **实时监控**: 多屏播放支持1/4/9/16分屏
- **流媒体代理**: 支持多种流媒体协议
- **设备状态监控**: 实时监控摄像头在线状态

### 3. AI应用中心
- **算法市场**: 上传和管理AI算法包
- **动态加载**: 支持运行时动态加载算法
- **版本管理**: 支持多版本算法并存
- **配置管理**: 灵活的算法参数配置
- **分布式执行**: 支持多Worker节点分布式处理

### 4. 智能诊断系统
- **14种诊断算法**: 覆盖常见的视频质量问题
  - 亮度检测 (BRIGHTNESS)
  - 清晰度检测 (CLARITY)
  - 对比度检测 (CONTRAST)
  - 噪声检测 (NOISE)
  - 蓝屏检测 (BLUE_SCREEN)
  - 冻结检测 (FREEZE)
  - 抖动检测 (JITTER)
  - 偏色检测 (COLOR_CAST)
  - 遮挡检测 (OCCLUSION)
  - 马赛克检测 (MOSAIC)
  - 花屏检测 (DISTORTION)
  - 信号丢失检测 (SIGNAL_LOSS)
  - 过曝检测 (OVEREXPOSURE)
  - 欠曝检测 (UNDEREXPOSURE)
- **统一评分**: 0-100分制评分系统
- **任务调度**: 支持定时和手动诊断任务
- **结果分析**: 详细的诊断报告和建议

### 5. 事件告警中心
- **实时告警**: 基于AI分析的实时事件告警
- **告警规则**: 灵活的告警规则配置
- **通知渠道**: 多种通知方式支持
- **事件记录**: 完整的事件历史记录

### 6. 系统配置管理
- **版本信息**: 系统版本和更新信息
- **存储配置**: 数据保留策略配置
- **流媒体管理**: 流媒体节点管理
- **消息中心**: 消息推送配置
- **系统监控**: 系统性能指标监控

### 7. 仪表盘
- **数据可视化**: 基于ECharts的数据展示
- **实时统计**: 系统运行状态统计
- **性能监控**: 系统性能指标展示
- **趋势分析**: 历史数据趋势分析

## 🚀 快速开始

### 环境要求
- **Node.js**: >= 16.0.0
- **Yarn**: >= 1.22.0
- **Python**: >= 3.8
- **Docker**: 推荐使用Docker & Docker Compose
- **操作系统**: Linux, Windows, macOS

### 1. 克隆项目
```bash
git clone <repository-url>
cd EasySight
```

### 2. 启动基础服务
```bash
# 启动数据库、缓存、对象存储等基础服务
docker-compose up -d
```

### 3. 后端服务部署
```bash
# 进入后端目录
cd backend

# 创建虚拟环境
python -m venv .venv

# 激活虚拟环境 (Windows)
.venv\Scripts\activate
# 激活虚拟环境 (Linux/macOS)
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 启动开发服务器
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 4. 前端服务部署
```bash
# 进入前端目录
cd web

# 安装依赖
yarn install

# 启动开发服务器
yarn dev

# 构建生产版本
yarn build
```

### 5. 流媒体服务部署
```bash
# 进入流媒体服务目录
cd zlmediakitServer

# 安装依赖
pip install -r requirements.txt

# 启动服务
python main.py
```

### 6. 默认登录信息
- **管理员账号**: admin
- **管理员密码**: admin123

## 📁 项目结构

```
EasySight/
├── README.md                          # 项目说明
├── docker-compose.yaml                # Docker编排文件
├── QUICK_START_WORKER.md              # Worker快速启动指南
├── PROJECT_DOCUMENTATION.md           # 完整项目说明书
├── backend/                           # 后端服务
│   ├── main.py                       # 主应用入口
│   ├── config.py                     # 配置文件
│   ├── database.py                   # 数据库连接
│   ├── requirements.txt              # Python依赖
│   ├── alembic/                      # 数据库迁移
│   ├── models/                       # 数据模型
│   ├── routers/                      # API路由
│   ├── middleware/                   # 中间件
│   ├── diagnosis/                    # 诊断系统
│   ├── tasks/                        # 后台任务
│   ├── utils/                        # 工具函数
│   ├── scripts/                      # 脚本文件
│   ├── algorithms_cache/             # 算法缓存
│   ├── packages/                     # 算法包
│   └── *.md                         # 技术文档
├── web/                              # 前端应用
│   ├── src/                         # 源代码
│   │   ├── views/                   # 页面组件
│   │   ├── components/              # 通用组件
│   │   ├── api/                     # API接口
│   │   ├── stores/                  # 状态管理
│   │   ├── router/                  # 路由配置
│   │   ├── types/                   # 类型定义
│   │   └── utils/                   # 工具函数
│   ├── public/                      # 静态资源
│   ├── package.json                 # 前端依赖
│   └── vite.config.ts              # Vite配置
├── zlmediakitServer/                 # 流媒体服务
│   ├── main.py                      # 服务入口
│   ├── config.py                    # 配置文件
│   ├── requirements.txt             # Python依赖
│   ├── utils/                       # 工具模块
│   └── *.md                        # 服务文档
├── example-algorithm-package/        # 算法包示例
└── data/                            # 数据目录
    ├── postgres_data/               # PostgreSQL数据
    ├── minio_data/                  # MinIO数据
    └── mysql_data/                  # MySQL数据(可选)
```

## 🔧 配置说明

### 环境变量配置

#### 后端配置 (backend/.env)
```env
# 数据库配置
DATABASE_URL=postgresql://rotanova:RotaNova%402025@127.0.0.1:5432/easysight

# Redis配置
REDIS_URL=redis://127.0.0.1:6379/0

# MinIO配置
MINIO_ENDPOINT=127.0.0.1:9000
MINIO_ACCESS_KEY=rotanova
MINIO_SECRET_KEY=RotaNova@2025
MINIO_BUCKET_NAME=easysight

# RabbitMQ配置
RABBITMQ_URL=amqp://rotanova:RotaNova@2025@127.0.0.1:5672/

# JWT配置
SECRET_KEY=your-secret-key-here-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=60

# 应用配置
DEBUG=True
MAX_FILE_SIZE=104857600  # 100MB
```

#### 流媒体服务配置
```env
# MinIO配置
minio_host=192.168.2.177:9000

# MySQL配置
mysql_host=192.168.2.177

# ZLMediaKit配置
zlm_host=192.168.2.177

# 日志配置
LOG_DEBUG=False
LOG_FILE=logs/mediaworker.log
```

### 端口配置

| 服务 | 端口 | 用途 |
|------|------|------|
| 前端开发服务器 | 5173 | Vue开发服务器 |
| 后端API服务 | 8000 | FastAPI服务 |
| 流媒体服务 | 18080 | 流媒体管理API |
| ZLMediaKit | 8060 | 媒体服务器API |
| PostgreSQL | 5432 | 数据库 |
| Redis | 6379 | 缓存 |
| MinIO | 9000/9001 | 对象存储 |
| RabbitMQ | 5672/15672 | 消息队列 |
| RTSP | 554 | 视频流接收 |
| RTMP | 1935 | 直播推流 |

## 🤖 AI算法开发指南

### 完整诊断算法实现

EasySight 系统现已实现了完整的 14 种诊断算法，覆盖了视频监控系统中常见的各种图像质量问题。所有算法都采用统一的 0-100 分制评分系统，分数越高表示质量越好。

#### 基础质量检测算法

**1. 亮度检测 (BRIGHTNESS)**
- **功能**: 检测图像亮度是否在合理范围内
- **算法**: 计算图像平均亮度，根据阈值范围评分
- **评分逻辑**:
  - 过低/过高 (< 30 或 > 220): 0-60分
  - 正常范围: 60-100分，距离最佳值越近分数越高
- **配置参数**:
  - `brightness_min`: 最低亮度阈值 (默认: 30)
  - `brightness_max`: 最高亮度阈值 (默认: 220)

**2. 清晰度检测 (CLARITY)**
- **功能**: 检测图像清晰度
- **算法**: 使用 Laplacian 算子计算图像锐度
- **评分逻辑**:
  - 模糊 (< 100): 0-60分
  - 正常: 60-95分
  - 优秀 (≥ 500): 95-100分
- **配置参数**:
  - `clarity_min`: 最低清晰度阈值 (默认: 100)
  - `clarity_excellent`: 优秀清晰度阈值 (默认: 500)

**3. 对比度检测 (CONTRAST)**
- **功能**: 检测图像对比度
- **算法**: 计算图像灰度值标准差
- **评分逻辑**:
  - 过低 (< 20): 0-60分
  - 正常: 60-95分
  - 优秀 (≥ 60): 95-100分
- **配置参数**:
  - `contrast_min`: 最低对比度阈值 (默认: 20)
  - `contrast_excellent`: 优秀对比度阈值 (默认: 60)

**4. 噪声检测 (NOISE)**
- **功能**: 检测图像噪声水平
- **算法**: 使用高斯滤波去噪后计算差异
- **评分逻辑**:
  - 噪声过高 (> 15): 0-60分
  - 正常: 60-95分
  - 优秀 (≤ 3): 95-100分
- **配置参数**:
  - `noise_max`: 最大噪声阈值 (默认: 15)
  - `noise_excellent`: 优秀噪声阈值 (默认: 3)

#### 特殊问题检测算法

**5. 蓝屏检测 (BLUE_SCREEN)**
- **功能**: 检测蓝屏故障
- **算法**: 在 HSV 色彩空间检测蓝色区域比例
- **评分逻辑**:
  - 蓝色比例过高: 0-60分
  - 正常: 60-100分
- **配置参数**:
  - `blue_screen_ratio`: 蓝屏阈值 (默认: 0.8)

**6. 冻结检测 (FREEZE)**
- **功能**: 检测画面冻结
- **算法**: 计算连续帧间差异
- **评分逻辑**:
  - 疑似冻结 (< 0.01): 0-60分
  - 轻微变化: 60-95分
  - 正常变化 (≥ 0.05): 95-100分
- **配置参数**:
  - `freeze_threshold`: 冻结阈值 (默认: 0.01)
  - `freeze_normal`: 正常变化阈值 (默认: 0.05)

**7. 抖动检测 (JITTER)**
- **功能**: 检测图像抖动
- **算法**: 结合边缘检测和梯度方差分析
- **评分逻辑**:
  - 抖动严重 (< 0.5): 0-60分
  - 正常: 60-95分
  - 非常稳定 (≥ 2.0): 95-100分
- **配置参数**:
  - `jitter_min`: 最低稳定性阈值 (默认: 0.5)
  - `jitter_excellent`: 优秀稳定性阈值 (默认: 2.0)

**8. 偏色检测 (COLOR_CAST)**
- **功能**: 检测图像偏色问题
- **算法**: 计算 RGB 三通道平均值偏差
- **评分逻辑**:
  - 严重偏色 (≥ 50): 0-40分
  - 轻微偏色 (20-50): 40-60分
  - 颜色正常 (< 20): 60-100分
- **配置参数**:
  - `color_cast_threshold`: 偏色阈值 (默认: 20)
  - `color_cast_severe`: 严重偏色阈值 (默认: 50)

**9. 遮挡检测 (OCCLUSION)**
- **功能**: 检测镜头遮挡
- **算法**: 结合暗区域检测和边缘密度分析
- **评分逻辑**:
  - 严重遮挡 (≥ 0.6): 0-40分
  - 轻微遮挡 (0.3-0.6): 40-60分
  - 无遮挡 (< 0.3): 60-100分
- **配置参数**:
  - `occlusion_threshold`: 遮挡阈值 (默认: 0.3)
  - `occlusion_severe`: 严重遮挡阈值 (默认: 0.6)
  - `occlusion_dark_threshold`: 暗区域阈值 (默认: 30)

**10. 马赛克检测 (MOSAIC)**
- **功能**: 检测马赛克化失真
- **算法**: 使用形态学操作和霍夫直线检测
- **评分逻辑**:
  - 严重马赛克 (≥ 0.5): 0-40分
  - 轻微马赛克 (0.2-0.5): 40-60分
  - 无马赛克 (< 0.2): 60-100分
- **配置参数**:
  - `mosaic_threshold`: 马赛克阈值 (默认: 0.2)
  - `mosaic_severe`: 严重马赛克阈值 (默认: 0.5)

**11. 花屏检测 (DISTORTION)**
- **功能**: 检测花屏故障
- **算法**: 分析颜色分布异常、饱和像素和噪声模式
- **评分逻辑**:
  - 严重花屏 (≥ 0.6): 0-40分
  - 轻微花屏 (0.3-0.6): 40-60分
  - 无花屏 (< 0.3): 60-100分
- **配置参数**:
  - `distortion_threshold`: 花屏阈值 (默认: 0.3)
  - `distortion_severe`: 严重花屏阈值 (默认: 0.6)

**12. 信号丢失检测 (SIGNAL_LOSS)**
- **功能**: 检测信号丢失
- **算法**: 检测全黑/全白区域、图像方差和边缘密度
- **评分逻辑**:
  - 严重信号丢失 (≥ 0.7): 0-40分
  - 信号不稳定 (0.3-0.7): 40-60分
  - 信号正常 (< 0.3): 60-100分
- **配置参数**:
  - `signal_loss_threshold`: 信号丢失阈值 (默认: 0.3)
  - `signal_loss_severe`: 严重信号丢失阈值 (默认: 0.7)

**13. 过曝检测 (OVEREXPOSURE)**
- **功能**: 检测图像过曝
- **算法**: 检测高亮度像素比例
- **评分逻辑**:
  - 严重过曝 (≥ 0.3): 0-40分
  - 轻微过曝 (0.1-0.3): 40-60分
  - 曝光正常 (< 0.1): 60-100分
- **配置参数**:
  - `overexposure_threshold`: 过曝阈值 (默认: 0.1)
  - `overexposure_severe`: 严重过曝阈值 (默认: 0.3)

**14. 欠曝检测 (UNDEREXPOSURE)**
- **功能**: 检测图像欠曝
- **算法**: 检测低亮度像素比例
- **评分逻辑**:
  - 严重欠曝 (≥ 0.5): 0-40分
  - 轻微欠曝 (0.2-0.5): 40-60分
  - 曝光正常 (< 0.2): 60-100分
- **配置参数**:
  - `underexposure_threshold`: 欠曝阈值 (默认: 0.2)
  - `underexposure_severe`: 严重欠曝阈值 (默认: 0.5)

### 算法评分标准化

#### 统一评分标准
- **评分范围**: 0-100 分
- **评分原则**: 分数越高表示质量越好
- **状态分级**:
  - **NORMAL (正常)**: 60-100 分
  - **WARNING (警告)**: 40-59 分
  - **ERROR/CRITICAL (错误/严重)**: 0-39 分

#### 评分区间设计
- **0-40分**: 严重问题，需要立即处理
- **40-60分**: 轻微问题，建议关注
- **60-95分**: 正常范围，质量可接受
- **95-100分**: 优秀质量，表现卓越

### 算法包开发规范

#### 目录结构
```
algorithm_package/
├── __init__.py          # 包初始化文件
├── algorithm.py         # 主要算法实现
├── config.json         # 算法配置元数据
└── README.md           # 说明文档（可选）
```

#### 算法类规范
```python
class ExampleAlgorithm:
    def __init__(self, config=None):
        """初始化算法"""
        pass
    
    def run(self, data):
        """运行算法"""
        return {
            'prediction': '结果',
            'confidence': 0.95,
            'status': 'success'
        }
    
    def get_info(self):
        """获取算法信息"""
        return {
            'name': '算法名称',
            'version': '1.0.0',
            'description': '算法描述'
        }

# 工厂函数
def create_algorithm(config=None):
    return ExampleAlgorithm(config)
```

#### 配置文件规范 (config.json)
```json
{
  "name": "算法名称",
  "code": "algorithm_code",
  "version": "1.0.0",
  "description": "算法描述",
  "author": "作者",
  "type": "detection",
  "requirements": {
    "python": ">=3.8",
    "packages": ["numpy>=1.20.0"]
  },
  "parameters": {
    "threshold": {
      "type": "number",
      "default": 0.5,
      "description": "阈值参数"
    }
  },
  "entry_point": {
    "module": "algorithm",
    "class": "ExampleAlgorithm",
    "factory_function": "create_algorithm"
  }
}
```

### 动态加载功能

EasySight 分布式Worker系统支持动态加载算法包功能，Worker节点可以在启动时自动从主服务器获取算法包列表，下载并安装缺失的算法包，并动态导入算法模块，无需重启Worker节点。

#### 功能特性
- **自动同步**: Worker节点启动时自动从主服务器获取算法包列表
- **动态导入**: 运行时动态导入算法模块，无需重启Worker节点
- **缓存管理**: 本地缓存已下载的算法包，避免重复下载

#### 算法包缓存目录结构
```
algorithms_cache/
├── algorithm_code_1/
│   ├── 1.0.0/
│   │   ├── __init__.py
│   │   ├── algorithm.py
│   │   └── config.json
│   └── 1.1.0/
└── algorithm_code_2/
    └── 2.0.0/
```

### 阈值配置增强

#### 配置传递机制
系统支持从诊断模板到算法实例的阈值配置传递，确保前端模板中设置的阈值能正确传递到算法执行过程中。

#### 配置映射规则
| 诊断类型 | 前端字段 | 算法参数 | 转换规则 |
|---------|---------|---------|----------|
| clarity | threshold (0-1) | clarity_min | 乘以100 |
| brightness | threshold (0-1) | brightness_min | 直接使用 |
| contrast | threshold (0-1) | contrast_min | 直接使用 |
| noise | threshold (0-1) | noise_max | 直接使用 |

### 使用示例

#### 单个算法使用
```python
from diagnosis.algorithms import BrightnessAlgorithm
import cv2

# 加载图像
image = cv2.imread('test_image.jpg')

# 创建算法实例
algorithm = BrightnessAlgorithm({
    'thresholds': {
        'brightness_min': 30,
        'brightness_max': 220
    }
})

# 执行诊断
result = algorithm.diagnose(image)
print(f"评分: {result['score']}, 状态: {result['status']}")
```

#### 批量诊断
```python
from models.diagnosis import DiagnosisType
from diagnosis.algorithms import get_algorithm

# 定义要执行的诊断类型
diagnosis_types = [
    DiagnosisType.BRIGHTNESS,
    DiagnosisType.CLARITY,
    DiagnosisType.BLUE_SCREEN,
    DiagnosisType.NOISE,
    DiagnosisType.CONTRAST
]

# 批量执行诊断
results = {}
for diagnosis_type in diagnosis_types:
    algorithm = get_algorithm(diagnosis_type)
    result = algorithm.diagnose(image)
    results[diagnosis_type.value] = result
```

## 🔄 分布式Worker部署

### 系统架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   主服务器       │    │   Worker节点1    │    │   Worker节点2    │
│  (调度器)       │◄──►│  (任务执行)     │    │  (任务执行)     │
│                │    │                │    │                │
│ - 任务调度      │    │ - 注册/心跳     │    │ - 注册/心跳     │
│ - 任务分配      │    │ - 任务获取      │    │ - 任务获取      │
│ - Worker管理    │    │ - 任务执行      │    │ - 任务执行      │
│ - 状态监控      │    │ - 状态报告      │    │ - 状态报告      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 快速开始

#### 启动主服务
首先确保主服务正在运行：
```bash
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

#### 启动Worker节点

**方式一：直接启动（推荐）**
```bash
# 基本启动（连接到本地主服务）
python start_distributed_worker.py

# 连接到远程主服务
python start_distributed_worker.py --server-url http://192.168.1.100:8000

# 自定义配置
python start_distributed_worker.py \
  --worker-pool-size 5 \
  --max-concurrent-tasks 3 \
  --node-name ProductionWorker \
  --log-level INFO
```

**方式二：使用配置文件**
```bash
# 复制配置文件模板
cp worker.env.example worker.env

# 编辑配置文件
# worker.env
server_url=http://localhost:8000
worker_pool_size=3
max_concurrent_tasks=2
node_name=MyWorker
log_level=INFO

# 使用配置文件启动
python start_distributed_worker.py --config worker.env
```

### 配置参数

#### 基本配置
| 参数 | 默认值 | 说明 |
|------|--------|---------|
| `--config` | - | 配置文件路径 (.env格式) |
| `--server-url` | `http://localhost:8000` | 主服务器URL |
| `--api-token` | - | API认证令牌 |

#### Worker配置
| 参数 | 默认值 | 说明 |
|------|--------|---------|
| `--worker-pool-size` | `3` | Worker池大小 |
| `--max-concurrent-tasks` | `2` | 每个Worker最大并发任务数 |
| `--node-name` | `Worker-<hostname>` | 节点名称 |
| `--node-id` | 自动生成 | 节点ID |

#### 任务配置
| 参数 | 默认值 | 说明 |
|------|--------|---------|
| `--task-poll-interval` | `5` | 任务轮询间隔（秒） |
| `--heartbeat-interval` | `30` | 心跳间隔（秒） |
| `--max-retries` | `3` | 最大重试次数 |

#### 日志配置
| 参数 | 默认值 | 说明 |
|------|--------|---------|
| `--log-level` | `INFO` | 日志级别 (DEBUG/INFO/WARNING/ERROR) |
| `--log-file` | - | 日志文件路径 (默认仅控制台输出) |

### 功能特性

#### 自动注册和发现
- Worker节点启动时自动注册到主服务
- 定期发送心跳保持连接
- 主服务重启后自动重新注册

#### 智能任务分配
- 优先分配给可用的Worker节点
- 支持任务亲和性（分配给特定Worker）
- 负载均衡和容错处理

#### 实时监控
- Worker节点状态监控
- 任务执行统计
- 系统资源监控

### Worker重连机制

#### 问题背景
当主服务重启时，已连接的Worker节点会出现以下问题：
- 404错误持续出现
- 无法自动重连
- 连接状态不一致

#### 解决方案

**自动重新注册机制**
```python
# 心跳发送时检测404错误
elif response.status == 404:
    # 主服务重启导致节点未注册，自动重新注册
    logger.warning(f"节点未注册(404)，尝试重新注册: {self.config.node_id}")
    await self._register_node()
```

**改进注册逻辑**
- 添加重试机制和更好的错误处理
- 支持重复注册并保留统计信息
- 独立的连接监控循环

### 验证Worker状态

访问主服务的API来检查Worker状态：
```bash
# 获取Worker统计信息
curl http://localhost:8000/api/diagnosis/workers/stats

# 获取在线Worker列表
curl http://localhost:8000/api/diagnosis/workers
```

### 性能优化

#### 系统配置
- **心跳间隔**: 30秒
- **任务获取间隔**: 5秒
- **最大重试次数**: 3次
- **任务批量大小**: 最多5个任务

#### 资源监控
- CPU核心数自动检测
- 可用内存监控
- 网络连接状态检查

### Docker部署

#### 构建Worker镜像
```bash
# 构建Worker Docker镜像
docker build -f Dockerfile.worker -t easysight-worker .
```

#### 运行Worker容器
```bash
# 运行Worker容器
docker run -d \
  --name easysight-worker-1 \
  -e SERVER_URL=http://host.docker.internal:8000 \
  -e WORKER_POOL_SIZE=3 \
  -e MAX_CONCURRENT_TASKS=2 \
  easysight-worker
```

#### 使用Docker Compose
```yaml
# docker-compose.worker.yml
version: '3.8'
services:
  worker:
    build:
      context: .
      dockerfile: Dockerfile.worker
    environment:
      - SERVER_URL=http://backend:8000
      - WORKER_POOL_SIZE=3
      - MAX_CONCURRENT_TASKS=2
      - NODE_NAME=DockerWorker
    depends_on:
      - backend
    restart: unless-stopped
```

### 生产环境部署

#### 系统服务配置
```bash
# 复制服务文件
sudo cp scripts/easysight-worker.service /etc/systemd/system/

# 启用并启动服务
sudo systemctl enable easysight-worker
sudo systemctl start easysight-worker

# 查看服务状态
sudo systemctl status easysight-worker
```

#### 部署脚本
```bash
# 使用部署脚本
bash scripts/deploy_worker.sh
```

### 故障排除

#### 常见问题
1. **连接失败**: 检查网络连接和防火墙设置
2. **注册失败**: 验证服务器URL和API令牌
3. **任务执行失败**: 检查算法包和依赖
4. **性能问题**: 调整Worker池大小和并发数

#### 日志分析
```bash
# 查看Worker日志
tail -f worker.log

# 查看系统服务日志
sudo journalctl -u easysight-worker -f
```

## 📊 系统监控

### 性能指标
- **CPU使用率**: 系统CPU占用情况
- **内存使用率**: 系统内存占用情况
- **磁盘使用率**: 存储空间使用情况
- **网络流量**: 网络带宽使用情况
- **任务处理量**: AI任务处理统计
- **错误率**: 系统错误统计

### 日志管理
- **应用日志**: 应用运行日志
- **访问日志**: API访问日志
- **错误日志**: 系统错误日志
- **诊断日志**: AI诊断任务日志
- **Worker日志**: 分布式Worker运行日志

### 健康检查
```bash
# 检查主服务
curl http://localhost:8000/health

# 检查流媒体服务
curl http://localhost:18080/health

# 检查数据库连接
psql -h localhost -U rotanova -d easysight -c "SELECT 1;"

# 检查Redis连接
redis-cli ping
```

## 🔄 任务恢复指南

### 概述

EasySight 诊断任务恢复机制提供了强大的任务管理功能，允许用户在系统故障、网络中断或其他异常情况后恢复和重新执行诊断任务。

### API端点

#### 1. 恢复单个任务
```http
POST /api/diagnosis/tasks/{task_id}/recover
```

**请求参数：**
- `task_id` (路径参数): 要恢复的任务ID

**响应示例：**
```json
{
  "success": true,
  "message": "任务恢复成功",
  "task_id": "12345",
  "new_status": "pending"
}
```

#### 2. 批量恢复任务
```http
POST /api/diagnosis/tasks/recover/batch
```

**请求体：**
```json
{
  "task_ids": ["12345", "12346", "12347"],
  "force_recover": false
}
```

**响应示例：**
```json
{
  "success": true,
  "message": "批量恢复完成",
  "recovered_count": 2,
  "failed_count": 1,
  "details": [
    {
      "task_id": "12345",
      "status": "recovered",
      "message": "任务恢复成功"
    },
    {
      "task_id": "12346",
      "status": "recovered",
      "message": "任务恢复成功"
    },
    {
      "task_id": "12347",
      "status": "failed",
      "message": "任务已完成，无需恢复"
    }
  ]
}
```

#### 3. 按条件恢复任务
```http
POST /api/diagnosis/tasks/recover/by-criteria
```

**请求体：**
```json
{
  "status": ["failed", "timeout"],
  "camera_ids": [1, 2, 3],
  "start_time": "2024-01-01T00:00:00Z",
  "end_time": "2024-01-31T23:59:59Z",
  "algorithm_types": ["blue_screen", "black_screen"]
}
```

### 使用场景

#### 1. 系统故障后恢复
当系统因为硬件故障、软件崩溃或其他原因停机后，可以使用任务恢复功能重新执行未完成的任务：

```bash
# 恢复所有失败的任务
curl -X POST "http://localhost:8000/api/diagnosis/tasks/recover/by-criteria" \
  -H "Content-Type: application/json" \
  -d '{
    "status": ["failed", "timeout", "error"]
  }'
```

#### 2. 网络中断后恢复
当网络中断导致任务执行失败时，可以批量恢复相关任务：

```bash
# 恢复特定时间段内的失败任务
curl -X POST "http://localhost:8000/api/diagnosis/tasks/recover/by-criteria" \
  -H "Content-Type: application/json" \
  -d '{
    "status": ["failed"],
    "start_time": "2024-01-15T10:00:00Z",
    "end_time": "2024-01-15T12:00:00Z"
  }'
```

#### 3. 特定摄像头任务恢复
当某个摄像头出现问题后恢复正常，可以恢复该摄像头的相关任务：

```bash
# 恢复特定摄像头的失败任务
curl -X POST "http://localhost:8000/api/diagnosis/tasks/recover/by-criteria" \
  -H "Content-Type: application/json" \
  -d '{
    "camera_ids": [5],
    "status": ["failed", "timeout"]
  }'
```

#### 4. 算法更新后重新执行
当算法更新后，可能需要重新执行之前的任务以获得更准确的结果：

```bash
# 恢复特定算法类型的任务
curl -X POST "http://localhost:8000/api/diagnosis/tasks/recover/by-criteria" \
  -H "Content-Type: application/json" \
  -d '{
    "algorithm_types": ["blue_screen"],
    "start_time": "2024-01-01T00:00:00Z"
  }'
```

### 前端集成建议

#### 1. 任务列表页面
在任务列表页面添加恢复按钮：

```javascript
// 单个任务恢复
async function recoverTask(taskId) {
  try {
    const response = await fetch(`/api/diagnosis/tasks/${taskId}/recover`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      }
    });
    
    const result = await response.json();
    if (result.success) {
      showMessage('任务恢复成功', 'success');
      refreshTaskList();
    } else {
      showMessage(result.message, 'error');
    }
  } catch (error) {
    showMessage('恢复任务时发生错误', 'error');
  }
}

// 批量任务恢复
async function batchRecoverTasks(taskIds) {
  try {
    const response = await fetch('/api/diagnosis/tasks/recover/batch', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        task_ids: taskIds,
        force_recover: false
      })
    });
    
    const result = await response.json();
    showMessage(`成功恢复 ${result.recovered_count} 个任务`, 'success');
    refreshTaskList();
  } catch (error) {
    showMessage('批量恢复任务时发生错误', 'error');
  }
}
```

#### 2. 系统管理页面
在系统管理页面添加高级恢复功能：

```javascript
// 按条件恢复任务
async function recoverTasksByCriteria(criteria) {
  try {
    const response = await fetch('/api/diagnosis/tasks/recover/by-criteria', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify(criteria)
    });
    
    const result = await response.json();
    if (result.success) {
      showMessage(`成功恢复 ${result.recovered_count} 个任务`, 'success');
      if (result.failed_count > 0) {
        showMessage(`${result.failed_count} 个任务恢复失败`, 'warning');
      }
    }
  } catch (error) {
    showMessage('恢复任务时发生错误', 'error');
  }
}
```

#### 3. 用户界面建议

**任务状态指示器：**
- 使用不同颜色表示任务状态（成功、失败、进行中、待恢复）
- 为失败的任务显示恢复按钮
- 支持多选进行批量恢复

**恢复历史记录：**
- 记录任务恢复操作的历史
- 显示恢复时间、操作用户、恢复结果
- 提供恢复操作的审计日志

**智能恢复建议：**
- 分析失败任务的原因
- 提供恢复建议和最佳实践
- 自动识别可恢复的任务类型

### 最佳实践

#### 1. 恢复策略
- **渐进式恢复**: 先恢复少量任务测试系统稳定性
- **优先级恢复**: 优先恢复重要摄像头或关键时段的任务
- **分批恢复**: 避免一次性恢复大量任务造成系统负载过高

#### 2. 监控和告警
- 监控任务恢复的成功率
- 设置任务失败率告警阈值
- 记录恢复操作的详细日志

#### 3. 数据备份
- 在大规模恢复操作前备份数据库
- 保留原始任务数据以便回滚
- 定期清理过期的任务恢复记录

## 🛠️ 故障排除

### 常见问题

#### 1. 数据库连接问题
```bash
# 检查PostgreSQL服务状态
docker ps | grep postgres

# 查看数据库日志
docker logs postgres

# 测试数据库连接
psql -h localhost -U rotanova -d easysight
```

#### 2. Redis连接问题
```bash
# 检查Redis服务状态
docker ps | grep redis

# 测试Redis连接
redis-cli ping
```

#### 3. MinIO连接问题
```bash
# 检查MinIO服务状态
docker ps | grep minio

# 访问MinIO控制台
http://localhost:9001
```

#### 4. Worker节点连接问题
```bash
# 检查网络连接
ping your-server-host
telnet your-server-host 8000

# 检查认证信息
curl -X POST http://your-server-host:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

## 🎥 流媒体服务端口配置

### 端口架构概览

EasySight 流媒体服务基于 ZLMediaKit 构建，提供完整的视频流处理和分发能力。以下是详细的端口配置说明：

```
┌─────────────────────────────────────────────────────────────┐
│                    EasySight 端口架构                        │
├─────────────────────────────────────────────────────────────┤
│  主要服务端口                                                │
│  ├─ EasySight 主服务: 8000 (HTTP API)                      │
│  ├─ ZLMediaKit HTTP API: 8060                              │
│  ├─ ZLMediaKit 管理界面: 18080                              │
│  └─ 前端应用: 3000 (开发模式)                               │
├─────────────────────────────────────────────────────────────┤
│  流媒体协议端口                                              │
│  ├─ RTSP: 554                                              │
│  ├─ RTMP: 1935                                             │
│  ├─ HTTP-FLV: 8060                                         │
│  ├─ WebRTC: 8000 (UDP)                                     │
│  ├─ HLS: 8060                                              │
│  └─ TS over WebSocket: 8060                                │
├─────────────────────────────────────────────────────────────┤
│  数据库和缓存端口                                            │
│  ├─ PostgreSQL: 5432                                       │
│  ├─ Redis: 6379                                            │
│  ├─ MinIO API: 9000                                        │
│  ├─ MinIO Console: 9001                                    │
│  └─ RabbitMQ: 5672, 15672                                  │
└─────────────────────────────────────────────────────────────┘
```

### 服务架构

#### 1. EasySight 主服务 (端口 8000)
- **功能**: 提供 REST API 接口
- **协议**: HTTP/HTTPS
- **用途**: 
  - 用户认证和授权
  - 摄像头管理
  - AI 诊断任务调度
  - 系统配置管理
  - WebSocket 实时通信

#### 2. ZLMediaKit 流媒体服务

**HTTP API 端口 (8060)**
- **功能**: 流媒体控制和管理 API
- **协议**: HTTP
- **用途**:
  - 流状态查询
  - 推流/拉流控制
  - 录制管理
  - 统计信息获取

**管理界面端口 (18080)**
- **功能**: Web 管理界面
- **协议**: HTTP
- **用途**:
  - 流媒体服务监控
  - 配置管理
  - 实时统计查看

### 视频流处理流程

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   摄像头     │───►│ ZLMediaKit  │───►│ EasySight   │───►│   前端      │
│  (RTSP源)   │    │ 流媒体服务   │    │  主服务     │    │  播放器     │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
      │                    │                    │                    │
      │                    │                    │                    │
   RTSP://           HTTP-FLV/HLS         WebSocket           HTTP-FLV/
 camera-ip:554       :8060/live          :8000/ws            HLS/WebRTC
```

#### 流程说明：
1. **摄像头推流**: 摄像头通过 RTSP 协议推送视频流到 ZLMediaKit
2. **协议转换**: ZLMediaKit 将 RTSP 流转换为多种格式（HTTP-FLV、HLS、WebRTC）
3. **流管理**: EasySight 主服务通过 HTTP API 管理流状态
4. **前端播放**: 前端通过多种协议播放视频流

### 环境变量配置

#### ZLMediaKit 配置 (zlmediakitServer/.env)
```env
# HTTP API 端口
HTTP_PORT=8060

# RTSP 端口
RTSP_PORT=554

# RTMP 端口
RTMP_PORT=1935

# 管理界面端口
WEB_PORT=18080

# WebRTC 端口
WEBRTC_PORT=8000

# 日志级别
LOG_LEVEL=INFO

# 录制配置
RECORD_ENABLE=true
RECORD_PATH=/data/record

# HLS 配置
HLS_ENABLE=true
HLS_SEGMENT_DURATION=5
HLS_SEGMENT_NUM=3
```

#### EasySight 主服务配置 (backend/.env)
```env
# ZLMediaKit 连接配置
ZLMEDIAKIT_HOST=127.0.0.1
ZLMEDIAKIT_HTTP_PORT=8060
ZLMEDIAKIT_SECRET=035c73f7-bb6b-4889-a715-d9eb2d1925cc

# 流媒体配置
STREAM_TIMEOUT=30
STREAM_RETRY_COUNT=3
STREAM_BUFFER_SIZE=1024
```

### 防火墙配置建议

#### Linux (iptables)
```bash
# 允许 EasySight 主服务
sudo iptables -A INPUT -p tcp --dport 8000 -j ACCEPT

# 允许 ZLMediaKit HTTP API
sudo iptables -A INPUT -p tcp --dport 8060 -j ACCEPT

# 允许 ZLMediaKit 管理界面
sudo iptables -A INPUT -p tcp --dport 18080 -j ACCEPT

# 允许 RTSP
sudo iptables -A INPUT -p tcp --dport 554 -j ACCEPT

# 允许 RTMP
sudo iptables -A INPUT -p tcp --dport 1935 -j ACCEPT

# 允许 WebRTC (UDP)
sudo iptables -A INPUT -p udp --dport 8000 -j ACCEPT

# 保存规则
sudo iptables-save > /etc/iptables/rules.v4
```

#### Windows 防火墙
```powershell
# 允许 EasySight 主服务
New-NetFirewallRule -DisplayName "EasySight Main" -Direction Inbound -Protocol TCP -LocalPort 8000 -Action Allow

# 允许 ZLMediaKit HTTP API
New-NetFirewallRule -DisplayName "ZLMediaKit HTTP" -Direction Inbound -Protocol TCP -LocalPort 8060 -Action Allow

# 允许 ZLMediaKit 管理界面
New-NetFirewallRule -DisplayName "ZLMediaKit Web" -Direction Inbound -Protocol TCP -LocalPort 18080 -Action Allow

# 允许 RTSP
New-NetFirewallRule -DisplayName "RTSP" -Direction Inbound -Protocol TCP -LocalPort 554 -Action Allow

# 允许 RTMP
New-NetFirewallRule -DisplayName "RTMP" -Direction Inbound -Protocol TCP -LocalPort 1935 -Action Allow

# 允许 WebRTC
New-NetFirewallRule -DisplayName "WebRTC" -Direction Inbound -Protocol UDP -LocalPort 8000 -Action Allow
```

### 健康检查

#### 服务状态检查
```bash
# 检查 EasySight 主服务
curl -f http://localhost:8000/health || echo "EasySight 主服务异常"

# 检查 ZLMediaKit HTTP API
curl -f http://localhost:8060/index/api/getServerConfig || echo "ZLMediaKit API 异常"

# 检查 ZLMediaKit 管理界面
curl -f http://localhost:18080 || echo "ZLMediaKit 管理界面异常"

# 检查端口监听状态
netstat -tlnp | grep -E ':(8000|8060|18080|554|1935)'
```

#### 流状态检查
```bash
# 获取所有流信息
curl "http://localhost:8060/index/api/getMediaList"

# 获取特定流信息
curl "http://localhost:8060/index/api/getMediaInfo?schema=rtsp&vhost=__defaultVhost__&app=live&stream=camera001"

# 检查流播放统计
curl "http://localhost:8060/index/api/getStatistic"
```

### 故障排查

#### 1. 端口冲突问题
```bash
# 检查端口占用
netstat -tlnp | grep :8000
lsof -i :8000

# 查找占用进程
ps aux | grep $(lsof -t -i:8000)

# 终止占用进程
kill -9 $(lsof -t -i:8000)
```

#### 2. 流媒体服务异常
```bash
# 查看 ZLMediaKit 日志
tail -f /var/log/zlmediakit/zlmediakit.log

# 重启 ZLMediaKit 服务
sudo systemctl restart zlmediakit

# 检查配置文件
cat /etc/zlmediakit/config.ini
```

#### 3. 网络连接问题
```bash
# 测试端口连通性
telnet localhost 8060
nc -zv localhost 8060

# 检查防火墙状态
sudo ufw status
sudo iptables -L

# 检查网络接口
ip addr show
ifconfig
```

#### 4. 性能问题
```bash
# 监控系统资源
top -p $(pgrep zlmediakit)
htop

# 检查网络流量
iftop
netstat -i

# 监控磁盘 I/O
iostat -x 1
```

### 性能优化建议

#### 1. 系统级优化
```bash
# 增加文件描述符限制
echo "* soft nofile 65536" >> /etc/security/limits.conf
echo "* hard nofile 65536" >> /etc/security/limits.conf

# 优化网络参数
echo "net.core.rmem_max = 134217728" >> /etc/sysctl.conf
echo "net.core.wmem_max = 134217728" >> /etc/sysctl.conf
echo "net.ipv4.tcp_rmem = 4096 65536 134217728" >> /etc/sysctl.conf
echo "net.ipv4.tcp_wmem = 4096 65536 134217728" >> /etc/sysctl.conf
sysctl -p
```

#### 2. ZLMediaKit 优化
```ini
# config.ini 优化配置
[general]
# 增加线程数
threadNum=0  # 0表示自动检测CPU核心数

# 优化缓存
[protocol]
# 增加缓存时间
cacheMS=1000

# 优化 HLS
[hls]
# 减少分片时间提高实时性
segDur=2
# 减少分片数量
segNum=3
```

### 监控和告警

#### 1. 服务监控脚本
```bash
#!/bin/bash
# monitor_services.sh

check_service() {
    local service_name=$1
    local port=$2
    local url=$3
    
    if curl -f -s "$url" > /dev/null; then
        echo "[OK] $service_name (端口 $port) 运行正常"
    else
        echo "[ERROR] $service_name (端口 $port) 异常" >&2
        # 发送告警通知
        # send_alert "$service_name 服务异常"
    fi
}

# 检查各个服务
check_service "EasySight 主服务" 8000 "http://localhost:8000/health"
check_service "ZLMediaKit API" 8060 "http://localhost:8060/index/api/getServerConfig"
check_service "ZLMediaKit 管理界面" 18080 "http://localhost:18080"
```

#### 2. 流状态监控
```bash
#!/bin/bash
# monitor_streams.sh

# 获取流统计信息
stream_count=$(curl -s "http://localhost:8060/index/api/getMediaList" | jq '.data | length')
player_count=$(curl -s "http://localhost:8060/index/api/getStatistic" | jq '.data.PlayerCount')

echo "当前流数量: $stream_count"
echo "当前播放器数量: $player_count"

# 检查异常流
if [ "$stream_count" -eq 0 ]; then
    echo "[WARNING] 没有活跃的视频流" >&2
fi

if [ "$player_count" -gt 100 ]; then
    echo "[WARNING] 播放器数量过多，可能影响性能" >&2
fi
```

### 性能优化

#### 1. 数据库优化
- 定期执行VACUUM和ANALYZE
- 合理设置连接池大小
- 添加必要的索引
- 定期清理过期数据

#### 2. 缓存优化
- 合理设置Redis过期时间
- 使用Redis集群提高性能
- 监控缓存命中率

#### 3. 算法优化
- 合理设置Worker并发数
- 优化算法处理时间
- 使用GPU加速计算
- 实施算法结果缓存

## 🔐 安全配置

### 生产环境安全建议

1. **修改默认密码**
   - 数据库密码
   - MinIO访问密钥
   - 管理员账户密码
   - JWT密钥

2. **网络安全**
   - 配置防火墙规则
   - 使用HTTPS协议
   - 限制API访问来源
   - 配置VPN访问

3. **数据安全**
   - 定期备份数据
   - 加密敏感数据
   - 配置访问日志
   - 实施数据保留策略

4. **应用安全**
   - 定期更新依赖包
   - 配置CORS策略
   - 实施API限流
   - 监控异常访问

## 📈 扩展开发

### 添加新的诊断算法

1. **创建算法类**
```python
from diagnosis.algorithms import BaseAlgorithm

class CustomAlgorithm(BaseAlgorithm):
    def __init__(self, config):
        super().__init__(config)
        # 初始化算法
    
    def process(self, image_data):
        # 实现算法逻辑
        return {
            'score': 85,
            'status': 'NORMAL',
            'details': {}
        }
```

2. **注册算法**
```python
# 在diagnosis/algorithms.py中注册
ALGORITHM_REGISTRY['CUSTOM'] = CustomAlgorithm
```

3. **添加数据库枚举**
```python
# 在models/diagnosis.py中添加
class DiagnosisType(str, Enum):
    # ... 现有类型
    CUSTOM = "custom"
```

### 添加新的API接口

1. **创建路由文件**
```python
# routers/custom.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db

router = APIRouter()

@router.get("/custom-endpoint")
async def custom_endpoint(db: Session = Depends(get_db)):
    return {"message": "Custom endpoint"}
```

2. **注册路由**
```python
# main.py
from routers import custom
app.include_router(custom.router, prefix="/api/v1/custom", tags=["自定义"])
```

### 添加新的前端页面

1. **创建页面组件**
```vue
<!-- src/views/custom/CustomPage.vue -->
<template>
  <div class="custom-page">
    <h1>自定义页面</h1>
  </div>
</template>

<script setup lang="ts">
// 页面逻辑
</script>
```

2. **添加路由**
```typescript
// src/router/index.ts
{
  path: '/custom',
  name: 'Custom',
  component: () => import('@/views/custom/CustomPage.vue')
}
```

## 📝 更新日志

### v1.0.0 (2024-01-01)
- 初始版本发布
- 完整的智能安防平台功能
- 支持14种诊断算法
- 分布式Worker架构
- 现代化Web界面

### 主要更新记录
- **算法评分标准化**: 统一0-100分制评分系统
- **蓝屏检测优化**: 改进评分逻辑和状态判断
- **Worker重连机制**: 修复主服务重启后的连接问题
- **动态算法加载**: 支持运行时动态加载算法包
- **任务恢复机制**: 自动检测和恢复卡住的诊断任务
- **阈值配置增强**: 支持从模板传递自定义阈值参数
- **日志系统优化**: 改进日志记录和时区处理

## 🤝 贡献指南

### 开发流程
1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

### 代码规范
- **Python**: 遵循PEP 8规范
- **TypeScript**: 使用ESLint和Prettier
- **Vue**: 遵循Vue 3 Composition API规范
- **提交信息**: 使用语义化提交信息

### 测试要求
- 单元测试覆盖率 > 80%
- 集成测试通过
- 性能测试达标
- 安全测试通过

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 📞 联系我们

如有问题或建议，请通过以下方式联系我们：

- 提交 Issue
- 发送邮件
- 加入讨论群

---

⭐ 如果这个项目对你有帮助，请给我们一个星标！

**EasySight Team**  
*让智能安防更简单*