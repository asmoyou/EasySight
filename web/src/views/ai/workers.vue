<template>
  <div class="workers-container">
    <!-- 页面标题 -->
    <div class="page-header">
      <h2>Worker节点管理</h2>
      <p class="page-description">管理和监控分布式Worker节点状态及任务执行情况</p>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-grid">
      <el-card class="stat-card">
        <div class="stat-content">
          <div class="stat-icon online">
            <el-icon><Monitor /></el-icon>
          </div>
          <div class="stat-info"> 
            <div class="stat-value">{{ stats.online_workers }}</div>
            <div class="stat-label">在线节点</div>
          </div>
        </div>
      </el-card>
      
      <el-card class="stat-card">
        <div class="stat-content">
          <div class="stat-icon total">
            <el-icon><Cpu /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.total_workers }}</div>
            <div class="stat-label">总节点数</div>
          </div>
        </div>
      </el-card>
      
      <el-card class="stat-card">
        <div class="stat-content">
          <div class="stat-icon busy">
            <el-icon><Loading /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.busy_workers }}</div>
            <div class="stat-label">繁忙节点</div>
          </div>
        </div>
      </el-card>
      
      <el-card class="stat-card">
        <div class="stat-content">
          <div class="stat-icon tasks">
            <el-icon><Operation /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.completed_tasks_today }}</div>
            <div class="stat-label">今日完成任务</div>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 操作栏 -->
    <div class="action-bar">
      <div class="action-left">
        <el-button type="primary" @click="refreshData" :loading="loading">
          <el-icon><Refresh /></el-icon>
          刷新数据
        </el-button>
        <el-button type="success" @click="showStartWorkerDialog">
          <el-icon><VideoPlay /></el-icon>
          启动本地Worker
        </el-button>
        <el-button type="danger" @click="stopLocalWorkers" :loading="stopping">
          <el-icon><VideoPause /></el-icon>
          停止本地Worker
        </el-button>
      </div>
      <div class="action-right">
        <el-input
          v-model="searchQuery"
          placeholder="搜索节点名称或ID"
          style="width: 300px"
          clearable
          @input="handleSearch"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
      </div>
    </div>

    <!-- Worker节点列表 -->
    <el-card class="table-card">
      <template #header>
        <div class="card-header">
          <span>Worker节点列表</span>
          <el-tag :type="getStatusTagType(workerData.online_nodes, workerData.total_nodes)">
            {{ workerData.online_nodes }}/{{ workerData.total_nodes }} 在线
          </el-tag>
        </div>
      </template>
      
      <el-table
        :data="filteredWorkers"
        v-loading="loading"
        stripe
        style="width: 100%"
        empty-text="暂无Worker节点"
      >
        <el-table-column label="节点信息" min-width="200">
          <template #default="{ row }">
            <div class="node-info">
              <div class="node-name">{{ row.node_name }}</div>
              <div class="node-id">{{ row.node_id }}</div>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column label="状态" width="120">
          <template #default="{ row }">
            <el-tag :type="getStatusColor(row.status)" size="small">
              {{ getStatusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column label="Worker池" width="100">
          <template #default="{ row }">
            <span class="pool-size">{{ row.worker_pool_size }}</span>
          </template>
        </el-table-column>
        
        <el-table-column label="任务情况" width="150">
          <template #default="{ row }">
            <div class="task-info">
              <div class="current-tasks">
                当前: <span class="task-count">{{ row.current_tasks || 0 }}</span>
              </div>
              <div class="total-tasks">
                总计: <span class="task-count">{{ row.total_tasks_executed || 0 }}</span>
              </div>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column label="最后心跳" width="180">
          <template #default="{ row }">
            <div class="heartbeat-info">
              <div class="heartbeat-time">{{ formatTime(row.last_heartbeat) }}</div>
              <div class="heartbeat-ago">{{ getTimeAgo(row.last_heartbeat) }}</div>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column label="注册时间" width="180">
          <template #default="{ row }">
            {{ formatTime(row.registered_at) }}
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button
              type="primary"
              size="small"
              @click="viewWorkerTasks(row)"
            >
              查看任务
            </el-button>
            <el-button
              type="danger"
              size="small"
              @click="unregisterWorker(row)"
              :disabled="row.status === 'online'"
            >
              注销
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 启动Worker对话框 -->
    <el-dialog
      v-model="showWorkerDialog"
      title="启动本地Worker池"
      width="500px"
      :close-on-click-modal="false"
    >
      <el-form :model="workerForm" label-width="120px">
        <el-form-item label="Worker池大小">
          <el-input-number
            v-model="workerForm.poolSize"
            :min="1"
            :max="10"
            controls-position="right"
            style="width: 200px"
          />
          <div class="form-tip">建议根据服务器CPU核心数设置</div>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="showWorkerDialog = false">取消</el-button>
        <el-button type="primary" @click="startLocalWorkers" :loading="starting">
          启动
        </el-button>
      </template>
    </el-dialog>

    <!-- Worker任务详情对话框 -->
    <el-dialog
      v-model="showTaskDialog"
      :title="`${selectedWorker?.node_name} - 任务详情`"
      width="80%"
      :close-on-click-modal="false"
    >
      <div class="task-dialog-content">
        <!-- 任务统计 -->
        <div class="task-stats">
          <el-card class="task-stat-card">
            <div class="task-stat-content">
              <div class="task-stat-value">{{ workerTasks.length }}</div>
              <div class="task-stat-label">总任务数</div>
            </div>
          </el-card>
          <el-card class="task-stat-card">
            <div class="task-stat-content">
              <div class="task-stat-value">{{ getTaskCountByStatus('running') }}</div>
              <div class="task-stat-label">运行中</div>
            </div>
          </el-card>
          <el-card class="task-stat-card">
            <div class="task-stat-content">
              <div class="task-stat-value">{{ getTaskCountByStatus('completed') }}</div>
              <div class="task-stat-label">已完成</div>
            </div>
          </el-card>
          <el-card class="task-stat-card">
            <div class="task-stat-content">
              <div class="task-stat-value">{{ getTaskCountByStatus('failed') }}</div>
              <div class="task-stat-label">失败</div>
            </div>
          </el-card>
        </div>

        <!-- 任务列表 -->
        <el-table
          :data="workerTasks"
          v-loading="loadingTasks"
          stripe
          style="width: 100%; margin-top: 20px"
          empty-text="暂无任务数据"
        >
          <el-table-column label="任务ID" width="80">
            <template #default="{ row }">
              <span class="task-id">#{{ row.task_id }}</span>
            </template>
          </el-table-column>
          
          <el-table-column label="任务名称" min-width="150">
            <template #default="{ row }">
              <div class="task-name">{{ row.task_name }}</div>
            </template>
          </el-table-column>
          
          <el-table-column label="诊断类型" width="120">
            <template #default="{ row }">
              <el-tag size="small">{{ row.diagnosis_type }}</el-tag>
            </template>
          </el-table-column>
          
          <el-table-column label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="getTaskStatusColor(row.status)" size="small">
                {{ getTaskStatusLabel(row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          
          <el-table-column label="进度" width="120">
            <template #default="{ row }">
              <el-progress
                v-if="row.progress !== undefined"
                :percentage="row.progress"
                :stroke-width="6"
                :show-text="false"
              />
              <span v-else>-</span>
            </template>
          </el-table-column>
          
          <el-table-column label="执行次数" width="150">
            <template #default="{ row }">
              <div class="execution-stats">
                <div class="total-runs">
                  总计: <span class="run-count">{{ row.total_runs || 0 }}</span>
                </div>
                <div class="success-runs">
                  成功: <span class="success-count">{{ row.success_runs || 0 }}</span>
                </div>
                <div class="failed-runs">
                  失败: <span class="failed-count">{{ row.failed_runs || 0 }}</span>
                </div>
              </div>
            </template>
          </el-table-column>
          
          <el-table-column label="分配时间" width="180">
            <template #default="{ row }">
              {{ formatTime(row.assigned_at) }}
            </template>
          </el-table-column>
          
          <el-table-column label="开始时间" width="180">
            <template #default="{ row }">
              {{ row.started_at ? formatTime(row.started_at) : '-' }}
            </template>
          </el-table-column>
          
          <el-table-column label="完成时间" width="180">
            <template #default="{ row }">
              {{ row.completed_at ? formatTime(row.completed_at) : '-' }}
            </template>
          </el-table-column>
          
          <el-table-column label="错误信息" min-width="200">
            <template #default="{ row }">
              <span v-if="row.error_message" class="error-message">
                {{ row.error_message }}
              </span>
              <span v-else>-</span>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Monitor,
  Cpu,
  Loading,
  Operation,
  Refresh,
  VideoPlay,
  VideoPause,
  Search
} from '@element-plus/icons-vue'
import { workerApi, type WorkerNode, type WorkerTask, type WorkerStats } from '@/api/worker'
import { formatDistanceToNow } from 'date-fns'
import { zhCN } from 'date-fns/locale'

// 响应式数据
const loading = ref(false)
const starting = ref(false)
const stopping = ref(false)
const loadingTasks = ref(false)
const searchQuery = ref('')
const showWorkerDialog = ref(false)
const showTaskDialog = ref(false)

// Worker数据
const workerData = reactive({
  total_nodes: 0,
  online_nodes: 0,
  nodes: [] as WorkerNode[]
})

// 统计数据
const stats = reactive<WorkerStats>({
  total_workers: 0,
  online_workers: 0,
  busy_workers: 0,
  total_tasks_today: 0,
  completed_tasks_today: 0,
  failed_tasks_today: 0,
  avg_task_duration: 0
})

// Worker表单
const workerForm = reactive({
  poolSize: 3
})

// 选中的Worker和任务
const selectedWorker = ref<WorkerNode | null>(null)
const workerTasks = ref<WorkerTask[]>([])

// 计算属性
const filteredWorkers = computed(() => {
  if (!searchQuery.value) {
    return workerData.nodes
  }
  const query = searchQuery.value.toLowerCase()
  return workerData.nodes.filter(worker => 
    worker.node_name.toLowerCase().includes(query) ||
    worker.node_id.toLowerCase().includes(query)
  )
})

// 方法
const loadWorkerData = async () => {
  try {
    loading.value = true
    const response = await workerApi.getDistributedWorkers()
    if (response.code === 200) {
      Object.assign(workerData, response.data)
    }
  } catch (error) {
    console.error('加载Worker数据失败:', error)
    ElMessage.error('加载Worker数据失败')
  } finally {
    loading.value = false
  }
}

const loadWorkerStats = async () => {
  try {
    const response = await workerApi.getWorkerStats()
    if (response.code === 200) {
      Object.assign(stats, response.data)
    }
  } catch (error) {
    console.error('加载统计数据失败:', error)
  }
}

const refreshData = async () => {
  await Promise.all([
    loadWorkerData(),
    loadWorkerStats()
  ])
}

const showStartWorkerDialog = () => {
  showWorkerDialog.value = true
}

const startLocalWorkers = async () => {
  try {
    starting.value = true
    const response = await workerApi.startWorkers(workerForm.poolSize)
    if (response.code === 200) {
      ElMessage.success(response.data.message)
      showWorkerDialog.value = false
      await refreshData()
    }
  } catch (error) {
    console.error('启动Worker失败:', error)
    ElMessage.error('启动Worker失败')
  } finally {
    starting.value = false
  }
}

const stopLocalWorkers = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要停止本地Worker池吗？这将中断正在执行的任务。',
      '确认停止',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    stopping.value = true
    const response = await workerApi.stopWorkers()
    if (response.code === 200) {
      ElMessage.success(response.data.message)
      await refreshData()
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('停止Worker失败:', error)
      ElMessage.error('停止Worker失败')
    }
  } finally {
    stopping.value = false
  }
}

const unregisterWorker = async (worker: WorkerNode) => {
  try {
    await ElMessageBox.confirm(
      `确定要注销Worker节点 "${worker.node_name}" 吗？`,
      '确认注销',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    const response = await workerApi.unregisterWorker(worker.node_id)
    if (response.code === 200) {
      ElMessage.success(response.data.message)
      await refreshData()
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('注销Worker失败:', error)
      ElMessage.error('注销Worker失败')
    }
  }
}

const viewWorkerTasks = async (worker: WorkerNode) => {
  selectedWorker.value = worker
  showTaskDialog.value = true
  
  try {
    loadingTasks.value = true
    const response = await workerApi.getWorkerTasks(worker.node_id)
    if (response.code === 200) {
      workerTasks.value = response.data
    }
  } catch (error) {
    console.error('加载任务数据失败:', error)
    ElMessage.error('加载任务数据失败')
    workerTasks.value = []
  } finally {
    loadingTasks.value = false
  }
}

const handleSearch = () => {
  // 搜索逻辑已在计算属性中处理
}

// 工具函数
const getStatusColor = (status: string) => {
  const colorMap: Record<string, string> = {
    online: 'success',
    offline: 'info',
    busy: 'warning',
    error: 'danger'
  }
  return colorMap[status] || 'info'
}

const getStatusLabel = (status: string) => {
  const labelMap: Record<string, string> = {
    online: '在线',
    offline: '离线',
    busy: '繁忙',
    error: '错误'
  }
  return labelMap[status] || status
}

const getStatusTagType = (online: number, total: number) => {
  if (total === 0) return 'info'
  const ratio = online / total
  if (ratio >= 0.8) return 'success'
  if (ratio >= 0.5) return 'warning'
  return 'danger'
}

const getTaskStatusColor = (status: string) => {
  const colorMap: Record<string, string> = {
    pending: 'info',
    running: 'warning',
    completed: 'success',
    failed: 'danger',
    cancelled: 'info'
  }
  return colorMap[status] || 'info'
}

const getTaskStatusLabel = (status: string) => {
  const labelMap: Record<string, string> = {
    pending: '等待中',
    running: '运行中',
    completed: '已完成',
    failed: '失败',
    cancelled: '已取消'
  }
  return labelMap[status] || status
}

const getTaskCountByStatus = (status: string) => {
  return workerTasks.value.filter(task => task.status === status).length
}

const formatTime = (timeStr: string) => {
  if (!timeStr) return '-'
  return new Date(timeStr).toLocaleString('zh-CN')
}

const getTimeAgo = (timeStr: string) => {
  if (!timeStr) return '-'
  try {
    return formatDistanceToNow(new Date(timeStr), {
      addSuffix: true,
      locale: zhCN
    })
  } catch {
    return '-'
  }
}

// 生命周期
onMounted(() => {
  refreshData()
  
  // 设置定时刷新
  const interval = setInterval(refreshData, 30000) // 30秒刷新一次
  
  // 组件卸载时清除定时器
  const cleanup = () => clearInterval(interval)
  if (typeof window !== 'undefined') {
    window.addEventListener('beforeunload', cleanup)
  }
})
</script>

<style scoped>
.workers-container {
  padding: 20px;
  background-color: #f5f7fa;
  min-height: 100vh;
}

.page-header {
  margin-bottom: 24px;
}

.page-header h2 {
  margin: 0 0 8px 0;
  color: #303133;
  font-size: 24px;
  font-weight: 600;
}

.page-description {
  margin: 0;
  color: #606266;
  font-size: 14px;
}

/* 统计卡片样式 */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
  margin-bottom: 24px;
}

.stat-card {
  border: none;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.stat-content {
  display: flex;
  align-items: center;
  padding: 8px 0;
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 16px;
  font-size: 24px;
  color: white;
}

.stat-icon.online {
  background: linear-gradient(135deg, #67c23a, #85ce61);
}

.stat-icon.total {
  background: linear-gradient(135deg, #409eff, #66b1ff);
}

.stat-icon.busy {
  background: linear-gradient(135deg, #e6a23c, #ebb563);
}

.stat-icon.tasks {
  background: linear-gradient(135deg, #909399, #a6a9ad);
}

.stat-value {
  font-size: 28px;
  font-weight: 600;
  color: #303133;
  line-height: 1;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 14px;
  color: #606266;
}

/* 操作栏样式 */
.action-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding: 16px 20px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.action-left {
  display: flex;
  gap: 12px;
}

/* 表格卡片样式 */
.table-card {
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

/* 节点信息样式 */
.node-info {
  display: flex;
  flex-direction: column;
}

.node-name {
  font-weight: 600;
  color: #303133;
  margin-bottom: 4px;
}

.node-id {
  font-size: 12px;
  color: #909399;
  font-family: 'Courier New', monospace;
}

.pool-size {
  font-weight: 600;
  color: #409eff;
}

/* 任务信息样式 */
.task-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.current-tasks,
.total-tasks {
  font-size: 12px;
  color: #606266;
}

.task-count {
  font-weight: 600;
  color: #303133;
}

/* 心跳信息样式 */
.heartbeat-info {
  display: flex;
  flex-direction: column;
}

.heartbeat-time {
  font-size: 12px;
  color: #303133;
  margin-bottom: 2px;
}

.heartbeat-ago {
  font-size: 11px;
  color: #909399;
}

/* 表单提示样式 */
.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

/* 任务对话框样式 */
.task-dialog-content {
  max-height: 70vh;
  overflow-y: auto;
}

.task-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 16px;
  margin-bottom: 20px;
}

.task-stat-card {
  text-align: center;
  border: none;
  box-shadow: 0 2px 8px 0 rgba(0, 0, 0, 0.1);
}

.task-stat-content {
  padding: 8px 0;
}

.task-stat-value {
  font-size: 24px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 4px;
}

.task-stat-label {
  font-size: 12px;
  color: #606266;
}

.task-id {
  font-family: 'Courier New', monospace;
  font-weight: 600;
  color: #409eff;
}

.task-name {
  font-weight: 500;
  color: #303133;
}

.error-message {
  color: #f56c6c;
  font-size: 12px;
  word-break: break-all;
}

/* 执行次数统计样式 */
.execution-stats {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.total-runs,
.success-runs,
.failed-runs {
  font-size: 12px;
  color: #606266;
}

.run-count {
  font-weight: 600;
  color: #303133;
}

.success-count {
  font-weight: 600;
  color: #67C23A;
}

.failed-count {
  font-weight: 600;
  color: #F56C6C;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .workers-container {
    padding: 12px;
  }
  
  .stats-grid {
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 12px;
  }
  
  .action-bar {
    flex-direction: column;
    gap: 12px;
    align-items: stretch;
  }
  
  .action-left {
    justify-content: center;
  }
}
</style>