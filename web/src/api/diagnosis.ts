import request from '@/utils/request'
import type { ApiResponse } from '@/types/api'

// 诊断类型枚举
export enum DiagnosisType {
  BRIGHTNESS = 'brightness',
  BLUE_SCREEN = 'blue_screen',
  CLARITY = 'clarity',
  SHAKE = 'shake',
  FREEZE = 'freeze',
  COLOR_CAST = 'color_cast',
  OCCLUSION = 'occlusion',
  NOISE = 'noise',
  CONTRAST = 'contrast',
  MOSAIC = 'mosaic',
  FLOWER_SCREEN = 'flower_screen',
  SIGNAL_LOSS = 'signal_loss',
  LENS_DIRTY = 'lens_dirty',
  FOCUS_BLUR = 'focus_blur'
}

// 诊断状态枚举
export enum DiagnosisStatus {
  NORMAL = 'normal',
  WARNING = 'warning',
  ERROR = 'error',
  CRITICAL = 'critical'
}

// 任务状态枚举
export enum TaskStatus {
  PENDING = 'pending',
  RUNNING = 'running',
  COMPLETED = 'completed',
  FAILED = 'failed',
  CANCELLED = 'cancelled'
}

// 诊断任务接口
export interface DiagnosisTask {
  id: number
  name: string
  diagnosis_type: DiagnosisType
  target_id: number
  target_type: string
  template_id?: number
  template_name?: string
  config: Record<string, any>
  schedule_config: Record<string, any>
  status: TaskStatus
  is_scheduled: boolean
  is_active: boolean
  last_run?: string
  next_run?: string
  run_count: number
  success_count: number
  error_count: number
  created_by: number
  created_by_name: string
  created_at: string
  updated_at: string
  description?: string
}

export interface DiagnosisTaskCreate {
  name: string
  diagnosis_type: DiagnosisType
  target_id: number
  target_type: string
  template_id?: number
  config?: Record<string, any>
  schedule_config?: Record<string, any>
  is_scheduled?: boolean
  description?: string
}

export interface DiagnosisTaskUpdate {
  name?: string
  config?: Record<string, any>
  schedule_config?: Record<string, any>
  is_scheduled?: boolean
  is_active?: boolean
  description?: string
}

// 诊断结果接口
export interface DiagnosisResult {
  id: number
  task_id: number
  task_name: string
  status: DiagnosisStatus
  result_data: Record<string, any>
  score?: number
  issues_found: Array<Record<string, any>>
  recommendations: string[]
  execution_time?: number
  error_message?: string
  created_at: string
}

// 诊断告警接口
export interface DiagnosisAlarm {
  id: number
  result_id: number
  task_name: string
  alarm_type: string
  severity: string
  title: string
  description: string
  threshold_config: Record<string, any>
  current_value?: number
  threshold_value?: number
  is_acknowledged: boolean
  acknowledged_by?: number
  acknowledged_by_name?: string
  acknowledged_at?: string
  created_at: string
}

// 诊断模板接口
export interface DiagnosisTemplate {
  id: number
  name: string
  diagnosis_type: DiagnosisType
  config_template: Record<string, any>
  default_schedule: Record<string, any>
  threshold_config: Record<string, any>
  is_active: boolean
  is_public: boolean
  usage_count: number
  created_by: number
  created_by_name: string
  created_at: string
  updated_at: string
  description?: string
}

export interface DiagnosisTemplateCreate {
  name: string
  diagnosis_type: DiagnosisType
  config_template: Record<string, any>
  default_schedule?: Record<string, any>
  threshold_config?: Record<string, any>
  description?: string
  is_public?: boolean
}

// 诊断统计接口
export interface DiagnosisStats {
  total_tasks: number
  active_tasks: number
  running_tasks: number
  scheduled_tasks: number
  total_results: number
  success_results: number
  failed_results: number
  warning_results: number
  total_alarms: number
  unacknowledged_alarms: number
  critical_alarms: number
  avg_score: number
  by_type: Record<string, number>
  by_status: Record<string, number>
  trend_data: Array<Record<string, any>>
}

// 诊断任务API
export const diagnosisTaskApi = {
  // 获取任务列表
  getTasks: (params?: {
    page?: number
    page_size?: number
    search?: string
    diagnosis_type?: DiagnosisType
    status?: TaskStatus
    is_active?: boolean
    is_scheduled?: boolean
    target_type?: string
  }): Promise<ApiResponse<DiagnosisTask[]>> => {
    return request.get('/api/v1/diagnosis/tasks/', { params })
  },

  // 获取任务详情
  getTask: (id: number): Promise<ApiResponse<DiagnosisTask>> => {
    return request.get(`/api/v1/diagnosis/tasks/${id}`)
  },

  // 创建任务
  createTask: (data: DiagnosisTaskCreate): Promise<ApiResponse<DiagnosisTask>> => {
    return request.post('/api/v1/diagnosis/tasks/', data)
  },

  // 更新任务
  updateTask: (id: number, data: DiagnosisTaskUpdate): Promise<ApiResponse<DiagnosisTask>> => {
    return request.put(`/api/v1/diagnosis/tasks/${id}`, data)
  },

  // 删除任务
  deleteTask: (id: number): Promise<ApiResponse<void>> => {
    return request.delete(`/api/v1/diagnosis/tasks/${id}`)
  },

  // 执行任务
  runTask: (id: number): Promise<ApiResponse<void>> => {
    return request.post(`/api/v1/diagnosis/tasks/${id}/run`)
  },

  // 启用/禁用任务
  toggleTask: (id: number, is_active: boolean): Promise<ApiResponse<DiagnosisTask>> => {
    return request.put(`/api/v1/diagnosis/tasks/${id}`, { is_active })
  }
}

// 诊断结果API
export const diagnosisResultApi = {
  // 获取结果列表
  getResults: (params?: {
    page?: number
    page_size?: number
    task_id?: number
    status?: DiagnosisStatus
    start_date?: string
    end_date?: string
  }): Promise<ApiResponse<DiagnosisResult[]>> => {
    return request.get('/api/v1/diagnosis/results/', { params })
  },

  // 获取结果详情
  getResult: (id: number): Promise<ApiResponse<DiagnosisResult>> => {
    return request.get(`/api/v1/diagnosis/results/${id}`)
  }
}

// 诊断告警API
export const diagnosisAlarmApi = {
  // 获取告警列表
  getAlarms: (params?: {
    page?: number
    page_size?: number
    alarm_type?: string
    severity?: string
    is_acknowledged?: boolean
    start_date?: string
    end_date?: string
  }): Promise<ApiResponse<DiagnosisAlarm[]>> => {
    return request.get('/api/v1/diagnosis/alarms/', { params })
  },

  // 确认告警
  acknowledgeAlarm: (id: number): Promise<ApiResponse<void>> => {
    return request.post(`/api/v1/diagnosis/alarms/${id}/acknowledge`)
  },

  // 批量确认告警
  batchAcknowledge: (ids: number[]): Promise<ApiResponse<void>> => {
    return request.post('/api/v1/diagnosis/alarms/batch-acknowledge', { alarm_ids: ids })
  }
}

// 诊断模板API
export const diagnosisTemplateApi = {
  // 获取模板列表
  getTemplates: (params?: {
    page?: number
    page_size?: number
    search?: string
    diagnosis_type?: DiagnosisType
    is_active?: boolean
    is_public?: boolean
  }): Promise<ApiResponse<DiagnosisTemplate[]>> => {
    return request.get('/api/v1/diagnosis/templates/', { params })
  },

  // 获取模板详情
  getTemplate: (id: number): Promise<ApiResponse<DiagnosisTemplate>> => {
    return request.get(`/api/v1/diagnosis/templates/${id}`)
  },

  // 创建模板
  createTemplate: (data: DiagnosisTemplateCreate): Promise<ApiResponse<DiagnosisTemplate>> => {
    return request.post('/api/v1/diagnosis/templates/', data)
  },

  // 更新模板
  updateTemplate: (id: number, data: Partial<DiagnosisTemplateCreate>): Promise<ApiResponse<DiagnosisTemplate>> => {
    return request.put(`/api/v1/diagnosis/templates/${id}`, data)
  },

  // 删除模板
  deleteTemplate: (id: number): Promise<ApiResponse<void>> => {
    return request.delete(`/api/v1/diagnosis/templates/${id}`)
  }
}

// 诊断统计API
export const diagnosisStatsApi = {
  // 获取统计概览
  getOverview: (days?: number): Promise<ApiResponse<DiagnosisStats>> => {
    return request.get('/api/v1/diagnosis/stats/overview', { params: { days } })
  }
}