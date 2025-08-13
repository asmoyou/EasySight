# 日志中间件使用指南

## 概述

本项目提供了完善的日志中间件系统，支持异步数据库日志记录、性能监控、配置管理等功能。

## 功能特性

### 1. SystemLoggingMiddleware
- **异步数据库日志记录**: 将请求日志异步写入数据库，避免阻塞主请求
- **性能监控**: 自动检测慢请求和性能问题
- **智能日志级别**: 根据响应时间自动调整日志级别
- **客户端信息记录**: 支持代理环境下的真实IP获取
- **错误处理**: 完善的异常处理和超时控制

### 2. DependencyLoggingMiddleware
- **依赖注入监控**: 专门监控API依赖注入的性能
- **慢请求检测**: 自动检测依赖注入中的性能瓶颈
- **详细日志模式**: 可选的详细调试信息

### 3. LoggingConfig
- **环境变量配置**: 通过环境变量灵活配置日志行为
- **日志轮转**: 自动管理日志文件大小和数量
- **敏感信息过滤**: 自动过滤敏感的请求头信息
- **性能阈值配置**: 可配置的性能监控阈值

## 配置说明

### 环境变量配置

```bash
# 基础配置
ENABLE_DB_LOGGING=true              # 是否启用数据库日志记录
ENABLE_DETAILED_LOGGING=false       # 是否启用详细日志记录
ENABLE_PERFORMANCE_MONITORING=true  # 是否启用性能监控
LOG_LEVEL=INFO                      # 日志级别

# 文件配置
MAX_LOG_FILE_SIZE=10485760          # 最大日志文件大小 (10MB)
MAX_LOG_FILES=5                     # 最大日志文件数量

# 性能配置
SLOW_REQUEST_THRESHOLD=1000         # 慢请求阈值 (毫秒)
VERY_SLOW_REQUEST_THRESHOLD=5000    # 严重慢请求阈值 (毫秒)
```

### 在应用中使用

```python
from middleware.logging_middleware import SystemLoggingMiddleware, DependencyLoggingMiddleware

# 添加中间件
app.add_middleware(SystemLoggingMiddleware)
app.add_middleware(DependencyLoggingMiddleware)

# 或者手动配置
app.add_middleware(SystemLoggingMiddleware, enable_db_logging=True)
app.add_middleware(DependencyLoggingMiddleware, enable_detailed_logging=False)
```

## 日志输出

### 1. 标准日志
```
2024-01-01 12:00:00 - middleware.logging_middleware - INFO - POST /api/v1/cameras/ - Status: 201 - Time: 150.5ms - Client: 192.168.1.100 - RequestID: 12345678-1234-1234-1234-123456789012
```

### 2. 性能警告日志
```
2024-01-01 12:00:00 - middleware.logging_middleware - WARNING - SLOW REQUEST: POST /api/v1/cameras/ - Status: 200 - Time: 1500.0ms - Client: 192.168.1.100 - RequestID: 12345678-1234-1234-1234-123456789012
```

### 3. 严重性能问题日志
```
2024-01-01 12:00:00 - middleware.logging_middleware - ERROR - CRITICAL PERFORMANCE: POST /api/v1/cameras/ - Status: 200 - Time: 6000.0ms - Client: 192.168.1.100 - RequestID: 12345678-1234-1234-1234-123456789012
```

## 数据库日志结构

日志会被存储在 `system_logs` 表中，包含以下字段：

- `id`: 主键
- `level`: 日志级别 (INFO/WARNING/ERROR)
- `module`: 模块名称 (middleware)
- `action`: 操作类型 (http_request/request_error)
- `message`: 日志消息
- `request_id`: 请求唯一标识
- `request_method`: HTTP方法
- `request_url`: 请求URL
- `response_status`: 响应状态码
- `response_time`: 响应时间 (毫秒)
- `ip_address`: 客户端IP地址
- `user_agent`: 用户代理
- `user_id`: 用户ID (如果已认证)
- `username`: 用户名 (如果已认证)
- `extra_data`: 额外数据 (JSON格式)
- `created_at`: 创建时间

## 性能优化

### 1. 异步处理
- 数据库日志记录使用异步任务，不会阻塞主请求
- 设置了5秒的数据库操作超时，避免长时间等待

### 2. 智能过滤
- 自动排除静态资源、健康检查等不重要的请求
- 过滤敏感信息，如认证头等

### 3. 日志轮转
- 自动管理日志文件大小，避免磁盘空间问题
- 保留指定数量的历史日志文件

## 故障排除

### 1. 数据库连接问题
如果数据库日志记录失败，中间件会：
- 记录错误到标准日志
- 继续处理请求，不影响业务功能
- 在详细日志模式下记录失败的日志数据

### 2. 性能问题
如果发现大量慢请求警告：
- 检查数据库连接池配置
- 优化数据库查询
- 考虑增加缓存
- 调整性能阈值配置

### 3. 日志文件过大
- 调整 `MAX_LOG_FILE_SIZE` 和 `MAX_LOG_FILES` 配置
- 考虑使用外部日志管理系统
- 定期清理旧日志文件

## 最佳实践

1. **生产环境配置**:
   - 设置 `ENABLE_DETAILED_LOGGING=false`
   - 根据业务需求调整性能阈值
   - 定期监控日志文件大小

2. **开发环境配置**:
   - 设置 `ENABLE_DETAILED_LOGGING=true`
   - 降低性能阈值以便及早发现问题
   - 启用所有监控功能

3. **监控建议**:
   - 定期检查性能日志文件
   - 设置告警机制监控严重性能问题
   - 分析慢请求模式，优化系统性能