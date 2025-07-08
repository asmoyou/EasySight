<template>
  <div class="diagnosis-results">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <h2>诊断结果</h2>
        <p class="page-description">查看视频质量诊断的详细结果和分析报告</p>
      </div>
      <div class="header-right">
        <el-button @click="handleExport">
          <el-icon><Download /></el-icon>
          导出结果
        </el-button>
      </div>
    </div>

    <!-- 搜索和筛选 -->
    <div class="search-filters">
      <div class="search-bar">
        <el-input
          v-model="searchForm.search"
          placeholder="搜索任务名称或摄像头名称"
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
        
        <el-select v-model="searchForm.status" placeholder="诊断状态" clearable style="width: 120px">
          <el-option label="正常" value="normal" />
          <el-option label="异常" value="abnormal" />
          <el-option label="警告" value="warning" />
          <el-option label="错误" value="error" />
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
            <div class="stat-icon normal">
              <el-icon><CircleCheck /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ stats.normal_count }}</div>
              <div class="stat-label">正常</div>
            </div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-card">
            <div class="stat-icon warning">
              <el-icon><Warning /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ stats.warning_count }}</div>
              <div class="stat-label">警告</div>
            </div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-card">
            <div class="stat-icon abnormal">
              <el-icon><CircleClose /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ stats.abnormal_count }}</div>
              <div class="stat-label">异常</div>
            </div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-card">
            <div class="stat-icon error">
              <el-icon><Close /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ stats.error_count }}</div>
              <div class="stat-label">错误</div>
            </div>
          </div>
        </el-col>
      </el-row>
    </div>

    <!-- 结果列表 -->
    <div class="table-container">
      <el-table
        :data="results"
        v-loading="loading"
        stripe
        style="width: 100%"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="55" />
        
        <el-table-column prop="task_name" label="任务名称" min-width="150">
          <template #default="{ row }">
            <div class="task-info">
              <span class="task-name">{{ row.task_name }}</span>
              <el-tag size="small" :type="getDiagnosisTypeColor(row.diagnosis_type)">
                {{ getDiagnosisTypeName(row.diagnosis_type) }}
              </el-tag>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column prop="camera_name" label="摄像头" width="150" />
        
        <el-table-column prop="status" label="诊断状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusColor(row.status)" size="small">
              {{ getStatusName(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column label="诊断分数" width="120">
          <template #default="{ row }">
            <div class="score-display">
              <el-progress
                :percentage="Math.round(row.score * 100)"
                :color="getScoreColor(row.score)"
                :stroke-width="8"
              />
              <span class="score-text">{{ (row.score * 100).toFixed(1) }}%</span>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column label="阈值对比" width="100">
          <template #default="{ row }">
            <div class="threshold-info">
              <span :class="{ 'threshold-exceeded': row.score < row.threshold }">{{ (row.threshold * 100).toFixed(1) }}%</span>
              <el-icon v-if="row.score < row.threshold" color="#F56C6C"><Warning /></el-icon>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column label="检测图像" width="100">
          <template #default="{ row }">
            <el-image
              v-if="row.image_url"
              :src="row.image_url"
              :preview-src-list="[row.image_url]"
              fit="cover"
              style="width: 60px; height: 40px; border-radius: 4px"
            />
            <span v-else class="text-muted">无图像</span>
          </template>
        </el-table-column>
        
        <el-table-column prop="detected_at" label="检测时间" width="150">
          <template #default="{ row }">
            {{ formatDateTime(row.detected_at) }}
          </template>
        </el-table-column>
        
        <el-table-column prop="processing_time" label="处理时间" width="100">
          <template #default="{ row }">
            <span v-if="row.processing_time">{{ row.processing_time }}ms</span>
            <span v-else class="text-muted">-</span>
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="handleViewDetail(row)">详情</el-button>
            <el-button size="small" type="primary" @click="handleViewImage(row)" :disabled="!row.image_url">
              查看图像
            </el-button>
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
      title="诊断结果详情"
      width="800px"
    >
      <div v-if="currentResult" class="result-detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="任务名称">{{ currentResult.task_name }}</el-descriptions-item>
          <el-descriptions-item label="摄像头">{{ currentResult.camera_name }}</el-descriptions-item>
          <el-descriptions-item label="诊断类型">
            <el-tag :type="getDiagnosisTypeColor(currentResult.diagnosis_type)">
              {{ getDiagnosisTypeName(currentResult.diagnosis_type) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="诊断状态">
            <el-tag :type="getStatusColor(currentResult.status)">
              {{ getStatusName(currentResult.status) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="诊断分数">{{ (currentResult.score * 100).toFixed(2) }}%</el-descriptions-item>
          <el-descriptions-item label="阈值">{{ (currentResult.threshold * 100).toFixed(2) }}%</el-descriptions-item>
          <el-descriptions-item label="检测时间">{{ formatDateTime(currentResult.detected_at) }}</el-descriptions-item>
          <el-descriptions-item label="处理时间">{{ currentResult.processing_time }}ms</el-descriptions-item>
        </el-descriptions>
        
        <div v-if="currentResult.details" class="detail-section">
          <h4>详细结果</h4>
          <el-card>
            <pre>{{ JSON.stringify(currentResult.details, null, 2) }}</pre>
          </el-card>
        </div>
        
        <div v-if="currentResult.image_url" class="image-section">
          <h4>检测图像</h4>
          <el-image
            :src="currentResult.image_url"
            :preview-src-list="[currentResult.image_url]"
            fit="contain"
            style="max-width: 100%; max-height: 400px"
          />
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Search, Refresh, Download, CircleCheck, Warning, CircleClose, Close } from '@element-plus/icons-vue'
import { diagnosisResultApi, type DiagnosisResult } from '@/api/diagnosis'
import { formatDateTime } from '@/utils/date'

// 响应式数据
const loading = ref(false)
const results = ref<DiagnosisResult[]>([])
const selectedResults = ref<DiagnosisResult[]>([])
const dateRange = ref<[string, string] | null>(null)

// 分页
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)

// 搜索表单
const searchForm = reactive({
  search: '',
  diagnosis_type: '',
  status: '',
  start_time: '',
  end_time: ''
})

// 统计数据
const stats = ref({
  normal_count: 0,
  warning_count: 0,
  abnormal_count: 0,
  error_count: 0
})

// 详情对话框
const detailVisible = ref(false)
const currentResult = ref<DiagnosisResult | null>(null)

// 计算属性和方法
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
    normal: '正常',
    abnormal: '异常',
    warning: '警告',
    error: '错误'
  }
  return statusMap[status] || status
}

const getStatusColor = (status: string) => {
  const colorMap: Record<string, string> = {
    normal: 'success',
    abnormal: 'danger',
    warning: 'warning',
    error: 'danger'
  }
  return colorMap[status] || 'info'
}

const getScoreColor = (score: number) => {
  if (score >= 0.8) return '#67C23A'
  if (score >= 0.6) return '#E6A23C'
  return '#F56C6C'
}

// 方法
const loadResults = async () => {
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
    
    const response = await diagnosisResultApi.getResults(params)
    results.value = response.data || []
    // 后端返回的是数组，不是分页格式，所以total设置为数组长度
    total.value = (response.data || []).length
    
    // 更新统计数据
    updateStats()
  } catch (error) {
    console.error('加载诊断结果失败:', error)
    ElMessage.error('加载诊断结果失败')
  } finally {
    loading.value = false
  }
}

const updateStats = () => {
  stats.value = {
    normal_count: results.value.filter(r => r.status === 'normal').length,
    warning_count: results.value.filter(r => r.status === 'warning').length,
    abnormal_count: results.value.filter(r => r.status === 'abnormal').length,
    error_count: results.value.filter(r => r.status === 'error').length
  }
}

const handleSearch = () => {
  currentPage.value = 1
  loadResults()
}

const handleReset = () => {
  Object.assign(searchForm, {
    search: '',
    diagnosis_type: '',
    status: '',
    start_time: '',
    end_time: ''
  })
  dateRange.value = null
  currentPage.value = 1
  loadResults()
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
  loadResults()
}

const handleCurrentChange = (page: number) => {
  currentPage.value = page
  loadResults()
}

const handleSelectionChange = (selection: DiagnosisResult[]) => {
  selectedResults.value = selection
}

const handleViewDetail = (result: DiagnosisResult) => {
  currentResult.value = result
  detailVisible.value = true
}

const handleViewImage = (result: DiagnosisResult) => {
  if (result.image_url) {
    window.open(result.image_url, '_blank')
  }
}

const handleExport = () => {
  // TODO: 实现导出功能
  ElMessage.info('导出功能开发中')
}

// 生命周期
onMounted(() => {
  loadResults()
})
</script>

<style scoped>
.diagnosis-results {
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

.stat-icon.normal {
  background: #67C23A;
}

.stat-icon.warning {
  background: #E6A23C;
}

.stat-icon.abnormal {
  background: #F56C6C;
}

.stat-icon.error {
  background: #F56C6C;
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

.task-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.task-name {
  font-weight: 500;
}

.score-display {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.score-text {
  font-size: 12px;
  text-align: center;
  font-weight: 500;
}

.threshold-info {
  display: flex;
  align-items: center;
  gap: 4px;
}

.threshold-exceeded {
  color: #F56C6C;
  font-weight: 500;
}

.text-muted {
  color: #999;
}

.pagination-container {
  padding: 20px;
  text-align: right;
}

.result-detail {
  max-height: 600px;
  overflow-y: auto;
}

.detail-section,
.image-section {
  margin-top: 20px;
}

.detail-section h4,
.image-section h4 {
  margin: 0 0 12px 0;
  font-size: 16px;
  font-weight: 600;
}

.detail-section pre {
  background: #f5f5f5;
  padding: 12px;
  border-radius: 4px;
  font-size: 12px;
  line-height: 1.4;
  max-height: 200px;
  overflow-y: auto;
}
</style>