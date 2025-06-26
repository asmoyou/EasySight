# Token 自动管理系统

## 概述

EasySight 系统现在包含了一个完整的 Token 自动管理系统，可以在用户使用过程中自动检查和刷新 Token，避免用户因为 Token 过期而突然需要重新登录的问题。

## 功能特性

### 1. 多层次的 Token 检查机制

- **路由守卫检查**: 在页面切换时自动检查 Token 状态
- **请求拦截器检查**: 在发送 API 请求前检查 Token 状态
- **用户活动监听**: 监听用户操作，在有活动时检查 Token
- **定时检查**: 定期检查 Token 状态（默认每分钟一次）

### 2. 智能刷新策略

- **提前刷新**: Token 过期前 5 分钟开始尝试刷新
- **活动时刷新**: 用户有操作时立即检查并刷新即将过期的 Token
- **请求前刷新**: 发送请求前检查并刷新即将过期的 Token
- **失败处理**: 刷新失败时自动登出用户

### 3. 性能优化

- **活动监听**: 只在用户有活动时进行监控
- **智能停止**: 用户长时间无活动时自动停止监控以节省资源
- **页面可见性**: 页面隐藏时停止监控，重新可见时恢复

## 配置选项

配置文件位置: `src/config/token.ts`

```typescript
export const TOKEN_CONFIG = {
  // Token过期前多少毫秒开始提醒刷新（默认5分钟）
  EXPIRY_WARNING_TIME: 5 * 60 * 1000,
  
  // Token监控检查间隔（默认1分钟）
  CHECK_INTERVAL: 60 * 1000,
  
  // 用户无活动多长时间后停止监控（默认5分钟）
  ACTIVITY_TIMEOUT: 5 * 60 * 1000,
  
  // 监听的用户活动事件类型
  ACTIVITY_EVENTS: ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart', 'click'],
  
  // 是否启用控制台日志
  ENABLE_CONSOLE_LOG: true,
  
  // 是否在用户活动时立即检查token
  CHECK_ON_ACTIVITY: true,
  
  // 是否在请求前检查token
  CHECK_BEFORE_REQUEST: true,
  
  // 是否在路由切换时检查token
  CHECK_ON_ROUTE_CHANGE: true
}
```

## 使用方法

### 自动启动

系统会在以下情况自动启动 Token 监控：

1. 用户登录成功后
2. 应用启动时（如果本地存储中有有效 Token）
3. 用户有活动且当前没有监控时

### 手动控制

```typescript
import { tokenManager } from '@/utils/tokenManager'

// 手动启动监控
tokenManager.startMonitoring()

// 手动停止监控
tokenManager.stopMonitoring()

// 手动检查并刷新 Token
await tokenManager.checkAndRefreshToken()
```

### 配置更新

```typescript
import { updateTokenConfig } from '@/config/token'

// 更新配置
updateTokenConfig({
  CHECK_INTERVAL: 30 * 1000, // 改为30秒检查一次
  ENABLE_CONSOLE_LOG: false   // 关闭控制台日志
})
```

## 工作流程

### 1. 用户登录
```
用户登录 → 保存 Token → 启动 Token 监控 → 开始定时检查
```

### 2. Token 检查流程
```
检查 Token 状态 → 是否即将过期？ → 是 → 调用刷新 API → 更新本地 Token
                                  ↓
                                 否 → 继续监控
```

### 3. 用户活动监听
```
用户操作 → 更新活动时间 → 检查 Token → 如需要则刷新 → 重置活动超时
```

### 4. 请求拦截
```
发送请求 → 检查 Token → 即将过期？ → 是 → 先刷新 Token → 使用新 Token 发送请求
                                   ↓
                                  否 → 直接发送请求
```

## 错误处理

- **刷新失败**: 自动登出用户并重定向到登录页
- **Token 无效**: 清除本地存储并要求重新登录
- **网络错误**: 保留原 Token，由后续的 401 响应处理

## 性能考虑

1. **资源节约**: 用户无活动时自动停止监控
2. **避免重复**: 使用标志位避免重复刷新
3. **智能检查**: 只在必要时进行 Token 检查
4. **页面可见性**: 页面隐藏时暂停监控

## 调试信息

当 `ENABLE_CONSOLE_LOG` 为 `true` 时，系统会输出以下调试信息：

- Token 监控启动/停止
- Token 过期检查结果
- Token 刷新成功/失败
- 用户活动检测
- 长时间无活动检测

## 注意事项

1. **Token 有效期**: 确保后端 Token 有效期设置合理
2. **刷新接口**: 确保后端提供可靠的 Token 刷新接口
3. **时间同步**: 客户端和服务器时间应保持同步
4. **配置调整**: 根据实际使用情况调整检查间隔和超时时间

## 故障排除

### Token 频繁刷新
- 检查系统时间是否同步
- 调整 `EXPIRY_WARNING_TIME` 配置
- 检查后端 Token 有效期设置

### Token 刷新失败
- 检查网络连接
- 检查后端刷新接口状态
- 查看控制台错误信息

### 监控未启动
- 检查用户是否已登录
- 检查本地存储中是否有 Token
- 检查配置开关是否开启