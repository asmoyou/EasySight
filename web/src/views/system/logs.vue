<template>
  <div class="system-logs">
    <div class="page-header">
      <h1>系统日志</h1>
      <p>查看和管理系统运行日志</p>
    </div>

    <!-- 搜索和筛选 -->
    <el-card class="filter-card">
      <el-form :model="queryParams" inline>
        <el-form-item label="日志级别">
          <el-select v-model="queryParams.level" placeholder="选择日志级别" clearable>
            <el-option label="调试" value="debug" />
            <el-option label="信息" value="info" />
            <el-option label="警告" value="warning" />
            <el-option label="错误" value="error" />
            <el-option label="严重" value="critical" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="模块">
          <el-select v-model="queryParams.module" placeholder="选择模块" clearable>
            <el-option label="用户管理" value="user" />
            <el-option label="角色管理" value="role" />
            <el-option label="摄像头管理" value="camera" />
            <el-option label="AI算法" value="ai" />
            <el-option label="事件处理" value="event" />
            <el-option label="系统配置" value="system" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="用户ID">
          <el-input v-model="queryParams.user_id" placeholder="输入用户ID" clearable />
        </el-form-item>
        
        <el-form-item label="时间范围">
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            @change="handleDateRangeChange"
          />
        </el-form-item>
        
        <el-form-item label="搜索">
          <el-input v-model="queryParams.search" placeholder="搜索日志内容" clearable />
        </el-form-item>
        
        <el-form-item>
          <el-button type="primary" @click="loadLogs">搜索</el-button>
          <el-button @click="resetQuery">重置</el-button>
          <el-button type="success" @click="exportLogs">导出</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 日志列表 -->
    <el-card class="table-card">
      <el-table 
        v-loading="loading" 
        :data="logs" 
        stripe 
        style="width: 100%"
        @sort-change="handleSortChange"
      >
        <el-table-column prop="created_at" label="时间" width="180" sortable="custom">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>
        
        <el-table-column prop="level" label="级别" width="100">
          <template #default="{ row }">
            <el-tag :type="getLevelTagType(row.level)">{{ getLevelText(row.level) }}</el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="module" label="模块" width="120" />
        
        <el-table-column prop="action" label="操作" width="150">
          <template #default="{ row }">
            {{ getActionText(row.action) }}
          </template>
        </el-table-column>
        
        <el-table-column prop="page_function" label="页面功能" width="180" show-overflow-tooltip>
          <template #default="{ row }">
            {{ row.page_function || getDefaultPageFunction(row.module, row.action) }}
          </template>
        </el-table-column>
        
        <el-table-column prop="message" label="消息" min-width="300" show-overflow-tooltip />
        
        <el-table-column prop="user_name" label="用户" width="120" />
        
        <el-table-column prop="ip_address" label="IP地址" width="140" />
        
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="viewDetail(row)">详情</el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <!-- 分页 -->
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="queryParams.page"
          v-model:page-size="queryParams.page_size"
          :page-sizes="[20, 50, 100, 200]"
          :total="total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="loadLogs"
          @current-change="loadLogs"
        />
      </div>
    </el-card>

    <!-- 日志详情对话框 -->
    <el-dialog v-model="detailVisible" title="日志详情" width="800px">
      <div v-if="selectedLog" class="log-detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="时间">
            {{ formatDateTime(selectedLog.created_at) }}
          </el-descriptions-item>
          <el-descriptions-item label="级别">
            <el-tag :type="getLevelTagType(selectedLog.level)">{{ getLevelText(selectedLog.level) }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="模块">{{ selectedLog.module }}</el-descriptions-item>
          <el-descriptions-item label="操作">{{ getActionText(selectedLog.action) }}</el-descriptions-item>
          <el-descriptions-item label="页面功能" :span="2">
            {{ selectedLog.page_function || getDefaultPageFunction(selectedLog.module, selectedLog.action) }}
          </el-descriptions-item>
          <el-descriptions-item label="用户">{{ selectedLog.user_name || '系统' }}</el-descriptions-item>
          <el-descriptions-item label="用户ID">{{ selectedLog.user_id || '-' }}</el-descriptions-item>
          <el-descriptions-item label="IP地址">{{ selectedLog.ip_address || '-' }}</el-descriptions-item>
          <el-descriptions-item label="请求ID">{{ selectedLog.request_id || '-' }}</el-descriptions-item>
        </el-descriptions>
        
        <div class="log-message">
          <h4>消息内容</h4>
          <el-input
            v-model="selectedLog.message"
            type="textarea"
            :rows="4"
            readonly
          />
        </div>
        
        <!-- 请求参数 -->
        <div v-if="getRequestParams(selectedLog)" class="request-params">
          <h4>请求参数</h4>
          <el-descriptions :column="1" border size="small">
            <el-descriptions-item 
              v-for="(value, key) in getRequestParams(selectedLog)" 
              :key="key" 
              :label="getParamLabel(key)"
            >
              <span v-if="typeof value === 'object'">{{ JSON.stringify(value) }}</span>
              <span v-else>{{ value }}</span>
            </el-descriptions-item>
          </el-descriptions>
        </div>
        
        <!-- 响应信息 -->
        <div v-if="getResponseInfo(selectedLog)" class="response-info">
          <h4>响应信息</h4>
          <el-descriptions :column="2" border size="small">
            <el-descriptions-item label="状态码">
              <el-tag :type="getStatusTagType(getResponseInfo(selectedLog)?.response_status)">
                {{ getResponseInfo(selectedLog)?.response_status }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="处理时间">
              {{ getResponseInfo(selectedLog)?.process_time_ms }}ms
            </el-descriptions-item>
            <el-descriptions-item label="用户代理" :span="2">
              {{ getResponseInfo(selectedLog)?.user_agent || '-' }}
            </el-descriptions-item>
          </el-descriptions>
        </div>
        
        <div v-if="selectedLog.extra_data && Object.keys(selectedLog.extra_data).length > 0" class="extra-data">
          <h4>完整数据</h4>
          <pre>{{ JSON.stringify(selectedLog.extra_data, null, 2) }}</pre>
        </div>
        
        <div v-if="selectedLog.user_agent" class="user-agent">
          <h4>用户代理</h4>
          <el-input v-model="selectedLog.user_agent" readonly />
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { systemApi, type SystemLog, type SystemLogsQuery } from '@/api/system'
import { formatDateTime } from '@/utils/date'

// 响应式数据
const loading = ref(false)
const logs = ref<SystemLog[]>([])
const total = ref(0)
const detailVisible = ref(false)
const selectedLog = ref<SystemLog | null>(null)
const dateRange = ref<[string, string] | null>(null)

// 查询参数
const queryParams = reactive<SystemLogsQuery>({
  page: 1,
  page_size: 50,
  level: undefined,
  module: undefined,
  user_id: undefined,
  start_time: undefined,
  end_time: undefined,
  search: undefined
})

// 加载日志列表
const loadLogs = async () => {
  try {
    loading.value = true
    const response = await systemApi.getSystemLogs(queryParams)
    logs.value = response.data.items
    total.value = response.data.total
  } catch (error) {
    console.error('加载日志失败:', error)
    ElMessage.error('加载日志失败')
  } finally {
    loading.value = false
  }
}

// 重置查询
const resetQuery = () => {
  Object.assign(queryParams, {
    page: 1,
    page_size: 50,
    level: undefined,
    module: undefined,
    user_id: undefined,
    start_time: undefined,
    end_time: undefined,
    search: undefined
  })
  dateRange.value = null
  loadLogs()
}

// 处理日期范围变化
const handleDateRangeChange = (dates: [string, string] | null) => {
  if (dates) {
    queryParams.start_time = dates[0]
    queryParams.end_time = dates[1]
  } else {
    queryParams.start_time = undefined
    queryParams.end_time = undefined
  }
}

// 处理排序变化
const handleSortChange = ({ prop, order }: { prop: string; order: string }) => {
  // 这里可以添加排序逻辑
  loadLogs()
}

// 查看详情
const viewDetail = (log: SystemLog) => {
  selectedLog.value = log
  detailVisible.value = true
}

// 导出日志
const exportLogs = () => {
  ElMessage.info('导出功能开发中...')
}

// 获取级别标签类型
const getLevelTagType = (level: string) => {
  const typeMap: Record<string, string> = {
    debug: '',
    info: 'success',
    warning: 'warning',
    error: 'danger',
    critical: 'danger'
  }
  return typeMap[level] || ''
}

// 获取级别文本
const getLevelText = (level: string) => {
  const textMap: Record<string, string> = {
    debug: '调试',
    info: '信息',
    warning: '警告',
    error: '错误',
    critical: '严重'
  }
  return textMap[level] || level
}

// 获取操作文本
const getActionText = (action: string) => {
  const actionMap: Record<string, string> = {
    'api_request': 'API请求',
    'create': '创建',
    'update': '更新',
    'delete': '删除',
    'batch_create': '批量创建',
    'batch_delete': '批量删除',
    'partial_update': '部分更新',
    'login': '登录',
    'logout': '登出',
    'upload': '上传',
    'download': '下载',
    'export': '导出',
    'import': '导入'
  }
  return actionMap[action] || action
}

// 获取默认页面功能描述
const getDefaultPageFunction = (module: string, action: string) => {
  if (action === 'api_request') {
    const moduleMap: Record<string, string> = {
      'user': '用户管理',
      'role': '角色管理', 
      'camera': '摄像头管理',
      'ai': 'AI管理',
      'event': '事件管理',
      'system': '系统管理',
      'diagnosis': '系统诊断',
      'file': '文件管理'
    }
    return moduleMap[module] || '未知操作'
  }
  return getActionText(action)
}

// 获取请求参数
const getRequestParams = (log: SystemLog) => {
  if (!log.extra_data) return null
  
  // 从URL路径中提取参数
  const params: Record<string, any> = {}
  
  // 添加基本请求信息
  if (log.extra_data.method) {
    params['请求方法'] = log.extra_data.method
  }
  if (log.extra_data.path) {
    params['请求路径'] = log.extra_data.path
  }
  
  // 添加查询参数
  if (log.extra_data.query_params && Object.keys(log.extra_data.query_params).length > 0) {
    Object.entries(log.extra_data.query_params).forEach(([key, value]) => {
      params[`查询参数.${key}`] = value
    })
  }
  
  // 添加请求体参数
  if (log.extra_data.request_body) {
    if (typeof log.extra_data.request_body === 'object') {
      Object.entries(log.extra_data.request_body).forEach(([key, value]) => {
        params[`请求参数.${key}`] = value
      })
    } else {
      params['请求体'] = log.extra_data.request_body
    }
  }
  
  return Object.keys(params).length > 0 ? params : null
}

// 获取响应信息
const getResponseInfo = (log: SystemLog) => {
  if (!log.extra_data) return null
  
  const info: Record<string, any> = {}
  if (log.extra_data.response_status) info.response_status = log.extra_data.response_status
  if (log.extra_data.process_time_ms) info.process_time_ms = log.extra_data.process_time_ms
  if (log.extra_data.user_agent) info.user_agent = log.extra_data.user_agent
  
  return Object.keys(info).length > 0 ? info : null
}

// 获取参数标签
const getParamLabel = (key: string) => {
  const labelMap: Record<string, string> = {
    '请求方法': '请求方法',
    '请求路径': '请求路径',
    '请求体': '请求体数据'
  }
  
  // 处理查询参数和请求参数的标签
  if (key.startsWith('查询参数.')) {
    return key.replace('查询参数.', '查询参数 → ')
  }
  if (key.startsWith('请求参数.')) {
    const paramName = key.replace('请求参数.', '')
    const paramLabelMap: Record<string, string> = {
      'code': '摄像头编码',
      'name': '摄像头名称', 
      'stream_url': '流媒体地址',
      'location': '安装位置',
      'description': '描述信息',
      'camera_type': '摄像头类型',
      'ip_address': 'IP地址',
      'port': '端口号',
      'username': '用户名',
      'password': '密码',
      'resolution': '分辨率',
      'frame_rate': '帧率',
      'bitrate': '码率',
      'is_active': '是否启用',
      'alarm_enabled': '是否启用告警',
      'algorithm_id': '算法ID',
      'model_id': '模型ID',
      'roi_areas': 'ROI区域',
      'threshold': '阈值',
      'schedule_config': '调度配置'
    }
    return paramLabelMap[paramName] || paramName
  }
  
  return labelMap[key] || key
}

// 获取状态码标签类型
const getStatusTagType = (status: number) => {
  if (status >= 200 && status < 300) return 'success'
  if (status >= 300 && status < 400) return 'info'
  if (status >= 400 && status < 500) return 'warning'
  if (status >= 500) return 'danger'
  return ''
}

// 组件挂载时加载数据
onMounted(() => {
  loadLogs()
})
</script>

<style scoped>
.system-logs {
  padding: 20px;
}

.page-header {
  margin-bottom: 20px;
}

.page-header h1 {
  margin: 0 0 8px 0;
  font-size: 24px;
  font-weight: 600;
}

.page-header p {
  margin: 0;
  color: #666;
}

.filter-card {
  margin-bottom: 20px;
}

.table-card {
  margin-bottom: 20px;
}

.pagination-wrapper {
  margin-top: 20px;
  text-align: right;
}

.log-detail {
  padding: 20px 0;
}

.log-message,
.request-params,
.response-info,
.extra-data,
.user-agent {
  margin-top: 20px;
}

.log-message h4,
.request-params h4,
.response-info h4,
.extra-data h4,
.user-agent h4 {
  margin: 0 0 10px 0;
  font-size: 14px;
  font-weight: 600;
}

.extra-data pre {
  background: #f5f5f5;
  padding: 10px;
  border-radius: 4px;
  font-size: 12px;
  overflow-x: auto;
}
</style>