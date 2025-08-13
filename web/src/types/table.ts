export interface ActionItem {
  key: string
  label: string
  type?: 'primary' | 'success' | 'warning' | 'danger' | 'info' | 'text'
  size?: 'large' | 'default' | 'small'
  icon?: any
  disabled?: boolean
  loading?: boolean
  dropdown?: boolean
  children?: ActionItem[]
  handler: () => void
}

export interface TableActionsProps {
  actions: ActionItem[]
  row?: any
  maxPrimaryActions?: number
  compact?: boolean
}