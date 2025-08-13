<template>
  <div class="event-tasks-container">
    <!-- 页面标题和操作栏 -->
    <div class="page-header">
      <div class="header-left">
        <h1 class="page-title">
          <q-icon name="task_alt" class="title-icon" />
          事件任务管理
        </h1>
        <p class="page-description">管理和监控事件检测任务的运行状态</p>
      </div>
      <div class="header-actions">
        <q-btn
          color="primary"
          icon="refresh"
          label="刷新"
          @click="loadTasks"
          :loading="loading"
        />
        <q-btn
          color="positive"
          icon="add"
          label="创建任务"
          @click="showCreateDialog = true"
        />
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-cards">
      <q-card class="stat-card">
        <q-card-section>
          <div class="stat-content">
            <q-icon name="assignment" class="stat-icon text-primary" />
            <div class="stat-info">
              <div class="stat-value">{{ stats.total_tasks }}</div>
              <div class="stat-label">总任务数</div>
            </div>
          </div>
        </q-card-section>
      </q-card>

      <q-card class="stat-card">
        <q-card-section>
          <div class="stat-content">
            <q-icon name="play_circle" class="stat-icon text-positive" />
            <div class="stat-info">
              <div class="stat-value">{{ stats.running_tasks }}</div>
              <div class="stat-label">运行中</div>
            </div>
          </div>
        </q-card-section>
      </q-card>

      <q-card class="stat-card">
        <q-card-section>
          <div class="stat-content">
            <q-icon name="stop_circle" class="stat-icon text-warning" />
            <div class="stat-info">
              <div class="stat-value">{{ stats.stopped_tasks }}</div>
              <div class="stat-label">已停止</div>
            </div>
          </div>
        </q-card-section>
      </q-card>

      <q-card class="stat-card">
        <q-card-section>
          <div class="stat-content">
            <q-icon name="error" class="stat-icon text-negative" />
            <div class="stat-info">
              <div class="stat-value">{{ stats.failed_tasks }}</div>
              <div class="stat-label">失败</div>
            </div>
          </div>
        </q-card-section>
      </q-card>

      <q-card class="stat-card">
        <q-card-section>
          <div class="stat-content">
            <q-icon name="trending_up" class="stat-icon text-info" />
            <div class="stat-info">
              <div class="stat-value">{{ stats.success_rate }}%</div>
              <div class="stat-label">成功率</div>
            </div>
          </div>
        </q-card-section>
      </q-card>
    </div>

    <!-- 筛选和搜索 -->
    <q-card class="filter-card">
      <q-card-section>
        <div class="filter-row">
          <q-input
            v-model="searchText"
            placeholder="搜索任务名称、描述、摄像头..."
            outlined
            dense
            clearable
            class="search-input"
            @keyup.enter="loadTasks"
          >
            <template v-slot:prepend>
              <q-icon name="search" />
            </template>
          </q-input>

          <q-select
            v-model="statusFilter"
            :options="statusOptions"
            label="状态筛选"
            outlined
            dense
            clearable
            emit-value
            map-options
            class="filter-select"
            @update:model-value="loadTasks"
          />

          <q-select
            v-model="typeFilter"
            :options="typeOptions"
            label="类型筛选"
            outlined
            dense
            clearable
            emit-value
            map-options
            class="filter-select"
            @update:model-value="loadTasks"
          />

          <q-select
            v-model="activeFilter"
            :options="activeOptions"
            label="启用状态"
            outlined
            dense
            clearable
            emit-value
            map-options
            class="filter-select"
            @update:model-value="loadTasks"
          />
        </div>
      </q-card-section>
    </q-card>

    <!-- 任务列表 -->
    <q-card class="tasks-card">
      <q-table
        :rows="tasks"
        :columns="columns"
        :loading="loading"
        :pagination="pagination"
        @request="onRequest"
        row-key="id"
        flat
        bordered
      >
        <!-- 状态列 -->
        <template v-slot:body-cell-status="props">
          <q-td :props="props">
            <q-chip
              :color="getStatusColor(props.value)"
              text-color="white"
              dense
              :icon="getStatusIcon(props.value)"
            >
              {{ getStatusText(props.value) }}
            </q-chip>
          </q-td>
        </template>

        <!-- 任务类型列 -->
        <template v-slot:body-cell-task_type="props">
          <q-td :props="props">
            <q-chip
              :color="getTypeColor(props.value)"
              text-color="white"
              dense
              :icon="getTypeIcon(props.value)"
            >
              {{ getTypeText(props.value) }}
            </q-chip>
          </q-td>
        </template>

        <!-- 启用状态列 -->
        <template v-slot:body-cell-is_active="props">
          <q-td :props="props">
            <q-toggle
              :model-value="props.value"
              @update:model-value="toggleTaskActive(props.row)"
              color="positive"
              :disable="props.row.status === 'RUNNING'"
            />
          </q-td>
        </template>

        <!-- 检测统计列 -->
        <template v-slot:body-cell-detection_stats="props">
          <q-td :props="props">
            <div class="detection-stats">
              <div class="stat-item">
                <span class="stat-label">总检测:</span>
                <span class="stat-value">{{ props.row.total_detections }}</span>
              </div>
              <div class="stat-item">
                <span class="stat-label">成功:</span>
                <span class="stat-value text-positive">{{ props.row.success_detections }}</span>
              </div>
              <div class="stat-item">
                <span class="stat-label">事件:</span>
                <span class="stat-value text-warning">{{ props.row.total_events }}</span>
              </div>
            </div>
          </q-td>
        </template>

        <!-- Worker分配列 -->
        <template v-slot:body-cell-assigned_worker="props">
          <q-td :props="props">
            <div v-if="props.value" class="worker-info">
              <div class="worker-main">
                <q-chip
                  :color="getWorkerStatusColor(props.row)"
                  text-color="white"
                  dense
                  icon="computer"
                  size="sm"
                >
                  {{ props.value }}
                </q-chip>
              </div>
              <div class="worker-details">
                <div class="worker-status">
                  <q-icon 
                    :name="getWorkerStatusIcon(props.row)" 
                    :color="getWorkerStatusColor(props.row)"
                    size="xs"
                  />
                  <span class="status-text">{{ getWorkerStatusText(props.row) }}</span>
                </div>
                <div v-if="props.row.worker_heartbeat" class="heartbeat-time">
                  <q-icon name="favorite" color="red" size="xs" />
                  <span class="time-text">{{ formatRelativeTime(props.row.worker_heartbeat) }}</span>
                </div>
              </div>
            </div>
            <div v-else class="text-grey-6">
              <q-chip
                color="grey-5"
                text-color="grey-8"
                dense
                icon="help_outline"
                size="sm"
              >
                未分配
              </q-chip>
            </div>
          </q-td>
        </template>

        <!-- 最后检测时间列 -->
        <template v-slot:body-cell-last_detection_time="props">
          <q-td :props="props">
            <div v-if="props.value">
              {{ formatDateTime(props.value) }}
            </div>
            <div v-else class="text-grey-6">-</div>
          </q-td>
        </template>

        <!-- 操作列 -->
        <template v-slot:body-cell-actions="props">
          <q-td :props="props">
            <div class="action-buttons">
              <!-- 启动按钮 -->
              <q-btn
                v-if="props.row.status !== 'RUNNING'"
                icon="play_arrow"
                color="positive"
                size="sm"
                dense
                round
                @click="startTask(props.row)"
                :loading="actionLoading[props.row.id]"
              >
                <q-tooltip>启动任务</q-tooltip>
              </q-btn>

              <!-- 停止按钮 -->
              <q-btn
                v-if="props.row.status === 'RUNNING'"
                icon="stop"
                color="negative"
                size="sm"
                dense
                round
                @click="stopTask(props.row)"
                :loading="actionLoading[props.row.id]"
              >
                <q-tooltip>停止任务</q-tooltip>
              </q-btn>

              <!-- 查看详情 -->
              <q-btn
                icon="visibility"
                color="primary"
                size="sm"
                dense
                round
                @click="viewTaskDetail(props.row)"
              >
                <q-tooltip>查看详情</q-tooltip>
              </q-btn>

              <!-- 查看日志 -->
              <q-btn
                icon="description"
                color="info"
                size="sm"
                dense
                round
                @click="viewTaskLogs(props.row)"
              >
                <q-tooltip>查看日志</q-tooltip>
              </q-btn>

              <!-- 编辑 -->
              <q-btn
                icon="edit"
                color="warning"
                size="sm"
                dense
                round
                @click="editTask(props.row)"
                :disable="props.row.status === 'RUNNING'"
              >
                <q-tooltip>编辑任务</q-tooltip>
              </q-btn>

              <!-- 删除 -->
              <q-btn
                icon="delete"
                color="negative"
                size="sm"
                dense
                round
                @click="deleteTask(props.row)"
                :disable="props.row.status === 'RUNNING'"
              >
                <q-tooltip>删除任务</q-tooltip>
              </q-btn>
            </div>
          </q-td>
        </template>
      </q-table>
    </q-card>

    <!-- 创建任务对话框 -->
    <q-dialog v-model="showCreateDialog" persistent>
      <q-card style="min-width: 600px">
        <q-card-section class="row items-center">
          <div class="text-h6">创建事件任务</div>
          <q-space />
          <q-btn icon="close" flat round dense @click="showCreateDialog = false" />
        </q-card-section>

        <q-card-section>
          <q-form @submit="createTask" class="q-gutter-md">
            <q-input
              v-model="newTask.name"
              label="任务名称 *"
              outlined
              :rules="[val => !!val || '请输入任务名称']"
            />

            <q-input
              v-model="newTask.description"
              label="任务描述"
              outlined
              type="textarea"
              rows="3"
            />

            <q-select
              v-model="newTask.ai_service_id"
              :options="aiServiceOptions"
              label="AI服务 *"
              outlined
              emit-value
              map-options
              :rules="[val => !!val || '请选择AI服务']"
            />

            <q-select
              v-model="newTask.task_type"
              :options="typeOptions"
              label="任务类型"
              outlined
              emit-value
              map-options
            />

            <q-input
              v-model.number="newTask.alarm_threshold"
              label="告警阈值"
              outlined
              type="number"
              step="0.1"
              min="0"
              max="1"
            />

            <q-input
              v-model.number="newTask.check_interval"
              label="检查间隔(秒)"
              outlined
              type="number"
              min="1"
            />

            <q-checkbox
              v-model="newTask.auto_recovery"
              label="启用自动恢复"
            />

            <div class="row q-gutter-sm">
              <q-btn
                type="submit"
                color="primary"
                label="创建"
                :loading="createLoading"
              />
              <q-btn
                label="取消"
                color="grey"
                @click="showCreateDialog = false"
              />
            </div>
          </q-form>
        </q-card-section>
      </q-card>
    </q-dialog>

    <!-- 任务详情对话框 -->
    <q-dialog v-model="showDetailDialog" persistent>
      <q-card style="min-width: 800px; max-width: 90vw">
        <q-card-section class="row items-center">
          <div class="text-h6">任务详情</div>
          <q-space />
          <q-btn icon="close" flat round dense @click="showDetailDialog = false" />
        </q-card-section>

        <q-card-section v-if="selectedTask">
          <div class="task-detail-content">
            <!-- 基本信息 -->
            <div class="detail-section">
              <h6 class="section-title">基本信息</h6>
              <div class="detail-grid">
                <div class="detail-item">
                  <label>任务名称:</label>
                  <span>{{ selectedTask.name }}</span>
                </div>
                <div class="detail-item">
                  <label>任务ID:</label>
                  <span>{{ selectedTask.task_id }}</span>
                </div>
                <div class="detail-item">
                  <label>状态:</label>
                  <q-chip
                    :color="getStatusColor(selectedTask.status)"
                    text-color="white"
                    dense
                    :icon="getStatusIcon(selectedTask.status)"
                  >
                    {{ getStatusText(selectedTask.status) }}
                  </q-chip>
                </div>
                <div class="detail-item">
                  <label>类型:</label>
                  <q-chip
                    :color="getTypeColor(selectedTask.task_type)"
                    text-color="white"
                    dense
                    :icon="getTypeIcon(selectedTask.task_type)"
                  >
                    {{ getTypeText(selectedTask.task_type) }}
                  </q-chip>
                </div>
                <div class="detail-item">
                  <label>摄像头:</label>
                  <span>{{ selectedTask.camera_name }}</span>
                </div>
                <div class="detail-item">
                  <label>算法:</label>
                  <span>{{ selectedTask.algorithm_name }}</span>
                </div>
                <div class="detail-item">
                  <label>分配Worker:</label>
                  <span>{{ selectedTask.assigned_worker || '-' }}</span>
                </div>
                <div class="detail-item">
                  <label>告警阈值:</label>
                  <span>{{ selectedTask.alarm_threshold }}</span>
                </div>
              </div>
            </div>

            <!-- 统计信息 -->
            <div class="detail-section">
              <h6 class="section-title">统计信息</h6>
              <div class="detail-grid">
                <div class="detail-item">
                  <label>总检测次数:</label>
                  <span>{{ selectedTask.total_detections }}</span>
                </div>
                <div class="detail-item">
                  <label>成功检测:</label>
                  <span class="text-positive">{{ selectedTask.success_detections }}</span>
                </div>
                <div class="detail-item">
                  <label>失败检测:</label>
                  <span class="text-negative">{{ selectedTask.failed_detections }}</span>
                </div>
                <div class="detail-item">
                  <label>触发事件:</label>
                  <span class="text-warning">{{ selectedTask.total_events }}</span>
                </div>
                <div class="detail-item">
                  <label>平均处理时间:</label>
                  <span>{{ selectedTask.avg_processing_time ? selectedTask.avg_processing_time.toFixed(2) + 'ms' : '-' }}</span>
                </div>
                <div class="detail-item">
                  <label>错误次数:</label>
                  <span>{{ selectedTask.error_count }}</span>
                </div>
                <div class="detail-item">
                  <label>重试次数:</label>
                  <span>{{ selectedTask.retry_count }}/{{ selectedTask.max_retry_count }}</span>
                </div>
                <div class="detail-item">
                  <label>最后检测:</label>
                  <span>{{ selectedTask.last_detection_time ? formatDateTime(selectedTask.last_detection_time) : '-' }}</span>
                </div>
              </div>
            </div>

            <!-- 时间信息 -->
            <div class="detail-section">
              <h6 class="section-title">时间信息</h6>
              <div class="detail-grid">
                <div class="detail-item">
                  <label>创建时间:</label>
                  <span>{{ formatDateTime(selectedTask.created_at) }}</span>
                </div>
                <div class="detail-item">
                  <label>更新时间:</label>
                  <span>{{ formatDateTime(selectedTask.updated_at) }}</span>
                </div>
                <div class="detail-item">
                  <label>启动时间:</label>
                  <span>{{ selectedTask.started_at ? formatDateTime(selectedTask.started_at) : '-' }}</span>
                </div>
                <div class="detail-item">
                  <label>停止时间:</label>
                  <span>{{ selectedTask.stopped_at ? formatDateTime(selectedTask.stopped_at) : '-' }}</span>
                </div>
              </div>
            </div>
          </div>
        </q-card-section>
      </q-card>
    </q-dialog>

    <!-- 日志查看对话框 -->
    <q-dialog v-model="showLogsDialog" persistent>
      <q-card style="min-width: 1000px; max-width: 90vw; max-height: 80vh">
        <q-card-section class="row items-center">
          <div class="text-h6">任务日志</div>
          <q-space />
          <q-btn icon="close" flat round dense @click="showLogsDialog = false" />
        </q-card-section>

        <q-card-section class="q-pa-none" style="max-height: 60vh; overflow-y: auto">
          <q-table
            :rows="taskLogs"
            :columns="logColumns"
            :loading="logsLoading"
            row-key="id"
            flat
            dense
          >
            <!-- 日志级别列 -->
            <template v-slot:body-cell-log_level="props">
              <q-td :props="props">
                <q-chip
                  :color="getLogLevelColor(props.value)"
                  text-color="white"
                  dense
                  size="sm"
                >
                  {{ props.value }}
                </q-chip>
              </q-td>
            </template>

            <!-- 时间列 -->
            <template v-slot:body-cell-created_at="props">
              <q-td :props="props">
                {{ formatDateTime(props.value) }}
              </q-td>
            </template>
          </q-table>
        </q-card-section>
      </q-card>
    </q-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useQuasar } from 'quasar'
import { eventTasksApi } from 'src/api/event-tasks'
import { aiAlgorithmsApi } from 'src/api/ai-algorithms'

const $q = useQuasar()

// 响应式数据
const loading = ref(false)
const createLoading = ref(false)
const logsLoading = ref(false)
const tasks = ref([])
const taskLogs = ref([])
const stats = ref({
  total_tasks: 0,
  running_tasks: 0,
  stopped_tasks: 0,
  failed_tasks: 0,
  success_rate: 0
})
const actionLoading = ref({})

// 筛选和搜索
const searchText = ref('')
const statusFilter = ref(null)
const typeFilter = ref(null)
const activeFilter = ref(null)

// 分页
const pagination = ref({
  page: 1,
  rowsPerPage: 20,
  rowsNumber: 0
})

// 对话框状态
const showCreateDialog = ref(false)
const showDetailDialog = ref(false)
const showLogsDialog = ref(false)
const selectedTask = ref(null)

// 新任务表单
const newTask = reactive({
  name: '',
  description: '',
  ai_service_id: null,
  task_type: 'CONTINUOUS',
  alarm_threshold: 0.5,
  check_interval: 5,
  auto_recovery: true
})

// AI服务选项
const aiServiceOptions = ref([])

// 选项定义
const statusOptions = [
  { label: '待启动', value: 'PENDING' },
  { label: '运行中', value: 'RUNNING' },
  { label: '已停止', value: 'STOPPED' },
  { label: '失败', value: 'FAILED' },
  { label: '暂停', value: 'PAUSED' }
]

const typeOptions = [
  { label: '连续检测', value: 'CONTINUOUS' },
  { label: '定时检测', value: 'SCHEDULED' },
  { label: '事件触发', value: 'EVENT_TRIGGERED' }
]

const activeOptions = [
  { label: '启用', value: true },
  { label: '禁用', value: false }
]

// 表格列定义
const columns = [
  {
    name: 'name',
    label: '任务名称',
    field: 'name',
    align: 'left',
    sortable: true
  },
  {
    name: 'status',
    label: '状态',
    field: 'status',
    align: 'center',
    sortable: true
  },
  {
    name: 'task_type',
    label: '类型',
    field: 'task_type',
    align: 'center',
    sortable: true
  },
  {
    name: 'camera_name',
    label: '摄像头',
    field: 'camera_name',
    align: 'left',
    sortable: true
  },
  {
    name: 'algorithm_name',
    label: '算法',
    field: 'algorithm_name',
    align: 'left',
    sortable: true
  },
  {
    name: 'assigned_worker',
    label: 'Worker',
    field: 'assigned_worker',
    align: 'left'
  },
  {
    name: 'is_active',
    label: '启用',
    field: 'is_active',
    align: 'center'
  },
  {
    name: 'detection_stats',
    label: '检测统计',
    field: 'detection_stats',
    align: 'center'
  },
  {
    name: 'last_detection_time',
    label: '最后检测',
    field: 'last_detection_time',
    align: 'center',
    sortable: true
  },
  {
    name: 'actions',
    label: '操作',
    field: 'actions',
    align: 'center'
  }
]

// 日志表格列定义
const logColumns = [
  {
    name: 'created_at',
    label: '时间',
    field: 'created_at',
    align: 'left',
    sortable: true
  },
  {
    name: 'log_level',
    label: '级别',
    field: 'log_level',
    align: 'center'
  },
  {
    name: 'log_type',
    label: '类型',
    field: 'log_type',
    align: 'center'
  },
  {
    name: 'message',
    label: '消息',
    field: 'message',
    align: 'left'
  },
  {
    name: 'worker_id',
    label: 'Worker',
    field: 'worker_id',
    align: 'left'
  },
  {
    name: 'processing_time',
    label: '处理时间(ms)',
    field: 'processing_time',
    align: 'right'
  }
]

// 方法定义
const loadTasks = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.value.page,
      page_size: pagination.value.rowsPerPage,
      search: searchText.value || undefined,
      status: statusFilter.value || undefined,
      task_type: typeFilter.value || undefined,
      is_active: activeFilter.value
    }
    
    const response = await eventTasksApi.getTasks(params)
    tasks.value = response.tasks
    pagination.value.rowsNumber = response.total
  } catch (error) {
    $q.notify({
      type: 'negative',
      message: '加载任务列表失败: ' + error.message
    })
  } finally {
    loading.value = false
  }
}

const loadStats = async () => {
  try {
    const response = await eventTasksApi.getStats()
    stats.value = response
  } catch (error) {
    console.error('加载统计信息失败:', error)
  }
}

const loadAIServices = async () => {
  try {
    const response = await aiAlgorithmsApi.getServices()
    aiServiceOptions.value = response.services.map(service => ({
      label: `${service.name} (${service.camera_name})`,
      value: service.id
    }))
  } catch (error) {
    console.error('加载AI服务失败:', error)
  }
}

const onRequest = (props) => {
  pagination.value = props.pagination
  loadTasks()
}

const createTask = async () => {
  createLoading.value = true
  try {
    await eventTasksApi.createTask(newTask)
    $q.notify({
      type: 'positive',
      message: '任务创建成功'
    })
    showCreateDialog.value = false
    resetNewTask()
    loadTasks()
    loadStats()
  } catch (error) {
    $q.notify({
      type: 'negative',
      message: '创建任务失败: ' + error.message
    })
  } finally {
    createLoading.value = false
  }
}

const startTask = async (task) => {
  actionLoading.value[task.id] = true
  try {
    await eventTasksApi.startTask(task.id)
    $q.notify({
      type: 'positive',
      message: '任务启动成功'
    })
    loadTasks()
    loadStats()
  } catch (error) {
    $q.notify({
      type: 'negative',
      message: '启动任务失败: ' + error.message
    })
  } finally {
    actionLoading.value[task.id] = false
  }
}

const stopTask = async (task) => {
  actionLoading.value[task.id] = true
  try {
    await eventTasksApi.stopTask(task.id, '手动停止')
    $q.notify({
      type: 'positive',
      message: '任务停止成功'
    })
    loadTasks()
    loadStats()
  } catch (error) {
    $q.notify({
      type: 'negative',
      message: '停止任务失败: ' + error.message
    })
  } finally {
    actionLoading.value[task.id] = false
  }
}

const toggleTaskActive = async (task) => {
  try {
    await eventTasksApi.updateTask(task.id, {
      is_active: !task.is_active
    })
    $q.notify({
      type: 'positive',
      message: `任务已${!task.is_active ? '启用' : '禁用'}`
    })
    loadTasks()
  } catch (error) {
    $q.notify({
      type: 'negative',
      message: '更新任务状态失败: ' + error.message
    })
  }
}

const viewTaskDetail = (task) => {
  selectedTask.value = task
  showDetailDialog.value = true
}

const viewTaskLogs = async (task) => {
  selectedTask.value = task
  showLogsDialog.value = true
  logsLoading.value = true
  try {
    const response = await eventTasksApi.getTaskLogs(task.id)
    taskLogs.value = response
  } catch (error) {
    $q.notify({
      type: 'negative',
      message: '加载任务日志失败: ' + error.message
    })
  } finally {
    logsLoading.value = false
  }
}

const editTask = (task) => {
  // TODO: 实现编辑功能
  $q.notify({
    type: 'info',
    message: '编辑功能开发中...'
  })
}

const deleteTask = async (task) => {
  $q.dialog({
    title: '确认删除',
    message: `确定要删除任务 "${task.name}" 吗？此操作不可恢复。`,
    cancel: true,
    persistent: true
  }).onOk(async () => {
    try {
      await eventTasksApi.deleteTask(task.id)
      $q.notify({
        type: 'positive',
        message: '任务删除成功'
      })
      loadTasks()
      loadStats()
    } catch (error) {
      $q.notify({
        type: 'negative',
        message: '删除任务失败: ' + error.message
      })
    }
  })
}

const resetNewTask = () => {
  Object.assign(newTask, {
    name: '',
    description: '',
    ai_service_id: null,
    task_type: 'CONTINUOUS',
    alarm_threshold: 0.5,
    check_interval: 5,
    auto_recovery: true
  })
}

// 工具方法
const getStatusColor = (status) => {
  const colors = {
    PENDING: 'grey',
    RUNNING: 'positive',
    STOPPED: 'warning',
    FAILED: 'negative',
    PAUSED: 'info'
  }
  return colors[status] || 'grey'
}

const getStatusIcon = (status) => {
  const icons = {
    PENDING: 'schedule',
    RUNNING: 'play_circle',
    STOPPED: 'stop_circle',
    FAILED: 'error',
    PAUSED: 'pause_circle'
  }
  return icons[status] || 'help'
}

const getStatusText = (status) => {
  const texts = {
    PENDING: '待启动',
    RUNNING: '运行中',
    STOPPED: '已停止',
    FAILED: '失败',
    PAUSED: '暂停'
  }
  return texts[status] || status
}

const getTypeColor = (type) => {
  const colors = {
    CONTINUOUS: 'primary',
    SCHEDULED: 'secondary',
    EVENT_TRIGGERED: 'accent'
  }
  return colors[type] || 'grey'
}

const getTypeIcon = (type) => {
  const icons = {
    CONTINUOUS: 'loop',
    SCHEDULED: 'schedule',
    EVENT_TRIGGERED: 'flash_on'
  }
  return icons[type] || 'help'
}

const getTypeText = (type) => {
  const texts = {
    CONTINUOUS: '连续检测',
    SCHEDULED: '定时检测',
    EVENT_TRIGGERED: '事件触发'
  }
  return texts[type] || type
}

const getLogLevelColor = (level) => {
  const colors = {
    DEBUG: 'grey',
    INFO: 'primary',
    WARNING: 'warning',
    ERROR: 'negative',
    CRITICAL: 'negative'
  }
  return colors[level] || 'grey'
}

const formatDateTime = (dateTime) => {
  if (!dateTime) return '-'
  return new Date(dateTime).toLocaleString('zh-CN')
}

const formatRelativeTime = (dateTime) => {
  if (!dateTime) return '-'
  const now = new Date()
  const time = new Date(dateTime)
  const diffMs = now - time
  const diffMins = Math.floor(diffMs / 60000)
  
  if (diffMins < 1) return '刚刚'
  if (diffMins < 60) return `${diffMins}分钟前`
  if (diffMins < 1440) return `${Math.floor(diffMins / 60)}小时前`
  return `${Math.floor(diffMins / 1440)}天前`
}

// Worker状态相关方法
const getWorkerStatusColor = (task) => {
  if (!task.assigned_worker) return 'grey'
  
  if (task.status === 'RUNNING') {
    // 检查心跳时间，判断Worker是否在线
    if (task.worker_heartbeat) {
      const now = new Date()
      const heartbeat = new Date(task.worker_heartbeat)
      const diffMins = (now - heartbeat) / 60000
      
      if (diffMins <= 3) return 'positive' // 在线
      if (diffMins <= 10) return 'warning' // 可能离线
      return 'negative' // 离线
    }
    return 'warning' // 无心跳数据
  }
  
  return 'info' // 非运行状态
}

const getWorkerStatusIcon = (task) => {
  if (!task.assigned_worker) return 'help_outline'
  
  if (task.status === 'RUNNING') {
    if (task.worker_heartbeat) {
      const now = new Date()
      const heartbeat = new Date(task.worker_heartbeat)
      const diffMins = (now - heartbeat) / 60000
      
      if (diffMins <= 3) return 'check_circle' // 在线
      if (diffMins <= 10) return 'warning' // 可能离线
      return 'error' // 离线
    }
    return 'help' // 无心跳数据
  }
  
  return 'info' // 非运行状态
}

const getWorkerStatusText = (task) => {
  if (!task.assigned_worker) return '未分配'
  
  if (task.status === 'RUNNING') {
    if (task.worker_heartbeat) {
      const now = new Date()
      const heartbeat = new Date(task.worker_heartbeat)
      const diffMins = (now - heartbeat) / 60000
      
      if (diffMins <= 3) return '在线执行'
      if (diffMins <= 10) return '可能离线'
      return '离线'
    }
    return '状态未知'
  }
  
  if (task.status === 'STOPPED') return '已停止'
  if (task.status === 'PENDING') return '等待执行'
  if (task.status === 'FAILED') return '执行失败'
  
  return task.status
}

// 生命周期
onMounted(() => {
  loadTasks()
  loadStats()
  loadAIServices()
})
</script>

<style scoped>
.event-tasks-container {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
}

.header-left {
  flex: 1;
}

.page-title {
  display: flex;
  align-items: center;
  margin: 0 0 8px 0;
  font-size: 28px;
  font-weight: 600;
  color: #1976d2;
}

.title-icon {
  margin-right: 12px;
  font-size: 32px;
}

.page-description {
  margin: 0;
  color: #666;
  font-size: 16px;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.stats-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

.stat-card {
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.stat-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-icon {
  font-size: 32px;
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 24px;
  font-weight: 600;
  line-height: 1;
}

.stat-label {
  font-size: 14px;
  color: #666;
  margin-top: 4px;
}

.filter-card {
  margin-bottom: 24px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.filter-row {
  display: grid;
  grid-template-columns: 2fr 1fr 1fr 1fr;
  gap: 16px;
  align-items: center;
}

.search-input {
  min-width: 300px;
}

.filter-select {
  min-width: 150px;
}

.tasks-card {
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.action-buttons {
  display: flex;
  gap: 4px;
  justify-content: center;
}

.detection-stats {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.stat-item {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
}

.stat-label {
  color: #666;
}

/* Worker信息样式 */
.worker-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 120px;
}

.worker-main {
  display: flex;
  align-items: center;
}

.worker-details {
  display: flex;
  flex-direction: column;
  gap: 2px;
  font-size: 11px;
}

.worker-status {
  display: flex;
  align-items: center;
  gap: 4px;
}

.status-text {
  color: #666;
  font-weight: 500;
}

.heartbeat-time {
  display: flex;
  align-items: center;
  gap: 4px;
}

.time-text {
  color: #999;
  font-size: 10px;
}

.task-detail-content {
  max-height: 60vh;
  overflow-y: auto;
}

.detail-section {
  margin-bottom: 24px;
}

.section-title {
  margin: 0 0 16px 0;
  padding-bottom: 8px;
  border-bottom: 2px solid #e0e0e0;
  color: #1976d2;
  font-weight: 600;
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 12px;
}

.detail-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: #f5f5f5;
  border-radius: 6px;
}

.detail-item label {
  font-weight: 500;
  color: #333;
  margin-right: 12px;
}

.detail-item span {
  color: #666;
  text-align: right;
}

@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    gap: 16px;
  }
  
  .filter-row {
    grid-template-columns: 1fr;
  }
  
  .stats-cards {
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  }
  
  .detail-grid {
    grid-template-columns: 1fr;
  }
}
</style>