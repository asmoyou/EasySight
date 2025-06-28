import request from '@/utils/request'
import type { ApiResponse } from '@/types/api'
import type {
  Camera,
  CameraCreateForm,
  CameraUpdateForm,
  CameraListResponse,
  CameraQueryParams,
  CameraStats,
  MediaProxy,
  MediaProxyCreateForm,
  MediaProxyUpdateForm,
  CameraGroup,
  CameraGroupCreateForm,
  CameraGroupUpdateForm
} from '@/types/camera'

export const cameraApi = {
  // 获取摄像头列表
  getCameras(params?: CameraQueryParams) {
    return request.get<ApiResponse<CameraListResponse>>('/api/v1/cameras/', { params })
  },

  // 获取摄像头详情
  getCamera(id: number) {
    return request.get<ApiResponse<Camera>>(`/api/v1/cameras/${id}`)
  },

  // 创建摄像头
  createCamera(data: CameraCreateForm) {
    return request.post<ApiResponse<Camera>>('/api/v1/cameras/', data)
  },

  // 更新摄像头
  updateCamera(id: number, data: CameraUpdateForm) {
    return request.put<ApiResponse<Camera>>(`/api/v1/cameras/${id}`, data)
  },

  // 删除摄像头
  deleteCamera(id: number) {
    return request.delete<ApiResponse<{ message: string }>>(`/api/v1/cameras/${id}`)
  },

  // 获取摄像头统计信息
  getCameraStats() {
    return request.get<ApiResponse<CameraStats>>('/api/v1/cameras/stats/overview')
  },

  // 获取摄像头预览地址
  getPreview(id: number) {
    return request.get<ApiResponse<{
      camera_id: number
      camera_code: string
      camera_name: string
      status: string
      stream_url: string
      preview_url: string
      media_proxy_name?: string
    }>>(`/api/v1/cameras/${id}/preview`)
  },


}

export const mediaProxyApi = {
  // 获取媒体代理列表
  getMediaProxies() {
    return request.get<ApiResponse<MediaProxy[]>>('/api/v1/cameras/media-proxies/')
  },

  // 创建媒体代理
  createMediaProxy(data: MediaProxyCreateForm) {
    return request.post<ApiResponse<MediaProxy>>('/api/v1/cameras/media-proxies/', data)
  },

  // 更新媒体代理
  updateMediaProxy(id: number, data: MediaProxyUpdateForm) {
    return request.put<ApiResponse<MediaProxy>>(`/api/v1/cameras/media-proxies/${id}`, data)
  },

  // 删除媒体代理
  deleteMediaProxy(id: number) {
    return request.delete<ApiResponse<{ message: string }>>(`/api/v1/cameras/media-proxies/${id}`)
  }
}

export const cameraGroupApi = {
  // 获取摄像头分组列表
  getCameraGroups() {
    return request.get<ApiResponse<CameraGroup[]>>('/api/v1/cameras/groups/')
  },

  // 创建摄像头分组
  createCameraGroup(data: CameraGroupCreateForm) {
    return request.post<ApiResponse<CameraGroup>>('/api/v1/cameras/groups/', data)
  },

  // 更新摄像头分组
  updateCameraGroup(id: number, data: CameraGroupUpdateForm) {
    return request.put<ApiResponse<CameraGroup>>(`/api/v1/cameras/groups/${id}`, data)
  },

  // 删除摄像头分组
  deleteCameraGroup(id: number) {
    return request.delete<ApiResponse<{ message: string }>>(`/api/v1/cameras/groups/${id}`)
  }
}