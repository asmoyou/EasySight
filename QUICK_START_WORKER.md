# EasySight 分布式Worker节点快速启动指南

本指南将帮助您快速部署和使用EasySight的分布式Worker节点功能。

## 📋 前置要求

- Python 3.8+
- 已安装EasySight主应用的依赖
- 网络连通性（如果使用分布式模式）

## 🚀 快速开始

### 1. 验证部署环境

首先验证您的环境是否满足部署要求：

```bash
# 进入backend目录
cd backend

# 运行部署验证
python verify_deployment.py --check-all
```

### 2. 配置Worker节点

复制并编辑配置文件：

```bash
# 复制示例配置
cp worker.env.example worker.env

# 编辑配置文件
notepad worker.env  # Windows
# 或
vim worker.env      # Linux/Mac
```

基本配置示例：
```env
# 节点基本信息
WORKER_NODE_NAME=worker-01
WORKER_POOL_SIZE=3

# 主节点连接
MASTER_HOST=localhost
MASTER_PORT=8000

# 数据库连接（如果需要）
DATABASE_URL=postgresql://user:password@localhost:5432/easysight

# Redis连接（如果需要）
REDIS_URL=redis://localhost:6379/0
```

### 3. 启动主应用

在主节点上启动EasySight主应用：

```bash
# 启动主应用
python main.py
```

主应用将在 `http://localhost:8000` 启动。

### 4. 启动Worker节点

#### 方式一：使用配置文件启动

```bash
# 使用配置文件启动分布式Worker
python start_worker.py --config worker.env
```

#### 方式二：使用命令行参数启动

```bash
# 启动分布式Worker（连接到主节点）
python start_worker.py \
  --mode distributed \
  --node-name worker-01 \
  --pool-size 3 \
  --master-host localhost \
  --master-port 8000
```

#### 方式三：启动独立Worker

```bash
# 启动独立Worker（不连接主节点）
python start_worker.py \
  --mode standalone \
  --node-name standalone-worker \
  --pool-size 2
```

### 5. 验证Worker状态

#### 检查分布式Worker状态

```bash
# 通过API检查所有分布式Worker
curl http://localhost:8000/api/v1/diagnosis/workers/distributed
```

#### 运行功能测试

```bash
# 运行完整测试
python test_worker.py --test-all --master-host localhost

# 仅测试连接
python test_worker.py --test-connection --master-host localhost

# 仅测试配置
python test_worker.py --test-config
```

## 🔧 常用操作

### 查看Worker日志

```bash
# Worker节点会输出详细日志到控制台
# 您也可以重定向到文件
python start_worker.py --config worker.env > worker.log 2>&1
```

### 停止Worker节点

- 在控制台按 `Ctrl+C` 优雅停止
- Worker会自动从主节点注销

### 监控Worker状态

访问主应用的管理界面：
- 浏览器打开：`http://localhost:8000/docs`
- 查看 `/diagnosis/workers/distributed` 接口

## 🐳 Docker部署

### 构建Worker镜像

```bash
# 构建Worker Docker镜像
docker build -f Dockerfile.worker -t easysight-worker .
```

### 运行Worker容器

```bash
# 运行单个Worker容器
docker run -d \
  --name easysight-worker-01 \
  --env-file worker.env \
  easysight-worker
```

### 使用Docker Compose

```bash
# 启动完整的分布式集群
docker-compose -f docker-compose.worker.yml up -d

# 查看服务状态
docker-compose -f docker-compose.worker.yml ps

# 查看日志
docker-compose -f docker-compose.worker.yml logs -f worker-01
```

## 🌐 多机部署

### 主节点配置

确保主节点可以被其他机器访问：

```bash
# 启动时绑定到所有接口
uvicorn main:app --host 0.0.0.0 --port 8000
```

### Worker节点配置

在其他机器上配置Worker：

```env
# worker.env
WORKER_NODE_NAME=worker-remote-01
MASTER_HOST=192.168.1.100  # 主节点IP
MASTER_PORT=8000
```

```bash
# 启动远程Worker
python start_worker.py --config worker.env
```

## 📊 性能优化

### Worker池大小调优

```bash
# CPU密集型任务：Worker数 = CPU核心数
python start_worker.py --pool-size 4

# IO密集型任务：Worker数 = CPU核心数 * 2-4
python start_worker.py --pool-size 8
```

### 内存优化

```env
# 在worker.env中设置
WORKER_MAX_MEMORY_MB=1024
WORKER_TASK_TIMEOUT=300
```

## 🔍 故障排除

### 常见问题

1. **Worker无法连接到主节点**
   ```bash
   # 检查网络连通性
   python test_worker.py --test-connection --master-host <主节点IP>
   
   # 检查防火墙设置
   telnet <主节点IP> 8000
   ```

2. **Worker注册失败**
   ```bash
   # 检查主节点API是否正常
   curl http://<主节点IP>:8000/health
   
   # 查看Worker详细日志
   python start_worker.py --log-level DEBUG
   ```

3. **任务执行失败**
   ```bash
   # 检查数据库连接
   python test_worker.py --test-config
   
   # 查看任务队列状态
   curl http://localhost:8000/api/v1/diagnosis/tasks/status
   ```

### 日志分析

```bash
# 启用详细日志
python start_worker.py --log-level DEBUG

# 过滤特定日志
python start_worker.py 2>&1 | grep "ERROR\|WARNING"
```

## 🔐 安全配置

### API密钥认证

```env
# 在worker.env中配置
API_KEY=your-secure-api-key
API_KEY_HEADER=X-API-Key
```

### SSL/TLS配置

```env
# 使用HTTPS连接主节点
MASTER_HOST=https://your-master-node.com
SSL_VERIFY=true
```

## 📈 监控和告警

### 健康检查

```bash
# Worker节点提供健康检查接口
curl http://localhost:8001/health
```

### 指标收集

```bash
# 查看Worker指标
curl http://localhost:8001/metrics
```

## 🔄 升级和维护

### 滚动更新

```bash
# 1. 停止旧Worker
pkill -f "start_worker.py"

# 2. 更新代码
git pull

# 3. 启动新Worker
python start_worker.py --config worker.env
```

### 备份配置

```bash
# 备份配置文件
cp worker.env worker.env.backup.$(date +%Y%m%d)
```

## 📚 更多资源

- [完整部署指南](DISTRIBUTED_WORKER_README.md)
- [API文档](http://localhost:8000/docs)
- [故障排除指南](DISTRIBUTED_WORKER_README.md#故障排除)

## 💡 最佳实践

1. **生产环境建议**：
   - 使用systemd或Docker管理Worker进程
   - 配置日志轮转
   - 设置资源限制
   - 启用监控告警

2. **开发环境建议**：
   - 使用独立模式进行本地测试
   - 启用详细日志
   - 使用较小的Worker池

3. **性能调优**：
   - 根据任务类型调整Worker池大小
   - 监控系统资源使用情况
   - 定期检查任务执行时间

---

如果您遇到任何问题，请查看详细的[部署指南](DISTRIBUTED_WORKER_README.md)或提交Issue。