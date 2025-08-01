// AI算法相关类型定义
export interface AIAlgorithm {
  id: number
  name: string
  algorithm_type: AlgorithmType
  version: string
  description?: string
  config_schema: Record<string, any>
  input_format: Record<string, any>
  output_format: Record<string, any>
  performance_metrics?: {
    accuracy?: number
    precision?: number
    recall?: number
    f1_score?: number
    inference_time?: number
    memory_usage?: number
  }
  resource_requirements?: {
    min_cpu_cores?: number
    min_memory_gb?: number
    min_gpu_memory_gb?: number
    supported_gpu_types?: string[]
  }
  supported_platforms: string[]
  tags: string[]
  file_path?: string
  file_size?: number
  usage_count?: number
  status: AlgorithmStatus
  is_active: boolean
  created_by?: number
  created_at: string
  updated_at: string
}

export interface AIAlgorithmCreate {
  name: string
  algorithm_type: AlgorithmType
  version: string
  description?: string
  config_schema: Record<string, any>
  input_format: Record<string, any>
  output_format: Record<string, any>
  performance_metrics?: Record<string, any>
  resource_requirements?: Record<string, any>
  supported_platforms: string[]
  tags: string[]
  file_path?: string
  file_size?: number
  status?: AlgorithmStatus
  is_active: boolean
}

export interface AIAlgorithmUpdate {
  name?: string
  algorithm_type?: AlgorithmType
  version?: string
  description?: string
  config_schema?: Record<string, any>
  input_format?: Record<string, any>
  output_format?: Record<string, any>
  performance_metrics?: Record<string, any>
  resource_requirements?: Record<string, any>
  supported_platforms?: string[]
  tags?: string[]
  file_path?: string
  file_size?: number
  status?: AlgorithmStatus
  is_active?: boolean
}

// AI服务相关类型定义
export interface AIService {
  id: number
  name: string
  algorithm_id: number
  algorithm?: AIAlgorithm
  camera_id: number
  camera?: {
    id: number
    name: string
    location: string
    stream_url: string
  }
  description?: string
  config: Record<string, any>
  status: ServiceStatus
  performance_metrics?: {
    fps?: number
    latency?: number
    cpu_usage?: number
    memory_usage?: number
    gpu_usage?: number
    error_rate?: number
  }
  last_heartbeat?: string
  error_message?: string
  start_time?: string
  stop_time?: string
  created_by?: number
  created_at: string
  updated_at: string
  loading?: boolean
}

export interface AIServiceCreate {
  name: string
  algorithm_id: number
  camera_id: number
  description?: string
  config: Record<string, any>
  auto_start?: boolean
}

export interface AIServiceUpdate {
  name?: string
  algorithm_id?: number
  camera_id?: number
  description?: string
  config?: Record<string, any>
  status?: ServiceStatus
}

// AI模型相关类型定义
export interface AIModel {
  id: number
  name: string
  model_type: ModelType
  version: string
  description?: string
  file_path: string
  file_size: number
  algorithm_id?: number
  algorithm?: AIAlgorithm
  input_format: Record<string, any>
  output_format: Record<string, any>
  performance_metrics?: {
    accuracy?: number
    precision?: number
    recall?: number
    f1_score?: number
    inference_time?: number
    model_size?: number
    flops?: number
  }
  tags: string[]
  checksum?: string
  is_active: boolean
  created_by?: number
  created_at: string
  updated_at: string
}

export interface AIModelCreate {
  name: string
  model_type: ModelType
  version: string
  description?: string
  file_path: string
  file_size: number
  algorithm_id: number
  input_format: Record<string, any>
  output_format: Record<string, any>
  performance_metrics?: Record<string, any>
  tags: string[]
  checksum?: string
  is_active: boolean
}

export interface AIModelUpdate {
  name?: string
  model_type?: ModelType
  version?: string
  description?: string
  file_path?: string
  file_size?: number
  algorithm_id?: number
  input_format?: Record<string, any>
  output_format?: Record<string, any>
  performance_metrics?: Record<string, any>
  tags?: string[]
  checksum?: string
  is_active?: boolean
}

// AI服务日志相关类型定义
export interface AIServiceLog {
  id: number
  service_id: number
  service?: AIService
  log_level: LogLevel
  message: string
  details?: Record<string, any>
  timestamp: string
}

// 统计数据类型定义
export interface AIStats {
  total_algorithms: number
  active_algorithms: number
  total_services: number
  online_services: number
  total_models: number
  active_models: number
  total_requests_today: number
  success_rate: number
  avg_response_time: number
  algorithm_type_distribution: Record<string, number>
  service_status_distribution: Record<string, number>
  model_type_distribution: Record<string, number>
  // 服务统计
  total_count?: number
  online_count?: number
  processing_count?: number
  // 模型统计
  total_model_size?: number
  avg_model_accuracy?: number
}

// 枚举类型定义
export type AlgorithmType = 
  | 'object_detection'
  | 'face_recognition'
  | 'behavior_analysis'
  | 'vehicle_detection'
  | 'intrusion_detection'
  | 'fire_detection'
  | 'smoke_detection'
  | 'crowd_analysis'
  | 'abnormal_behavior'
  | 'custom'

export type AlgorithmStatus = 
  | 'draft'
  | 'published'
  | 'deprecated'
  | 'testing'

export type ServiceStatus = 
  | 'running'
  | 'stopped'
  | 'error'
  | 'starting'
  | 'stopping'

export type ModelType = 
  | 'pytorch'
  | 'tensorflow'
  | 'onnx'
  | 'openvino'
  | 'tensorrt'
  | 'other'

export type LogLevel = 
  | 'debug'
  | 'info'
  | 'warning'
  | 'error'
  | 'critical'

// API响应类型定义
export interface AIApiResponse<T> {
  data: T[]
  total: number
  page: number
  page_size: number
}

export interface AIStatsResponse {
  total_algorithms: number
  active_algorithms: number
  total_services: number
  online_services: number
  total_models: number
  active_models: number
  total_requests_today: number
  success_rate: number
  avg_response_time: number
  algorithm_type_distribution: Record<string, number>
  service_status_distribution: Record<string, number>
  model_type_distribution: Record<string, number>
  total_count: number
  online_count: number
  processing_count: number
  total_model_size: number
  avg_model_accuracy: number
}

// API查询参数类型定义
export interface AIAlgorithmQuery {
  page?: number
  page_size?: number
  search?: string
  algorithm_type?: AlgorithmType
  status?: AlgorithmStatus
  is_active?: boolean
  created_by?: number
}

export interface AIServiceQuery {
  page?: number
  page_size?: number
  search?: string
  algorithm_id?: number
  camera_id?: number
  status?: ServiceStatus
  created_by?: number
}

export interface AIModelQuery {
  page?: number
  page_size?: number
  search?: string
  model_type?: ModelType
  algorithm_id?: number
  is_active?: boolean
  created_by?: number
}

export interface AIServiceLogQuery {
  page?: number
  page_size?: number
  service_id?: number
  log_level?: LogLevel
  start_time?: string
  end_time?: string
}

// 表单验证规则类型
export interface ValidationRule {
  required?: boolean
  message: string
  trigger?: string | string[]
  min?: number
  max?: number
  pattern?: RegExp
  validator?: (rule: any, value: any, callback: any) => void
}

// 操作结果类型
export interface OperationResult {
  success: boolean
  message: string
  data?: any
}

// 文件上传相关类型
export interface FileUploadOptions {
  accept?: string
  maxSize?: number
  multiple?: boolean
}

export interface UploadedFile {
  name: string
  size: number
  type: string
  url: string
  path: string
}

// 性能监控相关类型
export interface PerformanceMetrics {
  timestamp: string
  cpu_usage: number
  memory_usage: number
  gpu_usage?: number
  fps?: number
  latency?: number
  error_rate?: number
}

export interface ResourceUsage {
  cpu_cores: number
  memory_gb: number
  gpu_memory_gb?: number
  disk_space_gb: number
}

// 配置相关类型
export interface AIConfig {
  detection_threshold?: number
  nms_threshold?: number
  max_detections?: number
  input_size?: [number, number]
  batch_size?: number
  device?: 'cpu' | 'gpu'
  precision?: 'fp32' | 'fp16' | 'int8'
  [key: string]: any
}

// 算法市场相关类型
export interface AlgorithmMarketItem {
  id: number
  name: string
  description: string
  algorithm_type: AlgorithmType
  version: string
  author: string
  downloads: number
  rating: number
  price: number
  is_free: boolean
  tags: string[]
  screenshots: string[]
  created_at: string
  updated_at: string
}

// 部署相关类型
export interface DeploymentConfig {
  replicas: number
  resources: ResourceUsage
  environment: Record<string, string>
  volumes: Array<{
    name: string
    path: string
    size: string
  }>
  ports: Array<{
    name: string
    port: number
    protocol: 'TCP' | 'UDP'
  }>
}

export interface DeploymentStatus {
  status: 'pending' | 'running' | 'failed' | 'stopped'
  replicas: {
    desired: number
    ready: number
    available: number
  }
  conditions: Array<{
    type: string
    status: string
    reason?: string
    message?: string
    lastTransitionTime: string
  }>
  events: Array<{
    type: 'Normal' | 'Warning'
    reason: string
    message: string
    timestamp: string
  }>
}