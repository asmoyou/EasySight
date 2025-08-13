<template>
  <div class="users-container">
    <!-- 页面标题和操作栏 -->
    <div class="page-header">
      <div class="header-left">
        <h2>用户管理</h2>
        <p class="page-description">管理系统用户账户、权限和状态</p>
      </div>
      <div class="header-right">
        <el-button type="primary" :icon="Plus" @click="showCreateDialog">
          新增用户
        </el-button>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-cards" v-if="userStats">
      <el-row :gutter="20">
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-content">
              <div class="stat-icon total">
                <el-icon><User /></el-icon>
              </div>
              <div class="stat-info">
                <div class="stat-value">{{ userStats.total_users }}</div>
                <div class="stat-label">总用户数</div>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-content">
              <div class="stat-icon active">
                <el-icon><Check /></el-icon>
              </div>
              <div class="stat-info">
                <div class="stat-value">{{ userStats.active_users }}</div>
                <div class="stat-label">活跃用户</div>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-content">
              <div class="stat-icon verified">
                <el-icon><CircleCheck /></el-icon>
              </div>
              <div class="stat-info">
                <div class="stat-value">{{ userStats.verified_users }}</div>
                <div class="stat-label">已验证用户</div>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-content">
              <div class="stat-icon recent">
                <el-icon><Clock /></el-icon>
              </div>
              <div class="stat-info">
                <div class="stat-value">{{ userStats.recent_logins }}</div>
                <div class="stat-label">近期登录</div>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 搜索和筛选 -->
    <el-card class="search-card">
      <el-form :model="searchForm" inline>
        <el-form-item label="搜索">
          <el-input
            v-model="searchForm.search"
            placeholder="用户名、邮箱或姓名"
            :prefix-icon="Search"
            clearable
            @clear="handleSearch"
            @keyup.enter="handleSearch"
            style="width: 250px"
          />
        </el-form-item>
        <el-form-item label="角色">
          <el-select v-model="searchForm.role" placeholder="选择角色" clearable style="width: 150px">
            <el-option 
              v-for="role in availableRoles" 
              :key="role.id" 
              :label="role.display_name" 
              :value="role.name" 
            />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="searchForm.is_active" placeholder="选择状态" clearable style="width: 120px">
            <el-option label="活跃" :value="true" />
            <el-option label="禁用" :value="false" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :icon="Search" @click="handleSearch">
            搜索
          </el-button>
          <el-button :icon="Refresh" @click="handleReset">
            重置
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 用户列表 -->
    <el-card class="table-card">
      <template #header>
        <div class="table-header">
          <span>用户列表</span>
          <div class="table-actions">
            <el-button
              type="danger"
              :icon="Delete"
              :disabled="selectedUsers.length === 0"
              @click="handleBatchDelete"
            >
              批量删除
            </el-button>
          </div>
        </div>
      </template>

      <el-table
        v-loading="loading"
        :data="userList"
        @selection-change="handleSelectionChange"
        stripe
        style="width: 100%"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column label="用户信息" min-width="200">
          <template #default="{ row }">
            <div class="user-info">
              <el-avatar :size="40" :src="row.avatar">
                <el-icon><User /></el-icon>
              </el-avatar>
              <div class="user-details">
                <div class="username">{{ row.username }}</div>
                <div class="email">{{ row.email }}</div>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="full_name" label="姓名" width="120" />
        <el-table-column prop="phone" label="电话" width="130" />
        <el-table-column label="角色" width="120">
          <template #default="{ row }">
            <el-tag
              v-for="role in row.roles"
              :key="role"
              :type="getRoleTagType(role)"
              size="small"
              style="margin-right: 4px"
            >
              {{ getRoleLabel(role) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'danger'" size="small">
              {{ row.is_active ? '活跃' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="验证状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_verified ? 'success' : 'warning'" size="small">
              {{ row.is_verified ? '已验证' : '未验证' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="login_count" label="登录次数" width="100" />
        <el-table-column prop="last_login" label="最后登录" width="160">
          <template #default="{ row }">
            {{ row.last_login ? formatDateTime(row.last_login) : '从未登录' }}
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="160">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="140" fixed="right">
          <template #default="{ row }">
            <div class="action-buttons">
              <el-button-group>
                <el-button 
                  type="primary" 
                  size="small" 
                  @click="showEditDialog(row)"
                  title="编辑用户"
                >
                  <el-icon><Edit /></el-icon>
                </el-button>
                <el-button 
                  type="warning" 
                  size="small" 
                  @click="showResetPasswordDialog(row)"
                  title="重置密码"
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
                      :disabled="row.id === currentUserId"
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

      <!-- 分页 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.page_size"
          :page-sizes="[10, 20, 50, 100]"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <!-- 创建/编辑用户对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogMode === 'create' ? '新增用户' : '编辑用户'"
      width="600px"
      @close="resetForm"
    >
      <el-form
        ref="userFormRef"
        :model="userForm"
        :rules="userFormRules"
        label-width="100px"
      >
        <el-form-item label="用户名" prop="username">
          <el-input
            v-model="userForm.username"
            placeholder="请输入用户名"
            :disabled="dialogMode === 'edit'"
          />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="userForm.email" placeholder="请输入邮箱" />
        </el-form-item>
        <el-form-item label="密码" prop="password" v-if="dialogMode === 'create'">
          <el-input
            v-model="userForm.password"
            type="password"
            placeholder="请输入密码"
            show-password
          />
        </el-form-item>
        <el-form-item label="姓名" prop="full_name">
          <el-input v-model="userForm.full_name" placeholder="请输入姓名" />
        </el-form-item>
        <el-form-item label="电话" prop="phone">
          <el-input v-model="userForm.phone" placeholder="请输入电话号码" />
        </el-form-item>
        <el-form-item label="角色" prop="roles">
          <el-select v-model="userForm.roles" multiple placeholder="选择角色" style="width: 100%">
            <el-option 
              v-for="role in availableRoles" 
              :key="role.id" 
              :label="role.display_name" 
              :value="role.name" 
            />
          </el-select>
        </el-form-item>
        <el-form-item label="语言" prop="language">
          <el-select v-model="userForm.language" placeholder="选择语言" style="width: 100%">
            <el-option label="中文" value="zh-CN" />
            <el-option label="English" value="en-US" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态" prop="is_active">
          <el-switch v-model="userForm.is_active" active-text="启用" inactive-text="禁用" />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input
            v-model="userForm.description"
            type="textarea"
            :rows="3"
            placeholder="请输入用户描述"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">
          {{ dialogMode === 'create' ? '创建' : '更新' }}
        </el-button>
      </template>
    </el-dialog>

    <!-- 重置密码对话框 -->
    <el-dialog v-model="resetPasswordVisible" title="重置密码" width="400px">
      <el-form ref="passwordFormRef" :model="passwordForm" :rules="passwordFormRules">
        <el-form-item label="新密码" prop="new_password">
          <el-input
            v-model="passwordForm.new_password"
            type="password"
            placeholder="请输入新密码"
            show-password
          />
        </el-form-item>
        <el-form-item label="确认密码" prop="confirm_password">
          <el-input
            v-model="passwordForm.confirm_password"
            type="password"
            placeholder="请确认新密码"
            show-password
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="resetPasswordVisible = false">取消</el-button>
        <el-button type="primary" @click="handleResetPassword" :loading="submitting">
          确认重置
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import {
  Plus,
  Search,
  Refresh,
  Edit,
  Delete,
  Key,
  User,
  Check,
  CircleCheck,
  Clock,
  MoreFilled
} from '@element-plus/icons-vue'
import { usersApi } from '@/api/users'
import { rolesApi } from '@/api/roles'
import { useUserStore } from '@/stores/user'
import type { User as UserType, UserCreateForm, UserUpdateForm, UserStats } from '@/types/user'
import type { Role } from '@/types/role'
import { formatDateTime } from '@/utils/date'

const userStore = useUserStore()

// 当前用户ID
const currentUserId = computed(() => userStore.user?.id)

// 数据状态
const loading = ref(false)
const submitting = ref(false)
const userList = ref<UserType[]>([])
const userStats = ref<UserStats | null>(null)
const selectedUsers = ref<UserType[]>([])
const availableRoles = ref<Role[]>([])

// 搜索表单
const searchForm = reactive({
  search: '',
  role: '',
  is_active: undefined as boolean | undefined
})

// 分页
const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0,
  total_pages: 0
})

// 对话框状态
const dialogVisible = ref(false)
const dialogMode = ref<'create' | 'edit'>('create')
const resetPasswordVisible = ref(false)
const currentEditUser = ref<UserType | null>(null)

// 表单引用
const userFormRef = ref<FormInstance>()
const passwordFormRef = ref<FormInstance>()

// 用户表单
const userForm = reactive<UserCreateForm & { id?: number }>({
  username: '',
  email: '',
  password: '',
  full_name: '',
  phone: '',
  roles: ['user'],
  permissions: [],
  language: 'zh-CN',
  is_active: true,
  description: ''
})

// 密码表单
const passwordForm = reactive({
  new_password: '',
  confirm_password: ''
})

// 表单验证规则
const userFormRules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 50, message: '用户名长度在 3 到 50 个字符', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度至少 6 个字符', trigger: 'blur' }
  ],
  roles: [
    { required: true, message: '请选择角色', trigger: 'change' }
  ]
}

const passwordFormRules: FormRules = {
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码长度至少 6 个字符', trigger: 'blur' }
  ],
  confirm_password: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== passwordForm.new_password) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ]
}

// 获取用户列表
const fetchUserList = async () => {
  try {
    loading.value = true
    const params = {
      page: pagination.page,
      page_size: pagination.page_size,
      ...searchForm
    }
    
    // 过滤空值
    Object.keys(params).forEach(key => {
      if (params[key as keyof typeof params] === '' || params[key as keyof typeof params] === undefined) {
        delete params[key as keyof typeof params]
      }
    })
    
    const response = await usersApi.getUserList(params)
    const data = response.data
    
    userList.value = data.users
    pagination.total = data.total
    pagination.total_pages = data.total_pages
  } catch (error) {
    ElMessage.error('获取用户列表失败')
  } finally {
    loading.value = false
  }
}

// 获取用户统计
const fetchUserStats = async () => {
  try {
    const response = await usersApi.getUserStats()
    userStats.value = response.data
  } catch (error) {
    console.error('获取用户统计失败:', error)
  }
}

// 搜索处理
const handleSearch = () => {
  pagination.page = 1
  fetchUserList()
}

// 重置搜索
const handleReset = () => {
  searchForm.search = ''
  searchForm.role = ''
  searchForm.is_active = undefined
  pagination.page = 1
  fetchUserList()
}

// 分页处理
const handleSizeChange = (size: number) => {
  pagination.page_size = size
  pagination.page = 1
  fetchUserList()
}

const handleCurrentChange = (page: number) => {
  pagination.page = page
  fetchUserList()
}

// 选择处理
const handleSelectionChange = (selection: UserType[]) => {
  selectedUsers.value = selection
}

// 显示创建对话框
const showCreateDialog = () => {
  dialogMode.value = 'create'
  dialogVisible.value = true
  resetForm()
}

// 显示编辑对话框
const showEditDialog = (user: UserType) => {
  dialogMode.value = 'edit'
  currentEditUser.value = user
  dialogVisible.value = true
  
  // 填充表单数据
  Object.assign(userForm, {
    id: user.id,
    username: user.username,
    email: user.email,
    full_name: user.full_name,
    phone: user.phone,
    roles: user.roles,
    language: user.language,
    is_active: user.is_active,
    description: user.description
  })
}

// 重置表单
const resetForm = () => {
  userFormRef.value?.resetFields()
  Object.assign(userForm, {
    username: '',
    email: '',
    password: '',
    full_name: '',
    phone: '',
    roles: ['user'],
    permissions: [],
    language: 'zh-CN',
    is_active: true,
    description: ''
  })
  currentEditUser.value = null
}

// 提交表单
const handleSubmit = async () => {
  if (!userFormRef.value) return
  
  try {
    await userFormRef.value.validate()
    submitting.value = true
    
    if (dialogMode.value === 'create') {
      await usersApi.createUser(userForm as UserCreateForm)
      ElMessage.success('用户创建成功')
    } else {
      const updateData: UserUpdateForm = {
        email: userForm.email,
        full_name: userForm.full_name,
        phone: userForm.phone,
        roles: userForm.roles,
        language: userForm.language,
        is_active: userForm.is_active,
        description: userForm.description
      }
      await usersApi.updateUser(userForm.id!, updateData)
      ElMessage.success('用户更新成功')
    }
    
    dialogVisible.value = false
    fetchUserList()
    fetchUserStats()
  } catch (error) {
    ElMessage.error(dialogMode.value === 'create' ? '创建用户失败' : '更新用户失败')
  } finally {
    submitting.value = false
  }
}

// 删除用户
const handleDelete = async (user: UserType) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除用户 "${user.username}" 吗？此操作不可恢复。`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await usersApi.deleteUser(user.id)
    ElMessage.success('用户删除成功')
    fetchUserList()
    fetchUserStats()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除用户失败')
    }
  }
}

// 下拉菜单处理
const handleDropdownCommand = (command: string, user: UserType) => {
  if (command === 'delete') {
    handleDelete(user)
  }
}

// 批量删除
const handleBatchDelete = async () => {
  if (selectedUsers.value.length === 0) return
  
  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${selectedUsers.value.length} 个用户吗？此操作不可恢复。`,
      '确认批量删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    const userIds = selectedUsers.value.map(user => user.id)
    await usersApi.batchDeleteUsers(userIds)
    ElMessage.success('批量删除成功')
    fetchUserList()
    fetchUserStats()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('批量删除失败')
    }
  }
}

// 显示重置密码对话框
const showResetPasswordDialog = (user: UserType) => {
  currentEditUser.value = user
  resetPasswordVisible.value = true
  passwordForm.new_password = ''
  passwordForm.confirm_password = ''
}

// 重置密码
const handleResetPassword = async () => {
  if (!passwordFormRef.value || !currentEditUser.value) return
  
  try {
    await passwordFormRef.value.validate()
    submitting.value = true
    
    await usersApi.resetUserPassword(currentEditUser.value.id, {
      new_password: passwordForm.new_password
    })
    
    ElMessage.success('密码重置成功')
    resetPasswordVisible.value = false
  } catch (error) {
    ElMessage.error('密码重置失败')
  } finally {
    submitting.value = false
  }
}

// 获取角色标签类型
const getRoleTagType = (role: string) => {
  const typeMap: Record<string, string> = {
    admin: 'danger',
    operator: 'warning',
    viewer: 'info',
    user: 'success'
  }
  return typeMap[role] || 'info'
}

// 获取角色标签文本
const getRoleLabel = (role: string) => {
  const labelMap: Record<string, string> = {
    admin: '管理员',
    operator: '操作员',
    viewer: '观察员',
    user: '普通用户'
  }
  return labelMap[role] || role
}

// 获取角色列表
const fetchRoleList = async () => {
  try {
    const response = await rolesApi.getRoleList({ is_active: true })
    availableRoles.value = response.data.data
  } catch (error) {
    console.error('获取角色列表失败:', error)
  }
}

// 初始化
onMounted(() => {
  fetchUserList()
  fetchUserStats()
  fetchRoleList()
})
</script>

<style scoped lang="scss">
.users-container {
  padding: 20px;
  
  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    
    .header-left {
      h2 {
        margin: 0 0 8px 0;
        color: #303133;
        font-size: 24px;
        font-weight: 600;
      }
      
      .page-description {
        margin: 0;
        color: #909399;
        font-size: 14px;
      }
    }
  }
  
  .stats-cards {
    margin-bottom: 20px;
    
    .stat-card {
      .stat-content {
        display: flex;
        align-items: center;
        
        .stat-icon {
          width: 60px;
          height: 60px;
          border-radius: 12px;
          display: flex;
          align-items: center;
          justify-content: center;
          margin-right: 16px;
          
          .el-icon {
            font-size: 24px;
            color: white;
          }
          
          &.total {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          }
          
          &.active {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
          }
          
          &.verified {
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
          }
          
          &.recent {
            background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
          }
        }
        
        .stat-info {
          .stat-value {
            font-size: 28px;
            font-weight: 600;
            color: #303133;
            line-height: 1;
            margin-bottom: 4px;
          }
          
          .stat-label {
            font-size: 14px;
            color: #909399;
          }
        }
      }
    }
  }
  
  .search-card {
    margin-bottom: 20px;
  }
  
  .table-card {
    .table-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    
    .user-info {
      display: flex;
      align-items: center;
      
      .user-details {
        margin-left: 12px;
        
        .username {
          font-weight: 500;
          color: #303133;
          margin-bottom: 4px;
        }
        
        .email {
          font-size: 12px;
          color: #909399;
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
    
    .pagination-container {
      display: flex;
      justify-content: center;
      margin-top: 20px;
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
}
</style>