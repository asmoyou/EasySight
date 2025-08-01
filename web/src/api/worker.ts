import request from '@/utils/request'
import type { ApiResponse } from '@/types/api'

// Worker节点状态枚举
export enum WorkerStatus {
  ONLINE = 'online',
  OFFLINE = 'offline',
  BUSY = 'busy',
  ERROR = 'error'
}

// Worker节点信息接口
export interface WorkerNode {
  node_id: string
  node_name: string
  status: WorkerStatus
  worker_pool_size: number
  current_tasks: number
  total_tasks_executed: number
  last_heartbeat: string
  registered_at: string
  worker_status: Record<string, any>
}

// Worker节点注册信息
export interface WorkerNodeInfo {
  node_id: string
  node_name: string
  worker_pool_size: number
}

// Worker心跳信息
export interface WorkerHeartbeat {
  timestamp: string
  status: WorkerStatus
  worker_status: Record<string, any>
}

// Worker节点列表响应
export interface WorkerNodeListResponse {
  total_nodes: number
  online_nodes: number
  nodes: WorkerNode[]
}

// Worker任务信息
export interface WorkerTask {
  task_id: number
  task_name: string
  diagnosis_type: string
  status: string
  assigned_at: string
  started_at?: string
  completed_at?: string
  node_id: string
  progress?: number
  error_message?: string
}

// Worker统计信息
export interface WorkerStats {
  total_workers: number
  online_workers: number
  busy_workers: number
  total_tasks_today: number
  completed_tasks_today: number
  failed_tasks_today: number
  avg_task_duration: number
}

// Worker API
export const workerApi = {
  // 获取所有分布式Worker节点状态
  getDistributedWorkers: (): Promise<ApiResponse<WorkerNodeListResponse>> => {
    return request.get('/v1/diagnosis/workers/distributed').then(response => ({
      code: 200,
      message: 'success',
      data: response.data,
      success: true
    }))
  },

  // 获取本地Worker状态
  getWorkerStatus: (): Promise<ApiResponse<any>> => {
    return request.get('/v1/diagnosis/workers/status').then(response => ({
      code: 200,
      message: 'success',
      data: response.data,
      success: true
    }))
  },

  // 启动Worker池
  startWorkers: (poolSize: number = 3): Promise<ApiResponse<{ message: string }>> => {
    return request.post('/v1/diagnosis/workers/start', null, {
      params: { pool_size: poolSize }
    }).then(response => ({
      code: 200,
      message: 'success',
      data: response.data,
      success: true
    }))
  },

  // 停止Worker池
  stopWorkers: (): Promise<ApiResponse<{ message: string }>> => {
    return request.post('/v1/diagnosis/workers/stop').then(response => ({
      code: 200,
      message: 'success',
      data: response.data,
      success: true
    }))
  },

  // 注销Worker节点
  unregisterWorker: (nodeId: string): Promise<ApiResponse<{ message: string }>> => {
    return request.delete(`/v1/diagnosis/workers/${nodeId}`).then(response => ({
      code: 200,
      message: 'success',
      data: response.data,
      success: true
    }))
  },

  // 获取Worker节点的任务列表
  getWorkerTasks: (nodeId: string, params?: {
    page?: number
    page_size?: number
    status?: string
  }): Promise<ApiResponse<WorkerTask[]>> => {
    return request.get(`/v1/diagnosis/workers/${nodeId}/tasks`, { params }).then(response => ({
      code: 200,
      message: 'success',
      data: response.data,
      success: true
    }))
  },

  // 获取Worker统计信息
  getWorkerStats: (): Promise<ApiResponse<WorkerStats>> => {
    return request.get('/v1/diagnosis/workers/stats').then(response => ({
      code: 200,
      message: 'success',
      data: response.data,
      success: true
    }))
  },

  // 为Worker节点获取待执行任务
  fetchTasksForWorker: (nodeId: string, batchSize: number = 1): Promise<ApiResponse<any[]>> => {
    return request.get('/v1/diagnosis/workers/fetch-tasks', {
      params: { node_id: nodeId, batch_size: batchSize }
    }).then(response => ({
      code: 200,
      message: 'success',
      data: response.data,
      success: true
    }))
  },

  // Worker完成任务回调
  completeTask: (nodeId: string, data: {
    task_id: number
    success: boolean
    result_data?: any
    error_message?: string
  }): Promise<ApiResponse<{ message: string }>> => {
    return request.post('/v1/diagnosis/workers/complete-task', data, {
      params: { node_id: nodeId }
    }).then(response => ({
      code: 200,
      message: 'success',
      data: response.data,
      success: true
    }))
  }
}