import axios from 'axios'
import type { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useUserStore } from '@/stores/user'
import { getToken, isTokenExpiringSoon } from '@/utils/auth'
import { tokenManager } from '@/utils/tokenManager'
import { TOKEN_CONFIG } from '@/config/token'
import router from '@/router'

// 创建axios实例
const service: AxiosInstance = axios.create({
  baseURL: '/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
service.interceptors.request.use(
  async (config: AxiosRequestConfig) => {
    // 添加认证token（logout和refresh接口不需要预检查）
    const token = getToken()
    if (token && config.headers && !config.url?.includes('/v1/auth/logout') && !config.url?.includes('/v1/auth/refresh')) {
      // 检查token是否即将过期，如果是则先刷新
      if (TOKEN_CONFIG.CHECK_BEFORE_REQUEST && isTokenExpiringSoon(token)) {
        if (TOKEN_CONFIG.ENABLE_CONSOLE_LOG) {
          console.log('请求前检测到token即将过期，尝试刷新')
        }
        try {
          await tokenManager.checkAndRefreshToken()
          // 刷新后重新获取token
          const newToken = getToken()
          if (newToken) {
            config.headers.Authorization = `Bearer ${newToken}`
          }
        } catch (error) {
          console.error('请求前刷新token失败:', error)
          // 刷新失败，仍然使用原token，让后续的401处理
          config.headers.Authorization = `Bearer ${token}`
        }
      } else {
        config.headers.Authorization = `Bearer ${token}`
      }
    }
    
    return config
  },
  (error) => {
    console.error('请求错误:', error)
    return Promise.reject(error)
  }
)

// 响应拦截器
service.interceptors.response.use(
  (response: AxiosResponse) => {
    const { data } = response
    
    // 如果是文件下载等特殊响应，直接返回
    if (response.config.responseType === 'blob') {
      return response
    }
    
    // 正常响应
    if (data.success !== false) {
      return response
    }
    
    // 业务错误
    ElMessage.error(data.message || '请求失败')
    return Promise.reject(new Error(data.message || '请求失败'))
  },
  async (error) => {
    const { response } = error
    
    if (!response) {
      ElMessage.error('网络连接失败，请检查网络设置')
      return Promise.reject(error)
    }
    
    const { status, data } = response
    
    switch (status) {
      case 401:
        // 如果是登录请求失败，显示错误消息
        if (error.config?.url?.includes('/v1/auth/login')) {
          ElMessage.error(data?.detail || '用户名或密码错误')
        } else if (error.config?.url?.includes('/v1/auth/logout')) {
          // logout接口401错误，直接清除本地数据并跳转
          const userStore = useUserStore()
          userStore.logout(false).then(() => {
            router.push('/login')
          })
        } else {
          // 其他401错误，可能token过期
          await handleUnauthorized(error.config)
        }
        break
      case 403:
        ElMessage.error('权限不足，无法访问该资源')
        break
      case 404:
        ElMessage.error('请求的资源不存在')
        break
      case 422:
        // 表单验证错误
        if (data.detail && Array.isArray(data.detail)) {
          const errors = data.detail.map((item: any) => item.msg).join(', ')
          ElMessage.error(errors)
        } else {
          ElMessage.error(data.detail || '请求参数错误')
        }
        break
      case 429:
        ElMessage.error('请求过于频繁，请稍后再试')
        break
      case 500:
        ElMessage.error('服务器内部错误，请联系管理员')
        break
      case 502:
      case 503:
      case 504:
        ElMessage.error('服务暂时不可用，请稍后再试')
        break
      default:
        ElMessage.error(data?.detail || `请求失败 (${status})`)
    }
    
    return Promise.reject(error)
  }
)

// 处理未授权错误
let isRefreshing = false
let failedQueue: Array<{
  resolve: (value?: any) => void
  reject: (reason?: any) => void
}> = []

const processQueue = (error: any, token: string | null = null) => {
  failedQueue.forEach(({ resolve, reject }) => {
    if (error) {
      reject(error)
    } else {
      resolve(token)
    }
  })
  
  failedQueue = []
}

const handleUnauthorized = async (config?: any) => {
  const userStore = useUserStore()
  
  // 如果是登录请求失败，不进行token刷新和弹窗处理
  if (config?.url?.includes('/v1/auth/login')) {
    return Promise.reject(new Error('登录失败'))
  }
  
  if (isRefreshing) {
    // 如果正在刷新token，将请求加入队列
    return new Promise((resolve, reject) => {
      failedQueue.push({ resolve, reject })
    })
  }
  
  isRefreshing = true
  
  try {
    // 尝试刷新token
    const success = await userStore.refreshToken()
    if (success) {
      processQueue(null, getToken())
      return Promise.resolve()
    } else {
      throw new Error('刷新token失败')
    }
  } catch (error) {
    processQueue(error, null)
    
    // 刷新失败，提示用户重新登录
    ElMessageBox.confirm(
      '登录状态已过期，请重新登录',
      '提示',
      {
        confirmButtonText: '重新登录',
        cancelButtonText: '取消',
        type: 'warning'
      }
    ).then(() => {
      userStore.logout(false).then(() => {
        // 确保在下一个事件循环中执行路由跳转
        setTimeout(() => {
          router.push('/login')
        }, 0)
      })
    }).catch(() => {
      // 用户取消，也执行登出
      userStore.logout(false).then(() => {
        setTimeout(() => {
          router.push('/login')
        }, 0)
      })
    })
    
    return Promise.reject(error)
  } finally {
    isRefreshing = false
  }
}

// 导出常用的请求方法
export default {
  get<T = any>(url: string, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return service.get(url, config)
  },
  
  post<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return service.post(url, data, config)
  },
  
  put<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return service.put(url, data, config)
  },
  
  delete<T = any>(url: string, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return service.delete(url, config)
  },
  
  patch<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return service.patch(url, data, config)
  },
  
  upload<T = any>(url: string, formData: FormData, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return service.post(url, formData, {
      ...config,
      headers: {
        'Content-Type': 'multipart/form-data',
        ...config?.headers
      }
    })
  },
  
  download(url: string, config?: AxiosRequestConfig): Promise<AxiosResponse<Blob>> {
    return service.get(url, {
      ...config,
      responseType: 'blob'
    })
  }
}

// 导出axios实例，供特殊情况使用
export { service }