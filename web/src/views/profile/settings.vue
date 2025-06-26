<template>
  <div class="settings-container">
    <el-card class="settings-card">
      <template #header>
        <div class="card-header">
          <el-button type="text" @click="goBack" class="back-btn">
            <el-icon><ArrowLeft /></el-icon>
            返回
          </el-button>
          <span>账户设置</span>
        </div>
      </template>
      
      <div class="settings-content">
        <el-tabs v-model="activeTab" class="settings-tabs">
          <!-- 基本信息 -->
          <el-tab-pane label="基本信息" name="basic">
            <el-form
              ref="basicFormRef"
              :model="basicForm"
              :rules="basicRules"
              label-width="100px"
              class="settings-form"
            >
              <el-form-item label="头像">
                <div class="avatar-upload">
                  <el-avatar 
                    :size="80" 
                    :src="userStore.user?.avatar" 
                    class="avatar"
                  >
                    <el-icon><User /></el-icon>
                  </el-avatar>
                  <div class="avatar-actions">
                    <el-button 
                      type="primary" 
                      size="small" 
                      :loading="uploading"
                      @click="handleAvatarUpload"
                    >
                      {{ uploading ? '上传中...' : '更换头像' }}
                    </el-button>
                    <el-button 
                      v-if="userStore.user?.avatar" 
                      type="danger" 
                      size="small" 
                      :loading="deleting"
                      @click="handleDeleteAvatar"
                    >
                      {{ deleting ? '删除中...' : '删除头像' }}
                    </el-button>
                  </div>
                </div>
              </el-form-item>
              
              <el-form-item label="用户名" prop="username">
                <el-input v-model="basicForm.username" disabled>
                  <template #suffix>
                    <el-tooltip content="用户名不可修改" placement="top">
                      <el-icon><InfoFilled /></el-icon>
                    </el-tooltip>
                  </template>
                </el-input>
              </el-form-item>
              
              <el-form-item label="姓名" prop="full_name">
                <el-input v-model="basicForm.full_name" placeholder="请输入姓名" />
              </el-form-item>
              
              <el-form-item label="邮箱" prop="email">
                <el-input v-model="basicForm.email" placeholder="请输入邮箱" />
              </el-form-item>
              
              <el-form-item label="手机号" prop="phone">
                <el-input v-model="basicForm.phone" placeholder="请输入手机号" />
              </el-form-item>
              
              <el-form-item label="部门" prop="department">
                <el-input v-model="basicForm.department" placeholder="请输入部门" />
              </el-form-item>
              
              <el-form-item>
                <el-button type="primary" @click="handleBasicSubmit" :loading="basicLoading">
                  保存修改
                </el-button>
                <el-button @click="resetBasicForm">重置</el-button>
              </el-form-item>
            </el-form>
          </el-tab-pane>
          
          <!-- 安全设置 -->
          <el-tab-pane label="安全设置" name="security">
            <div class="security-section">
              <div class="security-item">
                <div class="security-info">
                  <h4>登录密码</h4>
                  <p class="security-desc">定期更换密码可以提高账户安全性</p>
                </div>
                <el-button type="primary" @click="showPasswordDialog">
                  修改密码
                </el-button>
              </div>
              
              <el-divider />
              
              <div class="security-item">
                <div class="security-info">
                  <h4>登录记录</h4>
                  <p class="security-desc">查看最近的登录记录</p>
                </div>
                <el-button @click="showLoginHistory">
                  查看记录
                </el-button>
              </div>
            </div>
          </el-tab-pane>
          
          <!-- 通知设置 -->
          <el-tab-pane label="通知设置" name="notification">
            <el-form class="settings-form">
              <el-form-item label="邮件通知">
                <el-switch
                  v-model="notificationSettings.email_enabled"
                  @change="handleNotificationChange"
                />
                <span class="setting-desc">接收系统邮件通知</span>
              </el-form-item>
              
              <el-form-item label="短信通知">
                <el-switch
                  v-model="notificationSettings.sms_enabled"
                  @change="handleNotificationChange"
                />
                <span class="setting-desc">接收重要事件短信通知</span>
              </el-form-item>
              
              <el-form-item label="浏览器通知">
                <el-switch
                  v-model="notificationSettings.browser_enabled"
                  @change="handleNotificationChange"
                />
                <span class="setting-desc">接收浏览器推送通知</span>
              </el-form-item>
              
              <el-form-item label="事件告警">
                <el-switch
                  v-model="notificationSettings.alert_enabled"
                  @change="handleNotificationChange"
                />
                <span class="setting-desc">接收系统事件告警</span>
              </el-form-item>
            </el-form>
          </el-tab-pane>
        </el-tabs>
      </div>
    </el-card>
    
    <!-- 修改密码对话框 -->
    <el-dialog v-model="passwordDialogVisible" title="修改密码" width="400px">
      <el-form ref="passwordFormRef" :model="passwordForm" :rules="passwordRules" label-width="80px">
        <el-form-item label="原密码" prop="old_password">
          <el-input
            v-model="passwordForm.old_password"
            type="password"
            placeholder="请输入原密码"
            show-password
          />
        </el-form-item>
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
            placeholder="请再次输入新密码"
            show-password
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="passwordDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handlePasswordSubmit" :loading="passwordLoading">
            确认修改
          </el-button>
        </span>
      </template>
    </el-dialog>
    
    <!-- 登录记录对话框 -->
    <el-dialog v-model="loginHistoryVisible" title="登录记录" width="600px">
      <el-table :data="loginHistory" style="width: 100%">
        <el-table-column prop="login_time" label="登录时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.login_time) }}
          </template>
        </el-table-column>
        <el-table-column prop="ip_address" label="IP地址" width="120" />
        <el-table-column prop="user_agent" label="设备信息" show-overflow-tooltip />
        <el-table-column prop="status" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.status === 'success' ? 'success' : 'danger'">
              {{ row.status === 'success' ? '成功' : '失败' }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { ArrowLeft, InfoFilled } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import { authApi } from '@/api/auth'
import { usersApi } from '@/api/users'
import { formatDate } from '@/utils/date'
import type { User } from '@/types/user'

const router = useRouter()
const userStore = useUserStore()

// 当前激活的标签页
const activeTab = ref('basic')

// 基本信息表单
const basicFormRef = ref<FormInstance>()
const basicLoading = ref(false)
const uploading = ref(false)
const deleting = ref(false)
const basicForm = reactive<Partial<User>>({
  username: '',
  full_name: '',
  email: '',
  phone: '',
  department: ''
})

const basicRules: FormRules = {
  full_name: [
    { required: true, message: '请输入姓名', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }
  ],
  phone: [
    { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号', trigger: 'blur' }
  ]
}

// 密码修改相关
const passwordDialogVisible = ref(false)
const passwordLoading = ref(false)
const passwordFormRef = ref<FormInstance>()
const passwordForm = reactive({
  old_password: '',
  new_password: '',
  confirm_password: ''
})

const passwordRules: FormRules = {
  old_password: [
    { required: true, message: '请输入原密码', trigger: 'blur' }
  ],
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于6位', trigger: 'blur' }
  ],
  confirm_password: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
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

// 通知设置
const notificationSettings = reactive({
  email_enabled: true,
  sms_enabled: false,
  browser_enabled: true,
  alert_enabled: true
})

// 登录记录
const loginHistoryVisible = ref(false)
const loginHistory = ref([
  {
    login_time: new Date().toISOString(),
    ip_address: '192.168.1.100',
    user_agent: 'Chrome 120.0.0.0 Windows',
    status: 'success'
  },
  {
    login_time: new Date(Date.now() - 86400000).toISOString(),
    ip_address: '192.168.1.100',
    user_agent: 'Chrome 120.0.0.0 Windows',
    status: 'success'
  }
])

// 初始化数据
const initData = () => {
  if (userStore.user) {
    Object.assign(basicForm, {
      username: userStore.user.username,
      full_name: userStore.user.full_name,
      email: userStore.user.email,
      phone: userStore.user.phone,
      department: userStore.user.department
    })
  }
}

// 返回上一页
const goBack = () => {
  router.back()
}

// 提交基本信息
const handleBasicSubmit = async () => {
  if (!basicFormRef.value || !userStore.user?.id) return
  
  try {
    await basicFormRef.value.validate()
    basicLoading.value = true
    
    await authApi.updateProfile({
      full_name: basicForm.full_name,
      email: basicForm.email,
      phone: basicForm.phone,
      department: basicForm.department
    })
    
    // 更新用户信息
    await userStore.getUserInfo()
    
    ElMessage.success('基本信息更新成功')
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '更新失败')
  } finally {
    basicLoading.value = false
  }
}

// 重置基本信息表单
const resetBasicForm = () => {
  initData()
}

// 处理头像上传
const handleAvatarUpload = () => {
  const input = document.createElement('input')
  input.type = 'file'
  input.accept = 'image/*'
  input.onchange = async (event) => {
    const file = (event.target as HTMLInputElement).files?.[0]
    if (!file) return
    
    // 验证文件大小 (5MB)
    if (file.size > 5 * 1024 * 1024) {
      ElMessage.error('文件大小不能超过5MB')
      return
    }
    
    // 验证文件类型
    const validTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif']
    if (!validTypes.includes(file.type)) {
      ElMessage.error('只支持 JPG, JPEG, PNG, GIF 格式的图片')
      return
    }
    
    try {
      uploading.value = true
      const response = await authApi.uploadAvatar(file)
      
      if (response.data.success) {
        // 更新用户头像
        if (userStore.user) {
          userStore.user.avatar = response.data.data.avatar_url
        }
        ElMessage.success('头像上传成功')
        // 刷新用户信息
        await userStore.getUserInfo()
      } else {
        ElMessage.error(response.data.message || '头像上传失败')
      }
    } catch (error: any) {
      console.error('头像上传失败:', error)
      ElMessage.error(error.response?.data?.detail || '头像上传失败')
    } finally {
      uploading.value = false
    }
  }
  input.click()
}

// 处理删除头像
const handleDeleteAvatar = async () => {
  try {
    deleting.value = true
    const response = await authApi.deleteAvatar()
    
    if (response.data.success) {
      // 清除用户头像
      if (userStore.user) {
        userStore.user.avatar = null
      }
      ElMessage.success('头像删除成功')
      // 刷新用户信息
      await userStore.getUserInfo()
    } else {
      ElMessage.error(response.data.message || '头像删除失败')
    }
  } catch (error: any) {
    console.error('头像删除失败:', error)
    ElMessage.error(error.response?.data?.detail || '头像删除失败')
  } finally {
    deleting.value = false
  }
}

// 显示密码修改对话框
const showPasswordDialog = () => {
  passwordDialogVisible.value = true
  Object.assign(passwordForm, {
    old_password: '',
    new_password: '',
    confirm_password: ''
  })
}

// 提交密码修改
const handlePasswordSubmit = async () => {
  if (!passwordFormRef.value) return
  
  try {
    await passwordFormRef.value.validate()
    passwordLoading.value = true
    
    await authApi.changePassword({
      old_password: passwordForm.old_password,
      new_password: passwordForm.new_password
    })
    
    ElMessage.success('密码修改成功')
    passwordDialogVisible.value = false
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '密码修改失败')
  } finally {
    passwordLoading.value = false
  }
}

// 显示登录记录
const showLoginHistory = () => {
  loginHistoryVisible.value = true
}

// 处理通知设置变更
const handleNotificationChange = () => {
  ElMessage.success('通知设置已更新')
}

onMounted(() => {
  initData()
})
</script>

<style scoped>
.settings-container {
  padding: 20px;
}

.settings-card {
  max-width: 800px;
  margin: 0 auto;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 18px;
  font-weight: 600;
}

.back-btn {
  padding: 0;
  font-size: 16px;
  color: #409eff;
}

.settings-content {
  padding: 20px 0;
}

.settings-tabs {
  min-height: 400px;
}

.settings-form {
  max-width: 500px;
}

.security-section {
  max-width: 600px;
}

.security-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 0;
}

.security-info h4 {
  margin: 0 0 4px 0;
  font-size: 16px;
  color: #303133;
}

.security-desc {
  margin: 0;
  font-size: 14px;
  color: #909399;
}

.setting-desc {
  margin-left: 12px;
  font-size: 14px;
  color: #909399;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

:deep(.el-tabs__item) {
  font-size: 16px;
}

:deep(.el-form-item__label) {
  font-weight: 500;
}
</style>