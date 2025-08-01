# Worker节点重连机制修复文档

## 问题描述

当主服务重启时，已连接的Worker节点会出现以下问题：

1. **404错误持续出现**: Worker节点继续发送心跳和请求任务，但收到404 Not Found错误
2. **无法自动重连**: Worker节点没有检测到主服务重启，不会自动重新注册
3. **连接状态不一致**: 主服务重启后内存中的`distributed_workers`字典被清空，但Worker节点仍认为自己已注册

## 根本原因

1. **内存存储**: 主服务使用内存字典`distributed_workers`存储Worker节点信息，重启后数据丢失
2. **缺乏重连逻辑**: Worker节点收到404错误时没有自动重新注册的机制
3. **状态检测不足**: 没有有效的机制来检测主服务是否重启

## 解决方案

### 1. Worker端修复

#### 1.1 自动重新注册机制

在`distributed_worker.py`中添加了404错误处理逻辑：

```python
# 心跳发送时检测404错误
elif response.status == 404:
    # 主服务重启导致节点未注册，自动重新注册
    logger.warning(f"节点未注册(404)，尝试重新注册: {self.config.node_id}")
    await self._register_node()

# 任务获取时检测404错误
elif response.status == 404:
    # 主服务重启导致节点未注册，自动重新注册
    logger.warning(f"节点未注册(404)，尝试重新注册: {self.config.node_id}")
    await self._register_node()
    return []
```

#### 1.2 改进注册逻辑

添加了重试机制和更好的错误处理：

```python
async def _register_node(self):
    max_retries = 3
    retry_delay = 5  # 秒
    
    for attempt in range(max_retries):
        try:
            # 注册逻辑...
            if response.status == 200:
                logger.info(f"节点 {self.config.node_id} 注册成功")
                return True
        except Exception as e:
            logger.error(f"节点注册异常 (尝试 {attempt + 1}/{max_retries}): {str(e)}")
            
        # 重试延迟
        if attempt < max_retries - 1:
            await asyncio.sleep(retry_delay)
```

#### 1.3 连接监控循环

添加了独立的连接监控机制：

```python
async def _connection_monitor_loop(self):
    """连接监控循环，定期检查与主服务的连接状态"""
    monitor_interval = 60  # 每60秒检查一次
    
    while self.running:
        # 检查最后一次成功心跳的时间
        if self.last_heartbeat:
            time_since_last_heartbeat = (datetime.now(timezone.utc) - self.last_heartbeat).total_seconds()
            
            # 如果超过3个心跳间隔没有成功心跳，尝试重新注册
            if time_since_last_heartbeat > (self.config.heartbeat_interval * 3):
                logger.warning(f"长时间未收到心跳响应，尝试重新注册节点: {self.config.node_id}")
                await self._register_node()
```

### 2. 服务端修复

#### 2.1 支持重复注册

修改了`_register_worker_internal`函数，支持Worker节点重复注册并保留统计信息：

```python
async def _register_worker_internal(worker_info: dict, db: AsyncSession):
    node_id = worker_info.get("node_id")
    
    # 检查是否已存在该节点，如果存在则保留统计信息
    existing_data = distributed_workers.get(node_id, {})
    
    node_data = {
        # ... 基本信息 ...
        # 保留已有的统计信息，如果是新节点则使用默认值
        "total_tasks_executed": existing_data.get("total_tasks_executed", 0),
        "current_tasks": 0,  # 重新注册时重置当前任务数
        "current_task_ids": []  # 重新注册时清空当前任务列表
    }
```

## 修复效果

1. **自动重连**: Worker节点在检测到404错误时会自动重新注册
2. **状态保持**: 重新注册时保留Worker节点的历史统计信息
3. **连接监控**: 独立的监控循环确保长期连接稳定性
4. **错误恢复**: 多重机制确保在各种网络问题下都能恢复连接

## 测试方法

使用提供的测试脚本验证修复效果：

```bash
# 启动主服务
python main.py

# 在另一个终端启动测试脚本
python test_worker_reconnect.py

# 在第三个终端重启主服务，观察Worker是否自动重连
```

## 预防措施

为了进一步提高系统稳定性，建议：

1. **持久化存储**: 考虑将Worker节点信息存储到数据库中，而不是内存
2. **健康检查**: 添加定期的健康检查机制
3. **监控告警**: 添加Worker节点连接状态的监控和告警
4. **负载均衡**: 在多个主服务实例之间实现负载均衡

## 相关文件

- `distributed_worker.py`: Worker客户端实现
- `routers/diagnosis.py`: 主服务Worker API实现
- `worker_config.py`: Worker配置
- `test_worker_reconnect.py`: 重连机制测试脚本