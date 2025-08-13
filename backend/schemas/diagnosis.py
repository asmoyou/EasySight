from pydantic import BaseModel
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from models.diagnosis import DiagnosisType, TaskStatus
from models.worker import WorkerStatus

# 诊断任务相关模式
class DiagnosisTaskCreate(BaseModel):
    name: str
    description: Optional[str] = None
    template_id: Optional[int] = None
    camera_ids: List[Union[int, str]] = []
    camera_groups: List[str] = []
    diagnosis_types: List[str] = []
    diagnosis_config: Dict[str, Any] = {}
    schedule_type: Optional[str] = None
    schedule_config: Dict[str, Any] = {}
    cron_expression: Optional[str] = None
    interval_minutes: Optional[int] = None
    threshold_config: Dict[str, Any] = {}
    # 前端兼容性字段
    target_id: Optional[int] = None
    target_type: Optional[str] = None
    diagnosis_type: Optional[str] = None
    
    def to_db_dict(self):
        """转换为数据库字段格式"""
        data = self.dict(exclude={'target_id', 'target_type', 'diagnosis_type'})
        
        # 处理target_id到camera_ids的映射
        if self.target_id is not None:
            if not data['camera_ids']:
                data['camera_ids'] = [self.target_id]
            elif self.target_id not in data['camera_ids']:
                data['camera_ids'].append(self.target_id)
        
        # 处理diagnosis_type到diagnosis_types的映射
        if self.diagnosis_type is not None:
            if not data['diagnosis_types']:
                data['diagnosis_types'] = [self.diagnosis_type]
            elif self.diagnosis_type not in data['diagnosis_types']:
                data['diagnosis_types'].append(self.diagnosis_type)
        
        return data

class DiagnosisTaskUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    template_id: Optional[int] = None
    camera_ids: Optional[List[Union[int, str]]] = None
    camera_groups: Optional[List[str]] = None
    diagnosis_types: Optional[List[str]] = None
    diagnosis_config: Optional[Dict[str, Any]] = None
    schedule_type: Optional[str] = None
    schedule_config: Optional[Dict[str, Any]] = None
    cron_expression: Optional[str] = None
    interval_minutes: Optional[int] = None
    threshold_config: Optional[Dict[str, Any]] = None
    status: Optional[TaskStatus] = None
    is_active: Optional[bool] = None
    # 前端兼容性字段
    target_id: Optional[int] = None
    target_type: Optional[str] = None
    diagnosis_type: Optional[str] = None
    
    def to_db_dict(self):
        """转换为数据库字段格式"""
        data = self.dict(exclude_unset=True, exclude={'target_id', 'target_type', 'diagnosis_type'})
        
        # 处理target_id到camera_ids的映射
        if self.target_id is not None:
            data['camera_ids'] = [self.target_id]
        
        # 处理diagnosis_type到diagnosis_types的映射
        if self.diagnosis_type is not None:
            data['diagnosis_types'] = [self.diagnosis_type]
        
        return data

class DiagnosisTaskResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    template_id: Optional[int]
    camera_ids: List[Union[int, str]] = []
    camera_groups: List[str] = []
    diagnosis_types: List[str] = []
    diagnosis_config: Dict[str, Any] = {}
    schedule_type: Optional[str]
    schedule_config: Dict[str, Any] = {}
    cron_expression: Optional[str]
    interval_minutes: Optional[int]
    threshold_config: Dict[str, Any] = {}
    status: TaskStatus
    is_active: bool = True
    is_scheduled: bool = False  # 前端期望的字段名，表示是否为定时任务
    assigned_worker: Optional[str]
    last_run: Optional[datetime] = None  # 前端期望的字段名
    next_run_time: Optional[datetime]
    run_count: int = 0  # 前端期望的字段名
    success_count: int = 0  # 前端期望的字段名
    error_count: int = 0  # 前端期望的字段名
    created_by_name: Optional[str] = None  # 前端期望的字段名
    created_by: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    # 前端兼容性字段
    target_id: Optional[int] = None  # 从camera_ids[0]映射而来
    target_type: str = "camera"  # 固定为camera类型
    diagnosis_type: Optional[str] = None  # 从diagnosis_types[0]映射而来
    
    class Config:
        from_attributes = True
        
    @classmethod
    def from_orm(cls, obj):
        """从ORM对象创建响应模型，处理字段名映射"""
        camera_ids = obj.camera_ids or []
        diagnosis_types = obj.diagnosis_types or []
        
        data = {
            'id': obj.id,
            'name': obj.name,
            'description': obj.description,
            'template_id': obj.template_id,
            'camera_ids': camera_ids,
            'camera_groups': obj.camera_groups or [],
            'diagnosis_types': diagnosis_types,
            'diagnosis_config': obj.diagnosis_config or {},
            'schedule_type': obj.schedule_type,
            'schedule_config': obj.schedule_config or {},
            'cron_expression': obj.cron_expression,
            'interval_minutes': obj.interval_minutes,
            'threshold_config': obj.threshold_config or {},
            'status': obj.status,
            'is_active': obj.is_active,
            'is_scheduled': bool(obj.cron_expression),  # 根据是否有cron表达式判断是否为定时任务
            'assigned_worker': obj.assigned_worker,
            'last_run': obj.last_run_time,  # 映射字段名
            'next_run_time': obj.next_run_time,
            'run_count': obj.total_runs,  # 映射字段名
            'success_count': obj.success_runs,  # 映射字段名
            'error_count': getattr(obj, 'error_runs', 0),  # 映射字段名，如果不存在则为0
            'created_by_name': getattr(obj, 'created_by_name', None),  # 映射字段名
            'created_by': obj.created_by,
            'created_at': obj.created_at,
            'updated_at': obj.updated_at,
            # 前端兼容性字段映射
            'target_id': camera_ids[0] if camera_ids else None,  # 取第一个摄像头ID
            'target_type': 'camera',  # 固定为camera类型
            'diagnosis_type': diagnosis_types[0] if diagnosis_types else None,  # 取第一个诊断类型
        }
        return cls(**data)

class DiagnosisTaskListResponse(BaseModel):
    tasks: List[DiagnosisTaskResponse]
    total: int
    skip: int
    limit: int

# Worker相关模式
class WorkerResponse(BaseModel):
    worker_id: str
    host: str
    port: int
    max_concurrent_tasks: int
    current_tasks: int
    capabilities: List[str]
    status: WorkerStatus
    last_heartbeat: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class WorkerListResponse(BaseModel):
    workers: List[WorkerResponse]
    total: int
    skip: int
    limit: int

class WorkerRegistrationRequest(BaseModel):
    worker_id: str
    host: str
    port: int
    max_concurrent_tasks: int = 3
    capabilities: List[str] = []

class WorkerRegistrationResponse(BaseModel):
    success: bool
    message: str
    worker_id: str

class WorkerHeartbeatRequest(BaseModel):
    worker_id: str
    current_tasks: int
    status: WorkerStatus

class WorkerTaskFetchRequest(BaseModel):
    worker_id: str
    max_tasks: int = 1
    capabilities: List[str] = []

class WorkerTaskFetchResponse(BaseModel):
    tasks: List[Dict[str, Any]]
    total_available: int
    message: Optional[str] = None

# 任务提交相关模式
class TaskSubmitResponse(BaseModel):
    task_id: int
    status: str
    message: str