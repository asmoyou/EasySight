<template>
  <div class="result-detail">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <el-button 
          type="text" 
          @click="$router.back()"
          class="back-btn"
        >
          <el-icon><ArrowLeft /></el-icon>
          返回
        </el-button>
        <h2>诊断结果详情</h2>
      </div>
      <div class="header-right">
        <el-button 
          type="primary" 
          @click="handleViewTask"
          v-if="result?.task_id"
        >
          查看任务
        </el-button>
      </div>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading-container">
      <el-skeleton :rows="8" animated />
    </div>

    <!-- 结果详情 -->
    <div v-else-if="result" class="result-content">
      <!-- 基本信息 -->
      <el-card class="info-card" shadow="never">
        <template #header>
          <div class="card-header">
            <span>基本信息</span>
            <el-tag 
              :type="getStatusTagType(result.status)"
              size="large"
            >
              {{ getStatusName(result.status) }}
            </el-tag>
          </div>
        </template>
        
        <el-row :gutter="24">
          <el-col :span="8">
            <div class="info-item">
              <label>结果ID：</label>
              <span>{{ result.id }}</span>
            </div>
          </el-col>
          <el-col :span="8">
            <div class="info-item">
              <label>关联任务：</label>
              <span>{{ result.task_name }}</span>
            </div>
          </el-col>
          <el-col :span="8">
            <div class="info-item">
              <label>执行时间：</label>
              <span>{{ result.execution_time ? `${result.execution_time}ms` : '-' }}</span>
            </div>
          </el-col>
          <el-col :span="8">
            <div class="info-item">
              <label>诊断评分：</label>
              <span>
                <el-rate 
                  v-if="result.score !== null && result.score !== undefined"
                  :model-value="result.score / 20"
                  disabled
                  show-score
                  text-color="#ff9900"
                  score-template="{value}分"
                />
                <span v-else>-</span>
              </span>
            </div>
          </el-col>
          <el-col :span="8">
            <div class="info-item">
              <label>创建时间：</label>
              <span>{{ formatDateTime(result.created_at) }}</span>
            </div>
          </el-col>
        </el-row>
      </el-card>

      <!-- 错误信息 -->
      <el-card 
        v-if="result.error_message" 
        class="error-card" 
        shadow="never"
      >
        <template #header>
          <div class="card-header">
            <el-icon color="#f56c6c"><Warning /></el-icon>
            <span>错误信息</span>
          </div>
        </template>
        <el-alert 
          :title="result.error_message"
          type="error"
          :closable="false"
          show-icon
        />
      </el-card>

      <!-- 诊断数据 -->
      <el-card class="data-card" shadow="never">
        <template #header>
          <div class="card-header">
            <span>诊断数据</span>
            <el-button 
              type="text" 
              @click="copyResultData"
              size="small"
            >
              <el-icon><CopyDocument /></el-icon>
              复制数据
            </el-button>
          </div>
        </template>
        
        <div class="json-viewer">
          <pre>{{ formatJson(result.result_data) }}</pre>
        </div>
      </el-card>

      <!-- 发现的问题 -->
      <el-card 
        v-if="result.issues_found && result.issues_found.length > 0" 
        class="issues-card" 
        shadow="never"
      >
        <template #header>
          <div class="card-header">
            <el-icon color="#e6a23c"><Warning /></el-icon>
            <span>发现的问题 ({{ result.issues_found.length }})</span>
          </div>
        </template>
        
        <div class="issues-list">
          <div 
            v-for="(issue, index) in result.issues_found" 
            :key="index"
            class="issue-item"
          >
            <div class="issue-header">
              <el-tag 
                :type="getIssueSeverityType(issue.severity)"
                size="small"
              >
                {{ issue.severity || '一般' }}
              </el-tag>
              <span class="issue-title">{{ issue.title || `问题 ${index + 1}` }}</span>
            </div>
            <div class="issue-content">
              <p v-if="issue.description">{{ issue.description }}</p>
              <div v-if="issue.details" class="issue-details">
                <pre>{{ formatJson(issue.details) }}</pre>
              </div>
            </div>
          </div>
        </div>
      </el-card>

      <!-- 建议和推荐 -->
      <el-card 
        v-if="result.recommendations && result.recommendations.length > 0" 
        class="recommendations-card" 
        shadow="never"
      >
        <template #header>
          <div class="card-header">
            <el-icon color="#67c23a"><Check /></el-icon>
            <span>建议和推荐</span>
          </div>
        </template>
        
        <ul class="recommendations-list">
          <li 
            v-for="(recommendation, index) in result.recommendations" 
            :key="index"
            class="recommendation-item"
          >
            {{ recommendation }}
          </li>
        </ul>
      </el-card>
    </div>

    <!-- 错误状态 -->
    <div v-else class="error-container">
      <el-result
        icon="error"
        title="加载失败"
        sub-title="无法加载诊断结果详情"
      >
        <template #extra>
          <el-button type="primary" @click="loadResult">重新加载</el-button>
        </template>
      </el-result>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft, Warning, CopyDocument, Check } from '@element-plus/icons-vue'
import { diagnosisResultApi } from '@/api/diagnosis'
import type { DiagnosisResult, DiagnosisStatus } from '@/api/diagnosis'

const route = useRoute()
const router = useRouter()

// 响应式数据
const loading = ref(false)
const result = ref<DiagnosisResult | null>(null)

// 计算属性
const resultId = computed(() => {
  const id = route.params.id
  return Array.isArray(id) ? parseInt(id[0]) : parseInt(id as string)
})

// 方法
const loadResult = async () => {
  if (!resultId.value || isNaN(resultId.value)) {
    ElMessage.error('无效的结果ID')
    return
  }

  loading.value = true
  try {
    const response = await diagnosisResultApi.getResult(resultId.value)
    result.value = response.data
  } catch (error) {
    console.error('加载诊断结果失败:', error)
    ElMessage.error('加载诊断结果失败')
  } finally {
    loading.value = false
  }
}

const handleViewTask = () => {
  if (result.value?.task_id) {
    router.push(`/diagnosis/tasks/${result.value.task_id}`)
  }
}

const getStatusName = (status: DiagnosisStatus): string => {
  const statusMap = {
    'SUCCESS': '成功',
    'FAILED': '失败',
    'WARNING': '警告',
    'RUNNING': '运行中'
  }
  return statusMap[status] || status
}

const getStatusTagType = (status: DiagnosisStatus): string => {
  const typeMap = {
    'SUCCESS': 'success',
    'FAILED': 'danger',
    'WARNING': 'warning',
    'RUNNING': 'info'
  }
  return typeMap[status] || 'info'
}

const getIssueSeverityType = (severity?: string): string => {
  const typeMap = {
    '严重': 'danger',
    '重要': 'warning',
    '一般': 'info',
    '轻微': 'success'
  }
  return typeMap[severity || '一般'] || 'info'
}

const formatDateTime = (dateTime: string): string => {
  return new Date(dateTime).toLocaleString('zh-CN')
}

const formatJson = (data: any): string => {
  if (!data) return ''
  try {
    return JSON.stringify(data, null, 2)
  } catch {
    return String(data)
  }
}

const copyResultData = async () => {
  if (!result.value?.result_data) return
  
  try {
    await navigator.clipboard.writeText(formatJson(result.value.result_data))
    ElMessage.success('数据已复制到剪贴板')
  } catch {
    ElMessage.error('复制失败')
  }
}

// 生命周期
onMounted(() => {
  loadResult()
})
</script>

<style scoped>
.result-detail {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid #ebeef5;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.back-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 8px 12px;
  color: #606266;
}

.back-btn:hover {
  color: #409eff;
}

.header-left h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: #303133;
}

.loading-container {
  padding: 20px;
}

.result-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.info-card,
.error-card,
.data-card,
.issues-card,
.recommendations-card {
  border: 1px solid #ebeef5;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
}

.card-header span {
  display: flex;
  align-items: center;
  gap: 8px;
}

.info-item {
  margin-bottom: 16px;
}

.info-item label {
  font-weight: 500;
  color: #606266;
  margin-right: 8px;
}

.json-viewer {
  background: #f5f7fa;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  padding: 16px;
  max-height: 400px;
  overflow: auto;
}

.json-viewer pre {
  margin: 0;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 12px;
  line-height: 1.5;
  color: #2c3e50;
}

.issues-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.issue-item {
  border: 1px solid #ebeef5;
  border-radius: 6px;
  padding: 16px;
  background: #fafafa;
}

.issue-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.issue-title {
  font-weight: 500;
  color: #303133;
}

.issue-content p {
  margin: 0 0 8px 0;
  color: #606266;
  line-height: 1.6;
}

.issue-details {
  background: #f0f2f5;
  border-radius: 4px;
  padding: 12px;
  margin-top: 8px;
}

.issue-details pre {
  margin: 0;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 11px;
  line-height: 1.4;
  color: #2c3e50;
}

.recommendations-list {
  margin: 0;
  padding-left: 20px;
}

.recommendation-item {
  margin-bottom: 8px;
  line-height: 1.6;
  color: #606266;
}

.error-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 400px;
}
</style>