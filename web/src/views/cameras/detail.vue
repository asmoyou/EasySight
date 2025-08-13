<template>
  <div class="camera-detail">
    <div class="page-header">
      <div class="header-left">
        <el-button @click="goBack" type="text">
          <el-icon><ArrowLeft /></el-icon>
          返回
        </el-button>
        <h2>{{ cameraInfo?.name }} - 摄像头详情</h2>
      </div>
      <div class="header-actions">
        <el-button type="primary" @click="handleEdit">
          <el-icon><Edit /></el-icon>
          编辑
        </el-button>
        <el-button type="success" @click="handlePreview" :disabled="!canPreview">
          <el-icon><VideoCamera /></el-icon>
          预览
        </el-button>
      </div>
    </div>

    <div v-loading="loading" class="detail-content">
      <el-row :gutter="20">
        <!-- 基本信息 -->
        <el-col :span="12">
          <el-card class="info-card">
            <template #header>
              <div class="card-header">
                <span>基本信息</span>
                <el-tag :type="statusTagType">{{ statusText }}</el-tag>
              </div>
            </template>
            <el-descriptions :column="1" border>
              <el-descriptions-item label="摄像头编码">{{ cameraInfo?.code }}</el-descriptions-item>
              <el-descriptions-item label="摄像头名称">{{ cameraInfo?.name }}</el-descriptions-item>
              <el-descriptions-item label="摄像头类型">{{ cameraTypeText }}</el-descriptions-item>
              <el-descriptions-item label="安装位置">{{ cameraInfo?.location || '未设置' }}</el-descriptions-item>
              <el-descriptions-item label="IP地址">{{ cameraInfo?.ip_address || '未设置' }}</el-descriptions-item>
              <el-descriptions-item label="端口">{{ cameraInfo?.port || '未设置' }}</el-descriptions-item>
              <el-descriptions-item label="描述">{{ cameraInfo?.description || '无' }}</el-descriptions-item>
            </el-descriptions>
          </el-card>
        </el-col>

        <!-- 设备信息 -->
        <el-col :span="12">
          <el-card class="info-card">
            <template #header>
              <span>设备信息</span>
            </template>
            <el-descriptions :column="1" border>
              <el-descriptions-item label="制造商">{{ cameraInfo?.manufacturer || '未设置' }}</el-descriptions-item>
              <el-descriptions-item label="型号">{{ cameraInfo?.model || '未设置' }}</el-descriptions-item>
              <el-descriptions-item label="固件版本">{{ cameraInfo?.firmware_version || '未设置' }}</el-descriptions-item>
              <el-descriptions-item label="分辨率">{{ cameraInfo?.resolution || '未设置' }}</el-descriptions-item>
              <el-descriptions-item label="帧率">{{ cameraInfo?.frame_rate ? `${cameraInfo.frame_rate} fps` : '未设置' }}</el-descriptions-item>
              <el-descriptions-item label="码率">{{ cameraInfo?.bitrate ? `${cameraInfo.bitrate} kbps` : '未设置' }}</el-descriptions-item>
            </el-descriptions>
          </el-card>
        </el-col>
      </el-row>

      <el-row :gutter="20" style="margin-top: 20px">
        <!-- 流媒体配置 -->
        <el-col :span="12">
          <el-card class="info-card">
            <template #header>
              <span>流媒体配置</span>
            </template>
            <el-descriptions :column="1" border>
              <el-descriptions-item label="主流地址">
                <el-text class="stream-url" :title="cameraInfo?.stream_url">
                  {{ cameraInfo?.stream_url }}
                </el-text>
              </el-descriptions-item>
              <el-descriptions-item label="备用流地址">
                <el-text class="stream-url" :title="cameraInfo?.backup_stream_url">
                  {{ cameraInfo?.backup_stream_url || '未设置' }}
                </el-text>
              </el-descriptions-item>
              <el-descriptions-item label="媒体代理">{{ cameraInfo?.media_proxy_name || '未设置' }}</el-descriptions-item>
            </el-descriptions>
          </el-card>
        </el-col>

        <!-- 状态信息 -->
        <el-col :span="12">
          <el-card class="info-card">
            <template #header>
              <span>状态信息</span>
            </template>
            <el-descriptions :column="1" border>
              <el-descriptions-item label="启用状态">
                <el-tag :type="cameraInfo?.is_active ? 'success' : 'info'">
                  {{ cameraInfo?.is_active ? '启用' : '禁用' }}
                </el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="录制状态">
                <el-tag :type="cameraInfo?.is_recording ? 'success' : 'info'">
                  {{ cameraInfo?.is_recording ? '录制中' : '未录制' }}
                </el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="告警状态">
                <el-tag :type="cameraInfo?.alarm_enabled ? 'warning' : 'info'">
                  {{ cameraInfo?.alarm_enabled ? '启用' : '禁用' }}
                </el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="最后心跳">{{ lastHeartbeatText }}</el-descriptions-item>
              <el-descriptions-item label="创建时间">{{ formatDateTime(cameraInfo?.created_at) }}</el-descriptions-item>
              <el-descriptions-item label="更新时间">{{ formatDateTime(cameraInfo?.updated_at) }}</el-descriptions-item>
            </el-descriptions>
          </el-card>
        </el-col>
      </el-row>

      <!-- 位置信息 -->
      <el-row :gutter="20" style="margin-top: 20px" v-if="hasLocationInfo">
        <el-col :span="24">
          <el-card class="info-card">
            <template #header>
              <span>位置信息</span>
            </template>
            <el-descriptions :column="3" border>
              <el-descriptions-item label="经度">{{ cameraInfo?.longitude || '未设置' }}</el-descriptions-item>
              <el-descriptions-item label="纬度">{{ cameraInfo?.latitude || '未设置' }}</el-descriptions-item>
              <el-descriptions-item label="海拔">{{ cameraInfo?.altitude ? `${cameraInfo.altitude}m` : '未设置' }}</el-descriptions-item>
            </el-descriptions>
          </el-card>
        </el-col>
      </el-row>

      <!-- 自定义属性 -->
      <el-row :gutter="20" style="margin-top: 20px" v-if="hasCustomAttributes">
        <el-col :span="24">
          <el-card class="info-card">
            <template #header>
              <span>自定义属性</span>
            </template>
            <el-descriptions :column="2" border>
              <el-descriptions-item 
                v-for="(value, key) in cameraInfo?.custom_attributes" 
                :key="key" 
                :label="key"
              >
                {{ value }}
              </el-descriptions-item>
            </el-descriptions>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 预览对话框 -->
    <el-dialog
      v-model="previewDialogVisible"
      title="摄像头预览"
      width="80%"
      :close-on-click-modal="false"
    >
      <div class="preview-container">
        <div v-if="previewLoading" class="preview-loading">
          <el-icon class="is-loading"><Loading /></el-icon>
          <span>正在加载预览...</span>
        </div>
        <div v-else-if="previewError" class="preview-error">
          <el-icon><Warning /></el-icon>
          <span>{{ previewError }}</span>
        </div>
        <video 
          v-else-if="previewUrl" 
          ref="videoRef"
          :src="previewUrl" 
          controls 
          autoplay 
          muted
          class="preview-video"
          @error="handleVideoError"
          @loadstart="handleVideoLoadStart"
          @loadeddata="handleVideoLoaded"
        >
          您的浏览器不支持视频播放
        </video>
      </div>
      <template #footer>
        <el-button @click="previewDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft, Edit, VideoCamera, Loading, Warning } from '@element-plus/icons-vue'
import { cameraApi } from '@/api/cameras'
import type { Camera, CameraType, CameraStatus } from '@/types/camera'
import { formatDateTime } from '@/utils/date'

const route = useRoute()
const router = useRouter()

const loading = ref(false)
const cameraInfo = ref<Camera | null>(null)
const previewDialogVisible = ref(false)
const previewLoading = ref(false)
const previewError = ref('')
const previewUrl = ref('')
const videoRef = ref<HTMLVideoElement>()

// 计算属性
const statusTagType = computed(() => {
  if (!cameraInfo.value) return 'info'
  switch (cameraInfo.value.status) {
    case 'online': return 'success'
    case 'offline': return 'danger'
    case 'error': return 'danger'
    case 'maintenance': return 'warning'
    default: return 'info'
  }
})

const statusText = computed(() => {
  if (!cameraInfo.value) return '未知'
  switch (cameraInfo.value.status) {
    case 'online': return '在线'
    case 'offline': return '离线'
    case 'error': return '错误'
    case 'maintenance': return '维护中'
    default: return '未知'
  }
})

const cameraTypeText = computed(() => {
  if (!cameraInfo.value) return '未知'
  switch (cameraInfo.value.camera_type) {
    case 'ip_camera': return 'IP摄像头'
    case 'analog_camera': return '模拟摄像头'
    case 'usb_camera': return 'USB摄像头'
    case 'wireless_camera': return '无线摄像头'
    default: return '未知类型'
  }
})

const lastHeartbeatText = computed(() => {
  if (!cameraInfo.value?.last_heartbeat) return '无'
  return formatDateTime(cameraInfo.value.last_heartbeat)
})

const canPreview = computed(() => {
  return cameraInfo.value?.is_active && cameraInfo.value?.status === 'online'
})

const hasLocationInfo = computed(() => {
  return cameraInfo.value?.longitude || cameraInfo.value?.latitude || cameraInfo.value?.altitude
})

const hasCustomAttributes = computed(() => {
  return cameraInfo.value?.custom_attributes && Object.keys(cameraInfo.value.custom_attributes).length > 0
})

// 方法
const goBack = () => {
  router.back()
}

const handleEdit = () => {
  // 跳转到编辑页面或打开编辑对话框
  router.push(`/cameras/list?edit=${cameraInfo.value?.id}`)
}

const handlePreview = async () => {
  if (!cameraInfo.value || !canPreview.value) {
    ElMessage.warning('摄像头不在线或未启用，无法预览')
    return
  }

  previewDialogVisible.value = true
  previewLoading.value = true
  previewError.value = ''
  previewUrl.value = ''

  try {
    const response = await cameraApi.getPreview(cameraInfo.value.id)
    if (response.data.code === 200) {
      previewUrl.value = response.data.data.preview_url
    } else {
      previewError.value = response.data.message || '获取预览地址失败'
    }
  } catch (error: any) {
    console.error('获取预览地址错误:', error)
    previewError.value = error.response?.data?.detail || '获取预览地址失败'
  } finally {
    previewLoading.value = false
  }
}

const handleVideoError = () => {
  previewError.value = '视频加载失败，请检查网络连接或摄像头状态'
}

const handleVideoLoadStart = () => {
  previewLoading.value = true
}

const handleVideoLoaded = () => {
  previewLoading.value = false
}

const loadCameraDetail = async () => {
  const cameraId = Number(route.params.id)
  if (!cameraId) {
    ElMessage.error('摄像头ID无效')
    router.push('/cameras/list')
    return
  }

  loading.value = true
  try {
    const response = await cameraApi.getCamera(cameraId)
    // 后端直接返回camera对象，不是包装在{code: 200, data: camera}中
    if (response.status === 200 && response.data) {
      cameraInfo.value = response.data
    } else {
      ElMessage.error('获取摄像头详情失败')
      router.push('/cameras/list')
    }
  } catch (error: any) {
    console.error('获取摄像头详情错误:', error)
    ElMessage.error(error.response?.data?.detail || '获取摄像头详情失败')
    router.push('/cameras/list')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadCameraDetail()
})
</script>

<style scoped>
.camera-detail {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.header-left h2 {
  margin: 0;
  color: #303133;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.detail-content {
  min-height: 400px;
}

.info-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.stream-url {
  max-width: 300px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  display: inline-block;
}

.preview-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 400px;
  background: #f5f5f5;
  border-radius: 4px;
}

.preview-loading,
.preview-error {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  color: #909399;
}

.preview-error {
  color: #f56c6c;
}

.preview-video {
  width: 100%;
  max-height: 500px;
  border-radius: 4px;
}

:deep(.el-descriptions__label) {
  width: 120px;
}
</style>