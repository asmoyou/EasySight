<template>
  <div class="main-layout" :class="{ 'sidebar-collapsed': themeStore.sidebarCollapsed }">
    <!-- 侧边栏 -->
    <aside class="sidebar">
      <div class="sidebar-header">
        <div class="logo">
          <el-icon :size="32" color="#409EFF">
            <Monitor />
          </el-icon>
          <span v-show="!themeStore.sidebarCollapsed" class="logo-text">EasySight</span>
        </div>
      </div>
      
      <div class="sidebar-content">
        <el-menu
          :default-active="activeMenu"
          :collapse="themeStore.sidebarCollapsed"
          :unique-opened="true"
          router
          class="sidebar-menu"
        >
          <!-- 仪表盘 -->
          <el-menu-item v-if="userStore.hasPagePermission('/dashboard')" index="/dashboard">
            <el-icon><DataBoard /></el-icon>
            <template #title>仪表盘</template>
          </el-menu-item>
          
          <!-- 摄像头管理 -->
          <el-sub-menu v-if="userStore.hasPagePermission('/cameras')" index="/cameras">
            <template #title>
              <el-icon><VideoCamera /></el-icon>
              <span>摄像头管理</span>
            </template>
            <el-menu-item index="/cameras/list">摄像头列表</el-menu-item>
            <el-menu-item index="/cameras/groups">分组管理</el-menu-item>
          </el-sub-menu>
          
          <!-- AI应用中心 -->
          <el-sub-menu v-if="userStore.hasPagePermission('/ai')" index="/ai">
            <template #title>
              <el-icon><Cpu /></el-icon>
              <span>AI应用中心</span>
            </template>
            <el-menu-item index="/ai/unified">AI应用管理中心</el-menu-item>
            <el-menu-item index="/ai/services">事件算法服务管理</el-menu-item>
            <el-menu-item index="/ai/workers">Worker节点管理</el-menu-item>
          </el-sub-menu>
          
          <!-- 事件告警中心 -->
          <el-sub-menu v-if="userStore.hasPagePermission('/events')" index="/events">
            <template #title>
              <el-icon><Warning /></el-icon>
              <span>事件告警中心</span>
            </template>
            <el-menu-item index="/events/list">事件列表</el-menu-item>
            <el-menu-item index="/events/rules">告警规则</el-menu-item>
            <el-menu-item index="/events/notifications">通知设置</el-menu-item>
          </el-sub-menu>
          
          <!-- 智能诊断 -->
          <el-sub-menu v-if="userStore.hasPagePermission('/diagnosis')" index="/diagnosis">
            <template #title>
              <el-icon><Monitor /></el-icon>
              <span>智能诊断</span>
            </template>
            <el-menu-item index="/diagnosis/tasks">诊断任务</el-menu-item>
            <el-menu-item index="/diagnosis/results">诊断结果</el-menu-item>
            <el-menu-item index="/diagnosis/alarms">诊断告警</el-menu-item>
            <el-menu-item index="/diagnosis/templates">模板管理</el-menu-item>
          </el-sub-menu>
          
          <!-- 系统配置 -->
          <el-sub-menu v-if="userStore.hasPagePermission('/system')" index="/system">
            <template #title>
              <el-icon><Setting /></el-icon>
              <span>系统配置</span>
            </template>
            <el-menu-item index="/system/config">系统设置</el-menu-item>
            <el-menu-item index="/system/users">用户管理</el-menu-item>
            <el-menu-item index="/system/roles">角色管理</el-menu-item>
            <el-menu-item index="/system/logs">系统日志</el-menu-item>
            <el-menu-item index="/system/metrics">系统监控</el-menu-item>
            <el-menu-item index="/system/media-nodes">流媒体节点</el-menu-item>
          </el-sub-menu>
        </el-menu>
      </div>
    </aside>
    
    <!-- 主内容区 -->
    <div class="main-content">
      <!-- 顶部导航栏 -->
      <header class="header">
        <div class="header-left">
          <el-button
            type="text"
            class="collapse-btn"
            @click="themeStore.toggleSidebar()"
          >
            <el-icon :size="20">
              <Expand v-if="themeStore.sidebarCollapsed" />
              <Fold v-else />
            </el-icon>
          </el-button>
          
          <el-breadcrumb separator="/" class="breadcrumb">
            <el-breadcrumb-item
              v-for="item in breadcrumbList"
              :key="item.path"
              :to="item.path"
            >
              {{ item.title }}
            </el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        
        <div class="header-right">
          <!-- 主题切换 -->
          <el-tooltip content="切换主题" placement="bottom">
            <el-button
              type="text"
              class="theme-btn"
              @click="themeStore.toggleTheme()"
            >
              <el-icon :size="18">
                <Sunny v-if="themeStore.isDark" />
                <Moon v-else />
              </el-icon>
            </el-button>
          </el-tooltip>
          
          <!-- 全屏切换 -->
          <el-tooltip content="全屏" placement="bottom">
            <el-button
              type="text"
              class="fullscreen-btn"
              @click="toggleFullscreen"
            >
              <el-icon :size="18">
                <FullScreen />
              </el-icon>
            </el-button>
          </el-tooltip>
          
          <!-- 通知 -->
          <MessageNotification ref="messageNotificationRef" />
          
          <!-- 用户菜单 -->
          <el-dropdown trigger="click" class="user-dropdown">
            <div class="user-info">
              <el-avatar :size="32" :src="userStore.user?.avatar">
                <el-icon><User /></el-icon>
              </el-avatar>
              <span class="username">{{ userStore.user?.username || '用户' }}</span>
              <el-icon class="arrow-down"><ArrowDown /></el-icon>
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item @click="handleProfile">
                  <el-icon><User /></el-icon>
                  个人中心
                </el-dropdown-item>
                <el-dropdown-item @click="handleSettings">
                  <el-icon><Setting /></el-icon>
                  账户设置
                </el-dropdown-item>
                <el-dropdown-item divided @click="handleLogout">
                  <el-icon><SwitchButton /></el-icon>
                  退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </header>
      
      <!-- 页面内容 -->
      <main class="page-content">
        <router-view v-slot="{ Component }">
          <transition name="fade-transform" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Monitor,
  DataBoard,
  VideoCamera,
  Cpu,
  Warning,
  Setting,
  Expand,
  Fold,
  Sunny,
  Moon,
  FullScreen,
  Bell,
  User,
  ArrowDown,
  SwitchButton
} from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import { useThemeStore } from '@/stores/theme'
import MessageNotification from '@/components/MessageNotification.vue'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const themeStore = useThemeStore()

const messageNotificationRef = ref()

// 当前激活的菜单项
const activeMenu = computed(() => {
  const path = route.path
  // 根据路径匹配对应的菜单项
  if (path.startsWith('/cameras')) {
    return path
  } else if (path.startsWith('/ai')) {
    return path
  } else if (path.startsWith('/events')) {
    return path
  } else if (path.startsWith('/diagnosis')) {
    return path
  } else if (path.startsWith('/system')) {
    return path
  }
  return path
})

// 面包屑导航
const breadcrumbList = computed(() => {
  const matched = route.matched.filter(item => item.meta && item.meta.title)
  const breadcrumbs = matched.map(item => ({
    path: item.path,
    title: item.meta?.title || ''
  }))
  
  // 如果不是首页，添加首页到面包屑
  if (route.path !== '/dashboard' && breadcrumbs.length > 0) {
    breadcrumbs.unshift({
      path: '/dashboard',
      title: '仪表盘'
    })
  }
  
  return breadcrumbs
})

// 全屏切换
const toggleFullscreen = () => {
  if (!document.fullscreenElement) {
    document.documentElement.requestFullscreen()
  } else {
    document.exitFullscreen()
  }
}

// 个人中心
const handleProfile = () => {
  router.push('/profile')
}

// 账户设置
const handleSettings = () => {
  router.push('/settings')
}

// 退出登录
const handleLogout = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要退出登录吗？',
      '提示',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await userStore.logout()
    ElMessage.success('退出登录成功')
    router.push('/login')
  } catch (error) {
    // 用户取消操作
  }
}

// 监听路由变化，更新页面标题
watch(
  () => route.meta.title,
  (title) => {
    if (title) {
      document.title = `${title} - EasySight`
    }
  },
  { immediate: true }
)
</script>

<style lang="scss" scoped>
.main-layout {
  display: flex;
  height: 100vh;
  
  .sidebar {
    width: $sidebar-width;
    background: $sidebar-bg-color;
    @include transition(width, 0.3s, ease);
    
    .sidebar-header {
      height: $header-height;
      @include flex-center;
      border-bottom: 1px solid rgba(255, 255, 255, 0.1);
      
      .logo {
        @include flex-center;
        gap: 12px;
        
        .logo-text {
          font-size: 20px;
          font-weight: 600;
          color: #fff;
          @include transition(opacity, 0.3s, ease);
        }
      }
    }
    
    .sidebar-content {
      height: calc(100vh - #{$header-height});
      overflow-y: auto;
      @include scrollbar(6px, transparent, rgba(255, 255, 255, 0.3));
      
      .sidebar-menu {
        border: none;
        background: transparent;
        
        :deep(.el-menu-item) {
          color: $sidebar-text-color;
          
          &:hover {
            background: $sidebar-hover-bg;
            color: #fff;
          }
          
          &.is-active {
            background: $sidebar-active-color;
            color: #fff;
          }
        }
        
        :deep(.el-sub-menu) {
          .el-sub-menu__title {
            color: $sidebar-text-color;
            
            &:hover {
              background: $sidebar-hover-bg;
              color: #fff;
            }
          }
          
          .el-menu {
            background: rgba(0, 0, 0, 0.2);
            
            .el-menu-item {
              &:hover {
                background: rgba(255, 255, 255, 0.1);
              }
              
              &.is-active {
                background: $sidebar-active-color;
              }
            }
          }
        }
      }
    }
  }
  
  .main-content {
    flex: 1;
    display: flex;
    flex-direction: column;
    overflow: hidden;
    
    .header {
      height: $header-height;
      background: var(--el-bg-color);
      border-bottom: 1px solid var(--el-border-color-lighter);
      @include flex-between;
      padding: 0 24px;
      
      .header-left {
        @include flex-vertical-center;
        gap: 16px;
        
        .collapse-btn {
          padding: 8px;
          
          &:hover {
            background: rgba(64, 158, 255, 0.1);
          }
        }
        
        .breadcrumb {
          :deep(.el-breadcrumb__item) {
            .el-breadcrumb__inner {
              color: var(--el-text-color-regular);
              
              &:hover {
                color: var(--el-color-primary);
              }
            }
            
            &:last-child {
              .el-breadcrumb__inner {
                color: var(--el-text-color-primary);
                font-weight: 500;
              }
            }
          }
        }
      }
      
      .header-right {
        @include flex-vertical-center;
        gap: 16px;
        
        .theme-btn,
        .fullscreen-btn,
        .notification-btn {
          padding: 8px;
          
          &:hover {
            background: rgba(64, 158, 255, 0.1);
          }
        }
        
        .user-dropdown {
          .user-info {
            @include flex-vertical-center;
            gap: 8px;
            padding: 4px 8px;
            border-radius: 6px;
            cursor: pointer;
            @include transition(background, 0.3s, ease);
            
            &:hover {
              background: rgba(64, 158, 255, 0.1);
            }
            
            .username {
              font-size: 14px;
              color: var(--el-text-color-primary);
              font-weight: 500;
            }
            
            .arrow-down {
              font-size: 12px;
              color: var(--el-text-color-secondary);
            }
          }
        }
      }
    }
    
    .page-content {
      flex: 1;
      padding: 24px;
      background: var(--el-bg-color-page);
      overflow-y: auto;
      @include scrollbar();
    }
  }
  
  // 侧边栏收起状态
  &.sidebar-collapsed {
    .sidebar {
      width: $sidebar-collapsed-width;
      
      .sidebar-header {
        .logo {
          .logo-text {
            opacity: 0;
          }
        }
      }
    }
  }
}

// 页面切换动画
.fade-transform-enter-active,
.fade-transform-leave-active {
  transition: all 0.3s ease;
}

.fade-transform-enter-from {
  opacity: 0;
  transform: translateX(30px);
}

.fade-transform-leave-to {
  opacity: 0;
  transform: translateX(-30px);
}

// 响应式设计
@include respond-to(md) {
  .main-layout {
    .main-content {
      .page-content {
        padding: 16px;
      }
    }
  }
}

@include respond-to(sm) {
  .main-layout {
    .sidebar {
      position: fixed;
      top: 0;
      left: 0;
      z-index: 1000;
      height: 100vh;
    }
    
    .main-content {
      margin-left: 0;
      
      .header {
        padding: 0 16px;
        
        .header-left {
          .breadcrumb {
            display: none;
          }
        }
      }
      
      .page-content {
        padding: 12px;
      }
    }
    
    &.sidebar-collapsed {
      .sidebar {
        transform: translateX(-100%);
      }
    }
  }
}
</style>