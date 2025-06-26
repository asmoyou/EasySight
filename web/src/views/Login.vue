<template>
  <div class="login-container">
    <div class="login-box">
      <div class="login-header">
        <div class="logo">
          <el-icon :size="40" color="#409EFF">
            <Monitor />
          </el-icon>
        </div>
        <h1 class="title">EasySight</h1>
        <p class="subtitle">智能视觉监控平台</p>
      </div>
      
      <el-form
        ref="loginFormRef"
        :model="loginForm"
        :rules="loginRules"
        class="login-form"
        @keyup.enter="handleLogin"
      >
        <el-form-item prop="username">
          <el-input
            v-model="loginForm.username"
            placeholder="请输入用户名"
            size="large"
            :prefix-icon="User"
            clearable
          />
        </el-form-item>
        
        <el-form-item prop="password">
          <el-input
            v-model="loginForm.password"
            type="password"
            placeholder="请输入密码"
            size="large"
            :prefix-icon="Lock"
            show-password
            clearable
          />
        </el-form-item>
        
        <el-form-item>
          <div class="login-options">
            <el-checkbox v-model="loginForm.remember_me">
              记住密码
            </el-checkbox>
            <el-link type="primary" :underline="false">
              忘记密码？
            </el-link>
          </div>
        </el-form-item>
        
        <el-form-item>
          <el-button
            type="primary"
            size="large"
            class="login-button"
            :loading="loading"
            @click="handleLogin"
          >
            {{ loading ? '登录中...' : '登录' }}
          </el-button>
        </el-form-item>
      </el-form>
      
      <div class="login-footer">
        <p class="copyright">
          © 2024 EasySight. All rights reserved.
        </p>
      </div>
    </div>
    
    <!-- 背景装饰 -->
    <div class="bg-decoration">
      <div class="circle circle-1"></div>
      <div class="circle circle-2"></div>
      <div class="circle circle-3"></div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { User, Lock, Monitor } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import type { LoginForm } from '@/types/user'

const router = useRouter()
const userStore = useUserStore()

const loginFormRef = ref<FormInstance>()
const loading = ref(false)

const loginForm = reactive<LoginForm>({
  username: '',
  password: '',
  remember_me: false
})

const loginRules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度在 3 到 20 个字符', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 20, message: '密码长度在 6 到 20 个字符', trigger: 'blur' }
  ]
}

const handleLogin = async () => {
  if (!loginFormRef.value) return
  
  try {
    await loginFormRef.value.validate()
    loading.value = true
    
    const loginSuccess = await userStore.login(loginForm)
    
    if (loginSuccess) {
      // 跳转到首页或之前访问的页面
      const redirect = router.currentRoute.value.query.redirect as string
      await router.push(redirect || '/')
    }
    // 登录失败的错误消息已在request拦截器中统一处理
  } catch (error: any) {
    console.error('登录失败:', error)
    // 错误处理统一在request拦截器中进行
  } finally {
    loading.value = false
  }
}

// 页面加载时检查是否已登录
onMounted(() => {
  if (userStore.isLoggedIn) {
    router.push('/')
  }
})
</script>

<style lang="scss" scoped>
.login-container {
  position: relative;
  width: 100vw;
  height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  @include flex-center;
  overflow: hidden;
  
  .login-box {
    position: relative;
    width: 400px;
    padding: 40px;
    background: rgba(255, 255, 255, 0.95);
    border-radius: 16px;
    backdrop-filter: blur(10px);
    @include card-shadow(3);
    z-index: 10;
    
    .login-header {
      text-align: center;
      margin-bottom: 32px;
      
      .logo {
        margin-bottom: 16px;
      }
      
      .title {
        font-size: 28px;
        font-weight: 600;
        color: var(--el-text-color-primary);
        margin: 0 0 8px 0;
      }
      
      .subtitle {
        font-size: 14px;
        color: var(--el-text-color-secondary);
        margin: 0;
      }
    }
    
    .login-form {
      .login-options {
        @include flex-between;
        width: 100%;
        
        .el-checkbox {
          :deep(.el-checkbox__label) {
            font-size: 14px;
            color: var(--el-text-color-regular);
          }
        }
        
        .el-link {
          font-size: 14px;
        }
      }
      
      .login-button {
        width: 100%;
        height: 44px;
        font-size: 16px;
        font-weight: 500;
        border-radius: 8px;
        @include transition(all, 0.3s, ease);
        
        &:hover {
          transform: translateY(-2px);
          @include card-shadow(2);
        }
      }
    }
    
    .login-footer {
      margin-top: 24px;
      text-align: center;
      
      .copyright {
        font-size: 12px;
        color: var(--el-text-color-placeholder);
        margin: 0;
      }
    }
  }
  
  .bg-decoration {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    pointer-events: none;
    
    .circle {
      position: absolute;
      border-radius: 50%;
      background: rgba(255, 255, 255, 0.1);
      animation: float 6s ease-in-out infinite;
      
      &.circle-1 {
        width: 200px;
        height: 200px;
        top: 10%;
        left: 10%;
        animation-delay: 0s;
      }
      
      &.circle-2 {
        width: 150px;
        height: 150px;
        top: 60%;
        right: 10%;
        animation-delay: 2s;
      }
      
      &.circle-3 {
        width: 100px;
        height: 100px;
        bottom: 20%;
        left: 20%;
        animation-delay: 4s;
      }
    }
  }
}

@keyframes float {
  0%, 100% {
    transform: translateY(0px) rotate(0deg);
  }
  50% {
    transform: translateY(-20px) rotate(180deg);
  }
}

// 响应式设计
@include respond-to(sm) {
  .login-container {
    .login-box {
      width: 90%;
      max-width: 400px;
      padding: 32px 24px;
    }
  }
}

@include respond-to(xs) {
  .login-container {
    .login-box {
      padding: 24px 20px;
      
      .login-header {
        margin-bottom: 24px;
        
        .title {
          font-size: 24px;
        }
      }
    }
  }
}
</style>