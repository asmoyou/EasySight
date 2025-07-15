<template>
  <div class="notification-channels">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <h2>通知设置</h2>
        <p class="page-description">管理告警通知渠道，配置邮件、短信、Webhook等通知方式</p>
      </div>
      <div class="header-right">
        <el-button type="primary" @click="handleCreate">
          <el-icon><Plus /></el-icon>
          新建渠道
        </el-button>
      </div>
    </div>

    <!-- 搜索和筛选 -->
    <div class="search-filters">
      <div class="search-bar">
        <el-input
          v-model="searchForm.search"
          placeholder="搜索渠道名称或描述"
          clearable
          @keyup.enter="handleSearch"
          style="width: 300px"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        <el-button type="primary" @click="handleSearch">
          <el-icon><Search /></el-icon>
          搜索
        </el-button>
        <el-button @click="handleReset">
          <el-icon><Refresh /></el-icon>
          重置
        </el-button>
      </div>
      
      <div class="filter-bar">
        <el-select v-model="searchForm.type" placeholder="渠道类型" clearable style="width: 150px">
          <el-option label="邮件" value="email" />
          <el-option label="短信" value="sms" />
          <el-option label="Webhook" value="webhook" />
          <el-option label="钉钉" value="dingtalk" />
          <el-option label="微信" value="wechat" />
        </el-select>
        
        <el-select v-model="searchForm.is_enabled" placeholder="启用状态" clearable style="width: 120px">
          <el-option label="已启用" :value="true" />
          <el-option label="已禁用" :value="false" />
        </el-select>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-cards">
      <el-row :gutter="20">
        <el-col :span="6">
          <div class="stat-card">
            <div class="stat-icon enabled">
              <el-icon><Check /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ stats.enabled_count }}</div>
              <div class="stat-label">已启用渠道</div>
            </div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-card">
            <div class="stat-icon sent">
              <el-icon><Message /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ stats.sent_today }}</div>
              <div class="stat-label">今日发送</div>
            </div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-card">
            <div class="stat-icon success">
              <el-icon><CircleCheck /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ stats.success_rate }}%</div>
              <div class="stat-label">成功率</div>
            </div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-card">
            <div class="stat-icon total">
              <el-icon><DataBoard /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ stats.total_count }}</div>
              <div class="stat-label">总渠道数</div>
            </div>
          </div>
        </el-col>
      </el-row>
    </div>

    <!-- 渠道列表 -->
    <div class="table-container">
      <el-table
        :data="channels"
        v-loading="loading"
        stripe
        style="width: 100%"
      >
        <el-table-column prop="name" label="渠道名称" min-width="200">
          <template #default="{ row }">
            <div class="channel-name">
              <el-icon class="channel-icon" :class="getChannelIconClass(row.type)">
                <component :is="getChannelIcon(row.type)" />
              </el-icon>
              <span class="name">{{ row.name }}</span>
              <el-tag v-if="!row.is_enabled" type="info" size="small">已禁用</el-tag>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column prop="type" label="类型" width="100">
          <template #default="{ row }">
            <el-tag :type="getChannelTypeColor(row.type)" size="small">
              {{ getChannelTypeName(row.type) }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column label="配置信息" min-width="250">
          <template #default="{ row }">
            <div class="config-info">
              <div v-if="row.type === 'email'" class="config-item">
                <span class="label">SMTP服务器:</span>
                <span class="value">{{ row.config?.smtp_host || '未配置' }}</span>
              </div>
              <div v-else-if="row.type === 'sms'" class="config-item">
                <span class="label">服务商:</span>
                <span class="value">{{ row.config?.provider || '未配置' }}</span>
              </div>
              <div v-else-if="row.type === 'webhook'" class="config-item">
                <span class="label">URL:</span>
                <span class="value">{{ row.config?.url || '未配置' }}</span>
              </div>
              <div v-else-if="row.type === 'dingtalk'" class="config-item">
                <span class="label">Webhook:</span>
                <span class="value">{{ row.config?.webhook_url ? '已配置' : '未配置' }}</span>
              </div>
              <div v-else-if="row.type === 'wechat'" class="config-item">
                <span class="label">企业ID:</span>
                <span class="value">{{ row.config?.corp_id || '未配置' }}</span>
              </div>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column label="发送统计" width="120">
          <template #default="{ row }">
            <div class="send-stats">
              <div class="stat-item">
                <span class="label">今日:</span>
                <span class="value">{{ row.stats?.sent_today || 0 }}</span>
              </div>
              <div class="stat-item">
                <span class="label">成功率:</span>
                <span class="value">{{ row.stats?.success_rate || 0 }}%</span>
              </div>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column prop="is_enabled" label="状态" width="80">
          <template #default="{ row }">
            <el-switch
              v-model="row.is_enabled"
              @change="handleToggleEnabled(row)"
            />
          </template>
        </el-table-column>
        
        <el-table-column prop="created_at" label="创建时间" width="150">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="250" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="handleEdit(row)">编辑</el-button>
            <el-button size="small" type="primary" @click="handleTest(row)">测试</el-button>
            <el-button size="small" @click="handleViewLogs(row)">日志</el-button>
            <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <!-- 分页 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </div>

    <!-- 创建/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑通知渠道' : '新建通知渠道'"
      width="800px"
      @close="handleDialogClose"
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="formRules"
        label-width="120px"
      >
        <el-form-item label="渠道名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入渠道名称" />
        </el-form-item>
        
        <el-form-item label="渠道类型" prop="type">
          <el-select v-model="form.type" placeholder="请选择渠道类型" style="width: 100%" @change="handleTypeChange">
            <el-option label="邮件" value="email" />
            <el-option label="短信" value="sms" />
            <el-option label="Webhook" value="webhook" />
            <el-option label="钉钉" value="dingtalk" />
            <el-option label="微信" value="wechat" />
          </el-select>
        </el-form-item>
        
        <!-- 邮件配置 -->
        <template v-if="form.type === 'email'">
          <el-form-item label="SMTP服务器" prop="config.smtp_host">
            <el-input v-model="form.config.smtp_host" placeholder="如: smtp.qq.com" />
          </el-form-item>
          <el-form-item label="SMTP端口" prop="config.smtp_port">
            <el-input-number v-model="form.config.smtp_port" :min="1" :max="65535" placeholder="如: 587" />
          </el-form-item>
          <el-form-item label="发送邮箱" prop="config.smtp_user">
            <el-input v-model="form.config.smtp_user" placeholder="发送邮箱地址" />
          </el-form-item>
          <el-form-item label="邮箱密码" prop="config.smtp_password">
            <el-input v-model="form.config.smtp_password" type="password" placeholder="邮箱密码或授权码" show-password />
          </el-form-item>
          <el-form-item label="启用TLS">
            <el-switch v-model="form.config.use_tls" />
          </el-form-item>
          <el-form-item label="收件人" prop="config.recipients">
            <el-input v-model="form.config.recipients" type="textarea" :rows="3" placeholder="多个邮箱用逗号分隔" />
          </el-form-item>
        </template>
        
        <!-- 短信配置 -->
        <template v-if="form.type === 'sms'">
          <el-form-item label="服务商" prop="config.provider">
            <el-select v-model="form.config.provider" placeholder="选择短信服务商" style="width: 100%">
              <el-option label="阿里云" value="aliyun" />
              <el-option label="腾讯云" value="tencent" />
              <el-option label="华为云" value="huawei" />
            </el-select>
          </el-form-item>
          <el-form-item label="Access Key" prop="config.access_key">
            <el-input v-model="form.config.access_key" placeholder="Access Key" />
          </el-form-item>
          <el-form-item label="Secret Key" prop="config.secret_key">
            <el-input v-model="form.config.secret_key" type="password" placeholder="Secret Key" show-password />
          </el-form-item>
          <el-form-item label="签名" prop="config.sign_name">
            <el-input v-model="form.config.sign_name" placeholder="短信签名" />
          </el-form-item>
          <el-form-item label="模板ID" prop="config.template_code">
            <el-input v-model="form.config.template_code" placeholder="短信模板ID" />
          </el-form-item>
          <el-form-item label="手机号" prop="config.phone_numbers">
            <el-input v-model="form.config.phone_numbers" type="textarea" :rows="3" placeholder="多个手机号用逗号分隔" />
          </el-form-item>
        </template>
        
        <!-- Webhook配置 -->
        <template v-if="form.type === 'webhook'">
          <el-form-item label="Webhook URL" prop="config.url">
            <el-input v-model="form.config.url" placeholder="https://example.com/webhook" />
          </el-form-item>
          <el-form-item label="请求方法" prop="config.method">
            <el-select v-model="form.config.method" placeholder="选择请求方法" style="width: 100%">
              <el-option label="POST" value="POST" />
              <el-option label="PUT" value="PUT" />
              <el-option label="PATCH" value="PATCH" />
            </el-select>
          </el-form-item>
          <el-form-item label="请求头">
            <el-input v-model="form.config.headers" type="textarea" :rows="3" placeholder="JSON格式，如: {\"Content-Type\": \"application/json\"}" />
          </el-form-item>
          <el-form-item label="超时时间(秒)">
            <el-input-number v-model="form.config.timeout" :min="1" :max="300" placeholder="30" />
          </el-form-item>
        </template>
        
        <!-- 钉钉配置 -->
        <template v-if="form.type === 'dingtalk'">
          <el-form-item label="Webhook URL" prop="config.webhook_url">
            <el-input v-model="form.config.webhook_url" placeholder="钉钉机器人Webhook地址" />
          </el-form-item>
          <el-form-item label="加签密钥">
            <el-input v-model="form.config.secret" placeholder="机器人加签密钥（可选）" />
          </el-form-item>
          <el-form-item label="@所有人">
            <el-switch v-model="form.config.at_all" />
          </el-form-item>
          <el-form-item label="@指定人员">
            <el-input v-model="form.config.at_mobiles" placeholder="手机号，多个用逗号分隔" />
          </el-form-item>
        </template>
        
        <!-- 微信配置 -->
        <template v-if="form.type === 'wechat'">
          <el-form-item label="企业ID" prop="config.corp_id">
            <el-input v-model="form.config.corp_id" placeholder="企业微信Corp ID" />
          </el-form-item>
          <el-form-item label="应用Secret" prop="config.corp_secret">
            <el-input v-model="form.config.corp_secret" type="password" placeholder="应用Secret" show-password />
          </el-form-item>
          <el-form-item label="应用ID" prop="config.agent_id">
            <el-input v-model="form.config.agent_id" placeholder="应用Agent ID" />
          </el-form-item>
          <el-form-item label="接收人">
            <el-input v-model="form.config.to_user" placeholder="用户ID，多个用|分隔，@all表示全部" />
          </el-form-item>
        </template>
        
        <el-form-item label="启用状态">
          <el-switch v-model="form.is_enabled" />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleSubmit" :loading="submitting">
            {{ isEdit ? '更新' : '创建' }}
          </el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 日志对话框 -->
    <el-dialog
      v-model="logsVisible"
      title="通知日志"
      width="1000px"
    >
      <el-table :data="logs" v-loading="logsLoading" stripe>
        <el-table-column prop="title" label="标题" min-width="200" />
        <el-table-column prop="recipient" label="接收人" width="150" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 'SUCCESS' ? 'success' : 'danger'" size="small">
              {{ row.status === 'SUCCESS' ? '成功' : '失败' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="error_message" label="错误信息" min-width="200" show-overflow-tooltip />
        <el-table-column prop="sent_at" label="发送时间" width="150">
          <template #default="{ row }">
            {{ formatDateTime(row.sent_at) }}
          </template>
        </el-table-column>
      </el-table>
      
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="logsCurrentPage"
          v-model:page-size="logsPageSize"
          :page-sizes="[10, 20, 50]"
          :total="logsTotal"
          layout="total, sizes, prev, pager, next"
          @size-change="handleLogsPageSizeChange"
          @current-change="handleLogsCurrentChange"
        />
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  Search, Refresh, Plus, Check, Message, CircleCheck, DataBoard,
  Message as MessageIcon, Phone, Link, ChatDotRound, Wechat
} from '@element-plus/icons-vue'
import { formatDateTime } from '@/utils/date'

// 类型定义
interface NotificationChannel {
  id?: number
  name: string
  type: string
  config: Record<string, any>
  is_enabled: boolean
  stats?: {
    sent_today: number
    success_rate: number
  }
  created_at?: string
  updated_at?: string
}

interface NotificationLog {
  id: number
  title: string
  recipient: string
  status: string
  error_message?: string
  sent_at: string
}

// 响应式数据
const loading = ref(false)
const submitting = ref(false)
const logsLoading = ref(false)
const channels = ref<NotificationChannel[]>([])
const logs = ref<NotificationLog[]>([])

// 分页
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)

const logsCurrentPage = ref(1)
const logsPageSize = ref(20)
const logsTotal = ref(0)

// 搜索表单
const searchForm = reactive({
  search: '',
  type: '',
  is_enabled: null as boolean | null
})

// 统计数据
const stats = ref({
  enabled_count: 0,
  sent_today: 0,
  success_rate: 0,
  total_count: 0
})

// 对话框
const dialogVisible = ref(false)
const logsVisible = ref(false)
const isEdit = ref(false)
const formRef = ref()
const currentChannelId = ref<number>()

// 表单数据
const form = reactive<NotificationChannel>({
  name: '',
  type: '',
  config: {},
  is_enabled: true
})

// 表单验证规则
const formRules = {
  name: [{ required: true, message: '请输入渠道名称', trigger: 'blur' }],
  type: [{ required: true, message: '请选择渠道类型', trigger: 'change' }]
}

// 计算属性和方法
const getChannelTypeName = (type: string) => {
  const typeMap: Record<string, string> = {
    email: '邮件',
    sms: '短信',
    webhook: 'Webhook',
    dingtalk: '钉钉',
    wechat: '微信'
  }
  return typeMap[type] || type
}

const getChannelTypeColor = (type: string) => {
  const colorMap: Record<string, string> = {
    email: 'primary',
    sms: 'success',
    webhook: 'warning',
    dingtalk: 'info',
    wechat: 'success'
  }
  return colorMap[type] || ''
}

const getChannelIcon = (type: string) => {
  const iconMap: Record<string, any> = {
    email: MessageIcon,
    sms: Phone,
    webhook: Link,
    dingtalk: ChatDotRound,
    wechat: Wechat
  }
  return iconMap[type] || MessageIcon
}

const getChannelIconClass = (type: string) => {
  const classMap: Record<string, string> = {
    email: 'email-icon',
    sms: 'sms-icon',
    webhook: 'webhook-icon',
    dingtalk: 'dingtalk-icon',
    wechat: 'wechat-icon'
  }
  return classMap[type] || ''
}

// 方法
const loadChannels = async () => {
  loading.value = true
  try {
    // TODO: 调用API获取通知渠道列表
    // const response = await notificationChannelApi.getChannels({
    //   page: currentPage.value,
    //   size: pageSize.value,
    //   ...searchForm
    // })
    // channels.value = response.data.items
    // total.value = response.data.total
    
    // 模拟数据
    channels.value = [
      {
        id: 1,
        name: '系统邮件通知',
        type: 'email',
        config: {
          smtp_host: 'smtp.qq.com',
          smtp_port: 587,
          smtp_user: 'system@example.com',
          recipients: 'admin@example.com,ops@example.com'
        },
        is_enabled: true,
        stats: { sent_today: 15, success_rate: 98 },
        created_at: '2024-01-15 10:30:00'
      },
      {
        id: 2,
        name: '紧急短信通知',
        type: 'sms',
        config: {
          provider: 'aliyun',
          sign_name: 'EasySight',
          template_code: 'SMS_123456',
          phone_numbers: '13800138000,13900139000'
        },
        is_enabled: true,
        stats: { sent_today: 3, success_rate: 100 },
        created_at: '2024-01-15 11:00:00'
      }
    ]
    total.value = 2
  } catch (error) {
    ElMessage.error('加载通知渠道失败')
  } finally {
    loading.value = false
  }
}

const loadStats = async () => {
  try {
    // TODO: 调用API获取统计数据
    stats.value = {
      enabled_count: 5,
      sent_today: 28,
      success_rate: 96,
      total_count: 6
    }
  } catch (error) {
    console.error('加载统计数据失败:', error)
  }
}

const loadLogs = async (channelId: number) => {
  logsLoading.value = true
  try {
    // TODO: 调用API获取通知日志
    logs.value = [
      {
        id: 1,
        title: '亮度异常告警',
        recipient: 'admin@example.com',
        status: 'SUCCESS',
        sent_at: '2024-01-15 14:30:00'
      },
      {
        id: 2,
        title: '蓝屏检测告警',
        recipient: 'ops@example.com',
        status: 'FAILED',
        error_message: 'SMTP连接超时',
        sent_at: '2024-01-15 14:25:00'
      }
    ]
    logsTotal.value = 2
  } catch (error) {
    ElMessage.error('加载通知日志失败')
  } finally {
    logsLoading.value = false
  }
}

const handleSearch = () => {
  currentPage.value = 1
  loadChannels()
}

const handleReset = () => {
  Object.assign(searchForm, {
    search: '',
    type: '',
    is_enabled: null
  })
  handleSearch()
}

const handleSizeChange = (size: number) => {
  pageSize.value = size
  loadChannels()
}

const handleCurrentChange = (page: number) => {
  currentPage.value = page
  loadChannels()
}

const handleLogsPageSizeChange = (size: number) => {
  logsPageSize.value = size
  if (currentChannelId.value) {
    loadLogs(currentChannelId.value)
  }
}

const handleLogsCurrentChange = (page: number) => {
  logsCurrentPage.value = page
  if (currentChannelId.value) {
    loadLogs(currentChannelId.value)
  }
}

const handleCreate = () => {
  isEdit.value = false
  resetForm()
  dialogVisible.value = true
}

const handleEdit = (channel: NotificationChannel) => {
  isEdit.value = true
  Object.assign(form, JSON.parse(JSON.stringify(channel)))
  dialogVisible.value = true
}

const handleDelete = async (channel: NotificationChannel) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除通知渠道"${channel.name}"吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    // TODO: 调用API删除渠道
    ElMessage.success('删除成功')
    loadChannels()
    loadStats()
  } catch (error) {
    // 用户取消删除
  }
}

const handleToggleEnabled = async (channel: NotificationChannel) => {
  try {
    // TODO: 调用API切换启用状态
    ElMessage.success(channel.is_enabled ? '渠道已启用' : '渠道已禁用')
    loadStats()
  } catch (error) {
    ElMessage.error('操作失败')
    channel.is_enabled = !channel.is_enabled // 回滚状态
  }
}

const handleTest = async (channel: NotificationChannel) => {
  try {
    // TODO: 调用API测试通知
    ElMessage.success('测试通知已发送')
  } catch (error) {
    ElMessage.error('测试失败')
  }
}

const handleViewLogs = (channel: NotificationChannel) => {
  currentChannelId.value = channel.id
  logsCurrentPage.value = 1
  loadLogs(channel.id!)
  logsVisible.value = true
}

const handleTypeChange = () => {
  // 重置配置
  form.config = {}
  
  // 根据类型设置默认配置
  switch (form.type) {
    case 'email':
      form.config = {
        smtp_port: 587,
        use_tls: true
      }
      break
    case 'webhook':
      form.config = {
        method: 'POST',
        timeout: 30
      }
      break
    case 'dingtalk':
      form.config = {
        at_all: false
      }
      break
  }
}

const handleSubmit = async () => {
  try {
    await formRef.value.validate()
    
    submitting.value = true
    
    if (isEdit.value) {
      // TODO: 调用API更新渠道
      ElMessage.success('更新成功')
    } else {
      // TODO: 调用API创建渠道
      ElMessage.success('创建成功')
    }
    
    dialogVisible.value = false
    loadChannels()
    loadStats()
  } catch (error) {
    console.error('提交失败:', error)
  } finally {
    submitting.value = false
  }
}

const handleDialogClose = () => {
  formRef.value?.resetFields()
  resetForm()
}

const resetForm = () => {
  Object.assign(form, {
    name: '',
    type: '',
    config: {},
    is_enabled: true
  })
}

// 生命周期
onMounted(() => {
  loadChannels()
  loadStats()
})
</script>

<style scoped>
.notification-channels {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header-left h2 {
  margin: 0 0 5px 0;
  color: #303133;
}

.page-description {
  margin: 0;
  color: #909399;
  font-size: 14px;
}

.search-filters {
  background: #fff;
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.search-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 15px;
}

.filter-bar {
  display: flex;
  align-items: center;
  gap: 15px;
}

.stats-cards {
  margin-bottom: 20px;
}

.stat-card {
  background: #fff;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  display: flex;
  align-items: center;
}

.stat-icon {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 15px;
  font-size: 24px;
  color: #fff;
}

.stat-icon.enabled {
  background: linear-gradient(135deg, #67c23a, #85ce61);
}

.stat-icon.sent {
  background: linear-gradient(135deg, #409eff, #66b1ff);
}

.stat-icon.success {
  background: linear-gradient(135deg, #67c23a, #85ce61);
}

.stat-icon.total {
  background: linear-gradient(135deg, #909399, #b1b3b8);
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
  margin-top: 5px;
}

.table-container {
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.channel-name {
  display: flex;
  align-items: center;
  gap: 8px;
}

.channel-icon {
  font-size: 16px;
}

.channel-icon.email-icon {
  color: #409eff;
}

.channel-icon.sms-icon {
  color: #67c23a;
}

.channel-icon.webhook-icon {
  color: #e6a23c;
}

.channel-icon.dingtalk-icon {
  color: #409eff;
}

.channel-icon.wechat-icon {
  color: #67c23a;
}

.channel-name .name {
  font-weight: 500;
}

.config-info {
  font-size: 12px;
}

.config-item {
  margin-bottom: 2px;
}

.config-item .label {
  color: #909399;
  margin-right: 4px;
}

.config-item .value {
  font-weight: 500;
}

.send-stats {
  font-size: 12px;
}

.stat-item {
  margin-bottom: 2px;
}

.stat-item .label {
  color: #909399;
  margin-right: 4px;
}

.stat-item .value {
  font-weight: 500;
}

.pagination-container {
  padding: 20px;
  text-align: right;
}

.dialog-footer {
  text-align: right;
}
</style>