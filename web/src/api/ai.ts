import request from '@/utils/request'
const { get, post, put, delete: del, patch, upload, download } = request
import type {
  AIAlgorithm,
  AIAlgorithmCreate,
  AIAlgorithmUpdate,
  AIAlgorithmQuery,
  AIService,
  AIServiceCreate,
  AIServiceUpdate,
  AIServiceQuery,
  AIModel,
  AIModelCreate,
  AIModelUpdate,
  AIModelQuery,
  AIServiceLog,
  AIServiceLogQuery,
  AIApiResponse,
  AIStatsResponse
} from '@/types/ai'

// AI算法相关API
export const aiApi = {
  // 获取算法列表
  getAlgorithms(params?: AIAlgorithmQuery): Promise<AIApiResponse<AIAlgorithm>> {
    return get('/v1/ai/algorithms/', { params }).then(response => response.data)
  },

  // 获取算法详情
  getAlgorithm(id: number): Promise<AIAlgorithm> {
    return get(`/v1/ai/algorithms/${id}`).then(response => response.data)
  },

  // 创建算法
  createAlgorithm(data: AIAlgorithmCreate): Promise<AIAlgorithm> {
    return post('/v1/ai/algorithms/', data).then(response => response.data)
  },

  // 更新算法
  updateAlgorithm(id: number, data: AIAlgorithmUpdate): Promise<AIAlgorithm> {
    return put(`/v1/ai/algorithms/${id}`, data).then(response => response.data)
  },

  // 删除算法
  deleteAlgorithm(id: number): Promise<void> {
    return del(`/v1/ai/algorithms/${id}`).then(response => response.data)
  },

  // 获取服务列表
  getServices(params?: AIServiceQuery): Promise<AIApiResponse<AIService>> {
    return get('/v1/ai/services/', { params }).then(response => response.data)
  },

  // 获取服务详情
  getService(id: number): Promise<AIService> {
    return get(`/v1/ai/services/${id}`).then(response => response.data)
  },

  // 创建服务
  createService(data: AIServiceCreate): Promise<AIService> {
    return post('/v1/ai/services/', data).then(response => response.data)
  },

  // 更新服务
  updateService(id: number, data: AIServiceUpdate): Promise<AIService> {
    return put(`/v1/ai/services/${id}`, data).then(response => response.data)
  },

  // 删除服务
  deleteService(id: number): Promise<void> {
    return del(`/v1/ai/services/${id}`).then(response => response.data)
  },

  // 启动服务
  startService(id: number): Promise<void> {
    return post(`/v1/ai/services/${id}/start`).then(response => response.data)
  },

  // 停止服务
  stopService(id: number): Promise<void> {
    return post(`/v1/ai/services/${id}/stop`).then(response => response.data)
  },

  // 重启服务
  restartService(id: number): Promise<void> {
    return post(`/v1/ai/services/${id}/restart`).then(response => response.data)
  },

  // 获取服务状态
  getServiceStatus(id: number): Promise<{ status: string; details?: any }> {
    return get(`/v1/ai/services/${id}/status`).then(response => response.data)
  },

  // 获取服务性能指标
  getServiceMetrics(id: number, params?: { start_time?: string; end_time?: string }): Promise<any> {
    return get(`/v1/ai/services/${id}/metrics`, { params }).then(response => response.data)
  },

  // 获取模型列表
  getModels(params?: AIModelQuery): Promise<AIApiResponse<AIModel>> {
    return get('/v1/ai/models/', { params }).then(response => response.data)
  },

  // 获取模型详情
  getModel(id: number): Promise<AIModel> {
    return get(`/v1/ai/models/${id}`).then(response => response.data)
  },

  // 创建模型
  createModel(data: AIModelCreate): Promise<AIModel> {
    return post('/v1/ai/models/', data).then(response => response.data)
  },

  // 更新模型
  updateModel(id: number, data: AIModelUpdate): Promise<AIModel> {
    return put(`/v1/ai/models/${id}`, data).then(response => response.data)
  },

  // 删除模型
  deleteModel(id: number): Promise<void> {
    return del(`/v1/ai/models/${id}`).then(response => response.data)
  },

  // 验证模型
  validateModel(id: number, data?: { test_data?: any }): Promise<any> {
    return post(`/v1/ai/models/${id}/validate`, data).then(response => response.data)
  },

  // 获取模型性能报告
  getModelPerformance(id: number): Promise<any> {
    return get(`/v1/ai/models/${id}/performance`).then(response => response.data)
  },

  // 获取服务日志
  getServiceLogs(params?: AIServiceLogQuery): Promise<AIApiResponse<AIServiceLog>> {
    return get('/v1/ai/logs/', { params }).then(response => response.data)
  },

  // 获取统计数据
  getStats(): Promise<AIStatsResponse> {
    return get('/v1/ai/stats/overview').then(response => response.data)
  },

  // 获取算法类型统计
  getAlgorithmTypeStats(): Promise<Record<string, number>> {
    return get('/v1/ai/stats/algorithm-types').then(response => response.data)
  },

  // 获取服务状态统计
  getServiceStatusStats(): Promise<Record<string, number>> {
    return get('/v1/ai/stats/service-status').then(response => response.data)
  },

  // 获取模型类型统计
  getModelTypeStats(): Promise<Record<string, number>> {
    return get('/v1/ai/stats/model-types').then(response => response.data)
  },

  // 获取性能趋势数据
  getPerformanceTrends(params?: { 
    start_time?: string
    end_time?: string
    service_id?: number
    metric?: string
  }): Promise<any> {
    return get('/v1/ai/stats/performance-trends', { params }).then(response => response.data)
  },

  // 文件上传相关
  uploadAlgorithmFile(file: File, onProgress?: (progress: number) => void): Promise<{ file_path: string; file_size: number }> {
    const formData = new FormData()
    formData.append('file', file)
    
    return upload('/v1/files/upload/algorithm-package', formData, {
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total)
          onProgress(progress)
        }
      }
    }).then(response => response.data)
  },

  uploadModelFile(file: File, onProgress?: (progress: number) => void): Promise<{ file_path: string; file_size: number }> {
    const formData = new FormData()
    formData.append('file', file)
    
    return upload('/v1/files/upload/model', formData, {
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total)
          onProgress(progress)
        }
      }
    }).then(response => response.data.data)
  },

  // 批量操作
  batchDeleteAlgorithms(ids: number[]): Promise<void> {
    return post('/v1/ai/algorithms/batch-delete', { ids }).then(response => response.data)
  },

  batchDeleteServices(ids: number[]): Promise<void> {
    return post('/v1/ai/services/batch-delete', { ids }).then(response => response.data)
  },

  batchDeleteModels(ids: number[]): Promise<void> {
    return post('/v1/ai/models/batch-delete', { ids }).then(response => response.data)
  },

  batchStartServices(ids: number[]): Promise<void> {
    return post('/v1/ai/services/batch-start', { ids }).then(response => response.data)
  },

  batchStopServices(ids: number[]): Promise<void> {
    return post('/v1/ai/services/batch-stop', { ids }).then(response => response.data)
  },

  // 配置相关
  getAlgorithmConfig(id: number): Promise<any> {
    return get(`/v1/ai/algorithms/${id}/config`).then(response => response.data)
  },

  updateAlgorithmConfig(id: number, config: any): Promise<void> {
    return put(`/v1/ai/algorithms/${id}/config`, config).then(response => response.data)
  },

  getServiceConfig(id: number): Promise<any> {
    return get(`/v1/ai/services/${id}/config`).then(response => response.data)
  },

  updateServiceConfig(id: number, config: any): Promise<void> {
    return put(`/v1/ai/services/${id}/config`, config).then(response => response.data)
  },

  // 健康检查
  healthCheck(): Promise<{ status: string; details: any }> {
    return get('/v1/ai/health').then(response => response.data)
  },

  // 系统信息
  getSystemInfo(): Promise<any> {
    return get('/v1/ai/system/info').then(response => response.data)
  },

  // 资源使用情况
  getResourceUsage(): Promise<any> {
    return get('/v1/ai/system/resources').then(response => response.data)
  },

  // 清理缓存
  clearCache(): Promise<void> {
    return post('/v1/ai/system/clear-cache').then(response => response.data)
  },

  // 导出数据
  exportAlgorithms(params?: AIAlgorithmQuery): Promise<Blob> {
    return download('/v1/ai/algorithms/export', { params }).then(response => response.data)
  },

  exportServices(params?: AIServiceQuery): Promise<Blob> {
    return download('/v1/ai/services/export', { params }).then(response => response.data)
  },

  exportModels(params?: AIModelQuery): Promise<Blob> {
    return download('/v1/ai/models/export', { params }).then(response => response.data)
  },

  // 导入数据
  importAlgorithms(file: File): Promise<{ success: number; failed: number; errors: string[] }> {
    const formData = new FormData()
    formData.append('file', file)
    
    return upload('/v1/ai/algorithms/import', formData).then(response => response.data)
  },

  importServices(file: File): Promise<{ success: number; failed: number; errors: string[] }> {
    const formData = new FormData()
    formData.append('file', file)
    
    return upload('/v1/ai/services/import', formData).then(response => response.data)
  },

  importModels(file: File): Promise<{ success: number; failed: number; errors: string[] }> {
    const formData = new FormData()
    formData.append('file', file)
    
    return upload('/v1/ai/models/import', formData).then(response => response.data)
  }
}

export default aiApi