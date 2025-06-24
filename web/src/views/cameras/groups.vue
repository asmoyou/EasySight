<template>
  <div class="camera-groups">
    <div class="page-header">
      <h2>摄像头分组管理</h2>
      <el-button type="primary" @click="handleAddGroup">
        <el-icon><Plus /></el-icon>
        新建分组
      </el-button>
    </div>

    <div class="search-bar">
      <el-input
        v-model="searchText"
        placeholder="搜索分组名称"
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
    </div>

    <el-table :data="filteredGroups" v-loading="loading" style="width: 100%">
      <el-table-column prop="name" label="分组名称" width="200" />
      <el-table-column prop="description" label="描述" width="300" />
      <el-table-column prop="camera_count" label="摄像头数量" width="120">
        <template #default="{ row }">
          <el-tag>{{ row.camera_count || 0 }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="关联摄像头" min-width="200">
        <template #default="{ row }">
          <div v-if="row.camera_count > 0">
            <el-tag
              v-for="camera in getCamerasByGroupId(row.id).slice(0, 3)"
              :key="camera.id"
              size="small"
              style="margin-right: 4px; margin-bottom: 4px"
            >
              {{ camera.name }}
            </el-tag>
            <el-tag
              v-if="row.camera_count > 3"
              size="small"
              type="info"
            >
              +{{ row.camera_count - 3 }}个
            </el-tag>
          </div>
          <span v-else class="text-gray-400">暂无摄像头</span>
        </template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="row.status === 'active' ? 'success' : 'info'">
            {{ row.status === 'active' ? '启用' : '禁用' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="180">
        <template #default="{ row }">
          {{ formatDate(row.created_at) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="250" fixed="right">
        <template #default="{ row }">
          <el-button size="small" @click="handleViewCameras(row)">查看摄像头</el-button>
          <el-button size="small" type="primary" @click="handleEdit(row)">编辑</el-button>
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

    <!-- 新建/编辑分组对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑分组' : '新建分组'"
      width="500px"
    >
      <el-form :model="groupForm" :rules="rules" ref="formRef" label-width="80px">
        <el-form-item label="分组名称" prop="name">
          <el-input v-model="groupForm.name" placeholder="请输入分组名称" />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input
            v-model="groupForm.description"
            type="textarea"
            :rows="3"
            placeholder="请输入分组描述"
          />
        </el-form-item>
        <el-form-item label="状态" prop="status">
          <el-radio-group v-model="groupForm.status">
            <el-radio label="active">启用</el-radio>
            <el-radio label="inactive">禁用</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleSubmit">确定</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, Refresh } from '@element-plus/icons-vue'
import type { FormInstance, FormRules } from 'element-plus'
import { getGroups, createGroup, updateGroup, deleteGroup, getGroupCameras } from '@/api/groups'
import { cameraApi } from '@/api/cameras'
import type { CameraGroup, GroupForm } from '@/api/groups'
import type { Camera } from '@/types/camera'

const router = useRouter()

interface ExtendedCameraGroup extends CameraGroup {
  status?: 'active' | 'inactive'
}

interface ExtendedGroupForm extends GroupForm {
  status?: 'active' | 'inactive'
}

const loading = ref(false)
const searchText = ref('')
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)
const dialogVisible = ref(false)
const isEdit = ref(false)
const editingGroupId = ref<number | null>(null)
const formRef = ref<FormInstance>()

const groupForm = ref<ExtendedGroupForm>({
  name: '',
  description: '',
  status: 'active'
})

const rules: FormRules = {
  name: [
    { required: true, message: '请输入分组名称', trigger: 'blur' },
    { min: 2, max: 50, message: '长度在 2 到 50 个字符', trigger: 'blur' }
  ],
  description: [
    { max: 200, message: '描述不能超过 200 个字符', trigger: 'blur' }
  ]
}

// 分组数据和摄像头数据
const groups = ref<ExtendedCameraGroup[]>([])
const cameras = ref<Camera[]>([])

// 加载摄像头列表
const loadCameras = async () => {
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
    
    cameras.value = allCameras
  } catch (error) {
    console.error('加载摄像头列表失败:', error)
  }
}

// 加载分组列表
const loadGroups = async () => {
  loading.value = true
  try {
    const response = await getGroups()
    if (response.status === 200 && response.data) {
      groups.value = response.data.map((group: CameraGroup) => ({
        ...group,
        status: 'active' // 后端没有status字段，前端默认为active
      }))
      total.value = groups.value.length
    } else {
      ElMessage.error('获取分组列表失败')
    }
  } catch (error) {
    console.error('获取分组列表错误:', error)
    ElMessage.error('获取分组列表失败')
  } finally {
    loading.value = false
  }
}

// 根据分组ID获取关联的摄像头
const getCamerasByGroupId = (groupId: number) => {
  const group = groups.value.find(g => g.id === groupId)
  if (!group || !group.camera_ids) return []
  
  return cameras.value.filter(camera => group.camera_ids.includes(camera.id))
}

const filteredGroups = computed(() => {
  let result = groups.value
  
  if (searchText.value) {
    result = result.filter(group => 
      group.name.includes(searchText.value) || 
      (group.description && group.description.includes(searchText.value))
    )
  }
  
  return result
})

const formatDate = (dateStr: string) => {
  return new Date(dateStr).toLocaleString('zh-CN')
}

const handleAddGroup = () => {
  isEdit.value = false
  editingGroupId.value = null
  groupForm.value = {
    name: '',
    description: '',
    status: 'active'
  }
  dialogVisible.value = true
}

const handleEdit = (group: ExtendedCameraGroup) => {
  isEdit.value = true
  editingGroupId.value = group.id
  groupForm.value = {
    name: group.name,
    description: group.description || '',
    status: group.status || 'active'
  }
  dialogVisible.value = true
}

const handleDelete = async (group: ExtendedCameraGroup) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除分组 "${group.name}" 吗？删除后该分组下的摄像头将移至默认分组。`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    const response = await deleteGroup(group.id)
    if (response.status === 200) {
      ElMessage.success('删除成功')
      await loadGroups() // 重新加载分组列表
    } else {
      ElMessage.error('删除失败')
    }
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('删除分组错误:', error)
      ElMessage.error('删除失败')
    }
  }
}

const handleViewCameras = (group: ExtendedCameraGroup) => {
  // 跳转到分组摄像头管理页面
  router.push(`/cameras/groups/${group.id}/cameras`)
}

const handleSubmit = async () => {
  if (!formRef.value) return
  
  try {
    await formRef.value.validate()
    
    const submitData = {
      name: groupForm.value.name,
      description: groupForm.value.description || undefined,
      camera_ids: [] // 创建时默认为空数组
    }
    
    if (isEdit.value && editingGroupId.value) {
      const response = await updateGroup(editingGroupId.value, submitData)
      if (response.status === 200) {
        ElMessage.success('编辑成功')
        await loadGroups() // 重新加载分组列表
      } else {
        ElMessage.error('编辑失败')
      }
    } else {
      const response = await createGroup(submitData)
      if (response.status === 200) {
        ElMessage.success('创建成功')
        await loadGroups() // 重新加载分组列表
      } else {
        ElMessage.error('创建失败')
      }
    }
    
    dialogVisible.value = false
  } catch (error) {
    console.error('提交表单错误:', error)
    ElMessage.error('操作失败，请检查表单输入')
  }
}

const handleSearch = () => {
  // 搜索逻辑已在computed中处理
}

const handleRefresh = async () => {
  await loadGroups()
  ElMessage.success('刷新成功')
}

const handleSizeChange = (size: number) => {
  pageSize.value = size
  currentPage.value = 1
}

const handleCurrentChange = (page: number) => {
  currentPage.value = page
}

onMounted(async () => {
  await Promise.all([
    loadGroups(),
    loadCameras()
  ])
})
</script>

<style scoped>
.camera-groups {
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

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
</style>