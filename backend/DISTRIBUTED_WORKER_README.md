# EasySight 分布式Worker节点部署指南

## 概述

EasySight现在支持分布式Worker节点部署，允许将诊断任务的执行分布到多个独立的服务器上，提高系统的可扩展性和容错能力。

## 架构说明

### 主要组件

1. **主应用节点**：运行FastAPI主服务，负责任务调度、API服务和Web界面
2. **分布式Worker节点**：独立运行的Worker进程，负责执行具体的诊断任务
3. **任务分发机制**：通过HTTP API进行任务分发和状态同步

### 运行模式

- **分布式模式**：Worker节点连接到主节点，自动拉取和执行任务
- **独立模式**：Worker节点仅启动本地Worker池，通过API接收任务

## 快速开始

### 1. 启动主应用（不含Worker）

主应用现在默认不启动Worker池，只提供API服务和任务调度：

```bash
cd backend
python main.py
```

### 2. 启动分布式Worker节点

#### 方式一：使用默认配置

```bash
cd backend
python start_worker.py --mode distributed --master-host localhost --pool-size 3
```

#### 方式二：使用配置文件

1. 复制配置文件模板：
```bash
cp worker.env.example worker.env
```

2. 编辑配置文件：
```bash
# 修改 worker.env 中的配置
WORKER_MASTER_HOST=192.168.1.100  # 主节点IP
WORKER_NODE_NAME=worker-node-1
WORKER_WORKER_POOL_SIZE=5
```

3. 启动Worker：
```bash
python start_worker.py --config worker.env
```

#### 方式三：独立模式

```bash
python start_worker.py --mode standalone --pool-size 3
```

## 配置说明

### 命令行参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--mode` | 运行模式（distributed/standalone） | distributed |
| `--config` | 配置文件路径 | - |
| `--node-id` | 节点ID（自动生成） | - |
| `--node-name` | 节点名称 | worker-node |
| `--pool-size` | Worker池大小 | 3 |
| `--max-concurrent-tasks` | 每个Worker最大并发任务数 | 3 |
| `--master-host` | 主节点主机地址 | localhost |
| `--master-port` | 主节点端口 | 8000 |
| `--api-token` | API认证令牌 | - |
| `--log-level` | 日志级别 | INFO |
| `--log-file` | 日志文件路径 | - |
| `--task-poll-interval` | 任务轮询间隔（秒） | 5 |
| `--heartbeat-interval` | 心跳间隔（秒） | 30 |

### 环境变量配置

所有配置都可以通过环境变量设置，变量名格式为 `WORKER_<配置名>`：

```bash
export WORKER_MASTER_HOST=192.168.1.100
export WORKER_WORKER_POOL_SIZE=5
export WORKER_LOG_LEVEL=DEBUG
```

## 部署示例

### 单机多Worker部署

在同一台服务器上运行多个Worker节点：

```bash
# 终端1：启动主应用
python main.py

# 终端2：启动Worker节点1
python start_worker.py --node-name worker-1 --pool-size 3

# 终端3：启动Worker节点2
python start_worker.py --node-name worker-2 --pool-size 2
```

### 多机分布式部署

#### 主节点（192.168.1.100）

```bash
# 启动主应用
python main.py
```

#### Worker节点1（192.168.1.101）

```bash
# 创建配置文件
cat > worker.env << EOF
WORKER_MASTER_HOST=192.168.1.100
WORKER_NODE_NAME=worker-node-101
WORKER_WORKER_POOL_SIZE=4
WORKER_LOG_LEVEL=INFO
EOF

# 启动Worker
python start_worker.py --config worker.env
```

#### Worker节点2（192.168.1.102）

```bash
# 直接使用命令行参数
python start_worker.py \
  --master-host 192.168.1.100 \
  --node-name worker-node-102 \
  --pool-size 6 \
  --log-level DEBUG
```

## 监控和管理

### API接口

1. **查看分布式Worker状态**：
   ```
   GET /api/v1/diagnosis/workers/distributed
   ```

2. **查看本地Worker状态**：
   ```
   GET /api/v1/diagnosis/workers/status
   ```

3. **手动提交任务**：
   ```
   POST /api/v1/diagnosis/tasks/{task_id}/submit
   ```

### 日志监控

```bash
# 查看Worker日志
tail -f /var/log/easysight/worker.log

# 或者使用标准输出
python start_worker.py --log-level DEBUG
```

## 故障排除

### 常见问题

1. **Worker节点无法连接到主节点**
   - 检查网络连通性
   - 确认主节点IP和端口配置正确
   - 检查防火墙设置

2. **Worker节点注册失败**
   - 检查API认证令牌配置
   - 确认主节点API服务正常运行

3. **任务执行失败**
   - 检查Worker节点的数据库连接配置
   - 确认诊断算法依赖库已安装
   - 查看详细错误日志

### 调试模式

```bash
# 启用详细日志
python start_worker.py --log-level DEBUG

# 查看系统资源使用情况
htop
iostat -x 1
```

## 性能优化

### Worker配置优化

1. **根据服务器配置调整Worker数量**：
   ```bash
   # CPU密集型任务：Worker数 = CPU核心数
   python start_worker.py --pool-size 8
   
   # IO密集型任务：Worker数 = CPU核心数 * 2
   python start_worker.py --pool-size 16
   ```

2. **调整任务轮询间隔**：
   ```bash
   # 高频任务场景
   python start_worker.py --task-poll-interval 1
   
   # 低频任务场景
   python start_worker.py --task-poll-interval 10
   ```

3. **配置并发任务数**：
   ```bash
   # 增加单个Worker的并发能力
   python start_worker.py --max-concurrent-tasks 5
   ```

### 系统级优化

1. **使用进程管理器**：
   ```bash
   # 使用systemd管理Worker进程
   sudo systemctl start easysight-worker
   sudo systemctl enable easysight-worker
   ```

2. **配置负载均衡**：
   - 在多个Worker节点前配置负载均衡器
   - 实现任务的智能分发

## 安全考虑

1. **API认证**：
   ```bash
   # 使用API令牌
   python start_worker.py --api-token your_secure_token
   ```

2. **网络安全**：
   - 使用VPN或专用网络连接Worker节点
   - 配置防火墙规则限制访问

3. **数据安全**：
   - 确保数据库连接使用SSL
   - 定期更新依赖库和系统补丁

## 扩展和定制

### 自定义Worker类型

可以通过修改 `distributed_worker.py` 来支持不同类型的Worker：

```python
class SpecializedWorker(StandaloneWorkerNode):
    def __init__(self, config, worker_type="image_analysis"):
        super().__init__(config)
        self.worker_type = worker_type
    
    async def execute_specialized_task(self, task_data):
        # 实现特定类型的任务处理逻辑
        pass
```

### 集成消息队列

对于更复杂的分布式场景，可以集成Redis或RabbitMQ：

```python
# 在 distributed_worker.py 中添加
import redis

class RedisWorkerClient(DistributedWorkerClient):
    def __init__(self, config):
        super().__init__(config)
        self.redis_client = redis.Redis(
            host=config.redis_host,
            port=config.redis_port,
            db=config.redis_db
        )
```

## 版本兼容性

- Python 3.7+
- FastAPI 0.68+
- SQLAlchemy 1.4+
- aiohttp 3.8+

## 更新日志

### v1.0.0
- 初始版本，支持基本的分布式Worker功能
- 实现节点注册、心跳和任务分发机制
- 支持配置文件和命令行参数配置