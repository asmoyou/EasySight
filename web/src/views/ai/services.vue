<template>
  <div class="ai-services-container">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <h1 class="page-title">
          <el-icon><Setting /></el-icon>
          AI服务管理
        </h1>
        <p class="page-description">管理AI服务实例，配置摄像头点位的AI算法服务</p>
      </div>
      <div class="header-right">
        <el-button type="primary" @click="handleAdd">
          <el-icon><Plus /></el-icon>
          创建服务
        </el-button>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-cards">
      <el-row :gutter="16">
        <el-col :span="6">
          <div class="stat-card">
            <div class="stat-icon online">
              <el-icon><VideoPlay /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ stats.online_count }}</div>
              <div class="stat-label">在线服务</div>
            </div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-card">
            <div class="stat-icon total">
              <el-icon><Grid /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ stats.total_count }}</div>
              <div class="stat-label">总服务数</div>
            </div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-card">
            <div class="stat-icon processing">
              <el-icon><Loading /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ stats.processing_count }}</div>
              <div class="stat-label">处理中</div>
            </div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-card">
            <div class="stat-icon success">
              <el-icon><SuccessFilled /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ stats.success_rate.toFixed(1) }}%</div>
              <div class="stat-label">成功率</div>
            </div>
          </div>
        </el-col>
      </el-row>
    </div>

    <!-- 搜索和筛选 -->
    <div class="search-filters">
      <el-row :gutter="16">
        <el-col :span="6">
          <el-input
            v-model="searchQuery"
            placeholder="搜索服务名称或摄像头"
            clearable
            @input="handleSearch"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </el-col>
        <el-col :span="4">
          <el-select
            v-model="filterAlgorithm"
            placeholder="算法类型"
            clearable
            @change="handleFilter"
          >
            <el-option
              v-for="algorithm in algorithms"
              :key="algorithm.id"
              :label="algorithm.name"
              :value="algorithm.id"
            />
          </el-select>
        </el-col>
        <el-col :span="4">
          <el-select
            v-model="filterStatus"
            placeholder="服务状态"
            clearable
            @change="handleFilter"
          >
            <el-option label="运行中" value="running" />
            <el-option label="已停止" value="stopped" />
            <el-option label="错误" value="error" />
            <el-option label="启动中" value="starting" />
            <el-option label="停止中" value="stopping" />
          </el-select>
        </el-col>
        <el-col :span="4">
          <el-select
            v-model="filterCamera"
            placeholder="摄像头"
            clearable
            @change="handleFilter"
          >
            <el-option
              v-for="camera in cameras"
              :key="camera.id"
              :label="camera.name"
              :value="camera.id"
            />
          </el-select>
        </el-col>
        <el-col :span="6">
          <div class="filter-actions">
            <el-button @click="resetFilters">重置</el-button>
            <el-button type="primary" @click="loadServices">搜索</el-button>
          </div>
        </el-col>
      </el-row>
    </div>

    <!-- 服务列表 -->
    <div class="services-table">
      <el-table
        :data="services"
        v-loading="loading"
        stripe
        style="width: 100%"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="55" />
        
        <el-table-column prop="name" label="服务名称" min-width="150">
          <template #default="{ row }">
            <div class="service-name">
              <strong>{{ row.name }}</strong>
              <div class="service-meta">
                <el-tag size="small" :type="getStatusColor(row.status)">
                  {{ getStatusLabel(row.status) }}
                </el-tag>
              </div>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column prop="algorithm" label="算法" min-width="120">
          <template #default="{ row }">
            <div class="algorithm-info">
              <div class="algorithm-name">{{ row.algorithm_name }}</div>
              <div class="algorithm-version">ID: {{ row.algorithm_id }}</div>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column prop="camera" label="摄像头" min-width="150">
          <template #default="{ row }">
            <div class="camera-info">
              <div class="camera-name">{{ row.camera_name }}</div>
              <div class="camera-id">ID: {{ row.camera_id }}</div>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column label="性能指标" min-width="200">
          <template #default="{ row }">
            <div class="performance-metrics">
              <div class="metric-item">
                <span class="metric-label">FPS:</span>
                <span class="metric-value">{{ row.performance_metrics?.fps || 0 }}</span>
              </div>
              <div class="metric-item">
                <span class="metric-label">延迟:</span>
                <span class="metric-value">{{ row.performance_metrics?.latency || 0 }}ms</span>
              </div>
              <div class="metric-item">
                <span class="metric-label">CPU:</span>
                <span class="metric-value">{{ row.performance_metrics?.cpu_usage || 0 }}%</span>
              </div>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column label="状态信息" min-width="180">
          <template #default="{ row }">
            <div class="status-info">
              <div class="status-item">
                <span class="status-label">运行状态:</span>
                <el-tag size="small" :type="getStatusColor(row.status)">
                  {{ getStatusLabel(row.status) }}
                </el-tag>
              </div>
              <div class="status-item">
                <span class="status-label">发布状态:</span>
                <el-tag size="small" :type="row.is_published ? 'success' : 'info'">
                  {{ row.is_published ? '已发布' : '未发布' }}
                </el-tag>
              </div>
              <div v-if="row.node_name" class="status-item">
                <span class="status-label">节点:</span>
                <span class="node-name">{{ row.node_name }}</span>
              </div>
              <div v-if="row.deployment_id" class="status-item">
                <span class="status-label">部署ID:</span>
                <span class="deployment-id">{{ row.deployment_id }}</span>
              </div>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <div class="action-buttons">
              <el-button
                v-if="row.status === 'stopped'"
                type="success"
                size="small"
                @click="startService(row)"
                :loading="row.loading"
              >
                启动
              </el-button>
              <el-button
                v-else-if="row.status === 'running'"
                type="warning"
                size="small"
                @click="stopService(row)"
                :loading="row.loading"
              >
                停止
              </el-button>
              <el-button
                type="primary"
                size="small"
                @click="editService(row)"
              >
                编辑
              </el-button>
              <el-button
                type="danger"
                size="small"
                @click="deleteService(row)"
              >
                删除
              </el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 分页 -->
    <div class="pagination-container">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="[10, 20, 50, 100]"
        :total="total"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </div>

    <!-- 创建/编辑服务对话框 -->
    <el-dialog
      v-model="showCreateDialog"
      :title="editingService ? '编辑服务' : '创建服务'"
      width="600px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="serviceFormRef"
        :model="serviceForm"
        :rules="serviceRules"
        label-width="120px"
      >
        <el-form-item label="服务名称" prop="name">
          <el-input v-model="serviceForm.name" placeholder="请输入服务名称" />
        </el-form-item>
        
        <el-form-item label="选择算法" prop="algorithm_id">
          <el-select v-model="serviceForm.algorithm_id" placeholder="选择算法" style="width: 100%">
            <el-option
              v-for="algorithm in algorithms"
              :key="algorithm.id"
              :label="`${algorithm.name} (v${algorithm.version})`"
              :value="algorithm.id"
            >
              <div class="algorithm-option">
                <div class="algorithm-name">{{ algorithm.name }}</div>
                <div class="algorithm-type">{{ getAlgorithmTypeLabel(algorithm.algorithm_type) }}</div>
              </div>
            </el-option>
          </el-select>
        </el-form-item>
        
        <el-form-item label="选择摄像头" prop="camera_id">
          <el-select v-model="serviceForm.camera_id" placeholder="选择摄像头" style="width: 100%">
            <el-option
              v-for="camera in cameras"
              :key="camera.id"
              :label="camera.name"
              :value="camera.id"
            >
              <div class="camera-option">
                <div class="camera-name">{{ camera.name }}</div>
                <div class="camera-location">{{ camera.location }}</div>
              </div>
            </el-option>
          </el-select>
        </el-form-item>
        
        <el-form-item label="服务描述">
          <el-input
            v-model="serviceForm.description"
            type="textarea"
            :rows="3"
            placeholder="请输入服务描述"
          />
        </el-form-item>
        
        <el-form-item label="配置参数">
          <el-input
            v-model="configJson"
            type="textarea"
            :rows="4"
            placeholder="请输入JSON格式的配置参数"
          />
          <div class="form-tip">请输入有效的JSON格式配置</div>
        </el-form-item>
        
        <el-form-item label="自动启动">
          <el-switch v-model="serviceForm.auto_start" />
          <span class="form-tip">创建后自动启动服务</span>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="showCreateDialog = false">取消</el-button>
          <el-button type="primary" @click="saveService" :loading="saving">
            {{ editingService ? '更新' : '创建' }}
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { 
  Setting, 
  Plus, 
  Search, 
  VideoPlay, 
  Grid, 
  Loading, 
  SuccessFilled 
} from '@element-plus/icons-vue'
import { aiApi } from '@/api/ai'
import { cameraApi } from '@/api/cameras'
import type { 
  AIService, 
  AIServiceCreate, 
  AIServiceUpdate, 
  AIAlgorithm 
} from '@/types/ai'
import type { Camera } from '@/types/camera'

// 响应式数据
const loading = ref(false)
const saving = ref(false)
const services = ref<AIService[]>([])
const algorithms = ref<AIAlgorithm[]>([])
const cameras = ref<Camera[]>([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)
const selectedServices = ref<AIService[]>([])

// 统计数据
const stats = ref({
  total_count: 0,
  online_count: 0,
  processing_count: 0,
  success_rate: 0
})

// 搜索和筛选
const searchQuery = ref('')
const filterAlgorithm = ref<number | undefined>(undefined)
const filterStatus = ref('')
const filterCamera = ref<number | undefined>(undefined)

// 对话框
const showCreateDialog = ref(false)
const editingService = ref<AIService | null>(null)
const serviceFormRef = ref<FormInstance>()

// 表单数据
const serviceForm = reactive<AIServiceCreate>({
  name: '',
  algorithm_id: undefined,
  camera_id: undefined,
  description: '',
  config: {},
  auto_start: true
})

// 配置JSON字符串
const configJson = ref('{}')

// 表单验证规则
const serviceRules: FormRules = {
  name: [
    { required: true, message: '请输入服务名称', trigger: 'blur' },
    { min: 2, max: 100, message: '长度在 2 到 100 个字符', trigger: 'blur' }
  ],
  algorithm_id: [
    { required: true, message: '请选择算法', trigger: 'change' }
  ],
  camera_id: [
    { required: true, message: '请选择摄像头', trigger: 'change' }
  ]
}

// 方法
const loadServices = async () => {
  try {
    loading.value = true
    const params = {
      page: currentPage.value,
      page_size: pageSize.value,
      search: searchQuery.value || undefined,
      algorithm_id: filterAlgorithm.value,
      status: filterStatus.value || undefined,
      camera_id: filterCamera.value
    }
    
    const response = await aiApi.getServices(params)
    
    // 后端直接返回数组，不是{data: [], total: number}格式
    if (Array.isArray(response)) {
      services.value = response
      total.value = response.length
    } else if (response && response.data) {
      // 如果是标准格式
      services.value = response.data || []
      total.value = response.total || 0
    } else {
      console.error('未知的响应格式:', response)
      services.value = []
      total.value = 0
    }
  } catch (error) {
    console.error('加载服务列表失败:', error)
    console.error('错误详情:', error.message)
    console.error('错误堆栈:', error.stack)
    ElMessage.error('加载服务列表失败')
  } finally {
    loading.value = false
  }
}

const loadAlgorithms = async () => {
  try {
    const response = await aiApi.getAlgorithms({ page: 1, page_size: 100, is_active: true })
    algorithms.value = response.data || []
  } catch (error) {
    console.error('加载算法列表失败:', error)
  }
}

const loadCameras = async () => {
  try {
    const response = await cameraApi.getCameras({ page: 1, page_size: 100, is_active: true })
    cameras.value = response.data?.cameras || []
  } catch (error) {
    console.error('加载摄像头列表失败:', error)
  }
}

const loadStats = async () => {
  try {
    console.log('开始加载统计数据...')
    const response = await aiApi.getStats()
    console.log('统计数据原始响应:', response)
    console.log('响应类型:', typeof response)
    console.log('响应字段:', Object.keys(response))
    
    stats.value = {
      total_count: response.total_count || 0,
      online_count: response.online_count || 0,
      processing_count: response.processing_count || 0,
      success_rate: response.success_rate || 0
    }
    console.log('设置的统计数据:', stats.value)
  } catch (error) {
    console.error('加载统计数据失败:', error)
    console.error('错误详情:', error.message)
    console.error('错误堆栈:', error.stack)
    // 设置默认值
    stats.value = {
      total_count: 0,
      online_count: 0,
      processing_count: 0,
      success_rate: 0
    }
  }
}

const handleSearch = () => {
  currentPage.value = 1
  loadServices()
}

const handleFilter = () => {
  currentPage.value = 1
  loadServices()
}

const resetFilters = () => {
  searchQuery.value = ''
  filterAlgorithm.value = undefined
  filterStatus.value = ''
  filterCamera.value = undefined
  currentPage.value = 1
  loadServices()
}

const handleSizeChange = (size: number) => {
  pageSize.value = size
  currentPage.value = 1
  loadServices()
}

const handleCurrentChange = (page: number) => {
  currentPage.value = page
  loadServices()
}

const handleSelectionChange = (selection: AIService[]) => {
  selectedServices.value = selection
}

const startService = async (service: AIService) => {
  try {
    service.loading = true
    await aiApi.startService(service.id)
    ElMessage.success('服务启动成功')
    loadServices()
    loadStats()
  } catch (error) {
    console.error('启动服务失败:', error)
    ElMessage.error('启动服务失败')
  } finally {
    service.loading = false
  }
}

const stopService = async (service: AIService) => {
  try {
    service.loading = true
    await aiApi.stopService(service.id)
    ElMessage.success('服务停止成功')
    loadServices()
    loadStats()
  } catch (error) {
    console.error('停止服务失败:', error)
    ElMessage.error('停止服务失败')
  } finally {
    service.loading = false
  }
}

const editService = async (service: AIService) => {
  try {
    editingService.value = service
    Object.assign(serviceForm, {
      name: service.name,
      algorithm_id: service.algorithm_id,
      camera_id: service.camera_id,
      description: service.description,
      config: service.config,
      auto_start: false
    })
    
    configJson.value = JSON.stringify(service.config || {}, null, 2)
    showCreateDialog.value = true
  } catch (error) {
    console.error('编辑服务失败:', error)
    ElMessage.error('编辑服务失败')
  }
}

const deleteService = async (service: AIService) => {
  try {
    await ElMessageBox.confirm(
      '确定要删除这个服务吗？删除后无法恢复。',
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await aiApi.deleteService(service.id)
    ElMessage.success('删除成功')
    loadServices()
    loadStats()
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('删除服务失败:', error)
      ElMessage.error('删除服务失败')
    }
  }
}

const saveService = async () => {
  try {
    await serviceFormRef.value?.validate()
    
    // 验证配置JSON
    try {
      serviceForm.config = JSON.parse(configJson.value)
    } catch (error) {
      ElMessage.error('配置参数格式错误，请输入有效的JSON')
      return
    }
    
    saving.value = true
    
    if (editingService.value) {
      // 更新服务
      const updateData: AIServiceUpdate = { ...serviceForm }
      delete updateData.auto_start
      await aiApi.updateService(editingService.value.id, updateData)
      ElMessage.success('服务更新成功')
    } else {
      // 创建服务
      await aiApi.createService(serviceForm)
      ElMessage.success('服务创建成功')
    }
    
    showCreateDialog.value = false
    resetForm()
    loadServices()
    loadStats()
  } catch (error) {
    console.error('保存服务失败:', error)
    ElMessage.error('保存服务失败')
  } finally {
    saving.value = false
  }
}

const resetForm = () => {
  editingService.value = null
  Object.assign(serviceForm, {
    name: '',
    algorithm_id: undefined,
    camera_id: undefined,
    description: '',
    config: {},
    auto_start: true
  })
  configJson.value = '{}'
  serviceFormRef.value?.resetFields()
}

const handleAdd = async () => {
  resetForm()
  // 确保摄像头数据已加载
  if (cameras.value.length === 0) {
    await loadCameras()
  }
  showCreateDialog.value = true
}

// 工具函数
const getStatusLabel = (status: string) => {
  const statusMap: Record<string, string> = {
    running: '运行中',
    stopped: '已停止',
    error: '错误',
    starting: '启动中',
    stopping: '停止中'
  }
  return statusMap[status] || status
}

const getStatusColor = (status: string) => {
  const colorMap: Record<string, string> = {
    running: 'success',
    stopped: 'info',
    error: 'danger',
    starting: 'warning',
    stopping: 'warning'
  }
  return colorMap[status] || ''
}

const getAlgorithmTypeLabel = (type: string) => {
  const typeMap: Record<string, string> = {
    object_detection: '目标检测',
    face_recognition: '人脸识别',
    behavior_analysis: '行为分析',
    vehicle_detection: '车辆检测',
    intrusion_detection: '入侵检测',
    fire_detection: '火焰检测',
    smoke_detection: '烟雾检测',
    crowd_analysis: '人群分析',
    abnormal_behavior: '异常行为',
    custom: '自定义'
  }
  return typeMap[type] || type
}

const formatDateTime = (date: string) => {
  return new Date(date).toLocaleString('zh-CN')
}

// 生命周期
onMounted(() => {
  loadServices()
  loadAlgorithms()
  loadCameras()
  loadStats()
})
</script>

<style scoped>
.ai-services-container {
  padding: 24px;
  background: #f5f5f5;
  min-height: 100vh;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
  padding: 24px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.header-left {
  flex: 1;
}

.page-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0 0 8px 0;
  font-size: 24px;
  font-weight: 600;
  color: #1f2937;
}

.page-description {
  margin: 0;
  color: #6b7280;
  font-size: 14px;
}

.header-right {
  display: flex;
  gap: 12px;
}

.stats-cards {
  margin-bottom: 24px;
}

.stat-card {
  display: flex;
  align-items: center;
  padding: 20px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
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
  background: linear-gradient(135deg, #10b981, #059669);
}

.stat-icon.total {
  background: linear-gradient(135deg, #3b82f6, #2563eb);
}

.stat-icon.processing {
  background: linear-gradient(135deg, #f59e0b, #d97706);
}

.stat-icon.success {
  background: linear-gradient(135deg, #8b5cf6, #7c3aed);
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #1f2937;
  line-height: 1;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 14px;
  color: #6b7280;
  font-weight: 500;
}

.search-filters {
  margin-bottom: 24px;
  padding: 20px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.filter-actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}

.services-table {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  margin-bottom: 24px;
}

.service-name {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.service-meta {
  display: flex;
  align-items: center;
  gap: 8px;
}

.algorithm-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.algorithm-name {
  font-weight: 600;
  color: #1f2937;
}

.algorithm-version {
  font-size: 12px;
  color: #6b7280;
}

.camera-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.camera-name {
  font-weight: 600;
  color: #1f2937;
}

.camera-location {
  font-size: 12px;
  color: #6b7280;
}

.performance-metrics {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.metric-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
}

.metric-label {
  color: #6b7280;
}

.metric-value {
  font-weight: 600;
  color: #1f2937;
}

.status-info {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.status-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
}

.status-label {
  color: #6b7280;
  font-weight: 500;
  min-width: 60px;
}

.node-name {
  font-weight: 600;
  color: #059669;
  background: #ecfdf5;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 11px;
}

.deployment-id {
  font-family: monospace;
  color: #7c3aed;
  background: #f3f4f6;
  padding: 2px 4px;
  border-radius: 3px;
  font-size: 10px;
}

.action-buttons {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
}

.pagination-container {
  display: flex;
  justify-content: center;
  padding: 24px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.algorithm-option,
.camera-option {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.algorithm-type,
.camera-location {
  font-size: 12px;
  color: #6b7280;
}

.form-tip {
  font-size: 12px;
  color: #6b7280;
  margin-top: 4px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    gap: 16px;
  }
  
  .search-filters .el-row {
    flex-direction: column;
  }
  
  .search-filters .el-col {
    width: 100%;
    margin-bottom: 12px;
  }
  
  .stats-cards .el-col {
    width: 50%;
    margin-bottom: 16px;
  }
}
</style>