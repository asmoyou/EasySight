// 摄像头状态枚举
export enum CameraStatus {
  ONLINE = 'online',
  OFFLINE = 'offline',
  ERROR = 'error',
  MAINTENANCE = 'maintenance'
}

// 摄像头类型枚举
export enum CameraType {
  IP_CAMERA = 'ip_camera',
  ANALOG_CAMERA = 'analog_camera',
  USB_CAMERA = 'usb_camera',
  WIRELESS_CAMERA = 'wireless_camera'
}

// 摄像头基础信息
export interface Camera {
  id: number
  code: string
  name: string
  stream_url: string
  backup_stream_url?: string
  camera_type: CameraType
  media_proxy_id?: number
  media_proxy_name?: string
  location?: string
  longitude?: number
  latitude?: number
  altitude?: number
  manufacturer?: string
  model?: string
  firmware_version?: string
  ip_address?: string
  port?: number
  resolution?: string
  frame_rate?: number
  bitrate?: number
  status: CameraStatus
  is_active: boolean
  is_recording: boolean
  custom_attributes?: Record<string, any>
  alarm_enabled: boolean
  alarm_config?: Record<string, any>
  last_heartbeat?: string
  created_at: string
  updated_at: string
  description?: string
}

// 摄像头创建表单
export interface CameraCreateForm {
  code: string
  name: string
  stream_url: string
  backup_stream_url?: string
  camera_type: CameraType
  media_proxy_id?: number
  location?: string
  longitude?: number
  latitude?: number
  altitude?: number
  manufacturer?: string
  model?: string
  firmware_version?: string
  ip_address?: string
  port?: number
  resolution?: string
  frame_rate?: number
  bitrate?: number
  is_active?: boolean
  is_recording?: boolean
  custom_attributes?: Record<string, any>
  alarm_enabled?: boolean
  alarm_config?: Record<string, any>
  description?: string
}

// 摄像头更新表单
export interface CameraUpdateForm {
  name?: string
  stream_url?: string
  backup_stream_url?: string
  camera_type?: CameraType
  media_proxy_id?: number
  location?: string
  longitude?: number
  latitude?: number
  altitude?: number
  manufacturer?: string
  model?: string
  firmware_version?: string
  ip_address?: string
  port?: number
  resolution?: string
  frame_rate?: number
  bitrate?: number
  status?: CameraStatus
  is_active?: boolean
  is_recording?: boolean
  custom_attributes?: Record<string, any>
  alarm_enabled?: boolean
  alarm_config?: Record<string, any>
  description?: string
}

// 摄像头列表响应
export interface CameraListResponse {
  cameras: Camera[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

// 摄像头查询参数
export interface CameraQueryParams {
  page?: number
  page_size?: number
  search?: string
  camera_type?: CameraType
  is_active?: boolean
  location?: string
}

// 摄像头统计信息
export interface CameraStats {
  total_cameras: number
  online_cameras: number
  offline_cameras: number
  recording_cameras: number
  alarm_enabled_cameras: number
  by_type: Record<string, number>
  by_status: Record<string, number>
}

// 媒体代理
export interface MediaProxy {
  id: number
  name: string
  ip_address: string
  port: number
  is_online: boolean
  cpu_usage?: number
  memory_usage?: number
  bandwidth_usage?: number
  max_connections?: number
  current_connections?: number
  last_heartbeat?: string
  created_at: string
  updated_at: string
  description?: string
}

// 媒体代理创建表单
export interface MediaProxyCreateForm {
  name: string
  ip_address: string
  port: number
  max_connections?: number
  description?: string
}

// 媒体代理更新表单
export interface MediaProxyUpdateForm {
  name?: string
  ip_address?: string
  port?: number
  is_online?: boolean
  max_connections?: number
  description?: string
}

// 摄像头分组
export interface CameraGroup {
  id: number
  name: string
  description?: string
  camera_ids: number[]
  camera_count: number
  created_at: string
  updated_at: string
}

// 摄像头分组创建表单
export interface CameraGroupCreateForm {
  name: string
  description?: string
  camera_ids?: number[]
}

// 摄像头分组更新表单
export interface CameraGroupUpdateForm {
  name?: string
  description?: string
  camera_ids?: number[]
}