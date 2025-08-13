import { api } from './index'

/**
 * 事件任务管理API
 */
export const eventTasksApi = {
  /**
   * 获取事件任务列表
   * @param {Object} params - 查询参数
   * @param {number} params.page - 页码
   * @param {number} params.page_size - 每页数量
   * @param {string} params.search - 搜索关键词
   * @param {string} params.status - 状态筛选
   * @param {string} params.task_type - 任务类型筛选
   * @param {number} params.ai_service_id - AI服务ID筛选
   * @param {number} params.camera_id - 摄像头ID筛选
   * @param {boolean} params.is_active - 是否启用筛选
   * @param {string} params.assigned_worker - Worker筛选
   * @param {string} params.start_date - 开始日期
   * @param {string} params.end_date - 结束日期
   * @returns {Promise} 任务列表响应
   */
  getTasks(params = {}) {
    return api.get('/event-tasks', { params })
  },

  /**
   * 创建事件任务
   * @param {Object} taskData - 任务数据
   * @param {string} taskData.name - 任务名称
   * @param {string} taskData.description - 任务描述
   * @param {number} taskData.ai_service_id - AI服务ID
   * @param {string} taskData.task_type - 任务类型
   * @param {Object} taskData.detection_config - 检测配置
   * @param {Array} taskData.roi_areas - ROI区域
   * @param {number} taskData.alarm_threshold - 告警阈值
   * @param {Object} taskData.schedule_config - 调度配置
   * @param {number} taskData.check_interval - 检查间隔
   * @param {boolean} taskData.auto_recovery - 自动恢复
   * @param {number} taskData.max_retry_count - 最大重试次数
   * @param {number} taskData.recovery_interval - 恢复间隔
   * @param {Object} taskData.metadata - 元数据
   * @param {Array} taskData.tags - 标签
   * @returns {Promise} 创建的任务信息
   */
  createTask(taskData) {
    return api.post('/event-tasks', taskData)
  },

  /**
   * 获取事件任务详情
   * @param {number} taskId - 任务ID
   * @returns {Promise} 任务详情
   */
  getTask(taskId) {
    return api.get(`/event-tasks/${taskId}`)
  },

  /**
   * 更新事件任务
   * @param {number} taskId - 任务ID
   * @param {Object} taskData - 更新的任务数据
   * @returns {Promise} 更新后的任务信息
   */
  updateTask(taskId, taskData) {
    return api.put(`/event-tasks/${taskId}`, taskData)
  },

  /**
   * 删除事件任务
   * @param {number} taskId - 任务ID
   * @returns {Promise} 删除结果
   */
  deleteTask(taskId) {
    return api.delete(`/event-tasks/${taskId}`)
  },

  /**
   * 启动事件任务
   * @param {number} taskId - 任务ID
   * @param {string} workerId - 指定的Worker ID（可选）
   * @returns {Promise} 启动结果
   */
  startTask(taskId, workerId = null) {
    const params = workerId ? { worker_id: workerId } : {}
    return api.post(`/event-tasks/${taskId}/start`, null, { params })
  },

  /**
   * 停止事件任务
   * @param {number} taskId - 任务ID
   * @param {string} reason - 停止原因
   * @returns {Promise} 停止结果
   */
  stopTask(taskId, reason = '手动停止') {
    return api.post(`/event-tasks/${taskId}/stop`, null, {
      params: { reason }
    })
  },

  /**
   * 获取事件任务日志
   * @param {number} taskId - 任务ID
   * @param {Object} params - 查询参数
   * @param {number} params.page - 页码
   * @param {number} params.page_size - 每页数量
   * @param {string} params.log_type - 日志类型筛选
   * @param {string} params.log_level - 日志级别筛选
   * @param {string} params.start_date - 开始日期
   * @param {string} params.end_date - 结束日期
   * @returns {Promise} 任务日志列表
   */
  getTaskLogs(taskId, params = {}) {
    return api.get(`/event-tasks/${taskId}/logs`, { params })
  },

  /**
   * 获取事件任务统计信息
   * @param {number} days - 统计天数
   * @returns {Promise} 统计信息
   */
  getStats(days = 7) {
    return api.get('/event-tasks/stats/overview', {
      params: { days }
    })
  },

  /**
   * 获取当前运行中的任务列表
   * @returns {Promise} 运行中的任务列表
   */
  getRunningTasks() {
    return api.get('/event-tasks/running/list')
  },

  /**
   * 批量操作事件任务
   * @param {Array} taskIds - 任务ID列表
   * @param {string} action - 操作类型 (start|stop|delete)
   * @param {Object} params - 操作参数
   * @returns {Promise} 批量操作结果
   */
  batchOperation(taskIds, action, params = {}) {
    return api.post('/event-tasks/batch', {
      task_ids: taskIds,
      action,
      params
    })
  },

  /**
   * 导出事件任务数据
   * @param {Object} params - 导出参数
   * @param {string} params.format - 导出格式 (csv|excel|json)
   * @param {Array} params.task_ids - 指定任务ID列表（可选）
   * @param {Object} params.filters - 筛选条件（可选）
   * @returns {Promise} 导出文件
   */
  exportTasks(params = {}) {
    return api.get('/event-tasks/export', {
      params,
      responseType: 'blob'
    })
  },

  /**
   * 获取任务性能指标
   * @param {number} taskId - 任务ID
   * @param {Object} params - 查询参数
   * @param {string} params.start_time - 开始时间
   * @param {string} params.end_time - 结束时间
   * @param {string} params.interval - 时间间隔 (1m|5m|1h|1d)
   * @returns {Promise} 性能指标数据
   */
  getTaskMetrics(taskId, params = {}) {
    return api.get(`/event-tasks/${taskId}/metrics`, { params })
  },

  /**
   * 获取任务恢复历史
   * @param {number} taskId - 任务ID
   * @param {Object} params - 查询参数
   * @returns {Promise} 恢复历史记录
   */
  getTaskRecoveryHistory(taskId, params = {}) {
    return api.get(`/event-tasks/${taskId}/recovery-history`, { params })
  },

  /**
   * 手动触发任务恢复
   * @param {number} taskId - 任务ID
   * @param {string} reason - 恢复原因
   * @returns {Promise} 恢复结果
   */
  triggerTaskRecovery(taskId, reason = '手动恢复') {
    return api.post(`/event-tasks/${taskId}/recover`, {
      reason
    })
  },

  /**
   * 获取任务配置模板
   * @param {string} algorithmType - 算法类型
   * @returns {Promise} 配置模板
   */
  getTaskTemplate(algorithmType) {
    return api.get('/event-tasks/templates', {
      params: { algorithm_type: algorithmType }
    })
  },

  /**
   * 验证任务配置
   * @param {Object} taskConfig - 任务配置
   * @returns {Promise} 验证结果
   */
  validateTaskConfig(taskConfig) {
    return api.post('/event-tasks/validate', taskConfig)
  },

  /**
   * 获取Worker状态和负载信息
   * @returns {Promise} Worker状态列表
   */
  getWorkerStatus() {
    return api.get('/event-tasks/workers/status')
  },

  /**
   * 重新分配任务到指定Worker
   * @param {number} taskId - 任务ID
   * @param {string} workerId - 目标Worker ID
   * @returns {Promise} 重新分配结果
   */
  reassignTask(taskId, workerId) {
    return api.post(`/event-tasks/${taskId}/reassign`, {
      worker_id: workerId
    })
  },

  /**
   * 获取任务依赖关系
   * @param {number} taskId - 任务ID
   * @returns {Promise} 依赖关系信息
   */
  getTaskDependencies(taskId) {
    return api.get(`/event-tasks/${taskId}/dependencies`)
  },

  /**
   * 设置任务依赖关系
   * @param {number} taskId - 任务ID
   * @param {Array} dependencies - 依赖任务ID列表
   * @returns {Promise} 设置结果
   */
  setTaskDependencies(taskId, dependencies) {
    return api.post(`/event-tasks/${taskId}/dependencies`, {
      dependencies
    })
  },

  /**
   * 获取任务执行历史
   * @param {number} taskId - 任务ID
   * @param {Object} params - 查询参数
   * @returns {Promise} 执行历史记录
   */
  getTaskExecutionHistory(taskId, params = {}) {
    return api.get(`/event-tasks/${taskId}/execution-history`, { params })
  },

  /**
   * 克隆事件任务
   * @param {number} taskId - 源任务ID
   * @param {Object} overrides - 覆盖配置
   * @returns {Promise} 新任务信息
   */
  cloneTask(taskId, overrides = {}) {
    return api.post(`/event-tasks/${taskId}/clone`, overrides)
  },

  /**
   * 获取任务告警规则
   * @param {number} taskId - 任务ID
   * @returns {Promise} 告警规则列表
   */
  getTaskAlarmRules(taskId) {
    return api.get(`/event-tasks/${taskId}/alarm-rules`)
  },

  /**
   * 设置任务告警规则
   * @param {number} taskId - 任务ID
   * @param {Array} rules - 告警规则列表
   * @returns {Promise} 设置结果
   */
  setTaskAlarmRules(taskId, rules) {
    return api.post(`/event-tasks/${taskId}/alarm-rules`, {
      rules
    })
  }
}

export default eventTasksApi