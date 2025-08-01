import request from '@/utils/request'

// 统一管理相关的API接口

// 获取统计数据
export function getUnifiedStats() {
  return request({
    url: '/ai/stats',
    method: 'get'
  })
}

// 获取算法列表
export function getAlgorithms(params: any) {
  return request({
    url: '/ai/algorithms',
    method: 'get',
    params
  })
}

// 获取模型列表
export function getModels(params: any) {
  return request({
    url: '/ai/models',
    method: 'get',
    params
  })
}

// 获取服务列表
export function getServices(params: any) {
  return request({
    url: '/ai/services',
    method: 'get',
    params
  })
}

// 创建算法
export function createAlgorithm(data: any) {
  return request({
    url: '/ai/algorithms',
    method: 'post',
    data
  })
}

// 更新算法
export function updateAlgorithm(id: number, data: any) {
  return request({
    url: `/ai/algorithms/${id}`,
    method: 'put',
    data
  })
}

// 删除算法
export function deleteAlgorithm(id: number) {
  return request({
    url: `/ai/algorithms/${id}`,
    method: 'delete'
  })
}

// 创建模型
export function createModel(data: any) {
  return request({
    url: '/ai/models',
    method: 'post',
    data
  })
}

// 更新模型
export function updateModel(id: number, data: any) {
  return request({
    url: `/ai/models/${id}`,
    method: 'put',
    data
  })
}

// 删除模型
export function deleteModel(id: number) {
  return request({
    url: `/ai/models/${id}`,
    method: 'delete'
  })
}

// 上传算法包
export function uploadAlgorithmPackage(file: File) {
  const formData = new FormData()
  formData.append('file', file)
  
  return request({
    url: '/files/upload/algorithm-package',
    method: 'post',
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data'
    },
    timeout: 300000 // 5分钟超时
  })
}

// 上传模型文件
export function uploadModelFile(file: File) {
  const formData = new FormData()
  formData.append('file', file)
  
  return request({
    url: '/files/upload/model',
    method: 'post',
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data'
    },
    timeout: 600000 // 10分钟超时
  })
}

// 安装算法包
export function installAlgorithmPackage(packageData: any) {
  return request({
    url: '/files/install/algorithm-package',
    method: 'post',
    data: packageData
  })
}

// 获取算法详情
export function getAlgorithmDetail(id: number) {
  return request({
    url: `/ai/algorithms/${id}`,
    method: 'get'
  })
}

// 获取模型详情
export function getModelDetail(id: number) {
  return request({
    url: `/ai/models/${id}`,
    method: 'get'
  })
}

// 切换算法状态
export function toggleAlgorithmStatus(id: number, isActive: boolean) {
  return request({
    url: `/ai/algorithms/${id}/toggle`,
    method: 'patch',
    data: { is_active: isActive }
  })
}

// 切换模型状态
export function toggleModelStatus(id: number, isActive: boolean) {
  return request({
    url: `/ai/models/${id}/toggle`,
    method: 'patch',
    data: { is_active: isActive }
  })
}

// 获取算法关联的模型
export function getAlgorithmModels(algorithmId: number) {
  return request({
    url: `/ai/algorithms/${algorithmId}/models`,
    method: 'get'
  })
}

// 关联模型到算法
export function linkModelToAlgorithm(algorithmId: number, modelId: number) {
  return request({
    url: `/ai/algorithms/${algorithmId}/models/${modelId}`,
    method: 'post'
  })
}

// 取消模型与算法的关联
export function unlinkModelFromAlgorithm(algorithmId: number, modelId: number) {
  return request({
    url: `/ai/algorithms/${algorithmId}/models/${modelId}`,
    method: 'delete'
  })
}