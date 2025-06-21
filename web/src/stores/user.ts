import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { User, LoginForm, LoginResponse } from '@/types/user'
import { authApi } from '@/api/auth'
import { getToken, setToken, removeToken } from '@/utils/auth'
import { ElMessage } from 'element-plus'

export const useUserStore = defineStore('user', () => {
  const user = ref<User | null>(null)
  const token = ref<string>('')
  const permissions = ref<string[]>([])
  
  // 计算属性
  const isLoggedIn = computed(() => !!token.value && !!user.value)
  const userInfo = computed(() => user.value)
  const userPermissions = computed(() => permissions.value)
  
  // 登录
  const login = async (loginForm: LoginForm): Promise<boolean> => {
    try {
        const response = await authApi.login(loginForm)
      const { access_token, user_info: userInfo } = response.data
      
      // 保存token和用户信息
      token.value = access_token
      user.value = userInfo
      permissions.value = userInfo.permissions || []
      
      // 保存到本地存储
      setToken(access_token)
      localStorage.setItem('user_info', JSON.stringify(userInfo))
      
      ElMessage.success('登录成功')
      return true
    } catch (error: any) {
      ElMessage.error(error.response?.data?.detail || '登录失败')
      return false
    }
  }
  
  // 登出
  const logout = async (): Promise<void> => {
    try {
      await authApi.logout()
    } catch (error) {
      console.error('登出请求失败:', error)
    } finally {
      // 清除本地数据
      token.value = ''
      user.value = null
      permissions.value = []
      removeToken()
      localStorage.removeItem('user_info')
      
      ElMessage.success('已退出登录')
    }
  }
  
  // 获取用户信息
  const getUserInfo = async (): Promise<void> => {
    try {
      const response = await authApi.getCurrentUser()
      user.value = response.data
      permissions.value = response.data.permissions || []
      
      // 更新本地存储
      localStorage.setItem('user_info', JSON.stringify(response.data))
    } catch (error) {
      console.error('获取用户信息失败:', error)
      // 如果获取用户信息失败，可能token已过期，执行登出
      await logout()
    }
  }
  
  // 刷新token
  const refreshToken = async (): Promise<boolean> => {
    try {
      const response = await authApi.refreshToken()
      const { access_token } = response.data
      
      token.value = access_token
      setToken(access_token)
      
      return true
    } catch (error) {
      console.error('刷新token失败:', error)
      await logout()
      return false
    }
  }
  
  // 修改密码
  const changePassword = async (oldPassword: string, newPassword: string): Promise<boolean> => {
    try {
      await authApi.changePassword({ old_password: oldPassword, new_password: newPassword })
      ElMessage.success('密码修改成功')
      return true
    } catch (error: any) {
      ElMessage.error(error.response?.data?.detail || '密码修改失败')
      return false
    }
  }
  
  // 从本地存储初始化用户状态
  const initUserFromStorage = (): void => {
    const storedToken = getToken()
    const storedUser = localStorage.getItem('user_info')
    
    if (storedToken && storedUser) {
      try {
        token.value = storedToken
        user.value = JSON.parse(storedUser)
        permissions.value = user.value?.permissions || []
        
        // 验证token是否仍然有效
        getUserInfo().catch(() => {
          // 如果验证失败，清除本地数据
          logout()
        })
      } catch (error) {
        console.error('解析本地用户信息失败:', error)
        logout()
      }
    }
  }
  
  // 检查权限
  const hasPermission = (permission: string): boolean => {
    if (!user.value) return false
    if (user.value.role === 'admin') return true
    return permissions.value.includes(permission)
  }
  
  // 检查角色
  const hasRole = (role: string): boolean => {
    return user.value?.role === role
  }
  
  return {
    // 状态
    user: readonly(user),
    token: readonly(token),
    permissions: readonly(permissions),
    
    // 计算属性
    isLoggedIn,
    userInfo,
    userPermissions,
    
    // 方法
    login,
    logout,
    getUserInfo,
    refreshToken,
    changePassword,
    initUserFromStorage,
    hasPermission,
    hasRole
  }
})