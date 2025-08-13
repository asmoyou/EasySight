<template>
  <div class="roles-container">
    <!-- 页面标题 -->
    <div class="page-header">
      <h2>角色管理</h2>
      <p>管理系统角色和权限配置</p>
    </div>

    <!-- 操作栏 -->
    <div class="toolbar">
      <div class="toolbar-left">
        <el-button type="primary" @click="showCreateDialog" :icon="Plus">
          新建角色
        </el-button>
        <el-button 
          type="danger" 
          :disabled="selectedRoles.length === 0"
          @click="handleBatchDelete"
          :icon="Delete"
        >
          批量删除
        </el-button>
      </div>
      <div class="toolbar-right">
        <el-input
          v-model="searchQuery"
          placeholder="搜索角色名称或描述"
          style="width: 300px"
          :prefix-icon="Search"
          @input="handleSearch"
          clearable
        />
        <el-select v-model="statusFilter" placeholder="状态筛选" style="width: 120px; margin-left: 10px">
          <el-option label="全部" :value="null" />
          <el-option label="启用" :value="true" />
          <el-option label="禁用" :value="false" />
        </el-select>
      </div>
    </div>

    <!-- 角色列表 -->
    <div class="table-container">
      <el-table
        :data="roleList"
        v-loading="loading"
        @selection-change="handleSelectionChange"
        stripe
        style="width: 100%"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column prop="display_name" label="角色名称" min-width="150">
          <template #default="{ row }">
            <div class="role-info">
              <div class="role-name">{{ row.display_name }}</div>
              <div class="role-code">{{ row.name }}</div>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
        <el-table-column label="权限数量" width="100" align="center">
          <template #default="{ row }">
            <el-tag size="small">{{ row.permissions?.length || 0 }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="用户数量" width="100" align="center">
          <template #default="{ row }">
            <el-tag type="info" size="small">{{ row.user_count || 0 }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'danger'" size="small">
              {{ row.is_active ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="系统角色" width="100" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.is_system" type="warning" size="small">系统</el-tag>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="140" fixed="right">
          <template #default="{ row }">
            <div class="action-buttons">
              <el-button-group>
                <el-button 
                  size="small" 
                  @click="showEditDialog(row)" 
                  title="编辑角色"
                >
                  <el-icon><Edit /></el-icon>
                </el-button>
                <el-button 
                  size="small" 
                  @click="showPermissionDialog(row)" 
                  title="权限设置"
                >
                  <el-icon><Key /></el-icon>
                </el-button>
              </el-button-group>
              <el-dropdown @command="(command) => handleDropdownCommand(command, row)" trigger="click">
                <el-button size="small" title="更多操作">
                  <el-icon><MoreFilled /></el-icon>
                </el-button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item 
                      command="delete" 
                      :disabled="row.is_system"
                      class="danger-item"
                    >
                      <el-icon><Delete /></el-icon>
                      删除
                    </el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 分页 -->
    <div class="pagination-container">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :total="total"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="fetchRoleList"
        @current-change="fetchRoleList"
      />
    </div>

    <!-- 创建/编辑角色对话框 -->
    <el-dialog
      v-model="roleDialogVisible"
      :title="isEdit ? '编辑角色' : '创建角色'"
      width="600px"
      @close="resetRoleForm"
    >
      <el-form
        ref="roleFormRef"
        :model="roleForm"
        :rules="roleFormRules"
        label-width="100px"
      >
        <el-form-item label="角色标识" prop="name">
          <el-input 
            v-model="roleForm.name" 
            placeholder="请输入角色标识，如：operator"
            :disabled="isEdit"
          />
          <div class="form-tip">角色标识用于系统内部识别，创建后不可修改</div>
        </el-form-item>
        <el-form-item label="角色名称" prop="display_name">
          <el-input v-model="roleForm.display_name" placeholder="请输入角色显示名称" />
        </el-form-item>
        <el-form-item label="角色描述" prop="description">
          <el-input
            v-model="roleForm.description"
            type="textarea"
            :rows="3"
            placeholder="请输入角色描述"
          />
        </el-form-item>
        <el-form-item label="状态" prop="is_active" v-if="isEdit">
          <el-switch v-model="roleForm.is_active" active-text="启用" inactive-text="禁用" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="roleDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleRoleSubmit" :loading="submitting">
          {{ isEdit ? '更新' : '创建' }}
        </el-button>
      </template>
    </el-dialog>

    <!-- 权限配置对话框 -->
    <el-dialog
      v-model="permissionDialogVisible"
      title="权限配置"
      width="800px"
      @close="resetPermissionForm"
    >
      <div class="permission-config">
        <div class="permission-tabs">
          <el-tabs v-model="activePermissionTab">
            <el-tab-pane label="功能权限" name="function">
              <div class="permission-section">
                <h4>功能权限配置</h4>
                <div class="permission-tree">
                  <el-tree
                    ref="permissionTreeRef"
                    :data="permissionTreeData"
                    :props="treeProps"
                    show-checkbox
                    node-key="name"
                    :default-checked-keys="selectedPermissions"
                    @check="handlePermissionCheck"
                  />
                </div>
              </div>
            </el-tab-pane>
            <el-tab-pane label="页面权限" name="page">
              <div class="page-permission-section">
                <h4>页面访问权限</h4>
                <div class="page-permission-list">
                  <div v-for="page in pagePermissions" :key="page.path" class="page-item">
                    <div class="page-info">
                      <div class="page-name">{{ page.name }}</div>
                      <div class="page-path">{{ page.path }}</div>
                    </div>
                    <div class="page-controls">
                      <el-switch
                        v-model="page.allowed"
                        active-text="允许访问"
                        inactive-text="禁止访问"
                        @change="handlePagePermissionChange"
                      />
                    </div>
                  </div>
                </div>
              </div>
            </el-tab-pane>
          </el-tabs>
        </div>
      </div>
      <template #footer>
        <el-button @click="permissionDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handlePermissionSubmit" :loading="submitting">
          保存权限
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed, watch, nextTick } from 'vue'
import { ElMessage, ElMessageBox, ElTree } from 'element-plus'
import { Plus, Delete, Edit, Key, Search, MoreFilled } from '@element-plus/icons-vue'
import type { FormInstance, FormRules } from 'element-plus'
import { rolesApi, type Role, type RoleCreate, type RoleUpdate, type Permission } from '@/api/roles'
import { formatDateTime } from '@/utils/date'

// 响应式数据
const loading = ref(false)
const submitting = ref(false)
const roleList = ref<Role[]>([])
const selectedRoles = ref<Role[]>([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)
const searchQuery = ref('')
const statusFilter = ref<boolean | null>(null)

// 对话框状态
const roleDialogVisible = ref(false)
const permissionDialogVisible = ref(false)
const isEdit = ref(false)
const activePermissionTab = ref('function')

// 表单引用
const roleFormRef = ref<FormInstance>()
const permissionTreeRef = ref<InstanceType<typeof ElTree>>()

// 角色表单
const roleForm = reactive<RoleCreate & { id?: number; is_active?: boolean }>({
  name: '',
  display_name: '',
  description: '',
  permissions: [],
  page_permissions: {}
})

// 表单验证规则
const roleFormRules: FormRules = {
  name: [
    { required: true, message: '请输入角色标识', trigger: 'blur' },
    { pattern: /^[a-zA-Z][a-zA-Z0-9_]*$/, message: '角色标识只能包含字母、数字和下划线，且以字母开头', trigger: 'blur' }
  ],
  display_name: [
    { required: true, message: '请输入角色名称', trigger: 'blur' }
  ]
}

// 权限相关数据
const permissionList = ref<Permission[]>([])
const selectedPermissions = ref<string[]>([])
const currentRole = ref<Role | null>(null)

// 权限树配置
const treeProps = {
  children: 'children',
  label: 'display_name',
  disabled: 'disabled'
}

// 权限树数据
const permissionTreeData = computed(() => {
  const tree: any[] = []
  const moduleMap = new Map()
  
  permissionList.value.forEach(permission => {
    const module = permission.module || '其他'
    if (!moduleMap.has(module)) {
      moduleMap.set(module, {
        name: module,
        display_name: module,
        children: []
      })
    }
    
    moduleMap.get(module).children.push({
      name: permission.name,
      display_name: permission.display_name,
      description: permission.description,
      disabled: permission.is_system
    })
  })
  
  return Array.from(moduleMap.values())
})

// 页面权限数据
const pagePermissions = ref([
  { path: '/dashboard', name: '仪表盘', allowed: true },
  { path: '/cameras', name: '摄像头管理', allowed: true },
  { path: '/ai', name: 'AI应用中心', allowed: true },
  { path: '/events', name: '事件告警中心', allowed: true },
  { path: '/diagnosis', name: '智能诊断', allowed: true },
  { path: '/system', name: '系统配置', allowed: false }
])

// 方法
const fetchRoleList = async () => {
  try {
    loading.value = true
    const params = {
      page: currentPage.value,
      page_size: pageSize.value,
      search: searchQuery.value || undefined,
      is_active: statusFilter.value
    }
    
    const response = await rolesApi.getRoleList(params)
    roleList.value = response.data.data
    total.value = response.data.total
  } catch (error) {
    console.error('获取角色列表失败:', error)
    ElMessage.error('获取角色列表失败')
  } finally {
    loading.value = false
  }
}

const fetchPermissions = async () => {
  try {
    const response = await rolesApi.getPermissions()
    permissionList.value = response.data
  } catch (error) {
    console.error('获取权限列表失败:', error)
  }
}

const handleSearch = () => {
  currentPage.value = 1
  fetchRoleList()
}

const handleSelectionChange = (selection: Role[]) => {
  selectedRoles.value = selection
}

const showCreateDialog = () => {
  isEdit.value = false
  roleDialogVisible.value = true
}

const showEditDialog = (role: Role) => {
  isEdit.value = true
  Object.assign(roleForm, {
    id: role.id,
    name: role.name,
    display_name: role.display_name,
    description: role.description,
    permissions: role.permissions,
    page_permissions: role.page_permissions,
    is_active: role.is_active
  })
  roleDialogVisible.value = true
}

const showPermissionDialog = async (role: Role) => {
  currentRole.value = role
  selectedPermissions.value = role.permissions || []
  
  // 设置页面权限
  const pagePerms = role.page_permissions || {}
  pagePermissions.value.forEach(page => {
    page.allowed = pagePerms[page.path] !== false
  })
  
  permissionDialogVisible.value = true
  
  // 等待DOM更新后设置权限树选中状态
  await nextTick()
  if (permissionTreeRef.value) {
    permissionTreeRef.value.setCheckedKeys(selectedPermissions.value)
  }
}

const resetRoleForm = () => {
  Object.assign(roleForm, {
    name: '',
    display_name: '',
    description: '',
    permissions: [],
    page_permissions: {}
  })
  roleFormRef.value?.resetFields()
}

const resetPermissionForm = () => {
  selectedPermissions.value = []
  currentRole.value = null
  activePermissionTab.value = 'function'
}

const handleRoleSubmit = async () => {
  if (!roleFormRef.value) return
  
  try {
    await roleFormRef.value.validate()
    submitting.value = true
    
    if (isEdit.value && roleForm.id) {
      const updateData: RoleUpdate = {
        display_name: roleForm.display_name,
        description: roleForm.description,
        is_active: roleForm.is_active
      }
      await rolesApi.updateRole(roleForm.id, updateData)
      ElMessage.success('角色更新成功')
    } else {
      const createData: RoleCreate = {
        name: roleForm.name,
        display_name: roleForm.display_name,
        description: roleForm.description,
        permissions: [],
        page_permissions: {}
      }
      await rolesApi.createRole(createData)
      ElMessage.success('角色创建成功')
    }
    
    roleDialogVisible.value = false
    fetchRoleList()
  } catch (error) {
    console.error('角色操作失败:', error)
    ElMessage.error('角色操作失败')
  } finally {
    submitting.value = false
  }
}

const handlePermissionCheck = () => {
  if (permissionTreeRef.value) {
    selectedPermissions.value = permissionTreeRef.value.getCheckedKeys() as string[]
  }
}

const handlePagePermissionChange = () => {
  // 页面权限变更处理
}

const handlePermissionSubmit = async () => {
  if (!currentRole.value) return
  
  try {
    submitting.value = true
    
    // 构建页面权限配置
    const pagePerms: Record<string, boolean> = {}
    pagePermissions.value.forEach(page => {
      pagePerms[page.path] = page.allowed
    })
    
    const updateData: RoleUpdate = {
      permissions: selectedPermissions.value,
      page_permissions: pagePerms
    }
    
    await rolesApi.updateRole(currentRole.value.id, updateData)
    ElMessage.success('权限配置保存成功')
    permissionDialogVisible.value = false
    fetchRoleList()
  } catch (error) {
    console.error('权限配置失败:', error)
    ElMessage.error('权限配置失败')
  } finally {
    submitting.value = false
  }
}

const handleDelete = async (role: Role) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除角色 "${role.display_name}" 吗？此操作不可恢复。`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await rolesApi.deleteRole(role.id)
    ElMessage.success('角色删除成功')
    fetchRoleList()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除角色失败:', error)
      ElMessage.error('删除角色失败')
    }
  }
}

// 下拉菜单处理
const handleDropdownCommand = (command: string, role: Role) => {
  if (command === 'delete') {
    handleDelete(role)
  }
}

const handleBatchDelete = async () => {
  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${selectedRoles.value.length} 个角色吗？此操作不可恢复。`,
      '确认批量删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    const roleIds = selectedRoles.value.map(role => role.id)
    await rolesApi.batchDeleteRoles(roleIds)
    ElMessage.success('批量删除成功')
    fetchRoleList()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('批量删除失败:', error)
      ElMessage.error('批量删除失败')
    }
  }
}

// 监听状态筛选变化
watch(statusFilter, () => {
  currentPage.value = 1
  fetchRoleList()
})

// 初始化
onMounted(() => {
  fetchRoleList()
  fetchPermissions()
})
</script>

<style scoped lang="scss">
.roles-container {
  padding: 20px;
  
  .page-header {
    margin-bottom: 20px;
    
    h2 {
      margin: 0 0 8px 0;
      color: #303133;
      font-size: 24px;
      font-weight: 600;
    }
    
    p {
      margin: 0;
      color: #606266;
      font-size: 14px;
    }
  }
  
  .toolbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    padding: 16px;
    background: #fff;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    
    .toolbar-left {
      display: flex;
      gap: 12px;
    }
    
    .toolbar-right {
      display: flex;
      align-items: center;
    }
  }
  
  .table-container {
    background: #fff;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    overflow: hidden;
    
    .role-info {
      .role-name {
        font-weight: 500;
        color: #303133;
      }
      
      .role-code {
        font-size: 12px;
        color: #909399;
        margin-top: 2px;
      }
    }
  }
  
  .pagination-container {
    display: flex;
    justify-content: center;
    margin-top: 20px;
  }
  
  .form-tip {
    font-size: 12px;
    color: #909399;
    margin-top: 4px;
  }
  
  .permission-config {
    .permission-section {
      h4 {
        margin: 0 0 16px 0;
        color: #303133;
        font-size: 16px;
        font-weight: 500;
      }
      
      .permission-tree {
        max-height: 400px;
        overflow-y: auto;
        border: 1px solid #dcdfe6;
        border-radius: 4px;
        padding: 12px;
      }
    }
    
    .page-permission-section {
      h4 {
        margin: 0 0 16px 0;
        color: #303133;
        font-size: 16px;
        font-weight: 500;
      }
      
      .page-permission-list {
        max-height: 400px;
        overflow-y: auto;
        
        .page-item {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 12px 16px;
          border: 1px solid #ebeef5;
          border-radius: 4px;
          margin-bottom: 8px;
          
          &:last-child {
            margin-bottom: 0;
          }
          
          .page-info {
            .page-name {
              font-weight: 500;
              color: #303133;
            }
            
            .page-path {
              font-size: 12px;
              color: #909399;
              margin-top: 2px;
            }
          }
        }
      }
    }
  }
  
  .action-buttons {
    display: flex;
    align-items: center;
    gap: 8px;
  }
  
  .action-buttons .el-button-group {
    margin-right: 0;
  }
  
  .action-buttons .el-button {
    padding: 5px 8px;
  }
  
  .action-buttons .el-dropdown .el-button {
    padding: 5px 8px;
    min-width: 28px;
  }
  
  /* 操作按钮颜色样式 */
  .action-buttons .el-button-group .el-button:first-child {
    color: #409eff;
    border-color: #c6e2ff;
    background-color: #ecf5ff;
  }
  
  .action-buttons .el-button-group .el-button:first-child:hover {
    color: #fff;
    background-color: #409eff;
    border-color: #409eff;
  }
  
  .action-buttons .el-button-group .el-button:last-child {
    color: #e6a23c;
    border-color: #f5dab1;
    background-color: #fdf6ec;
  }
  
  .action-buttons .el-button-group .el-button:last-child:hover {
    color: #fff;
    background-color: #e6a23c;
    border-color: #e6a23c;
  }
  
  .action-buttons .el-dropdown .el-button {
    color: #909399;
    border-color: #dcdfe6;
    background-color: #f5f7fa;
    padding: 5px 8px;
    min-width: 28px;
  }
  
  .action-buttons .el-dropdown .el-button:hover {
    color: #409eff;
    border-color: #c6e2ff;
    background-color: #ecf5ff;
  }
  
  /* 删除按钮危险样式 */
   .el-dropdown-menu .danger-item {
     color: #f56c6c !important;
   }
   
   .el-dropdown-menu .danger-item:hover {
     background-color: #fef0f0 !important;
     color: #f56c6c !important;
   }
   
   .el-dropdown-menu .danger-item .el-icon {
     color: #f56c6c !important;
   }
   
   .el-dropdown-menu .danger-item span {
     color: #f56c6c !important;
   }
}
</style>