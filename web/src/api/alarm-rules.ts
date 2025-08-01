import request from '@/utils/request'

// 告警规则接口定义
export interface AlarmRule {
  id: number
  name: string
  description?: string
  diagnosis_types: string[]
  camera_ids: number[]
  camera_groups: string[]
  severity_levels: string[]
  threshold_config: Record<string, any>
  frequency_limit: number
  notification_channels: number[]
  notification_template?: string
  is_enabled: boolean
  priority: number
  trigger_count: number
  last_triggered_at?: string
  created_at: string
  updated_at: string
  created_by?: string
}

export interface AlarmRuleCreate {
  name: string
  description?: string
  diagnosis_types: string[]
  camera_ids: number[]
  camera_groups: string[]
  severity_levels: string[]
  threshold_config: Record<string, any>
  frequency_limit: number
  notification_channels: number[]
  notification_template?: string
  is_enabled: boolean
  priority: number
}

export interface AlarmRuleUpdate {
  name?: string
  description?: string
  diagnosis_types?: string[]
  camera_ids?: number[]
  camera_groups?: string[]
  severity_levels?: string[]
  threshold_config?: Record<string, any>
  frequency_limit?: number
  notification_channels?: number[]
  notification_template?: string
  is_enabled?: boolean
  priority?: number
}

export interface AlarmRuleQuery {
  page?: number
  page_size?: number
  is_enabled?: boolean
  diagnosis_type?: string
}

export interface AlarmRuleResponse {
  data: AlarmRule[]
  total: number
  page: number
  page_size: number
}

// API 调用函数
export const alarmRulesApi = {
  // 获取告警规则列表
  getAlarmRules: async (params?: AlarmRuleQuery): Promise<AlarmRuleResponse> => {
    const response = await request.get('/v1/alarm-rules/', { params })
    return response.data
  },

  // 获取告警规则详情
  getAlarmRule: async (id: number): Promise<AlarmRule> => {
    const response = await request.get(`/v1/alarm-rules/${id}`)
    return response.data
  },

  // 创建告警规则
  createAlarmRule: async (data: AlarmRuleCreate): Promise<AlarmRule> => {
    const response = await request.post('/v1/alarm-rules/', data)
    return response.data
  },

  // 更新告警规则
  updateAlarmRule: async (id: number, data: AlarmRuleUpdate): Promise<AlarmRule> => {
    const response = await request.put(`/v1/alarm-rules/${id}`, data)
    return response.data
  },

  // 删除告警规则
  deleteAlarmRule: async (id: number): Promise<void> => {
    await request.delete(`/v1/alarm-rules/${id}`)
  },

  // 启用/禁用告警规则
  toggleAlarmRule: async (id: number, is_enabled: boolean): Promise<AlarmRule> => {
    const response = await request.put(`/v1/alarm-rules/${id}`, { is_enabled })
    return response.data
  },

  // 测试告警规则
  testAlarmRule: async (id: number): Promise<{ success: boolean; message: string }> => {
    const response = await request.post(`/v1/alarm-rules/${id}/test`)
    return response.data
  }
}

export default alarmRulesApi