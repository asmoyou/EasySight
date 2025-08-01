import request from '@/utils/request'

// 通知渠道接口定义
export interface NotificationChannel {
  id: number
  name: string
  type: string
  description?: string
  config: Record<string, any>
  is_enabled: boolean
  send_count: number
  success_count: number
  last_used_at?: string
  created_at: string
  updated_at: string
  created_by?: string
  stats?: {
    sent_today: number
    success_rate: number
  }
}

export interface NotificationChannelCreate {
  name: string
  type: string
  description?: string
  config: Record<string, any>
  is_enabled: boolean
}

export interface NotificationChannelUpdate {
  name?: string
  description?: string
  config?: Record<string, any>
  is_enabled?: boolean
}

export interface NotificationChannelQuery {
  page?: number
  page_size?: number
  type?: string
  is_enabled?: boolean
}

export interface NotificationChannelResponse {
  data: NotificationChannel[]
  total: number
  page: number
  page_size: number
}

export interface TestNotificationRequest {
  title: string
  content: string
  recipients?: string[]
}

// API 调用函数
export const notificationChannelsApi = {
  // 获取通知渠道列表
  getNotificationChannels: async (params?: NotificationChannelQuery): Promise<NotificationChannelResponse> => {
    const response = await request.get('/v1/notification-channels/', { params })
    return response.data
  },

  // 获取通知渠道详情
  getNotificationChannel: async (id: number): Promise<NotificationChannel> => {
    const response = await request.get(`/v1/notification-channels/${id}`)
    return response.data
  },

  // 创建通知渠道
  createNotificationChannel: async (data: NotificationChannelCreate): Promise<NotificationChannel> => {
    const response = await request.post('/v1/notification-channels/', data)
    return response.data
  },

  // 更新通知渠道
  updateNotificationChannel: async (id: number, data: NotificationChannelUpdate): Promise<NotificationChannel> => {
    const response = await request.put(`/v1/notification-channels/${id}`, data)
    return response.data
  },

  // 删除通知渠道
  deleteNotificationChannel: async (id: number): Promise<void> => {
    await request.delete(`/v1/notification-channels/${id}`)
  },

  // 启用/禁用通知渠道
  toggleNotificationChannel: async (id: number, is_enabled: boolean): Promise<NotificationChannel> => {
    const response = await request.put(`/v1/notification-channels/${id}`, { is_enabled })
    return response.data
  },

  // 测试通知渠道
  testNotificationChannel: async (id: number, data: TestNotificationRequest): Promise<{ success: boolean; message: string }> => {
    const response = await request.post(`/v1/notification-channels/${id}/test`, data)
    return response.data
  },

  // 获取通知统计
  getNotificationStats: async (): Promise<{
    enabled_count: number
    sent_today: number
    success_rate: number
    total_count: number
  }> => {
    const response = await request.get('/v1/notification-channels/stats')
    return response.data
  }
}

export default notificationChannelsApi