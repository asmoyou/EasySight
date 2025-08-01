<template>
  <div class="events-list">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <h2>事件列表</h2>
        <p class="page-description">查看和管理系统中的所有事件记录</p>
      </div>
      <div class="header-right">
        <el-button type="primary" @click="refreshEvents">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>
    </div>

    <!-- 搜索筛选 -->
    <el-card class="search-card" shadow="never">
      <el-form :model="searchForm" inline>
        <el-form-item label="事件类型">
          <el-select v-model="searchForm.event_type" placeholder="请选择事件类型" clearable>
            <el-option label="入侵检测" value="intrusion" />
            <el-option label="火灾检测" value="fire" />
            <el-option label="烟雾检测" value="smoke" />
            <el-option label="暴力行为" value="violence" />
            <el-option label="人群聚集" value="crowd" />
            <el-option label="车辆检测" value="vehicle" />
            <el-option label="人脸识别" value="face" />
            <el-option label="异常行为" value="abnormal_behavior" />
            <el-option label="物品遗留" value="object_left" />
            <el-option label="物品移除" value="object_removed" />
            <el-option label="周界入侵" value="perimeter_breach" />
            <el-option label="徘徊检测" value="loitering" />
          </el-select>
        </el-form-item>
        <el-form-item label="事件级别">
          <el-select v-model="searchForm.event_level" placeholder="请选择事件级别" clearable>
            <el-option label="低级" value="low" />
            <el-option label="中级" value="medium" />
            <el-option label="高级" value="high" />
            <el-option label="严重" value="critical" />
          </el-select>
        </el-form-item>
        <el-form-item label="摄像头">
          <el-input
            v-model="searchForm.camera_name"
            placeholder="请输入摄像头名称"
            clearable
            style="width: 200px"
          />
        </el-form-item>
        <el-form-item label="时间范围">
          <el-date-picker
            v-model="searchForm.dateRange"
            type="datetimerange"
            range-separator="至"
            start-placeholder="开始时间"
            end-placeholder="结束时间"
            format="YYYY-MM-DD HH:mm:ss"
            value-format="YYYY-MM-DD HH:mm:ss"
          />
        </el-form-item>
        <el-form-item label="事件状态">
          <el-select v-model="searchForm.is_ongoing" placeholder="请选择事件状态" clearable>
            <el-option label="进行中" value="true" />
            <el-option label="已结束" value="false" />
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

    <!-- 事件列表 -->
    <el-card class="table-card" shadow="never">
      <el-table
        v-loading="loading"
        :data="events"
        stripe
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column label="缩略图" width="100">
          <template #default="{ row }">
            <div class="thumbnail-container">
              <el-image
                v-if="row.thumbnail_url || (row.image_urls && row.image_urls.length > 0)"
                :src="row.thumbnail_url || row.image_urls[0]"
                :preview-src-list="row.image_urls || []"
                fit="cover"
                class="event-thumbnail"
                :preview-teleported="true"
              >
                <template #error>
                  <div class="image-slot">
                    <el-icon><Picture /></el-icon>
                  </div>
                </template>
              </el-image>
              <div v-else class="no-image">
                <el-icon><Picture /></el-icon>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="event_type" label="事件类型" width="120">
          <template #default="{ row }">
            <el-tag :type="getEventTypeColor(row.event_type)">
              {{ getEventTypeName(row.event_type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="event_level" label="级别" width="100">
          <template #default="{ row }">
            <el-tag :type="getLevelColor(row.event_level)">
              {{ getLevelName(row.event_level) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="设备信息" min-width="200">
          <template #default="{ row }">
            <div class="device-info">
              <div class="device-name">{{ row.camera_name }}</div>
              <div class="device-location">{{ row.camera_location }}</div>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="算法信息" min-width="150">
          <template #default="{ row }">
            <div class="algorithm-info">
              <div class="algorithm-name">{{ row.algorithm_name }}</div>
              <div class="confidence-score">置信度: {{ (row.confidence_score * 100).toFixed(1) }}%</div>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="title" label="事件标题" min-width="180" show-overflow-tooltip />
        <el-table-column label="检测对象" width="120">
          <template #default="{ row }">
            <el-tag v-if="row.object_count > 0" type="info" size="small">
              {{ row.object_count }} 个对象
            </el-tag>
            <span v-else class="no-objects">无</span>
          </template>
        </el-table-column>
        <el-table-column prop="start_time" label="开始时间" width="160">
          <template #default="{ row }">
            {{ formatDateTime(row.start_time) }}
          </template>
        </el-table-column>
        <el-table-column prop="end_time" label="结束时间" width="160">
          <template #default="{ row }">
            <span v-if="row.end_time">{{ formatDateTime(row.end_time) }}</span>
            <el-tag v-else type="success" size="small">进行中</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="duration" label="持续时间" width="120">
          <template #default="{ row }">
            <span v-if="row.duration">{{ formatDuration(row.duration) }}</span>
            <span v-else-if="row.is_ongoing">{{ calculateDuration(row.start_time) }}</span>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusColor(row.status)" size="small">
              {{ getStatusName(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="280" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="viewDetail(row)">
              详情
            </el-button>
            <el-button 
              v-if="row.video_urls && row.video_urls.length > 0" 
              type="success" 
              size="small" 
              @click="playVideo(row)"
            >
              视频
            </el-button>
            <el-dropdown v-if="row.status === 'pending'" trigger="click">
              <el-button type="warning" size="small">
                处理 <el-icon class="el-icon--right"><arrow-down /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item @click="confirmEvent(row)">
                    <el-icon><Check /></el-icon>
                    确认报警
                  </el-dropdown-item>
                  <el-dropdown-item @click="markFalseAlarm(row)">
                    <el-icon><Close /></el-icon>
                    标记误报
                  </el-dropdown-item>
                  <el-dropdown-item divided @click="markAsRead(row)">
                    <el-icon><View /></el-icon>
                    标记已读
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
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

    <!-- 事件详情对话框 -->
    <el-dialog
      v-model="detailDialogVisible"
      title="事件详情"
      width="1000px"
      destroy-on-close
    >
      <div v-if="currentEvent" class="event-detail">
        <!-- 基本信息 -->
        <el-card class="detail-card" shadow="never">
          <template #header>
            <span class="card-title">基本信息</span>
          </template>
          <el-descriptions :column="3" border>
            <el-descriptions-item label="事件ID">{{ currentEvent.event_id }}</el-descriptions-item>
            <el-descriptions-item label="事件类型">
              <el-tag :type="getEventTypeColor(currentEvent.event_type)">
                {{ getEventTypeName(currentEvent.event_type) }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="事件级别">
              <el-tag :type="getLevelColor(currentEvent.event_level)">
                {{ getLevelName(currentEvent.event_level) }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="事件标题" :span="3">
              {{ currentEvent.title }}
            </el-descriptions-item>
            <el-descriptions-item label="事件描述" :span="3">
              {{ currentEvent.description }}
            </el-descriptions-item>
            <el-descriptions-item label="开始时间">
              {{ formatDateTime(currentEvent.start_time) }}
            </el-descriptions-item>
            <el-descriptions-item label="结束时间">
              <span v-if="currentEvent.end_time">{{ formatDateTime(currentEvent.end_time) }}</span>
              <el-tag v-else type="success" size="small">进行中</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="持续时间">
              <span v-if="currentEvent.duration">{{ formatDuration(currentEvent.duration) }}</span>
              <span v-else-if="currentEvent.is_ongoing">{{ calculateDuration(currentEvent.start_time) }}</span>
              <span v-else>-</span>
            </el-descriptions-item>
            <el-descriptions-item label="状态">
              <el-tag :type="getStatusColor(currentEvent.status)">
                {{ getStatusName(currentEvent.status) }}
              </el-tag>
            </el-descriptions-item>
          </el-descriptions>
        </el-card>

        <!-- 设备信息 -->
        <el-card class="detail-card" shadow="never">
          <template #header>
            <span class="card-title">设备信息</span>
          </template>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="摄像头ID">{{ currentEvent.camera_id }}</el-descriptions-item>
            <el-descriptions-item label="摄像头名称">{{ currentEvent.camera_name }}</el-descriptions-item>
            <el-descriptions-item label="设备位置" :span="2">{{ currentEvent.camera_location }}</el-descriptions-item>
            <el-descriptions-item v-if="currentEvent.longitude && currentEvent.latitude" label="GPS坐标" :span="2">
              {{ currentEvent.longitude }}, {{ currentEvent.latitude }}
            </el-descriptions-item>
          </el-descriptions>
        </el-card>

        <!-- AI算法信息 -->
        <el-card class="detail-card" shadow="never">
          <template #header>
            <span class="card-title">AI算法信息</span>
          </template>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="算法名称">{{ currentEvent.algorithm_name }}</el-descriptions-item>
            <el-descriptions-item label="置信度分数">{{ (currentEvent.confidence_score * 100).toFixed(2) }}%</el-descriptions-item>
            <el-descriptions-item label="检测对象数量">{{ currentEvent.object_count }}</el-descriptions-item>
            <el-descriptions-item label="检测对象">
              <div v-if="currentEvent.detected_objects && currentEvent.detected_objects.length > 0">
                <el-tag 
                  v-for="(obj, index) in currentEvent.detected_objects" 
                  :key="index" 
                  size="small" 
                  style="margin-right: 5px; margin-bottom: 5px;"
                >
                  {{ obj.class_name || obj.name || '未知对象' }}
                  <span v-if="obj.confidence">({{ (obj.confidence * 100).toFixed(1) }}%)</span>
                </el-tag>
              </div>
              <span v-else>无检测对象</span>
            </el-descriptions-item>
          </el-descriptions>
        </el-card>

        <!-- 图片信息 -->
        <el-card v-if="currentEvent.image_urls && currentEvent.image_urls.length > 0" class="detail-card" shadow="never">
          <template #header>
            <span class="card-title">相关图片</span>
          </template>
          <div class="image-gallery">
            <el-image
              v-for="(url, index) in currentEvent.image_urls"
              :key="index"
              :src="url"
              :preview-src-list="currentEvent.image_urls"
              :initial-index="index"
              fit="cover"
              class="gallery-image"
              :preview-teleported="true"
            >
              <template #error>
                <div class="image-slot">
                  <el-icon><Picture /></el-icon>
                </div>
              </template>
            </el-image>
          </div>
        </el-card>

        <!-- 视频信息 -->
        <el-card v-if="currentEvent.video_urls && currentEvent.video_urls.length > 0" class="detail-card" shadow="never">
          <template #header>
            <span class="card-title">相关视频</span>
          </template>
          <div class="video-list">
            <div 
              v-for="(url, index) in currentEvent.video_urls" 
              :key="index" 
              class="video-item"
            >
              <el-button type="primary" @click="playVideoUrl(url)">
                <el-icon><VideoPlay /></el-icon>
                播放视频 {{ index + 1 }}
              </el-button>
              <span class="video-url">{{ url }}</span>
            </div>
          </div>
        </el-card>

        <!-- 扩展信息 -->
        <el-card v-if="currentEvent.event_metadata" class="detail-card" shadow="never">
          <template #header>
            <span class="card-title">扩展信息</span>
          </template>
          <pre class="metadata-content">{{ JSON.stringify(currentEvent.event_metadata, null, 2) }}</pre>
        </el-card>
      </div>
    </el-dialog>

    <!-- 视频播放对话框 -->
    <el-dialog
      v-model="videoDialogVisible"
      title="视频播放"
      width="800px"
      destroy-on-close
    >
      <div v-if="currentVideoUrl" class="video-player">
        <video 
          :src="currentVideoUrl" 
          controls 
          width="100%" 
          height="400px"
          preload="metadata"
        >
          您的浏览器不支持视频播放。
        </video>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Picture, VideoPlay, Check, Close, View, ArrowDown } from '@element-plus/icons-vue'
import { Search, Refresh, RefreshLeft } from '@element-plus/icons-vue'
import * as eventsApi from '@/api/events'
import type { Event, EventQuery } from '@/api/events'

// 类型定义
interface Event {
  id: number
  event_id: string
  event_type: string
  event_level: string
  title: string
  description: string
  camera_id: number
  camera_name: string
  camera_location: string
  algorithm_name: string
  confidence_score: number
  longitude?: number
  latitude?: number
  location_description?: string
  image_urls: string[]
  video_urls: string[]
  thumbnail_url?: string
  detected_objects: any[]
  object_count: number
  status: string
  is_read: boolean
  event_time: string
  start_time: string
  end_time?: string
  duration?: number
  is_ongoing: boolean
  created_at: string
  event_metadata?: any
}

// 响应式数据
const loading = ref(false)
const events = ref<Event[]>([])
const selectedEvents = ref<Event[]>([])
const detailDialogVisible = ref(false)
const currentEvent = ref<Event | null>(null)
const videoDialogVisible = ref(false)
const currentVideoUrl = ref('')

// 搜索表单
const searchForm = reactive({
  event_type: '',
  event_level: '',
  camera_name: '',
  dateRange: [] as string[],
  is_ongoing: ''
})

// 分页
const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

// 方法
const loadEvents = async () => {
  loading.value = true
  try {
    const params: EventQuery = {
      page: pagination.page,
      page_size: pagination.pageSize
    }
    
    // 添加搜索条件
    if (searchForm.event_type) {
      params.event_type = searchForm.event_type
    }
    if (searchForm.event_level) {
      params.event_level = searchForm.event_level
    }
    if (searchForm.camera_name) {
      params.camera_name = searchForm.camera_name
    }
    if (searchForm.is_ongoing !== '') {
      params.is_ongoing = searchForm.is_ongoing === 'true'
    }
    if (searchForm.dateRange && searchForm.dateRange.length === 2) {
      params.start_date = searchForm.dateRange[0]
      params.end_date = searchForm.dateRange[1]
    }

    const response = await eventsApi.getEvents(params)
    events.value = response.events
    pagination.total = response.total
  } catch (error) {
    console.error('加载事件数据失败:', error)
    ElMessage.error('加载事件列表失败')
    // 如果API调用失败，使用模拟数据作为后备
    const mockEvents: Event[] = [
      {
        id: 1,
        event_id: 'EVT-2024-001',
        event_type: 'intrusion',
        event_level: 'high',
        title: '入侵检测告警',
        description: '检测到未授权人员进入禁区A区，触发高级别安全警报',
        camera_id: 1,
        camera_name: '大门入口摄像头',
        camera_location: '主楼大门入口处',
        longitude: 116.397428,
        latitude: 39.90923,
        algorithm_name: '入侵检测算法v2.1',
        confidence_score: 0.95,
        object_count: 2,
        detected_objects: [
          { class_name: '人员', confidence: 0.95, bbox: [100, 150, 200, 350] },
          { class_name: '车辆', confidence: 0.88, bbox: [300, 200, 500, 400] }
        ],
        image_urls: [
          'https://via.placeholder.com/400x300/ff6b6b/ffffff?text=入侵检测图片1',
          'https://via.placeholder.com/400x300/4ecdc4/ffffff?text=入侵检测图片2'
        ],
        video_urls: [
          'https://sample-videos.com/zip/10/mp4/SampleVideo_1280x720_1mb.mp4'
        ],
        thumbnail_url: 'https://via.placeholder.com/100x75/ff6b6b/ffffff?text=缩略图1',
        status: 'pending',
        is_read: false,
        event_time: '2024-01-15 14:30:25',
        start_time: '2024-01-15 14:30:25',
        end_time: null,
        duration: null,
        is_ongoing: true,
        created_at: '2024-01-15 14:30:25',
        event_metadata: {
          zone: 'A区',
          alert_level: 'critical',
          auto_tracking: true
        }
      },
      {
        id: 2,
        event_id: 'EVT-2024-002',
        event_type: 'face',
        event_level: 'medium',
        title: '人脸识别告警',
        description: '检测到陌生人员，未在系统白名单中',
        camera_id: 2,
        camera_name: '办公区监控摄像头',
        camera_location: '办公楼2层走廊',
        longitude: 116.398428,
        latitude: 39.91023,
        algorithm_name: '人脸识别算法v3.0',
        confidence_score: 0.87,
        object_count: 1,
        detected_objects: [
          { class_name: '未知人员', confidence: 0.87, bbox: [150, 100, 250, 300] }
        ],
        image_urls: [
          'https://via.placeholder.com/400x300/45b7d1/ffffff?text=人脸识别图片'
        ],
        video_urls: [
          'https://sample-videos.com/zip/10/mp4/SampleVideo_640x360_1mb.mp4'
        ],
        thumbnail_url: 'https://via.placeholder.com/100x75/45b7d1/ffffff?text=缩略图2',
        status: 'confirmed',
        is_read: true,
        event_time: '2024-01-15 13:45:12',
        start_time: '2024-01-15 13:45:12',
        end_time: '2024-01-15 13:47:30',
        duration: 138,
        is_ongoing: false,
        created_at: '2024-01-15 13:45:12',
        event_metadata: {
          face_quality: 'high',
          age_estimate: '25-35',
          gender: 'male'
        }
      },
      {
        id: 3,
        event_id: 'EVT-2024-003',
        event_type: 'object_left',
        event_level: 'low',
        title: '物体检测告警',
        description: '检测到可疑遗留物品',
        camera_id: 3,
        camera_name: '停车场监控摄像头',
        camera_location: '地下停车场B区',
        longitude: 116.399428,
        latitude: 39.91123,
        algorithm_name: '物体检测算法v1.8',
        confidence_score: 0.78,
        object_count: 1,
        detected_objects: [
          { class_name: '背包', confidence: 0.78, bbox: [200, 250, 280, 350] }
        ],
        image_urls: [
          'https://via.placeholder.com/400x300/96ceb4/ffffff?text=物体检测图片'
        ],
        video_urls: [],
        thumbnail_url: 'https://via.placeholder.com/100x75/96ceb4/ffffff?text=缩略图3',
        status: 'false_alarm',
        is_read: true,
        event_time: '2024-01-15 12:20:08',
        start_time: '2024-01-15 12:20:08',
        end_time: '2024-01-15 12:25:08',
        duration: 300,
        is_ongoing: false,
        created_at: '2024-01-15 12:20:08',
        event_metadata: {
          object_size: 'medium',
          duration: '5分钟',
          risk_level: 'low'
        }
      }
    ]
    events.value = mockEvents
    pagination.total = mockEvents.length
  } finally {
    loading.value = false
  }
}

const refreshEvents = () => {
  loadEvents()
}

const handleSearch = () => {
  pagination.page = 1
  loadEvents()
}

const handleReset = () => {
  searchForm.event_type = ''
  searchForm.event_level = ''
  searchForm.camera_name = ''
  searchForm.dateRange = []
  searchForm.is_ongoing = ''
  pagination.page = 1
  loadEvents()
}

const handleSelectionChange = (selection: Event[]) => {
  selectedEvents.value = selection
}

const handleSizeChange = (size: number) => {
  pagination.pageSize = size
  pagination.page = 1
  loadEvents()
}

const handleCurrentChange = (page: number) => {
  pagination.page = page
  loadEvents()
}

const viewDetail = (event: Event) => {
  currentEvent.value = event
  detailDialogVisible.value = true
}

// 播放视频
const playVideo = (event: Event) => {
  if (event.video_urls && event.video_urls.length > 0) {
    currentVideoUrl.value = event.video_urls[0]
    videoDialogVisible.value = true
  } else {
    ElMessage.warning('该事件没有关联的视频文件')
  }
}

// 播放指定视频URL
const playVideoUrl = (url: string) => {
  currentVideoUrl.value = url
  videoDialogVisible.value = true
}

// 确认报警
const confirmEvent = async (event: Event) => {
  try {
    await eventsApi.confirmEvent(event.id, { resolution_notes: '' })
    ElMessage.success('已确认报警')
    loadEvents() // 刷新列表
  } catch (error) {
    console.error('确认报警失败:', error)
    ElMessage.error('确认报警失败')
  }
}

// 标记误报
const markFalseAlarm = async (event: Event) => {
  try {
    await eventsApi.markFalseAlarm(event.id, { resolution_notes: '' })
    ElMessage.success('已标记为误报')
    loadEvents() // 刷新列表
  } catch (error) {
    console.error('标记误报失败:', error)
    ElMessage.error('标记误报失败')
  }
}

// 标记为已读
const markAsRead = async (event: Event) => {
  try {
    await eventsApi.markAsRead(event.id)
    ElMessage.success('已标记为已读')
    loadEvents() // 刷新列表
  } catch (error) {
    console.error('标记已读失败:', error)
    ElMessage.error('标记失败')
  }
}

// 获取状态颜色
const getStatusColor = (status: string) => {
  const statusColors: Record<string, string> = {
    'pending': 'warning',
    'confirmed': 'success',
    'false_alarm': 'danger',
    'ignored': 'info'
  }
  return statusColors[status] || 'info'
}

// 获取状态名称
const getStatusName = (status: string) => {
  const statusNames: Record<string, string> = {
    'pending': '待处理',
    'confirmed': '确认报警',
    'false_alarm': '误报',
    'ignored': '已忽略'
  }
  return statusNames[status] || '未知'
}

// 辅助函数
const getEventTypeColor = (type: string) => {
  const colors: Record<string, string> = {
    'intrusion': 'danger',
    'face': 'warning',
    'object_left': 'primary',
    'behavior': 'success',
    'fire': 'danger',
    'smoke': 'warning',
    'vehicle': 'info',
    'crowd': 'warning'
  }
  return colors[type] || 'info'
}

const getEventTypeName = (type: string) => {
  const names: Record<string, string> = {
    'intrusion': '入侵检测',
    'face': '人脸识别',
    'object_left': '物品遗留',
    'behavior': '行为分析',
    'fire': '火灾检测',
    'smoke': '烟雾检测',
    'vehicle': '车辆检测',
    'crowd': '人群聚集'
  }
  return names[type] || type
}

const getLevelColor = (level: string) => {
  const colors: Record<string, string> = {
    low: 'info',
    medium: 'warning',
    high: 'danger',
    critical: 'danger'
  }
  return colors[level] || 'info'
}

const getLevelName = (level: string) => {
  const names: Record<string, string> = {
    low: '低级',
    medium: '中级',
    high: '高级',
    critical: '严重'
  }
  return names[level] || level
}

const formatDateTime = (dateTime: string) => {
  return new Date(dateTime).toLocaleString('zh-CN')
}

const formatDuration = (seconds: number) => {
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const secs = seconds % 60
  
  if (hours > 0) {
    return `${hours}小时${minutes}分${secs}秒`
  } else if (minutes > 0) {
    return `${minutes}分${secs}秒`
  } else {
    return `${secs}秒`
  }
}

const calculateDuration = (startTime: string) => {
  const start = new Date(startTime)
  const now = new Date()
  const diffInSeconds = Math.floor((now.getTime() - start.getTime()) / 1000)
  return formatDuration(diffInSeconds)
}

// 生命周期
onMounted(() => {
  loadEvents()
})
</script>

<style scoped>
.events-list {
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

.event-detail {
  max-height: 70vh;
  overflow-y: auto;
}

.detail-card {
  margin-bottom: 16px;
}

.detail-card:last-child {
  margin-bottom: 0;
}

.card-title {
  font-weight: 600;
  color: #303133;
}

.image-gallery {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.gallery-image {
  width: 120px;
  height: 90px;
  border-radius: 8px;
  cursor: pointer;
  transition: transform 0.2s;
}

.gallery-image:hover {
  transform: scale(1.05);
}

.image-slot {
  display: flex;
  justify-content: center;
  align-items: center;
  width: 100%;
  height: 100%;
  background: #f5f7fa;
  color: #909399;
}

.video-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.video-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: #f8f9fa;
  border-radius: 8px;
}

.video-url {
  font-size: 12px;
  color: #666;
  word-break: break-all;
}

.video-player {
  text-align: center;
}

.metadata-content {
  background: #f5f5f5;
  padding: 12px;
  border-radius: 4px;
  max-height: 200px;
  overflow-y: auto;
  font-size: 12px;
  line-height: 1.4;
}

.thumbnail-container {
  display: flex;
  justify-content: center;
  align-items: center;
}

.event-thumbnail {
  width: 60px;
  height: 45px;
  border-radius: 4px;
}

.no-image {
  width: 60px;
  height: 45px;
  display: flex;
  justify-content: center;
  align-items: center;
  background: #f5f7fa;
  color: #909399;
  border-radius: 4px;
}

.device-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.device-name {
  font-weight: 500;
  color: #303133;
}

.device-location {
  font-size: 12px;
  color: #909399;
}

.algorithm-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.algorithm-name {
  font-weight: 500;
  color: #303133;
}

.confidence-score {
  font-size: 12px;
  color: #67c23a;
  font-weight: 500;
}

.no-objects {
  color: #909399;
  font-size: 12px;
}

.event-detail pre {
  background-color: #f5f7fa;
  padding: 10px;
  border-radius: 4px;
  font-size: 12px;
  max-height: 200px;
  overflow-y: auto;
}
</style>