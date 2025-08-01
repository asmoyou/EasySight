import request from '@/utils/request'
import type { LoginForm, LoginResponse, User, ChangePasswordForm, UserUpdateForm } from '@/types/user'
import type { ApiResponse } from '@/types/api'

export const authApi = {
  // 用户登录
  login(data: LoginForm) {
    return request.post<ApiResponse<LoginResponse>>('/v1/auth/login', data)
  },

  // 用户登出
  logout() {
    return request.post<ApiResponse<null>>('/v1/auth/logout')
  },

  // 刷新token
  refreshToken(refreshToken: string) {
    return request.post<ApiResponse<{ access_token: string }>>('/v1/auth/refresh', {
      refresh_token: refreshToken
    })
  },

  // 获取当前用户信息
  getCurrentUser() {
    return request.get<ApiResponse<User>>('/v1/auth/me')
  },

  // 修改密码
  changePassword(data: ChangePasswordForm) {
    return request.post<ApiResponse<{ message: string }>>('/v1/auth/change-password', data)
  },

  // 更新当前用户信息
  updateProfile(data: UserUpdateForm) {
    return request.put<ApiResponse<User>>('/v1/auth/me', data)
  },

  // 验证token
  verifyToken() {
    return request.get<ApiResponse<{ valid: boolean }>>('/v1/auth/verify')
  },

  // 上传头像
  uploadAvatar(file: File) {
    const formData = new FormData()
    formData.append('file', file)
    return request.post<ApiResponse<{ message: string; avatar_url: string }>>('/v1/files/upload/avatar', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },

  // 删除头像
  deleteAvatar() {
    return request.delete<ApiResponse<{ message: string }>>('/v1/files/avatar')
  }
}