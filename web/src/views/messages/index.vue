<template>
  <div class="messages-container">
    <el-card class="page-card">
      <template #header>
        <div class="card-header">
          <h2>消息中心</h2>
          <div class="header-actions">
            <el-button
              v-if="unreadCount > 0"
              type="primary"
              @click="markAllRead"
              :loading="markingAllRead"
            >
              全部已读 ({{ unreadCount }})
            </el-button>
            <el-button @click="refreshMessages" :loading="loading">
              <el-icon><Refresh /></el-icon>
              刷新
            </el-button>
          </div>
        </div>
      </template>

      <!-- 筛选条件 -->
      <div class="filter-bar">
        <el-form :model="filterForm" inline>
          <el-form-item label="消息类型">
            <el-select v-model="filterForm.message_type" placeholder="全部类型" clearable>
              <el-option label="信息" value="info" />
              <el-option label="警告" value="warning" />
              <el-option label="错误" value="error" />
              <el-option label="成功" value="success" />
            </el-select>
          </el-form-item>
          <el-form-item label="分类">
            <el-select v-model="filterForm.category" placeholder="全部分类" clearable>
              <el-option label="系统通知" value="system" />
              <el-option label="安全告警" value="security" />
              <el-option label="设备状态" value="device" />
              <el-option label="用户操作" value="user" />
            </el-select>
          </el-form-item>
          <el-form-item label="状态">
            <el-select v-model="filterForm.is_read" placeholder="全部状态" clearable>
              <el-option label="未读" :value="false" />
              <el-option label="已读" :value="true" />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="handleFilter">
              <el-icon><Search /></el-icon>
              筛选
            </el-button>
            <el-button @click="resetFilter">
              <el-icon><RefreshLeft /></el-icon>
              重置
            </el-button>
          </el-form-item>
        </el-form>
      </div>

      <!-- 消息列表 -->
      <div class="message-list" v-loading="loading">
        <div v-if="messages.length === 0" class="empty-state">
          <el-empty description="暂无消息" :image-size="120" />
        </div>
        <div v-else>
          <div
            v-for="message in messages"
            :key="message.id"
            class="message-item"
            :class="{ 'unread': !message.is_read }"
          >
            <div class="message-checkbox">
              <el-checkbox
                v-model="selectedMessages"
                :label="message.id"
                @change="handleSelectionChange"
              />
            </div>
            
            <div class="message-icon">
              <el-icon
                :class="getMessageIconClass(message.message_type)"
                :color="getMessageIconColor(message.message_type)"
                :size="20"
              >
                <component :is="getMessageIcon(message.message_type)" />
              </el-icon>
            </div>
            
            <div class="message-content" @click="handleMessageClick(message)">
              <div class="message-header">
                <h4 class="message-title">{{ message.title }}</h4>
                <div class="message-meta">
                  <el-tag
                    :type="getMessageTagType(message.message_type)"
                    size="small"
                  >
                    {{ getMessageTypeText(message.message_type) }}
                  </el-tag>
                  <el-tag
                    v-if="message.category"
                    type="info"
                    size="small"
                    effect="plain"
                  >
                    {{ getCategoryText(message.category) }}
                  </el-tag>
                  <span class="message-time">{{ formatTime(message.created_at) }}</span>
                </div>
              </div>
              <div class="message-text">{{ message.content }}</div>
              <div v-if="message.sender_name" class="message-sender">
                发送者: {{ message.sender_name }}
              </div>
            </div>
            
            <div class="message-actions">
              <el-button
                v-if="!message.is_read"
                type="text"
                size="small"
                @click="markMessageRead(message)"
              >
                标记已读
              </el-button>
              <el-button
                type="text"
                size="small"
                @click="deleteMessage(message)"
                class="delete-btn"
              >
                删除
              </el-button>
            </div>
            
            <div v-if="!message.is_read" class="unread-indicator"></div>
          </div>
        </div>
      </div>

      <!-- 批量操作 -->
      <div v-if="selectedMessages.length > 0" class="batch-actions">
        <div class="selected-info">
          已选择 {{ selectedMessages.length }} 条消息
        </div>
        <div class="actions">
          <el-button
            type="primary"
            size="small"
            @click="batchMarkRead"
            :loading="batchOperating"
          >
            批量已读
          </el-button>
          <el-button
            type="danger"
            size="small"
            @click="batchDelete"
            :loading="batchOperating"
          >
            批量删除
          </el-button>
          <el-button size="small" @click="clearSelection">
            取消选择
          </el-button>
        </div>
      </div>

      <!-- 分页 -->
      <div class="pagination-wrapper">
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
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Refresh,
  Search,
  RefreshLeft,
  InfoFilled,
  WarningFilled,
  CircleCloseFilled,
  CircleCheckFilled
} from '@element-plus/icons-vue'
import { messagesApi, type Message } from '@/api/messages'
import { formatDistanceToNow } from 'date-fns'
import { zhCN } from 'date-fns/locale'

// 响应式数据
const messages = ref<Message[]>([])
const selectedMessages = ref<number[]>([])
const loading = ref(false)
const markingAllRead = ref(false)
const batchOperating = ref(false)
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)
const unreadCount = ref(0)

// 筛选表单
const filterForm = ref({
  message_type: '',
  category: '',
  is_read: undefined as boolean | undefined
})

// 获取消息列表
const fetchMessages = async () => {
  try {
    loading.value = true
    const params = {
      page: currentPage.value,
      page_size: pageSize.value,
      ...filterForm.value
    }
    
    // 移除空值
    Object.keys(params).forEach(key => {
      if (params[key] === '' || params[key] === undefined) {
        delete params[key]
      }
    })
    
    const { data } = await messagesApi.getMessages(params)
    messages.value = data.messages
    total.value = data.total
    unreadCount.value = data.unread_count
  } catch (error) {
    console.error('获取消息失败:', error)
    ElMessage.error('获取消息失败')
  } finally {
    loading.value = false
  }
}

// 刷新消息
const refreshMessages = () => {
  currentPage.value = 1
  fetchMessages()
}

// 筛选
const handleFilter = () => {
  currentPage.value = 1
  fetchMessages()
}

// 重置筛选
const resetFilter = () => {
  filterForm.value = {
    message_type: '',
    category: '',
    is_read: undefined
  }
  currentPage.value = 1
  fetchMessages()
}

// 标记所有消息为已读
const markAllRead = async () => {
  try {
    markingAllRead.value = true
    await messagesApi.markAllMessagesRead()
    messages.value.forEach(msg => {
      msg.is_read = true
    })
    unreadCount.value = 0
    ElMessage.success('已标记所有消息为已读')
  } catch (error) {
    console.error('标记已读失败:', error)
    ElMessage.error('标记已读失败')
  } finally {
    markingAllRead.value = false
  }
}

// 标记单条消息为已读
const markMessageRead = async (message: Message) => {
  try {
    await messagesApi.markMessagesRead({ message_ids: [message.id] })
    message.is_read = true
    unreadCount.value = Math.max(0, unreadCount.value - 1)
    ElMessage.success('已标记为已读')
  } catch (error) {
    console.error('标记已读失败:', error)
    ElMessage.error('标记已读失败')
  }
}

// 删除消息
const deleteMessage = async (message: Message) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除消息"${message.title}"吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await messagesApi.deleteMessage(message.id)
    ElMessage.success('删除成功')
    fetchMessages()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除消息失败:', error)
      ElMessage.error('删除失败')
    }
  }
}

// 处理消息点击
const handleMessageClick = async (message: Message) => {
  if (!message.is_read) {
    await markMessageRead(message)
  }
}

// 处理选择变化
const handleSelectionChange = () => {
  // 选择变化时的处理逻辑
}

// 批量标记已读
const batchMarkRead = async () => {
  if (selectedMessages.value.length === 0) return
  
  try {
    batchOperating.value = true
    await messagesApi.markMessagesRead({ message_ids: selectedMessages.value })
    
    // 更新本地状态
    messages.value.forEach(msg => {
      if (selectedMessages.value.includes(msg.id)) {
        msg.is_read = true
      }
    })
    
    // 重新计算未读数量
    unreadCount.value = messages.value.filter(msg => !msg.is_read).length
    
    selectedMessages.value = []
    ElMessage.success('批量标记已读成功')
  } catch (error) {
    console.error('批量标记已读失败:', error)
    ElMessage.error('批量标记已读失败')
  } finally {
    batchOperating.value = false
  }
}

// 批量删除
const batchDelete = async () => {
  if (selectedMessages.value.length === 0) return
  
  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${selectedMessages.value.length} 条消息吗？`,
      '确认批量删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    batchOperating.value = true
    
    // 逐个删除消息
    for (const messageId of selectedMessages.value) {
      await messagesApi.deleteMessage(messageId)
    }
    
    selectedMessages.value = []
    ElMessage.success('批量删除成功')
    fetchMessages()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('批量删除失败:', error)
      ElMessage.error('批量删除失败')
    }
  } finally {
    batchOperating.value = false
  }
}

// 清除选择
const clearSelection = () => {
  selectedMessages.value = []
}

// 分页处理
const handleSizeChange = (val: number) => {
  pageSize.value = val
  currentPage.value = 1
  fetchMessages()
}

const handleCurrentChange = (val: number) => {
  currentPage.value = val
  fetchMessages()
}

// 工具函数
const getMessageIcon = (type: string) => {
  switch (type) {
    case 'info':
      return InfoFilled
    case 'warning':
      return WarningFilled
    case 'error':
      return CircleCloseFilled
    case 'success':
      return CircleCheckFilled
    default:
      return InfoFilled
  }
}

const getMessageIconColor = (type: string) => {
  switch (type) {
    case 'info':
      return '#409EFF'
    case 'warning':
      return '#E6A23C'
    case 'error':
      return '#F56C6C'
    case 'success':
      return '#67C23A'
    default:
      return '#409EFF'
  }
}

const getMessageIconClass = (type: string) => {
  return `message-icon-${type}`
}

const getMessageTagType = (type: string) => {
  switch (type) {
    case 'info':
      return 'primary'
    case 'warning':
      return 'warning'
    case 'error':
      return 'danger'
    case 'success':
      return 'success'
    default:
      return 'primary'
  }
}

const getMessageTypeText = (type: string) => {
  switch (type) {
    case 'info':
      return '信息'
    case 'warning':
      return '警告'
    case 'error':
      return '错误'
    case 'success':
      return '成功'
    default:
      return '信息'
  }
}

const getCategoryText = (category: string) => {
  switch (category) {
    case 'system':
      return '系统通知'
    case 'security':
      return '安全告警'
    case 'device':
      return '设备状态'
    case 'user':
      return '用户操作'
    default:
      return category
  }
}

const formatTime = (time: string) => {
  return formatDistanceToNow(new Date(time), {
    addSuffix: true,
    locale: zhCN
  })
}

onMounted(() => {
  fetchMessages()
})
</script>

<style scoped>
.messages-container {
  padding: 20px;
}

.page-card {
  min-height: calc(100vh - 120px);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header h2 {
  margin: 0;
  color: var(--el-text-color-primary);
}

.header-actions {
  display: flex;
  gap: 12px;
}

.filter-bar {
  margin-bottom: 20px;
  padding: 16px;
  background: var(--el-fill-color-lighter);
  border-radius: 8px;
}

.message-list {
  min-height: 400px;
}

.empty-state {
  padding: 60px 0;
  text-align: center;
}

.message-item {
  display: flex;
  align-items: flex-start;
  padding: 16px;
  margin-bottom: 12px;
  border: 1px solid var(--el-border-color-light);
  border-radius: 8px;
  background: var(--el-bg-color);
  transition: all 0.3s;
  position: relative;
}

.message-item:hover {
  border-color: var(--el-color-primary-light-7);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.message-item.unread {
  background: var(--el-color-primary-light-9);
  border-color: var(--el-color-primary-light-7);
}

.message-checkbox {
  margin-right: 12px;
  margin-top: 4px;
}

.message-icon {
  margin-right: 16px;
  margin-top: 4px;
}

.message-content {
  flex: 1;
  cursor: pointer;
  min-width: 0;
}

.message-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 8px;
}

.message-title {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  line-height: 1.4;
}

.message-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.message-time {
  font-size: 12px;
  color: var(--el-text-color-placeholder);
  white-space: nowrap;
}

.message-text {
  font-size: 14px;
  color: var(--el-text-color-regular);
  line-height: 1.6;
  margin-bottom: 8px;
}

.message-sender {
  font-size: 12px;
  color: var(--el-text-color-placeholder);
}

.message-actions {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-left: 16px;
}

.delete-btn {
  color: var(--el-color-danger) !important;
}

.unread-indicator {
  position: absolute;
  top: 16px;
  right: 16px;
  width: 8px;
  height: 8px;
  background: var(--el-color-primary);
  border-radius: 50%;
}

.batch-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  margin: 20px 0;
  background: var(--el-color-primary-light-9);
  border: 1px solid var(--el-color-primary-light-7);
  border-radius: 8px;
}

.selected-info {
  font-size: 14px;
  color: var(--el-text-color-primary);
}

.actions {
  display: flex;
  gap: 8px;
}

.pagination-wrapper {
  display: flex;
  justify-content: center;
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid var(--el-border-color-light);
}
</style>