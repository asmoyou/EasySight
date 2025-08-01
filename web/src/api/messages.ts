import request from '@/utils/request'
import type { ApiResponse } from '@/types/api'

// 消息相关类型定义
export interface Message {
  id: number
  title: string
  content: string
  message_type: 'info' | 'warning' | 'error' | 'success'
  sender_id?: number
  receiver_id: number
  is_read: boolean
  read_at?: string
  category: string
  extra_data?: any
  created_at: string
  updated_at: string
  sender_name?: string
}

export interface MessageListResponse {
  messages: Message[]
  total: number
  unread_count: number
}

export interface MessageCreate {
  title: string
  content: string
  message_type?: 'info' | 'warning' | 'error' | 'success'
  receiver_id: number
  category?: string
  extra_data?: any
}

export interface MessageListParams {
  page?: number
  page_size?: number
  category?: string
  is_read?: boolean
  message_type?: string
}

export interface MarkReadRequest {
  message_ids: number[]
}

// 消息API
export const messagesApi = {
  // 获取消息列表
  getMessages(params: MessageListParams = {}) {
    return request.get<ApiResponse<MessageListResponse>>('/v1/messages/', { params })
  },

  // 获取未读消息数量
  getUnreadCount() {
    return request.get<ApiResponse<{ unread_count: number }>>('/v1/messages/unread-count')
  },

  // 创建消息
  createMessage(data: MessageCreate) {
    return request.post<ApiResponse<Message>>('/v1/messages/', data)
  },

  // 标记消息为已读
  markMessagesRead(data: MarkReadRequest) {
    return request.put<ApiResponse<{ message: string }>>('/v1/messages/mark-read', data)
  },

  // 标记所有消息为已读
  markAllMessagesRead() {
    return request.put<ApiResponse<{ message: string }>>('/v1/messages/mark-all-read')
  },

  // 获取单条消息详情
  getMessage(id: number) {
    return request.get<ApiResponse<Message>>(`/v1/messages/${id}`)
  },

  // 删除消息
  deleteMessage(id: number) {
    return request.delete<ApiResponse<{ message: string }>>(`/v1/messages/${id}`)
  }
}

export default messagesApi