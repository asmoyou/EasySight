// 用户相关类型定义

export interface User {
  id: number
  username: string
  email: string
  full_name: string
  role: 'admin' | 'operator' | 'viewer'
  roles: string[]
  is_active: boolean
  avatar?: string
  phone?: string
  department?: string
  permissions: string[]
  page_permissions: Record<string, boolean>
  last_login?: string
  created_at: string
  updated_at: string
}

export interface LoginForm {
  username: string
  password: string
  remember_me?: boolean
}

export interface LoginResponse {
  access_token: string
  token_type: string
  expires_in: number
  user: User
}

export interface ChangePasswordForm {
  old_password: string
  new_password: string
}

export interface UserCreateForm {
  username: string
  email: string
  full_name: string
  password: string
  role: 'admin' | 'operator' | 'viewer'
  phone?: string
  department?: string
  is_active?: boolean
}

export interface UserUpdateForm {
  email?: string
  full_name?: string
  role?: 'admin' | 'operator' | 'viewer'
  phone?: string
  department?: string
  is_active?: boolean
}

export interface UserSession {
  id: number
  user_id: number
  session_token: string
  ip_address: string
  user_agent: string
  is_active: boolean
  created_at: string
  last_activity: string
}

export interface UserLoginLog {
  id: number
  user_id: number
  username: string
  ip_address: string
  user_agent: string
  login_time: string
  logout_time?: string
  is_success: boolean
  failure_reason?: string
}

export interface UserStats {
  total_users: number
  active_users: number
  online_users: number
  admin_users: number
  operator_users: number
  viewer_users: number
  recent_logins: number
  by_role: Record<string, number>
  by_department: Record<string, number>
  login_trend: Array<{
    date: string
    count: number
  }>
}