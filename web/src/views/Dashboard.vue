<template>
  <div class="dashboard" v-loading="loading">
    <!-- 统计卡片 -->
    <div class="stats-grid">
      <el-card class="stats-card" shadow="hover">
        <div class="stats-content">
          <div class="stats-icon camera">
            <el-icon :size="32"><VideoCamera /></el-icon>
          </div>
          <div class="stats-info">
            <div class="stats-value">{{ stats.total_cameras }}</div>
        <div class="stats-label">摄像头总数</div>
          </div>
        </div>
        <div class="stats-trend positive">
          <el-icon><TrendCharts /></el-icon>
          <span>+12%</span>
        </div>
      </el-card>
      
      <el-card class="stats-card" shadow="hover">
        <div class="stats-content">
          <div class="stats-icon online">
            <el-icon :size="32"><Connection /></el-icon>
          </div>
          <div class="stats-info">
            <div class="stats-value">{{ stats.online_cameras }}</div>
        <div class="stats-label">在线摄像头</div>
          </div>
        </div>
        <div class="stats-trend positive">
          <el-icon><TrendCharts /></el-icon>
          <span>+5%</span>
        </div>
      </el-card>
      
      <el-card class="stats-card" shadow="hover">
        <div class="stats-content">
          <div class="stats-icon events">
            <el-icon :size="32"><Warning /></el-icon>
          </div>
          <div class="stats-info">
            <div class="stats-value">{{ stats.today_events }}</div>
        <div class="stats-label">今日事件</div>
          </div>
        </div>
        <div class="stats-trend negative">
          <el-icon><TrendCharts /></el-icon>
          <span>-8%</span>
        </div>
      </el-card>
      
      <el-card class="stats-card" shadow="hover">
        <div class="stats-content">
          <div class="stats-icon tasks">
            <el-icon :size="32"><Monitor /></el-icon>
          </div>
          <div class="stats-info">
            <div class="stats-value">{{ stats.running_tasks }}</div>
        <div class="stats-label">运行任务</div>
          </div>
        </div>
        <div class="stats-trend positive">
          <el-icon><TrendCharts /></el-icon>
          <span>+15%</span>
        </div>
      </el-card>
    </div>
    
    <!-- 图表区域 -->
    <div class="charts-grid">
      <!-- 事件趋势图 -->
      <el-card class="chart-card" shadow="hover">
        <template #header>
          <div class="card-header">
            <span class="card-title">事件趋势</span>
            <el-select v-model="eventTrendPeriod" size="small" style="width: 120px" @change="fetchDashboardData">
              <el-option label="最近7天" value="7d" />
              <el-option label="最近30天" value="30d" />
              <el-option label="最近90天" value="90d" />
            </el-select>
          </div>
        </template>
        <div ref="eventTrendChart" class="chart-container"></div>
      </el-card>
      
      <!-- 摄像头状态分布 -->
      <el-card class="chart-card" shadow="hover">
        <template #header>
          <span class="card-title">摄像头状态分布</span>
        </template>
        <div ref="cameraStatusChart" class="chart-container"></div>
      </el-card>
    </div>
    
    <!-- 详细信息区域 -->
    <div class="details-grid">
      <!-- 最近事件 -->
      <el-card class="details-card" shadow="hover">
        <template #header>
          <div class="card-header">
            <span class="card-title">最近事件</span>
            <el-button type="primary" size="small" @click="$router.push('/events/list')">
              查看全部
            </el-button>
          </div>
        </template>
        <div class="events-list">
          <div
            v-for="event in recentEvents"
            :key="event.id"
            class="event-item"
          >
            <div class="event-icon" :class="event.level">
              <el-icon><Warning /></el-icon>
            </div>
            <div class="event-content">
              <div class="event-title">{{ event.title }}</div>
              <div class="event-meta">
                <span class="event-camera">{{ event.camera }}</span>
                <span class="event-time">{{ formatTime(event.time) }}</span>
              </div>
            </div>
            <div class="event-status" :class="event.status">
              {{ getStatusText(event.status) }}
            </div>
          </div>
        </div>
      </el-card>
      
      <!-- 系统状态 -->
      <el-card class="details-card" shadow="hover">
        <template #header>
          <span class="card-title">系统状态</span>
        </template>
        <div class="system-status">
          <div class="status-item">
            <div class="status-label">CPU使用率</div>
            <div class="status-value">
              <el-progress
                :percentage="systemStatus.cpu"
                :color="getProgressColor(systemStatus.cpu)"
                :show-text="false"
              />
              <span class="percentage">{{ systemStatus.cpu }}%</span>
            </div>
          </div>
          
          <div class="status-item">
            <div class="status-label">内存使用率</div>
            <div class="status-value">
              <el-progress
                :percentage="systemStatus.memory"
                :color="getProgressColor(systemStatus.memory)"
                :show-text="false"
              />
              <span class="percentage">{{ systemStatus.memory }}%</span>
            </div>
          </div>
          
          <div class="status-item">
            <div class="status-label">磁盘使用率</div>
            <div class="status-value">
              <el-progress
                :percentage="systemStatus.disk"
                :color="getProgressColor(systemStatus.disk)"
                :show-text="false"
              />
              <span class="percentage">{{ systemStatus.disk }}%</span>
            </div>
          </div>
          
          <div class="status-item">
            <div class="status-label">网络状态</div>
            <div class="status-value network">
              <div class="network-item">
                <span class="network-label">上行:</span>
                <span class="network-speed">{{ systemStatus.networkUp }} MB/s</span>
              </div>
              <div class="network-item">
                <span class="network-label">下行:</span>
                <span class="network-speed">{{ systemStatus.networkDown }} MB/s</span>
              </div>
            </div>
          </div>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import {
  VideoCamera,
  Connection,
  Warning,
  Monitor,
  TrendCharts
} from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import dayjs from 'dayjs'
import { getDashboardOverview, getSystemHealth, type DashboardResponse, type DashboardStats } from '@/api/dashboard'

// 统计数据
const stats = ref<DashboardStats>({
  total_cameras: 0,
  online_cameras: 0,
  offline_cameras: 0,
  total_events: 0,
  today_events: 0,
  unhandled_events: 0,
  running_tasks: 0,
  completed_tasks_today: 0,
  failed_tasks_today: 0,
  total_algorithms: 0,
  active_algorithms: 0,
  system_health: {
    cpu_percent: 0,
    memory_percent: 0,
    disk_percent: 0,
    network_sent: 0,
    network_recv: 0,
    status: 'healthy'
  }
})

// 事件趋势周期
const eventTrendPeriod = ref('7d')

// 最近事件
const recentEvents = ref<any[]>([])

// 系统状态
const systemStatus = ref({
  cpu: 0,
  memory: 0,
  disk: 0,
  networkUp: 0,
  networkDown: 0
})

// 图表引用
const eventTrendChart = ref<HTMLElement>()
const cameraStatusChart = ref<HTMLElement>()

let eventTrendChartInstance: echarts.ECharts | null = null
let cameraStatusChartInstance: echarts.ECharts | null = null

// 格式化时间
const formatTime = (time: Date) => {
  return dayjs(time).format('HH:mm')
}

// 获取状态文本
const getStatusText = (status: string) => {
  const statusMap: Record<string, string> = {
    pending: '待处理',
    processing: '处理中',
    resolved: '已解决'
  }
  return statusMap[status] || status
}

// 获取进度条颜色
const getProgressColor = (percentage: number) => {
  if (percentage < 50) return '#67C23A'
  if (percentage < 80) return '#E6A23C'
  return '#F56C6C'
}

// 初始化事件趋势图
const initEventTrendChart = () => {
  if (!eventTrendChart.value) return
  
  eventTrendChartInstance = echarts.init(eventTrendChart.value)
  
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross'
      }
    },
    legend: {
      data: ['事件总数', '已处理']
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
    },
    yAxis: {
      type: 'value'
    },
    series: [
      {
        name: '事件总数',
        type: 'line',
        data: [12, 19, 15, 25, 18, 22, 16],
        smooth: true,
        itemStyle: {
          color: '#409EFF'
        }
      },
      {
        name: '已处理',
        type: 'line',
        data: [10, 17, 13, 23, 16, 20, 14],
        smooth: true,
        itemStyle: {
          color: '#67C23A'
        }
      }
    ]
  }
  
  eventTrendChartInstance.setOption(option)
}

// 初始化摄像头状态图
const initCameraStatusChart = () => {
  if (!cameraStatusChart.value) return
  
  cameraStatusChartInstance = echarts.init(cameraStatusChart.value)
  
  const option = {
    tooltip: {
      trigger: 'item',
      formatter: '{a} <br/>{b}: {c} ({d}%)'
    },
    legend: {
      orient: 'vertical',
      left: 'left'
    },
    series: [
      {
        name: '摄像头状态',
        type: 'pie',
        radius: ['40%', '70%'],
        avoidLabelOverlap: false,
        label: {
          show: false,
          position: 'center'
        },
        emphasis: {
          label: {
            show: true,
            fontSize: '18',
            fontWeight: 'bold'
          }
        },
        labelLine: {
          show: false
        },
        data: [
          { value: 142, name: '在线', itemStyle: { color: '#67C23A' } },
          { value: 8, name: '离线', itemStyle: { color: '#F56C6C' } },
          { value: 6, name: '故障', itemStyle: { color: '#E6A23C' } }
        ]
      }
    ]
  }
  
  cameraStatusChartInstance.setOption(option)
}

// 窗口大小变化处理
const handleResize = () => {
  eventTrendChartInstance?.resize()
  cameraStatusChartInstance?.resize()
}

// 定时更新数据
let updateTimer: NodeJS.Timeout | null = null

// 事件趋势数据
const eventTrendData = ref<any[]>([])

// 摄像头状态数据
const cameraStatusData = ref<any[]>([])

// 加载状态
const loading = ref(false)

// 获取仪表盘数据
const fetchDashboardData = async () => {
  try {
    loading.value = true
    const days = eventTrendPeriod.value === '7d' ? 7 : eventTrendPeriod.value === '30d' ? 30 : 7
    const response = await getDashboardOverview(days)
    
    if (response.data) {
      // 更新统计数据
      stats.value = response.data.stats
      
      // 更新事件趋势数据
      eventTrendData.value = response.data.event_trend
      
      // 更新摄像头状态数据
      cameraStatusData.value = response.data.camera_status
      
      // 更新最近事件
      recentEvents.value = response.data.recent_events.map(event => ({
        ...event,
        camera: event.camera_name,
        time: new Date(event.created_at)
      }))
      
      // 更新系统状态
      const health = response.data.stats.system_health
      systemStatus.value = {
        cpu: health.cpu_percent,
        memory: health.memory_percent,
        disk: health.disk_percent,
        networkUp: Math.round(health.network_sent / 1024 / 1024), // 转换为MB
        networkDown: Math.round(health.network_recv / 1024 / 1024) // 转换为MB
      }
      
      // 更新图表
      updateEventTrendChart()
      updateCameraStatusChart()
    }
  } catch (error) {
    console.error('获取仪表盘数据失败:', error)
    ElMessage.error('获取仪表盘数据失败')
  } finally {
    loading.value = false
  }
}

// 更新事件趋势图表
const updateEventTrendChart = () => {
  if (!eventTrendChartInstance || !eventTrendData.value.length) return
  
  const dates = eventTrendData.value.map(item => dayjs(item.date).format('MM/DD'))
  const eventCounts = eventTrendData.value.map(item => item.event_count)
  const handledCounts = eventTrendData.value.map(item => item.handled_count)
  
  eventTrendChartInstance.setOption({
    xAxis: {
      data: dates
    },
    series: [
      {
        name: '事件总数',
        data: eventCounts
      },
      {
        name: '已处理',
        data: handledCounts
      }
    ]
  })
}

// 更新摄像头状态图表
const updateCameraStatusChart = () => {
  if (!cameraStatusChartInstance || !cameraStatusData.value.length) return
  
  const data = cameraStatusData.value.map(item => ({
    name: item.status === 'online' ? '在线' : item.status === 'offline' ? '离线' : item.status,
    value: item.count
  }))
  
  cameraStatusChartInstance.setOption({
    series: [{
      data: data
    }]
  })
}

const updateData = async () => {
  await fetchDashboardData()
}

onMounted(async () => {
  await nextTick()
  
  // 初始化图表
  initEventTrendChart()
  initCameraStatusChart()
  
  // 获取初始数据
  await fetchDashboardData()
  
  // 监听窗口大小变化
  window.addEventListener('resize', handleResize)
  
  // 定时更新数据
  updateTimer = setInterval(updateData, 30000) // 30秒更新一次
})

onUnmounted(() => {
  // 销毁图表实例
  eventTrendChartInstance?.dispose()
  cameraStatusChartInstance?.dispose()
  
  // 移除事件监听
  window.removeEventListener('resize', handleResize)
  
  // 清除定时器
  if (updateTimer) {
    clearInterval(updateTimer)
  }
})
</script>

<style lang="scss" scoped>
.dashboard {
  .stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 24px;
    margin-bottom: 24px;
    
    .stats-card {
      :deep(.el-card__body) {
        padding: 24px;
      }
      
      .stats-content {
        @include flex-vertical-center;
        gap: 16px;
        margin-bottom: 12px;
        
        .stats-icon {
          width: 60px;
          height: 60px;
          border-radius: 12px;
          @include flex-center;
          
          &.camera {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #fff;
          }
          
          &.online {
            background: linear-gradient(135deg, #67C23A 0%, #85ce61 100%);
            color: #fff;
          }
          
          &.events {
            background: linear-gradient(135deg, #E6A23C 0%, #ebb563 100%);
            color: #fff;
          }
          
          &.tasks {
            background: linear-gradient(135deg, #409EFF 0%, #66b1ff 100%);
            color: #fff;
          }
        }
        
        .stats-info {
          flex: 1;
          
          .stats-value {
            font-size: 32px;
            font-weight: 600;
            color: var(--el-text-color-primary);
            line-height: 1;
            margin-bottom: 4px;
          }
          
          .stats-label {
            font-size: 14px;
            color: var(--el-text-color-secondary);
          }
        }
      }
      
      .stats-trend {
        @include flex-vertical-center;
        gap: 4px;
        font-size: 12px;
        font-weight: 500;
        
        &.positive {
          color: $success-color;
        }
        
        &.negative {
          color: $danger-color;
        }
      }
    }
  }
  
  .charts-grid {
    display: grid;
    grid-template-columns: 2fr 1fr;
    gap: 24px;
    margin-bottom: 24px;
    
    .chart-card {
      .card-header {
        @include flex-between;
        
        .card-title {
          font-size: 16px;
          font-weight: 600;
          color: var(--el-text-color-primary);
        }
      }
      
      .chart-container {
        height: 300px;
      }
    }
  }
  
  .details-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 24px;
    
    .details-card {
      .card-header {
        @include flex-between;
        
        .card-title {
          font-size: 16px;
          font-weight: 600;
          color: $text-color-primary;
        }
      }
      
      .events-list {
        .event-item {
          @include flex-vertical-center;
          gap: 12px;
          padding: 12px 0;
          border-bottom: 1px solid var(--el-border-color-lighter);
          
          &:last-child {
            border-bottom: none;
          }
          
          .event-icon {
            width: 36px;
            height: 36px;
            border-radius: 8px;
            @include flex-center;
            
            &.high {
              background: rgba(245, 108, 108, 0.1);
              color: $danger-color;
            }
            
            &.medium {
              background: rgba(230, 162, 60, 0.1);
              color: var(--el-color-warning);
            }
            
            &.low {
              background: rgba(144, 147, 153, 0.1);
              color: $info-color;
            }
          }
          
          .event-content {
            flex: 1;
            
            .event-title {
              font-size: 14px;
              font-weight: 500;
              color: var(--el-text-color-primary);
              margin-bottom: 4px;
            }
            
            .event-meta {
              @include flex-vertical-center;
              gap: 12px;
              font-size: 12px;
              color: var(--el-text-color-secondary);
            }
          }
          
          .event-status {
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 500;
            
            &.pending {
              background: rgba(230, 162, 60, 0.1);
              color: $warning-color;
            }
            
            &.processing {
              background: rgba(64, 158, 255, 0.1);
              color: var(--el-color-primary);
            }
            
            &.resolved {
              background: rgba(103, 194, 58, 0.1);
              color: var(--el-color-success);
            }
          }
        }
      }
      
      .system-status {
        .status-item {
          margin-bottom: 20px;
          
          &:last-child {
            margin-bottom: 0;
          }
          
          .status-label {
            font-size: 14px;
            color: var(--el-text-color-regular);
            margin-bottom: 8px;
          }
          
          .status-value {
            @include flex-vertical-center;
            gap: 12px;
            
            .el-progress {
              flex: 1;
            }
            
            .percentage {
              font-size: 14px;
              font-weight: 500;
              color: var(--el-text-color-primary);
              min-width: 40px;
              text-align: right;
            }
            
            &.network {
              flex-direction: column;
              align-items: stretch;
              gap: 8px;
              
              .network-item {
                @include flex-between;
                
                .network-label {
                  font-size: 12px;
                  color: var(--el-text-color-secondary);
                }
                
                .network-speed {
                  font-size: 12px;
                  font-weight: 500;
                  color: var(--el-text-color-primary);
                }
              }
            }
          }
        }
      }
    }
  }
}

// 响应式设计
@include respond-to(lg) {
  .dashboard {
    .charts-grid {
      grid-template-columns: 1fr;
    }
    
    .details-grid {
      grid-template-columns: 1fr;
    }
  }
}

@include respond-to(md) {
  .dashboard {
    .stats-grid {
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    }
  }
}

@include respond-to(sm) {
  .dashboard {
    .stats-grid {
      grid-template-columns: 1fr;
    }
  }
}
</style>