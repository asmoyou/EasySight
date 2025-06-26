 <template>
  <el-popover
    placement="bottom-end"
    :width="400"
    trigger="click"
    popper-class="message-notification-popover"
  >
    <template #reference>
      <el-badge :value="unreadCount" :hidden="unreadCount === 0" class="notification-badge">
        <el-button circle size="large" class="notification-btn">
          <el-icon :size="18"><Bell /></el-icon>
        </el-button>
      </el-badge>
    </template>

    <div class="message-notification">
      <div class="message-header">
        <h4>消息通知</h4>
        <div class="header-actions">
          <el-button
            v-if="unreadCount > 0"
            type="text"
            size="small"
            @click="markAllRead"
          >
            全部已读
          </el-button>
          <el-button type="text" size="small" @click="viewAllMessages">
            查看全部
          </el-button>
        </div>
      </div>

      <div class="message-list" v-loading="loading">
        <div v-if="messages.length === 0" class="empty-message">
          <el-empty description="暂无消息" :image-size="80" />
        </div>
        <div v-else>
          <div
            v-for="message in messages"
            :key="message.id"
            class="message-item"
            :class="{ 'unread': !message.is_read }"
            @click="handleMessageClick(message)"
          >
            <div class="message-icon">
              <el-icon
                :class="getMessageIconClass(message.message_type)"
                :color="getMessageIconColor(message.message_type)"
              >
                <component :is="getMessageIcon(message.message_type)" />
              </el-icon>
            </div>
            <div class="message-content">
              <div class="message-title">{{ message.title }}</div>
              <div class="message-text">{{ message.content }}</div>
              <div class="message-time">{{ formatTime(message.created_at) }}</div>
            </div>
            <div v-if="!message.is_read" class="unread-dot"></div>
          </div>
        </div>
      </div>

      <div class="message-footer" v-if="messages.length > 0">
        <el-button type="text" @click="loadMore" :loading="loadingMore">
          加载更多
        </el-button>
      </div>
    </div>
  </el-popover>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { Bell, InfoFilled, WarningFilled, CircleCloseFilled, CircleCheckFilled } from '@element-plus/icons-vue'
import { messagesApi, type Message } from '@/api/messages'
import { useRouter } from 'vue-router'
import { formatDistanceToNow } from 'date-fns'
import { zhCN } from 'date-fns/locale'

const router = useRouter()

const messages = ref<Message[]>([])
const unreadCount = ref(0)
const loading = ref(false)
const loadingMore = ref(false)
const currentPage = ref(1)
const pageSize = 10
const hasMore = ref(true)

// 获取消息列表
const fetchMessages = async (page = 1, append = false) => {
  try {
    if (page === 1) {
      loading.value = true
    } else {
      loadingMore.value = true
    }

    const { data } = await messagesApi.getMessages({
      page,
      page_size: pageSize
    })

    if (append) {
      messages.value.push(...data.messages)
    } else {
      messages.value = data.messages
    }

    unreadCount.value = data.unread_count
    hasMore.value = data.messages.length === pageSize
    currentPage.value = page
  } catch (error) {
    console.error('获取消息失败:', error)
    ElMessage.error('获取消息失败')
  } finally {
    loading.value = false
    loadingMore.value = false
  }
}

// 获取未读消息数量
const fetchUnreadCount = async () => {
  try {
    const { data } = await messagesApi.getUnreadCount()
    unreadCount.value = data.unread_count
  } catch (error) {
    console.error('获取未读消息数量失败:', error)
  }
}

// 标记所有消息为已读
const markAllRead = async () => {
  try {
    await messagesApi.markAllMessagesRead()
    messages.value.forEach(msg => {
      msg.is_read = true
    })
    unreadCount.value = 0
    ElMessage.success('已标记所有消息为已读')
  } catch (error) {
    console.error('标记已读失败:', error)
    ElMessage.error('标记已读失败')
  }
}

// 处理消息点击
const handleMessageClick = async (message: Message) => {
  if (!message.is_read) {
    try {
      await messagesApi.markMessagesRead({ message_ids: [message.id] })
      message.is_read = true
      unreadCount.value = Math.max(0, unreadCount.value - 1)
    } catch (error) {
      console.error('标记消息已读失败:', error)
    }
  }
  
  // 可以根据消息类型或内容跳转到相应页面
  // 这里暂时不做跳转处理
}

// 查看全部消息
const viewAllMessages = () => {
  router.push('/messages')
}

// 加载更多
const loadMore = () => {
  if (hasMore.value && !loadingMore.value) {
    fetchMessages(currentPage.value + 1, true)
  }
}

// 获取消息图标
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

// 获取消息图标颜色
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

// 获取消息图标样式类
const getMessageIconClass = (type: string) => {
  return `message-icon-${type}`
}

// 格式化时间
const formatTime = (time: string) => {
  return formatDistanceToNow(new Date(time), {
    addSuffix: true,
    locale: zhCN
  })
}

// 定期刷新未读消息数量
let refreshTimer: NodeJS.Timeout | null = null

const startRefreshTimer = () => {
  refreshTimer = setInterval(() => {
    fetchUnreadCount()
  }, 30000) // 每30秒刷新一次
}

const stopRefreshTimer = () => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }
}

onMounted(() => {
  fetchMessages()
  startRefreshTimer()
})

// 组件卸载时清理定时器
import { onUnmounted } from 'vue'
onUnmounted(() => {
  stopRefreshTimer()
})

// 暴露未读消息数量给父组件
defineExpose({
  unreadCount,
  fetchUnreadCount,
  fetchMessages
})
</script>

<style scoped>
.notification-badge {
  margin-right: 12px;
}

.notification-btn {
  border: none;
  background: transparent;
  color: var(--el-text-color-regular);
  transition: all 0.3s;
}

.notification-btn:hover {
  background: var(--el-fill-color-light);
  color: var(--el-color-primary);
}

.message-notification {
  max-height: 500px;
  display: flex;
  flex-direction: column;
}

.message-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid var(--el-border-color-light);
}

.message-header h4 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.header-actions {
  display: flex;
  gap: 8px;
}

.message-list {
  flex: 1;
  max-height: 350px;
  overflow-y: auto;
  padding: 8px 0;
}

.empty-message {
  padding: 20px;
  text-align: center;
}

.message-item {
  display: flex;
  align-items: flex-start;
  padding: 12px;
  margin: 4px 0;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
  position: relative;
}

.message-item:hover {
  background: var(--el-fill-color-light);
}

.message-item.unread {
  background: var(--el-color-primary-light-9);
}

.message-item.unread:hover {
  background: var(--el-color-primary-light-8);
}

.message-icon {
  margin-right: 12px;
  margin-top: 2px;
}

.message-content {
  flex: 1;
  min-width: 0;
}

.message-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--el-text-color-primary);
  margin-bottom: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.message-text {
  font-size: 12px;
  color: var(--el-text-color-regular);
  line-height: 1.4;
  margin-bottom: 4px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.message-time {
  font-size: 11px;
  color: var(--el-text-color-placeholder);
}

.unread-dot {
  width: 8px;
  height: 8px;
  background: var(--el-color-primary);
  border-radius: 50%;
  margin-left: 8px;
  margin-top: 6px;
  flex-shrink: 0;
}

.message-footer {
  text-align: center;
  padding: 8px 0;
  border-top: 1px solid var(--el-border-color-light);
}

/* 滚动条样式 */
.message-list::-webkit-scrollbar {
  width: 4px;
}

.message-list::-webkit-scrollbar-track {
  background: var(--el-fill-color-lighter);
  border-radius: 2px;
}

.message-list::-webkit-scrollbar-thumb {
  background: var(--el-border-color);
  border-radius: 2px;
}

.message-list::-webkit-scrollbar-thumb:hover {
  background: var(--el-border-color-dark);
}
</style>

<style>
.message-notification-popover {
  padding: 16px !important;
}
</style>