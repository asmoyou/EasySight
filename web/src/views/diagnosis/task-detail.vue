<template>
  <div class="task-detail">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <el-button @click="goBack" size="small">
          <el-icon><ArrowLeft /></el-icon>
          返回
        </el-button>
        <div class="title-section">
          <h2>{{ task?.name || '任务详情' }}</h2>
          <div class="task-status">
            <el-tag :type="getStatusColor(task?.status)" size="large">
              {{ getStatusName(task?.status) }}
            </el-tag>
            <el-tag v-if="task?.template_name" type="info" size="small">{{ task.template_name }}</el-tag>
          </div>
        </div>
      </div>
      <div class="header-right">
        <el-button 
          type="success" 
          @click="handleRun"
          :disabled="task?.status === 'running'"
          :loading="running"
        >
          <el-icon><VideoPlay /></el-icon>
          执行任务
        </el-button>
        <el-button type="primary" @click="handleEdit">
          <el-icon><Edit /></el-icon>
          编辑
        </el-button>
      </div>
    </div>

    <!-- 任务信息卡片 -->
    <div class="content-grid">
      <!-- 基本信息 -->
      <el-card class="info-card" shadow="hover">
        <template #header>
          <div class="card-header">
            <span>基本信息</span>
          </div>
        </template>
        <div class="info-grid" v-loading="loading">
          <div class="info-item">
            <label>任务名称：</label>
            <span>{{ task?.name }}</span>
          </div>
          <div class="info-item">
            <label>诊断类型：</label>
            <el-tag :type="getDiagnosisTypeColor(task?.diagnosis_type)" size="small">
              {{ getDiagnosisTypeName(task?.diagnosis_type) }}
            </el-tag>
          </div>
          <div class="info-item">
            <label>目标摄像头：</label>
            <span>{{ cameraName || '未知' }}</span>
          </div>
          <div class="info-item">
            <label>启用状态：</label>
            <el-switch
              v-model="taskIsActive"
              @change="handleToggleActive"
              :loading="switching"
              :disabled="!task"
            />
          </div>
          <div class="info-item">
            <label>调度类型：</label>
            <span>
              <el-icon v-if="task?.is_scheduled" color="#67C23A"><Clock /></el-icon>
              <el-icon v-else color="#909399"><Minus /></el-icon>
              {{ task?.is_scheduled ? '定时任务' : '手动任务' }}
            </span>
          </div>
          <div class="info-item" v-if="task?.is_scheduled && task?.schedule_config?.cron_expression">
            <label>Cron表达式：</label>
            <code>{{ task.schedule_config.cron_expression }}</code>
          </div>
          <div class="info-item">
            <label>创建人：</label>
            <span>{{ task?.created_by_name }}</span>
          </div>
          <div class="info-item">
            <label>创建时间：</label>
            <span>{{ formatDateTime(task?.created_at) }}</span>
          </div>
          <div class="info-item">
            <label>更新时间：</label>
            <span>{{ formatDateTime(task?.updated_at) }}</span>
          </div>
          <div class="info-item full-width" v-if="task?.description">
            <label>任务描述：</label>
            <span>{{ task.description }}</span>
          </div>
        </div>
      </el-card>

      <!-- 执行统计 -->
      <el-card class="stats-card" shadow="hover">
        <template #header>
          <div class="card-header">
            <span>执行统计</span>
          </div>
        </template>
        <div class="stats-content" v-loading="loading">
          <div class="stat-item">
            <div class="stat-value">{{ task?.run_count || 0 }}</div>
            <div class="stat-label">总执行次数</div>
          </div>
          <div class="stat-item">
            <div class="stat-value success">{{ task?.success_count || 0 }}</div>
            <div class="stat-label">成功次数</div>
          </div>
          <div class="stat-item">
            <div class="stat-value error">{{ task?.error_count || 0 }}</div>
            <div class="stat-label">失败次数</div>
          </div>
          <div class="stat-item">
            <div class="stat-value">{{ successRate }}%</div>
            <div class="stat-label">成功率</div>
          </div>
        </div>
        <div class="time-info">
          <div class="time-item">
            <label>最后执行：</label>
            <span>{{ task?.last_run ? formatDateTime(task.last_run) : '未执行' }}</span>
          </div>
          <div class="time-item" v-if="task?.next_run">
            <label>下次执行：</label>
            <span>{{ formatDateTime(task.next_run) }}</span>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 配置信息 -->
    <el-card class="config-card" shadow="hover" v-if="task?.config && Object.keys(task.config).length > 0">
      <template #header>
        <div class="card-header">
          <span>配置参数</span>
        </div>
      </template>
      <div class="config-content" v-loading="loading">
        <el-descriptions :column="2" border>
          <el-descriptions-item
            v-for="(value, key) in (task?.config || {})"
            :key="key"
            :label="key"
          >
            <span v-if="typeof value === 'object'">{{ JSON.stringify(value) }}</span>
            <span v-else>{{ value }}</span>
          </el-descriptions-item>
        </el-descriptions>
      </div>
    </el-card>

    <!-- 执行历史 -->
    <el-card class="history-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <span>执行历史</span>
          <el-button size="small" @click="loadResults">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>
      </template>
      <div class="history-content">
        <el-table
          :data="results"
          v-loading="resultsLoading"
          stripe
          style="width: 100%"
        >
          <el-table-column prop="id" label="ID" width="80" />
          <el-table-column label="执行状态" width="100">
            <template #default="{ row }">
              <el-tag :type="getResultStatusColor(row.status)" size="small">
                {{ getResultStatusName(row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="score" label="评分" width="80">
            <template #default="{ row }">
              <span v-if="row.score !== null">{{ row.score.toFixed(2) }}</span>
              <span v-else class="text-muted">-</span>
            </template>
          </el-table-column>
          <el-table-column prop="issues_count" label="问题数量" width="100" />
          <el-table-column prop="execution_time" label="执行时长" width="120">
            <template #default="{ row }">
              <span v-if="row.execution_time">{{ row.execution_time }}ms</span>
              <span v-else class="text-muted">-</span>
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="执行时间" width="150">
            <template #default="{ row }">
              {{ formatDateTime(row.created_at) }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="120">
            <template #default="{ row }">
              <el-button 
                type="text" 
                size="small"
                @click="handleViewResult(row)"
              >
                查看详情
              </el-button>
            </template>
          </el-table-column>
        </el-table>
        
        <!-- 分页 -->
        <div class="pagination-container" v-if="resultsTotal > 0">
          <el-pagination
            v-model:current-page="resultsPage"
            v-model:page-size="resultsPageSize"
            :page-sizes="[10, 20, 50]"
            :total="resultsTotal"
            layout="total, sizes, prev, pager, next"
            @size-change="handleResultsSizeChange"
            @current-change="handleResultsCurrentChange"
          />
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft, VideoPlay, Edit, Clock, Minus, Refresh } from '@element-plus/icons-vue'
import { diagnosisTaskApi, diagnosisResultApi, type DiagnosisTask, type DiagnosisResult } from '@/api/diagnosis'
import { cameraApi, type Camera } from '@/api/cameras'
import { formatDateTime } from '@/utils/date'

const route = useRoute()
const router = useRouter()

// 响应式数据
const loading = ref(false)
const running = ref(false)
const switching = ref(false)
const resultsLoading = ref(false)
const task = ref<DiagnosisTask | null>(null)
const camera = ref<Camera | null>(null)
const results = ref<DiagnosisResult[]>([])

// 分页
const resultsPage = ref(1)
const resultsPageSize = ref(10)
const resultsTotal = ref(0)

// 计算属性
const taskId = computed(() => parseInt(route.params.id as string))
const cameraName = computed(() => camera.value?.name || '未知')
const successRate = computed(() => {
  if (!task.value || task.value.run_count === 0) return 0
  return Math.round((task.value.success_count / task.value.run_count) * 100)
})
const taskIsActive = computed({
  get: () => task.value?.is_active || false,
  set: (value: boolean) => {
    if (task.value) {
      task.value.is_active = value
    }
  }
})

// 状态映射函数
const getStatusName = (status: string) => {
  const statusMap: Record<string, string> = {
    pending: '待执行',
    running: '运行中',
    completed: '已完成',
    failed: '失败',
    cancelled: '已取消'
  }
  return statusMap[status] || status
}

const getStatusColor = (status: string) => {
  const colorMap: Record<string, string> = {
    pending: 'info',
    running: 'warning',
    completed: 'success',
    failed: 'danger',
    cancelled: 'info'
  }
  return colorMap[status] || 'info'
}

const getDiagnosisTypeName = (type: string) => {
  const typeMap: Record<string, string> = {
    brightness: '亮度检测',
    blue_screen: '蓝屏检查',
    clarity: '清晰度检查',
    shake: '抖动检查',
    freeze: '冻结检测',
    color_cast: '偏色检测',
    occlusion: '遮挡检测',
    noise: '噪声检测',
    contrast: '对比度检测',
    mosaic: '马赛克检测',
    flower_screen: '花屏检测'
  }
  return typeMap[type] || type
}

const getDiagnosisTypeColor = (type: string) => {
  const colorMap: Record<string, string> = {
    brightness: 'warning',
    blue_screen: 'danger',
    clarity: 'primary',
    shake: 'warning',
    freeze: 'danger',
    color_cast: 'warning',
    occlusion: 'danger',
    noise: 'warning',
    contrast: 'primary',
    mosaic: 'danger',
    flower_screen: 'danger'
  }
  return colorMap[type] || 'info'
}

const getResultStatusName = (status: string) => {
  const statusMap: Record<string, string> = {
    success: '成功',
    failed: '失败',
    error: '错误'
  }
  return statusMap[status] || status
}

const getResultStatusColor = (status: string) => {
  const colorMap: Record<string, string> = {
    success: 'success',
    failed: 'warning',
    error: 'danger'
  }
  return colorMap[status] || 'info'
}

// 方法
const loadTask = async () => {
  try {
    loading.value = true
    const response = await diagnosisTaskApi.getTask(taskId.value)
    task.value = response.data
    
    // 加载摄像头信息
    if (task.value?.target_id) {
      loadCamera(task.value.target_id)
    }
  } catch (error) {
    console.error('加载任务详情失败:', error)
    ElMessage.error('加载任务详情失败')
  } finally {
    loading.value = false
  }
}

const loadCamera = async (cameraId: number) => {
  try {
    const response = await cameraApi.getCamera(cameraId)
    camera.value = response.data
  } catch (error) {
    console.error('加载摄像头信息失败:', error)
  }
}

const loadResults = async () => {
  try {
    resultsLoading.value = true
    const response = await diagnosisResultApi.getResults({
      task_id: taskId.value,
      page: resultsPage.value,
      page_size: resultsPageSize.value
    })
    results.value = response.data?.results || []
    resultsTotal.value = response.data?.total || 0
  } catch (error) {
    console.error('加载执行历史失败:', error)
    ElMessage.error('加载执行历史失败')
  } finally {
    resultsLoading.value = false
  }
}

const goBack = () => {
  router.push('/diagnosis/tasks')
}

const handleEdit = () => {
  router.push(`/diagnosis/tasks?edit=${taskId.value}`)
}

const handleRun = async () => {
  try {
    await ElMessageBox.confirm(
      `确定要执行诊断任务 "${task.value?.name}" 吗？`,
      '确认执行',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    running.value = true
    await diagnosisTaskApi.runTask(taskId.value)
    ElMessage.success('任务执行成功')
    
    // 刷新任务信息和执行历史
    await loadTask()
    await loadResults()
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('执行任务失败:', error)
      ElMessage.error('执行任务失败')
    }
  } finally {
    running.value = false
  }
}

const handleToggleActive = async () => {
  if (!task.value) {
    ElMessage.error('任务数据未加载')
    return
  }
  
  try {
    switching.value = true
    await diagnosisTaskApi.toggleTask(taskId.value, task.value.is_active)
    ElMessage.success(task.value.is_active ? '任务已启用' : '任务已禁用')
  } catch (error) {
    console.error('切换任务状态失败:', error)
    ElMessage.error('操作失败')
    // 回滚状态
    if (task.value) {
      task.value.is_active = !task.value.is_active
    }
  } finally {
    switching.value = false
  }
}

const handleViewResult = (result: DiagnosisResult) => {
  router.push(`/diagnosis/results/${result.id}`)
}

const handleResultsSizeChange = (size: number) => {
  resultsPageSize.value = size
  resultsPage.value = 1
  loadResults()
}

const handleResultsCurrentChange = (page: number) => {
  resultsPage.value = page
  loadResults()
}

// 生命周期
onMounted(() => {
  loadTask()
  loadResults()
})
</script>

<style scoped>
.task-detail {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
}

.header-left {
  display: flex;
  align-items: flex-start;
  gap: 16px;
}

.title-section h2 {
  margin: 0 0 8px 0;
  font-size: 24px;
  font-weight: 600;
}

.task-status {
  display: flex;
  align-items: center;
  gap: 8px;
}

.header-right {
  display: flex;
  gap: 12px;
}

.content-grid {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 20px;
  margin-bottom: 20px;
}

.info-card,
.stats-card,
.config-card,
.history-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
}

.info-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.info-item {
  display: flex;
  align-items: center;
}

.info-item.full-width {
  grid-column: 1 / -1;
  align-items: flex-start;
}

.info-item label {
  font-weight: 500;
  color: #666;
  margin-right: 8px;
  min-width: 80px;
}

.info-item code {
  background: #f5f5f5;
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'Courier New', monospace;
}

.stats-content {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  margin-bottom: 20px;
}

.stat-item {
  text-align: center;
}

.stat-value {
  font-size: 24px;
  font-weight: 600;
  margin-bottom: 4px;
}

.stat-value.success {
  color: #67C23A;
}

.stat-value.error {
  color: #F56C6C;
}

.stat-label {
  font-size: 12px;
  color: #666;
}

.time-info {
  border-top: 1px solid #eee;
  padding-top: 16px;
}

.time-item {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
}

.time-item label {
  font-weight: 500;
  color: #666;
  margin-right: 8px;
  min-width: 80px;
}

.config-content {
  max-height: 400px;
  overflow-y: auto;
}

.history-content {
  min-height: 300px;
}

.pagination-container {
  padding: 20px 0;
  text-align: right;
}

.text-muted {
  color: #999;
}

@media (max-width: 768px) {
  .content-grid {
    grid-template-columns: 1fr;
  }
  
  .info-grid {
    grid-template-columns: 1fr;
  }
  
  .stats-content {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .header-left {
    flex-direction: column;
    gap: 8px;
  }
}
</style>