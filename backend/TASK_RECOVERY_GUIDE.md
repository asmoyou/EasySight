# 诊断任务恢复机制使用指南

## 概述

EasySight 系统现已集成了完善的诊断任务恢复机制，用于解决任务长时间处于运行状态而实际未执行的问题。该机制包含两个主要API端点和一个命令行工具。

## 问题背景

在某些情况下，诊断任务可能会出现以下异常状态：
- 数据库中任务状态显示为 `running`，但实际未在执行
- 任务运行时间过长（超过预期时间）
- 执行器内存中的运行任务列表与数据库状态不一致
- 系统重启后任务状态未正确恢复

## API 端点

### 1. 任务状态检查 API

**端点**: `GET /api/diagnosis/tasks/status-check`

**功能**: 检查当前运行中的任务状态，识别可能卡住的任务，但不进行任何修改操作。

**参数**:
- `max_runtime_minutes` (可选): 任务最大运行时间（分钟），默认30分钟

**响应示例**:
```json
{
  "running_tasks": [
    {
      "id": 1,
      "name": "亮度检测任务",
      "last_run_time": "2025-01-15T10:30:00Z",
      "is_active": true,
      "is_actually_running": false,
      "runtime_minutes": 45.5,
      "stuck_reason": "任务不在执行器运行列表中"
    }
  ],
  "stuck_tasks": [
    {
      "id": 1,
      "name": "亮度检测任务",
      "stuck_reason": "任务不在执行器运行列表中"
    }
  ],
  "total_running": 1,
  "total_stuck": 1,
  "message": "检查完成：运行中任务 1 个，卡住任务 1 个"
}
```

### 2. 任务恢复 API

**端点**: `POST /api/diagnosis/tasks/recovery`

**功能**: 自动检测并重置卡住的任务状态为 `pending`，使其可以重新执行。

**参数**:
- `force_reset` (可选): 是否强制重置所有运行中的任务，默认 `false`
- `max_runtime_minutes` (可选): 任务最大运行时间（分钟），默认30分钟

**响应示例**:
```json
{
  "checked_tasks": 1,
  "reset_tasks": 1,
  "reset_task_ids": [1],
  "message": "成功重置 1 个卡住的任务"
}
```

## 使用场景

### 场景1: 定期检查任务状态

```bash
# 使用curl检查任务状态
curl -X GET "http://localhost:8000/api/diagnosis/tasks/status-check" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 场景2: 发现卡住任务后进行恢复

```bash
# 恢复卡住的任务
curl -X POST "http://localhost:8000/api/diagnosis/tasks/recovery" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 场景3: 强制重置所有运行中的任务

```bash
# 强制重置（谨慎使用）
curl -X POST "http://localhost:8000/api/diagnosis/tasks/recovery?force_reset=true" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 命令行工具

### 简单检查工具

位置: `backend/check_running_tasks_sql.py`

```bash
# 在backend目录下运行
python check_running_tasks_sql.py
```

该工具会：
1. 检查数据库中所有运行状态的任务
2. 验证任务是否真的在执行器中运行
3. 检查任务运行时间是否过长
4. 自动重置异常任务状态

## 前端集成建议

### 1. 任务管理页面增强

在任务列表页面添加以下功能：

```javascript
// 检查任务状态
async function checkTaskStatus() {
  try {
    const response = await fetch('/api/diagnosis/tasks/status-check', {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    const data = await response.json();
    
    if (data.total_stuck > 0) {
      // 显示警告信息
      showWarning(`发现 ${data.total_stuck} 个卡住的任务`);
      // 提供恢复按钮
      showRecoveryButton();
    }
  } catch (error) {
    console.error('检查任务状态失败:', error);
  }
}

// 恢复卡住的任务
async function recoverStuckTasks() {
  try {
    const response = await fetch('/api/diagnosis/tasks/recovery', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    const data = await response.json();
    
    showSuccess(data.message);
    // 刷新任务列表
    refreshTaskList();
  } catch (error) {
    console.error('任务恢复失败:', error);
  }
}
```

### 2. 自动监控

```javascript
// 定期检查任务状态（每5分钟）
setInterval(checkTaskStatus, 5 * 60 * 1000);

// 页面加载时检查
window.addEventListener('load', checkTaskStatus);
```

### 3. 用户界面提示

在任务列表中为卡住的任务添加特殊标识：

```html
<!-- 任务状态显示 -->
<div class="task-status">
  <span class="status-badge status-stuck" v-if="task.isStuck">
    <i class="icon-warning"></i>
    任务卡住
  </span>
  <span class="status-badge status-running" v-else-if="task.status === 'running'">
    <i class="icon-loading"></i>
    运行中
  </span>
</div>

<!-- 恢复按钮 -->
<button class="btn-recovery" @click="recoverTask(task.id)" v-if="task.isStuck">
  恢复任务
</button>
```

## 监控和告警

### 1. 系统监控

建议在系统监控中添加以下指标：
- 卡住任务数量
- 任务平均运行时间
- 任务恢复频率

### 2. 告警规则

```yaml
# 示例告警配置
alerts:
  - name: stuck_tasks
    condition: stuck_tasks_count > 0
    message: "发现 {{ stuck_tasks_count }} 个卡住的诊断任务"
    actions:
      - send_notification
      - auto_recovery  # 可选：自动恢复
```

## 最佳实践

### 1. 预防措施

- 设置合理的任务超时时间
- 定期重启诊断服务
- 监控系统资源使用情况
- 及时处理异常日志

### 2. 恢复策略

- 优先使用状态检查API确认问题
- 避免频繁使用强制重置
- 在系统维护时间进行批量恢复
- 记录恢复操作日志

### 3. 故障排查

1. **检查执行器状态**
   ```python
   from diagnosis.executor import diagnosis_executor
   print(f"当前运行任务: {diagnosis_executor.running_tasks}")
   ```

2. **检查数据库状态**
   ```sql
   SELECT id, name, status, last_run_time 
   FROM diagnosis_tasks 
   WHERE status = 'running';
   ```

3. **检查系统日志**
   ```bash
   tail -f logs/diagnosis.log | grep ERROR
   ```

## 注意事项

1. **权限控制**: 任务恢复操作需要管理员权限
2. **数据一致性**: 恢复操作会修改数据库状态，请谨慎使用
3. **并发安全**: API端点已考虑并发安全，但仍建议避免同时调用
4. **日志记录**: 所有恢复操作都会记录在系统日志中
5. **备份策略**: 建议在大规模恢复前备份相关数据

## 更新日志

- **2025-01-15**: 初始版本，添加任务恢复机制
- 新增 `/tasks/status-check` 和 `/tasks/recovery` API端点
- 新增命令行检查工具
- 完善错误处理和日志记录