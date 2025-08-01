<template>
  <div class="event-notifications">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <h2>通知配置</h2>
        <p class="page-description">配置事件通知渠道和模板，确保重要事件及时通知</p>
      </div>
      <div class="header-right">
        <el-button type="primary" @click="showCreateDialog">
          <el-icon><Plus /></el-icon>
          新建配置
        </el-button>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-cards">
      <el-row :gutter="20">
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-content">
              <div class="stat-value">{{ stats.enabled_count }}</div>
              <div class="stat-label">已启用配置</div>
            </div>
            <el-icon class="stat-icon" color="#67C23A"><Check /></el-icon>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-content">
              <div class="stat-value">{{ stats.sent_today }}</div>
              <div class="stat-label">今日发送</div>
            </div>
            <el-icon class="stat-icon" color="#409EFF"><Message /></el-icon>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-content">
              <div class="stat-value">{{ stats.success_rate }}%</div>
              <div class="stat-label">成功率</div>
            </div>
            <el-icon class="stat-icon" color="#E6A23C"><TrendCharts /></el-icon>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-content">
              <div class="stat-value">{{ stats.total_count }}</div>
              <div class="stat-label">总配置数</div>
            </div>
            <el-icon class="stat-icon" color="#909399"><DataBoard /></el-icon>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 搜索筛选 -->
    <el-card class="search-card" shadow="never">
      <el-form :model="searchForm" inline>
        <el-form-item label="配置名称">
          <el-input
            v-model="searchForm.name"
            placeholder="请输入配置名称"
            clearable
            style="width: 200px"
          />
        </el-form-item>
        <el-form-item label="通知类型">
          <el-select v-model="searchForm.type" placeholder="请选择通知类型" clearable>
            <el-option label="邮件" value="email" />
            <el-option label="短信" value="sms" />
            <el-option label="微信" value="wechat" />
            <el-option label="钉钉" value="dingtalk" />
            <el-option label="Webhook" value="webhook" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="searchForm.is_enabled" placeholder="请选择状态" clearable>
            <el-option label="启用" :value="true" />
            <el-option label="禁用" :value="false" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">
            <el-icon><Search /></el-icon>
            搜索
          </el-button>
          <el-button @click="handleReset">
            <el-icon><RefreshLeft /></el-icon>
            重置
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 通知配置列表 -->
    <el-card class="table-card" shadow="never">
      <el-table
        v-loading="loading"
        :data="notifications"
        stripe
      >
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" label="配置名称" min-width="150" />
        <el-table-column prop="type" label="通知类型" width="120">
          <template #default="{ row }">
            <el-tag :type="getTypeColor(row.type)">
              <el-icon style="margin-right: 4px">
                <component :is="getTypeIcon(row.type)" />
              </el-icon>
              {{ getTypeName(row.type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
        <el-table-column label="配置信息" min-width="250">
          <template #default="{ row }">
            <div class="config-info">
              <div v-if="row.type === 'email'">
                <span class="config-label">SMTP:</span> {{ row.config.smtp_host }}:{{ row.config.smtp_port }}
              </div>
              <div v-else-if="row.type === 'sms'">
                <span class="config-label">服务商:</span> {{ row.config.provider }}
              </div>
              <div v-else-if="row.type === 'webhook'">
                <span class="config-label">URL:</span> {{ row.config.url }}
              </div>
              <div v-else-if="row.type === 'dingtalk'">
                <span class="config-label">机器人:</span> {{ row.config.robot_name }}
              </div>
              <div v-else-if="row.type === 'wechat'">
                <span class="config-label">企业ID:</span> {{ row.config.corp_id }}
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="发送统计" width="120">
          <template #default="{ row }">
            <div class="send-stats">
              <div>今日: {{ row.stats?.sent_today || 0 }}</div>
              <div>成功率: {{ row.stats?.success_rate || 0 }}%</div>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="is_enabled" label="状态" width="100">
          <template #default="{ row }">
            <el-switch
              v-model="row.is_enabled"
              @change="toggleNotification(row)"
            />
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="editNotification(row)">
              编辑
            </el-button>
            <el-button type="info" size="small" @click="testNotification(row)">
              测试
            </el-button>
            <el-button type="danger" size="small" @click="deleteNotification(row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :total="pagination.total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <!-- 新建/编辑通知配置对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑通知配置' : '新建通知配置'"
      width="800px"
      destroy-on-close
    >
      <el-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-width="120px"
      >
        <el-form-item label="配置名称" prop="name">
          <el-input v-model="formData.name" placeholder="请输入配置名称" />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input
            v-model="formData.description"
            type="textarea"
            :rows="2"
            placeholder="请输入配置描述"
          />
        </el-form-item>
        <el-form-item label="通知类型" prop="type">
          <el-select v-model="formData.type" placeholder="请选择通知类型" @change="onTypeChange">
            <el-option label="邮件" value="email" />
            <el-option label="短信" value="sms" />
            <el-option label="微信" value="wechat" />
            <el-option label="钉钉" value="dingtalk" />
            <el-option label="Webhook" value="webhook" />
          </el-select>
        </el-form-item>

        <!-- 邮件配置 -->
        <template v-if="formData.type === 'email'">
          <el-form-item label="SMTP主机" prop="config.smtp_host">
            <el-input v-model="formData.config.smtp_host" placeholder="请输入SMTP主机地址" />
          </el-form-item>
          <el-form-item label="SMTP端口" prop="config.smtp_port">
            <el-input-number v-model="formData.config.smtp_port" :min="1" :max="65535" />
          </el-form-item>
          <el-form-item label="用户名" prop="config.username">
            <el-input v-model="formData.config.username" placeholder="请输入邮箱用户名" />
          </el-form-item>
          <el-form-item label="密码" prop="config.password">
            <el-input v-model="formData.config.password" type="password" placeholder="请输入邮箱密码" show-password />
          </el-form-item>
          <el-form-item label="发件人" prop="config.from_email">
            <el-input v-model="formData.config.from_email" placeholder="请输入发件人邮箱" />
          </el-form-item>
        </template>

        <!-- 短信配置 -->
        <template v-if="formData.type === 'sms'">
          <el-form-item label="服务商" prop="config.provider">
            <el-select v-model="formData.config.provider" placeholder="请选择短信服务商">
              <el-option label="阿里云" value="aliyun" />
              <el-option label="腾讯云" value="tencent" />
              <el-option label="华为云" value="huawei" />
            </el-select>
          </el-form-item>
          <el-form-item label="Access Key" prop="config.access_key">
            <el-input v-model="formData.config.access_key" placeholder="请输入Access Key" />
          </el-form-item>
          <el-form-item label="Secret Key" prop="config.secret_key">
            <el-input v-model="formData.config.secret_key" type="password" placeholder="请输入Secret Key" show-password />
          </el-form-item>
          <el-form-item label="签名" prop="config.sign_name">
            <el-input v-model="formData.config.sign_name" placeholder="请输入短信签名" />
          </el-form-item>
        </template>

        <!-- Webhook配置 -->
        <template v-if="formData.type === 'webhook'">
          <el-form-item label="Webhook URL" prop="config.url">
            <el-input v-model="formData.config.url" placeholder="请输入Webhook URL" />
          </el-form-item>
          <el-form-item label="请求方法" prop="config.method">
            <el-select v-model="formData.config.method" placeholder="请选择请求方法">
              <el-option label="POST" value="POST" />
              <el-option label="PUT" value="PUT" />
              <el-option label="PATCH" value="PATCH" />
            </el-select>
          </el-form-item>
          <el-form-item label="请求头">
            <el-input
              v-model="formData.config.headers"
              type="textarea"
              :rows="3"
              placeholder="请输入请求头，JSON格式"
            />
          </el-form-item>
        </template>

        <!-- 钉钉配置 -->
        <template v-if="formData.type === 'dingtalk'">
          <el-form-item label="机器人名称" prop="config.robot_name">
            <el-input v-model="formData.config.robot_name" placeholder="请输入机器人名称" />
          </el-form-item>
          <el-form-item label="Webhook URL" prop="config.webhook_url">
            <el-input v-model="formData.config.webhook_url" placeholder="请输入钉钉机器人Webhook URL" />
          </el-form-item>
          <el-form-item label="安全密钥">
            <el-input v-model="formData.config.secret" placeholder="请输入安全密钥（可选）" />
          </el-form-item>
        </template>

        <!-- 微信配置 -->
        <template v-if="formData.type === 'wechat'">
          <el-form-item label="企业ID" prop="config.corp_id">
            <el-input v-model="formData.config.corp_id" placeholder="请输入企业微信ID" />
          </el-form-item>
          <el-form-item label="应用Secret" prop="config.corp_secret">
            <el-input v-model="formData.config.corp_secret" type="password" placeholder="请输入应用Secret" show-password />
          </el-form-item>
          <el-form-item label="应用ID" prop="config.agent_id">
            <el-input v-model="formData.config.agent_id" placeholder="请输入应用ID" />
          </el-form-item>
        </template>

        <el-form-item label="启用状态">
          <el-switch v-model="formData.is_enabled" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitForm">确定</el-button>
      </template>
    </el-dialog>

    <!-- 测试通知对话框 -->
    <el-dialog
      v-model="testDialogVisible"
      title="测试通知"
      width="600px"
      destroy-on-close
    >
      <el-form :model="testForm" label-width="100px">
        <el-form-item label="通知标题">
          <el-input v-model="testForm.title" placeholder="请输入测试通知标题" />
        </el-form-item>
        <el-form-item label="通知内容">
          <el-input
            v-model="testForm.content"
            type="textarea"
            :rows="4"
            placeholder="请输入测试通知内容"
          />
        </el-form-item>
        <el-form-item v-if="currentNotification?.type === 'email' || currentNotification?.type === 'sms'" label="接收人">
          <el-input v-model="testForm.recipient" placeholder="请输入接收人（邮箱或手机号）" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="testDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="sendTestNotification">发送测试</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Plus, Search, RefreshLeft, Check, Message, TrendCharts, DataBoard,
  ChatDotRound, Phone, Link, Monitor, ChatLineRound
} from '@element-plus/icons-vue'
import type { FormInstance, FormRules } from 'element-plus'
import { notificationChannelsApi, type NotificationChannel, type NotificationChannelCreate, type NotificationChannelUpdate } from '@/api/notification-channels'

// 类型定义
interface NotificationForm {
  name: string
  description: string
  type: string
  config: Record<string, any>
  is_enabled: boolean
}

// 响应式数据
const loading = ref(false)
const notifications = ref<NotificationChannel[]>([])
const dialogVisible = ref(false)
const testDialogVisible = ref(false)
const isEdit = ref(false)
const formRef = ref<FormInstance>()
const currentNotification = ref<NotificationChannel | null>(null)

// 统计数据
const stats = reactive({
  enabled_count: 0,
  sent_today: 0,
  success_rate: 0,
  total_count: 0
})

// 搜索表单
const searchForm = reactive({
  name: '',
  type: '',
  is_enabled: undefined as boolean | undefined
})

// 表单数据
const formData = reactive<NotificationForm>({
  name: '',
  description: '',
  type: '',
  config: {},
  is_enabled: true
})

// 测试表单
const testForm = reactive({
  title: '测试通知',
  content: '这是一条测试通知消息',
  recipient: ''
})

// 表单验证规则
const formRules = computed((): FormRules => {
  const baseRules: FormRules = {
    name: [{ required: true, message: '请输入配置名称', trigger: 'blur' }],
    description: [{ required: true, message: '请输入配置描述', trigger: 'blur' }],
    type: [{ required: true, message: '请选择通知类型', trigger: 'change' }]
  }

  // 根据类型添加特定验证规则
  if (formData.type === 'email') {
    baseRules['config.smtp_host'] = [{ required: true, message: '请输入SMTP主机', trigger: 'blur' }]
    baseRules['config.smtp_port'] = [{ required: true, message: '请输入SMTP端口', trigger: 'blur' }]
    baseRules['config.username'] = [{ required: true, message: '请输入用户名', trigger: 'blur' }]
    baseRules['config.password'] = [{ required: true, message: '请输入密码', trigger: 'blur' }]
    baseRules['config.from_email'] = [{ required: true, message: '请输入发件人邮箱', trigger: 'blur' }]
  } else if (formData.type === 'sms') {
    baseRules['config.provider'] = [{ required: true, message: '请选择服务商', trigger: 'change' }]
    baseRules['config.access_key'] = [{ required: true, message: '请输入Access Key', trigger: 'blur' }]
    baseRules['config.secret_key'] = [{ required: true, message: '请输入Secret Key', trigger: 'blur' }]
  } else if (formData.type === 'webhook') {
    baseRules['config.url'] = [{ required: true, message: '请输入Webhook URL', trigger: 'blur' }]
    baseRules['config.method'] = [{ required: true, message: '请选择请求方法', trigger: 'change' }]
  } else if (formData.type === 'dingtalk') {
    baseRules['config.robot_name'] = [{ required: true, message: '请输入机器人名称', trigger: 'blur' }]
    baseRules['config.webhook_url'] = [{ required: true, message: '请输入Webhook URL', trigger: 'blur' }]
  } else if (formData.type === 'wechat') {
    baseRules['config.corp_id'] = [{ required: true, message: '请输入企业ID', trigger: 'blur' }]
    baseRules['config.corp_secret'] = [{ required: true, message: '请输入应用Secret', trigger: 'blur' }]
    baseRules['config.agent_id'] = [{ required: true, message: '请输入应用ID', trigger: 'blur' }]
  }

  return baseRules
})

// 分页
const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

// 方法
const loadNotifications = async () => {
  loading.value = true
  try {
    const response = await notificationChannelsApi.getNotificationChannels({
      page: pagination.page,
      page_size: pagination.pageSize,
      type: searchForm.type || undefined,
      is_enabled: searchForm.is_enabled
    })
    
    notifications.value = response.data || response as any
    pagination.total = response.total || (response as any).length || 0
    
    // 加载统计数据
    try {
      const statsResponse = await notificationChannelsApi.getNotificationStats()
      Object.assign(stats, statsResponse)
    } catch (statsError) {
      console.error('加载统计数据失败:', statsError)
    }
  } catch (error) {
    console.error('加载通知配置失败:', error)
    ElMessage.error('加载通知配置失败')
    
    // 备用模拟数据
    const mockNotifications: NotificationChannel[] = [
      {
        id: 1,
        name: '系统邮件通知',
        description: '用于发送系统告警邮件',
        type: 'email',
        config: {
          smtp_server: 'smtp.qq.com',
          smtp_port: 587,
          username: 'system@example.com',
          password: '***',
          recipients: ['admin@example.com']
        },
        is_enabled: true,
        send_count: 150,
        success_count: 147,
        stats: { sent_today: 15, success_rate: 98 },
        created_at: '2024-01-15 10:00:00',
        updated_at: '2024-01-15 10:00:00'
      }
    ]
    
    notifications.value = mockNotifications
    pagination.total = mockNotifications.length
    
    // 更新统计数据
    stats.enabled_count = mockNotifications.filter(n => n.is_enabled).length
    stats.sent_today = mockNotifications.reduce((sum, n) => sum + (n.stats?.sent_today || 0), 0)
    stats.success_rate = Math.round(mockNotifications.reduce((sum, n) => sum + (n.stats?.success_rate || 0), 0) / mockNotifications.length)
    stats.total_count = mockNotifications.length
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  pagination.page = 1
  loadNotifications()
}

const handleReset = () => {
  searchForm.name = ''
  searchForm.type = ''
  searchForm.is_enabled = undefined
  pagination.page = 1
  loadNotifications()
}

const handleSizeChange = (size: number) => {
  pagination.pageSize = size
  pagination.page = 1
  loadNotifications()
}

const handleCurrentChange = (page: number) => {
  pagination.page = page
  loadNotifications()
}

const showCreateDialog = () => {
  isEdit.value = false
  resetForm()
  dialogVisible.value = true
}

const editNotification = (notification: NotificationChannel) => {
  isEdit.value = true
  Object.assign(formData, {
    name: notification.name,
    description: notification.description,
    type: notification.type,
    config: { ...notification.config },
    is_enabled: notification.is_enabled
  })
  dialogVisible.value = true
}

const toggleNotification = async (notification: NotificationChannel) => {
  try {
    await notificationChannelsApi.toggleNotificationChannel(notification.id)
    ElMessage.success(`通知配置已${notification.is_enabled ? '启用' : '禁用'}`)
  } catch (error) {
    console.error('切换通知渠道状态失败:', error)
    ElMessage.error('操作失败')
    notification.is_enabled = !notification.is_enabled
  }
}

const testNotification = (notification: NotificationChannel) => {
  currentNotification.value = notification
  testForm.title = '测试通知'
  testForm.content = `这是一条来自 ${notification.name} 的测试消息，发送时间：${new Date().toLocaleString()}`
  testForm.recipient = ''
  testDialogVisible.value = true
}

const sendTestNotification = async () => {
  if (!currentNotification.value) return
  
  try {
    await notificationChannelsApi.testNotificationChannel(currentNotification.value.id, {
      title: testForm.title,
      content: testForm.content,
      recipient: testForm.recipient
    })
    ElMessage.success('测试通知发送成功')
    testDialogVisible.value = false
  } catch (error) {
    console.error('测试通知发送失败:', error)
    ElMessage.error('测试通知发送失败')
  }
}

const deleteNotification = async (notification: NotificationChannel) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除通知配置 "${notification.name}" 吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await notificationChannelsApi.deleteNotificationChannel(notification.id)
    
    const index = notifications.value.findIndex(n => n.id === notification.id)
    if (index > -1) {
      notifications.value.splice(index, 1)
      pagination.total--
    }
    
    ElMessage.success('删除成功')
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除通知渠道失败:', error)
      ElMessage.error('删除失败')
    }
  }
}

const submitForm = async () => {
  if (!formRef.value) return
  
  try {
    await formRef.value.validate()
    
    if (isEdit.value && currentNotification.value) {
      await notificationChannelsApi.updateNotificationChannel(currentNotification.value.id, formData)
      ElMessage.success('更新成功')
    } else {
      await notificationChannelsApi.createNotificationChannel(formData)
      ElMessage.success('创建成功')
    }
    
    dialogVisible.value = false
    loadNotifications()
  } catch (error) {
    console.error('提交表单失败:', error)
    ElMessage.error(isEdit.value ? '更新失败' : '创建失败')
  }
}

const onTypeChange = () => {
  formData.config = {}
  
  // 设置默认配置
  if (formData.type === 'email') {
    formData.config = {
      smtp_host: '',
      smtp_port: 587,
      username: '',
      password: '',
      from_email: '',
      use_tls: true
    }
  } else if (formData.type === 'sms') {
    formData.config = {
      provider: '',
      access_key: '',
      secret_key: '',
      sign_name: ''
    }
  } else if (formData.type === 'webhook') {
    formData.config = {
      url: '',
      method: 'POST',
      headers: '{}'
    }
  } else if (formData.type === 'dingtalk') {
    formData.config = {
      robot_name: '',
      webhook_url: '',
      secret: ''
    }
  } else if (formData.type === 'wechat') {
    formData.config = {
      corp_id: '',
      corp_secret: '',
      agent_id: ''
    }
  }
}

const resetForm = () => {
  Object.assign(formData, {
    name: '',
    description: '',
    type: '',
    config: {},
    is_enabled: true
  })
}

// 辅助函数
const getTypeColor = (type: string) => {
  const colors: Record<string, string> = {
    email: 'primary',
    sms: 'success',
    wechat: 'success',
    dingtalk: 'info',
    webhook: 'warning'
  }
  return colors[type] || 'info'
}

const getTypeName = (type: string) => {
  const names: Record<string, string> = {
    email: '邮件',
    sms: '短信',
    wechat: '微信',
    dingtalk: '钉钉',
    webhook: 'Webhook'
  }
  return names[type] || type
}

const getTypeIcon = (type: string) => {
  const icons: Record<string, any> = {
    email: ChatDotRound,
    sms: Phone,
    wechat: ChatLineRound,
    dingtalk: Monitor,
    webhook: Link
  }
  return icons[type] || ChatDotRound
}

const formatDateTime = (dateTime: string) => {
  return dateTime
}

// 生命周期
onMounted(() => {
  loadNotifications()
})
</script>

<style scoped>
.event-notifications {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header-left h2 {
  margin: 0;
  color: #303133;
}

.page-description {
  margin: 5px 0 0 0;
  color: #909399;
  font-size: 14px;
}

.stats-cards {
  margin-bottom: 20px;
}

.stat-card {
  position: relative;
  overflow: hidden;
}

.stat-card :deep(.el-card__body) {
  padding: 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 28px;
  font-weight: bold;
  color: #303133;
  line-height: 1;
}

.stat-label {
  font-size: 14px;
  color: #909399;
  margin-top: 8px;
}

.stat-icon {
  font-size: 40px;
  opacity: 0.8;
}

.search-card {
  margin-bottom: 20px;
}

.table-card {
  margin-bottom: 20px;
}

.pagination-wrapper {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}

.config-info {
  font-size: 12px;
  color: #606266;
}

.config-label {
  font-weight: bold;
  color: #303133;
}

.send-stats {
  font-size: 12px;
  color: #606266;
}

.send-stats div {
  margin-bottom: 2px;
}
</style>