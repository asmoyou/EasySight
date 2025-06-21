// API 相关类型定义

// 通用响应类型
export interface ApiResponse<T = any> {
  code: number
  message: string
  data: T
  success: boolean
}

// 分页响应类型
export interface PaginatedResponse<T = any> {
  items: T[]
  total: number
  page: number
  page_size: number
  pages: number
}

// 分页请求参数
export interface PaginationParams {
  page?: number
  page_size?: number
  search?: string
  sort_by?: string
  sort_order?: 'asc' | 'desc'
}

// 文件上传响应
export interface UploadResponse {
  url: string
  filename: string
  size: number
  content_type: string
}

// 错误响应
export interface ErrorResponse {
  detail: string
  code?: string
  field?: string
}

// WebSocket 消息类型
export interface WebSocketMessage {
  type: string
  data: any
  timestamp: string
}

// 统计数据类型
export interface StatsData {
  label: string
  value: number
  change?: number
  trend?: 'up' | 'down' | 'stable'
}

// 图表数据类型
export interface ChartData {
  labels: string[]
  datasets: Array<{
    label: string
    data: number[]
    backgroundColor?: string | string[]
    borderColor?: string
    borderWidth?: number
  }>
}

// 时间范围类型
export interface TimeRange {
  start_time: string
  end_time: string
}

// 导出参数
export interface ExportParams {
  format: 'csv' | 'excel' | 'pdf'
  fields?: string[]
  filters?: Record<string, any>
}

// 批量操作参数
export interface BatchOperation {
  action: string
  ids: number[]
  params?: Record<string, any>
}