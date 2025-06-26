<template>
  <div class="config-container">
    <!-- 页面标题和操作栏 -->
    <div class="page-header">
      <div class="header-left">
        <h2>系统设置</h2>
        <p class="page-description">管理系统配置参数和设置</p>
      </div>
      <div class="header-right">
        <el-button type="primary" :icon="Plus" @click="showCreateDialog">
          新增配置
        </el-button>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-cards" v-if="configStats">
      <el-row :gutter="20">
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-content">
              <div class="stat-icon total">
                <el-icon><Setting /></el-icon>
              </div>
              <div class="stat-info">
                <div class="stat-value">{{ configStats.total_configs }}</div>
                <div class="stat-label">总配置数</div>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-content">
              <div class="stat-icon public">
                <el-icon><View /></el-icon>
              </div>
              <div class="stat-info">
                <div class="stat-value">{{ configStats.public_configs }}</div>
                <div class="stat-label">公开配置</div>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-content">
              <div class="stat-icon editable">
                <el-icon><Edit /></el-icon>
              </div>
              <div class="stat-info">
                <div class="stat-value">{{ configStats.editable_configs }}</div>
                <div class="stat-label">可编辑配置</div>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-content">
              <div class="stat-icon categories">
                <el-icon><FolderOpened /></el-icon>
              </div>
              <div class="stat-info">
                <div class="stat-value">{{ configStats.categories_count }}</div>
                <div class="stat-label">配置分类</div>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 搜索和筛选 -->
    <el-card class="search-card">
      <el-row :gutter="20">
        <el-col :span="6">
          <el-input
            v-model="searchForm.search"
            placeholder="搜索配置键或描述"
            :prefix-icon="Search"
            clearable
            @input="handleSearch"
          />
        </el-col>
        <el-col :span="4">
          <el-select
            v-model="searchForm.category"
            placeholder="选择分类"
            clearable
            @change="handleSearch"
          >
            <el-option
              v-for="category in categories"
              :key="category"
              :label="category"
              :value="category"
            />
          </el-select>
        </el-col>
        <el-col :span="4">
          <el-select
            v-model="searchForm.is_public"
            placeholder="公开状态"
            clearable
            @change="handleSearch"
          >
            <el-option label="公开" :value="true" />
            <el-option label="私有" :value="false" />
          </el-select>
        </el-col>
        <el-col :span="4">
          <el-select
            v-model="searchForm.data_type"
            placeholder="值类型"
            clearable
            @change="handleSearch"
          >
            <el-option label="字符串" value="string" />
            <el-option label="整数" value="int" />
            <el-option label="浮点数" value="float" />
            <el-option label="布尔值" value="bool" />
            <el-option label="JSON" value="json" />
          </el-select>
        </el-col>
        <el-col :span="6">
          <el-button @click="resetSearch">重置</el-button>
          <el-button type="primary" @click="handleSearch">搜索</el-button>
        </el-col>
      </el-row>
    </el-card>

    <!-- 配置列表 -->
    <el-card class="table-card">
      <el-table
        :data="configs"
        v-loading="loading"
        stripe
        style="width: 100%"
      >
        <el-table-column prop="key" label="配置键" width="200" show-overflow-tooltip />
        <el-table-column prop="value" label="配置值" width="200" show-overflow-tooltip>
          <template #default="{ row }">
            <span v-if="row.data_type === 'bool'">
              <el-tag :type="row.value === 'true' ? 'success' : 'danger'">
                {{ row.value === 'true' ? '是' : '否' }}
              </el-tag>
            </span>
            <span v-else>{{ row.value }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="data_type" label="类型" width="100">
          <template #default="{ row }">
            <el-tag size="small" :type="getTypeTagType(row.data_type)">
              {{ getTypeLabel(row.data_type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="category" label="分类" width="120" show-overflow-tooltip />
        <el-table-column prop="description" label="描述" show-overflow-tooltip />
        <el-table-column label="状态" width="120">
          <template #default="{ row }">
            <div class="status-tags">
              <el-tag v-if="row.is_public" size="small" type="success">公开</el-tag>
              <el-tag v-if="!row.is_editable" size="small" type="warning">只读</el-tag>
              <el-tag v-if="row.requires_restart" size="small" type="danger">需重启</el-tag>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="updated_at" label="更新时间" width="160">
          <template #default="{ row }">
            {{ formatDateTime(row.updated_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button
              type="primary"
              size="small"
              :icon="Edit"
              @click="showEditDialog(row)"
              :disabled="!row.is_editable"
            >
              编辑
            </el-button>
            <el-button
              type="danger"
              size="small"
              :icon="Delete"
              @click="handleDelete(row)"
              :disabled="!row.is_editable"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 新增/编辑配置对话框 -->
    <el-dialog
      :title="dialogTitle"
      v-model="dialogVisible"
      width="600px"
      @close="resetForm"
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="formRules"
        label-width="100px"
      >
        <el-form-item label="配置键" prop="key">
          <el-input
            v-model="form.key"
            placeholder="请输入配置键"
            :disabled="isEdit"
          />
        </el-form-item>
        <el-form-item label="配置值" prop="value">
          <el-input
            v-if="form.data_type !== 'bool'"
          v-model="form.value"
          :type="form.data_type === 'json' ? 'textarea' : 'text'"
            :rows="4"
            placeholder="请输入配置值"
          />
          <el-switch
            v-else
            v-model="boolValue"
            @change="handleBoolChange"
          />
        </el-form-item>
        <el-form-item label="值类型" prop="data_type">
          <el-select v-model="form.data_type" placeholder="选择值类型">
            <el-option label="字符串" value="string" />
            <el-option label="整数" value="int" />
            <el-option label="浮点数" value="float" />
            <el-option label="布尔值" value="bool" />
            <el-option label="JSON" value="json" />
          </el-select>
        </el-form-item>
        <el-form-item label="分类" prop="category">
          <el-input v-model="form.category" placeholder="请输入配置分类" />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="3"
            placeholder="请输入配置描述"
          />
        </el-form-item>
        <el-form-item label="是否公开">
          <el-switch v-model="form.is_public" />
          <span class="form-tip">公开配置可被前端访问</span>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">
          {{ isEdit ? '更新' : '创建' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance } from 'element-plus'
import {
  Plus,
  Search,
  Edit,
  Delete,
  Setting,
  View,
  FolderOpened
} from '@element-plus/icons-vue'
import { systemApi } from '@/api/system'
import type { SystemConfig, SystemConfigCreate, SystemConfigUpdate } from '@/api/system'
import { formatDateTime } from '@/utils/date'

// 响应式数据
const loading = ref(false)
const submitting = ref(false)
const configs = ref<SystemConfig[]>([])
const configStats = ref<any>(null)
const categories = ref<string[]>([])

// 搜索表单
const searchForm = reactive({
  search: '',
  category: '',
  is_public: null as boolean | null,
  data_type: ''
})

// 对话框相关
const dialogVisible = ref(false)
const isEdit = ref(false)
const currentConfig = ref<SystemConfig | null>(null)

// 表单相关
const formRef = ref<FormInstance>()
const form = reactive<SystemConfigCreate>({
  key: '',
  value: '',
  category: '',
  description: '',
  is_public: false,
  data_type: 'string'
})

const boolValue = ref(false)

// 表单验证规则
const formRules = {
  key: [
    { required: true, message: '请输入配置键', trigger: 'blur' },
    { min: 1, max: 100, message: '长度在 1 到 100 个字符', trigger: 'blur' }
  ],
  value: [
    { required: true, message: '请输入配置值', trigger: 'blur' }
  ],
  category: [
    { required: true, message: '请输入配置分类', trigger: 'blur' }
  ]
}

// 计算属性
const dialogTitle = computed(() => isEdit.value ? '编辑配置' : '新增配置')

// 方法
const loadConfigs = async () => {
  try {
    loading.value = true
    const response = await systemApi.getSystemConfigs()
    configs.value = response.data
    
    // 提取分类
    const categorySet = new Set(configs.value.map(config => config.category).filter(Boolean))
    categories.value = Array.from(categorySet)
    
    // 计算统计信息
    configStats.value = {
      total_configs: configs.value.length,
      public_configs: configs.value.filter(c => c.is_public).length,
      editable_configs: configs.value.filter(c => c.is_editable).length,
      categories_count: categories.value.length
    }
  } catch (error) {
    ElMessage.error('加载配置列表失败')
  } finally {
    loading.value = false
  }
}

const handleSearch = async () => {
  try {
    loading.value = true
    const response = await systemApi.getSystemConfigs()
    let filteredConfigs = response.data
    
    // 根据搜索条件过滤
    if (searchForm.search) {
      filteredConfigs = filteredConfigs.filter(config => 
        config.key.toLowerCase().includes(searchForm.search.toLowerCase()) ||
        config.description?.toLowerCase().includes(searchForm.search.toLowerCase())
      )
    }
    
    if (searchForm.category) {
      filteredConfigs = filteredConfigs.filter(config => config.category === searchForm.category)
    }
    
    if (searchForm.is_public !== null) {
      filteredConfigs = filteredConfigs.filter(config => config.is_public === searchForm.is_public)
    }
    
    if (searchForm.data_type) {
      filteredConfigs = filteredConfigs.filter(config => config.data_type === searchForm.data_type)
    }
    
    configs.value = filteredConfigs
    
    // 重新计算统计信息
    configStats.value = {
      total_configs: filteredConfigs.length,
      public_configs: filteredConfigs.filter(c => c.is_public).length,
      editable_configs: filteredConfigs.filter(c => c.is_editable).length,
      categories_count: new Set(filteredConfigs.map(c => c.category).filter(Boolean)).size
    }
  } catch (error) {
    ElMessage.error('搜索配置失败')
  } finally {
    loading.value = false
  }
}

const resetSearch = () => {
  searchForm.search = ''
  searchForm.category = ''
  searchForm.is_public = null
  searchForm.data_type = ''
  handleSearch()
}

const showCreateDialog = () => {
  isEdit.value = false
  currentConfig.value = null
  resetForm()
  dialogVisible.value = true
}

const showEditDialog = (config: SystemConfig) => {
  isEdit.value = true
  currentConfig.value = config
  
  // 填充表单
  form.key = config.key
  form.value = config.value
  form.category = config.category
  form.description = config.description || ''
  form.is_public = config.is_public
  form.data_type = config.data_type
  
  if (config.data_type === 'bool') {
    boolValue.value = config.value === 'true'
  }
  
  dialogVisible.value = true
}

const resetForm = () => {
  form.key = ''
  form.value = ''
  form.category = ''
  form.description = ''
  form.is_public = false
  form.data_type = 'string'
  boolValue.value = false
  formRef.value?.clearValidate()
}

const handleBoolChange = (value: boolean) => {
  form.value = value.toString()
}

const handleSubmit = async () => {
  if (!formRef.value) return
  
  try {
    await formRef.value.validate()
    submitting.value = true
    
    if (isEdit.value && currentConfig.value) {
      const updateData: SystemConfigUpdate = {
        value: form.value,
        description: form.description,
        is_public: form.is_public
      }
      await systemApi.updateSystemConfig(currentConfig.value.id, updateData)
      ElMessage.success('配置更新成功')
    } else {
      await systemApi.createSystemConfig(form)
      ElMessage.success('配置创建成功')
    }
    
    dialogVisible.value = false
    await loadConfigs()
  } catch (error) {
    ElMessage.error(isEdit.value ? '配置更新失败' : '配置创建失败')
  } finally {
    submitting.value = false
  }
}

const handleDelete = async (config: SystemConfig) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除配置 "${config.key}" 吗？此操作不可恢复。`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await systemApi.deleteSystemConfig(config.id)
    ElMessage.success('配置删除成功')
    await loadConfigs()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('配置删除失败')
    }
  }
}

const getTypeTagType = (type: string) => {
  const typeMap: Record<string, string> = {
    string: '',
    int: 'success',
    float: 'warning',
    bool: 'info',
    json: 'danger'
  }
  return typeMap[type] || ''
}

const getTypeLabel = (type: string) => {
  const labelMap: Record<string, string> = {
    string: '字符串',
    int: '整数',
    float: '浮点数',
    bool: '布尔值',
    json: 'JSON'
  }
  return labelMap[type] || type
}

// 生命周期
onMounted(() => {
  loadConfigs()
})
</script>

<style scoped>
.config-container {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header-left h2 {
  margin: 0 0 8px 0;
  color: #303133;
  font-size: 24px;
  font-weight: 600;
}

.page-description {
  margin: 0;
  color: #909399;
  font-size: 14px;
}

.stats-cards {
  margin-bottom: 20px;
}

.stat-card {
  border: none;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.stat-content {
  display: flex;
  align-items: center;
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

.stat-icon.total {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.stat-icon.public {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.stat-icon.editable {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
}

.stat-icon.categories {
  background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
}

.stat-info {
  flex: 1;
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
  color: #909399;
}

.search-card,
.table-card {
  margin-bottom: 20px;
}

.status-tags {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.form-tip {
  margin-left: 10px;
  color: #909399;
  font-size: 12px;
}
</style>