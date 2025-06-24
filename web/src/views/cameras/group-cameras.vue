<template>
  <div class="group-cameras">
    <div class="page-header">
      <div class="header-left">
        <el-button @click="goBack" type="text">
          <el-icon><ArrowLeft /></el-icon>
          返回分组列表
        </el-button>
        <h2>{{ groupInfo?.name }} - 摄像头管理</h2>
      </div>
      <el-button type="primary" @click="handleAddCamera">
        <el-icon><Plus /></el-icon>
        添加摄像头
      </el-button>
    </div>

    <div class="group-info">
      <el-descriptions :column="3" border>
        <el-descriptions-item label="分组名称">{{ groupInfo?.name }}</el-descriptions-item>
        <el-descriptions-item label="分组描述">{{ groupInfo?.description || '无' }}</el-descriptions-item>
        <el-descriptions-item label="摄像头数量">{{ groupInfo?.camera_count }}</el-descriptions-item>
      </el-descriptions>
    </div>

    <div class="search-bar">
      <el-input
        v-model="searchText"
        placeholder="搜索摄像头名称或位置"
        style="width: 300px; margin-right: 16px"
        clearable
        @input="handleSearch"
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>
      <el-button @click="handleRefresh">
        <el-icon><Refresh /></el-icon>
        刷新
      </el-button>
      <el-button 
        type="danger" 
        @click="handleBatchRemove" 
        :disabled="selectedCameras.length === 0"
      >
        批量移除
      </el-button>
    </div>

    <el-table 
      :data="cameras" 
      v-loading="loading" 
      style="width: 100%"
      @selection-change="handleSelectionChange"
    >
      <el-table-column type="selection" width="55" />
      <el-table-column prop="name" label="摄像头名称" width="200" />
      <el-table-column prop="ip_address" label="IP地址" width="150" />
      <el-table-column prop="location" label="位置" width="200" />
      <el-table-column prop="camera_type" label="类型" width="120">
        <template #default="{ row }">
          <el-tag>{{ row.camera_type }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="row.status === 'online' ? 'success' : 'danger'">
            {{ row.status === 'online' ? '在线' : '离线' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="is_active" label="启用状态" width="100">
        <template #default="{ row }">
          <el-tag :type="row.is_active ? 'success' : 'info'">
            {{ row.is_active ? '启用' : '禁用' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <el-button size="small" type="primary" @click="handleViewCamera(row)">查看</el-button>
          <el-button size="small" type="danger" @click="handleRemoveCamera(row)">移除</el-button>
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

    <!-- 添加摄像头对话框 -->
    <el-dialog
      v-model="addCameraDialogVisible"
      title="添加摄像头到分组"
      width="600px"
    >
      <el-form :model="addCameraForm" label-width="100px">
        <el-form-item label="选择摄像头">
          <el-select
            v-model="addCameraForm.camera_ids"
            multiple
            placeholder="请选择要添加的摄像头"
            style="width: 100%"
            filterable
          >
            <el-option
              v-for="camera in availableCameras"
              :key="camera.id"
              :label="`${camera.name} (${camera.location})`"
              :value="camera.id"
            />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="addCameraDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleConfirmAddCamera">确定</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft, Plus, Search, Refresh } from '@element-plus/icons-vue'
import { getGroupCameras, updateGroup } from '@/api/groups'
import { cameraApi } from '@/api/cameras'
import type { CameraGroup } from '@/api/groups'

interface Camera {
  id: number
  name: string
  ip_address: string
  location: string
  camera_type: string
  status: string
  is_active: boolean
}

const route = useRoute()
const router = useRouter()

const loading = ref(false)
const searchText = ref('')
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)
const addCameraDialogVisible = ref(false)

const groupId = ref<number>(parseInt(route.params.id as string))
const groupInfo = ref<CameraGroup | null>(null)
const cameras = ref<Camera[]>([])
const availableCameras = ref<Camera[]>([])
const selectedCameras = ref<Camera[]>([])

const addCameraForm = ref({
  camera_ids: [] as number[]
})

// 加载分组摄像头列表
const loadGroupCameras = async () => {
  loading.value = true
  try {
    const response = await getGroupCameras(groupId.value, currentPage.value, pageSize.value)
    if (response.status === 200 && response.data) {
      cameras.value = response.data.cameras
      total.value = response.data.total
    } else {
      ElMessage.error('获取分组摄像头列表失败')
    }
  } catch (error) {
    console.error('获取分组摄像头列表错误:', error)
    ElMessage.error('获取分组摄像头列表失败')
  } finally {
    loading.value = false
  }
}

// 加载可用摄像头列表
const loadAvailableCameras = async () => {
  try {
    // 由于后端限制page_size最大为100，需要分页加载所有摄像头
    let allCameras: Camera[] = []
    let currentPage = 1
    let hasMore = true
    
    while (hasMore) {
      const response = await cameraApi.getCameras({ page: currentPage, page_size: 100 })
      if (response.data && response.data.cameras) {
        allCameras = [...allCameras, ...response.data.cameras]
        hasMore = response.data.cameras.length === 100
        currentPage++
      } else {
        hasMore = false
      }
    }
    
    // 过滤掉已经在当前分组中的摄像头
    const currentCameraIds = cameras.value.map(c => c.id)
    availableCameras.value = allCameras.filter(
      (camera: Camera) => !currentCameraIds.includes(camera.id)
    )
  } catch (error) {
    console.error('获取可用摄像头列表错误:', error)
  }
}

const goBack = () => {
  router.push('/cameras/groups')
}

const handleAddCamera = async () => {
  await loadAvailableCameras()
  addCameraForm.value.camera_ids = []
  addCameraDialogVisible.value = true
}

const handleConfirmAddCamera = async () => {
  if (addCameraForm.value.camera_ids.length === 0) {
    ElMessage.warning('请选择要添加的摄像头')
    return
  }

  try {
    // 获取当前分组的摄像头ID列表
    const currentCameraIds = cameras.value.map(c => c.id)
    const newCameraIds = [...currentCameraIds, ...addCameraForm.value.camera_ids]
    
    const response = await updateGroup(groupId.value, {
      camera_ids: newCameraIds
    })
    
    if (response.status === 200) {
      ElMessage.success('添加摄像头成功')
      addCameraDialogVisible.value = false
      await loadGroupCameras()
    } else {
      ElMessage.error('添加摄像头失败')
    }
  } catch (error) {
    console.error('添加摄像头错误:', error)
    ElMessage.error('添加摄像头失败')
  }
}

const handleRemoveCamera = async (camera: Camera) => {
  try {
    await ElMessageBox.confirm(
      `确定要从分组中移除摄像头 "${camera.name}" 吗？`,
      '确认移除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    // 从分组中移除摄像头
    const currentCameraIds = cameras.value.map(c => c.id)
    const newCameraIds = currentCameraIds.filter(id => id !== camera.id)
    
    const response = await updateGroup(groupId.value, {
      camera_ids: newCameraIds
    })
    
    if (response.status === 200) {
      ElMessage.success('移除摄像头成功')
      await loadGroupCameras()
    } else {
      ElMessage.error('移除摄像头失败')
    }
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('移除摄像头错误:', error)
      ElMessage.error('移除摄像头失败')
    }
  }
}

const handleViewCamera = (camera: Camera) => {
  // 跳转到摄像头详情页面
  ElMessage.info(`查看摄像头 "${camera.name}" 详情功能待实现`)
}

const handleSearch = () => {
  // 搜索逻辑可以在这里实现
}

const handleRefresh = async () => {
  await loadGroupCameras()
  ElMessage.success('刷新成功')
}

const handleSizeChange = (size: number) => {
  pageSize.value = size
  currentPage.value = 1
  loadGroupCameras()
}

const handleCurrentChange = (page: number) => {
  currentPage.value = page
  loadGroupCameras()
}

// 表格选择变化
const handleSelectionChange = (selection: Camera[]) => {
  selectedCameras.value = selection
}

// 批量移除摄像头
const handleBatchRemove = async () => {
  if (selectedCameras.value.length === 0) {
    ElMessage.warning('请先选择要移除的摄像头')
    return
  }

  try {
    await ElMessageBox.confirm(
      `确定要从分组中移除选中的 ${selectedCameras.value.length} 个摄像头吗？`,
      '确认批量移除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    // 从分组中移除选中的摄像头
    const currentCameraIds = cameras.value.map(c => c.id)
    const selectedCameraIds = selectedCameras.value.map(c => c.id)
    const newCameraIds = currentCameraIds.filter(id => !selectedCameraIds.includes(id))
    
    const response = await updateGroup(groupId.value, {
      camera_ids: newCameraIds
    })
    
    if (response.status === 200) {
      ElMessage.success(`成功移除 ${selectedCameras.value.length} 个摄像头`)
      selectedCameras.value = []
      await loadGroupCameras()
    } else {
      ElMessage.error('批量移除摄像头失败')
    }
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('批量移除摄像头错误:', error)
      ElMessage.error('批量移除摄像头失败')
    }
  }
}

onMounted(() => {
  loadGroupCameras()
})
</script>

<style scoped>
.group-cameras {
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

.group-info {
  margin-bottom: 20px;
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

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
</style>