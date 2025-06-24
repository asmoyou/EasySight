import Cookies from 'js-cookie'

const TOKEN_KEY = 'easysight_token'
const REFRESH_TOKEN_KEY = 'easysight_refresh_token'

// Token 相关操作
export const getToken = (): string | undefined => {
  return Cookies.get(TOKEN_KEY)
}

export const setToken = (token: string): void => {
  Cookies.set(TOKEN_KEY, token, { expires: 7 }) // 7天过期
}

export const removeToken = (): void => {
  Cookies.remove(TOKEN_KEY)
  Cookies.remove(REFRESH_TOKEN_KEY)
}

// Refresh Token 相关操作
export const getRefreshToken = (): string | undefined => {
  return Cookies.get(REFRESH_TOKEN_KEY)
}

export const setRefreshToken = (token: string): void => {
  Cookies.set(REFRESH_TOKEN_KEY, token, { expires: 30 }) // 30天过期
}

// 检查是否已登录
export const isLoggedIn = (): boolean => {
  return !!getToken()
}

// 解析JWT Token（简单解析，不验证签名）
export const parseJWT = (token: string): any => {
  try {
    const base64Url = token.split('.')[1]
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/')
    const jsonPayload = decodeURIComponent(
      atob(base64)
        .split('')
        .map(c => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
        .join('')
    )
    return JSON.parse(jsonPayload)
  } catch (error) {
    console.error('解析JWT失败:', error)
    return null
  }
}

// 检查Token是否即将过期（提前5分钟）
export const isTokenExpiringSoon = (token: string): boolean => {
  const payload = parseJWT(token)
  if (!payload || !payload.exp) {
    return true
  }
  
  const expirationTime = payload.exp * 1000 // 转换为毫秒
  const currentTime = Date.now()
  const fiveMinutes = 5 * 60 * 1000 // 5分钟
  
  return (expirationTime - currentTime) < fiveMinutes
}

// 检查Token是否已过期
export const isTokenExpired = (token: string): boolean => {
  const payload = parseJWT(token)
  if (!payload || !payload.exp) {
    return true
  }
  
  const expirationTime = payload.exp * 1000
  const currentTime = Date.now()
  
  return currentTime >= expirationTime
}

// 获取Token中的用户信息
export const getUserFromToken = (token: string): any => {
  const payload = parseJWT(token)
  return payload ? {
    id: payload.sub,
    username: payload.username,
    role: payload.role,
    permissions: payload.permissions || []
  } : null
}

// 权限检查
export const hasPermission = (permission: string, userPermissions: string[]): boolean => {
  return userPermissions.indexOf(permission) !== -1 || userPermissions.indexOf('*') !== -1
}

export const hasRole = (role: string, userRole: string): boolean => {
  return userRole === role || userRole === 'admin'
}

// 权限级别检查
export const hasMinimumRole = (requiredRole: string, userRole: string): boolean => {
  const roleHierarchy = {
    'viewer': 1,
    'operator': 2,
    'admin': 3
  }
  
  const userLevel = roleHierarchy[userRole as keyof typeof roleHierarchy] || 0
  const requiredLevel = roleHierarchy[requiredRole as keyof typeof roleHierarchy] || 0
  
  return userLevel >= requiredLevel
}