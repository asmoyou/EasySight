import request from '@/utils/request'
import type { ApiResponse } from '@/types/api'

// 系统统计信息接口
export interface SystemStats {
  total_configs: number
  active_policies: number
  active_message_centers: number
  system_logs_today: number
  error_logs_today: number
  warning_logs_today: number
  current_version: string
  license_status: string
  license_expires_in_days: number | null
  disk_usage: {
    total: number
    used: number
    free: number
    percent: number
  }
  memory_usage: {
    total: number
    used: number
    available: number
    percent: number
  }
  cpu_usage: number
}

// 系统指标接口
export interface SystemMetric {
  id: number
  metric_name: string
  metric_value: number
  metric_unit: string | null
  dimensions: Record<string, any>
  timestamp: string
  created_at: string
}

// 系统指标查询参数
export interface SystemMetricsQuery {
  metric_name?: string
  start_time?: string
  end_time?: string
  limit?: number
}

// 系统配置接口
export interface SystemConfig {
  id: number
  key: string
  value: string
  value_type: string
  category: string
  description: string | null
  is_public: boolean
  is_editable: boolean
  requires_restart: boolean
  created_at: string
  updated_at: string
  updated_by: string | null
}

// 系统配置创建表单
export interface SystemConfigCreate {
  key: string
  value: string
  category: string
  description?: string
  is_public?: boolean
  value_type?: string
  is_editable?: boolean
  requires_restart?: boolean
}

// 系统配置更新表单
export interface SystemConfigUpdate {
  value?: string
  description?: string
  is_public?: boolean
  is_editable?: boolean
  requires_restart?: boolean
}

// 系统日志接口
export interface SystemLog {
  id: number
  level: string
  module: string
  action: string
  message: string
  user_id: number | null
  user_name: string | null
  ip_address: string | null
  user_agent: string | null
  request_id: string | null
  extra_data: Record<string, any>
  created_at: string
}

// 系统日志查询参数
export interface SystemLogsQuery {
  level?: string
  module?: string
  user_id?: number
  start_time?: string
  end_time?: string
  search?: string
  page?: number
  page_size?: number
}

// 许可证信息接口
export interface License {
  id: number
  license_key: string
  product_name: string
  license_type: string
  max_users: number | null
  max_cameras: number | null
  features: string[]
  issued_to: string
  issued_by: string
  issued_at: string
  expires_at: string | null
  is_active: boolean
  hardware_fingerprint: string | null
  created_at: string
  updated_at: string
}

// 系统API类
class SystemApi {
  // 获取系统统计信息
  getSystemStats() {
    return request.get<ApiResponse<SystemStats>>('/v1/system/stats/overview')
  }

  // 获取系统指标数据
  getSystemMetrics(params?: SystemMetricsQuery) {
    return request.get<ApiResponse<SystemMetric[]>>('/v1/system/metrics/', { params })
  }

  // 获取系统配置列表
  getSystemConfigs(params?: {
    category?: string
    search?: string
    is_public?: boolean
  }) {
    return request.get<ApiResponse<SystemConfig[]>>('/v1/system/configs/', { params })
  }

  // 获取单个系统配置
  getSystemConfig(id: number) {
    return request.get<ApiResponse<SystemConfig>>(`/v1/system/configs/${id}`)
  }

  // 创建系统配置
  createSystemConfig(data: SystemConfigCreate) {
    return request.post<ApiResponse<SystemConfig>>('/v1/system/configs/', data)
  }

  // 更新系统配置
  updateSystemConfig(id: number, data: SystemConfigUpdate) {
    return request.put<ApiResponse<SystemConfig>>(`/v1/system/configs/${id}`, data)
  }

  // 删除系统配置
  deleteSystemConfig(id: number) {
    return request.delete<ApiResponse<null>>(`/v1/system/configs/${id}`)
  }

  // 获取系统日志列表
  getSystemLogs(params?: SystemLogsQuery) {
    return request.get<ApiResponse<{
      items: SystemLog[]
      total: number
      page: number
      page_size: number
      pages: number
    }>>('/v1/system/logs/', { params })
  }

  // 获取许可证信息
  getLicenseInfo() {
    return request.get<ApiResponse<License>>('/v1/system/license/')
  }

  // 验证许可证
  validateLicense(licenseKey: string) {
    return request.post<ApiResponse<License>>('/v1/system/license/validate', {
      license_key: licenseKey
    })
  }

  // 激活许可证
  activateLicense(licenseKey: string) {
    return request.post<ApiResponse<License>>('/v1/system/license/activate', {
      license_key: licenseKey
    })
  }

  // 停用许可证
  deactivateLicense() {
    return request.post<ApiResponse<null>>('/v1/system/license/deactivate')
  }
}

// 导出系统API实例
export const systemApi = new SystemApi()

// 默认导出
export default systemApi