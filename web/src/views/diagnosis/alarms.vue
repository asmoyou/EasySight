<template>
  <div class="diagnosis-alarms">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <h2>诊断告警</h2>
        <p class="page-description">查看视频质量诊断产生的告警信息，支持缩略图展示</p>
      </div>
      <div class="header-right">
        <el-button @click="handleMarkAllRead" :disabled="selectedAlarms.length === 0">
          <el-icon><Check /></el-icon>
          标记已读
        </el-button>
        <el-button @click="handleClearAll">
          <el-icon><Delete /></el-icon>
          清空告警
        </el-button>
      </div>
    </div>

    <!-- 搜索和筛选 -->
    <div class="search-filters">
      <div class="search-bar">
        <el-input
          v-model="searchForm.search"
          placeholder="搜索告警标题或设备名称"
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
        <el-select v-model="searchForm.alarm_type" placeholder="告警类型" clearable style="width: 150px">
          <el-option label="亮度异常" value="brightness" />
          <el-option label="蓝屏检测" value="blue_screen" />
          <el-option label="清晰度异常" value="clarity" />
          <el-option label="画面抖动" value="shake" />
          <el-option label="画面冻结" value="freeze" />
          <el-option label="偏色检测" value="color_cast" />
          <el-option label="遮挡检测" value="occlusion" />
          <el-option label="噪声检测" value="noise" />
          <el-option label="对比度异常" value="contrast" />
          <el-option label="马赛克检测" value="mosaic" />
          <el-option label="花屏检测" value="flower_screen" />
        </el-select>
        
        <el-select v-model="searchForm.level" placeholder="告警级别" clearable style="width: 120px">
          <el-option label="低" value="low" />
          <el-option label="中" value="medium" />
          <el-option label="高" value="high" />
          <el-option label="紧急" value="critical" />
        </el-select>
        
        <el-select v-model="searchForm.status" placeholder="处理状态" clearable style="width: 120px">
          <el-option label="未读" value="unread" />
          <el-option label="已读" value="read" />
          <el-option label="已处理" value="handled" />
          <el-option label="已忽略" value="ignored" />
        </el-select>
        
        <el-date-picker
          v-model="dateRange"
          type="datetimerange"
          range-separator="至"
          start-placeholder="开始时间"
          end-placeholder="结束时间"
          format="YYYY-MM-DD HH:mm:ss"
          value-format="YYYY-MM-DD HH:mm:ss"
          @change="handleDateChange"
          style="width: 350px"
        />
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-cards">
      <el-row :gutter="20">
        <el-col :span="6">
          <div class="stat-card">
            <div class="stat-icon unread">
              <el-icon><Bell /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ stats.unread_count }}</div>
              <div class="stat-label">未读告警</div>
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
              <div class="stat-label">紧急告警</div>
            </div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-card">
            <div class="stat-icon today">
              <el-icon><Calendar /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ stats.today_count }}</div>
              <div class="stat-label">今日告警</div>
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
              <div class="stat-label">总告警数</div>
            </div>
          </div>
        </el-col>
      </el-row>
    </div>

    <!-- 告警列表 -->
    <div class="table-container">
      <el-table
        :data="alarms"
        v-loading="loading"
        stripe
        style="width: 100%"
        @selection-change="handleSelectionChange"
        :row-class-name="getRowClassName"
      >
        <el-table-column type="selection" width="55" />
        
        <el-table-column label="缩略图" width="100">
          <template #default="{ row }">
            <el-image
              v-if="row.thumbnail_url"
              :src="row.thumbnail_url"
              :preview-src-list="[row.thumbnail_url]"
              fit="cover"
              style="width: 60px; height: 40px; border-radius: 4px"
            >
              <template #error>
                <div class="image-slot">
                  <el-icon><Picture /></el-icon>
                </div>
              </template>
            </el-image>
            <div v-else class="image-slot">
              <el-icon><Picture /></el-icon>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column prop="title" label="告警标题" min-width="200">
          <template #default="{ row }">
            <div class="alarm-title">
              <span class="title" :class="{ 'unread': row.status === 'unread' }">{{ row.title }}</span>
              <div class="alarm-meta">
                <el-tag :type="getAlarmTypeColor(row.alarm_type)" size="small">
                  {{ getAlarmTypeName(row.alarm_type) }}
                </el-tag>
                <el-tag :type="getLevelColor(row.level)" size="small">
                  {{ getLevelName(row.level) }}
                </el-tag>
              </div>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column prop="device_name" label="设备点位" width="150">
          <template #default="{ row }">
            <div class="device-info">
              <span class="device-name">{{ row.device_name }}</span>
              <span class="device-location" v-if="row.device_location">{{ row.device_location }}</span>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column prop="description" label="告警描述" min-width="200" show-overflow-tooltip />
        
        <el-table-column label="检测数据" width="120">
          <template #default="{ row }">
            <div v-if="row.detection_data" class="detection-data">
              <div v-if="row.detection_data.score !== undefined">
                分数: {{ (row.detection_data.score * 100).toFixed(1) }}%
              </div>
              <div v-if="row.detection_data.threshold !== undefined">
                阈值: {{ (row.detection_data.threshold * 100).toFixed(1) }}%
              </div>
            </div>
            <span v-else class="text-muted">无数据</span>
          </template>
        </el-table-column>
        
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusColor(row.status)" size="small">
              {{ getStatusName(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="created_at" label="告警时间" width="150">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="handleViewDetail(row)">详情</el-button>
            <el-button 
              size="small" 
              type="primary" 
              @click="handleMarkRead(row)"
              :disabled="row.status !== 'unread'"
            >
              标记已读
            </el-button>
            <el-dropdown @command="(command) => handleAction(command, row)">
              <el-button size="small">
                更多<el-icon class="el-icon--right"><ArrowDown /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="handle">标记已处理</el-dropdown-item>
                  <el-dropdown-item command="ignore">忽略</el-dropdown-item>
                  <el-dropdown-item command="delete" divided>删除</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
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

    <!-- 详情对话框 -->
    <el-dialog
      v-model="detailVisible"
      title="告警详情"
      width="800px"
    >
      <div v-if="currentAlarm" class="alarm-detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="告警标题">{{ currentAlarm.title }}</el-descriptions-item>
          <el-descriptions-item label="告警类型">
            <el-tag :type="getAlarmTypeColor(currentAlarm.alarm_type)">
              {{ getAlarmTypeName(currentAlarm.alarm_type) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="告警级别">
            <el-tag :type="getLevelColor(currentAlarm.level)">
              {{ getLevelName(currentAlarm.level) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="处理状态">
            <el-tag :type="getStatusColor(currentAlarm.status)">
              {{ getStatusName(currentAlarm.status) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="设备名称">{{ currentAlarm.device_name }}</el-descriptions-item>
          <el-descriptions-item label="设备位置">{{ currentAlarm.device_location || '未设置' }}</el-descriptions-item>
          <el-descriptions-item label="告警时间">{{ formatDateTime(currentAlarm.created_at) }}</el-descriptions-item>
          <el-descriptions-item label="更新时间">{{ formatDateTime(currentAlarm.updated_at) }}</el-descriptions-item>
        </el-descriptions>
        
        <div class="description-section">
          <h4>告警描述</h4>
          <el-card>
            <p>{{ currentAlarm.description }}</p>
          </el-card>
        </div>
        
        <div v-if="currentAlarm.detection_data" class="detection-section">
          <h4>检测数据</h4>
          <el-card>
            <pre>{{ JSON.stringify(currentAlarm.detection_data, null, 2) }}</pre>
          </el-card>
        </div>
        
        <div v-if="currentAlarm.thumbnail_url" class="image-section">
          <h4>告警图像</h4>
          <el-image
            :src="currentAlarm.thumbnail_url"
            :preview-src-list="[currentAlarm.thumbnail_url]"
            fit="contain"
            style="max-width: 100%; max-height: 400px"
          />
        </div>
        
        <div v-if="currentAlarm.media_files && currentAlarm.media_files.length > 0" class="media-section">
          <h4>相关媒体文件</h4>
          <div class="media-list">
            <div v-for="(file, index) in currentAlarm.media_files" :key="index" class="media-item">
              <el-link :href="file.url" target="_blank" type="primary">
                {{ file.filename || `文件${index + 1}` }}
              </el-link>
              <span class="file-type">{{ file.type }}</span>
            </div>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  Search, Refresh, Check, Delete, Bell, Warning, Calendar, DataBoard, 
  Picture, ArrowDown 
} from '@element-plus/icons-vue'
import { diagnosisAlarmApi, type DiagnosisAlarm } from '@/api/diagnosis'
import { formatDateTime } from '@/utils/date'

// 响应式数据
const loading = ref(false)
const alarms = ref<DiagnosisAlarm[]>([])
const selectedAlarms = ref<DiagnosisAlarm[]>([])
const dateRange = ref<[string, string] | null>(null)

// 分页
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)

// 搜索表单
const searchForm = reactive({
  search: '',
  alarm_type: '',
  level: '',
  status: '',
  start_time: '',
  end_time: ''
})

// 统计数据
const stats = ref({
  unread_count: 0,
  critical_count: 0,
  today_count: 0,
  total_count: 0
})

// 详情对话框
const detailVisible = ref(false)
const currentAlarm = ref<DiagnosisAlarm | null>(null)

// 计算属性和方法
const getAlarmTypeName = (type: string) => {
  const typeMap: Record<string, string> = {
    brightness: '亮度异常',
    blue_screen: '蓝屏检测',
    clarity: '清晰度异常',
    shake: '画面抖动',
    freeze: '画面冻结',
    color_cast: '偏色检测',
    occlusion: '遮挡检测',
    noise: '噪声检测',
    contrast: '对比度异常',
    mosaic: '马赛克检测',
    flower_screen: '花屏检测'
  }
  return typeMap[type] || type
}

const getAlarmTypeColor = (type: string) => {
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

const getLevelName = (level: string) => {
  const levelMap: Record<string, string> = {
    low: '低',
    medium: '中',
    high: '高',
    critical: '紧急'
  }
  return levelMap[level] || level
}

const getLevelColor = (level: string) => {
  const colorMap: Record<string, string> = {
    low: 'info',
    medium: 'warning',
    high: 'danger',
    critical: 'danger'
  }
  return colorMap[level] || 'info'
}

const getStatusName = (status: string) => {
  const statusMap: Record<string, string> = {
    unread: '未读',
    read: '已读',
    handled: '已处理',
    ignored: '已忽略'
  }
  return statusMap[status] || status
}

const getStatusColor = (status: string) => {
  const colorMap: Record<string, string> = {
    unread: 'danger',
    read: 'primary',
    handled: 'success',
    ignored: 'info'
  }
  return colorMap[status] || 'info'
}

const getRowClassName = ({ row }: { row: DiagnosisAlarm }) => {
  if (row.status === 'unread') {
    return 'unread-row'
  }
  return ''
}

// 方法
const loadAlarms = async () => {
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
    
    const response = await diagnosisAlarmApi.getAlarms(params)
    alarms.value = response.data || []
    // 后端返回的是数组，不是分页格式，所以total设置为数组长度
    total.value = (response.data || []).length
    
    // 更新统计数据
    updateStats()
  } catch (error) {
    console.error('加载告警列表失败:', error)
    ElMessage.error('加载告警列表失败')
  } finally {
    loading.value = false
  }
}

const updateStats = () => {
  const today = new Date().toDateString()
  stats.value = {
    unread_count: alarms.value.filter(a => a.status === 'unread').length,
    critical_count: alarms.value.filter(a => a.level === 'critical').length,
    today_count: alarms.value.filter(a => new Date(a.created_at).toDateString() === today).length,
    total_count: alarms.value.length
  }
}

const handleSearch = () => {
  currentPage.value = 1
  loadAlarms()
}

const handleReset = () => {
  Object.assign(searchForm, {
    search: '',
    alarm_type: '',
    level: '',
    status: '',
    start_time: '',
    end_time: ''
  })
  dateRange.value = null
  currentPage.value = 1
  loadAlarms()
}

const handleDateChange = (dates: [string, string] | null) => {
  if (dates) {
    searchForm.start_time = dates[0]
    searchForm.end_time = dates[1]
  } else {
    searchForm.start_time = ''
    searchForm.end_time = ''
  }
}

const handleSizeChange = (size: number) => {
  pageSize.value = size
  currentPage.value = 1
  loadAlarms()
}

const handleCurrentChange = (page: number) => {
  currentPage.value = page
  loadAlarms()
}

const handleSelectionChange = (selection: DiagnosisAlarm[]) => {
  selectedAlarms.value = selection
}

const handleViewDetail = (alarm: DiagnosisAlarm) => {
  currentAlarm.value = alarm
  detailVisible.value = true
  
  // 如果是未读状态，自动标记为已读
  if (alarm.status === 'unread') {
    handleMarkRead(alarm)
  }
}

const handleMarkRead = async (alarm: DiagnosisAlarm) => {
  try {
    await diagnosisAlarmApi.updateAlarmStatus(alarm.id, 'read')
    alarm.status = 'read'
    ElMessage.success('已标记为已读')
    updateStats()
  } catch (error) {
    console.error('标记已读失败:', error)
    ElMessage.error('操作失败')
  }
}

const handleMarkAllRead = async () => {
  try {
    const unreadIds = selectedAlarms.value
      .filter(alarm => alarm.status === 'unread')
      .map(alarm => alarm.id)
    
    if (unreadIds.length === 0) {
      ElMessage.warning('没有未读告警需要标记')
      return
    }
    
    await diagnosisAlarmApi.batchUpdateStatus(unreadIds, 'read')
    
    // 更新本地状态
    selectedAlarms.value.forEach(alarm => {
      if (alarm.status === 'unread') {
        alarm.status = 'read'
      }
    })
    
    ElMessage.success(`已标记 ${unreadIds.length} 条告警为已读`)
    updateStats()
  } catch (error) {
    console.error('批量标记已读失败:', error)
    ElMessage.error('操作失败')
  }
}

const handleAction = async (command: string, alarm: DiagnosisAlarm) => {
  try {
    let statusMap: Record<string, string> = {
      handle: 'handled',
      ignore: 'ignored'
    }
    
    if (command === 'delete') {
      await ElMessageBox.confirm(
        `确定要删除告警 "${alarm.title}" 吗？`,
        '确认删除',
        {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        }
      )
      
      await diagnosisAlarmApi.deleteAlarm(alarm.id)
      ElMessage.success('删除成功')
      loadAlarms()
    } else {
      await diagnosisAlarmApi.updateAlarmStatus(alarm.id, statusMap[command])
      alarm.status = statusMap[command]
      ElMessage.success('操作成功')
      updateStats()
    }
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('操作失败:', error)
      ElMessage.error('操作失败')
    }
  }
}

const handleClearAll = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要清空所有告警吗？此操作不可恢复！',
      '确认清空',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await diagnosisAlarmApi.clearAllAlarms()
    ElMessage.success('清空成功')
    loadAlarms()
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('清空失败:', error)
      ElMessage.error('操作失败')
    }
  }
}

// 生命周期
onMounted(() => {
  loadAlarms()
})
</script>

<style scoped>
.diagnosis-alarms {
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

.stats-cards {
  margin-bottom: 20px;
}

.stat-card {
  background: #fff;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  color: #fff;
}

.stat-icon.unread {
  background: #F56C6C;
}

.stat-icon.critical {
  background: #E6A23C;
}

.stat-icon.today {
  background: #409EFF;
}

.stat-icon.total {
  background: #67C23A;
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 28px;
  font-weight: 600;
  line-height: 1;
  margin-bottom: 4px;
}

.stat-label {
  color: #666;
  font-size: 14px;
}

.table-container {
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.image-slot {
  width: 60px;
  height: 40px;
  background: #f5f5f5;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #ccc;
}

.alarm-title {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.alarm-title .title {
  font-weight: 500;
}

.alarm-title .title.unread {
  font-weight: 600;
  color: #F56C6C;
}

.alarm-meta {
  display: flex;
  gap: 4px;
}

.device-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.device-name {
  font-weight: 500;
}

.device-location {
  font-size: 12px;
  color: #999;
}

.detection-data {
  font-size: 12px;
  line-height: 1.4;
}

.text-muted {
  color: #999;
}

.pagination-container {
  padding: 20px;
  text-align: right;
}

:deep(.unread-row) {
  background-color: #fef0f0;
}

.alarm-detail {
  max-height: 600px;
  overflow-y: auto;
}

.description-section,
.detection-section,
.image-section,
.media-section {
  margin-top: 20px;
}

.description-section h4,
.detection-section h4,
.image-section h4,
.media-section h4 {
  margin: 0 0 12px 0;
  font-size: 16px;
  font-weight: 600;
}

.detection-section pre {
  background: #f5f5f5;
  padding: 12px;
  border-radius: 4px;
  font-size: 12px;
  line-height: 1.4;
  max-height: 200px;
  overflow-y: auto;
}

.media-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.media-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px;
  background: #f5f5f5;
  border-radius: 4px;
}

.file-type {
  font-size: 12px;
  color: #999;
  background: #e4e7ed;
  padding: 2px 6px;
  border-radius: 2px;
}
</style>