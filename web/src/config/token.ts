/**
 * Token管理相关配置
 */
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

/**
 * 获取token配置
 */
export const getTokenConfig = () => {
  return { ...TOKEN_CONFIG }
}

/**
 * 更新token配置
 */
export const updateTokenConfig = (config: Partial<typeof TOKEN_CONFIG>) => {
  Object.assign(TOKEN_CONFIG, config)
}