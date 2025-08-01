import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import { useUserStore } from '@/stores/user'
import NProgress from 'nprogress'
import 'nprogress/nprogress.css'

// 配置 NProgress
NProgress.configure({ showSpinner: false })

const routes: Array<RouteRecordRaw> = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: {
      title: '登录',
      requiresAuth: false
    }
  },
  {
    path: '/',
    name: 'Layout',
    component: () => import('@/layouts/MainLayout.vue'),
    redirect: '/dashboard',
    meta: {
      requiresAuth: true
    },
    children: [
      {
        path: '/dashboard',
        name: 'Dashboard',
        component: () => import('@/views/Dashboard.vue'),
        meta: {
          title: '仪表盘',
          icon: 'DataBoard'
        }
      },
      {
        path: '/cameras',
        name: 'Cameras',
        redirect: '/cameras/list',
        meta: {
          title: '摄像头管理',
          icon: 'VideoCamera'
        },
        children: [
          {
            path: '/cameras/list',
            name: 'CameraList',
            component: () => import('@/views/cameras/index.vue'),
            meta: {
              title: '摄像头列表',
              icon: 'VideoCamera'
            }
          },
          {
            path: '/cameras/groups',
            name: 'CameraGroups',
            component: () => import('@/views/cameras/groups.vue'),
            meta: {
              title: '摄像头分组',
              icon: 'Collection'
            }
          },
          {
            path: '/cameras/groups/:id/cameras',
            name: 'GroupCameras',
            component: () => import('@/views/cameras/group-cameras.vue'),
            meta: {
              title: '分组摄像头管理',
              hidden: true // 在菜单中隐藏
            }
          }
        ]
      },
      {
        path: '/ai',
        name: 'AI',
        meta: {
          title: 'AI应用中心',
          icon: 'Cpu'
        },
        children: [
          {
            path: '/ai/unified',
            name: 'AIUnified',
            component: () => import('@/views/ai/unified-management.vue'),
            meta: {
              title: 'AI应用管理中心',
              icon: 'MagicStick'
            }
          },
          {
            path: '/ai/services',
            name: 'AIServices',
            component: () => import('@/views/ai/services.vue'),
            meta: {
              title: 'AI服务管理',
              icon: 'Service'
            }
          },
          {
            path: '/ai/workers',
            name: 'AIWorkers',
            component: () => import('@/views/ai/workers.vue'),
            meta: {
              title: 'Worker节点管理',
              icon: 'Monitor'
            }
          }
        ]
      },
      {
        path: '/events',
        name: 'Events',
        meta: {
          title: '事件告警中心',
          icon: 'Warning'
        },
        children: [
          {
            path: '/events/list',
            name: 'EventsList',
            component: () => import('@/views/events/list.vue'),
            meta: {
              title: '事件列表',
              icon: 'List'
            }
          },
          {
            path: '/events/rules',
            name: 'EventRules',
            component: () => import('@/views/events/rules.vue'),
            meta: {
              title: '事件规则',
              icon: 'SetUp'
            }
          },
          {
            path: '/events/notifications',
            name: 'EventNotifications',
            component: () => import('@/views/events/notifications.vue'),
            meta: {
              title: '通知配置',
              icon: 'Bell'
            }
          }
        ]
      },
      {
        path: '/diagnosis',
        name: 'Diagnosis',
        meta: {
          title: '智能诊断',
          icon: 'Monitor'
        },
        children: [
          {
            path: '/diagnosis/tasks',
            name: 'DiagnosisTasks',
            component: () => import('@/views/diagnosis/tasks.vue'),
            meta: {
              title: '诊断任务',
              icon: 'Operation'
            }
          },
          {
            path: '/diagnosis/tasks/:id',
            name: 'DiagnosisTaskDetail',
            component: () => import('@/views/diagnosis/task-detail.vue'),
            meta: {
              title: '任务详情',
              hidden: true
            }
          },
          {
            path: '/diagnosis/results/:id',
            name: 'DiagnosisResultDetail',
            component: () => import('@/views/diagnosis/result-detail.vue'),
            meta: {
              title: '诊断结果详情',
              hidden: true
            }
          },
          {
            path: '/diagnosis/results',
            name: 'DiagnosisResults',
            component: () => import('@/views/diagnosis/results.vue'),
            meta: {
              title: '诊断结果',
              icon: 'DocumentChecked'
            }
          },
          {
            path: '/diagnosis/alarms',
            name: 'DiagnosisAlarms',
            component: () => import('@/views/diagnosis/alarms.vue'),
            meta: {
              title: '诊断告警',
              icon: 'AlarmClock'
            }
          },
          {
            path: '/diagnosis/templates',
            name: 'DiagnosisTemplates',
            component: () => import('@/views/diagnosis/templates.vue'),
            meta: {
              title: '诊断模板',
              icon: 'Document'
            }
          },
          {
            path: '/diagnosis/alarm-rules',
            name: 'DiagnosisAlarmRules',
            component: () => import('@/views/diagnosis/alarm-rules.vue'),
            meta: {
              title: '告警规则',
              icon: 'Warning'
            }
          },
          {
            path: '/diagnosis/notification-channels',
            name: 'DiagnosisNotificationChannels',
            component: () => import('@/views/diagnosis/notification-channels.vue'),
            meta: {
              title: '通知设置',
              icon: 'Message'
            }
          }
        ]
      },
      {
        path: '/system',
        name: 'System',
        meta: {
          title: '系统配置',
          icon: 'Setting'
        },
        children: [
          {
            path: '/system/config',
            name: 'SystemConfig',
            component: () => import('@/views/system/config.vue'),
            meta: {
              title: '系统设置',
              icon: 'Tools'
            }
          },
          {
            path: '/system/users',
            name: 'SystemUsers',
            component: () => import('@/views/system/users.vue'),
            meta: {
              title: '用户管理',
              icon: 'User'
            }
          },
          {
            path: '/system/roles',
            name: 'SystemRoles',
            component: () => import('@/views/system/roles.vue'),
            meta: {
              title: '角色管理',
              icon: 'UserFilled'
            }
          },
          {
            path: '/system/logs',
            name: 'SystemLogs',
            component: () => import('@/views/system/logs.vue'),
            meta: {
              title: '系统日志',
              icon: 'Document'
            }
          },
          {
            path: '/system/metrics',
            name: 'SystemMetrics',
            component: () => import('@/views/system/metrics.vue'),
            meta: {
              title: '系统监控',
              icon: 'TrendCharts'
            }
          },
          {
            path: '/system/media-nodes',
            name: 'SystemMediaNodes',
            component: () => import('@/views/system/media-nodes.vue'),
            meta: {
              title: '流媒体节点',
              icon: 'Connection'
            }
          }
        ]
      },
      // 消息中心
      {
        path: '/messages',
        name: 'Messages',
        component: () => import('@/views/messages/index.vue'),
        meta: {
          title: '消息中心',
          hidden: true // 在菜单中隐藏
        }
      },
      // 个人中心和设置页面
      {
        path: '/profile',
        name: 'Profile',
        component: () => import('@/views/profile/index.vue'),
        meta: {
          title: '个人中心',
          hidden: true // 在菜单中隐藏
        }
      },
      {
        path: '/settings',
        name: 'Settings',
        component: () => import('@/views/profile/settings.vue'),
        meta: {
          title: '账户设置',
          hidden: true // 在菜单中隐藏
        }
      }
    ]
  },
  {
    path: '/404',
    name: '404',
    component: () => import('@/views/404.vue'),
    meta: {
      title: '页面不存在'
    }
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/404'
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach(async (to, from, next) => {
  NProgress.start()
  
  const userStore = useUserStore()
  
  // 设置页面标题
  if (to.meta.title) {
    document.title = `${to.meta.title} - EasySight`
  } else {
    document.title = 'EasySight - 智能视频监控系统'
  }
  
  // 检查是否需要认证
  if (to.meta.requiresAuth !== false) {
    if (!userStore.isLoggedIn) {
      // 未登录，重定向到登录页
      next({ name: 'Login', query: { redirect: to.fullPath } })
      return
    }
    
    // 检查页面权限
    const routePath = to.path
    
    // 对于系统管理相关页面，检查页面权限
    if (routePath.startsWith('/system')) {
      if (!userStore.hasPagePermission('/system')) {
        // 没有系统管理权限，重定向到首页
        next({ name: 'Dashboard' })
        return
      }
    }
    
    // 检查其他页面权限
    const pagePermissionMap: Record<string, string> = {
      '/cameras': '/cameras',
      '/ai': '/ai',
      '/events': '/events',
      '/diagnosis': '/diagnosis'
    }
    
    for (const [pathPrefix, permission] of Object.entries(pagePermissionMap)) {
      if (routePath.startsWith(pathPrefix)) {
        if (!userStore.hasPagePermission(permission)) {
          // 没有页面权限，重定向到首页
          next({ name: 'Dashboard' })
          return
        }
        break
      }
    }
  } else {
    // 不需要认证的页面，如果已登录则重定向到首页
    if (userStore.isLoggedIn && to.name === 'Login') {
      next({ name: 'Dashboard' })
      return
    }
  }
  
  next()
})

router.afterEach(() => {
  NProgress.done()
})

export default router