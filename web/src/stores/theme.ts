import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export type ThemeMode = 'light' | 'dark' | 'auto'

export const useThemeStore = defineStore('theme', () => {
  const mode = ref<ThemeMode>('light')
  const sidebarCollapsed = ref(false)
  const primaryColor = ref('#409EFF')
  
  // 计算属性
  const isDark = computed(() => {
    if (mode.value === 'auto') {
      return window.matchMedia('(prefers-color-scheme: dark)').matches
    }
    return mode.value === 'dark'
  })
  
  const currentTheme = computed(() => isDark.value ? 'dark' : 'light')
  
  // 设置主题模式
  const setThemeMode = (newMode: ThemeMode) => {
    mode.value = newMode
    applyTheme()
    localStorage.setItem('theme_mode', newMode)
  }
  
  // 切换主题
  const toggleTheme = () => {
    const newMode = mode.value === 'light' ? 'dark' : 'light'
    setThemeMode(newMode)
  }
  
  // 设置主色调
  const setPrimaryColor = (color: string) => {
    primaryColor.value = color
    applyPrimaryColor(color)
    localStorage.setItem('primary_color', color)
  }
  
  // 切换侧边栏折叠状态
  const toggleSidebar = () => {
    sidebarCollapsed.value = !sidebarCollapsed.value
    localStorage.setItem('sidebar_collapsed', String(sidebarCollapsed.value))
  }
  
  // 设置侧边栏折叠状态
  const setSidebarCollapsed = (collapsed: boolean) => {
    sidebarCollapsed.value = collapsed
    localStorage.setItem('sidebar_collapsed', String(collapsed))
  }
  
  // 应用主题
  const applyTheme = () => {
    const html = document.documentElement
    
    if (isDark.value) {
      html.classList.add('dark')
    } else {
      html.classList.remove('dark')
    }
  }
  
  // 应用主色调
  const applyPrimaryColor = (color: string) => {
    const html = document.documentElement
    html.style.setProperty('--el-color-primary', color)
    
    // 生成主色调的各种变体
    const colors = generateColorVariants(color)
    Object.entries(colors).forEach(([key, value]) => {
      html.style.setProperty(key, value)
    })
  }
  
  // 生成颜色变体
  const generateColorVariants = (color: string) => {
    // 这里可以使用颜色处理库来生成变体，简化处理
    const variants: Record<string, string> = {}
    
    // Element Plus 主色调变体
    const lightLevels = [3, 5, 7, 8, 9]
    const darkLevels = [2]
    
    lightLevels.forEach(level => {
      variants[`--el-color-primary-light-${level}`] = lighten(color, level * 0.1)
    })
    
    darkLevels.forEach(level => {
      variants[`--el-color-primary-dark-${level}`] = darken(color, level * 0.1)
    })
    
    return variants
  }
  
  // 颜色变亮
  const lighten = (color: string, amount: number): string => {
    const num = parseInt(color.replace('#', ''), 16)
    const amt = Math.round(2.55 * amount * 100)
    const R = (num >> 16) + amt
    const G = (num >> 8 & 0x00FF) + amt
    const B = (num & 0x0000FF) + amt
    return '#' + (0x1000000 + (R < 255 ? R < 1 ? 0 : R : 255) * 0x10000 +
      (G < 255 ? G < 1 ? 0 : G : 255) * 0x100 +
      (B < 255 ? B < 1 ? 0 : B : 255)).toString(16).slice(1)
  }
  
  // 颜色变暗
  const darken = (color: string, amount: number): string => {
    const num = parseInt(color.replace('#', ''), 16)
    const amt = Math.round(2.55 * amount * 100)
    const R = (num >> 16) - amt
    const G = (num >> 8 & 0x00FF) - amt
    const B = (num & 0x0000FF) - amt
    return '#' + (0x1000000 + (R > 255 ? 255 : R < 0 ? 0 : R) * 0x10000 +
      (G > 255 ? 255 : G < 0 ? 0 : G) * 0x100 +
      (B > 255 ? 255 : B < 0 ? 0 : B)).toString(16).slice(1)
  }
  
  // 初始化主题
  const initTheme = () => {
    // 从本地存储恢复设置
    const storedMode = localStorage.getItem('theme_mode') as ThemeMode
    const storedColor = localStorage.getItem('primary_color')
    const storedSidebarCollapsed = localStorage.getItem('sidebar_collapsed')
    
    if (storedMode) {
      mode.value = storedMode
    }
    
    if (storedColor) {
      primaryColor.value = storedColor
      applyPrimaryColor(storedColor)
    }
    
    if (storedSidebarCollapsed !== null) {
      sidebarCollapsed.value = storedSidebarCollapsed === 'true'
    }
    
    // 应用主题
    applyTheme()
    
    // 监听系统主题变化
    if (mode.value === 'auto') {
      const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
      mediaQuery.addEventListener('change', applyTheme)
    }
  }
  
  // 重置主题设置
  const resetTheme = () => {
    setThemeMode('light')
    setPrimaryColor('#409EFF')
    setSidebarCollapsed(false)
  }
  
  return {
    // 状态
    mode: readonly(mode),
    sidebarCollapsed: readonly(sidebarCollapsed),
    primaryColor: readonly(primaryColor),
    
    // 计算属性
    isDark,
    currentTheme,
    
    // 方法
    setThemeMode,
    toggleTheme,
    setPrimaryColor,
    toggleSidebar,
    setSidebarCollapsed,
    initTheme,
    resetTheme
  }
})