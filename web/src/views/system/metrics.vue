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
                <div class="metric-value">{{ systemStats?.disk_usage?.percent?.toFixed(1) || 0 }}%</div>
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
                  <span class="resource-value">{{ systemStats?.disk_usage?.percent?.toFixed(1) || 0 }}%</span>
                </div>
                <el-progress 
                  :percentage="systemStats?.disk_usage?.percent || 0" 
                  :color="getProgressColor(systemStats?.disk_usage?.percent || 0)"
                  :show-text="false"
                />
                <div class="resource-sub-info">
                  已用: {{ formatBytes(systemStats?.disk_usage?.used || 0) }} / 
                  总计: {{ formatBytes(systemStats?.disk_usage?.total || 0) }}
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
    <div class="metrics-charts">
      <el-card class="panel-card">
        <template #header>
          <div class="card-header">
            <span>历史性能指标</span>
            <div class="chart-controls">
              <el-select v-model="selectedMetric" @change="loadMetricsData" style="width: 150px; margin-right: 10px;">
                <el-option label="CPU使用率" value="cpu_usage" />
                <el-option label="内存使用率" value="memory_usage" />
                <el-option label="磁盘使用率" value="disk_usage" />
              </el-select>
              <el-date-picker
                v-model="timeRange"
                type="datetimerange"
                range-separator="至"
                start-placeholder="开始时间"
                end-placeholder="结束时间"
                @change="loadMetricsData"
                style="width: 350px;"
              />
            </div>
          </div>
        </template>
        
        <div class="chart-container" ref="chartContainer">
          <div v-if="metricsLoading" class="chart-loading">
            <el-icon class="is-loading"><Loading /></el-icon>
            <span>加载中...</span>
          </div>
          <div v-else-if="!metricsData.length" class="chart-empty">
            <el-empty description="暂无数据" />
          </div>
          <div v-else id="metricsChart" style="width: 100%; height: 400px;"></div>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
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

// 渲染图表
const renderChart = () => {
  if (!chartContainer.value || !metricsData.value.length) return
  
  const chartElement = document.getElementById('metricsChart')
  if (!chartElement) return
  
  if (chart) {
    chart.dispose()
  }
  
  chart = echarts.init(chartElement)
  
  const option = {
    title: {
      text: getMetricTitle(selectedMetric.value),
      left: 'center'
    },
    tooltip: {
      trigger: 'axis',
      formatter: (params: any) => {
        const data = params[0]
        return `${data.name}<br/>${data.seriesName}: ${data.value}${getMetricUnit(selectedMetric.value)}`
      }
    },
    xAxis: {
      type: 'category',
      data: metricsData.value.map(item => 
        new Date(item.timestamp).toLocaleString()
      )
    },
    yAxis: {
      type: 'value',
      name: getMetricUnit(selectedMetric.value),
      min: 0,
      max: selectedMetric.value.includes('usage') ? 100 : undefined
    },
    series: [{
      name: getMetricTitle(selectedMetric.value),
      type: 'line',
      smooth: true,
      data: metricsData.value.map(item => item.metric_value),
      areaStyle: {
        opacity: 0.3
      },
      lineStyle: {
        width: 2
      }
    }]
  }
  
  chart.setOption(option)
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

// 获取指标标题
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

// 组件挂载
onMounted(async () => {
  await loadSystemStats()
  await loadMetricsData()
  
  // 设置定时刷新
  refreshTimer = setInterval(() => {
    loadSystemStats()
  }, 30000) // 30秒刷新一次
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
  color: #303133;
  font-size: 24px;
  font-weight: 600;
}

.page-header p {
  margin: 0;
  color: #909399;
  font-size: 14px;
}

.overview-cards {
  margin-bottom: 20px;
}

.metric-card {
  border: none;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  transition: all 0.3s;
}

.metric-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 20px 0 rgba(0, 0, 0, 0.15);
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
}

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
  color: #303133;
  line-height: 1;
  margin-bottom: 4px;
}

.metric-label {
  font-size: 14px;
  color: #909399;
}

.monitoring-panels,
.log-statistics,
.metrics-charts {
  margin-bottom: 20px;
}

.panel-card {
  border: none;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
  color: #303133;
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
  color: #303133;
}

.resource-value {
  font-weight: 600;
  color: #409eff;
}

.resource-sub-info {
  margin-top: 8px;
  font-size: 12px;
  color: #909399;
}

.status-info {
  padding: 10px 0;
}

.status-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid #f0f0f0;
}

.status-item:last-child {
  border-bottom: none;
}

.status-label {
  font-weight: 500;
  color: #606266;
}

.status-value {
  color: #303133;
  font-weight: 500;
}

.log-stat-item {
  display: flex;
  align-items: center;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 8px;
  transition: all 0.3s;
}

.log-stat-item:hover {
  background: #e9ecef;
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
  color: #303133;
  line-height: 1;
  margin-bottom: 4px;
}

.log-stat-label {
  font-size: 14px;
  color: #909399;
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
  color: #909399;
}

.chart-loading .el-icon {
  font-size: 32px;
  margin-bottom: 16px;
}
</style>