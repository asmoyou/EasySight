import request from '@/utils/request'

export interface CameraGroup {
  id: number
  name: string
  description?: string
  camera_ids: number[]
  camera_count: number
  created_at: string
  updated_at: string
}

export interface GroupForm {
  name: string
  description?: string
  camera_ids?: number[]
}

export interface GroupListResponse {
  groups: CameraGroup[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

// 获取分组列表
export function getGroups() {
  return request.get('/api/v1/cameras/groups/')
}

// 创建分组
export function createGroup(data: GroupForm) {
  return request.post('/api/v1/cameras/groups/', data)
}

// 更新分组
export function updateGroup(id: number, data: Partial<GroupForm>) {
  return request.put(`/api/v1/cameras/groups/${id}`, data)
}

// 删除分组
export function deleteGroup(id: number) {
  return request.delete(`/api/v1/cameras/groups/${id}`)
}

// 获取分组下的摄像头列表
export function getGroupCameras(groupId: number, page = 1, pageSize = 20) {
  return request.get(`/api/v1/cameras/groups/${groupId}/cameras`, {
    params: {
      page,
      page_size: pageSize
    }
  })
}