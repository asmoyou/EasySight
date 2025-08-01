# EasySight 分布式Worker系统使用指南

## 概述

EasySight 分布式Worker系统允许您在多个节点上运行诊断任务，实现负载分布和横向扩展。系统会优先将任务分配给可用的Worker节点，只有在没有Worker节点时才在主服务中执行任务。

## 系统架构

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

## 快速开始

### 1. 启动主服务

首先确保主服务正在运行：

```bash
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. 启动Worker节点

#### 方式一：直接启动（推荐）

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

#### 方式二：使用配置文件

1. 复制配置文件模板：
```bash
cp worker.env.example worker.env
```

2. 编辑配置文件：
```bash
# worker.env
server_url=http://localhost:8000
worker_pool_size=3
max_concurrent_tasks=2
node_name=MyWorker
log_level=INFO
```

3. 使用配置文件启动：
```bash
python start_distributed_worker.py --config worker.env
```

#### 方式三：直接运行Worker模块

```bash
python distributed_worker.py --server-url http://localhost:8000 --max-concurrent-tasks 2
```

### 3. 验证Worker状态

访问主服务的API来检查Worker状态：

```bash
# 获取Worker统计信息
curl http://localhost:8000/api/diagnosis/workers/stats

# 获取在线Worker列表
curl http://localhost:8000/api/diagnosis/workers
```

## 配置参数

### 启动脚本参数

#### 基本配置

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--config` | - | 配置文件路径 (.env格式) |
| `--server-url` | `http://localhost:8000` | 主服务器URL |
| `--api-token` | - | API认证令牌 |

#### Worker配置

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--worker-pool-size` | `3` | Worker池大小 |
| `--max-concurrent-tasks` | `2` | 每个Worker最大并发任务数 |
| `--node-name` | `Worker-<hostname>` | 节点名称 |
| `--node-id` | 自动生成 | 节点ID |

#### 任务配置

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--task-poll-interval` | `5` | 任务轮询间隔（秒） |
| `--heartbeat-interval` | `30` | 心跳间隔（秒） |
| `--max-retries` | `3` | 最大重试次数 |

#### 日志配置

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--log-level` | `INFO` | 日志级别 (DEBUG/INFO/WARNING/ERROR) |
| `--log-file` | - | 日志文件路径 (默认仅控制台输出) |

#### 性能配置

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--enable-metrics` | `false` | 启用性能指标收集 |
| `--metrics-port` | `9090` | 指标服务端口 |

### 配置文件格式

配置文件使用简单的 `.env` 格式：

```bash
# 服务器连接配置
server_url=http://localhost:8000
api_token=your_api_token_here

# Worker配置
worker_pool_size=3
max_concurrent_tasks=2
node_name=Worker-Production
node_id=worker-001

# 任务配置
task_poll_interval=5
heartbeat_interval=30
max_retries=3

# 日志配置
log_level=INFO
log_file=worker.log

# 性能配置
enable_metrics=false
metrics_port=9090
```

**注意事项：**
- 命令行参数会覆盖配置文件中的设置
- 布尔值使用 `true`/`false` 或 `1`/`0`
- 数值类型会自动转换
- 以 `#` 开头的行为注释

### 系统配置

系统会自动检测以下配置：
- CPU核心数（用于确定默认Worker池大小）
- 可用内存（用于任务调度优化）
- 网络连接状态（用于主节点通信）

默认系统配置：
- **心跳间隔**: 30秒
- **任务获取间隔**: 5秒
- **最大重试次数**: 3次
- **任务批量大小**: 最多5个任务

## 功能特性

### 1. 自动注册和发现

- Worker节点启动时自动注册到主服务
- 定期发送心跳保持连接
- 主服务重启后自动重新注册

### 2. 智能任务分配

- 优先分配给可用的Worker节点
- 支持任务亲和性（分配给特定Worker）
- 负载均衡和容错处理

### 3. 实时监控

- Worker节点状态监控
- 任务执行统计
- 系统资源监控

### 4. 容错机制

- Worker节点断线重连
- 任务执行失败重试
- 优雅关闭和清理

## API接口

### Worker管理

```bash
# 获取Worker统计信息
GET /api/diagnosis/workers/stats

# 获取Worker列表
GET /api/diagnosis/workers

# 获取特定Worker的任务
GET /api/diagnosis/workers/{worker_id}/tasks
```

### Worker注册（内部API）

```bash
# Worker注册
POST /api/diagnosis/workers/register

# Worker心跳
POST /api/diagnosis/workers/{worker_id}/heartbeat

# Worker注销
DELETE /api/diagnosis/workers/{worker_id}

# 获取任务
GET /api/diagnosis/workers/{worker_id}/tasks

# 完成任务
POST /api/diagnosis/tasks/{task_id}/complete
```

## 部署建议

### 1. 生产环境部署

```bash
# 使用systemd服务
sudo cp scripts/easysight-worker.service /etc/systemd/system/
sudo systemctl enable easysight-worker
sudo systemctl start easysight-worker
```

### 2. Docker部署

```bash
# 构建Worker镜像
docker build -f Dockerfile.worker -t easysight-worker .

# 运行Worker容器
docker run -d --name worker1 \
  -e SERVER_URL=http://主服务IP:8000 \
  -e MAX_CONCURRENT_TASKS=4 \
  -e NODE_NAME=DockerWorker1 \
  easysight-worker
```

### 3. 多节点部署

```bash
# 节点1
python start_distributed_worker.py --server-url http://主服务IP:8000 --node-name Node1 --max-concurrent-tasks 4

# 节点2
python start_distributed_worker.py --server-url http://主服务IP:8000 --node-name Node2 --max-concurrent-tasks 2

# 节点3
python start_distributed_worker.py --server-url http://主服务IP:8000 --node-name Node3 --max-concurrent-tasks 6
```

## 监控和调试

### 1. 日志文件

- Worker日志: `worker.log`
- 主服务日志: 控制台输出

### 2. 状态检查

```bash
# 检查Worker状态
curl http://localhost:8000/api/diagnosis/workers/stats

# 检查任务队列
curl http://localhost:8000/api/diagnosis/tasks?status=pending

# 检查运行中的任务
curl http://localhost:8000/api/diagnosis/tasks?status=running
```

### 3. 性能监控

- CPU使用率
- 内存使用率
- 任务执行时间
- 任务成功/失败率

## 故障排除

### 1. Worker无法连接到主服务

- 检查网络连接
- 确认主服务URL正确
- 检查防火墙设置

### 2. Worker注册失败

- 检查主服务是否运行
- 查看Worker日志
- 确认API端点可访问

### 3. 任务执行失败

- 检查诊断算法配置
- 查看任务执行日志
- 确认数据库连接正常

### 4. Worker频繁断线

- 检查网络稳定性
- 调整心跳间隔
- 查看系统资源使用情况

## 最佳实践

### 1. 生产环境部署

#### 使用配置文件（推荐）

创建生产环境配置文件 `production.env`：

```bash
# production.env
server_url=http://your-production-server:8000
api_token=your_secure_api_token
worker_pool_size=5
max_concurrent_tasks=3
node_name=Production-Worker
task_poll_interval=3
heartbeat_interval=30
max_retries=5
log_level=INFO
log_file=/var/log/easysight/worker.log
enable_metrics=true
metrics_port=9090
```

启动命令：
```bash
python start_distributed_worker.py --config production.env
```

#### 使用命令行参数

```bash
# 推荐的生产环境配置
python start_distributed_worker.py \
  --server-url http://your-production-server:8000 \
  --worker-pool-size 5 \
  --max-concurrent-tasks 3 \
  --node-name "Production-Worker-$(hostname)" \
  --log-level INFO \
  --log-file /var/log/easysight/worker.log \
  --enable-metrics
```

### 2. 开发环境配置

创建开发环境配置文件 `development.env`：

```bash
# development.env
server_url=http://localhost:8000
worker_pool_size=2
max_concurrent_tasks=1
node_name=Dev-Worker
log_level=DEBUG
task_poll_interval=5
heartbeat_interval=30
```

启动命令：
```bash
python start_distributed_worker.py --config development.env
```

### 3. 资源优化

#### CPU和内存配置

- **CPU密集型任务**: 设置 `worker_pool_size = CPU核心数`
- **IO密集型任务**: 设置 `worker_pool_size = CPU核心数 * 2`
- **内存限制**: 根据可用内存调整 `max_concurrent_tasks`
- **混合负载**: 从较小值开始，逐步调优

#### 网络优化

- **本地网络**: `task_poll_interval=3`, `heartbeat_interval=20`
- **远程网络**: `task_poll_interval=5`, `heartbeat_interval=30`
- **不稳定网络**: `max_retries=5`, `heartbeat_interval=45`

### 4. 监控和日志

#### 日志配置

```bash
# 详细日志配置
log_level=INFO
log_file=/var/log/easysight/worker-$(date +%Y%m%d).log
```

#### 性能监控

```bash
# 启用指标收集
enable_metrics=true
metrics_port=9090
```

#### 监控建议

- 监控Worker节点的CPU和内存使用率
- 定期检查任务执行日志
- 设置告警机制监控节点连接状态
- 使用指标端点监控任务处理性能

### 5. 部署策略

#### 单机多Worker

```bash
# 启动多个Worker实例
python start_distributed_worker.py --config worker1.env --node-name Worker-1 &
python start_distributed_worker.py --config worker2.env --node-name Worker-2 &
python start_distributed_worker.py --config worker3.env --node-name Worker-3 &
```

#### 容器化部署

```dockerfile
# Dockerfile
FROM python:3.9-slim
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
CMD ["python", "start_distributed_worker.py", "--config", "production.env"]
```

#### 系统服务

```bash
# 创建 systemd 服务
sudo cp scripts/easysight-worker.service /etc/systemd/system/
sudo systemctl enable easysight-worker
sudo systemctl start easysight-worker
```

### 6. 通用建议

1. **合理配置并发数**: 根据机器性能设置`max-concurrent-tasks`
2. **监控资源使用**: 定期检查CPU、内存使用情况
3. **日志管理**: 定期清理和归档日志文件
4. **网络优化**: 确保Worker和主服务之间网络稳定
5. **容错设计**: 部署多个Worker节点以提高可用性
6. **配置管理**: 使用配置文件而非命令行参数进行生产部署
7. **优雅关闭**: 使用 Ctrl+C 或发送 SIGTERM 信号优雅关闭Worker
8. **资源监控**: 启用指标收集以便性能分析和故障排除

## 故障排除

### 常见问题

#### 1. 连接问题

**问题**: Worker无法连接到主节点

**解决方案**:
```bash
# 检查网络连接
ping your-server-host

# 检查端口是否开放
telnet your-server-host 8000

# 检查防火墙设置
# Windows: 检查Windows防火墙
# Linux: 检查iptables或ufw
```

#### 2. 认证问题

**问题**: API认证失败

**解决方案**:
```bash
# 检查API令牌是否正确
curl -H "Authorization: Bearer your_token" http://your-server:8000/api/health

# 更新配置文件中的令牌
api_token=your_correct_token
```

#### 3. 性能问题

**问题**: Worker处理任务缓慢

**解决方案**:
```bash
# 调整并发配置
worker_pool_size=4  # 增加Worker池大小
max_concurrent_tasks=2  # 减少并发任务数

# 优化轮询间隔
task_poll_interval=3  # 减少轮询间隔
```

#### 4. 内存问题

**问题**: Worker内存使用过高

**解决方案**:
```bash
# 减少并发任务数
max_concurrent_tasks=1

# 增加任务处理间隔
task_poll_interval=10

# 启用详细日志查看内存使用
log_level=DEBUG
```

### 日志分析

#### 关键日志信息

```bash
# 启动成功
[INFO] Worker节点启动成功: Worker-001
[INFO] 连接到主节点: http://localhost:8000
[INFO] Worker池大小: 3, 最大并发任务: 2

# 任务处理
[INFO] 接收到新任务: task_12345
[INFO] 任务处理完成: task_12345, 耗时: 45.2秒

# 错误信息
[ERROR] 连接主节点失败: Connection refused
[ERROR] 任务处理失败: task_12345, 错误: TimeoutError
[WARNING] 心跳超时，尝试重连...
```

#### 日志级别说明

- **DEBUG**: 详细的调试信息，包括所有操作细节
- **INFO**: 一般信息，包括启动、任务处理等
- **WARNING**: 警告信息，如连接问题、重试等
- **ERROR**: 错误信息，需要关注和处理
- **CRITICAL**: 严重错误，可能导致Worker停止

### 性能调优

#### 基准测试

```bash
# 测试不同配置的性能
python start_distributed_worker.py --config test1.env  # 配置1
python start_distributed_worker.py --config test2.env  # 配置2

# 比较处理速度和资源使用
```

#### 监控指标

启用指标收集后，可以通过以下端点查看性能数据：

```bash
# 查看Worker指标
curl http://localhost:9090/metrics

# 关键指标包括：
# - 任务处理速度
# - 内存使用情况
# - CPU使用率
# - 网络连接状态
```

## 版本兼容性

- **EasySight 主服务**: v1.0+
- **Python**: 3.8+
- **依赖库**: 见 `requirements.txt`

## 更新日志

### v1.1.0 (当前版本)
- 重构启动脚本 `start_distributed_worker.py`
- 新增配置文件支持（`.env` 格式）
- 增强命令行参数处理
- 添加优雅关闭机制
- 改进错误处理和日志记录
- 新增性能监控指标支持
- 完善文档和使用指南

### v1.0.0
- 初始版本发布
- 支持基本的分布式任务执行
- 自动注册和心跳机制
- 任务分配和状态报告

## 总结

**EasySight 分布式 Worker 系统** 现在提供了更加完善和易用的启动方式：

### 主要改进

1. **统一启动脚本**: 使用 `start_distributed_worker.py` 作为唯一启动入口
2. **灵活配置**: 支持命令行参数、环境变量和配置文件三种配置方式
3. **生产就绪**: 包含完整的错误处理、日志记录和监控功能
4. **易于部署**: 提供多种部署策略和最佳实践指南
5. **故障排除**: 详细的故障排除指南和性能调优建议

### 推荐使用方式

- **开发环境**: 使用命令行参数快速启动
- **生产环境**: 使用配置文件进行标准化部署
- **容器化**: 支持 Docker 和 Kubernetes 部署
- **监控**: 启用指标收集进行性能监控

### 下一步

1. 根据本指南配置您的 Worker 节点
2. 选择适合的部署策略
3. 配置监控和日志收集
4. 进行性能调优和故障排除

---

**注意**: 本文档会随着系统更新而持续更新，请定期查看最新版本。

如有问题或建议，请联系开发团队或提交 Issue。