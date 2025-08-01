import request from '@/utils/request'

// 仪表盘统计数据接口
export interface DashboardStats {
  total_cameras: number
  online_cameras: number
  offline_cameras: number
  total_events: number
  today_events: number
  unhandled_events: number
  running_tasks: number
  completed_tasks_today: number
  failed_tasks_today: number
  total_algorithms: number
  active_algorithms: number
  system_health: {
    cpu_percent: number
    memory_percent: number
    disk_percent: number
    network_sent: number
    network_recv: number
    status: string
  }
}

// 事件趋势数据接口
export interface EventTrendData {
  date: string
  event_count: number
  handled_count: number
}

// 摄像头状态分布接口
export interface CameraStatusData {
  status: string
  count: number
  percentage: number
}

// 最近事件接口
export interface RecentEvent {
  id: number
  title: string
  camera_name: string
  level: string
  status: string
  created_at: string
}

// 仪表盘响应数据接口
export interface DashboardResponse {
  stats: DashboardStats
  event_trend: EventTrendData[]
  camera_status: CameraStatusData[]
  recent_events: RecentEvent[]
  last_updated: string
}

// 获取仪表盘概览数据
export function getDashboardOverview(days: number = 7) {
  return request.get<DashboardResponse>('/v1/dashboard/overview', {
    params: { days }
  })
}

// 获取系统健康状态
export function getSystemHealth() {
  return request.get('/v1/dashboard/system-health')
}