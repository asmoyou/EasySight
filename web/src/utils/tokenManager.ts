import { isTokenExpiringSoon, getToken, isTokenExpired } from './auth'
import { useUserStore } from '@/stores/user'
import { TOKEN_CONFIG } from '@/config/token'

class TokenManager {
  private checkInterval: number | null = null
  private activityTimeout: number | null = null
  private lastActivity: number = Date.now()
  private readonly CHECK_INTERVAL = TOKEN_CONFIG.CHECK_INTERVAL
  private readonly ACTIVITY_TIMEOUT = TOKEN_CONFIG.ACTIVITY_TIMEOUT
  private readonly ACTIVITY_EVENTS = TOKEN_CONFIG.ACTIVITY_EVENTS
  
  constructor() {
    this.bindActivityListeners()
  }
  
  /**
   * 开始token监控
   */
  startMonitoring() {
    if (this.checkInterval) {
      return
    }
    
    if (TOKEN_CONFIG.ENABLE_CONSOLE_LOG) {
      console.log('开始Token监控')
    }
    this.checkInterval = window.setInterval(() => {
      this.checkTokenStatus()
    }, this.CHECK_INTERVAL)
    
    // 立即检查一次
    this.checkTokenStatus()
  }
  
  /**
   * 停止token监控
   */
  stopMonitoring() {
    if (this.checkInterval) {
      clearInterval(this.checkInterval)
      this.checkInterval = null
      if (TOKEN_CONFIG.ENABLE_CONSOLE_LOG) {
        console.log('停止Token监控')
      }
    }
    
    if (this.activityTimeout) {
      clearTimeout(this.activityTimeout)
      this.activityTimeout = null
    }
  }
  
  /**
   * 检查token状态
   */
  private async checkTokenStatus() {
    const token = getToken()
    if (!token) {
      this.stopMonitoring()
      return
    }
    
    // 检查token是否已过期
    if (isTokenExpired(token)) {
      if (TOKEN_CONFIG.ENABLE_CONSOLE_LOG) {
        console.log('Token已过期，尝试刷新')
      }
      await this.refreshTokenIfNeeded()
      return
    }
    
    // 检查token是否即将过期
    if (isTokenExpiringSoon(token)) {
      if (TOKEN_CONFIG.ENABLE_CONSOLE_LOG) {
        console.log('Token即将过期，尝试刷新')
      }
      await this.refreshTokenIfNeeded()
    }
  }
  
  /**
   * 刷新token
   */
  private async refreshTokenIfNeeded() {
    try {
      const userStore = useUserStore()
      await userStore.refreshToken()
      if (TOKEN_CONFIG.ENABLE_CONSOLE_LOG) {
        console.log('Token自动刷新成功')
      }
    } catch (error) {
      console.error('Token自动刷新失败:', error)
      this.stopMonitoring()
      // 可以在这里触发登出或重定向到登录页
      const userStore = useUserStore()
      userStore.logout()
    }
  }
  
  /**
   * 绑定用户活动监听器
   */
  private bindActivityListeners() {
    const updateActivity = async () => {
      this.lastActivity = Date.now()
      
      // 如果有活动且当前没有监控，则开始监控
      const token = getToken()
      if (token && !this.checkInterval) {
        this.startMonitoring()
      }
      
      // 用户有活动时检查token是否即将过期，如果是则立即刷新
       if (token && TOKEN_CONFIG.CHECK_ON_ACTIVITY && isTokenExpiringSoon(token)) {
         if (TOKEN_CONFIG.ENABLE_CONSOLE_LOG) {
           console.log('用户活动时检测到token即将过期，立即刷新')
         }
         await this.refreshTokenIfNeeded()
       }
      
      // 重置活动超时
      if (this.activityTimeout) {
        clearTimeout(this.activityTimeout)
      }
      
      // 设置新的活动超时
      this.activityTimeout = window.setTimeout(() => {
        const timeSinceLastActivity = Date.now() - this.lastActivity
        if (timeSinceLastActivity >= this.ACTIVITY_TIMEOUT) {
          if (TOKEN_CONFIG.ENABLE_CONSOLE_LOG) {
            console.log('用户长时间无活动，停止Token监控')
          }
          this.stopMonitoring()
        }
      }, this.ACTIVITY_TIMEOUT)
    }
    
    // 绑定所有活动事件
    this.ACTIVITY_EVENTS.forEach(event => {
      document.addEventListener(event, updateActivity, { passive: true })
    })
    
    // 页面可见性变化时的处理
    document.addEventListener('visibilitychange', () => {
      if (document.visibilityState === 'visible') {
        updateActivity()
        // 页面重新可见时立即检查token
        this.checkTokenStatus()
      } else {
        // 页面隐藏时停止监控以节省资源
        this.stopMonitoring()
      }
    })
  }
  
  /**
   * 手动触发token检查和刷新
   */
  async checkAndRefreshToken() {
    const token = getToken()
    if (!token) {
      return false
    }
    
    if (isTokenExpired(token) || isTokenExpiringSoon(token)) {
      await this.refreshTokenIfNeeded()
      return true
    }
    
    return false
  }
}

// 创建全局实例
export const tokenManager = new TokenManager()

// 导出类型以便其他地方使用
export default TokenManager