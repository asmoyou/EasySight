<template>
  <div class="diagnosis-tasks">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <h2>诊断任务</h2>
        <p class="page-description">管理视频质量诊断任务，支持多种检测类型和调度配置</p>
      </div>
      <div class="header-right">
        <el-button 
          type="danger" 
          :disabled="selectedTasks.length === 0"
          @click="handleBatchDelete"
        >
          <el-icon><Delete /></el-icon>
          批量删除 ({{ selectedTasks.length }})
        </el-button>
        <el-button type="primary" @click="handleCreate">
          <el-icon><Plus /></el-icon>
          创建任务
        </el-button>
      </div>
    </div>

    <!-- 搜索和筛选 -->
    <div class="search-filters">
      <div class="search-bar">
        <el-input
          v-model="searchForm.search"
          placeholder="搜索任务名称或描述"
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
          <el-option label="亮度检测" value="brightness" />
          <el-option label="蓝屏检查" value="blue_screen" />
          <el-option label="清晰度检查" value="clarity" />
          <el-option label="抖动检查" value="shake" />
          <el-option label="冻结检测" value="freeze" />
          <el-option label="偏色检测" value="color_cast" />
          <el-option label="遮挡检测" value="occlusion" />
          <el-option label="噪声检测" value="noise" />
          <el-option label="对比度检测" value="contrast" />
          <el-option label="马赛克检测" value="mosaic" />
          <el-option label="花屏检测" value="flower_screen" />
        </el-select>
        
        <el-select v-model="searchForm.status" placeholder="任务状态" clearable style="width: 120px">
          <el-option label="待执行" value="pending" />
          <el-option label="运行中" value="running" />
          <el-option label="已完成" value="completed" />
          <el-option label="失败" value="failed" />
          <el-option label="已取消" value="cancelled" />
        </el-select>
        
        <el-select v-model="searchForm.is_active" placeholder="启用状态" clearable style="width: 120px">
          <el-option label="已启用" :value="true" />
          <el-option label="已禁用" :value="false" />
        </el-select>
        
        <el-select v-model="searchForm.is_scheduled" placeholder="调度类型" clearable style="width: 120px">
          <el-option label="定时任务" :value="true" />
          <el-option label="手动任务" :value="false" />
        </el-select>
      </div>
    </div>

    <!-- 任务列表 -->
    <div class="table-container">
      <el-table
        :data="tasks"
        v-loading="loading"
        stripe
        style="width: 100%"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="55" />
        
        <el-table-column prop="name" label="任务名称" min-width="150">
          <template #default="{ row }">
            <div class="task-name">
              <span class="name">{{ row.name }}</span>
              <el-tag v-if="row.template_name" size="small" type="info">{{ row.template_name }}</el-tag>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column prop="diagnosis_types" label="诊断类型" width="120">
          <template #default="{ row }">
            <el-tag :type="getDiagnosisTypeColor(row.diagnosis_types?.[0])" size="small">
              {{ getDiagnosisTypeName(row.diagnosis_types?.[0]) }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusColor(row.status)" size="small">
              {{ getStatusName(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column label="启用状态" width="100">
          <template #default="{ row }">
            <el-switch
              v-model="row.is_active"
              @change="handleToggleActive(row)"
              :loading="row.switching"
            />
          </template>
        </el-table-column>
        
        <el-table-column label="调度" width="80">
          <template #default="{ row }">
            <el-icon v-if="row.is_scheduled" color="#67C23A"><Clock /></el-icon>
            <el-icon v-else color="#909399"><Minus /></el-icon>
          </template>
        </el-table-column>
        
        <el-table-column label="执行统计" width="120">
          <template #default="{ row }">
            <div class="run-stats">
              <span>{{ row.success_count }}/{{ row.run_count }}</span>
              <el-progress
                :percentage="row.run_count > 0 ? Math.round((row.success_count / row.run_count) * 100) : 0"
                :stroke-width="4"
                :show-text="false"
                style="margin-top: 2px"
              />
            </div>
          </template>
        </el-table-column>
        
        <el-table-column prop="last_run" label="最后执行" width="150">
          <template #default="{ row }">
            <span v-if="row.last_run">{{ formatDateTime(row.last_run) }}</span>
            <span v-else class="text-muted">未执行</span>
          </template>
        </el-table-column>
        
        <el-table-column prop="created_by_name" label="创建人" width="100" />
        
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <div class="action-buttons">
              <el-button-group>
                <el-button size="small" @click="handleView(row)">
                  <el-icon><View /></el-icon>
                </el-button>
                <el-button size="small" type="primary" @click="handleEdit(row)">
                  <el-icon><Edit /></el-icon>
                </el-button>
                <el-button 
                  size="small" 
                  type="success" 
                  @click="handleRun(row)"
                  :disabled="row.status === 'running'"
                >
                  <el-icon><VideoPlay /></el-icon>
                </el-button>
              </el-button-group>
              <el-dropdown trigger="click" @command="(command) => handleDropdownCommand(command, row)">
                <el-button size="small" type="info">
                  <el-icon><MoreFilled /></el-icon>
                </el-button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item command="delete" :icon="Delete" class="danger-item">删除</el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>
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
      :title="dialogMode === 'create' ? '创建诊断任务' : '编辑诊断任务'"
      width="800px"
      @close="handleDialogClose"
    >
      <el-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-width="120px"
      >
        <el-form-item label="任务名称" prop="name">
          <el-input v-model="formData.name" placeholder="请输入任务名称" />
        </el-form-item>
        
        <el-form-item label="诊断类型" prop="diagnosis_type">
          <el-select 
            v-model="formData.diagnosis_type" 
            placeholder="请选择诊断类型" 
            style="width: 100%"
            :key="`diagnosis-${currentTaskId}`"
          >
            <el-option label="亮度检测" value="brightness" />
            <el-option label="蓝屏检查" value="blue_screen" />
            <el-option label="清晰度检查" value="clarity" />
            <el-option label="抖动检查" value="shake" />
            <el-option label="冻结检测" value="freeze" />
            <el-option label="偏色检测" value="color_cast" />
            <el-option label="遮挡检测" value="occlusion" />
            <el-option label="噪声检测" value="noise" />
            <el-option label="对比度检测" value="contrast" />
            <el-option label="马赛克检测" value="mosaic" />
            <el-option label="花屏检测" value="flower_screen" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="目标摄像头" prop="target_id">
          <el-select 
            v-model="formData.target_id" 
            placeholder="请选择摄像头" 
            style="width: 100%"
            :key="`camera-${currentTaskId}`"
          >
            <el-option
              v-for="camera in cameras"
              :key="camera.id"
              :label="camera.name"
              :value="camera.id"
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="诊断模板">
          <el-select 
            v-model="formData.template_id" 
            placeholder="选择模板（可选）" 
            clearable 
            style="width: 100%"
            :key="`template-${currentTaskId}`"
          >
            <el-option
              v-for="template in templates"
              :key="template.id"
              :label="template.name"
              :value="template.id"
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="是否定时任务">
          <el-switch v-model="formData.is_scheduled" @change="handleScheduleChange" />
        </el-form-item>
        
        <el-form-item v-if="formData.is_scheduled" label="调度配置">
          <el-input
            v-model="scheduleConfig.cron_expression"
            placeholder="Cron表达式，如：0 0 * * * 表示每小时执行"
          />
          <div class="form-tip">支持标准Cron表达式格式</div>
        </el-form-item>
        
        <el-form-item label="任务描述">
          <el-input
            v-model="formData.description"
            type="textarea"
            :rows="3"
            placeholder="请输入任务描述"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSave" :loading="saving">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Refresh, Plus, Clock, Minus, View, Edit, VideoPlay, MoreFilled, Delete } from '@element-plus/icons-vue'
import { diagnosisTaskApi, diagnosisTemplateApi, type DiagnosisTask, type DiagnosisTaskCreate, DiagnosisType, TaskStatus } from '@/api/diagnosis'
import { cameraApi, type Camera } from '@/api/cameras'
import { formatDateTime } from '@/utils/date'

// 路由
const router = useRouter()

// 响应式数据
const loading = ref(false)
const saving = ref(false)
const tasks = ref<DiagnosisTask[]>([])
const cameras = ref<Camera[]>([])
const templates = ref([])
const selectedTasks = ref<DiagnosisTask[]>([])

// 分页
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)

// 搜索表单
const searchForm = reactive({
  search: '',
  diagnosis_type: '',
  status: '',
  is_active: null as boolean | null,
  is_scheduled: null as boolean | null
})

// 对话框
const dialogVisible = ref(false)
const dialogMode = ref<'create' | 'edit'>('create')
const currentTask = ref<DiagnosisTask | null>(null)
const currentTaskId = ref<number | null>(null)

// 表单数据
const formData = ref<DiagnosisTaskCreate>({
  name: '',
  diagnosis_type: DiagnosisType.BRIGHTNESS,
  target_id: 0,
  target_type: 'camera',
  template_id: undefined,
  config: {},
  schedule_config: {},
  threshold_config: {},
  is_scheduled: false,
  description: ''
})

const scheduleConfig = ref({
  cron_expression: '0 0 * * *'
})

// 表单验证规则
const formRules = {
  name: [{ required: true, message: '请输入任务名称', trigger: 'blur' }],
  diagnosis_type: [{ required: true, message: '请选择诊断类型', trigger: 'change' }],
  target_id: [{ required: true, message: '请选择目标摄像头', trigger: 'change' }]
}

const formRef = ref()

// 计算属性
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

// 方法
const loadTasks = async () => {
  try {
    loading.value = true
    const params = {
      page: currentPage.value,
      page_size: pageSize.value,
      ...searchForm
    }
    
    // 过滤空值
    Object.keys(params).forEach(key => {
      if (params[key] === '' || params[key] === null) {
        delete params[key]
      }
    })
    
    const response = await diagnosisTaskApi.getTasks(params)
    const data = response.data
    tasks.value = data?.tasks || []
    total.value = data?.total || 0
  } catch (error) {
    console.error('加载任务列表失败:', error)
    ElMessage.error('加载任务列表失败')
  } finally {
    loading.value = false
  }
}

const loadCameras = async () => {
  try {
    const response = await cameraApi.getCameras({ page_size: 100 })
    cameras.value = response.data?.cameras || []
  } catch (error) {
    console.error('加载摄像头列表失败:', error)
  }
}

const loadTemplates = async () => {
  try {
    console.log('开始加载模板数据...')
    const response = await diagnosisTemplateApi.getTemplates({ page_size: 100 })
    console.log('API响应:', response)
    console.log('响应数据:', response.data)
    
    // 后端返回的数据结构是 { items: [], total: number, ... }
    if (response.data && response.data.items) {
      templates.value = response.data.items
      console.log('成功加载模板:', templates.value.length, '个')
      console.log('模板列表:', templates.value)
    } else {
      templates.value = []
      console.warn('未找到模板数据或数据格式不正确')
    }
  } catch (error) {
    console.error('加载模板列表失败:', error)
    console.error('错误详情:', error.response || error.message)
    ElMessage.error('加载模板列表失败: ' + (error.message || '未知错误'))
    templates.value = []
  }
}

const handleSearch = () => {
  currentPage.value = 1
  loadTasks()
}

const handleReset = () => {
  Object.assign(searchForm, {
    search: '',
    diagnosis_type: '',
    status: '',
    is_active: null,
    is_scheduled: null
  })
  currentPage.value = 1
  loadTasks()
}

const handleSizeChange = (size: number) => {
  pageSize.value = size
  currentPage.value = 1
  loadTasks()
}

const handleCurrentChange = (page: number) => {
  currentPage.value = page
  loadTasks()
}

const handleSelectionChange = (selection: DiagnosisTask[]) => {
  selectedTasks.value = selection
}

const handleCreate = () => {
  dialogMode.value = 'create'
  currentTask.value = null
  currentTaskId.value = null
  resetForm()
  dialogVisible.value = true
}

const handleEdit = async (task: DiagnosisTask) => {
  dialogMode.value = 'edit'
  currentTask.value = task
  currentTaskId.value = task.id
  
  console.log('原始任务数据 - name:', task.name, 'diagnosis_type:', task.diagnosis_type, 'target_id:', task.target_id, 'template_id:', task.template_id)
  
  // 确保相机列表已加载
  if (cameras.value.length === 0) {
    console.log('相机列表为空，重新加载相机数据')
    await loadCameras()
  }
  
  // 重置表单数据
  // 处理诊断类型：可能是单个值或数组的第一个元素
  const diagnosisType = task.diagnosis_type || (task.diagnosis_types && task.diagnosis_types[0]) || DiagnosisType.BRIGHTNESS
  
  formData.value = {
    name: task.name,
    diagnosis_type: diagnosisType as DiagnosisType,
    target_id: task.target_id !== null && task.target_id !== undefined && !isNaN(Number(task.target_id)) ? Number(task.target_id) : null,
    target_type: task.target_type,
    template_id: task.template_id || undefined,
    config: task.config || {},
    schedule_config: task.schedule_config || {},
    threshold_config: task.threshold_config || {},
    is_scheduled: task.is_scheduled || false,
    description: task.description || ''
  }
  
  if (task.schedule_config?.cron_expression) {
    scheduleConfig.value.cron_expression = task.schedule_config.cron_expression
  } else {
    scheduleConfig.value.cron_expression = '0 0 * * *'
  }
  
  console.log('设置后的formData - name:', formData.value.name, 'diagnosis_type:', formData.value.diagnosis_type, 'target_id:', formData.value.target_id)
  
  // 等待DOM更新后再显示对话框
  await nextTick()
  dialogVisible.value = true
  
  // 再次确保数据正确设置并强制更新选择框
  await nextTick()
  console.log('对话框打开后的formData - target_id:', formData.value.target_id)
  
  // 强制更新选择框显示
  await nextTick()
}

const handleView = (task: DiagnosisTask) => {
  router.push(`/diagnosis/tasks/${task.id}`)
}

const handleRun = async (task: DiagnosisTask) => {
  try {
    await ElMessageBox.confirm(
      `确定要执行诊断任务 "${task.name}" 吗？`,
      '确认执行',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await diagnosisTaskApi.runTask(task.id)
    ElMessage.success('任务执行成功')
    loadTasks()
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('执行任务失败:', error)
      ElMessage.error('执行任务失败')
    }
  }
}

const handleDelete = async (task: DiagnosisTask) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除诊断任务 "${task.name}" 吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await diagnosisTaskApi.deleteTask(task.id)
    ElMessage.success('删除成功')
    loadTasks()
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('删除任务失败:', error)
      ElMessage.error('删除失败')
    }
  }
}

const handleBatchDelete = async () => {
  if (selectedTasks.value.length === 0) {
    ElMessage.warning('请先选择要删除的任务')
    return
  }
  
  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${selectedTasks.value.length} 个诊断任务吗？`,
      '确认批量删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    const taskIds = selectedTasks.value.map(task => task.id)
    const response = await diagnosisTaskApi.batchDeleteTasks(taskIds)
    
    if (response.data.deleted_count > 0) {
      ElMessage.success(`成功删除 ${response.data.deleted_count} 个任务`)
    }
    
    if (response.data.not_found_ids.length > 0) {
      ElMessage.warning(`${response.data.not_found_ids.length} 个任务未找到或已被删除`)
    }
    
    selectedTasks.value = []
    loadTasks()
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('批量删除任务失败:', error)
      ElMessage.error('批量删除失败')
    }
  }
}

const handleToggleActive = async (task: DiagnosisTask) => {
  try {
    console.log('切换任务状态:', task.id, '前端显示状态:', task.is_active, '将传递给后端:', task.is_active)
    
    // 修复：直接传递当前的is_active状态，而不是取反
    // 因为前端显示的状态与数据库状态相反，所以直接传递当前状态就是正确的目标状态
    const newStatus = task.is_active
    const response = await diagnosisTaskApi.toggleTask(task.id, newStatus)
    console.log('API响应:', response)
    
    // 立即更新本地状态，确保UI响应
    const index = tasks.value.findIndex(t => t.id === task.id)
    if (index !== -1) {
      console.log('更新前状态:', tasks.value[index].is_active)
      // 修复：由于我们传递的是当前状态，所以本地状态应该取反
      tasks.value[index].is_active = !task.is_active
      console.log('更新后状态:', tasks.value[index].is_active)
      
      // 如果API返回了完整的任务数据，则使用API数据
      if (response.data && response.data.is_active !== undefined) {
        tasks.value[index] = { ...tasks.value[index], ...response.data }
        console.log('使用API返回数据更新:', response.data)
      }
    }
    
    ElMessage.success(newStatus ? '任务已启用' : '任务已禁用')
    
    console.log('状态切换完成，当前任务列表状态:')
    tasks.value.forEach(t => {
      if (t.id === task.id) {
        console.log(`任务 ${t.id}: ${t.is_active ? '启用' : '禁用'}`)
      }
    })
  } catch (error) {
    console.error('切换任务状态失败:', error)
    ElMessage.error('操作失败')
    
    // 发生错误时重新加载任务列表
    await loadTasks()
  }
}

const handleDropdownCommand = (command: string, task: DiagnosisTask) => {
  switch (command) {
    case 'delete':
      handleDelete(task)
      break
  }
}

const handleScheduleChange = (value: boolean) => {
  if (value) {
    formData.value.schedule_config = {
      cron_expression: scheduleConfig.value.cron_expression
    }
  } else {
    formData.value.schedule_config = {}
  }
}

const handleSave = async () => {
  try {
    await formRef.value?.validate()
    saving.value = true
    
    // 无论是否开启定时任务，都要保存 cron 表达式配置
    // 这样用户配置的 cron 表达式不会丢失
    if (formData.value.is_scheduled) {
      formData.value.schedule_config = {
        cron_expression: scheduleConfig.value.cron_expression
      }
    } else {
      // 即使没有开启定时任务，也要保存 cron 表达式到 schedule_config
      // 这样下次开启定时任务时，之前配置的表达式仍然有效
      formData.value.schedule_config = {
        ...formData.value.schedule_config,
        cron_expression: scheduleConfig.value.cron_expression
      }
    }
    
    if (dialogMode.value === 'create') {
      await diagnosisTaskApi.createTask(formData.value)
      ElMessage.success('创建成功')
    } else if (currentTask.value) {
      await diagnosisTaskApi.updateTask(currentTask.value.id, formData.value)
      ElMessage.success('更新成功')
    }
    
    dialogVisible.value = false
    loadTasks()
  } catch (error) {
    console.error('保存失败:', error)
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

const handleDialogClose = () => {
  resetForm()
}

const resetForm = () => {
  formData.value = {
    name: '',
    diagnosis_type: DiagnosisType.BRIGHTNESS,
    target_id: 0,
    target_type: 'camera',
    template_id: undefined,
    config: {},
    schedule_config: {},
    threshold_config: {},
    is_scheduled: false,
    description: ''
  }
  scheduleConfig.value.cron_expression = '0 0 * * *'
  formRef.value?.clearValidate()
}

// 生命周期
onMounted(() => {
  loadTasks()
  loadCameras()
  loadTemplates()
})
</script>

<style scoped>
.diagnosis-tasks {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
}

.header-left h2 {
  margin: 0 0 8px 0;
  font-size: 24px;
  font-weight: 600;
}

.page-description {
  margin: 0;
  color: #666;
  font-size: 14px;
}

.search-filters {
  background: #fff;
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 20px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.search-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}

.filter-bar {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.table-container {
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.task-name {
  display: flex;
  align-items: center;
  gap: 8px;
}

.task-name .name {
  font-weight: 500;
}

.run-stats {
  font-size: 12px;
}

.text-muted {
  color: #999;
}

.pagination-container {
  padding: 20px;
  text-align: right;
}

.form-tip {
  font-size: 12px;
  color: #999;
  margin-top: 4px;
}

.action-buttons {
  display: flex;
  align-items: center;
  gap: 8px;
  justify-content: flex-start;
}

.action-buttons .el-button-group {
  display: flex;
}

.action-buttons .el-button {
  min-width: auto;
  padding: 5px 8px;
}

.action-buttons .el-dropdown .el-button {
  padding: 5px 8px;
}

/* 删除按钮危险样式 */
.el-dropdown-menu .danger-item {
  color: #f56c6c !important;
}

.el-dropdown-menu .danger-item:hover {
  background-color: #fef0f0 !important;
  color: #f56c6c !important;
}

.el-dropdown-menu .danger-item .el-icon {
  color: #f56c6c !important;
}

.el-dropdown-menu .danger-item span {
  color: #f56c6c !important;
}
</style>