# EasySight 智能安防平台 - RabbitMQ版本

## 概述

这是EasySight智能安防平台的RabbitMQ增强版本，采用事件驱动架构，提供实时任务分发、高可用性和更好的稳定性。

## 🌟 新功能特性

### 🚀 核心改进
- **RabbitMQ任务队列**: 替换原有的HTTP轮询机制
- **实时任务分发**: 任务创建后立即分发给可用Worker
- **事件驱动架构**: 基于消息队列的异步处理
- **高可用性**: 支持Worker故障自动恢复
- **负载均衡**: 智能任务分配和Worker负载管理

### 📊 性能提升
- **延迟降低**: 从平均30-35秒降低到秒级响应
- **吞吐量提升**: 支持更高的并发任务处理
- **资源优化**: 减少无效的轮询请求
- **扩展性**: 支持动态添加Worker节点

## 🏗️ 架构组件

### 核心组件
1. **TaskQueueManager**: RabbitMQ连接和队列管理
2. **RabbitMQTaskScheduler**: 基于RabbitMQ的任务调度器
3. **RabbitMQDistributedWorker**: 基于RabbitMQ的分布式Worker
4. **RabbitMQEventTaskManager**: 基于RabbitMQ的事件任务管理器

### 消息队列
- `diagnosis_tasks`: 诊断任务队列
- `event_tasks`: 事件任务队列
- `ai_service_tasks`: AI服务任务队列
- `task_results`: 任务结果队列
- `worker_heartbeats`: Worker心跳队列

## 🚀 快速开始

### 前置条件

1. **RabbitMQ服务**
   ```bash
   # 确保RabbitMQ正在运行
   rabbitmq-server
   ```

2. **Python依赖**
   ```bash
   pip install aio-pika
   ```

### 启动服务

#### 1. 启动主服务
```bash
# 方式1: 使用启动脚本（推荐）
python start_rabbitmq.py

# 方式2: 直接启动
python -m uvicorn main_rabbitmq:app --host 0.0.0.0 --port 8000 --reload
```

#### 2. 启动Worker节点
```bash
# 启动默认Worker
python start_rabbitmq_worker.py

# 启动指定ID的Worker
python start_rabbitmq_worker.py worker-001

# 启动多个Worker（在不同终端）
python start_rabbitmq_worker.py worker-002
python start_rabbitmq_worker.py worker-003
```

## 📡 API接口

### 主要接口
- **主页**: http://localhost:8000
- **API文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/health
- **RabbitMQ状态**: http://localhost:8000/api/v1/rabbitmq/status
- **队列状态**: http://localhost:8000/api/v1/diagnosis/queue/status

### 新增接口
```http
GET /api/v1/rabbitmq/status
# 获取RabbitMQ连接状态和队列统计

GET /api/v1/diagnosis/queue/status
# 获取诊断任务队列状态

POST /api/v1/diagnosis/tasks/{task_id}/submit
# 立即将任务提交到RabbitMQ队列
```

## 🔧 配置说明

### RabbitMQ配置
```python
# config.py
RABBITMQ_URL = "amqp://rotanova:RotaNova@2025@127.0.0.1:5672/"
```

### Worker配置
```python
# 默认配置
max_concurrent_tasks = 3  # 最大并发任务数
heartbeat_interval = 30   # 心跳间隔（秒）
task_timeout = 300        # 任务超时时间（秒）
```

## 🔄 工作流程

### 任务分发流程
1. **任务创建**: 用户通过API创建诊断任务
2. **立即分发**: 任务立即发布到RabbitMQ队列
3. **Worker接收**: 可用Worker实时接收任务
4. **任务执行**: Worker执行任务并更新状态
5. **结果返回**: 执行结果通过队列返回

### 心跳监控
1. **定期心跳**: Worker每30秒发送心跳
2. **状态更新**: 更新Worker状态和当前任务数
3. **故障检测**: 超时Worker自动标记为离线
4. **任务恢复**: 离线Worker的任务重新分配

## 🛠️ 故障排除

### 常见问题

#### 1. RabbitMQ连接失败
```bash
# 检查RabbitMQ服务状态
rabbitmqctl status

# 检查端口占用
netstat -an | findstr :5672

# 重启RabbitMQ服务
rabbitmq-server restart
```

#### 2. Worker无法连接
```bash
# 检查主服务是否运行
curl http://localhost:8000/health

# 检查Worker注册
curl http://localhost:8000/api/v1/diagnosis/workers
```

#### 3. 任务不执行
```bash
# 检查队列状态
curl http://localhost:8000/api/v1/diagnosis/queue/status

# 检查RabbitMQ管理界面
# http://localhost:15672 (如果启用了管理插件)
```

### 日志查看
```bash
# 主服务日志
tail -f logs/main_service.log

# Worker日志
tail -f logs/worker.log

# RabbitMQ日志
tail -f /var/log/rabbitmq/rabbit@hostname.log
```

## 📊 监控和管理

### 队列监控
```python
# 获取队列统计信息
import aiohttp

async def get_queue_stats():
    async with aiohttp.ClientSession() as session:
        async with session.get('http://localhost:8000/api/v1/diagnosis/queue/status') as resp:
            return await resp.json()
```

### Worker管理
```python
# 获取Worker列表
async def get_workers():
    async with aiohttp.ClientSession() as session:
        async with session.get('http://localhost:8000/api/v1/diagnosis/workers') as resp:
            return await resp.json()
```

## 🔄 从原版本迁移

### 迁移步骤
1. **备份数据**: 备份现有数据库
2. **安装依赖**: 安装RabbitMQ和aio-pika
3. **配置RabbitMQ**: 设置连接参数
4. **启动新版本**: 使用RabbitMQ版本启动
5. **验证功能**: 测试任务分发和执行

### 兼容性
- **数据库**: 完全兼容现有数据库结构
- **API**: 保持向后兼容，新增RabbitMQ相关接口
- **Worker**: 支持新旧Worker混合部署（过渡期）

## 🎯 性能优化建议

### 生产环境配置
1. **RabbitMQ集群**: 部署RabbitMQ集群提高可用性
2. **Worker扩展**: 根据负载动态调整Worker数量
3. **监控告警**: 设置队列长度和Worker状态监控
4. **资源限制**: 合理配置Worker并发数和内存限制

### 调优参数
```python
# 高负载环境建议配置
max_concurrent_tasks = 5      # 增加并发数
heartbeat_interval = 15       # 缩短心跳间隔
queue_prefetch_count = 10     # 队列预取数量
connection_pool_size = 20     # 连接池大小
```

## 📞 技术支持

如有问题或建议，请联系开发团队或提交Issue。

---

**EasySight智能安防平台 - 让安防更智能，让监控更高效！** 🚀