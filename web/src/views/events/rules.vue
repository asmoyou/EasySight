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
        <el-form-item label="事件类型">
          <el-select v-model="searchForm.event_type" placeholder="请选择事件类型" clearable>
            <el-option label="告警事件" value="alarm" />
            <el-option label="系统事件" value="system" />
            <el-option label="用户事件" value="user" />
            <el-option label="设备事件" value="device" />
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
        <el-table-column prop="event_type" label="事件类型" width="120">
          <template #default="{ row }">
            <el-tag :type="getEventTypeColor(row.event_type)">
              {{ getEventTypeName(row.event_type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="trigger_condition" label="触发条件" min-width="200" show-overflow-tooltip />
        <el-table-column prop="action_type" label="动作类型" width="120">
          <template #default="{ row }">
            <el-tag :type="getActionTypeColor(row.action_type)">
              {{ getActionTypeName(row.action_type) }}
            </el-tag>
          </template>
        </el-table-column>
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
        <el-form-item label="事件类型" prop="event_type">
          <el-select v-model="formData.event_type" placeholder="请选择事件类型">
            <el-option label="告警事件" value="alarm" />
            <el-option label="系统事件" value="system" />
            <el-option label="用户事件" value="user" />
            <el-option label="设备事件" value="device" />
          </el-select>
        </el-form-item>
        <el-form-item label="触发条件" prop="trigger_condition">
          <el-input
            v-model="formData.trigger_condition"
            type="textarea"
            :rows="3"
            placeholder="请输入触发条件，支持JSON格式"
          />
        </el-form-item>
        <el-form-item label="动作类型" prop="action_type">
          <el-select v-model="formData.action_type" placeholder="请选择动作类型">
            <el-option label="发送通知" value="notification" />
            <el-option label="执行脚本" value="script" />
            <el-option label="调用API" value="api" />
            <el-option label="记录日志" value="log" />
          </el-select>
        </el-form-item>
        <el-form-item label="动作配置" prop="action_config">
          <el-input
            v-model="formData.action_config"
            type="textarea"
            :rows="4"
            placeholder="请输入动作配置，支持JSON格式"
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

// 类型定义
interface EventRule {
  id: number
  name: string
  description: string
  event_type: string
  trigger_condition: string
  action_type: string
  action_config: string
  priority: number
  is_enabled: boolean
  created_at: string
  updated_at: string
}

interface EventRuleForm {
  name: string
  description: string
  event_type: string
  trigger_condition: string
  action_type: string
  action_config: string
  priority: number
  is_enabled: boolean
}

// 响应式数据
const loading = ref(false)
const rules = ref<EventRule[]>([])
const dialogVisible = ref(false)
const isEdit = ref(false)
const formRef = ref<FormInstance>()

// 搜索表单
const searchForm = reactive({
  name: '',
  event_type: '',
  is_enabled: undefined as boolean | undefined
})

// 表单数据
const formData = reactive<EventRuleForm>({
  name: '',
  description: '',
  event_type: '',
  trigger_condition: '',
  action_type: '',
  action_config: '',
  priority: 5,
  is_enabled: true
})

// 表单验证规则
const formRules: FormRules = {
  name: [{ required: true, message: '请输入规则名称', trigger: 'blur' }],
  description: [{ required: true, message: '请输入规则描述', trigger: 'blur' }],
  event_type: [{ required: true, message: '请选择事件类型', trigger: 'change' }],
  trigger_condition: [{ required: true, message: '请输入触发条件', trigger: 'blur' }],
  action_type: [{ required: true, message: '请选择动作类型', trigger: 'change' }],
  action_config: [{ required: true, message: '请输入动作配置', trigger: 'blur' }]
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
    // 模拟数据
    const mockRules: EventRule[] = [
      {
        id: 1,
        name: '摄像头离线告警规则',
        description: '当摄像头离线时自动发送通知',
        event_type: 'alarm',
        trigger_condition: '{"type": "camera_offline", "duration": ">5min"}',
        action_type: 'notification',
        action_config: '{"channels": ["email", "sms"], "template": "camera_offline"}',
        priority: 8,
        is_enabled: true,
        created_at: '2024-01-15 10:00:00',
        updated_at: '2024-01-15 10:00:00'
      },
      {
        id: 2,
        name: '系统启动日志记录',
        description: '系统启动时记录日志',
        event_type: 'system',
        trigger_condition: '{"type": "system_start"}',
        action_type: 'log',
        action_config: '{"level": "info", "message": "System started successfully"}',
        priority: 3,
        is_enabled: true,
        created_at: '2024-01-15 09:00:00',
        updated_at: '2024-01-15 09:00:00'
      }
    ]
    
    rules.value = mockRules
    pagination.total = mockRules.length
  } catch (error) {
    ElMessage.error('加载规则列表失败')
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
  searchForm.event_type = ''
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

const editRule = (rule: EventRule) => {
  isEdit.value = true
  Object.assign(formData, {
    name: rule.name,
    description: rule.description,
    event_type: rule.event_type,
    trigger_condition: rule.trigger_condition,
    action_type: rule.action_type,
    action_config: rule.action_config,
    priority: rule.priority,
    is_enabled: rule.is_enabled
  })
  dialogVisible.value = true
}

const toggleRule = async (rule: EventRule) => {
  try {
    ElMessage.success(`规则已${rule.is_enabled ? '启用' : '禁用'}`)
  } catch (error) {
    ElMessage.error('操作失败')
    rule.is_enabled = !rule.is_enabled // 回滚状态
  }
}

const testRule = async (rule: EventRule) => {
  try {
    ElMessage.success('规则测试成功')
  } catch (error) {
    ElMessage.error('规则测试失败')
  }
}

const deleteRule = async (rule: EventRule) => {
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
    
    ElMessage.success('删除成功')
    loadRules()
  } catch (error) {
    // 用户取消删除
  }
}

const submitForm = async () => {
  if (!formRef.value) return
  
  try {
    await formRef.value.validate()
    
    if (isEdit.value) {
      ElMessage.success('更新成功')
    } else {
      ElMessage.success('创建成功')
    }
    
    dialogVisible.value = false
    loadRules()
  } catch (error) {
    ElMessage.error('表单验证失败')
  }
}

const resetForm = () => {
  Object.assign(formData, {
    name: '',
    description: '',
    event_type: '',
    trigger_condition: '',
    action_type: '',
    action_config: '',
    priority: 5,
    is_enabled: true
  })
}

// 辅助函数
const getEventTypeColor = (type: string) => {
  const colors: Record<string, string> = {
    alarm: 'danger',
    system: 'info',
    user: 'success',
    device: 'warning'
  }
  return colors[type] || 'info'
}

const getEventTypeName = (type: string) => {
  const names: Record<string, string> = {
    alarm: '告警事件',
    system: '系统事件',
    user: '用户事件',
    device: '设备事件'
  }
  return names[type] || type
}

const getActionTypeColor = (type: string) => {
  const colors: Record<string, string> = {
    notification: 'primary',
    script: 'warning',
    api: 'success',
    log: 'info'
  }
  return colors[type] || 'info'
}

const getActionTypeName = (type: string) => {
  const names: Record<string, string> = {
    notification: '发送通知',
    script: '执行脚本',
    api: '调用API',
    log: '记录日志'
  }
  return names[type] || type
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