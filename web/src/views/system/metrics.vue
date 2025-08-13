<template>
  <div class="metrics-container">
    <!-- 页面标题 -->
    <div class="page-header">
      <h2>性能监控</h2>
      <p>实时监控系统性能指标和资源使用情况</p>
    </div>

    <!-- 系统概览卡片 -->
    <div class="overview-cards">
      <el-row :gutter="20">
        <el-col :span="6">
          <el-card class="metric-card cpu-card">
            <div class="metric-content">
              <div class="metric-icon">
                <el-icon size="32"><Cpu /></el-icon>
              </div>
              <div class="metric-info">
                <div class="metric-value">{{ systemStats?.cpu_usage?.toFixed(1) || 0 }}%</div>
                <div class="metric-label">CPU 使用率</div>
              </div>
            </div>
          </el-card>
        </el-col>
        
        <el-col :span="6">
          <el-card class="metric-card memory-card">
            <div class="metric-content">
              <div class="metric-icon">
                <el-icon size="32"><Monitor /></el-icon>
              </div>
              <div class="metric-info">
                <div class="metric-value">{{ systemStats?.memory_usage?.percent?.toFixed(1) || 0 }}%</div>
                <div class="metric-label">内存使用率</div>
              </div>
            </div>
          </el-card>
        </el-col>
        
        <el-col :span="6">
          <el-card class="metric-card disk-card">
            <div class="metric-content">
              <div class="metric-icon">
                <el-icon size="32"><FolderOpened /></el-icon>
              </div>
              <div class="metric-info">
                <div class="metric-value">{{ getAverageDiskUsage() }}%</div>
                <div class="metric-label">磁盘使用率</div>
              </div>
            </div>
          </el-card>
        </el-col>
        
        <el-col :span="6">
          <el-card class="metric-card logs-card">
            <div class="metric-content">
              <div class="metric-icon">
                <el-icon size="32"><Document /></el-icon>
              </div>
              <div class="metric-info">
                <div class="metric-value">{{ systemStats?.system_logs_today || 0 }}</div>
                <div class="metric-label">今日日志</div>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 详细监控面板 -->
    <div class="monitoring-panels">
      <el-row :gutter="20">
        <!-- 系统资源使用情况 -->
        <el-col :span="12">
          <el-card class="panel-card">
            <template #header>
              <div class="card-header">
                <span>系统资源使用情况</span>
                <el-button type="primary" size="small" @click="refreshStats">
                  <el-icon><Refresh /></el-icon>
                  刷新
                </el-button>
              </div>
            </template>
            
            <div class="resource-details">
              <!-- CPU 详情 -->
              <div class="resource-item">
                <div class="resource-header">
                  <span class="resource-name">CPU 使用率</span>
                  <span class="resource-value">{{ systemStats?.cpu_usage?.toFixed(1) || 0 }}%</span>
                </div>
                <el-progress 
                  :percentage="systemStats?.cpu_usage || 0" 
                  :color="getProgressColor(systemStats?.cpu_usage || 0)"
                  :show-text="false"
                />
              </div>
              
              <!-- 内存详情 -->
              <div class="resource-item">
                <div class="resource-header">
                  <span class="resource-name">内存使用率</span>
                  <span class="resource-value">{{ systemStats?.memory_usage?.percent?.toFixed(1) || 0 }}%</span>
                </div>
                <el-progress 
                  :percentage="systemStats?.memory_usage?.percent || 0" 
                  :color="getProgressColor(systemStats?.memory_usage?.percent || 0)"
                  :show-text="false"
                />
                <div class="resource-sub-info">
                  已用: {{ formatBytes(systemStats?.memory_usage?.used || 0) }} / 
                  总计: {{ formatBytes(systemStats?.memory_usage?.total || 0) }}
                </div>
              </div>
              
              <!-- 磁盘详情 -->
              <div class="resource-item">
                <div class="resource-header">
                  <span class="resource-name">磁盘使用率</span>
                  <span class="resource-value">{{ getAverageDiskUsage() }}%</span>
                </div>
                <el-progress 
                  :percentage="getAverageDiskUsageValue()" 
                  :color="getProgressColor(getAverageDiskUsageValue())"
                  :show-text="false"
                />
                <div class="disk-details" v-if="systemStats?.disk_usage?.length">
                  <div v-for="(disk, index) in systemStats.disk_usage" :key="index" class="disk-item">
                    <div class="disk-header">
                      <span class="disk-name">{{ disk.device }} ({{ disk.mountpoint }})</span>
                      <span class="disk-percent">{{ disk.percent?.toFixed(1) }}%</span>
                    </div>
                    <el-progress 
                      :percentage="disk.percent || 0" 
                      :color="getProgressColor(disk.percent || 0)"
                      :show-text="false"
                      size="small"
                    />
                    <div class="disk-sub-info">
                      已用: {{ formatBytes(disk.used || 0) }} / 总计: {{ formatBytes(disk.total || 0) }}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </el-card>
        </el-col>
        
        <!-- 系统状态信息 -->
        <el-col :span="12">
          <el-card class="panel-card">
            <template #header>
              <div class="card-header">
                <span>系统状态信息</span>
              </div>
            </template>
            
            <div class="status-info">
              <div class="status-item">
                <span class="status-label">系统版本:</span>
                <span class="status-value">{{ systemStats?.current_version || '未知' }}</span>
              </div>
              
              <div class="status-item">
                <span class="status-label">许可证状态:</span>
                <el-tag :type="getLicenseTagType(systemStats?.license_status)">
                  {{ systemStats?.license_status || '未知' }}
                </el-tag>
              </div>
              
              <div class="status-item" v-if="systemStats?.license_expires_in_days !== null">
                <span class="status-label">许可证剩余天数:</span>
                <span class="status-value">{{ systemStats?.license_expires_in_days }} 天</span>
              </div>
              
              <div class="status-item">
                <span class="status-label">系统配置数:</span>
                <span class="status-value">{{ systemStats?.total_configs || 0 }}</span>
              </div>
              
              <div class="status-item">
                <span class="status-label">活跃策略数:</span>
                <span class="status-value">{{ systemStats?.active_policies || 0 }}</span>
              </div>
              
              <div class="status-item">
                <span class="status-label">活跃消息中心:</span>
                <span class="status-value">{{ systemStats?.active_message_centers || 0 }}</span>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 日志统计 -->
    <div class="log-statistics">
      <el-card class="panel-card">
        <template #header>
          <div class="card-header">
            <span>今日日志统计</span>
          </div>
        </template>
        
        <el-row :gutter="20">
          <el-col :span="8">
            <div class="log-stat-item">
              <div class="log-stat-icon total">
                <el-icon size="24"><Document /></el-icon>
              </div>
              <div class="log-stat-info">
                <div class="log-stat-value">{{ systemStats?.system_logs_today || 0 }}</div>
                <div class="log-stat-label">总日志数</div>
              </div>
            </div>
          </el-col>
          
          <el-col :span="8">
            <div class="log-stat-item">
              <div class="log-stat-icon warning">
                <el-icon size="24"><Warning /></el-icon>
              </div>
              <div class="log-stat-info">
                <div class="log-stat-value">{{ systemStats?.warning_logs_today || 0 }}</div>
                <div class="log-stat-label">警告日志</div>
              </div>
            </div>
          </el-col>
          
          <el-col :span="8">
            <div class="log-stat-item">
              <div class="log-stat-icon error">
                <el-icon size="24"><CircleClose /></el-icon>
              </div>
              <div class="log-stat-info">
                <div class="log-stat-value">{{ systemStats?.error_logs_today || 0 }}</div>
                <div class="log-stat-label">错误日志</div>
              </div>
            </div>
          </el-col>
        </el-row>
      </el-card>
    </div>

    <!-- 历史指标图表 -->
    <div class="historical-metrics">
      <el-card class="panel-card">
        <template #header>
          <div class="card-header">
            <span>历史性能指标</span>
            <div class="chart-controls">
              <el-select v-model="selectedMetric" @change="updateChart" style="width: 150px; margin-right: 10px;">
                <el-option label="CPU 使用率" value="cpu_usage" />
                <el-option label="内存使用率" value="memory_usage" />
                <el-option label="磁盘使用率" value="disk_usage" />
              </el-select>
              
              <el-select v-model="timeRangeOption" @change="updateChart" style="width: 120px; margin-right: 10px;">
                <el-option label="1小时" value="1h" />
                <el-option label="6小时" value="6h" />
                <el-option label="24小时" value="24h" />
                <el-option label="7天" value="7d" />
              </el-select>
              
              <el-date-picker
                v-model="timeRange"
                type="datetimerange"
                range-separator="至"
                start-placeholder="开始时间"
                end-placeholder="结束时间"
                format="YYYY-MM-DD HH:mm:ss"
                value-format="YYYY-MM-DD HH:mm:ss"
                @change="updateChart"
                style="width: 300px; margin-right: 10px;"
              />
              
              <el-button @click="refreshChart" :loading="metricsLoading">
                <el-icon><Refresh /></el-icon>
                刷新
              </el-button>
            </div>
          </div>
        </template>
        
        <div v-if="metricsLoading" class="chart-loading">
          <el-icon class="is-loading"><Loading /></el-icon>
          <span>加载中...</span>
        </div>
        
        <div v-else-if="!metricsData || metricsData.length === 0" class="no-data">
          <el-empty description="暂无数据" />
        </div>
        
        <div v-else ref="chartContainer" class="chart-container"></div>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { 
  Cpu, 
  Monitor, 
  FolderOpened, 
  Document, 
  Refresh, 
  Warning, 
  CircleClose,
  Loading
} from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import { systemApi } from '@/api/system'

// 响应式数据
const systemStats = ref<any>(null)
const metricsData = ref<any[]>([])
const metricsLoading = ref(false)
const selectedMetric = ref('cpu_usage')
const timeRangeOption = ref('1h')
const timeRange = ref<[Date, Date]>([new Date(Date.now() - 24 * 60 * 60 * 1000), new Date()])
const chartContainer = ref<HTMLElement>()
let chart: echarts.ECharts | null = null
let refreshTimer: NodeJS.Timeout | null = null

// 加载系统统计信息
const loadSystemStats = async () => {
  try {
    const response = await systemApi.getSystemStats()
    systemStats.value = response.data
  } catch (error) {
    console.error('加载系统统计信息失败:', error)
    ElMessage.error('加载系统统计信息失败')
  }
}

// 加载指标数据
const loadMetricsData = async () => {
  if (!timeRange.value || timeRange.value.length !== 2) return
  
  metricsLoading.value = true
  try {
    const response = await systemApi.getSystemMetrics({
      metric_name: selectedMetric.value,
      start_time: timeRange.value[0].toISOString(),
      end_time: timeRange.value[1].toISOString(),
      limit: 1000
    })
    metricsData.value = response.data
    await nextTick()
    renderChart()
  } catch (error) {
    console.error('加载指标数据失败:', error)
    ElMessage.error('加载指标数据失败')
  } finally {
    metricsLoading.value = false
  }
}

// 刷新图表
const refreshChart = async () => {
  await updateChart()
}

// 获取历史性能指标数据
const fetchHistoricalMetrics = async () => {
  try {
    const endTime = new Date()
    const startTime = new Date(endTime.getTime() - 24 * 60 * 60 * 1000) // 最近24小时
    
    // 使用systemApi获取数据
    const response = await systemApi.getSystemMetrics({
      start_time: startTime.toISOString(),
      end_time: endTime.toISOString(),
      limit: 1000
    })
    
    if (response && response.data) {
      // 直接设置metricsData以便图表渲染
      metricsData.value = response.data
      await nextTick()
      renderChart()
    }
  } catch (error) {
    console.error('获取历史性能指标失败:', error)
    ElMessage.error('获取历史性能指标失败')
  }
}

// 更新图表 - 根据选择的指标和时间范围获取数据
const updateChart = async () => {
  metricsLoading.value = true
  try {
    let startTime: Date
    let endTime: Date
    
    if (timeRange.value && timeRange.value.length === 2) {
      // 使用自定义时间范围
      startTime = new Date(timeRange.value[0])
      endTime = new Date(timeRange.value[1])
    } else {
      // 使用预设时间范围
      endTime = new Date()
      switch (timeRangeOption.value) {
        case '1h':
          startTime = new Date(endTime.getTime() - 60 * 60 * 1000)
          break
        case '6h':
          startTime = new Date(endTime.getTime() - 6 * 60 * 60 * 1000)
          break
        case '7d':
          startTime = new Date(endTime.getTime() - 7 * 24 * 60 * 60 * 1000)
          break
        default: // 24h
          startTime = new Date(endTime.getTime() - 24 * 60 * 60 * 1000)
      }
    }
    
    const response = await systemApi.getSystemMetrics({
      metric_name: selectedMetric.value,
      start_time: startTime.toISOString(),
      end_time: endTime.toISOString(),
      limit: 1000
    })
    
    metricsData.value = response.data || []
  } catch (error) {
    console.error('获取指标数据失败:', error)
    ElMessage.error('获取指标数据失败')
  } finally {
    metricsLoading.value = false
    // 等待DOM更新后再渲染图表
    await nextTick()
    await renderChart()
  }
}

// 处理历史数据并更新图表
const updatePerformanceCharts = (data) => {
  if (!data || !Array.isArray(data)) return
  
  // 按时间排序
  const sortedData = data.sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp))
  
  // 分组数据
  const cpuMetrics = sortedData.filter(item => item.metric_name === 'cpu_usage')
  const memoryMetrics = sortedData.filter(item => item.metric_name === 'memory_usage')
  const diskMetrics = sortedData.filter(item => item.metric_name === 'disk_usage')
  
  // 更新时间标签和数据
  timeLabels.value = cpuMetrics.map(item => {
    const date = new Date(item.timestamp)
    return `${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`
  })
  
  cpuData.value = cpuMetrics.map(item => item.metric_value.toFixed(1))
  memoryData.value = memoryMetrics.map(item => item.metric_value.toFixed(1))
  
  // 计算平均磁盘使用率
  const diskByTime = {}
  diskMetrics.forEach(item => {
    const timeKey = item.timestamp
    if (!diskByTime[timeKey]) {
      diskByTime[timeKey] = []
    }
    diskByTime[timeKey].push(item.metric_value)
  })
  
  diskData.value = Object.values(diskByTime).map(values => {
    const avg = values.reduce((sum, val) => sum + val, 0) / values.length
    return avg.toFixed(1)
  })
}

// 渲染图表
const renderChart = async () => {
  if (!metricsData.value || !metricsData.value.length) {
    console.log('No metrics data available for chart rendering')
    return
  }
  
  // 等待DOM更新，确保容器已渲染
  await nextTick()
  
  if (!chartContainer.value) {
    console.error('Chart container not found')
    return
  }
  
  // 检查容器是否可见且有尺寸
  if (chartContainer.value.offsetWidth === 0 || chartContainer.value.offsetHeight === 0) {
    console.warn('Chart container not visible, waiting...')
    // 等待容器变为可见
    const waitForContainer = () => {
      return new Promise<void>((resolve, reject) => {
        let attempts = 0
        const maxAttempts = 30 // 最多等待3秒
        const checkContainer = () => {
          attempts++
          if (chartContainer.value && 
              chartContainer.value.offsetWidth > 0 && 
              chartContainer.value.offsetHeight > 0) {
            resolve()
          } else if (attempts >= maxAttempts) {
            reject(new Error('Chart container failed to become visible'))
          } else {
            setTimeout(checkContainer, 100)
          }
        }
        checkContainer()
      })
    }
    
    try {
      await waitForContainer()
    } catch (error) {
      console.error('Chart container visibility check failed:', error)
      return
    }
  }
  
  if (chart) {
    chart.dispose()
    chart = null
  }
  
  // 检查是否为暗黑模式
  const isDarkMode = document.documentElement.classList.contains('dark')
  
  chart = echarts.init(chartContainer.value, isDarkMode ? 'dark' : null)
  
  // 过滤选中指标的数据
  const filteredData = metricsData.value.filter(item => 
    item.metric_name === selectedMetric.value
  ).sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime())
  
  if (filteredData.length === 0) {
    console.log(`No data found for metric: ${selectedMetric.value}`)
    return
  }
  
  let series = []
  let timeData = []
  
  // 对于磁盘使用率，需要按设备分组显示多条曲线
  if (selectedMetric.value === 'disk_usage') {
    // 按设备分组数据
    const deviceGroups = {}
    filteredData.forEach(item => {
      const device = item.dimensions?.device || 'Unknown'
      const mountpoint = item.dimensions?.mountpoint || ''
      const deviceKey = `${device} (${mountpoint})`
      
      if (!deviceGroups[deviceKey]) {
        deviceGroups[deviceKey] = []
      }
      deviceGroups[deviceKey].push(item)
    })
    
    // 获取时间轴数据（使用第一个设备的时间点）
    const firstDevice = Object.keys(deviceGroups)[0]
    if (firstDevice) {
      timeData = deviceGroups[firstDevice].map(item => 
        new Date(item.timestamp).toLocaleString()
      )
    }
    
    // 为每个设备创建一个系列
    const colors = ['#409eff', '#67c23a', '#e6a23c', '#f56c6c', '#909399', '#c71585', '#ff6347', '#32cd32']
    let colorIndex = 0
    
    Object.keys(deviceGroups).forEach(deviceKey => {
      const deviceData = deviceGroups[deviceKey]
      const color = colors[colorIndex % colors.length]
      colorIndex++
      
      series.push({
        name: deviceKey,
        type: 'line',
        smooth: true,
        data: deviceData.map(item => item.metric_value),
        lineStyle: {
          width: 2,
          color: color
        },
        itemStyle: {
          color: color
        }
      })
    })
  } else {
    // 对于CPU和内存使用率，显示单条曲线
    timeData = filteredData.map(item => 
      new Date(item.timestamp).toLocaleString()
    )
    
    series = [{
      name: getMetricTitle(selectedMetric.value),
      type: 'line',
      smooth: true,
      data: filteredData.map(item => item.metric_value),
      areaStyle: {
        opacity: 0.3
      },
      lineStyle: {
        width: 2,
        color: '#409eff'
      },
      itemStyle: {
        color: '#409eff'
      }
    }]
  }
  
  const option = {
    title: {
      text: getMetricTitle(selectedMetric.value),
      left: 'center',
      textStyle: {
        color: isDarkMode ? '#e5eaf3' : '#303133'
      }
    },
    tooltip: {
      trigger: 'axis',
      formatter: (params: any) => {
        let result = `${params[0].name}<br/>`
        params.forEach(param => {
          result += `${param.seriesName}: ${param.value}${getMetricUnit(selectedMetric.value)}<br/>`
        })
        return result
      }
    },
    legend: {
      show: selectedMetric.value === 'disk_usage' && series.length > 1,
      top: 30,
      textStyle: {
        color: isDarkMode ? '#cfd3dc' : '#606266'
      }
    },
    xAxis: {
      type: 'category',
      data: timeData,
      axisLabel: {
        color: isDarkMode ? '#cfd3dc' : '#606266'
      }
    },
    yAxis: {
      type: 'value',
      name: getMetricUnit(selectedMetric.value),
      min: 0,
      max: selectedMetric.value.includes('usage') ? 100 : undefined,
      axisLabel: {
        color: isDarkMode ? '#cfd3dc' : '#606266'
      },
      nameTextStyle: {
        color: isDarkMode ? '#cfd3dc' : '#606266'
      }
    },
    series: series
  }
  
  chart.setOption(option)
  console.log(`Chart rendered with ${series.length} series for ${selectedMetric.value}`)
}

// 刷新统计信息
const refreshStats = async () => {
  await loadSystemStats()
  ElMessage.success('数据已刷新')
}

// 格式化字节数
const formatBytes = (bytes: number): string => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

// 获取进度条颜色
const getProgressColor = (percentage: number): string => {
  if (percentage < 50) return '#67c23a'
  if (percentage < 80) return '#e6a23c'
  return '#f56c6c'
}

// 获取许可证标签类型
const getLicenseTagType = (status: string): string => {
  switch (status) {
    case '正常':
    case '永久':
      return 'success'
    case '即将过期':
      return 'warning'
    case '已过期':
    case '无效':
      return 'danger'
    default:
      return 'info'
  }
}

// 获取指标标题
const getMetricTitle = (metric: string): string => {
  const titles: Record<string, string> = {
    cpu_usage: 'CPU使用率',
    memory_usage: '内存使用率',
    disk_usage: '磁盘使用率'
  }
  return titles[metric] || metric
}

// 获取指标单位
const getMetricUnit = (metric: string): string => {
  if (metric.includes('usage')) return '%'
  return ''
}

// 计算平均磁盘使用率
const getAverageDiskUsage = (): string => {
  if (!systemStats.value?.disk_usage?.length) return '0.0'
  const total = systemStats.value.disk_usage.reduce((sum, disk) => sum + (disk.percent || 0), 0)
  return (total / systemStats.value.disk_usage.length).toFixed(1)
}

// 获取平均磁盘使用率数值
const getAverageDiskUsageValue = (): number => {
  if (!systemStats.value?.disk_usage?.length) return 0
  const total = systemStats.value.disk_usage.reduce((sum, disk) => sum + (disk.percent || 0), 0)
  return total / systemStats.value.disk_usage.length
}

// 组件挂载
onMounted(async () => {
  await loadSystemStats()
  
  // 确保DOM完全渲染后再初始化图表
  await nextTick()
  
  // 初始化时先获取数据，但不显示loading状态
  try {
    let startTime: Date
    let endTime: Date
    
    // 使用预设时间范围
    endTime = new Date()
    switch (timeRangeOption.value) {
      case '1h':
        startTime = new Date(endTime.getTime() - 60 * 60 * 1000)
        break
      case '6h':
        startTime = new Date(endTime.getTime() - 6 * 60 * 60 * 1000)
        break
      case '7d':
        startTime = new Date(endTime.getTime() - 7 * 24 * 60 * 60 * 1000)
        break
      default: // 24h
        startTime = new Date(endTime.getTime() - 24 * 60 * 60 * 1000)
    }
    
    const response = await systemApi.getSystemMetrics({
      metric_name: selectedMetric.value,
      start_time: startTime.toISOString(),
      end_time: endTime.toISOString(),
      limit: 1000
    })
    
    metricsData.value = response.data || []
    
    // 等待DOM更新后再渲染图表
    await nextTick()
    
    // 等待图表容器准备好
    const waitForContainer = () => {
      return new Promise<void>((resolve) => {
        const checkContainer = () => {
          if (chartContainer.value && chartContainer.value.offsetWidth > 0 && chartContainer.value.offsetHeight > 0) {
            resolve()
          } else {
            setTimeout(checkContainer, 50)
          }
        }
        checkContainer()
      })
    }
    
    await waitForContainer()
    await renderChart()
  } catch (error) {
    console.error('初始化指标数据失败:', error)
  }
  
  // 设置定时刷新
  refreshTimer = setInterval(() => {
    loadSystemStats()
    updateChart() // 同时刷新历史指标数据
  }, 30000) // 30秒刷新一次
})

// 监听指标类型变化
watch(selectedMetric, () => {
  updateChart()
})

// 监听时间范围选项变化
watch(timeRangeOption, () => {
  updateChart()
})

// 监听自定义时间范围变化
watch(timeRange, () => {
  if (timeRange.value && timeRange.value.length === 2) {
    updateChart()
  }
})

// 组件卸载
onUnmounted(() => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
  }
  if (chart) {
    chart.dispose()
  }
})
</script>

<style scoped>

.metrics-container {
  padding: 20px;
}

.page-header {
  margin-bottom: 20px;
}

.page-header h2 {
  margin: 0 0 8px 0;
  color: var(--el-text-color-primary);
  font-size: 24px;
  font-weight: 600;
}

.page-header p {
  margin: 0;
  color: var(--el-text-color-secondary);
  font-size: 14px;
}

.overview-cards {
  margin-bottom: 20px;
}

.metric-card {
  border: none;
  box-shadow: var(--el-box-shadow-light);
  transition: all 0.3s;
  background-color: var(--el-bg-color);
}

.metric-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--el-box-shadow);
}

.metric-content {
  display: flex;
  align-items: center;
  padding: 10px 0;
}

.metric-icon {
  margin-right: 16px;
  padding: 12px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  font-size: 24px;
}

/* 性能监控页面特有的图标颜色 */
.cpu-card .metric-icon {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.memory-card .metric-icon {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  color: white;
}

.disk-card .metric-icon {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
  color: white;
}

.logs-card .metric-icon {
  background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
  color: white;
}

.metric-info {
  flex: 1;
}

.metric-value {
  font-size: 28px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  line-height: 1;
  margin-bottom: 4px;
}

.metric-label {
  font-size: 14px;
  color: var(--el-text-color-secondary);
}

.monitoring-panels,
.log-statistics,
.metrics-charts {
  margin-bottom: 20px;
}

.panel-card {
  border: none;
  box-shadow: var(--el-box-shadow-light);
  background-color: var(--el-bg-color);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.resource-details {
  padding: 10px 0;
}

.resource-item {
  margin-bottom: 24px;
}

.resource-item:last-child {
  margin-bottom: 0;
}

.resource-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.resource-name {
  font-weight: 500;
  color: var(--el-text-color-primary);
}

.resource-value {
  font-weight: 600;
  color: var(--el-color-primary);
}

.resource-sub-info {
  margin-top: 8px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.status-info {
  padding: 10px 0;
}

.status-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.status-item:last-child {
  border-bottom: none;
}

.status-label {
  font-weight: 500;
  color: var(--el-text-color-regular);
}

.status-value {
  color: var(--el-text-color-primary);
  font-weight: 500;
}

.log-stat-item {
  display: flex;
  align-items: center;
  padding: 20px;
  background: var(--el-fill-color-light);
  border-radius: 8px;
  transition: all 0.3s;
}

.log-stat-item:hover {
  background: var(--el-fill-color);
}

.log-stat-icon {
  margin-right: 16px;
  padding: 12px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.log-stat-icon.total {
  background: #e3f2fd;
  color: #1976d2;
}

.log-stat-icon.warning {
  background: #fff3e0;
  color: #f57c00;
}

.log-stat-icon.error {
  background: #ffebee;
  color: #d32f2f;
}

.log-stat-info {
  flex: 1;
}

.log-stat-value {
  font-size: 24px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  line-height: 1;
  margin-bottom: 4px;
}

.log-stat-label {
  font-size: 14px;
  color: var(--el-text-color-secondary);
}

.chart-controls {
  display: flex;
  align-items: center;
}

.chart-container {
  position: relative;
  min-height: 400px;
}

.chart-loading,
.chart-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 400px;
  color: var(--el-text-color-secondary);
}

.chart-loading .el-icon {
  font-size: 32px;
  margin-bottom: 16px;
}

.disk-details {
  margin-top: 16px;
}

.disk-item {
  margin-bottom: 16px;
  padding: 12px;
  background: var(--el-fill-color-light);
  border-radius: 6px;
  border: 1px solid var(--el-border-color-lighter);
}

.disk-item:last-child {
  margin-bottom: 0;
}

.disk-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.disk-name {
  font-weight: 500;
  color: var(--el-text-color-primary);
  font-size: 13px;
}

.disk-percent {
  font-weight: 600;
  color: var(--el-color-primary);
  font-size: 13px;
}

.disk-sub-info {
  margin-top: 6px;
  font-size: 11px;
  color: var(--el-text-color-secondary);
}
</style>
