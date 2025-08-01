import request from '@/utils/request'

// 事件相关的API接口
export interface Event {
  id: string
  event_type: string
  event_level: string
  title: string
  description: string
  camera_id: string
  camera_name: string
  algorithm_name: string
  confidence: number
  latitude?: number
  longitude?: number
  image_urls: string[]
  video_urls: string[]
  thumbnail_url: string
  detected_objects: string[]
  status: 'pending' | 'confirmed' | 'false_alarm' | 'ignored'
  is_read: boolean
  event_time: string
  end_time?: string
  duration?: number
  handled_by?: string
  handled_time?: string
  resolution_notes?: string
  is_ongoing: boolean
  created_at: string
  updated_at: string
}

export interface EventQuery {
  event_type?: string
  event_level?: string
  camera_id?: string
  camera_name?: string
  algorithm_name?: string
  is_read?: boolean
  is_ongoing?: boolean
  start_date?: string
  end_date?: string
  status?: string
  page?: number
  page_size?: number
}

export interface EventResponse {
  events: Event[]
  total: number
  page: number
  page_size: number
}

// 获取事件列表
export const getEvents = (params: EventQuery): Promise<EventResponse> => {
  return request.get('/v1/events', { params }).then(res => res.data)
}

// 获取事件详情
export const getEvent = (id: string): Promise<Event> => {
  return request.get(`/v1/events/${id}`).then(res => res.data)
}

// 确认报警
export const confirmEvent = (id: string, data: { resolution_notes?: string }): Promise<Event> => {
  return request.post(`/v1/events/${id}/confirm`, data).then(res => res.data)
}

// 标记误报
export const markFalseAlarm = (id: string, data: { resolution_notes?: string }): Promise<Event> => {
  return request.post(`/v1/events/${id}/false-alarm`, data).then(res => res.data)
}

// 标记已读
export const markAsRead = (id: string): Promise<Event> => {
  return request.post(`/v1/events/${id}/mark-read`).then(res => res.data)
}

// 更新事件
export const updateEvent = (id: string, data: Partial<Event>): Promise<Event> => {
  return request.put(`/v1/events/${id}`, data).then(res => res.data)
}

// 删除事件
export const deleteEvent = (id: string): Promise<void> => {
  return request.delete(`/v1/events/${id}`).then(res => res.data)
}