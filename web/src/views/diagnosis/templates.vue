<template>
  <div class="diagnosis-templates">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <h2>诊断模板</h2>
        <p class="page-description">管理诊断任务模板，预设常用的诊断配置和参数</p>
      </div>
      <div class="header-right">
        <el-button type="primary" @click="handleCreate">
          <el-icon><Plus /></el-icon>
          创建模板
        </el-button>
      </div>
    </div>

    <!-- 搜索和筛选 -->
    <div class="search-filters">
      <div class="search-bar">
        <el-input
          v-model="searchForm.search"
          placeholder="搜索模板名称或描述"
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
        
        <el-select v-model="searchForm.is_active" placeholder="启用状态" clearable style="width: 120px">
          <el-option label="已启用" :value="true" />
          <el-option label="已禁用" :value="false" />
        </el-select>
      </div>
    </div>

    <!-- 模板列表 -->
    <div class="template-grid">
      <div v-for="template in templates" :key="template.id" class="template-card">
        <div class="card-header">
          <div class="template-info">
            <h3 class="template-name">{{ template.name }}</h3>
            <el-tag 
              v-for="type in template.diagnosis_types" 
              :key="type" 
              :type="getDiagnosisTypeColor(type)" 
              size="small"
              style="margin-right: 4px"
            >
              {{ getDiagnosisTypeName(type) }}
            </el-tag>
          </div>
          <div class="template-actions">
            <el-switch
              v-model="template.is_active"
              @change="handleToggleActive(template)"
              :loading="template.switching"
            />
          </div>
        </div>
        
        <div class="card-content">
          <p class="template-description">{{ template.description || '暂无描述' }}</p>
          
          <div class="template-config">
            <div class="config-item" v-if="template.default_config?.threshold !== undefined">
              <span class="config-label">阈值:</span>
              <span class="config-value">{{ (template.default_config.threshold * 100).toFixed(1) }}%</span>
            </div>
            <div class="config-item" v-if="template.default_config?.sensitivity !== undefined">
              <span class="config-label">灵敏度:</span>
              <span class="config-value">{{ template.default_config.sensitivity }}</span>
            </div>
            <div class="config-item" v-if="template.default_config?.sample_interval !== undefined">
              <span class="config-label">采样间隔:</span>
              <span class="config-value">{{ template.default_config.sample_interval }}s</span>
            </div>
          </div>
          
          <div class="template-stats">
            <div class="stat-item">
              <span class="stat-label">使用次数:</span>
              <span class="stat-value">{{ template.usage_count || 0 }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">创建时间:</span>
              <span class="stat-value">{{ formatDate(template.created_at) }}</span>
            </div>
          </div>
        </div>
        
        <div class="card-footer">
          <el-button size="small" @click="handleView(template)">查看</el-button>
          <el-button size="small" type="primary" @click="handleEdit(template)">编辑</el-button>
          <el-button size="small" @click="handleCopy(template)">复制</el-button>
          <el-button size="small" type="danger" @click="handleDelete(template)">删除</el-button>
        </div>
      </div>
      
      <!-- 空状态 -->
      <div v-if="templates.length === 0 && !loading" class="empty-state">
        <el-empty description="暂无模板数据">
          <el-button type="primary" @click="handleCreate">创建第一个模板</el-button>
        </el-empty>
      </div>
    </div>

    <!-- 分页 -->
    <div class="pagination-container" v-if="total > 0">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="[12, 24, 48]"
        :total="total"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </div>

    <!-- 创建/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogMode === 'create' ? '创建诊断模板' : '编辑诊断模板'"
      width="800px"
      @close="handleDialogClose"
    >
      <el-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-width="120px"
      >
        <el-form-item label="模板名称" prop="name">
          <el-input v-model="formData.name" placeholder="请输入模板名称" />
        </el-form-item>
        
        <el-form-item label="诊断类型" prop="diagnosis_type">
          <el-select v-model="formData.diagnosis_type" placeholder="请选择诊断类型" style="width: 100%" @change="handleTypeChange">
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
        
        <el-form-item label="模板描述">
          <el-input
            v-model="formData.description"
            type="textarea"
            :rows="3"
            placeholder="请输入模板描述"
          />
        </el-form-item>
        
        <!-- 动态配置项 -->
        <div class="config-section">
          <h4>诊断配置</h4>
          
          <el-form-item label="检测阈值" v-if="showThreshold">
            <el-slider
              v-model="thresholdPercent"
              :min="0"
              :max="100"
              :step="1"
              show-input
              :format-tooltip="(val) => val + '%'"
            />
            <div class="form-tip">低于此阈值将触发告警</div>
          </el-form-item>
          
          <el-form-item label="灵敏度" v-if="showSensitivity">
            <el-select v-model="configForm.sensitivity" placeholder="请选择灵敏度">
              <el-option label="低" value="low" />
              <el-option label="中" value="medium" />
              <el-option label="高" value="high" />
            </el-select>
            <div class="form-tip">检测算法的敏感程度</div>
          </el-form-item>
          
          <el-form-item label="采样间隔" v-if="showSampleInterval">
            <el-input-number
              v-model="configForm.sample_interval"
              :min="1"
              :max="3600"
              :step="1"
              controls-position="right"
            />
            <span style="margin-left: 8px">秒</span>
            <div class="form-tip">视频帧采样的时间间隔</div>
          </el-form-item>
          
          <el-form-item label="检测区域" v-if="showDetectionArea">
            <el-radio-group v-model="configForm.detection_area">
              <el-radio label="full">全画面</el-radio>
              <el-radio label="center">中心区域</el-radio>
              <el-radio label="custom">自定义区域</el-radio>
            </el-radio-group>
            <div class="form-tip">指定检测的画面区域</div>
          </el-form-item>
          
          <el-form-item label="最小持续时间" v-if="showMinDuration">
            <el-input-number
              v-model="configForm.min_duration"
              :min="1"
              :max="300"
              :step="1"
              controls-position="right"
            />
            <span style="margin-left: 8px">秒</span>
            <div class="form-tip">异常状态持续多长时间后触发告警</div>
          </el-form-item>
        </div>
        
        <!-- 告警配置 -->
        <div class="alarm-section">
          <h4>告警配置</h4>
          
          <el-form-item label="告警级别">
            <el-select v-model="alarmConfig.level" placeholder="请选择告警级别">
              <el-option label="低" value="low" />
              <el-option label="中" value="medium" />
              <el-option label="高" value="high" />
              <el-option label="紧急" value="critical" />
            </el-select>
          </el-form-item>
          
          <el-form-item label="启用告警">
            <el-switch v-model="alarmConfig.enabled" />
          </el-form-item>
          
          <el-form-item label="告警抑制" v-if="alarmConfig.enabled">
            <el-input-number
              v-model="alarmConfig.suppress_duration"
              :min="0"
              :max="3600"
              :step="60"
              controls-position="right"
            />
            <span style="margin-left: 8px">秒</span>
            <div class="form-tip">相同告警的抑制时间，0表示不抑制</div>
          </el-form-item>
        </div>
      </el-form>
      
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSave" :loading="saving">保存</el-button>
      </template>
    </el-dialog>

    <!-- 查看详情对话框 -->
    <el-dialog
      v-model="viewVisible"
      title="模板详情"
      width="600px"
    >
      <div v-if="currentTemplate" class="template-detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="模板名称">{{ currentTemplate.name }}</el-descriptions-item>
          <el-descriptions-item label="诊断类型">
            <el-tag 
              v-for="type in currentTemplate.diagnosis_types" 
              :key="type" 
              :type="getDiagnosisTypeColor(type)"
              style="margin-right: 4px"
            >
              {{ getDiagnosisTypeName(type) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="启用状态">
            <el-tag :type="currentTemplate.is_active ? 'success' : 'danger'">
              {{ currentTemplate.is_active ? '已启用' : '已禁用' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="使用次数">{{ currentTemplate.usage_count || 0 }}</el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ formatDateTime(currentTemplate.created_at) }}</el-descriptions-item>
          <el-descriptions-item label="更新时间">{{ formatDateTime(currentTemplate.updated_at) }}</el-descriptions-item>
        </el-descriptions>
        
        <div class="description-section" v-if="currentTemplate.description">
          <h4>模板描述</h4>
          <el-card>
            <p>{{ currentTemplate.description }}</p>
          </el-card>
        </div>
        
        <div class="config-section">
          <h4>诊断配置</h4>
          <el-card>
            <pre>{{ JSON.stringify(currentTemplate.default_config, null, 2) }}</pre>
          </el-card>
        </div>
        
        <div class="alarm-config-section" v-if="currentTemplate.threshold_config">
          <h4>告警配置</h4>
          <el-card>
            <pre>{{ JSON.stringify(currentTemplate.threshold_config, null, 2) }}</pre>
          </el-card>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Refresh, Plus } from '@element-plus/icons-vue'
import { diagnosisTemplateApi, type DiagnosisTemplate, type DiagnosisTemplateCreate, DiagnosisType } from '@/api/diagnosis'
import { formatDateTime, formatDate } from '@/utils/date'

// 响应式数据
const loading = ref(false)
const saving = ref(false)
const templates = ref<DiagnosisTemplate[]>([])

// 分页
const currentPage = ref(1)
const pageSize = ref(12)
const total = ref(0)

// 搜索表单
const searchForm = reactive({
  search: '',
  diagnosis_type: '',
  is_active: null as boolean | null
})

// 对话框
const dialogVisible = ref(false)
const viewVisible = ref(false)
const dialogMode = ref<'create' | 'edit'>('create')
const currentTemplate = ref<DiagnosisTemplate | null>(null)

// 表单数据
const formData = ref<DiagnosisTemplateCreate>({
  name: '',
  diagnosis_type: DiagnosisType.BRIGHTNESS,
  description: '',
  config: {},
  alarm_config: {},
  is_active: true
})

// 配置表单
const configForm = ref({
  threshold: 0.8,
  sensitivity: 'medium',
  sample_interval: 30,
  detection_area: 'full',
  min_duration: 5
})

const alarmConfig = ref({
  enabled: true,
  level: 'medium',
  suppress_duration: 300
})

const thresholdPercent = ref(80)

// 表单验证规则
const formRules = {
  name: [{ required: true, message: '请输入模板名称', trigger: 'blur' }],
  diagnosis_type: [{ required: true, message: '请选择诊断类型', trigger: 'change' }]
}

const formRef = ref()

// 计算属性
const showThreshold = computed(() => {
  return ['brightness', 'clarity', 'contrast', 'noise'].includes(formData.value.diagnosis_type)
})

const showSensitivity = computed(() => {
  return ['shake', 'freeze', 'occlusion', 'mosaic'].includes(formData.value.diagnosis_type)
})

const showSampleInterval = computed(() => {
  return true // 所有类型都支持采样间隔
})

const showDetectionArea = computed(() => {
  return ['occlusion', 'mosaic', 'flower_screen'].includes(formData.value.diagnosis_type)
})

const showMinDuration = computed(() => {
  return ['freeze', 'blue_screen', 'flower_screen'].includes(formData.value.diagnosis_type)
})

// 监听阈值百分比变化
watch(thresholdPercent, (val) => {
  configForm.value.threshold = val / 100
})

// 方法
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

const loadTemplates = async () => {
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
    
    const response = await diagnosisTemplateApi.getTemplates(params)
    templates.value = response.data || []
    // 后端返回的是数组，不是分页格式，所以total设置为数组长度
    total.value = (response.data || []).length
  } catch (error) {
    console.error('加载模板列表失败:', error)
    ElMessage.error('加载模板列表失败')
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  currentPage.value = 1
  loadTemplates()
}

const handleReset = () => {
  Object.assign(searchForm, {
    search: '',
    diagnosis_type: '',
    is_active: null
  })
  currentPage.value = 1
  loadTemplates()
}

const handleSizeChange = (size: number) => {
  pageSize.value = size
  currentPage.value = 1
  loadTemplates()
}

const handleCurrentChange = (page: number) => {
  currentPage.value = page
  loadTemplates()
}

const handleCreate = () => {
  dialogMode.value = 'create'
  currentTemplate.value = null
  resetForm()
  dialogVisible.value = true
}

const handleEdit = (template: DiagnosisTemplate) => {
  dialogMode.value = 'edit'
  currentTemplate.value = template
  formData.value = {
    name: template.name,
    diagnosis_type: template.diagnosis_types?.[0] || DiagnosisType.BRIGHTNESS,  // 取第一个诊断类型
    description: template.description,
    config: { ...template.default_config },  // default_config -> config
    alarm_config: { ...template.threshold_config },  // threshold_config -> alarm_config
    is_active: template.is_active
  }
  
  // 填充配置表单
  if (template.default_config) {
    Object.assign(configForm.value, template.default_config)
    if (template.default_config.threshold) {
      thresholdPercent.value = Math.round(template.default_config.threshold * 100)
    }
  }
  
  if (template.threshold_config) {
    Object.assign(alarmConfig.value, template.threshold_config)
  }
  
  dialogVisible.value = true
}

const handleView = (template: DiagnosisTemplate) => {
  currentTemplate.value = template
  viewVisible.value = true
}

const handleCopy = (template: DiagnosisTemplate) => {
  dialogMode.value = 'create'
  currentTemplate.value = null
  formData.value = {
    name: template.name + ' - 副本',
    diagnosis_type: template.diagnosis_types?.[0] || DiagnosisType.BRIGHTNESS,  // 取第一个诊断类型
    description: template.description,
    config: { ...template.default_config },
    alarm_config: { ...template.threshold_config },
    is_active: true
  }
  
  // 填充配置表单
  if (template.default_config) {
    Object.assign(configForm.value, template.default_config)
    if (template.default_config.threshold) {
      thresholdPercent.value = Math.round(template.default_config.threshold * 100)
    }
  }
  
  if (template.threshold_config) {
    Object.assign(alarmConfig.value, template.threshold_config)
  }
  
  dialogVisible.value = true
}

const handleDelete = async (template: DiagnosisTemplate) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除模板 "${template.name}" 吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await diagnosisTemplateApi.deleteTemplate(template.id)
    ElMessage.success('删除成功')
    loadTemplates()
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('删除模板失败:', error)
      ElMessage.error('删除失败')
    }
  }
}

const handleToggleActive = async (template: DiagnosisTemplate) => {
  try {
    template.switching = true
    await diagnosisTemplateApi.toggleTemplate(template.id, template.is_active)
    ElMessage.success(template.is_active ? '模板已启用' : '模板已禁用')
  } catch (error) {
    console.error('切换模板状态失败:', error)
    ElMessage.error('操作失败')
    template.is_active = !template.is_active // 回滚状态
  } finally {
    template.switching = false
  }
}

const handleTypeChange = () => {
  // 重置配置表单
  configForm.value = {
    threshold: 0.8,
    sensitivity: 'medium',
    sample_interval: 30,
    detection_area: 'full',
    min_duration: 5
  }
  thresholdPercent.value = 80
}

const handleSave = async () => {
  try {
    await formRef.value?.validate()
    saving.value = true
    
    // 构建配置对象
    const config: any = {
      sample_interval: configForm.value.sample_interval
    }
    
    if (showThreshold.value) {
      config.threshold = configForm.value.threshold
    }
    if (showSensitivity.value) {
      config.sensitivity = configForm.value.sensitivity
    }
    if (showDetectionArea.value) {
      config.detection_area = configForm.value.detection_area
    }
    if (showMinDuration.value) {
      config.min_duration = configForm.value.min_duration
    }
    
    // 构建API请求数据，字段映射：前端 -> API
    const apiData = {
      name: formData.value.name,
      diagnosis_type: formData.value.diagnosis_type,
      description: formData.value.description,
      config_template: config,  // config -> config_template
      default_schedule: {},
      threshold_config: { ...alarmConfig.value },
      is_public: formData.value.is_active
    }
    
    if (dialogMode.value === 'create') {
      await diagnosisTemplateApi.createTemplate(apiData)
      ElMessage.success('创建成功')
    } else if (currentTemplate.value) {
      await diagnosisTemplateApi.updateTemplate(currentTemplate.value.id, apiData)
      ElMessage.success('更新成功')
    }
    
    dialogVisible.value = false
    loadTemplates()
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
    description: '',
    config: {},
    alarm_config: {},
    is_active: true
  }
  
  configForm.value = {
    threshold: 0.8,
    sensitivity: 'medium',
    sample_interval: 30,
    detection_area: 'full',
    min_duration: 5
  }
  
  alarmConfig.value = {
    enabled: true,
    level: 'medium',
    suppress_duration: 300
  }
  
  thresholdPercent.value = 80
  formRef.value?.clearValidate()
}

// 生命周期
onMounted(() => {
  loadTemplates()
})
</script>

<style scoped>
.diagnosis-templates {
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

.template-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
  gap: 20px;
  margin-bottom: 20px;
}

.template-card {
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  overflow: hidden;
  transition: box-shadow 0.3s;
}

.template-card:hover {
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}

.card-header {
  padding: 20px 20px 0 20px;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.template-info {
  flex: 1;
}

.template-name {
  margin: 0 0 8px 0;
  font-size: 18px;
  font-weight: 600;
  line-height: 1.2;
}

.template-actions {
  margin-left: 16px;
}

.card-content {
  padding: 16px 20px;
}

.template-description {
  margin: 0 0 16px 0;
  color: #666;
  font-size: 14px;
  line-height: 1.4;
  min-height: 40px;
}

.template-config {
  margin-bottom: 16px;
}

.config-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 4px 0;
  font-size: 13px;
}

.config-label {
  color: #666;
}

.config-value {
  font-weight: 500;
}

.template-stats {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #999;
}

.stat-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.stat-label {
  font-size: 11px;
}

.stat-value {
  font-weight: 500;
}

.card-footer {
  padding: 16px 20px;
  background: #f8f9fa;
  border-top: 1px solid #eee;
  display: flex;
  gap: 8px;
}

.empty-state {
  grid-column: 1 / -1;
  padding: 60px 20px;
}

.pagination-container {
  text-align: center;
}

.config-section,
.alarm-section {
  margin-top: 24px;
  padding-top: 20px;
  border-top: 1px solid #eee;
}

.config-section h4,
.alarm-section h4 {
  margin: 0 0 16px 0;
  font-size: 16px;
  font-weight: 600;
}

.form-tip {
  font-size: 12px;
  color: #999;
  margin-top: 4px;
}

.template-detail {
  max-height: 600px;
  overflow-y: auto;
}

.description-section,
.config-section,
.alarm-config-section {
  margin-top: 20px;
}

.description-section h4,
.config-section h4,
.alarm-config-section h4 {
  margin: 0 0 12px 0;
  font-size: 16px;
  font-weight: 600;
}

.description-section p {
  margin: 0;
  line-height: 1.6;
}

.config-section pre,
.alarm-config-section pre {
  background: #f5f5f5;
  padding: 12px;
  border-radius: 4px;
  font-size: 12px;
  line-height: 1.4;
  max-height: 200px;
  overflow-y: auto;
  margin: 0;
}
</style>