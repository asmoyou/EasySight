<template>
  <div class="event-rules">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <h2>事件规则</h2>
        <p class="page-description">配置和管理事件触发规则，自动化事件处理流程</p>
      </div>
      <div class="header-right">
        <el-button type="primary" @click="showCreateDialog">
          <el-icon><Plus /></el-icon>
          新建规则
        </el-button>
      </div>
    </div>

    <!-- 搜索筛选 -->
    <el-card class="search-card" shadow="never">
      <el-form :model="searchForm" inline>
        <el-form-item label="规则名称">
          <el-input
            v-model="searchForm.name"
            placeholder="请输入规则名称"
            clearable
            style="width: 200px"
          />
        </el-form-item>
        <el-form-item label="诊断类型">
          <el-select v-model="searchForm.diagnosis_type" placeholder="请选择诊断类型" clearable>
            <el-option label="摄像头离线" value="camera_offline" />
            <el-option label="视频质量异常" value="video_quality" />
            <el-option label="运动检测" value="motion_detection" />
            <el-option label="人脸识别" value="face_recognition" />
          </el-select>
        </el-form-item>
        <el-form-item label="规则状态">
          <el-select v-model="searchForm.is_enabled" placeholder="请选择状态" clearable>
            <el-option label="启用" :value="true" />
            <el-option label="禁用" :value="false" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">
            <el-icon><Search /></el-icon>
            搜索
          </el-button>
          <el-button @click="handleReset">
            <el-icon><RefreshLeft /></el-icon>
            重置
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 规则列表 -->
    <el-card class="table-card" shadow="never">
      <el-table
        v-loading="loading"
        :data="rules"
        stripe
      >
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" label="规则名称" min-width="150" />
        <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
        <el-table-column prop="diagnosis_types" label="诊断类型" width="150">
          <template #default="{ row }">
            <el-tag v-for="type in row.diagnosis_types" :key="type" :type="getDiagnosisTypeColor(type)" style="margin-right: 4px;">
              {{ getDiagnosisTypeName(type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="severity_level" label="严重程度" width="120">
          <template #default="{ row }">
            <el-tag :type="getSeverityLevelColor(row.severity_level)">
              {{ getSeverityLevelText(row.severity_level) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="frequency_limit" label="频率限制" width="100" />
        <el-table-column prop="is_enabled" label="状态" width="100">
          <template #default="{ row }">
            <el-switch
              v-model="row.is_enabled"
              @change="toggleRule(row)"
            />
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="editRule(row)">
              编辑
            </el-button>
            <el-button type="info" size="small" @click="testRule(row)">
              测试
            </el-button>
            <el-button type="danger" size="small" @click="deleteRule(row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :total="pagination.total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <!-- 新建/编辑规则对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑规则' : '新建规则'"
      width="800px"
      destroy-on-close
    >
      <el-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-width="120px"
      >
        <el-form-item label="规则名称" prop="name">
          <el-input v-model="formData.name" placeholder="请输入规则名称" />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input
            v-model="formData.description"
            type="textarea"
            :rows="3"
            placeholder="请输入规则描述"
          />
        </el-form-item>
        <el-form-item label="诊断类型" prop="diagnosis_types">
          <el-select v-model="formData.diagnosis_types" placeholder="请选择诊断类型" multiple>
            <el-option label="摄像头离线" value="camera_offline" />
            <el-option label="视频质量异常" value="video_quality" />
            <el-option label="运动检测" value="motion_detection" />
            <el-option label="人脸识别" value="face_recognition" />
          </el-select>
        </el-form-item>
        <el-form-item label="严重程度" prop="severity_level">
          <el-select v-model="formData.severity_level" placeholder="请选择严重程度">
            <el-option label="低" value="low" />
            <el-option label="中" value="medium" />
            <el-option label="高" value="high" />
            <el-option label="紧急" value="critical" />
          </el-select>
        </el-form-item>
        <el-form-item label="频率限制" prop="frequency_limit">
          <el-input-number
            v-model="formData.frequency_limit"
            :min="0"
            placeholder="每小时最大触发次数"
          />
        </el-form-item>
        <el-form-item label="优先级" prop="priority">
          <el-input-number
            v-model="formData.priority"
            :min="1"
            :max="10"
            placeholder="请输入优先级"
          />
        </el-form-item>
        <el-form-item label="启用状态">
          <el-switch v-model="formData.is_enabled" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitForm">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, RefreshLeft } from '@element-plus/icons-vue'
import type { FormInstance, FormRules } from 'element-plus'
import { alarmRulesApi, type AlarmRule, type AlarmRuleCreate, type AlarmRuleUpdate } from '@/api/alarm-rules'

// 类型定义
interface EventRuleForm {
  name: string
  description: string
  diagnosis_types: string[]
  camera_ids: number[]
  camera_groups: string[]
  severity_level: string
  threshold_config: Record<string, any>
  frequency_limit: number
  notification_channels: number[]
  notification_template: string
  priority: number
  is_enabled: boolean
}

// 响应式数据
const loading = ref(false)
const rules = ref<AlarmRule[]>([])
const dialogVisible = ref(false)
const isEdit = ref(false)
const formRef = ref<FormInstance>()

// 搜索表单
const searchForm = reactive({
  name: '',
  diagnosis_type: '',
  is_enabled: undefined as boolean | undefined
})

// 表单数据
const formData = reactive<EventRuleForm>({
  name: '',
  description: '',
  diagnosis_types: [],
  camera_ids: [],
  camera_groups: [],
  severity_level: '',
  threshold_config: {},
  frequency_limit: 0,
  notification_channels: [],
  notification_template: '',
  priority: 5,
  is_enabled: true
})

// 表单验证规则
const formRules: FormRules = {
  name: [{ required: true, message: '请输入规则名称', trigger: 'blur' }],
  description: [{ required: true, message: '请输入规则描述', trigger: 'blur' }],
  diagnosis_types: [{ required: true, message: '请选择诊断类型', trigger: 'change' }],
  severity_level: [{ required: true, message: '请选择严重程度级别', trigger: 'change' }]
}

// 分页
const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

// 方法
const loadRules = async () => {
  loading.value = true
  try {
    const response = await alarmRulesApi.getAlarmRules({
      page: pagination.page,
      page_size: pagination.pageSize,
      is_enabled: searchForm.is_enabled,
      diagnosis_type: searchForm.diagnosis_type || undefined
    })
    
    rules.value = response.data || response as any
    pagination.total = response.total || (response as any).length || 0
  } catch (error) {
    console.error('加载规则列表失败:', error)
    ElMessage.error('加载规则列表失败')
    
    // 备用模拟数据
    const mockRules: AlarmRule[] = [
      {
        id: 1,
        name: '摄像头离线告警规则',
        description: '当摄像头离线时自动发送通知',
        diagnosis_types: ['camera_offline'],
        camera_ids: [],
        camera_groups: [],
        severity_level: 'high',
        threshold_config: { duration: 300 },
        frequency_limit: 5,
        notification_channels: [1],
        notification_template: 'camera_offline_template',
        priority: 8,
        is_enabled: true,
        trigger_count: 0,
        created_at: '2024-01-15 10:00:00',
        updated_at: '2024-01-15 10:00:00'
      }
    ]
    
    rules.value = mockRules
    pagination.total = mockRules.length
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  pagination.page = 1
  loadRules()
}

const handleReset = () => {
  searchForm.name = ''
  searchForm.diagnosis_type = ''
  searchForm.is_enabled = undefined
  pagination.page = 1
  loadRules()
}

const handleSizeChange = (size: number) => {
  pagination.pageSize = size
  pagination.page = 1
  loadRules()
}

const handleCurrentChange = (page: number) => {
  pagination.page = page
  loadRules()
}

const showCreateDialog = () => {
  isEdit.value = false
  resetForm()
  dialogVisible.value = true
}

const editRule = (rule: AlarmRule) => {
  isEdit.value = true
  Object.assign(formData, {
    name: rule.name,
    description: rule.description || '',
    diagnosis_types: rule.diagnosis_types,
    camera_ids: rule.camera_ids,
    camera_groups: rule.camera_groups,
    severity_level: rule.severity_level,
    threshold_config: rule.threshold_config,
    frequency_limit: rule.frequency_limit,
    notification_channels: rule.notification_channels,
    notification_template: rule.notification_template || '',
    priority: rule.priority,
    is_enabled: rule.is_enabled
  })
  dialogVisible.value = true
}

const toggleRule = async (rule: AlarmRule) => {
  try {
    await alarmRulesApi.toggleAlarmRule(rule.id, rule.is_enabled)
    ElMessage.success(`规则已${rule.is_enabled ? '启用' : '禁用'}`)
  } catch (error) {
    console.error('切换规则状态失败:', error)
    ElMessage.error('操作失败')
    rule.is_enabled = !rule.is_enabled // 回滚状态
  }
}

const testRule = async (rule: AlarmRule) => {
  try {
    await alarmRulesApi.testAlarmRule(rule.id)
    ElMessage.success('规则测试成功')
  } catch (error) {
    console.error('测试规则失败:', error)
    ElMessage.error('规则测试失败')
  }
}

const deleteRule = async (rule: AlarmRule) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除规则 "${rule.name}" 吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await alarmRulesApi.deleteAlarmRule(rule.id)
    ElMessage.success('删除成功')
    loadRules()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除规则失败:', error)
      ElMessage.error('删除失败')
    }
  }
}

const submitForm = async () => {
  if (!formRef.value) return
  
  try {
    await formRef.value.validate()
    
    if (isEdit.value) {
      // 更新规则 - 需要获取当前编辑的规则ID
      const currentRule = rules.value.find(r => r.name === formData.name)
      if (currentRule) {
        await alarmRulesApi.updateAlarmRule(currentRule.id, formData as AlarmRuleUpdate)
        ElMessage.success('更新成功')
      }
    } else {
      await alarmRulesApi.createAlarmRule(formData as AlarmRuleCreate)
      ElMessage.success('创建成功')
    }
    
    dialogVisible.value = false
    loadRules()
  } catch (error) {
    console.error('提交表单失败:', error)
    if (error.response?.data?.detail) {
      ElMessage.error(error.response.data.detail)
    } else {
      ElMessage.error(isEdit.value ? '更新失败' : '创建失败')
    }
  }
}

const resetForm = () => {
  Object.assign(formData, {
    name: '',
    description: '',
    diagnosis_types: [],
    camera_ids: [],
    camera_groups: [],
    severity_level: '',
    threshold_config: {},
    frequency_limit: 0,
    notification_channels: [],
    notification_template: '',
    priority: 5,
    is_enabled: true
  })
}

// 辅助函数
const getDiagnosisTypeColor = (type: string) => {
  const colors: Record<string, string> = {
    camera_offline: 'danger',
    video_quality: 'warning',
    motion_detection: 'info',
    face_recognition: 'success'
  }
  return colors[type] || 'info'
}

const getDiagnosisTypeName = (type: string) => {
  const names: Record<string, string> = {
    camera_offline: '摄像头离线',
    video_quality: '视频质量异常',
    motion_detection: '运动检测',
    face_recognition: '人脸识别'
  }
  return names[type] || type
}

const getSeverityLevelColor = (level: string) => {
  const colors: Record<string, string> = {
    low: 'info',
    medium: 'warning',
    high: 'danger',
    critical: 'danger'
  }
  return colors[level] || 'info'
}

const getSeverityLevelName = (level: string) => {
  const names: Record<string, string> = {
    low: '低',
    medium: '中',
    high: '高',
    critical: '紧急'
  }
  return names[level] || level
}

const formatDateTime = (dateTime: string) => {
  return dateTime
}

// 生命周期
onMounted(() => {
  loadRules()
})
</script>

<style scoped>
.event-rules {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header-left h2 {
  margin: 0;
  color: #303133;
}

.page-description {
  margin: 5px 0 0 0;
  color: #909399;
  font-size: 14px;
}

.search-card {
  margin-bottom: 20px;
}

.table-card {
  margin-bottom: 20px;
}

.pagination-wrapper {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}
</style>