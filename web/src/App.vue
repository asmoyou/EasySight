<template>
  <div id="app">
    <router-view />
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useUserStore } from '@/stores/user'
import { useThemeStore } from '@/stores/theme'

const userStore = useUserStore()
const themeStore = useThemeStore()

onMounted(() => {
  // 初始化主题
  themeStore.initTheme()
  
  // 尝试从本地存储恢复用户登录状态
  userStore.initUserFromStorage()
})
</script>

<style lang="scss">
#app {
  width: 100%;
  height: 100vh;
  overflow: hidden;
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html, body {
  width: 100%;
  height: 100%;
  font-family: 'Helvetica Neue', Helvetica, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', '微软雅黑', Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

// 滚动条样式
::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

::-webkit-scrollbar-track {
  background: var(--el-bg-color-page);
}

::-webkit-scrollbar-thumb {
  background: var(--el-border-color-light);
  border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
  background: var(--el-border-color);
}

// Element Plus 样式覆盖
.el-loading-mask {
  background-color: rgba(255, 255, 255, 0.8);
}

.dark .el-loading-mask {
  background-color: rgba(0, 0, 0, 0.8);
}

// 响应式布局
@media (max-width: 768px) {
  .el-aside {
    width: 200px !important;
  }
}
</style>