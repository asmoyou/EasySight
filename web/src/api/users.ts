import request from '@/utils/request'
import type { ApiResponse, PaginatedResponse } from '@/types/api'
import type { User, UserCreateForm, UserUpdateForm, UserStats } from '@/types/user'

export interface UserListParams {
  page?: number
  page_size?: number
  search?: string
  role?: string
  is_active?: boolean
}

export interface UserListResponse {
  users: User[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface PasswordResetForm {
  new_password: string
}

class UsersApi {
  // 获取用户列表
  getUserList(params: UserListParams = {}) {
    return request.get<ApiResponse<UserListResponse>>('/api/v1/users/', { params })
  }

  // 创建用户
  createUser(data: UserCreateForm) {
    return request.post<ApiResponse<User>>('/api/v1/users/', data)
  }

  // 获取用户详情
  getUserById(id: number) {
    return request.get<ApiResponse<User>>(`/api/v1/users/${id}`)
  }

  // 更新用户信息
  updateUser(id: number, data: UserUpdateForm) {
    return request.put<ApiResponse<User>>(`/api/v1/users/${id}`, data)
  }

  // 删除用户
  deleteUser(id: number) {
    return request.delete<ApiResponse<{ message: string }>>(`/api/v1/users/${id}`)
  }

  // 重置用户密码
  resetUserPassword(id: number, data: PasswordResetForm) {
    return request.post<ApiResponse<{ message: string }>>(`/api/v1/users/${id}/reset-password`, data)
  }

  // 获取用户统计信息
  getUserStats() {
    return request.get<ApiResponse<UserStats>>('/api/v1/users/stats/overview')
  }

  // 批量删除用户
  batchDeleteUsers(userIds: number[]) {
    return request.post<ApiResponse<{ message: string }>>('/api/v1/users/batch-delete/', { user_ids: userIds })
  }

  // 批量更新用户状态
  batchUpdateUserStatus(userIds: number[], isActive: boolean) {
    return request.post<ApiResponse<{ message: string }>>('/api/v1/users/batch-update-status/', {
      user_ids: userIds,
      is_active: isActive
    })
  }
}

export const usersApi = new UsersApi()
export default usersApi