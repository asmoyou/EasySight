<template>
  <div class="alarm-rules">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <h2>告警规则</h2>
        <p class="page-description">管理诊断告警规则，配置告警条件和通知方式</p>
      </div>
      <div class="header-right">
        <el-button type="primary" @click="handleCreate">
          <el-icon><Plus /></el-icon>
          新建规则
        </el-button>
      </div>
    </div>

    <!-- 搜索和筛选 -->
    <div class="search-filters">
      <div class="search-bar">
        <el-input
          v-model="searchForm.search"
          placeholder="搜索规则名称或描述"
          clearable
          @keyup.enter="handleSearch"
          style="width: 300px"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        <el-button type="primary" @click="handleSearch">
          <el-icon><Search /></el-icon>
          搜索
        </el-button>
        <el-button @click="handleReset">
          <el-icon><Refresh /></el-icon>
          重置
        </el-button>
      </div>
      
      <div class="filter-bar">
        <el-select v-model="searchForm.diagnosis_type" placeholder="诊断类型" clearable style="width: 150px">
          <el-option label="亮度检测" value="BRIGHTNESS" />
          <el-option label="蓝屏检测" value="BLUE_SCREEN" />
          <el-option label="清晰度检测" value="CLARITY" />
          <el-option label="画面抖动" value="SHAKE" />
          <el-option label="画面冻结" value="FREEZE" />
          <el-option label="偏色检测" value="COLOR_CAST" />
          <el-option label="遮挡检测" value="OCCLUSION" />
          <el-option label="噪声检测" value="NOISE" />
          <el-option label="对比度检测" value="CONTRAST" />
          <el-option label="马赛克检测" value="MOSAIC" />
          <el-option label="花屏检测" value="FLOWER_SCREEN" />
        </el-select>
        
        <el-select v-model="searchForm.severity" placeholder="严重程度" clearable style="width: 120px">
          <el-option label="低" value="LOW" />
          <el-option label="中" value="MEDIUM" />
          <el-option label="高" value="HIGH" />
          <el-option label="紧急" value="CRITICAL" />
        </el-select>
        
        <el-select v-model="searchForm.is_enabled" placeholder="启用状态" clearable style="width: 120px">
          <el-option label="已启用" :value="true" />
          <el-option label="已禁用" :value="false" />
        </el-select>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-cards">
      <el-row :gutter="20">
        <el-col :span="6">
          <div class="stat-card">
            <div class="stat-icon enabled">
              <el-icon><Check /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ stats.enabled_count }}</div>
              <div class="stat-label">已启用规则</div>
            </div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-card">
            <div class="stat-icon critical">
              <el-icon><Warning /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ stats.critical_count }}</div>
              <div class="stat-label">紧急级别规则</div>
            </div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-card">
            <div class="stat-icon triggered">
              <el-icon><Bell /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ stats.triggered_today }}</div>
              <div class="stat-label">今日触发次数</div>
            </div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-card">
            <div class="stat-icon total">
              <el-icon><DataBoard /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ stats.total_count }}</div>
              <div class="stat-label">总规则数</div>
            </div>
          </div>
        </el-col>
      </el-row>
    </div>

    <!-- 规则列表 -->
    <div class="table-container">
      <el-table
        :data="rules"
        v-loading="loading"
        stripe
        style="width: 100%"
      >
        <el-table-column prop="name" label="规则名称" min-width="200">
          <template #default="{ row }">
            <div class="rule-name">
              <span class="name">{{ row.name }}</span>
              <el-tag v-if="!row.is_enabled" type="info" size="small">已禁用</el-tag>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
        
        <el-table-column prop="diagnosis_type" label="诊断类型" width="120">
          <template #default="{ row }">
            <el-tag :type="getDiagnosisTypeColor(row.diagnosis_type)" size="small">
              {{ getDiagnosisTypeName(row.diagnosis_type) }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="camera_id" label="摄像头" width="120">
          <template #default="{ row }">
            <span v-if="row.camera_id">{{ getCameraName(row.camera_id) }}</span>
            <span v-else class="text-muted">全部</span>
          </template>
        </el-table-column>
        
        <el-table-column prop="severity" label="严重程度" width="100">
          <template #default="{ row }">
            <el-tag :type="getSeverityColor(row.severity)" size="small">
              {{ getSeverityName(row.severity) }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column label="阈值配置" width="150">
          <template #default="{ row }">
            <div v-if="row.threshold_config" class="threshold-config">
              <div v-for="(value, key) in row.threshold_config" :key="key" class="threshold-item">
                <span class="key">{{ key }}:</span>
                <span class="value">{{ value }}</span>
              </div>
            </div>
            <span v-else class="text-muted">无配置</span>
          </template>
        </el-table-column>
        
        <el-table-column label="通知渠道" width="120">
          <template #default="{ row }">
            <span v-if="row.notification_channels && row.notification_channels.length > 0">
              {{ row.notification_channels.length }} 个渠道
            </span>
            <span v-else class="text-muted">无</span>
          </template>
        </el-table-column>
        
        <el-table-column prop="is_enabled" label="状态" width="80">
          <template #default="{ row }">
            <el-switch
              v-model="row.is_enabled"
              @change="handleToggleEnabled(row)"
            />
          </template>
        </el-table-column>
        
        <el-table-column prop="created_at" label="创建时间" width="150">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="handleEdit(row)">编辑</el-button>
            <el-button size="small" type="primary" @click="handleTest(row)">测试</el-button>
            <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      
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
    </div>

    <!-- 创建/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑告警规则' : '新建告警规则'"
      width="800px"
      @close="handleDialogClose"
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="120px"
      >
        <el-form-item label="规则名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入规则名称" />
        </el-form-item>
        
        <el-form-item label="描述" prop="description">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="3"
            placeholder="请输入规则描述"
          />
        </el-form-item>
        
        <el-form-item label="诊断类型" prop="diagnosis_type">
          <el-select v-model="form.diagnosis_type" placeholder="请选择诊断类型" style="width: 100%">
            <el-option label="亮度检测" value="BRIGHTNESS" />
            <el-option label="蓝屏检测" value="BLUE_SCREEN" />
            <el-option label="清晰度检测" value="CLARITY" />
            <el-option label="画面抖动" value="SHAKE" />
            <el-option label="画面冻结" value="FREEZE" />
            <el-option label="偏色检测" value="COLOR_CAST" />
            <el-option label="遮挡检测" value="OCCLUSION" />
            <el-option label="噪声检测" value="NOISE" />
            <el-option label="对比度检测" value="CONTRAST" />
            <el-option label="马赛克检测" value="MOSAIC" />
            <el-option label="花屏检测" value="FLOWER_SCREEN" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="摄像头">
          <el-select v-model="form.camera_id" placeholder="选择摄像头（留空表示全部）" clearable style="width: 100%">
            <el-option
              v-for="camera in cameras"
              :key="camera.id"
              :label="camera.name"
              :value="camera.id"
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="严重程度" prop="severity">
          <el-select v-model="form.severity" placeholder="请选择严重程度" style="width: 100%">
            <el-option label="低" value="LOW" />
            <el-option label="中" value="MEDIUM" />
            <el-option label="高" value="HIGH" />
            <el-option label="紧急" value="CRITICAL" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="阈值配置">
          <div class="threshold-config-editor">
            <div v-for="(item, index) in thresholdItems" :key="index" class="threshold-item">
              <el-input
                v-model="item.key"
                placeholder="参数名"
                style="width: 200px; margin-right: 10px"
              />
              <el-input-number
                v-model="item.value"
                placeholder="阈值"
                style="width: 150px; margin-right: 10px"
                :precision="2"
              />
              <el-button
                type="danger"
                size="small"
                @click="removeThresholdItem(index)"
                :disabled="thresholdItems.length <= 1"
              >
                删除
              </el-button>
            </div>
            <el-button type="primary" size="small" @click="addThresholdItem">
              添加阈值
            </el-button>
          </div>
        </el-form-item>
        
        <el-form-item label="通知渠道">
          <el-select
            v-model="form.notification_channels"
            multiple
            placeholder="选择通知渠道"
            style="width: 100%"
          >
            <el-option
              v-for="channel in notificationChannels"
              :key="channel.id"
              :label="channel.name"
              :value="channel.id"
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="启用状态">
          <el-switch v-model="form.is_enabled" />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleSubmit" :loading="submitting">
            {{ isEdit ? '更新' : '创建' }}
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  Search, Refresh, Plus, Check, Warning, Bell, DataBoard
} from '@element-plus/icons-vue'
import { formatDateTime } from '@/utils/date'

// 类型定义
interface AlarmRule {
  id?: number
  name: string
  description: string
  diagnosis_type: string
  camera_id?: number
  severity: string
  threshold_config: Record<string, any>
  notification_channels: number[]
  is_enabled: boolean
  created_at?: string
  updated_at?: string
}

interface Camera {
  id: number
  name: string
}

interface NotificationChannel {
  id: number
  name: string
  type: string
}

interface ThresholdItem {
  key: string
  value: number
}

// 响应式数据
const loading = ref(false)
const submitting = ref(false)
const rules = ref<AlarmRule[]>([])
const cameras = ref<Camera[]>([])
const notificationChannels = ref<NotificationChannel[]>([])

// 分页
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)

// 搜索表单
const searchForm = reactive({
  search: '',
  diagnosis_type: '',
  severity: '',
  is_enabled: null as boolean | null
})

// 统计数据
const stats = ref({
  enabled_count: 0,
  critical_count: 0,
  triggered_today: 0,
  total_count: 0
})

// 对话框
const dialogVisible = ref(false)
const isEdit = ref(false)
const formRef = ref()

// 表单数据
const form = reactive<AlarmRule>({
  name: '',
  description: '',
  diagnosis_type: '',
  camera_id: undefined,
  severity: '',
  threshold_config: {},
  notification_channels: [],
  is_enabled: true
})

// 阈值配置项
const thresholdItems = ref<ThresholdItem[]>([{ key: '', value: 0 }])

// 表单验证规则
const formRules = {
  name: [{ required: true, message: '请输入规则名称', trigger: 'blur' }],
  diagnosis_type: [{ required: true, message: '请选择诊断类型', trigger: 'change' }],
  severity: [{ required: true, message: '请选择严重程度', trigger: 'change' }]
}

// 计算属性
const getDiagnosisTypeName = (type: string) => {
  const typeMap: Record<string, string> = {
    BRIGHTNESS: '亮度检测',
    BLUE_SCREEN: '蓝屏检测',
    CLARITY: '清晰度检测',
    SHAKE: '画面抖动',
    FREEZE: '画面冻结',
    COLOR_CAST: '偏色检测',
    OCCLUSION: '遮挡检测',
    NOISE: '噪声检测',
    CONTRAST: '对比度检测',
    MOSAIC: '马赛克检测',
    FLOWER_SCREEN: '花屏检测'
  }
  return typeMap[type] || type
}

const getDiagnosisTypeColor = (type: string) => {
  const colorMap: Record<string, string> = {
    BRIGHTNESS: '',
    BLUE_SCREEN: 'warning',
    CLARITY: 'success',
    SHAKE: 'danger',
    FREEZE: 'danger',
    COLOR_CAST: 'warning',
    OCCLUSION: 'danger',
    NOISE: 'info',
    CONTRAST: '',
    MOSAIC: 'warning',
    FLOWER_SCREEN: 'danger'
  }
  return colorMap[type] || ''
}

const getSeverityName = (severity: string) => {
  const severityMap: Record<string, string> = {
    LOW: '低',
    MEDIUM: '中',
    HIGH: '高',
    CRITICAL: '紧急'
  }
  return severityMap[severity] || severity
}

const getSeverityColor = (severity: string) => {
  const colorMap: Record<string, string> = {
    LOW: 'info',
    MEDIUM: '',
    HIGH: 'warning',
    CRITICAL: 'danger'
  }
  return colorMap[severity] || ''
}

const getCameraName = (cameraId: number) => {
  const camera = cameras.value.find(c => c.id === cameraId)
  return camera?.name || `摄像头${cameraId}`
}

// 方法
const loadRules = async () => {
  loading.value = true
  try {
    // TODO: 调用API获取告警规则列表
    // const response = await alarmRuleApi.getRules({
    //   page: currentPage.value,
    //   size: pageSize.value,
    //   ...searchForm
    // })
    // rules.value = response.data.items
    // total.value = response.data.total
    
    // 模拟数据
    rules.value = [
      {
        id: 1,
        name: '亮度异常告警',
        description: '检测画面亮度异常情况',
        diagnosis_type: 'BRIGHTNESS',
        camera_id: 1,
        severity: 'HIGH',
        threshold_config: { min_brightness: 10, max_brightness: 240 },
        notification_channels: [1, 2],
        is_enabled: true,
        created_at: '2024-01-15 10:30:00'
      }
    ]
    total.value = 1
  } catch (error) {
    ElMessage.error('加载告警规则失败')
  } finally {
    loading.value = false
  }
}

const loadStats = async () => {
  try {
    // TODO: 调用API获取统计数据
    stats.value = {
      enabled_count: 5,
      critical_count: 2,
      triggered_today: 12,
      total_count: 8
    }
  } catch (error) {
    console.error('加载统计数据失败:', error)
  }
}

const loadCameras = async () => {
  try {
    // TODO: 调用API获取摄像头列表
    cameras.value = [
      { id: 1, name: '大门摄像头' },
      { id: 2, name: '停车场摄像头' }
    ]
  } catch (error) {
    console.error('加载摄像头列表失败:', error)
  }
}

const loadNotificationChannels = async () => {
  try {
    // TODO: 调用API获取通知渠道列表
    notificationChannels.value = [
      { id: 1, name: '邮件通知', type: 'email' },
      { id: 2, name: '短信通知', type: 'sms' }
    ]
  } catch (error) {
    console.error('加载通知渠道失败:', error)
  }
}

const handleSearch = () => {
  currentPage.value = 1
  loadRules()
}

const handleReset = () => {
  Object.assign(searchForm, {
    search: '',
    diagnosis_type: '',
    severity: '',
    is_enabled: null
  })
  handleSearch()
}

const handleSizeChange = (size: number) => {
  pageSize.value = size
  loadRules()
}

const handleCurrentChange = (page: number) => {
  currentPage.value = page
  loadRules()
}

const handleCreate = () => {
  isEdit.value = false
  resetForm()
  dialogVisible.value = true
}

const handleEdit = (rule: AlarmRule) => {
  isEdit.value = true
  Object.assign(form, rule)
  
  // 转换阈值配置为编辑格式
  thresholdItems.value = Object.entries(rule.threshold_config || {}).map(([key, value]) => ({
    key,
    value: Number(value)
  }))
  
  if (thresholdItems.value.length === 0) {
    thresholdItems.value = [{ key: '', value: 0 }]
  }
  
  dialogVisible.value = true
}

const handleDelete = async (rule: AlarmRule) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除告警规则"${rule.name}"吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    // TODO: 调用API删除规则
    ElMessage.success('删除成功')
    loadRules()
  } catch (error) {
    // 用户取消删除
  }
}

const handleToggleEnabled = async (rule: AlarmRule) => {
  try {
    // TODO: 调用API切换启用状态
    ElMessage.success(rule.is_enabled ? '规则已启用' : '规则已禁用')
    loadStats()
  } catch (error) {
    ElMessage.error('操作失败')
    rule.is_enabled = !rule.is_enabled // 回滚状态
  }
}

const handleTest = async (rule: AlarmRule) => {
  try {
    // TODO: 调用API测试规则
    ElMessage.success('测试通知已发送')
  } catch (error) {
    ElMessage.error('测试失败')
  }
}

const handleSubmit = async () => {
  try {
    await formRef.value.validate()
    
    // 构建阈值配置
    const thresholdConfig: Record<string, any> = {}
    thresholdItems.value.forEach(item => {
      if (item.key && item.value !== undefined) {
        thresholdConfig[item.key] = item.value
      }
    })
    form.threshold_config = thresholdConfig
    
    submitting.value = true
    
    if (isEdit.value) {
      // TODO: 调用API更新规则
      ElMessage.success('更新成功')
    } else {
      // TODO: 调用API创建规则
      ElMessage.success('创建成功')
    }
    
    dialogVisible.value = false
    loadRules()
    loadStats()
  } catch (error) {
    console.error('提交失败:', error)
  } finally {
    submitting.value = false
  }
}

const handleDialogClose = () => {
  formRef.value?.resetFields()
  resetForm()
}

const resetForm = () => {
  Object.assign(form, {
    name: '',
    description: '',
    diagnosis_type: '',
    camera_id: undefined,
    severity: '',
    threshold_config: {},
    notification_channels: [],
    is_enabled: true
  })
  thresholdItems.value = [{ key: '', value: 0 }]
}

const addThresholdItem = () => {
  thresholdItems.value.push({ key: '', value: 0 })
}

const removeThresholdItem = (index: number) => {
  if (thresholdItems.value.length > 1) {
    thresholdItems.value.splice(index, 1)
  }
}

// 生命周期
onMounted(() => {
  loadRules()
  loadStats()
  loadCameras()
  loadNotificationChannels()
})
</script>

<style scoped>
.alarm-rules {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header-left h2 {
  margin: 0 0 5px 0;
  color: #303133;
}

.page-description {
  margin: 0;
  color: #909399;
  font-size: 14px;
}

.search-filters {
  background: #fff;
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.search-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 15px;
}

.filter-bar {
  display: flex;
  align-items: center;
  gap: 15px;
}

.stats-cards {
  margin-bottom: 20px;
}

.stat-card {
  background: #fff;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  display: flex;
  align-items: center;
}

.stat-icon {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 15px;
  font-size: 24px;
  color: #fff;
}

.stat-icon.enabled {
  background: linear-gradient(135deg, #67c23a, #85ce61);
}

.stat-icon.critical {
  background: linear-gradient(135deg, #f56c6c, #f78989);
}

.stat-icon.triggered {
  background: linear-gradient(135deg, #e6a23c, #ebb563);
}

.stat-icon.total {
  background: linear-gradient(135deg, #409eff, #66b1ff);
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 28px;
  font-weight: bold;
  color: #303133;
  line-height: 1;
}

.stat-label {
  font-size: 14px;
  color: #909399;
  margin-top: 5px;
}

.table-container {
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.rule-name {
  display: flex;
  align-items: center;
  gap: 8px;
}

.rule-name .name {
  font-weight: 500;
}

.threshold-config {
  font-size: 12px;
}

.threshold-item {
  margin-bottom: 2px;
}

.threshold-item .key {
  color: #909399;
  margin-right: 4px;
}

.threshold-item .value {
  font-weight: 500;
}

.text-muted {
  color: #c0c4cc;
}

.pagination-container {
  padding: 20px;
  text-align: right;
}

.threshold-config-editor {
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  padding: 15px;
}

.threshold-config-editor .threshold-item {
  display: flex;
  align-items: center;
  margin-bottom: 10px;
}

.threshold-config-editor .threshold-item:last-child {
  margin-bottom: 0;
}

.dialog-footer {
  text-align: right;
}
</style>