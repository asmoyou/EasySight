<template>
  <div class="media-nodes-container">
    <!-- 页面标题和操作栏 -->
    <div class="page-header">
      <div class="header-left">
        <h2>流媒体节点管理</h2>
        <p class="page-description">管理系统中的流媒体代理节点，监控节点状态和性能</p>
      </div>
      <div class="header-right">
        <el-button type="primary" @click="showCreateDialog">
          <el-icon><Plus /></el-icon>
          添加节点
        </el-button>
        <el-button @click="refreshNodes">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-cards" v-if="nodeStats">
      <el-row :gutter="20">
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-content">
              <div class="stat-icon online">
                <el-icon><Connection /></el-icon>
              </div>
              <div class="stat-info">
                <div class="stat-value">{{ nodeStats?.online || 0 }}</div>
                <div class="stat-label">在线节点</div>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-content">
              <div class="stat-icon total">
                <el-icon><Monitor /></el-icon>
              </div>
              <div class="stat-info">
                <div class="stat-value">{{ nodeStats?.total || 0 }}</div>
                <div class="stat-label">总节点数</div>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-content">
              <div class="stat-icon connections">
                <el-icon><Link /></el-icon>
              </div>
              <div class="stat-info">
                <div class="stat-value">{{ nodeStats?.totalConnections || 0 }}</div>
                <div class="stat-label">总观看数</div>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-content">
              <div class="stat-icon capacity">
                <el-icon><DataAnalysis /></el-icon>
              </div>
              <div class="stat-info">
                <div class="stat-value">{{ nodeStats?.maxConnections || 0 }}</div>
                <div class="stat-label">最大连接数</div>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 搜索和筛选 -->
    <el-card class="search-card">
      <el-form :model="searchForm" inline>
        <el-form-item label="节点名称">
          <el-input
            v-model="searchForm.search"
            placeholder="请输入节点名称"
            clearable
            @change="handleSearch"
          />
        </el-form-item>
        <el-form-item label="在线状态">
          <el-select
            v-model="searchForm.is_online"
            placeholder="选择状态"
            clearable
            @change="handleSearch"
          >
            <el-option label="在线" :value="true" />
            <el-option label="离线" :value="false" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button @click="resetSearch">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 节点列表 -->
    <el-card class="table-card">
      <el-table
        :data="filteredNodes"
        v-loading="loading"
        stripe
        style="width: 100%"
      >
        <el-table-column prop="name" label="节点名称" width="150" />
        <el-table-column label="地址" width="180">
          <template #default="{ row }">
            {{ row.ip_address }}:{{ row.port }}
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_online ? 'success' : 'danger'">
              {{ row.is_online ? '在线' : '离线' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="观看数" width="120">
          <template #default="{ row }">
            <span>{{ row.current_connections || 0 }}/{{ row.max_connections }}</span>
          </template>
        </el-table-column>
        <el-table-column label="CPU使用率" width="120">
          <template #default="{ row }">
            <el-progress
              v-if="row.cpu_usage !== null"
              :percentage="Math.round(row.cpu_usage || 0)"
              :color="getProgressColor(row.cpu_usage || 0)"
              :stroke-width="8"
            />
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column label="内存使用率" width="120">
          <template #default="{ row }">
            <el-progress
              v-if="row.memory_usage !== null"
              :percentage="Math.round(row.memory_usage || 0)"
              :color="getProgressColor(row.memory_usage || 0)"
              :stroke-width="8"
            />
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column label="最后心跳" width="180">
          <template #default="{ row }">
            <span v-if="row.last_heartbeat">
              {{ formatDateTime(row.last_heartbeat) }}
            </span>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="描述" show-overflow-tooltip />
        <el-table-column label="操作" width="140" fixed="right">
          <template #default="{ row }">
            <div class="action-buttons">
              <el-button-group>
                <el-button
                  type="info"
                  size="small"
                  :icon="View"
                  @click="showStreamDetails(row)"
                  :disabled="!row.is_online"
                  title="流详情"
                />
                <el-button
                  type="primary"
                  size="small"
                  :icon="Edit"
                  @click="showEditDialog(row)"
                  title="编辑"
                />
              </el-button-group>
              <el-dropdown @command="(command) => handleDropdownCommand(command, row)">
                <el-button
                  type="primary"
                  size="small"
                  :icon="MoreFilled"
                  title="更多操作"
                />
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item command="delete" :icon="Delete" class="danger-item">
                      删除
                    </el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 添加/编辑节点对话框 -->
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
        <el-form-item label="节点名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入节点名称" />
        </el-form-item>
        <el-form-item label="IP地址" prop="ip_address">
          <el-input v-model="form.ip_address" placeholder="请输入IP地址" />
        </el-form-item>
        <el-form-item label="端口" prop="port">
          <el-input-number
            v-model="form.port"
            :min="1"
            :max="65535"
            placeholder="请输入端口号"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="密钥" prop="secret_key">
          <el-input
            v-model="form.secret_key"
            type="password"
            placeholder="请输入密钥（可选）"
            show-password
          />
        </el-form-item>
        <el-form-item label="最大连接数" prop="max_connections">
          <el-input-number
            v-model="form.max_connections"
            :min="1"
            :max="10000"
            placeholder="请输入最大连接数"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="3"
            placeholder="请输入节点描述（可选）"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button
          type="primary"
          @click="submitForm"
          :loading="submitting"
        >
          {{ isEdit ? '更新' : '创建' }}
        </el-button>
      </template>
    </el-dialog>

    <!-- 流详情对话框 -->
    <el-dialog
      title="节点流详情"
      v-model="streamDialogVisible"
      width="1200px"
      :close-on-click-modal="false"
    >
      <div v-loading="streamLoading">
        <div v-if="streamData" class="stream-details">
          <!-- 节点信息 -->
          <el-card class="node-info-card" shadow="never">
            <template #header>
              <div class="card-header">
                <span>节点信息</span>
              </div>
            </template>
            <el-row :gutter="20">
              <el-col :span="6">
                <div class="info-item">
                  <label>节点名称:</label>
                  <span>{{ streamData.proxy_name }}</span>
                </div>
              </el-col>
              <el-col :span="6">
                <div class="info-item">
                  <label>服务地址:</label>
                  <span>{{ streamData.proxy_address }}</span>
                </div>
              </el-col>
              <el-col :span="6">
                <div class="info-item">
                  <label>ZLM地址:</label>
                  <span>{{ streamData.zlm_address }}</span>
                </div>
              </el-col>
              <el-col :span="6">
                <div class="info-item">
                  <label>总流数:</label>
                  <span>{{ streamData.total_streams }}</span>
                </div>
              </el-col>
            </el-row>
          </el-card>

          <!-- 流列表 -->
          <el-card class="streams-card" shadow="never">
            <template #header>
              <div class="card-header">
                <span>活动流列表</span>
                <el-tag type="info">共 {{ streamData.total_streams }} 个流</el-tag>
              </div>
            </template>
            
            <el-table
              :data="streamData.streams"
              stripe
              style="width: 100%"
              max-height="400"
            >
              <el-table-column prop="camera_name" label="摄像头" width="150" />
              <el-table-column prop="stream" label="流ID" width="200" show-overflow-tooltip />
              <el-table-column prop="app" label="应用" width="80" />
              <el-table-column prop="schema" label="协议" width="80" />
              <el-table-column label="观看人数" width="100">
                <template #default="{ row }">
                  <span>{{ row.readerCount }}/{{ row.totalReaderCount }}</span>
                </template>
              </el-table-column>
              <el-table-column label="传输速度" width="120">
                <template #default="{ row }">
                  <span>{{ formatBytesSpeed(row.bytesSpeed) }}</span>
                </template>
              </el-table-column>
              <el-table-column label="运行时长" width="120">
                <template #default="{ row }">
                  <span>{{ formatDuration(row.aliveSecond) }}</span>
                </template>
              </el-table-column>
              <el-table-column label="来源类型" width="120">
                <template #default="{ row }">
                  <el-tag size="small" :type="row.originType === 0 ? 'success' : 'info'">
                    {{ row.originTypeStr || '未知' }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column label="轨道信息" min-width="200">
                <template #default="{ row }">
                  <div v-if="row.tracks && row.tracks.length > 0">
                    <el-tag
                      v-for="(track, index) in row.tracks"
                      :key="index"
                      size="small"
                      class="track-tag"
                      :type="track.codec_type === 0 ? 'primary' : 'warning'"
                    >
                      {{ track.codec_type === 0 ? '视频' : '音频' }}: {{ track.codec_id_name || 'Unknown' }}
                    </el-tag>
                  </div>
                  <span v-else>无轨道信息</span>
                </template>
              </el-table-column>
            </el-table>
          </el-card>
        </div>
        
        <div v-else-if="!streamLoading" class="no-data">
          <el-empty description="暂无流数据" />
        </div>
      </div>
      
      <template #footer>
        <el-button @click="streamDialogVisible = false">关闭</el-button>
        <el-button type="primary" @click="showStreamDetails(currentNode!)" v-if="currentNode">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance } from 'element-plus'
import {
  Plus,
  Refresh,
  Connection,
  Monitor,
  Link,
  DataAnalysis,
  View,
  Edit,
  Delete,
  MoreFilled
} from '@element-plus/icons-vue'
import { formatDateTime } from '@/utils/date'
import { mediaProxyApi } from '@/api/cameras'
import type { MediaProxy, MediaProxyCreateForm, MediaProxyUpdateForm } from '@/types/camera'

// 类型定义
type MediaNode = MediaProxy
type MediaNodeCreate = MediaProxyCreateForm
type MediaNodeUpdate = MediaProxyUpdateForm

// 响应式数据
const loading = ref(false)
const submitting = ref(false)
const nodes = ref<MediaNode[]>([])
const nodeStats = ref<any>(null)

// 搜索表单
const searchForm = reactive({
  search: '',
  is_online: null as boolean | null
})

// 对话框相关
const dialogVisible = ref(false)
const isEdit = ref(false)
const currentNode = ref<MediaNode | null>(null)

// 流详情对话框相关
const streamDialogVisible = ref(false)
const streamLoading = ref(false)
const streamData = ref<any>(null)

// 表单相关
const formRef = ref<FormInstance>()
const form = reactive<MediaNodeCreate>({
  name: '',
  ip_address: '',
  port: 8080,
  secret_key: '',
  max_connections: 100,
  description: ''
})

// 表单验证规则
const formRules = {
  name: [
    { required: true, message: '请输入节点名称', trigger: 'blur' },
    { min: 2, max: 50, message: '节点名称长度在 2 到 50 个字符', trigger: 'blur' }
  ],
  ip_address: [
    { required: true, message: '请输入IP地址', trigger: 'blur' },
    {
      pattern: /^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/,
      message: '请输入有效的IP地址',
      trigger: 'blur'
    }
  ],
  port: [
    { required: true, message: '请输入端口号', trigger: 'blur' },
    { type: 'number', min: 1, max: 65535, message: '端口号范围为 1-65535', trigger: 'blur' }
  ],
  max_connections: [
    { required: true, message: '请输入最大连接数', trigger: 'blur' },
    { type: 'number', min: 1, max: 10000, message: '最大连接数范围为 1-10000', trigger: 'blur' }
  ]
}

// 计算属性
const dialogTitle = computed(() => isEdit.value ? '编辑节点' : '添加节点')

const filteredNodes = computed(() => {
  let result = nodes.value
  
  if (searchForm.search) {
    result = result.filter(node => 
      node.name.toLowerCase().includes(searchForm.search.toLowerCase()) ||
      node.ip_address.includes(searchForm.search)
    )
  }
  
  if (searchForm.is_online !== null) {
    result = result.filter(node => node.is_online === searchForm.is_online)
  }
  
  return result
})

// 方法


const updateStats = () => {
  const onlineNodes = nodes.value.filter(node => node.is_online)
  const offlineNodes = nodes.value.filter(node => !node.is_online)
  
  nodeStats.value = {
    total: nodes.value.length,
    online: onlineNodes.length,
    offline: offlineNodes.length,
    totalConnections: nodes.value.reduce((sum, node) => sum + (node.current_connections || 0), 0),
    maxConnections: nodes.value.reduce((sum, node) => sum + (node.max_connections || 0), 0)
  }
}

const handleSearch = () => {
  // 搜索逻辑已在计算属性中处理
}

const resetSearch = () => {
  searchForm.search = ''
  searchForm.is_online = null
}

const loadNodes = async () => {
  try {
    loading.value = true
    const response = await mediaProxyApi.getMediaProxies()
    nodes.value = response.data
    updateStats()
  } catch (error: any) {
    ElMessage.error(error.message || '获取节点列表失败')
    console.error('Error loading nodes:', error)
  } finally {
    loading.value = false
  }
}

const refreshNodes = () => {
  loadNodes()
}

const showCreateDialog = () => {
  isEdit.value = false
  currentNode.value = null
  resetForm()
  dialogVisible.value = true
}

const showEditDialog = (node: MediaNode) => {
  isEdit.value = true
  currentNode.value = node
  
  // 填充表单
  form.name = node.name
  form.ip_address = node.ip_address
  form.port = node.port
  form.secret_key = ''
  form.max_connections = node.max_connections
  form.description = node.description || ''
  
  dialogVisible.value = true
}

const resetForm = () => {
  if (formRef.value) {
    formRef.value.resetFields()
  }
  
  form.name = ''
  form.ip_address = ''
  form.port = 8080
  form.secret_key = ''
  form.max_connections = 100
  form.description = ''
}

const submitForm = async () => {
  if (!formRef.value) return
  
  try {
    await formRef.value.validate()
    submitting.value = true
    
    if (isEdit.value) {
      // 更新节点
      await mediaProxyApi.updateMediaProxy(currentNode.value!.id, form as MediaProxyUpdateForm)
      ElMessage.success('节点更新成功')
    } else {
      // 创建节点
      await mediaProxyApi.createMediaProxy(form)
      ElMessage.success('节点创建成功')
    }
    
    dialogVisible.value = false
    await loadNodes()
  } catch (error: any) {
    ElMessage.error(error.message || '操作失败')
  } finally {
    submitting.value = false
  }
}

const deleteNode = async (node: MediaNode) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除节点 "${node.name}" 吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await mediaProxyApi.deleteMediaProxy(node.id)
     await loadNodes()
     ElMessage.success('节点删除成功')
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('节点删除失败')
      console.error('Error deleting node:', error)
    }
  }
}

// 下拉菜单处理
const handleDropdownCommand = (command: string, node: MediaNode) => {
  if (command === 'delete') {
    deleteNode(node)
  }
}

const getProgressColor = (percentage: number) => {
  if (percentage < 50) return '#67c23a'
  if (percentage < 80) return '#e6a23c'
  return '#f56c6c'
}

// 显示流详情
const showStreamDetails = async (node: MediaNode) => {
  if (!node.is_online) {
    ElMessage.warning('节点离线，无法获取流详情')
    return
  }
  
  currentNode.value = node
  streamDialogVisible.value = true
  streamLoading.value = true
  streamData.value = null
  
  try {
    const response = await mediaProxyApi.getMediaProxyStreams(node.id)
    // 后端返回的数据结构是 {code, message, data}，需要访问 data 字段
    streamData.value = response.data.data
  } catch (error: any) {
    ElMessage.error(error.message || '获取流详情失败')
    streamDialogVisible.value = false
  } finally {
    streamLoading.value = false
  }
}

// 格式化字节速度
const formatBytesSpeed = (bytes: number) => {
  if (bytes === 0) return '0 B/s'
  const k = 1024
  const sizes = ['B/s', 'KB/s', 'MB/s', 'GB/s']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

// 格式化时长
const formatDuration = (seconds: number) => {
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const secs = seconds % 60
  
  if (hours > 0) {
    return `${hours}h ${minutes}m ${secs}s`
  } else if (minutes > 0) {
    return `${minutes}m ${secs}s`
  } else {
    return `${secs}s`
  }
}

// 初始化
onMounted(() => {
  loadNodes()
})
</script>

<style scoped>
.media-nodes-container {
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
  color: #303133;
  font-size: 24px;
  font-weight: 600;
}

.page-description {
  margin: 0;
  color: #909399;
  font-size: 14px;
}

.header-right {
  display: flex;
  gap: 12px;
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
  gap: 16px;
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  color: white;
}

.stat-icon.online {
  background: linear-gradient(135deg, #67c23a, #85ce61);
}

.stat-icon.total {
  background: linear-gradient(135deg, #409eff, #66b1ff);
}

.stat-icon.connections {
  background: linear-gradient(135deg, #e6a23c, #ebb563);
}

.stat-icon.capacity {
  background: linear-gradient(135deg, #f56c6c, #f78989);
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

/* 流详情对话框样式 */
.stream-details {
  .node-info-card {
    margin-bottom: 20px;
    
    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-weight: 600;
    }
    
    .info-item {
      display: flex;
      align-items: center;
      margin-bottom: 10px;
      
      label {
        font-weight: 500;
        color: #606266;
        margin-right: 8px;
        min-width: 80px;
      }
      
      span {
        color: #303133;
      }
    }
  }
  
  .streams-card {
    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-weight: 600;
    }
    
    .track-tag {
      margin-right: 4px;
      margin-bottom: 2px;
    }
  }
}

.no-data {
  text-align: center;
  padding: 40px 0;
}

.search-card,
.table-card {
  margin-bottom: 20px;
  border: none;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.search-card :deep(.el-card__body) {
  padding: 20px;
}

.table-card :deep(.el-card__body) {
  padding: 0;
}

:deep(.el-table) {
  border-radius: 8px;
}

:deep(.el-table th) {
  background-color: #fafafa;
  color: #606266;
  font-weight: 600;
}

:deep(.el-progress-bar__outer) {
  border-radius: 4px;
}

:deep(.el-progress-bar__inner) {
  border-radius: 4px;
}

.action-buttons {
  display: flex;
  align-items: center;
  gap: 8px;
}

.action-buttons .el-button-group {
  margin-right: 0;
}

.action-buttons .el-button {
  padding: 5px 8px;
}

.action-buttons .el-dropdown .el-button {
  padding: 5px 8px;
  min-width: 28px;
}

/* 操作按钮颜色样式 */
.action-buttons .el-button-group .el-button:first-child {
  color: #409eff;
  border-color: #c6e2ff;
  background-color: #ecf5ff;
}

.action-buttons .el-button-group .el-button:first-child:hover {
  color: #fff;
  background-color: #409eff;
  border-color: #409eff;
}

.action-buttons .el-button-group .el-button:last-child {
  color: #e6a23c;
  border-color: #f5dab1;
  background-color: #fdf6ec;
}

.action-buttons .el-button-group .el-button:last-child:hover {
  color: #fff;
  background-color: #e6a23c;
  border-color: #e6a23c;
}

.action-buttons .el-dropdown .el-button {
  color: #909399;
  border-color: #dcdfe6;
  background-color: #f5f7fa;
  padding: 5px 8px;
  min-width: 28px;
}

.action-buttons .el-dropdown .el-button:hover {
  color: #409eff;
  border-color: #c6e2ff;
  background-color: #ecf5ff;
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