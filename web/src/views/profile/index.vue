<template>
  <div class="profile-container">
    <el-card class="profile-card">
      <template #header>
        <div class="card-header">
          <span>个人中心</span>
        </div>
      </template>
      
      <div class="profile-content">
        <div class="profile-left">
          <div class="avatar-section">
            <el-avatar :size="120" :src="userStore.user?.avatar" class="user-avatar">
              <el-icon><User /></el-icon>
            </el-avatar>
            <el-button 
              type="primary" 
              size="small" 
              class="upload-btn" 
              :loading="uploading"
              @click="handleAvatarUpload"
            >
              {{ uploading ? '上传中...' : '更换头像' }}
            </el-button>
          </div>
        </div>
        
        <div class="profile-right">
          <div class="user-info">
            <h2 class="username">{{ userStore.user?.full_name || userStore.user?.username }}</h2>
            <p class="user-role">
              <el-tag :type="getRoleType(userStore.user?.role)">{{ getRoleText(userStore.user?.role) }}</el-tag>
            </p>
            
            <div class="info-grid">
              <div class="info-item">
                <label>用户名：</label>
                <span>{{ userStore.user?.username }}</span>
              </div>
              <div class="info-item">
                <label>邮箱：</label>
                <span>{{ userStore.user?.email }}</span>
              </div>
              <div class="info-item">
                <label>手机号：</label>
                <span>{{ userStore.user?.phone || '未设置' }}</span>
              </div>
              <div class="info-item">
                <label>部门：</label>
                <span>{{ userStore.user?.department || '未设置' }}</span>
              </div>
              <div class="info-item">
                <label>最后登录：</label>
                <span>{{ formatDate(userStore.user?.last_login) }}</span>
              </div>
              <div class="info-item">
                <label>注册时间：</label>
                <span>{{ formatDate(userStore.user?.created_at) }}</span>
              </div>
            </div>
            
            <div class="action-buttons">
              <el-button type="primary" @click="goToSettings">
                <el-icon><Setting /></el-icon>
                编辑资料
              </el-button>
              <el-button @click="handleChangePassword">
                <el-icon><Lock /></el-icon>
                修改密码
              </el-button>
            </div>
          </div>
        </div>
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
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { User, Setting, Lock } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import { authApi } from '@/api/auth'
import { formatDate } from '@/utils/date'

const router = useRouter()
const userStore = useUserStore()

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

// 获取角色类型
const getRoleType = (role?: string) => {
  switch (role) {
    case 'admin':
      return 'danger'
    case 'operator':
      return 'warning'
    case 'viewer':
      return 'info'
    default:
      return 'info'
  }
}

// 获取角色文本
const getRoleText = (role?: string) => {
  switch (role) {
    case 'admin':
      return '管理员'
    case 'operator':
      return '操作员'
    case 'viewer':
      return '查看者'
    default:
      return '未知角色'
  }
}

// 跳转到设置页面
const goToSettings = () => {
  router.push('/settings')
}

// 处理头像上传
const uploading = ref(false)

const handleAvatarUpload = () => {
  // 创建文件输入元素
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
        await fetchUserInfo()
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

// 处理修改密码
const handleChangePassword = () => {
  passwordDialogVisible.value = true
  // 重置表单
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
</script>

<style scoped>
.profile-container {
  padding: 20px;
}

.profile-card {
  max-width: 1000px;
  margin: 0 auto;
}

.card-header {
  font-size: 18px;
  font-weight: 600;
}

.profile-content {
  display: flex;
  gap: 40px;
}

.profile-left {
  flex: 0 0 200px;
}

.avatar-section {
  text-align: center;
}

.user-avatar {
  margin-bottom: 16px;
  border: 3px solid #f0f0f0;
}

.upload-btn {
  display: block;
  margin: 0 auto;
}

.profile-right {
  flex: 1;
}

.username {
  margin: 0 0 8px 0;
  font-size: 24px;
  color: #303133;
}

.user-role {
  margin: 0 0 24px 0;
}

.info-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 32px;
}

.info-item {
  display: flex;
  align-items: center;
}

.info-item label {
  font-weight: 600;
  color: #606266;
  min-width: 80px;
  margin-right: 8px;
}

.info-item span {
  color: #303133;
}

.action-buttons {
  display: flex;
  gap: 12px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

@media (max-width: 768px) {
  .profile-content {
    flex-direction: column;
    gap: 20px;
  }
  
  .profile-left {
    flex: none;
  }
  
  .info-grid {
    grid-template-columns: 1fr;
  }
}
</style>