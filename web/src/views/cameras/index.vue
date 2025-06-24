<template>
  <div class="camera-management">
    <div class="page-header">
      <h2>摄像头管理</h2>
      <el-button type="primary" @click="handleAdd">
        <el-icon><Plus /></el-icon>
        添加摄像头
      </el-button>
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
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <el-button size="small" @click="handleView(row)">查看</el-button>
          <el-button size="small" type="primary" @click="handleEdit(row)">编辑</el-button>
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
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Refresh, Plus, View, Edit, Delete, ArrowDown } from '@element-plus/icons-vue'
import { cameraApi, mediaProxyApi } from '@/api/cameras'
import { getGroups, updateGroup } from '@/api/groups'
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
</style>