<template>
  <div class="table-actions">
    <!-- 主要操作按钮 -->
    <template v-for="(action, index) in primaryActions" :key="action.key">
      <el-button
        v-if="!action.dropdown"
        :type="action.type || 'default'"
        :size="action.size || 'small'"
        :disabled="action.disabled"
        :loading="action.loading"
        @click="action.handler"
        class="action-btn"
      >
        <el-icon v-if="action.icon" class="action-icon">
          <component :is="action.icon" />
        </el-icon>
        <span v-if="!compact || !action.icon">{{ action.label }}</span>
      </el-button>
      
      <!-- 下拉菜单按钮 -->
      <el-dropdown
        v-else
        @command="handleDropdownCommand"
        trigger="click"
        class="action-dropdown"
      >
        <el-button
          :type="action.type || 'default'"
          :size="action.size || 'small'"
          :disabled="action.disabled"
        >
          {{ action.label }}
          <el-icon class="el-icon--right">
            <ArrowDown />
          </el-icon>
        </el-button>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item
              v-for="child in action.children"
              :key="child.key"
              :command="child"
              :disabled="child.disabled"
            >
              <el-icon v-if="child.icon" class="dropdown-icon">
                <component :is="child.icon" />
              </el-icon>
              {{ child.label }}
            </el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </template>
    
    <!-- 更多操作下拉菜单 -->
    <el-dropdown
      v-if="secondaryActions.length > 0"
      @command="handleDropdownCommand"
      trigger="click"
      class="more-actions"
    >
      <el-button
        type="text"
        :size="compact ? 'small' : 'default'"
        class="more-btn"
      >
        更多
        <el-icon class="el-icon--right">
          <ArrowDown />
        </el-icon>
      </el-button>
      <template #dropdown>
        <el-dropdown-menu>
          <template v-for="action in flattenedSecondaryActions" :key="action.key">
            <el-dropdown-item
              :command="action"
              :disabled="action.disabled"
              :divided="action.divided"
            >
              <el-icon v-if="action.icon" class="dropdown-icon">
                <component :is="action.icon" />
              </el-icon>
              {{ action.label }}
            </el-dropdown-item>
          </template>
        </el-dropdown-menu>
      </template>
    </el-dropdown>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { ArrowDown } from '@element-plus/icons-vue'
import type { ActionItem, TableActionsProps } from '@/types/table'

interface Props {
  actions: ActionItem[]
  row?: any
  maxPrimaryActions?: number
  compact?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  maxPrimaryActions: 3,
  compact: false
})

// 分离主要操作和次要操作
const primaryActions = computed(() => {
  return props.actions.slice(0, props.maxPrimaryActions)
})

const secondaryActions = computed(() => {
  return props.actions.slice(props.maxPrimaryActions)
})

// 扁平化处理嵌套的下拉菜单项
const flattenedSecondaryActions = computed(() => {
  const flattened: ActionItem[] = []
  
  secondaryActions.value.forEach(action => {
    if (action.children && action.children.length > 0) {
      // 如果有子项，添加子项到扁平化列表
      action.children.forEach(child => {
        flattened.push({
          ...child,
          label: `${action.label} - ${child.label}` // 组合标签显示层级关系
        })
      })
    } else {
      // 没有子项的直接添加
      flattened.push(action)
    }
  })
  
  return flattened
})

// 处理下拉菜单命令
const handleDropdownCommand = (action: ActionItem) => {
  if (action.handler && !action.disabled) {
    action.handler()
  }
}
</script>

<style scoped>
.table-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: nowrap;
}

.action-btn {
  margin-right: 0;
}

.action-icon {
  margin-right: 4px;
}

.dropdown-icon {
  margin-right: 6px;
}

.more-btn {
  color: #606266;
  padding: 4px 8px;
}

.more-btn:hover {
  color: #409eff;
}

.action-dropdown,
.more-actions {
  margin-right: 0;
}
</style>