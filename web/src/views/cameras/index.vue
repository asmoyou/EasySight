<template>
  <div class="camera-management">
    <div class="page-header">
      <h2>摄像头管理</h2>
      <div class="header-buttons">
        <el-button type="success" @click="handleMultiPreview" :disabled="onlineCameras.length === 0">
          <el-icon><Monitor /></el-icon>
          多屏预览
        </el-button>
        <el-button type="primary" @click="handleAdd">
          <el-icon><Plus /></el-icon>
          添加摄像头
        </el-button>
      </div>
    </div>

    <div class="search-bar">
      <el-input
        v-model="searchText"
        placeholder="搜索摄像头名称或IP地址"
        style="width: 300px; margin-right: 16px"
        clearable
        @input="handleSearch"
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>
      <el-select v-model="statusFilter" placeholder="状态筛选" style="width: 120px; margin-right: 16px" @change="handleFilter">
        <el-option label="全部" value="" />
        <el-option label="在线" value="online" />
        <el-option label="离线" value="offline" />
      </el-select>
      <el-select v-model="groupFilter" placeholder="分组筛选" style="width: 150px; margin-right: 16px" @change="handleFilter">
        <el-option label="全部分组" value="" />
        <el-option label="未分组" value="unassigned" />
        <el-option
          v-for="group in cameraGroups"
          :key="group.id"
          :label="group.name"
          :value="group.id"
        />
      </el-select>
      <el-button @click="handleRefresh">
        <el-icon><Refresh /></el-icon>
        刷新
      </el-button>
      <el-button type="success" @click="handleBatchGroup" :disabled="selectedCameras.length === 0">
        批量分组
      </el-button>
    </div>

    <el-table 
      :data="filteredCameras" 
      v-loading="loading" 
      style="width: 100%"
      @selection-change="handleSelectionChange"
    >
      <el-table-column type="selection" width="55" />
      <el-table-column prop="name" label="摄像头名称" min-width="150" />
      <el-table-column prop="code" label="编码" width="120" />
      <el-table-column prop="ip_address" label="IP地址" width="140" />
      <el-table-column prop="port" label="端口" width="80" />
      <el-table-column prop="media_proxy_name" label="媒体节点" width="120">
        <template #default="{ row }">
          <el-tag v-if="row.media_proxy_name" type="info" size="small">
            {{ row.media_proxy_name }}
          </el-tag>
          <span v-else class="text-gray-400">未分配</span>
        </template>
      </el-table-column>
      <el-table-column prop="stream_url" label="视频源" min-width="200">
        <template #default="{ row }">
          <el-tooltip :content="row.stream_url" placement="top">
            <span class="truncate">{{ row.stream_url }}</span>
          </el-tooltip>
        </template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="getStatusType(row.status)">
            {{ getStatusText(row.status) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="location" label="位置" min-width="120" />
      <el-table-column label="所属分组" width="150">
        <template #default="{ row }">
          <el-tag v-if="getCameraGroups(row.id).length > 0" type="primary" size="small">
            {{ getCameraGroups(row.id).map(g => g.name).join(', ') }}
          </el-tag>
          <span v-else class="text-gray-400">未分组</span>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="160">
        <template #default="{ row }">
          {{ formatDateTime(row.created_at) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="280" fixed="right">
        <template #default="{ row }">
          <el-button size="small" @click="handleView(row)">查看</el-button>
          <el-button size="small" type="primary" @click="handleEdit(row)">编辑</el-button>
          <el-button size="small" type="info" @click="handlePreview(row)" :disabled="row.status !== 'online'">
            <el-icon><VideoPlay /></el-icon>
            预览
          </el-button>

          <el-dropdown @command="(command) => handleGroupAction(command, row)">
            <el-button size="small" type="success">
              分组操作<el-icon class="el-icon--right"><arrow-down /></el-icon>
            </el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="assign">分配到分组</el-dropdown-item>
                <el-dropdown-item command="remove">移出分组</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
          <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <div class="pagination">
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

    <!-- 摄像头创建/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="800px"
      :close-on-click-modal="false"
    >
      <el-form
        :model="formData"
        label-width="120px"
        :disabled="dialogMode === 'view'"
      >
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="摄像头编码" required>
              <el-input v-model="formData.code" placeholder="请输入摄像头编码" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="摄像头名称" required>
              <el-input v-model="formData.name" placeholder="请输入摄像头名称" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="摄像头类型">
              <el-select v-model="formData.camera_type" placeholder="请选择摄像头类型">
                <el-option label="IP摄像头" value="ip_camera" />
                <el-option label="模拟摄像头" value="analog_camera" />
                <el-option label="USB摄像头" value="usb_camera" />
                <el-option label="无线摄像头" value="wireless_camera" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="媒体节点">
              <el-select v-model="formData.media_proxy_id" placeholder="请选择媒体节点" clearable>
                <el-option
                  v-for="proxy in mediaProxies"
                  :key="proxy.id"
                  :label="proxy.name"
                  :value="proxy.id"
                />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="主视频源" required>
          <el-input v-model="formData.stream_url" placeholder="请输入主视频源地址" />
        </el-form-item>

        <el-form-item label="备用视频源">
          <el-input v-model="formData.backup_stream_url" placeholder="请输入备用视频源地址" />
        </el-form-item>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="IP地址">
              <el-input v-model="formData.ip_address" placeholder="请输入IP地址" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="端口">
              <el-input-number v-model="formData.port" :min="1" :max="65535" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="分辨率">
              <el-select v-model="formData.resolution" placeholder="请选择分辨率">
                <el-option label="1920x1080" value="1920x1080" />
                <el-option label="1280x720" value="1280x720" />
                <el-option label="640x480" value="640x480" />
                <el-option label="自定义" value="custom" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="帧率">
              <el-input-number v-model="formData.frame_rate" :min="1" :max="60" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="码率(kbps)">
              <el-input-number v-model="formData.bitrate" :min="64" :max="10240" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="位置">
              <el-input v-model="formData.location" placeholder="请输入摄像头位置" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="制造商">
              <el-input v-model="formData.manufacturer" placeholder="请输入制造商" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="型号">
              <el-input v-model="formData.model" placeholder="请输入型号" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="固件版本">
              <el-input v-model="formData.firmware_version" placeholder="请输入固件版本" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="启用状态">
              <el-switch v-model="formData.is_active" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="录像状态">
              <el-switch v-model="formData.is_recording" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="告警启用">
              <el-switch v-model="formData.alarm_enabled" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="描述">
          <el-input
            v-model="formData.description"
            type="textarea"
            :rows="3"
            placeholder="请输入描述信息"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button
            v-if="dialogMode !== 'view'"
            type="primary"
            @click="handleSave"
            :loading="loading"
          >
            {{ dialogMode === 'create' ? '创建' : '更新' }}
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 分组操作对话框 -->
    <el-dialog
      v-model="groupDialogVisible"
      :title="groupDialogTitle"
      width="500px"
      :close-on-click-modal="false"
    >
      <div v-if="groupDialogMode === 'remove'">
        <p>请选择要移出的分组：</p>
        <el-select v-model="selectedGroupId" placeholder="请选择分组" style="width: 100%">
          <el-option
            v-for="group in cameraGroups.filter(g => 
              operatingCameras.some(camera => g.camera_ids.includes(camera.id))
            )"
            :key="group.id"
            :label="group.name"
            :value="group.id"
          />
        </el-select>
      </div>
      <div v-else>
        <p>请选择目标分组：</p>
        <el-select v-model="selectedGroupId" placeholder="请选择分组" style="width: 100%">
          <el-option
            v-for="group in cameraGroups"
            :key="group.id"
            :label="group.name"
            :value="group.id"
          />
        </el-select>
      </div>
      
      <div style="margin-top: 16px">
        <p>操作摄像头：</p>
        <el-tag
          v-for="camera in operatingCameras"
          :key="camera.id"
          style="margin-right: 8px; margin-bottom: 8px"
        >
          {{ camera.name }}
        </el-tag>
      </div>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="groupDialogVisible = false">取消</el-button>
          <el-button
            type="primary"
            @click="handleGroupOperation"
            :loading="loading"
          >
            确定
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 视频预览对话框 -->
    <el-dialog
      v-model="previewDialogVisible"
      :title="`${previewCamera?.name || ''} - 视频预览`"
      width="90%"
      top="5vh"
      :before-close="handleClosePreview"
      :close-on-click-modal="false"
      :close-on-press-escape="true"
    >
      <div class="preview-container">
        <video-preview
          v-if="previewUrl"
          :video_url="previewUrl"
          @error="handleVideoError"
          @loaded="handleVideoLoaded"
        />
        <div v-else class="no-preview">
          <el-icon size="48"><VideoCamera /></el-icon>
          <p>无法获取预览链接</p>
          <p class="text-gray-500">请检查摄像头状态和网络连接</p>
        </div>
      </div>
      
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="handleClosePreview">关闭</el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 多屏预览对话框 -->
    <el-dialog
      v-model="multiPreviewDialogVisible"
      title="多屏视频预览"
      width="95%"
      top="2vh"
      :before-close="handleCloseMultiPreview"
      :close-on-click-modal="false"
      :close-on-press-escape="true"
      class="multi-preview-dialog"
    >
      <div class="multi-preview-header">
        <div class="layout-controls">
          <span>分屏布局：</span>
          <el-radio-group v-model="gridLayout" @change="handleLayoutChange">
            <el-radio-button :label="1">1分屏</el-radio-button>
            <el-radio-button :label="4">4分屏</el-radio-button>
            <el-radio-button :label="9">9分屏</el-radio-button>
            <el-radio-button :label="16">16分屏</el-radio-button>
          </el-radio-group>
        </div>
        <div class="camera-selector">
          <span>选择摄像头：</span>
          <el-select
            v-model="selectedCameraIds"
            multiple
            placeholder="请选择要预览的摄像头"
            style="width: 300px"
            :max-collapse-tags="3"
            collapse-tags
            collapse-tags-tooltip
            @change="handleCameraSelection"
          >
            <el-option
              v-for="camera in onlineCameras"
              :key="camera.id"
              :label="camera.name"
              :value="camera.id"
              :disabled="selectedCameraIds.length >= gridLayout && !selectedCameraIds.includes(camera.id)"
            >
              <span>{{ camera.name }}</span>
              <span style="float: right; color: #8492a6; font-size: 13px">{{ camera.location || '未设置位置' }}</span>
            </el-option>
          </el-select>
        </div>
      </div>
      
      <div class="multi-preview-container" :class="`grid-${gridLayout}`">
        <div
          v-for="(slot, index) in gridSlots"
          :key="index"
          class="preview-slot"
          :class="{ 'has-video': slot.camera }"
        >
          <div v-if="slot.camera" class="video-wrapper">
            <div class="video-header">
              <span class="camera-name">{{ slot.camera.name }}</span>
              <el-button
                size="small"
                type="danger"
                text
                @click="removeCameraFromSlot(index)"
              >
                <el-icon><Close /></el-icon>
              </el-button>
            </div>
            <video-preview
              :video_url="slot.previewUrl"
              @error="handleMultiVideoError(slot.camera, index)"
              @loaded="handleMultiVideoLoaded(slot.camera, index)"
              class="multi-video-player"
            />
          </div>
          <div v-else class="empty-slot">
            <el-icon size="32"><VideoCamera /></el-icon>
            <p>空闲位置</p>
            <p class="slot-number">{{ index + 1 }}</p>
          </div>
        </div>
      </div>
      
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="handleCloseMultiPreview">关闭</el-button>
          <el-button type="primary" @click="handleFullscreen">全屏显示</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Refresh, Plus, View, Edit, Delete, ArrowDown, VideoPlay, VideoCamera, Monitor, Close } from '@element-plus/icons-vue'
import { cameraApi, mediaProxyApi } from '@/api/cameras'
import { getGroups, updateGroup } from '@/api/groups'
import VideoPreview from '@/components/videoPreview.vue'
import type { Camera, CameraQueryParams, MediaProxy, CameraCreateForm, CameraUpdateForm } from '@/types/camera'
import type { CameraGroup } from '@/api/groups'

// 响应式数据
const loading = ref(false)
const searchText = ref('')
const statusFilter = ref('')
const groupFilter = ref('')
const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(0)

// 摄像头列表、媒体代理列表和分组列表
const cameras = ref<Camera[]>([])
const mediaProxies = ref<MediaProxy[]>([])
const cameraGroups = ref<CameraGroup[]>([])
const selectedCameras = ref<Camera[]>([])

// 对话框状态
const dialogVisible = ref(false)
const dialogTitle = ref('')
const dialogMode = ref<'create' | 'edit' | 'view'>('create')
const currentCamera = ref<Camera | null>(null)

// 分组操作对话框
const groupDialogVisible = ref(false)
const groupDialogTitle = ref('')
const groupDialogMode = ref<'assign' | 'remove' | 'batch'>('assign')
const selectedGroupId = ref<number | null>(null)
const operatingCameras = ref<Camera[]>([])

// 预览对话框
const previewDialogVisible = ref(false)
const previewCamera = ref<Camera | null>(null)
const previewUrl = ref('')

// 多屏预览对话框
const multiPreviewDialogVisible = ref(false)
const gridLayout = ref(4) // 默认4分屏
const selectedCameraIds = ref<number[]>([])
const gridSlots = ref<Array<{ camera: Camera | null, previewUrl: string }>>([])

// 表单数据
const formData = ref<CameraCreateForm>({
  code: '',
  name: '',
  stream_url: '',
  backup_stream_url: '',
  camera_type: 'ip_camera' as any,
  media_proxy_id: undefined,
  location: '',
  ip_address: '',
  port: 554,
  resolution: '1920x1080',
  frame_rate: 25,
  bitrate: 2048,
  is_active: true,
  is_recording: false,
  alarm_enabled: false,
  description: ''
})

const filteredCameras = computed(() => {
  let result = cameras.value
  
  if (searchText.value) {
    result = result.filter(camera => 
      camera.name.toLowerCase().includes(searchText.value.toLowerCase()) ||
      camera.code.toLowerCase().includes(searchText.value.toLowerCase()) ||
      camera.ip_address?.includes(searchText.value) ||
      camera.location?.toLowerCase().includes(searchText.value.toLowerCase())
    )
  }
  
  if (statusFilter.value) {
    result = result.filter(camera => camera.status === statusFilter.value)
  }
  
  if (groupFilter.value) {
    if (groupFilter.value === 'unassigned') {
      // 筛选未分组的摄像头
      result = result.filter(camera => 
        !cameraGroups.value.some(group => group.camera_ids.includes(camera.id))
      )
    } else {
      // 筛选指定分组的摄像头
      const groupId = parseInt(groupFilter.value as string)
      result = result.filter(camera => 
        cameraGroups.value.some(group => 
          group.id === groupId && group.camera_ids.includes(camera.id)
        )
      )
    }
  }
  
  return result
})

// 在线摄像头列表
const onlineCameras = computed(() => {
  return cameras.value.filter(camera => camera.status === 'online')
})

// 工具函数
const getStatusType = (status: string) => {
  switch (status) {
    case 'online': return 'success'
    case 'offline': return 'danger'
    case 'error': return 'danger'
    case 'maintenance': return 'warning'
    default: return 'info'
  }
}

const getStatusText = (status: string) => {
  switch (status) {
    case 'online': return '在线'
    case 'offline': return '离线'
    case 'error': return '错误'
    case 'maintenance': return '维护'
    default: return '未知'
  }
}

const formatDateTime = (dateString: string) => {
  return new Date(dateString).toLocaleString('zh-CN')
}

// 重置表单
const resetForm = () => {
  formData.value = {
    code: '',
    name: '',
    stream_url: '',
    backup_stream_url: '',
    camera_type: 'ip_camera' as any,
    media_proxy_id: undefined,
    location: '',
    ip_address: '',
    port: 554,
    resolution: '1920x1080',
    frame_rate: 25,
    bitrate: 2048,
    is_active: true,
    is_recording: false,
    alarm_enabled: false,
    description: ''
  }
}

// 加载摄像头列表
const loadCameras = async () => {
  try {
    loading.value = true
    const params: CameraQueryParams = {
      page: currentPage.value,
      page_size: pageSize.value,
      search: searchText.value || undefined
    }
    
    if (statusFilter.value) {
      params.is_active = statusFilter.value === 'online'
    }
    
    const response = await cameraApi.getCameras(params)
    // 后端直接返回CameraListResponse，不是包装在ApiResponse中
    if (response.data && response.data.cameras) {
      cameras.value = response.data.cameras
      total.value = response.data.total
    } else {
      ElMessage.error('加载摄像头列表失败')
    }
  } catch (error) {
    console.error('加载摄像头列表失败:', error)
    ElMessage.error('加载摄像头列表失败')
  } finally {
    loading.value = false
  }
}

// 加载媒体代理列表
const loadMediaProxies = async () => {
  try {
    const response = await mediaProxyApi.getMediaProxies()
    // 后端直接返回MediaProxy数组，不是包装在ApiResponse中
    if (response.data && Array.isArray(response.data)) {
      mediaProxies.value = response.data
    }
  } catch (error) {
    console.error('加载媒体代理列表失败:', error)
  }
}

// 加载分组列表
const loadCameraGroups = async () => {
  try {
    const response = await getGroups()
    if (response.data) {
      cameraGroups.value = response.data
    }
  } catch (error) {
    console.error('加载分组列表失败:', error)
  }
}

// 方法
const handleAdd = () => {
  dialogMode.value = 'create'
  dialogTitle.value = '添加摄像头'
  resetForm()
  dialogVisible.value = true
}

const handleView = (row: Camera) => {
  dialogMode.value = 'view'
  dialogTitle.value = '查看摄像头'
  currentCamera.value = row
  Object.assign(formData.value, row)
  dialogVisible.value = true
}

const handleEdit = (row: Camera) => {
  dialogMode.value = 'edit'
  dialogTitle.value = '编辑摄像头'
  currentCamera.value = row
  Object.assign(formData.value, row)
  dialogVisible.value = true
}

const handleDelete = async (row: Camera) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除摄像头 "${row.name}" 吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    const response = await cameraApi.deleteCamera(row.id)
    // 删除成功时，后端返回200状态码
    if (response.status === 200) {
      ElMessage.success('删除成功')
      await loadCameras()
    } else {
      ElMessage.error('删除失败')
    }
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('删除摄像头失败:', error)
      ElMessage.error('删除失败')
    }
  }
}

const handleSearch = () => {
  currentPage.value = 1
  loadCameras()
}

const handleFilter = () => {
  currentPage.value = 1
  loadCameras()
}

const handleRefresh = () => {
  loadCameras()
}

const handleSizeChange = (size: number) => {
  pageSize.value = size
  currentPage.value = 1
  loadCameras()
}

const handleCurrentChange = (page: number) => {
  currentPage.value = page
  loadCameras()
}

// 保存摄像头
const handleSave = async () => {
  try {
    loading.value = true
    
    if (dialogMode.value === 'create') {
      const response = await cameraApi.createCamera(formData.value)
      // 创建成功时，后端返回200状态码和摄像头数据
      if (response.status === 200 && response.data) {
        ElMessage.success('创建成功')
        dialogVisible.value = false
        await loadCameras()
      } else {
        ElMessage.error('创建失败')
      }
    } else if (dialogMode.value === 'edit' && currentCamera.value) {
      const updateData: CameraUpdateForm = { ...formData.value }
      const response = await cameraApi.updateCamera(currentCamera.value.id, updateData)
      // 更新成功时，后端返回200状态码和摄像头数据
      if (response.status === 200 && response.data) {
        ElMessage.success('更新成功')
        dialogVisible.value = false
        await loadCameras()
      } else {
        ElMessage.error('更新失败')
      }
    }
  } catch (error) {
    console.error('保存摄像头失败:', error)
    ElMessage.error('保存失败')
  } finally {
    loading.value = false
  }
}

// 获取摄像头所属的分组
const getCameraGroups = (cameraId: number) => {
  return cameraGroups.value.filter(group => group.camera_ids.includes(cameraId))
}

// 表格选择变化
const handleSelectionChange = (selection: Camera[]) => {
  selectedCameras.value = selection
}

// 分组操作
const handleGroupAction = (command: string, camera: Camera) => {
  operatingCameras.value = [camera]
  if (command === 'assign') {
    groupDialogMode.value = 'assign'
    groupDialogTitle.value = '分配摄像头到分组'
    groupDialogVisible.value = true
  } else if (command === 'remove') {
    groupDialogMode.value = 'remove'
    groupDialogTitle.value = '移出摄像头分组'
    groupDialogVisible.value = true
  }
}

// 批量分组操作
const handleBatchGroup = () => {
  if (selectedCameras.value.length === 0) {
    ElMessage.warning('请先选择要操作的摄像头')
    return
  }
  operatingCameras.value = [...selectedCameras.value]
  groupDialogMode.value = 'batch'
  groupDialogTitle.value = '批量分配摄像头到分组'
  groupDialogVisible.value = true
}

// 执行分组操作
const handleGroupOperation = async () => {
  if (!selectedGroupId.value) {
    ElMessage.warning('请选择分组')
    return
  }

  try {
    loading.value = true
    const groupId = selectedGroupId.value
    const group = cameraGroups.value.find(g => g.id === groupId)
    
    if (!group) {
      ElMessage.error('分组不存在')
      return
    }

    let newCameraIds = [...group.camera_ids]
    const operatingCameraIds = operatingCameras.value.map(c => c.id)

    if (groupDialogMode.value === 'assign' || groupDialogMode.value === 'batch') {
      // 添加摄像头到分组
      operatingCameraIds.forEach(id => {
        if (!newCameraIds.includes(id)) {
          newCameraIds.push(id)
        }
      })
    } else if (groupDialogMode.value === 'remove') {
      // 从分组中移除摄像头
      newCameraIds = newCameraIds.filter(id => !operatingCameraIds.includes(id))
    }

    await updateGroup(groupId, { camera_ids: newCameraIds })
    
    ElMessage.success('操作成功')
    groupDialogVisible.value = false
    selectedGroupId.value = null
    operatingCameras.value = []
    
    // 重新加载数据
    await loadCameraGroups()
  } catch (error) {
    console.error('分组操作失败:', error)
    ElMessage.error('操作失败')
  } finally {
    loading.value = false
  }
}

// 预览摄像头
const handlePreview = async (camera: Camera) => {
  if (camera.status !== 'online') {
    ElMessage.warning('摄像头离线，无法预览')
    return
  }
  
  try {
    const response = await cameraApi.getPreview(camera.id)
    console.log('Preview API response:', response) // 添加调试日志
    previewCamera.value = camera
    // 检查响应数据结构
    const previewData = response.data || response
    previewUrl.value = previewData.preview_url
    console.log('Preview URL:', previewUrl.value) // 添加调试日志
    previewDialogVisible.value = true
  } catch (error: any) {
    console.error('Preview error:', error) // 添加错误日志
    ElMessage.error(error.response?.data?.detail || '获取预览地址失败')
  }
}



// 关闭预览对话框
const handleClosePreview = () => {
  previewDialogVisible.value = false
  previewCamera.value = null
  previewUrl.value = ''
}

// 处理视频播放错误
const handleVideoError = (error: any) => {
  console.error('视频播放错误:', error)
  ElMessage.error('视频播放失败，预览窗口将自动关闭')
  // 延迟关闭对话框，让用户看到错误信息
  setTimeout(() => {
    handleClosePreview()
  }, 2000)
}

// 处理视频加载成功
const handleVideoLoaded = () => {
  console.log('视频加载成功')
}

// 多屏预览相关函数
// 打开多屏预览
const handleMultiPreview = () => {
  if (onlineCameras.value.length === 0) {
    ElMessage.warning('没有在线的摄像头可供预览')
    return
  }
  
  // 初始化网格槽位
  initializeGridSlots()
  
  // 自动选择前几个在线摄像头
  const autoSelectCount = Math.min(gridLayout.value, onlineCameras.value.length)
  selectedCameraIds.value = onlineCameras.value.slice(0, autoSelectCount).map(c => c.id)
  
  // 加载选中摄像头的预览
  loadSelectedCameraPreviews()
  
  multiPreviewDialogVisible.value = true
}

// 初始化网格槽位
const initializeGridSlots = () => {
  gridSlots.value = Array(gridLayout.value).fill(null).map(() => ({
    camera: null,
    previewUrl: ''
  }))
}

// 处理布局变化
const handleLayoutChange = (newLayout: number) => {
  gridLayout.value = newLayout
  initializeGridSlots()
  
  // 如果选中的摄像头数量超过新布局的槽位数，截取前面的
  if (selectedCameraIds.value.length > newLayout) {
    selectedCameraIds.value = selectedCameraIds.value.slice(0, newLayout)
  }
  
  loadSelectedCameraPreviews()
}

// 处理摄像头选择变化
const handleCameraSelection = () => {
  loadSelectedCameraPreviews()
}

// 加载选中摄像头的预览
const loadSelectedCameraPreviews = async () => {
  // 清空所有槽位
  initializeGridSlots()
  
  // 为每个选中的摄像头加载预览
  for (let i = 0; i < selectedCameraIds.value.length && i < gridLayout.value; i++) {
    const cameraId = selectedCameraIds.value[i]
    const camera = onlineCameras.value.find(c => c.id === cameraId)
    
    if (camera) {
      try {
        const response = await cameraApi.getPreview(camera.id)
        const previewData = response.data || response
        
        gridSlots.value[i] = {
          camera: camera,
          previewUrl: previewData.preview_url
        }
      } catch (error) {
        console.error(`获取摄像头 ${camera.name} 预览失败:`, error)
        gridSlots.value[i] = {
          camera: camera,
          previewUrl: ''
        }
      }
    }
  }
}

// 从槽位移除摄像头
const removeCameraFromSlot = (slotIndex: number) => {
  const slot = gridSlots.value[slotIndex]
  if (slot.camera) {
    // 从选中列表中移除
    selectedCameraIds.value = selectedCameraIds.value.filter(id => id !== slot.camera!.id)
    
    // 清空槽位
    gridSlots.value[slotIndex] = {
      camera: null,
      previewUrl: ''
    }
  }
}

// 处理多屏视频错误
const handleMultiVideoError = (camera: Camera, slotIndex: number) => {
  console.error(`摄像头 ${camera.name} 视频播放错误`)
  ElMessage.error(`摄像头 ${camera.name} 视频播放失败`)
}

// 处理多屏视频加载成功
const handleMultiVideoLoaded = (camera: Camera, slotIndex: number) => {
  console.log(`摄像头 ${camera.name} 视频加载成功`)
}

// 关闭多屏预览
const handleCloseMultiPreview = () => {
  multiPreviewDialogVisible.value = false
  selectedCameraIds.value = []
  gridSlots.value = []
}

// 全屏显示
const handleFullscreen = () => {
  const element = document.querySelector('.multi-preview-dialog .el-dialog')
  if (element) {
    if (element.requestFullscreen) {
      element.requestFullscreen()
    }
  }
}

// 组件挂载时的操作
onMounted(async () => {
  await Promise.all([
    loadCameras(),
    loadMediaProxies(),
    loadCameraGroups()
  ])
})
</script>

<style scoped>
.camera-management {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h2 {
  margin: 0;
  color: #303133;
}

.search-bar {
  display: flex;
  align-items: center;
  margin-bottom: 20px;
}

.pagination {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}

.preview-container {
  width: 100%;
  height: 60vh;
  min-height: 400px;
  max-height: 600px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f5f5;
  border-radius: 8px;
  overflow: hidden;
}

.no-preview {
  text-align: center;
  color: #909399;
  padding: 40px;
}

.no-preview p {
  margin: 10px 0;
  font-size: 16px;
}

.text-gray-500 {
  color: #909399;
  font-size: 14px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .preview-container {
    height: 50vh;
    min-height: 300px;
  }
}

@media (max-width: 480px) {
  .preview-container {
    height: 40vh;
    min-height: 250px;
  }
}

/* 多屏预览样式 */
.header-buttons {
  display: flex;
  gap: 12px;
}

.multi-preview-dialog {
  .el-dialog {
    margin: 0;
    height: 100vh;
    max-height: none;
  }
  
  .el-dialog__body {
    padding: 10px 20px;
  }
}

.multi-preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 8px;
  flex-wrap: wrap;
  gap: 15px;
}

.layout-controls,
.camera-selector {
  display: flex;
  align-items: center;
  gap: 10px;
}

.layout-controls span,
.camera-selector span {
  font-weight: 500;
  color: #606266;
  white-space: nowrap;
}

.multi-preview-container {
  display: grid;
  gap: 8px;
  width: 100%;
  height: 70vh;
  min-height: 500px;
  background: #000;
  border-radius: 8px;
  padding: 8px;
}

/* 网格布局 */
.grid-1 {
  grid-template-columns: 1fr;
  grid-template-rows: 1fr;
}

.grid-4 {
  grid-template-columns: 1fr 1fr;
  grid-template-rows: 1fr 1fr;
}

.grid-9 {
  grid-template-columns: repeat(3, 1fr);
  grid-template-rows: repeat(3, 1fr);
}

.grid-16 {
  grid-template-columns: repeat(4, 1fr);
  grid-template-rows: repeat(4, 1fr);
}

.preview-slot {
  position: relative;
  background: #1a1a1a;
  border-radius: 6px;
  overflow: hidden;
  border: 2px solid transparent;
  transition: border-color 0.3s ease;
}

.preview-slot.has-video {
  border-color: #409eff;
}

.preview-slot:hover {
  border-color: #66b1ff;
}

.video-wrapper {
  position: relative;
  width: 100%;
  height: 100%;
}

.video-header {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  background: linear-gradient(to bottom, rgba(0,0,0,0.8), transparent);
  color: white;
  padding: 8px 12px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  z-index: 10;
}

.camera-name {
  font-size: 14px;
  font-weight: 500;
  text-shadow: 0 1px 2px rgba(0,0,0,0.5);
}

.multi-video-player {
  width: 100%;
  height: 100%;
}

.empty-slot {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #666;
  text-align: center;
}

.empty-slot p {
  margin: 8px 0;
  font-size: 14px;
}

.slot-number {
  font-size: 24px;
  font-weight: bold;
  color: #999;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .multi-preview-header {
    flex-direction: column;
    align-items: stretch;
  }
  
  .layout-controls,
  .camera-selector {
    justify-content: center;
  }
}

@media (max-width: 768px) {
  .multi-preview-container {
    height: 60vh;
    min-height: 400px;
  }
  
  .grid-16 {
    grid-template-columns: repeat(3, 1fr);
    grid-template-rows: repeat(3, 1fr);
  }
  
  .video-header {
    padding: 6px 8px;
  }
  
  .camera-name {
    font-size: 12px;
  }
}

@media (max-width: 480px) {
  .multi-preview-container {
    height: 50vh;
    min-height: 300px;
  }
  
  .grid-9,
  .grid-16 {
    grid-template-columns: 1fr 1fr;
    grid-template-rows: 1fr 1fr;
  }
}
</style>