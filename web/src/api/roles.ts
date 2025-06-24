import request from '@/utils/request'
import type { ApiResponse } from '@/types/api'

// 角色相关类型定义
export interface Role {
  id: number
  name: string
  display_name: string
  description?: string
  permissions: string[]
  page_permissions: Record<string, any>
  is_active: boolean
  is_system: boolean
  created_at: string
  updated_at: string
  user_count?: number
}

export interface RoleCreate {
  name: string
  display_name: string
  description?: string
  permissions: string[]
  page_permissions: Record<string, any>
}

export interface RoleUpdate {
  display_name?: string
  description?: string
  permissions?: string[]
  page_permissions?: Record<string, any>
  is_active?: boolean
}

export interface Permission {
  id: number
  name: string
  display_name: string
  description?: string
  category?: string
  module?: string
  permission_type: string
  is_active: boolean
  is_system: boolean
  created_at: string
  updated_at: string
}

export interface PermissionCreate {
  name: string
  display_name: string
  description?: string
  category?: string
  module?: string
  permission_type: string
}

export interface UserRoleAssign {
  user_id: number
  role_ids: number[]
  expires_at?: string
}

export interface RoleListQuery {
  page?: number
  page_size?: number
  search?: string
  is_active?: boolean
}

export interface PermissionQuery {
  category?: string
  module?: string
  permission_type?: string
  is_active?: boolean
}

class RolesApi {
  // 获取角色列表
  getRoleList(params?: RoleListQuery) {
    return request.get<ApiResponse<{
      data: Role[]
      total: number
      page: number
      page_size: number
      pages: number
    }>>('/api/v1/roles/', { params })
  }

  // 创建角色
  createRole(data: RoleCreate) {
    return request.post<ApiResponse<Role>>('/api/v1/roles/', data)
  }

  // 获取角色详情
  getRole(id: number) {
    return request.get<ApiResponse<Role>>(`/api/v1/roles/${id}`)
  }

  // 更新角色
  updateRole(id: number, data: RoleUpdate) {
    return request.put<ApiResponse<Role>>(`/api/v1/roles/${id}`, data)
  }

  // 删除角色
  deleteRole(id: number) {
    return request.delete<ApiResponse<any>>(`/api/v1/roles/${id}`)
  }

  // 获取权限列表
  getPermissions(params?: PermissionQuery) {
    return request.get<ApiResponse<Permission[]>>('/api/v1/roles/permissions/', { params })
  }

  // 创建权限
  createPermission(data: PermissionCreate) {
    return request.post<ApiResponse<Permission>>('/api/v1/roles/permissions/', data)
  }

  // 分配用户角色
  assignUserRoles(data: UserRoleAssign) {
    return request.post<ApiResponse<any>>('/api/v1/roles/assign', data)
  }

  // 获取用户角色
  getUserRoles(userId: number) {
    return request.get<ApiResponse<Role[]>>(`/api/v1/roles/user/${userId}/roles`)
  }

  // 批量删除角色
  batchDeleteRoles(roleIds: number[]) {
    return request.delete<ApiResponse<any>>('/api/v1/roles/batch', {
      data: { role_ids: roleIds }
    })
  }

  // 批量更新角色状态
  batchUpdateRoleStatus(roleIds: number[], isActive: boolean) {
    return request.put<ApiResponse<any>>('/api/v1/roles/batch/status', {
      role_ids: roleIds,
      is_active: isActive
    })
  }
}

export const rolesApi = new RolesApi()
export default rolesApi