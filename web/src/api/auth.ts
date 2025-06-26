import request from '@/utils/request'
import type { LoginForm, LoginResponse, User, ChangePasswordForm } from '@/types/user'
import type { ApiResponse } from '@/types/api'

export const authApi = {
  // 用户登录
  login(data: LoginForm) {
    return request.post<ApiResponse<LoginResponse>>('/api/v1/auth/login', data)
  },

  // 用户登出
  logout() {
    return request.post<ApiResponse<null>>('/api/v1/auth/logout')
  },

  // 刷新token
  refreshToken() {
    return request.post<ApiResponse<{ access_token: string }>>('/api/v1/auth/refresh')
  },

  // 获取当前用户信息
  getCurrentUser() {
    return request.get<ApiResponse<User>>('/api/v1/auth/me')
  },

  // 修改密码
  changePassword(data: ChangePasswordForm) {
    return request.post<ApiResponse<{ message: string }>>('/api/v1/auth/change-password', data)
  },

  // 更新当前用户信息
  updateProfile(data: UserUpdateForm) {
    return request.put<ApiResponse<User>>('/api/v1/auth/me', data)
  },

  // 验证token
  verifyToken() {
    return request.get<ApiResponse<{ valid: boolean }>>('/api/v1/auth/verify')
  },

  // 上传头像
  uploadAvatar(file: File) {
    const formData = new FormData()
    formData.append('file', file)
    return request.post<ApiResponse<{ message: string; avatar_url: string }>>('/api/v1/files/upload/avatar', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },

  // 删除头像
  deleteAvatar() {
    return request.delete<ApiResponse<{ message: string }>>('/api/v1/files/avatar')
  }
}