from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc, text
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, date, timedelta, timezone
import json
import logging

from database import get_db
from models.diagnosis import (
    DiagnosisTask, DiagnosisResult, DiagnosisAlarm, DiagnosisTemplate, DiagnosisStatistics,
    DiagnosisType, DiagnosisStatus, TaskStatus
)
from models.user import User
from diagnosis.scheduler import task_scheduler
from diagnosis.worker import worker_pool
from diagnosis.executor import diagnosis_executor
from routers.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()

def process_suggestions(suggestions):
    """处理 suggestions 字段，确保返回正确的数据格式"""
    if not suggestions:
        return [], []
    
    # 如果是字符串，尝试解析为 JSON
    if isinstance(suggestions, str):
        try:
            suggestions = json.loads(suggestions)
        except (json.JSONDecodeError, TypeError):
            suggestions = []
    
    # 确保是列表
    if not isinstance(suggestions, list):
        suggestions = []
    
    # 转换为字典列表格式
    issues_found = []
    recommendations = []
    
    for item in suggestions:
        if isinstance(item, dict):
            issues_found.append(item)
            if 'recommendation' in item:
                recommendations.append(item['recommendation'])
        elif isinstance(item, str):
            recommendations.append(item)
            issues_found.append({'description': item, 'type': 'general'})
    
    return issues_found, recommendations

def get_score_assessment(score: Optional[float], threshold: Optional[float] = None) -> tuple[str, str]:
    """获取分数等级评估和描述"""
    if score is None:
        return "未知", "无法获取诊断分数"
    
    # 智能检测分数范围并标准化到0-100范围
    normalized_score = score
    
    # 如果分数在0-1之间，认为是百分比形式，转换为0-100
    if 0 <= score <= 1.0:
        normalized_score = score * 100
    # 如果分数大于100，可能是错误数据，限制在100以内
    elif score > 100:
        normalized_score = 100
    # 如果分数在1-100之间，直接使用
    else:
        normalized_score = score
    
    # 分数等级评估（0-100范围）
    if normalized_score >= 90:
        level = "优秀"
        description = "图像质量非常好，各项指标均达到最佳状态"
    elif normalized_score >= 80:
        level = "良好"
        description = "图像质量良好，大部分指标表现正常"
    elif normalized_score >= 70:
        level = "一般"
        description = "图像质量一般，部分指标可能需要关注"
    elif normalized_score >= 60:
        level = "较差"
        description = "图像质量较差，存在明显问题需要处理"
    else:
        level = "很差"
        description = "图像质量很差，存在严重问题需要立即处理"
    
    # 如果有阈值，添加阈值比较信息
    if threshold is not None:
        # 标准化阈值到相同范围
        normalized_threshold = threshold
        if 0 <= threshold <= 1.0 and score > 1.0:
            normalized_threshold = threshold * 100
        elif threshold > 1.0 and 0 <= score <= 1.0:
            normalized_threshold = threshold / 100
            
        if score < normalized_threshold:
            description += f"，当前分数({score:.2f})低于设定阈值({normalized_threshold:.2f})，建议检查设备状态"
        else:
            description += f"，当前分数({score:.2f})符合设定阈值({normalized_threshold:.2f})要求"
    
    return level, description

# Pydantic models
class DiagnosisTaskCreate(BaseModel):
    name: str
    diagnosis_type: DiagnosisType
    target_id: int
    target_type: str
    template_id: Optional[int] = None
    config: Dict[str, Any] = {}
    schedule_config: Dict[str, Any] = {}
    threshold_config: Dict[str, Any] = {}  # 添加阈值配置字段
    is_scheduled: bool = False
    description: Optional[str] = None

class DiagnosisTaskUpdate(BaseModel):
    name: Optional[str] = None
    diagnosis_type: Optional[DiagnosisType] = None
    target_id: Optional[int] = None
    template_id: Optional[int] = None
    config: Optional[Dict[str, Any]] = None
    schedule_config: Optional[Dict[str, Any]] = None
    threshold_config: Optional[Dict[str, Any]] = None  # 添加阈值配置字段
    is_scheduled: Optional[bool] = None
    is_active: Optional[bool] = None
    description: Optional[str] = None

class DiagnosisTaskResponse(BaseModel):
    id: int
    name: str
    diagnosis_type: DiagnosisType
    target_id: Optional[int]
    target_type: str
    template_id: Optional[int]
    template_name: Optional[str]
    config: Dict[str, Any]
    schedule_config: Dict[str, Any]
    threshold_config: Dict[str, Any] = {}  # 添加阈值配置字段
    status: TaskStatus
    is_scheduled: bool
    is_active: bool
    last_run: Optional[datetime]
    next_run: Optional[datetime]
    run_count: int
    success_count: int
    error_count: int
    created_by: str
    created_by_name: str
    created_at: datetime
    updated_at: datetime
    description: Optional[str]

class DiagnosisResultCreate(BaseModel):
    task_id: int
    status: DiagnosisStatus
    result_data: Dict[str, Any] = {}
    score: Optional[float] = None
    issues_found: List[Dict[str, Any]] = []
    recommendations: List[str] = []
    execution_time: Optional[float] = None
    error_message: Optional[str] = None

class DiagnosisResultResponse(BaseModel):
    id: int
    task_id: int
    task_name: str
    camera_name: Optional[str]  # 摄像头名称
    diagnosis_type: Optional[str]
    status: DiagnosisStatus
    result_data: Dict[str, Any]
    score: Optional[float]
    score_level: Optional[str] = None  # 分数等级评估
    score_description: Optional[str] = None  # 分数描述
    threshold: Optional[float] = None  # 阈值
    issues_found: List[Dict[str, Any]]
    recommendations: List[str]
    execution_time: Optional[float]  # 处理时间(ms)
    processing_time: Optional[float] = None  # 处理时间别名
    error_message: Optional[str]
    image_url: Optional[str]
    thumbnail_url: Optional[str]
    created_at: datetime  # 检测时间
    detected_at: Optional[datetime] = None  # 检测时间别名
    
    class Config:
        from_attributes = True
        
    def __init__(self, **data):
        super().__init__(**data)
        # 设置别名字段
        if self.execution_time is not None:
            self.processing_time = self.execution_time
        if self.created_at is not None:
            self.detected_at = self.created_at

class DiagnosisResultListResponse(BaseModel):
    results: List[DiagnosisResultResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

class DiagnosisAlarmCreate(BaseModel):
    result_id: int
    alarm_type: str
    severity: str
    title: str
    description: str
    threshold_config: Dict[str, Any] = {}
    current_value: Optional[float] = None
    threshold_value: Optional[float] = None

class DiagnosisAlarmResponse(BaseModel):
    id: int
    result_id: int
    task_name: str
    alarm_type: str
    severity: str
    title: str
    description: str
    threshold_config: Dict[str, Any]
    current_value: Optional[float]
    threshold_value: Optional[float]
    is_acknowledged: bool
    acknowledged_by: Optional[int]
    acknowledged_by_name: Optional[str]
    acknowledged_at: Optional[datetime]
    created_at: datetime
    # 新增字段用于前端显示
    thumbnail_url: Optional[str] = None
    device_name: Optional[str] = None
    device_location: Optional[str] = None
    detection_data: Optional[Dict[str, Any]] = None
    status: str = "unread"  # unread, read, handled, ignored
    level: str = "medium"  # 映射severity字段

class DiagnosisTemplateCreate(BaseModel):
    name: str
    diagnosis_type: DiagnosisType
    config_template: Dict[str, Any]
    default_schedule: Dict[str, Any] = {}
    threshold_config: Dict[str, Any] = {}
    description: Optional[str] = None
    is_public: bool = True

class DiagnosisTemplateUpdate(BaseModel):
    name: Optional[str] = None
    config_template: Optional[Dict[str, Any]] = None
    default_schedule: Optional[Dict[str, Any]] = None
    threshold_config: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None
    is_public: Optional[bool] = None
    description: Optional[str] = None

class DiagnosisTemplateResponse(BaseModel):
    id: int
    name: str
    diagnosis_types: List[str]
    default_config: Dict[str, Any]
    default_schedule: Dict[str, Any]
    threshold_config: Dict[str, Any]
    is_active: bool
    is_system: bool
    usage_count: int
    created_by: str
    created_by_name: str
    created_at: datetime
    updated_at: datetime
    description: Optional[str]

class DiagnosisStatsResponse(BaseModel):
    total_tasks: int
    active_tasks: int
    running_tasks: int
    scheduled_tasks: int
    total_results: int
    success_results: int
    failed_results: int
    warning_results: int
    total_alarms: int
    unacknowledged_alarms: int
    critical_alarms: int
    avg_score: float
    by_type: Dict[str, int]
    by_status: Dict[str, int]
    trend_data: List[Dict[str, Any]]

# 诊断任务管理
@router.get("/tasks/", response_model=List[DiagnosisTaskResponse])
async def get_diagnosis_tasks(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    diagnosis_type: Optional[DiagnosisType] = Query(None, description="诊断类型筛选"),
    status: Optional[TaskStatus] = Query(None, description="任务状态筛选"),
    is_active: Optional[bool] = Query(None, description="是否启用"),
    is_scheduled: Optional[bool] = Query(None, description="是否定时任务"),
    target_type: Optional[str] = Query(None, description="目标类型筛选"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取诊断任务列表"""
    conditions = []
    
    if search:
        search_pattern = f"%{search}%"
        conditions.append(
            or_(
                DiagnosisTask.name.ilike(search_pattern),
                DiagnosisTask.description.ilike(search_pattern)
            )
        )
    
    if diagnosis_type:
        # 使用JSON操作符检查diagnosis_types数组中是否包含指定类型
        conditions.append(DiagnosisTask.diagnosis_types.contains([diagnosis_type.value]))
    
    if status:
        conditions.append(DiagnosisTask.status == status)
    
    if is_active is not None:
        conditions.append(DiagnosisTask.is_active == is_active)
    
    if is_scheduled is not None:
        conditions.append(DiagnosisTask.is_scheduled == is_scheduled)
    
    if target_type:
        conditions.append(DiagnosisTask.target_type == target_type)
    
    query = select(DiagnosisTask).order_by(desc(DiagnosisTask.created_at))
    if conditions:
        query = query.where(and_(*conditions))
    
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    
    result = await db.execute(query)
    tasks = result.scalars().all()
    
    # 获取创建者信息和模板信息
    creator_map = {}
    template_map = {}
    
    if tasks:
        # 将字符串类型的 created_by 转换为整数类型
        creator_ids = []
        template_ids = []
        for t in tasks:
            if t.created_by and t.created_by.isdigit():
                creator_ids.append(int(t.created_by))
            if hasattr(t, 'template_id') and t.template_id:
                template_ids.append(t.template_id)
        
        if creator_ids:
            creator_result = await db.execute(select(User).where(User.id.in_(creator_ids)))
            creators = creator_result.scalars().all()
            creator_map = {str(c.id): c.username for c in creators}  # 使用字符串作为键
        
        if template_ids:
            template_result = await db.execute(select(DiagnosisTemplate).where(DiagnosisTemplate.id.in_(template_ids)))
            templates = template_result.scalars().all()
            template_map = {t.id: t.name for t in templates}
    
    return [DiagnosisTaskResponse(
        id=task.id,
        name=task.name,
        diagnosis_type=task.diagnosis_types[0] if task.diagnosis_types else None,  # 取第一个类型作为主类型
        target_id=task.camera_ids[0] if task.camera_ids else None,  # 取第一个摄像头ID
        target_type='camera',
        template_id=task.template_id,
        template_name=template_map.get(task.template_id) if hasattr(task, 'template_id') and task.template_id else None,
        config=task.diagnosis_config or {},
        schedule_config=task.schedule_config or {},
        threshold_config=task.threshold_config or {},  # 添加阈值配置
        status=task.status,
        is_scheduled=task.schedule_type is not None,  # 根据 schedule_type 判断是否为定时任务
        is_active=task.is_active,
        last_run=task.last_run_time,
        next_run=task.next_run_time,
        run_count=task.total_runs or 0,
        success_count=task.success_runs or 0,
        error_count=(task.total_runs or 0) - (task.success_runs or 0),
        created_by=task.created_by,
        created_by_name=creator_map.get(task.created_by, ""),
        created_at=task.created_at,
        updated_at=task.updated_at,
        description=task.description
    ) for task in tasks]

@router.post("/tasks/", response_model=DiagnosisTaskResponse)
async def create_diagnosis_task(
    task_data: DiagnosisTaskCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建诊断任务"""
    # 验证模板是否存在（如果指定了模板）
    template_name = None
    if task_data.template_id:
        template_result = await db.execute(select(DiagnosisTemplate).where(DiagnosisTemplate.id == task_data.template_id))
        template = template_result.scalar_one_or_none()
        if not template:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="指定的诊断模板不存在"
            )
        template_name = template.name
    
    task_dict = task_data.dict()
    task_dict['created_by'] = str(current_user.id)  # 转换为字符串类型
    
    # 字段名转换：前端使用 diagnosis_type，数据库使用 diagnosis_types
    if 'diagnosis_type' in task_dict:
        diagnosis_type = task_dict.pop('diagnosis_type')
        # 将枚举值转换为字符串值以便JSON序列化
        task_dict['diagnosis_types'] = [diagnosis_type.value] if diagnosis_type else []
    
    # 字段名转换：前端使用 target_id，数据库使用 camera_ids
    if 'target_id' in task_dict:
        target_id = task_dict.pop('target_id')
        task_dict['camera_ids'] = [target_id] if target_id else []
    
    # 字段名转换：前端使用 config，数据库使用 diagnosis_config
    if 'config' in task_dict:
        config = task_dict.pop('config')
        task_dict['diagnosis_config'] = config
    
    # 处理定时任务相关字段
    is_scheduled = task_dict.pop('is_scheduled', None)
    schedule_config = task_dict.get('schedule_config', {})
    
    if is_scheduled:
        # 开启定时任务
        task_dict['schedule_type'] = 'cron'
        if schedule_config and 'cron_expression' in schedule_config:
            task_dict['cron_expression'] = schedule_config['cron_expression']
        else:
            # 如果没有提供cron表达式，使用默认值
            task_dict['cron_expression'] = '0 0 * * *'  # 每天午夜执行
            task_dict['schedule_config'] = {'cron_expression': '0 0 * * *'}
    else:
        # 不是定时任务
        task_dict['schedule_type'] = None
        task_dict['cron_expression'] = None
        if not schedule_config:
            task_dict['schedule_config'] = {}
    
    # threshold_config 字段直接保存，无需转换
    # 移除前端字段，数据库中不存在
    task_dict.pop('target_type', None)
    
    task = DiagnosisTask(**task_dict)
    db.add(task)
    await db.commit()
    await db.refresh(task)
    
    return DiagnosisTaskResponse(
        id=task.id,
        name=task.name,
        diagnosis_type=task.diagnosis_types[0] if task.diagnosis_types else None,  # 取第一个类型作为主类型
        target_id=task.camera_ids[0] if task.camera_ids else None,  # 取第一个摄像头ID
        target_type='camera',
        template_id=task.template_id,
        template_name=template_name,
        config=task.diagnosis_config or {},
        schedule_config=task.schedule_config or {},
        threshold_config=task.threshold_config or {},  # 添加阈值配置
        status=task.status,
        is_scheduled=task.schedule_type is not None,  # 根据 schedule_type 判断是否为定时任务
        is_active=task.is_active,
        last_run=task.last_run_time,
        next_run=task.next_run_time,
        run_count=task.total_runs or 0,
        success_count=task.success_runs or 0,
        error_count=(task.total_runs or 0) - (task.success_runs or 0),
        created_by=task.created_by,
        created_by_name=current_user.username,
        created_at=task.created_at,
        updated_at=task.updated_at,
        description=task.description
    )

@router.get("/tasks/{task_id}", response_model=DiagnosisTaskResponse)
async def get_diagnosis_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取诊断任务详情"""
    result = await db.execute(select(DiagnosisTask).where(DiagnosisTask.id == task_id))
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="诊断任务不存在"
        )
    
    # 获取模板和创建者信息
    template_name = None
    template_id = None
    if hasattr(task, 'template_id') and task.template_id:
        template_result = await db.execute(select(DiagnosisTemplate).where(DiagnosisTemplate.id == task.template_id))
        template = template_result.scalar_one_or_none()
        if template:
            template_name = template.name
            template_id = template.id
    
    # 将字符串类型的 created_by 转换为整数类型进行查询
    creator_name = ""
    if task.created_by and task.created_by.isdigit():
        creator_result = await db.execute(select(User).where(User.id == int(task.created_by)))
        creator = creator_result.scalar_one_or_none()
        creator_name = creator.username if creator else ""
    
    return DiagnosisTaskResponse(
        id=task.id,
        name=task.name,
        diagnosis_type=task.diagnosis_types[0] if task.diagnosis_types else None,  # 取第一个类型作为主类型
        target_id=task.camera_ids[0] if task.camera_ids else None,  # 取第一个摄像头ID
        target_type='camera',
        template_id=template_id,
        template_name=template_name,
        config=task.diagnosis_config or {},
        schedule_config=task.schedule_config or {},
        threshold_config=task.threshold_config or {},  # 添加阈值配置
        status=task.status,
        is_scheduled=task.schedule_type is not None,  # 根据 schedule_type 判断是否为定时任务
        is_active=task.is_active,
        last_run=task.last_run_time,
        next_run=task.next_run_time,
        run_count=task.total_runs or 0,
        success_count=task.success_runs or 0,
        error_count=(task.total_runs or 0) - (task.success_runs or 0),
        created_by=task.created_by,
        created_by_name=creator_name,
        created_at=task.created_at,
        updated_at=task.updated_at,
        description=task.description
    )

@router.put("/tasks/{task_id}", response_model=DiagnosisTaskResponse)
async def update_diagnosis_task(
    task_id: int,
    task_data: DiagnosisTaskUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新诊断任务"""
    result = await db.execute(select(DiagnosisTask).where(DiagnosisTask.id == task_id))
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="诊断任务不存在"
        )
    
    update_data = task_data.dict(exclude_unset=True)
    
    # 字段映射：前端字段名 -> 数据库字段名
    field_mapping = {
        'diagnosis_type': 'diagnosis_types',
        'target_id': 'camera_ids',
        'config': 'diagnosis_config'
    }
    
    # 处理定时任务相关字段
    is_scheduled = update_data.get('is_scheduled')
    schedule_config = update_data.get('schedule_config')
    
    if is_scheduled is not None:
        if is_scheduled:
            # 开启定时任务
            task.schedule_type = 'cron'
            if schedule_config and 'cron_expression' in schedule_config:
                task.cron_expression = schedule_config['cron_expression']
                task.schedule_config = schedule_config
            else:
                # 如果没有提供cron表达式，使用默认值
                task.cron_expression = '0 0 * * *'  # 每天午夜执行
                task.schedule_config = {'cron_expression': '0 0 * * *'}
        else:
            # 关闭定时任务
            task.schedule_type = None
            task.cron_expression = None
            task.schedule_config = {}
    elif schedule_config is not None:
        # 只更新调度配置，不改变is_scheduled状态
        if task.schedule_type == 'cron' and 'cron_expression' in schedule_config:
            task.cron_expression = schedule_config['cron_expression']
            task.schedule_config = schedule_config
    
    # threshold_config 字段直接更新，无需映射
    
    for field, value in update_data.items():
        # 跳过已处理的定时任务相关字段
        if field in ['is_scheduled', 'schedule_config']:
            continue
            
        if field in field_mapping:
            db_field = field_mapping[field]
            if field == 'diagnosis_type' and value:
                # 诊断类型转换为列表，确保枚举值被转换为字符串
                if isinstance(value, DiagnosisType):
                    setattr(task, db_field, [value.value])
                else:
                    setattr(task, db_field, [value])
            elif field == 'target_id' and value:
                # 目标ID转换为列表
                setattr(task, db_field, [value])
            elif field == 'config':
                # 配置直接映射
                setattr(task, db_field, value)
        else:
            # 其他字段直接设置
            setattr(task, field, value)
    
    await db.commit()
    await db.refresh(task)
    
    # 获取相关信息
    template_name = None
    template_id = None
    if hasattr(task, 'template_id') and task.template_id:
        template_result = await db.execute(select(DiagnosisTemplate).where(DiagnosisTemplate.id == task.template_id))
        template = template_result.scalar_one_or_none()
        if template:
            template_name = template.name
            template_id = template.id
    
    # 将字符串类型的 created_by 转换为整数类型进行查询
    creator_name = ""
    if task.created_by and task.created_by.isdigit():
        creator_result = await db.execute(select(User).where(User.id == int(task.created_by)))
        creator = creator_result.scalar_one_or_none()
        creator_name = creator.username if creator else ""
    
    return DiagnosisTaskResponse(
        id=task.id,
        name=task.name,
        diagnosis_type=task.diagnosis_types[0] if task.diagnosis_types else None,  # 取第一个类型作为主类型
        target_id=task.camera_ids[0] if task.camera_ids else None,  # 取第一个摄像头ID
        target_type='camera',
        template_id=template_id,
        template_name=template_name,
        config=task.diagnosis_config or {},
        schedule_config=task.schedule_config or {},
        threshold_config=task.threshold_config or {},  # 添加阈值配置
        status=task.status,
        is_scheduled=task.schedule_type is not None,  # 根据 schedule_type 判断是否为定时任务
        is_active=task.is_active,
        last_run=task.last_run_time,
        next_run=task.next_run_time,
        run_count=task.total_runs or 0,
        success_count=task.success_runs or 0,
        error_count=(task.total_runs or 0) - (task.success_runs or 0),
        created_by=task.created_by,
        created_by_name=creator_name,
        created_at=task.created_at,
        updated_at=task.updated_at,
        description=task.description
    )

@router.delete("/tasks/{task_id}")
async def delete_diagnosis_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除诊断任务"""
    result = await db.execute(select(DiagnosisTask).where(DiagnosisTask.id == task_id))
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="诊断任务不存在"
        )
    
    await db.delete(task)
    await db.commit()
    
    return {"message": "诊断任务删除成功"}

@router.post("/tasks/{task_id}/run")
async def run_diagnosis_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """手动执行诊断任务"""
    result = await db.execute(select(DiagnosisTask).where(DiagnosisTask.id == task_id))
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="诊断任务不存在"
        )
    
    if not task.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="任务未启用，无法执行"
        )
    
    if task.status == TaskStatus.RUNNING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="任务正在运行中"
        )
    
    # 更新任务状态
    task.status = TaskStatus.RUNNING
    task.last_run_time = datetime.utcnow()
    task.total_runs += 1
    
    await db.commit()
    
    # 使用新的诊断执行系统
    from diagnosis.scheduler import task_scheduler
    
    # 立即执行任务
    execution_result = await task_scheduler.execute_task_immediately(task_id)
    
    if execution_result.get('error'):
        # 如果执行失败，恢复任务状态
        task.status = TaskStatus.FAILED
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"任务执行失败: {execution_result['error']}"
        )
    
    return {
        "message": "诊断任务执行完成",
        "result": execution_result
    }

# 诊断结果管理
@router.get("/results/", response_model=DiagnosisResultListResponse)
async def get_diagnosis_results(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    task_id: Optional[int] = Query(None, description="任务ID筛选"),
    status: Optional[DiagnosisStatus] = Query(None, description="状态筛选"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取诊断结果列表"""
    conditions = []
    
    if task_id:
        conditions.append(DiagnosisResult.task_id == task_id)
    
    if status:
        conditions.append(DiagnosisResult.diagnosis_status == status)
    
    if start_date:
        conditions.append(DiagnosisResult.created_at >= start_date)
    
    if end_date:
        end_datetime = datetime.combine(end_date, datetime.max.time())
        conditions.append(DiagnosisResult.created_at <= end_datetime)
    
    # 获取总数
    count_query = select(func.count(DiagnosisResult.id))
    if conditions:
        count_query = count_query.where(and_(*conditions))
    
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # 获取分页数据
    query = select(DiagnosisResult).order_by(desc(DiagnosisResult.created_at))
    if conditions:
        query = query.where(and_(*conditions))
    
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    
    result = await db.execute(query)
    results = result.scalars().all()
    
    # 获取任务信息和摄像头信息
    task_map = {}
    camera_map = {}
    if results:
        task_ids = [r.task_id for r in results]
        task_result = await db.execute(select(DiagnosisTask).where(DiagnosisTask.id.in_(task_ids)))
        tasks = task_result.scalars().all()
        task_map = {t.id: t.name for t in tasks}
        
        # 获取摄像头信息
        from models.camera import Camera
        camera_ids = []
        for task in tasks:
            if task.camera_ids:
                camera_ids.extend(task.camera_ids)
        
        if camera_ids:
            camera_result = await db.execute(select(Camera).where(Camera.id.in_(camera_ids)))
            cameras = camera_result.scalars().all()
            camera_map = {c.id: c.name for c in cameras}
    
    response_list = []
    for result in results:
        issues_found, recommendations = process_suggestions(result.suggestions)
        
        # 获取摄像头名称
        camera_name = None
        task = next((t for t in tasks if t.id == result.task_id), None)
        if task and task.camera_ids:
            camera_id = task.camera_ids[0]  # 取第一个摄像头
            camera_name = camera_map.get(camera_id)
        
        # 获取分数评估
        score_level, score_description = get_score_assessment(result.score, result.threshold)
        
        response_list.append(DiagnosisResultResponse(
            id=result.id,
            task_id=result.task_id,
            task_name=task_map.get(result.task_id, ""),
            camera_name=camera_name,
            diagnosis_type=result.diagnosis_type,
            status=result.diagnosis_status,
            result_data=result.result_data,
            score=result.score,
            score_level=score_level,
            score_description=score_description,
            threshold=result.threshold,
            issues_found=issues_found,
            recommendations=recommendations,
            execution_time=result.processing_time,
            error_message=result.error_message,
            image_url=result.image_url,
            thumbnail_url=result.thumbnail_url,
            created_at=result.created_at
        ))
    
    total_pages = (total + page_size - 1) // page_size
    
    return DiagnosisResultListResponse(
        results=response_list,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )

@router.post("/results/", response_model=DiagnosisResultResponse)
async def create_diagnosis_result(
    result_data: DiagnosisResultCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建诊断结果"""
    # 验证任务是否存在
    task_result = await db.execute(select(DiagnosisTask).where(DiagnosisTask.id == result_data.task_id))
    task = task_result.scalar_one_or_none()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="指定的诊断任务不存在"
        )
    
    result = DiagnosisResult(**result_data.dict())
    db.add(result)
    await db.commit()
    await db.refresh(result)
    
    # 更新任务统计
    if result_data.status == DiagnosisStatus.SUCCESS:
        task.success_count += 1
    elif result_data.status == DiagnosisStatus.FAILED:
        task.error_count += 1
    
    task.status = TaskStatus.IDLE
    await db.commit()
    
    # 处理 suggestions 字段
    issues_found, recommendations = process_suggestions(result.suggestions)
    
    return DiagnosisResultResponse(
        id=result.id,
        task_id=result.task_id,
        task_name=task.name,
        diagnosis_type=result.diagnosis_type,
        status=result.diagnosis_status,
        result_data=result.result_data,
        score=result.score,
        issues_found=issues_found,
        recommendations=recommendations,
        execution_time=result.processing_time,
        error_message=result.error_message,
        image_url=result.image_url,
        thumbnail_url=result.thumbnail_url,
        created_at=result.created_at
    )

@router.get("/results/{result_id}", response_model=DiagnosisResultResponse)
async def get_diagnosis_result(
    result_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取诊断结果详情"""
    result = await db.execute(select(DiagnosisResult).where(DiagnosisResult.id == result_id))
    diagnosis_result = result.scalar_one_or_none()
    
    if not diagnosis_result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="诊断结果不存在"
        )
    
    # 获取任务信息
    task_result = await db.execute(select(DiagnosisTask).where(DiagnosisTask.id == diagnosis_result.task_id))
    task = task_result.scalar_one_or_none()
    task_name = task.name if task else "未知任务"
    
    # 获取摄像头信息
    camera_name = None
    if task and task.camera_ids:
        from models.camera import Camera
        camera_result = await db.execute(select(Camera).where(Camera.id == task.camera_ids[0]))
        camera = camera_result.scalar_one_or_none()
        camera_name = camera.name if camera else None
    
    # 处理 suggestions 字段
    issues_found, recommendations = process_suggestions(diagnosis_result.suggestions)
    
    # 获取分数评估
    score_level, score_description = get_score_assessment(diagnosis_result.score, diagnosis_result.threshold)
    
    return DiagnosisResultResponse(
        id=diagnosis_result.id,
        task_id=diagnosis_result.task_id,
        task_name=task_name,
        camera_name=camera_name,
        diagnosis_type=diagnosis_result.diagnosis_type,
        status=diagnosis_result.diagnosis_status,
        result_data=diagnosis_result.result_data,
        score=diagnosis_result.score,
        score_level=score_level,
        score_description=score_description,
        threshold=diagnosis_result.threshold,
        issues_found=issues_found,
        recommendations=recommendations,
        execution_time=diagnosis_result.processing_time,
        error_message=diagnosis_result.error_message,
        image_url=diagnosis_result.image_url,
        thumbnail_url=diagnosis_result.thumbnail_url,
        created_at=diagnosis_result.created_at
    )

# 诊断告警管理
@router.get("/alarms/", response_model=List[DiagnosisAlarmResponse])
async def get_diagnosis_alarms(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    severity: Optional[str] = Query(None, description="严重程度筛选"),
    is_acknowledged: Optional[bool] = Query(None, description="是否已确认"),
    alarm_type: Optional[str] = Query(None, description="告警类型筛选"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取诊断告警列表"""
    conditions = []
    
    if severity:
        conditions.append(DiagnosisAlarm.severity == severity)
    
    if is_acknowledged is not None:
        conditions.append(DiagnosisAlarm.is_acknowledged == is_acknowledged)
    
    if alarm_type:
        conditions.append(DiagnosisAlarm.alarm_type == alarm_type)
    
    query = select(DiagnosisAlarm).order_by(desc(DiagnosisAlarm.created_at))
    if conditions:
        query = query.where(and_(*conditions))
    
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    
    result = await db.execute(query)
    alarms = result.scalars().all()
    
    # 获取任务、确认人和结果信息
    task_map = {}
    acknowledger_map = {}
    result_map = {}
    camera_map = {}
    
    if alarms:
        # 获取诊断结果信息
        result_ids = [a.result_id for a in alarms]
        result_query = await db.execute(
            select(DiagnosisResult)
            .where(DiagnosisResult.id.in_(result_ids))
        )
        results = result_query.scalars().all()
        result_map = {r.id: r for r in results}
        
        # 获取任务信息
        task_ids = [r.task_id for r in results]
        if task_ids:
            task_result = await db.execute(select(DiagnosisTask).where(DiagnosisTask.id.in_(task_ids)))
            tasks = task_result.scalars().all()
            task_name_map = {t.id: t.name for t in tasks}
            task_map = {r.id: task_name_map.get(r.task_id, "") for r in results}
            
            # 获取摄像头信息
            camera_ids = []
            for task in tasks:
                if task.camera_ids:
                    camera_ids.extend(task.camera_ids)
            camera_ids = list(set(camera_ids))  # 去重
            
            if camera_ids:
                from models.camera import Camera
                camera_result = await db.execute(select(Camera).where(Camera.id.in_(camera_ids)))
                cameras = camera_result.scalars().all()
                camera_name_map = {c.id: c for c in cameras}
                # 建立result_id到camera的映射
                for task in tasks:
                    if task.camera_ids:
                        for result in results:
                            if result.task_id == task.id and result.camera_id in camera_name_map:
                                camera_map[result.id] = camera_name_map[result.camera_id]
        
        # 获取确认人信息
        acknowledger_ids = [a.acknowledged_by for a in alarms if a.acknowledged_by]
        if acknowledger_ids:
            acknowledger_result = await db.execute(select(User).where(User.id.in_(acknowledger_ids)))
            acknowledgers = acknowledger_result.scalars().all()
            acknowledger_map = {u.id: u.username for u in acknowledgers}
    
    return [DiagnosisAlarmResponse(
        id=alarm.id,
        result_id=alarm.result_id,
        task_name=task_map.get(alarm.result_id, ""),
        alarm_type=alarm.alarm_type,
        severity=alarm.severity,
        title=alarm.title,
        description=alarm.description,
        threshold_config=alarm.threshold_config,
        current_value=alarm.current_value,
        threshold_value=alarm.threshold_value,
        is_acknowledged=alarm.is_acknowledged,
        acknowledged_by=alarm.acknowledged_by,
        acknowledged_by_name=acknowledger_map.get(alarm.acknowledged_by),
        acknowledged_at=alarm.acknowledged_at,
        created_at=alarm.created_at,
        # 填充新增字段
        thumbnail_url=result_map[alarm.result_id].thumbnail_url if alarm.result_id in result_map else None,
        device_name=camera_map[alarm.result_id].name if alarm.result_id in camera_map else None,
        device_location=camera_map[alarm.result_id].location if alarm.result_id in camera_map else None,
        detection_data={
            "score": result_map[alarm.result_id].score,
            "threshold": alarm.threshold_value or getattr(result_map[alarm.result_id], 'threshold', None)
        } if alarm.result_id in result_map else None,
        status="read" if alarm.is_acknowledged else "unread",
        level=alarm.severity.lower() if alarm.severity else "medium"
    ) for alarm in alarms]

@router.post("/alarms/{alarm_id}/acknowledge")
async def acknowledge_diagnosis_alarm(
    alarm_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """确认诊断告警"""
    result = await db.execute(select(DiagnosisAlarm).where(DiagnosisAlarm.id == alarm_id))
    alarm = result.scalar_one_or_none()
    
    if not alarm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="诊断告警不存在"
        )
    
    if alarm.is_acknowledged:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="告警已被确认"
        )
    
    alarm.is_acknowledged = True
    alarm.acknowledged_by = current_user.id
    alarm.acknowledged_at = datetime.utcnow()
    
    await db.commit()
    
    return {"message": "告警确认成功"}

class AlarmStatusUpdate(BaseModel):
    status: str

@router.put("/alarms/{alarm_id}/status")
async def update_alarm_status(
    alarm_id: int,
    status_data: AlarmStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新告警状态"""
    # 查询告警
    result = await db.execute(select(DiagnosisAlarm).where(DiagnosisAlarm.id == alarm_id))
    alarm = result.scalar_one_or_none()
    
    if not alarm:
        raise HTTPException(status_code=404, detail="告警不存在")
    
    # 更新状态 - 将status映射到is_acknowledged字段
    status = status_data.status
    if status in ["read", "handled"]:
        alarm.is_acknowledged = True
        alarm.acknowledged_by = current_user.id
        alarm.acknowledged_at = func.now()
    elif status == "ignored":
        alarm.is_acknowledged = False
        alarm.acknowledged_by = None
        alarm.acknowledged_at = None
    
    await db.commit()
    
    return {"message": "告警状态更新成功"}

class BatchAlarmStatusUpdate(BaseModel):
    alarm_ids: List[int]
    status: str

@router.put("/alarms/batch-status")
async def batch_update_alarm_status(
    status_data: BatchAlarmStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """批量更新告警状态"""
    # 查询告警
    alarm_ids = status_data.alarm_ids
    status = status_data.status
    result = await db.execute(select(DiagnosisAlarm).where(DiagnosisAlarm.id.in_(alarm_ids)))
    alarms = result.scalars().all()
    
    if not alarms:
        raise HTTPException(status_code=404, detail="未找到指定的告警")
    
    # 批量更新状态 - 将status映射到is_acknowledged字段
    for alarm in alarms:
        if status in ["read", "handled"]:
            alarm.is_acknowledged = True
            alarm.acknowledged_by = current_user.id
            alarm.acknowledged_at = func.now()
        elif status == "ignored":
            alarm.is_acknowledged = False
            alarm.acknowledged_by = None
            alarm.acknowledged_at = None
    
    await db.commit()
    
    return {"message": f"成功更新 {len(alarms)} 条告警状态"}

@router.delete("/alarms/{alarm_id}")
async def delete_alarm(
    alarm_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除告警"""
    # 查询告警
    result = await db.execute(select(DiagnosisAlarm).where(DiagnosisAlarm.id == alarm_id))
    alarm = result.scalar_one_or_none()
    
    if not alarm:
        raise HTTPException(status_code=404, detail="告警不存在")
    
    # 删除告警
    await db.delete(alarm)
    await db.commit()
    
    return {"message": "告警删除成功"}

@router.delete("/alarms/clear-all")
async def clear_all_alarms(
    confirmed: bool = Query(False, description="确认清空所有告警"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """清空所有告警"""
    if not confirmed:
        raise HTTPException(status_code=400, detail="请确认清空所有告警操作")
    
    # 删除所有告警
    result = await db.execute(select(func.count(DiagnosisAlarm.id)))
    total_count = result.scalar()
    
    await db.execute(text("DELETE FROM diagnosis_alarms"))
    await db.commit()
    
    return {"message": f"成功清空 {total_count} 条告警"}

# 诊断模板管理
@router.get("/templates/", response_model=List[DiagnosisTemplateResponse])
async def get_diagnosis_templates(
    diagnosis_type: Optional[DiagnosisType] = Query(None, description="诊断类型筛选"),
    is_public: Optional[bool] = Query(None, description="是否公开"),
    is_active: Optional[bool] = Query(None, description="是否启用"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取诊断模板列表"""
    conditions = []
    
    # 注意：diagnosis_types 现在是 JSON 数组，需要使用 JSON 操作符
    # if diagnosis_type:
    #     conditions.append(DiagnosisTemplate.diagnosis_types.contains([diagnosis_type]))
    
    if is_public is not None:
        conditions.append(DiagnosisTemplate.is_system == (not is_public))  # is_public 的反义是 is_system
    
    if is_active is not None:
        conditions.append(DiagnosisTemplate.is_active == is_active)
    
    query = select(DiagnosisTemplate).order_by(desc(DiagnosisTemplate.created_at))
    if conditions:
        query = query.where(and_(*conditions))
    
    result = await db.execute(query)
    templates = result.scalars().all()
    
    # 获取创建者信息
    creator_map = {}
    if templates:
        # 获取创建者信息
        creator_ids = []
        for t in templates:
            if t.created_by and t.created_by not in creator_ids:
                try:
                    creator_ids.append(int(t.created_by))
                except ValueError:
                    # 如果created_by是字符串（如'admin'），跳过
                    pass
        
        creator_map = {}
        if creator_ids:
            creator_result = await db.execute(select(User).where(User.id.in_(creator_ids)))
            creators = creator_result.scalars().all()
            creator_map = {str(c.id): c.username for c in creators}
    
    return [DiagnosisTemplateResponse(
        id=template.id,
        name=template.name,
        diagnosis_types=template.diagnosis_types or [],
        default_config=template.default_config,
        default_schedule=template.default_schedule,
        threshold_config=template.threshold_config,
        is_active=template.is_active,
        is_system=template.is_system,
        usage_count=template.usage_count,
        created_by=template.created_by,
        created_by_name=creator_map.get(template.created_by, ""),
        created_at=template.created_at,
        updated_at=template.updated_at,
        description=template.description
    ) for template in templates]

@router.put("/templates/{template_id}", response_model=DiagnosisTemplateResponse)
async def update_diagnosis_template(
    template_id: int,
    template_data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新诊断模板"""
    try:
        # 查找模板
        result = await db.execute(select(DiagnosisTemplate).where(DiagnosisTemplate.id == template_id))
        template = result.scalar_one_or_none()
        
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="模板不存在"
            )
        
        # 更新字段
        for key, value in template_data.items():
            if hasattr(template, key):
                # 特殊处理diagnosis_type字段，确保枚举值被转换为字符串
                if key == 'diagnosis_type' and value:
                    from models.diagnosis import DiagnosisType
                    if isinstance(value, DiagnosisType):
                        setattr(template, 'diagnosis_types', [value.value])
                    else:
                        setattr(template, 'diagnosis_types', [value])
                elif key == 'diagnosis_types' and value:
                    # 如果直接更新diagnosis_types，确保所有值都是字符串
                    from models.diagnosis import DiagnosisType
                    string_values = []
                    for v in value if isinstance(value, list) else [value]:
                        if isinstance(v, DiagnosisType):
                            string_values.append(v.value)
                        else:
                            string_values.append(v)
                    setattr(template, key, string_values)
                else:
                    setattr(template, key, value)
        
        await db.commit()
        await db.refresh(template)
        
        # 获取创建者信息
        creator_name = ""
        if template.created_by:
            try:
                creator_id = int(template.created_by)
                creator_result = await db.execute(select(User).where(User.id == creator_id))
                creator = creator_result.scalar_one_or_none()
                if creator:
                    creator_name = creator.username
            except (ValueError, TypeError):
                # 如果created_by不是有效的整数，跳过获取创建者信息
                pass
        
        return DiagnosisTemplateResponse(
            id=template.id,
            name=template.name,
            diagnosis_types=template.diagnosis_types or [],
            default_config=template.default_config,
            default_schedule=template.default_schedule,
            threshold_config=template.threshold_config,
            is_active=template.is_active,
            is_system=template.is_system,
            usage_count=template.usage_count,
            created_by=template.created_by,
            created_by_name=creator_name,
            created_at=template.created_at,
            updated_at=template.updated_at,
            description=template.description
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新模板失败: {str(e)}"
        )

@router.delete("/templates/{template_id}")
async def delete_diagnosis_template(
    template_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除诊断模板"""
    try:
        # 查找模板
        result = await db.execute(select(DiagnosisTemplate).where(DiagnosisTemplate.id == template_id))
        template = result.scalar_one_or_none()
        
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="模板不存在"
            )
        
        # 检查是否为系统模板
        if template.is_system:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="系统模板不能删除"
            )
        
        # 注意：当前数据库设计中任务和模板之间没有直接关联字段
        # 如果将来需要添加模板关联，可以在这里添加相应的检查逻辑
        
        # 删除模板
        await db.delete(template)
        await db.commit()
        
        return {"message": "模板删除成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除模板失败: {str(e)}"
        )

@router.post("/templates/", response_model=DiagnosisTemplateResponse)
async def create_diagnosis_template(
    template_data: DiagnosisTemplateCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建诊断模板"""
    try:
        template_dict = template_data.dict()
        
        # 字段映射：前端字段 -> 数据库字段
        mapped_dict = {
            'name': template_dict['name'],
            'description': template_dict.get('description'),
            'diagnosis_types': [template_dict['diagnosis_type'].value],  # 转换枚举为字符串值
            'default_config': template_dict['config_template'],  # config_template -> default_config
            'default_schedule': template_dict.get('default_schedule', {}),
            'threshold_config': template_dict.get('threshold_config', {}),
            'is_active': True,  # 新创建的模板默认启用
            'is_system': not template_dict.get('is_public', True),  # is_public -> is_system (取反)
            'created_by': str(current_user.id)  # 确保是字符串类型
        }
        
        template = DiagnosisTemplate(**mapped_dict)
        db.add(template)
        await db.commit()
        await db.refresh(template)
    except Exception as e:
        await db.rollback()
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建模板失败: {str(e)}"
        )
    
    return DiagnosisTemplateResponse(
        id=template.id,
        name=template.name,
        diagnosis_types=template.diagnosis_types or [],
        default_config=template.default_config,
        default_schedule=template.default_schedule,
        threshold_config=template.threshold_config,
        is_active=template.is_active,
        is_system=template.is_system,
        usage_count=template.usage_count,
        created_by=template.created_by,
        created_by_name=current_user.username,
        created_at=template.created_at,
        updated_at=template.updated_at,
        description=template.description
    )

# 诊断统计
@router.get("/stats/overview", response_model=DiagnosisStatsResponse)
async def get_diagnosis_stats(
    days: int = Query(7, ge=1, le=30, description="统计天数"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取诊断统计信息"""
    # 任务统计
    total_tasks_result = await db.execute(select(func.count(DiagnosisTask.id)))
    total_tasks = total_tasks_result.scalar()
    
    active_tasks_result = await db.execute(select(func.count(DiagnosisTask.id)).where(DiagnosisTask.is_active == True))
    active_tasks = active_tasks_result.scalar()
    
    running_tasks_result = await db.execute(select(func.count(DiagnosisTask.id)).where(DiagnosisTask.status == TaskStatus.RUNNING))
    running_tasks = running_tasks_result.scalar()
    
    # 注意：is_scheduled 字段已被移除，使用 schedule_type 判断是否为定时任务
    scheduled_tasks_result = await db.execute(select(func.count(DiagnosisTask.id)).where(DiagnosisTask.schedule_type.isnot(None)))
    scheduled_tasks = scheduled_tasks_result.scalar()
    
    # 结果统计
    total_results_result = await db.execute(select(func.count(DiagnosisResult.id)))
    total_results = total_results_result.scalar()
    
    success_results_result = await db.execute(select(func.count(DiagnosisResult.id)).where(DiagnosisResult.status == DiagnosisStatus.SUCCESS))
    success_results = success_results_result.scalar()
    
    failed_results_result = await db.execute(select(func.count(DiagnosisResult.id)).where(DiagnosisResult.status == DiagnosisStatus.FAILED))
    failed_results = failed_results_result.scalar()
    
    warning_results_result = await db.execute(select(func.count(DiagnosisResult.id)).where(DiagnosisResult.status == DiagnosisStatus.WARNING))
    warning_results = warning_results_result.scalar()
    
    # 告警统计
    total_alarms_result = await db.execute(select(func.count(DiagnosisAlarm.id)))
    total_alarms = total_alarms_result.scalar()
    
    unacknowledged_alarms_result = await db.execute(select(func.count(DiagnosisAlarm.id)).where(DiagnosisAlarm.is_acknowledged == False))
    unacknowledged_alarms = unacknowledged_alarms_result.scalar()
    
    critical_alarms_result = await db.execute(select(func.count(DiagnosisAlarm.id)).where(DiagnosisAlarm.severity == "critical"))
    critical_alarms = critical_alarms_result.scalar()
    
    # 平均分数
    avg_score_result = await db.execute(
        select(func.avg(DiagnosisResult.score))
        .where(DiagnosisResult.score.isnot(None))
    )
    avg_score = avg_score_result.scalar() or 0
    
    # 按类型统计 - 注意：diagnosis_types 现在是 JSON 数组，暂时跳过此统计
    # TODO: 需要使用 PostgreSQL JSON 函数来展开数组并统计
    by_type = {}
    
    # 按状态统计
    status_result = await db.execute(
        select(DiagnosisResult.status, func.count(DiagnosisResult.id))
        .group_by(DiagnosisResult.status)
    )
    by_status = {str(row[0].value): row[1] for row in status_result.all()}
    
    # 趋势数据
    trend_data = []
    today = date.today()
    for i in range(days):
        target_date = today - timedelta(days=i)
        
        daily_result = await db.execute(
            select(func.count(DiagnosisResult.id))
            .where(func.date(DiagnosisResult.created_at) == target_date)
        )
        daily_count = daily_result.scalar()
        
        success_daily = await db.execute(
            select(func.count(DiagnosisResult.id))
            .where(
                and_(
                    func.date(DiagnosisResult.created_at) == target_date,
                    DiagnosisResult.status == DiagnosisStatus.SUCCESS
                )
            )
        )
        success_count = success_daily.scalar()
        
        failed_daily = await db.execute(
            select(func.count(DiagnosisResult.id))
            .where(
                and_(
                    func.date(DiagnosisResult.created_at) == target_date,
                    DiagnosisResult.status == DiagnosisStatus.FAILED
                )
            )
        )
        failed_count = failed_daily.scalar()
        
        trend_data.append({
            "date": target_date.strftime("%Y-%m-%d"),
            "total_count": daily_count,
            "success_count": success_count,
            "failed_count": failed_count
        })
    
    trend_data.reverse()  # 按时间正序排列
    
    return DiagnosisStatsResponse(
        total_tasks=total_tasks,
        active_tasks=active_tasks,
        running_tasks=running_tasks,
        scheduled_tasks=scheduled_tasks,
        total_results=total_results,
        success_results=success_results,
        failed_results=failed_results,
        warning_results=warning_results,
        total_alarms=total_alarms,
        unacknowledged_alarms=unacknowledged_alarms,
        critical_alarms=critical_alarms,
        avg_score=avg_score,
        by_type=by_type,
        by_status=by_status,
        trend_data=trend_data
    )

# 调度器管理API
@router.get("/scheduler/status")
async def get_scheduler_status(
    current_user: User = Depends(get_current_user)
):
    """获取调度器状态"""
    return {
        "scheduler_running": task_scheduler.running,
        "running_tasks": task_scheduler.get_running_tasks(),
        "worker_status": task_scheduler.get_worker_status()
    }

@router.post("/scheduler/start")
async def start_scheduler(
    current_user: User = Depends(get_current_user)
):
    """启动调度器"""
    await task_scheduler.start()
    return {"message": "调度器已启动"}

@router.post("/scheduler/stop")
async def stop_scheduler(
    current_user: User = Depends(get_current_user)
):
    """停止调度器"""
    await task_scheduler.stop()
    return {"message": "调度器已停止"}

# Worker管理API
@router.get("/workers/status")
async def get_worker_status(
    current_user: User = Depends(get_current_user)
):
    """获取Worker状态"""
    return worker_pool.get_pool_status()

@router.post("/workers/start")
async def start_workers(
    pool_size: int = Query(3, ge=1, le=10, description="Worker池大小"),
    current_user: User = Depends(get_current_user)
):
    """启动Worker池"""
    from diagnosis.worker import start_worker_pool
    await start_worker_pool(pool_size)
    return {"message": f"Worker池已启动，包含 {pool_size} 个Worker"}

@router.post("/workers/stop")
async def stop_workers(
    current_user: User = Depends(get_current_user)
):
    """停止Worker池"""
    from diagnosis.worker import stop_worker_pool
    await stop_worker_pool()
    return {"message": "Worker池已停止"}

# 任务队列管理API
@router.post("/tasks/{task_id}/submit")
async def submit_task_to_queue(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """提交任务到Worker队列"""
    # 验证任务存在
    result = await db.execute(select(DiagnosisTask).where(DiagnosisTask.id == task_id))
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="诊断任务不存在"
        )
    
    # 提交到Worker队列
    success = await worker_pool.submit_task(task_id)
    
    if success:
        return {"message": "任务已提交到执行队列"}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="任务提交失败"
        )

# 分布式Worker节点管理API
class WorkerNodeInfo(BaseModel):
    node_id: str
    node_name: str
    worker_pool_size: int
    max_concurrent_tasks: int
    capabilities: List[str] = []
    status: str = "online"
    registered_at: datetime

class WorkerHeartbeat(BaseModel):
    node_id: str
    timestamp: datetime
    status: str
    worker_status: Dict[str, Any] = {}
    system_info: Dict[str, Any] = {}

class TaskFetchRequest(BaseModel):
    node_id: str
    batch_size: int = 1

class TaskFetchResponse(BaseModel):
    tasks: List[Dict[str, Any]]
    total_available: int

# 存储分布式worker节点信息（生产环境应使用Redis或数据库）
distributed_workers: Dict[str, Dict[str, Any]] = {}

@router.post("/workers/register")
async def register_worker_node(
    node_info: WorkerNodeInfo,
    db: AsyncSession = Depends(get_db)
):
    """注册分布式Worker节点"""
    worker_info = {
        "node_id": node_info.node_id,
        "node_name": node_info.node_name,
        "worker_pool_size": node_info.worker_pool_size,
        "max_concurrent_tasks": node_info.max_concurrent_tasks,
        "capabilities": node_info.capabilities,
        "status": node_info.status,
        "registered_at": node_info.registered_at
    }
    
    return await _register_worker_internal(worker_info, db)

@router.delete("/workers/{node_id}")
async def unregister_worker_node(
    node_id: str
):
    """注销分布式Worker节点"""
    if node_id in distributed_workers:
        del distributed_workers[node_id]
        return {"message": f"Worker节点 {node_id} 注销成功"}
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Worker节点不存在"
        )

@router.post("/workers/{node_id}/heartbeat")
async def worker_heartbeat(
    node_id: str,
    heartbeat: WorkerHeartbeat,
    db: AsyncSession = Depends(get_db)
):
    """接收Worker节点心跳"""
    heartbeat_data = {
        "timestamp": heartbeat.timestamp.isoformat(),
        "status": heartbeat.status,
        "worker_status": heartbeat.worker_status,
        "system_info": heartbeat.system_info
    }
    
    return await _worker_heartbeat_internal(node_id, heartbeat_data, db)

@router.get("/workers/distributed")
async def get_distributed_workers():
    """获取所有分布式Worker节点状态"""
    current_time = datetime.now(timezone.utc)
    
    # 检查节点是否在线（超过3分钟未发送心跳认为离线）
    for node_id, node_data in distributed_workers.items():
        last_heartbeat = node_data.get("last_heartbeat")
        if last_heartbeat:
            # 确保时区一致性
            if last_heartbeat.tzinfo is None:
                last_heartbeat = last_heartbeat.replace(tzinfo=timezone.utc)
            if (current_time - last_heartbeat).total_seconds() > 180:
                node_data["status"] = "offline"
    
    # 格式化节点数据，确保时间字段包含正确的时区信息
    formatted_nodes = []
    for node_data in distributed_workers.values():
        formatted_node = node_data.copy()
        
        # 格式化注册时间
        if "registered_at" in formatted_node and formatted_node["registered_at"]:
            if isinstance(formatted_node["registered_at"], str):
                # 如果是字符串，尝试解析并重新格式化
                try:
                    dt = datetime.fromisoformat(formatted_node["registered_at"].replace('Z', '+00:00'))
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=timezone.utc)
                    formatted_node["registered_at"] = dt.isoformat()
                except:
                    pass
            elif isinstance(formatted_node["registered_at"], datetime):
                dt = formatted_node["registered_at"]
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                formatted_node["registered_at"] = dt.isoformat()
        
        # 格式化心跳时间
        if "last_heartbeat" in formatted_node and formatted_node["last_heartbeat"]:
            if isinstance(formatted_node["last_heartbeat"], datetime):
                dt = formatted_node["last_heartbeat"]
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                formatted_node["last_heartbeat"] = dt.isoformat()
        
        formatted_nodes.append(formatted_node)
    
    return {
        "total_nodes": len(distributed_workers),
        "online_nodes": len([n for n in distributed_workers.values() if n["status"] == "online"]),
        "nodes": formatted_nodes
    }

# 创建一个独立的无认证路由
no_auth_router = APIRouter()

@no_auth_router.get("/tasks/fetch")
async def fetch_tasks_for_worker_no_auth(
    node_id: str = Query(..., description="Worker节点ID"),
    batch_size: int = Query(1, ge=1, le=10, description="批量获取任务数量"),
    db: AsyncSession = Depends(get_db)
):
    """为分布式Worker节点获取待执行的任务 - 无认证版本"""
    return await _fetch_tasks_internal(node_id, batch_size, db)

@no_auth_router.post("/register")
async def register_worker_no_auth(
    worker_info: dict,
    db: AsyncSession = Depends(get_db)
):
    """注册Worker节点 - 无认证版本"""
    return await _register_worker_internal(worker_info, db)

@no_auth_router.post("/{node_id}/heartbeat")
async def worker_heartbeat_no_auth(
    node_id: str,
    heartbeat_data: dict,
    db: AsyncSession = Depends(get_db)
):
    """Worker节点心跳 - 无认证版本"""
    return await _worker_heartbeat_internal(node_id, heartbeat_data, db)

@no_auth_router.post("/tasks/{task_id}/complete")
async def complete_task_no_auth(
    task_id: int,
    completion_data: dict,
    db: AsyncSession = Depends(get_db)
):
    """Worker完成任务 - 无认证版本"""
    return await _complete_task_internal(task_id, completion_data, db)

@no_auth_router.delete("/{node_id}")
async def unregister_worker_no_auth(
    node_id: str
):
    """注销Worker节点 - 无认证版本"""
    if node_id in distributed_workers:
        del distributed_workers[node_id]
        return {"message": f"Worker节点 {node_id} 注销成功"}
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Worker节点不存在"
        )

@router.get("/tasks/fetch", dependencies=[])
async def fetch_tasks_for_worker(
    node_id: str = Query(..., description="Worker节点ID"),
    batch_size: int = Query(1, ge=1, le=10, description="批量获取任务数量"),
    db: AsyncSession = Depends(get_db)
):
    """为分布式Worker节点获取待执行的任务"""
    return await _fetch_tasks_internal(node_id, batch_size, db)

async def _register_worker_internal(worker_info: dict, db: AsyncSession):
    """注册Worker节点内部逻辑"""
    node_id = worker_info.get("node_id")
    
    # 检查是否已存在该节点，如果存在则保留统计信息
    existing_data = distributed_workers.get(node_id, {})
    
    node_data = {
        "node_id": node_id,
        "node_name": worker_info.get("node_name"),
        "worker_pool_size": worker_info.get("worker_pool_size"),
        "max_concurrent_tasks": worker_info.get("max_concurrent_tasks"),
        "capabilities": worker_info.get("capabilities"),
        "status": worker_info.get("status"),
        "registered_at": worker_info.get("registered_at"),
        "last_heartbeat": datetime.now(timezone.utc),
        # 保留已有的统计信息，如果是新节点则使用默认值
        "total_tasks_executed": existing_data.get("total_tasks_executed", 0),
        "current_tasks": 0,  # 重新注册时重置当前任务数
        "current_task_ids": []  # 重新注册时清空当前任务列表
    }
    
    distributed_workers[node_id] = node_data
    
    action = "重新注册" if existing_data else "注册"
    logger.info(f"Worker节点 {node_id} {action}成功")
    
    return {
        "message": f"Worker节点 {node_id} {action}成功",
        "node_id": node_id
    }

async def _worker_heartbeat_internal(node_id: str, heartbeat_data: dict, db: AsyncSession):
    """Worker节点心跳内部逻辑"""
    if node_id not in distributed_workers:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Worker节点未注册"
        )
    
    # 更新心跳信息
    distributed_workers[node_id].update({
        "last_heartbeat": datetime.fromisoformat(heartbeat_data.get("timestamp").replace('Z', '+00:00')) if heartbeat_data.get("timestamp") else datetime.now(timezone.utc),
        "status": heartbeat_data.get("status"),
        "worker_status": heartbeat_data.get("worker_status"),
        "system_info": heartbeat_data.get("system_info")
    })
    
    return {"message": "心跳接收成功"}

async def _fetch_tasks_internal(node_id: str, batch_size: int, db: AsyncSession):
    """为分布式Worker节点获取待执行的任务"""
    if node_id not in distributed_workers:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Worker节点未注册"
        )
    
    # 优先查询分配给该worker的任务
    assigned_result = await db.execute(
        select(DiagnosisTask)
        .where(
            and_(
                DiagnosisTask.is_active == True,
                DiagnosisTask.status == TaskStatus.PENDING,
                DiagnosisTask.assigned_worker == node_id
            )
        )
        .limit(batch_size)
    )
    
    assigned_tasks = assigned_result.scalars().all()
    remaining_batch_size = batch_size - len(assigned_tasks)
    
    # 如果还有剩余容量，获取未分配的任务
    unassigned_tasks = []
    if remaining_batch_size > 0:
        unassigned_result = await db.execute(
            select(DiagnosisTask)
            .where(
                and_(
                    DiagnosisTask.is_active == True,
                    DiagnosisTask.status == TaskStatus.PENDING,
                    DiagnosisTask.assigned_worker.is_(None)
                )
            )
            .limit(remaining_batch_size)
        )
        unassigned_tasks = unassigned_result.scalars().all()
    
    # 合并任务列表
    all_tasks = list(assigned_tasks) + list(unassigned_tasks)
    
    # 将任务标记为运行中并分配给该worker
    task_list = []
    for task in all_tasks:
        task.status = TaskStatus.RUNNING
        task.assigned_worker = node_id
        task_list.append({
            "id": task.id,  # Worker期望的字段名
            "task_id": task.id,  # 保持兼容性
            "name": task.name,
            "diagnosis_types": task.diagnosis_types,
            "camera_ids": task.camera_ids,
            "camera_groups": task.camera_groups,
            "diagnosis_config": task.diagnosis_config,
            "assigned_node": node_id
        })
    
    await db.commit()
    
    # 更新节点当前任务数和任务ID列表
    if node_id in distributed_workers:
        distributed_workers[node_id]["current_tasks"] = distributed_workers[node_id].get("current_tasks", 0) + len(task_list)
        # 记录分配给该节点的任务ID
        current_task_ids = distributed_workers[node_id].get("current_task_ids", [])
        task_ids = [task["task_id"] for task in task_list]
        distributed_workers[node_id]["current_task_ids"] = current_task_ids + task_ids
    
    return TaskFetchResponse(
        tasks=task_list,
        total_available=len(task_list)
    )

async def _complete_task_internal(task_id: int, completion_data: dict, db: AsyncSession):
    """Worker完成任务内部逻辑"""
    try:
        # 获取任务信息
        result = await db.execute(
            select(DiagnosisTask).where(DiagnosisTask.id == task_id)
        )
        task = result.scalar_one_or_none()
        
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="任务不存在"
            )
        
        # 更新任务状态
        success = completion_data.get("success", False)
        task.status = TaskStatus.COMPLETED if success else TaskStatus.FAILED
        task.last_run_time = datetime.now(timezone.utc)
        task.total_runs = task.total_runs + 1
        
        if success:
            task.success_runs = task.success_runs + 1
            
            # 如果是cron类型的任务，更新下次运行时间
            if task.schedule_type == 'cron' and task.cron_expression:
                from diagnosis.scheduler import task_scheduler
                await task_scheduler._update_next_run_time(task, db)
        
        # 保留worker分配信息以便历史查询
        worker_node_id = task.assigned_worker
        # task.assigned_worker = None  # 注释掉这行，保留历史分配信息
        
        await db.commit()
        
        # 更新worker节点状态
        if worker_node_id and worker_node_id in distributed_workers:
            worker_data = distributed_workers[worker_node_id]
            
            # 减少当前任务数
            current_tasks = worker_data.get("current_tasks", 0)
            worker_data["current_tasks"] = max(0, current_tasks - 1)
            
            # 从当前任务ID列表中移除
            current_task_ids = worker_data.get("current_task_ids", [])
            if task_id in current_task_ids:
                current_task_ids.remove(task_id)
                worker_data["current_task_ids"] = current_task_ids
            
            # 更新统计信息
            worker_data["total_tasks_executed"] = worker_data.get("total_tasks_executed", 0) + 1
            
            logger.info(f"Worker节点 {worker_node_id} 完成任务 {task_id}，状态: {'成功' if success else '失败'}")
        
        return {
            "message": f"任务 {task_id} 完成，状态: {'成功' if success else '失败'}",
            "task_id": task_id,
            "success": success
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"完成任务 {task_id} 时发生错误: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"完成任务时发生错误: {str(e)}"
        )

@router.post("/tasks/{task_id}/complete")
async def complete_distributed_task(
    task_id: int,
    result_data: Dict[str, Any],
    node_id: str = Query(..., description="Worker节点ID"),
    db: AsyncSession = Depends(get_db)
):
    """分布式Worker节点完成任务后的回调"""
    if node_id not in distributed_workers:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Worker节点未注册"
        )
    
    # 查询任务
    result = await db.execute(select(DiagnosisTask).where(DiagnosisTask.id == task_id))
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )
    
    # 更新任务状态
    task.status = TaskStatus.COMPLETED if result_data.get("success", False) else TaskStatus.FAILED
    task.last_run = datetime.utcnow()
    task.run_count += 1
    
    if result_data.get("success", False):
        task.success_count += 1
    else:
        task.error_count += 1
    
    # 创建诊断结果
    diagnosis_result = DiagnosisResult(
        task_id=task_id,
        status=DiagnosisStatus.SUCCESS if result_data.get("success", False) else DiagnosisStatus.FAILED,
        result_data=result_data.get("result_data", {}),
        score=result_data.get("score"),
        issues_found=result_data.get("issues_found", []),
        recommendations=result_data.get("recommendations", []),
        execution_time=result_data.get("execution_time"),
        error_message=result_data.get("error_message")
    )
    
    db.add(diagnosis_result)
    await db.commit()
    
    # 更新节点统计
    if node_id in distributed_workers:
        distributed_workers[node_id]["total_tasks_executed"] = distributed_workers[node_id].get("total_tasks_executed", 0) + 1
        distributed_workers[node_id]["current_tasks"] = max(0, distributed_workers[node_id].get("current_tasks", 0) - 1)
        # 从任务ID列表中移除已完成的任务
        current_task_ids = distributed_workers[node_id].get("current_task_ids", [])
        if task_id in current_task_ids:
            current_task_ids.remove(task_id)
            distributed_workers[node_id]["current_task_ids"] = current_task_ids
    
    return {"message": "任务完成状态已更新"}

# 任务恢复机制相关API
class TaskRecoveryResponse(BaseModel):
    """任务恢复响应模型"""
    checked_tasks: int
    reset_tasks: int
    reset_task_ids: List[int]
    message: str

class TaskStatusCheckResponse(BaseModel):
    """任务状态检查响应模型"""
    running_tasks: List[Dict[str, Any]]
    stuck_tasks: List[Dict[str, Any]]
    total_running: int
    total_stuck: int
    message: str

@router.post("/tasks/recovery", response_model=TaskRecoveryResponse)
async def recover_stuck_tasks(
    force_reset: bool = Query(False, description="是否强制重置所有运行中的任务"),
    max_runtime_minutes: int = Query(30, description="任务最大运行时间（分钟），超过此时间认为卡住"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    恢复卡住的诊断任务
    
    检查数据库中处于运行状态但实际未在执行的任务，并将其重置为待执行状态。
    """
    try:
        logger.info(f"开始任务恢复检查，用户: {current_user.username}")
        
        # 使用原生SQL查询运行中的任务
        result = await db.execute(
            text("SELECT * FROM diagnosis_tasks WHERE status = 'running'")
        )
        running_tasks = result.fetchall()
        
        reset_count = 0
        reset_task_ids = []
        
        for task_row in running_tasks:
            task_id = task_row[0]  # id字段
            task_name = task_row[1]  # name字段
            last_run_time = task_row[16]  # last_run_time字段
            
            should_reset = False
            reset_reason = ""
            
            # 检查任务是否真的在运行
            is_actually_running = task_id in diagnosis_executor.running_tasks
            
            if force_reset:
                should_reset = True
                reset_reason = "强制重置"
            elif not is_actually_running:
                should_reset = True
                reset_reason = "任务不在执行器运行列表中"
            elif last_run_time:
                # 检查运行时间是否过长
                if isinstance(last_run_time, str):
                    last_run_time = datetime.fromisoformat(last_run_time.replace('Z', '+00:00'))
                
                time_diff = datetime.now(last_run_time.tzinfo) - last_run_time
                
                if time_diff > timedelta(minutes=max_runtime_minutes):
                    should_reset = True
                    reset_reason = f"任务运行时间过长 ({time_diff})"
            else:
                should_reset = True
                reset_reason = "任务无最后运行时间记录"
            
            if should_reset:
                logger.info(f"重置任务 {task_id} ({task_name}): {reset_reason}")
                
                # 使用原生SQL重置任务状态
                await db.execute(
                    text("UPDATE diagnosis_tasks SET status = 'pending' WHERE id = :task_id"),
                    {"task_id": task_id}
                )
                
                # 从执行器运行列表中移除
                diagnosis_executor.running_tasks.discard(task_id)
                
                reset_count += 1
                reset_task_ids.append(task_id)
        
        if reset_count > 0:
            await db.commit()
            message = f"成功重置 {reset_count} 个卡住的任务"
            logger.info(message)
        else:
            message = "没有发现需要重置的任务"
            logger.info(message)
        
        return TaskRecoveryResponse(
            checked_tasks=len(running_tasks),
            reset_tasks=reset_count,
            reset_task_ids=reset_task_ids,
            message=message
        )
        
    except Exception as e:
        logger.error(f"任务恢复失败: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"任务恢复失败: {str(e)}"
        )

@router.get("/tasks/status-check", response_model=TaskStatusCheckResponse)
async def check_task_status(
    max_runtime_minutes: int = Query(30, description="任务最大运行时间（分钟），超过此时间认为卡住"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    检查任务状态
    
    返回当前运行中的任务和可能卡住的任务信息，不进行任何修改操作。
    """
    try:
        # 使用原生SQL查询运行中的任务
        result = await db.execute(
            text("SELECT * FROM diagnosis_tasks WHERE status = 'running'")
        )
        running_tasks = result.fetchall()
        
        running_task_list = []
        stuck_task_list = []
        
        for task_row in running_tasks:
            task_id = task_row[0]  # id字段
            task_name = task_row[1]  # name字段
            last_run_time = task_row[16]  # last_run_time字段
            is_active = task_row[15]  # is_active字段
            
            # 检查任务是否真的在运行
            is_actually_running = task_id in diagnosis_executor.running_tasks
            
            task_info = {
                "id": task_id,
                "name": task_name,
                "last_run_time": last_run_time.isoformat() if last_run_time else None,
                "is_active": is_active,
                "is_actually_running": is_actually_running
            }
            
            # 判断是否卡住
            is_stuck = False
            stuck_reason = ""
            
            if not is_actually_running:
                is_stuck = True
                stuck_reason = "任务不在执行器运行列表中"
            elif last_run_time:
                if isinstance(last_run_time, str):
                    last_run_time = datetime.fromisoformat(last_run_time.replace('Z', '+00:00'))
                
                time_diff = datetime.now(last_run_time.tzinfo) - last_run_time
                task_info["runtime_minutes"] = time_diff.total_seconds() / 60
                
                if time_diff > timedelta(minutes=max_runtime_minutes):
                    is_stuck = True
                    stuck_reason = f"任务运行时间过长 ({time_diff})"
            else:
                is_stuck = True
                stuck_reason = "任务无最后运行时间记录"
            
            if is_stuck:
                task_info["stuck_reason"] = stuck_reason
                stuck_task_list.append(task_info)
            
            running_task_list.append(task_info)
        
        message = f"检查完成：运行中任务 {len(running_task_list)} 个，卡住任务 {len(stuck_task_list)} 个"
        
        return TaskStatusCheckResponse(
            running_tasks=running_task_list,
            stuck_tasks=stuck_task_list,
            total_running=len(running_task_list),
            total_stuck=len(stuck_task_list),
            message=message
        )
        
    except Exception as e:
        logger.error(f"任务状态检查失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"任务状态检查失败: {str(e)}"
        )

# Worker统计API
class WorkerStatsResponse(BaseModel):
    """Worker统计响应"""
    total_workers: int
    online_workers: int
    busy_workers: int
    total_tasks_today: int
    completed_tasks_today: int
    failed_tasks_today: int
    avg_task_duration: float

@router.get("/workers/stats", response_model=WorkerStatsResponse)
async def get_worker_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取Worker统计信息"""
    try:
        # 分布式Worker统计
        total_workers = len(distributed_workers)
        online_workers = len([w for w in distributed_workers.values() if w["status"] == "online"])
        busy_workers = len([w for w in distributed_workers.values() if w["status"] == "busy"])
        
        # 今日任务统计
        today = datetime.now().date()
        today_start = datetime.combine(today, datetime.min.time())
        
        # 今日总任务数
        total_tasks_result = await db.execute(
            select(func.count(DiagnosisTask.id))
            .where(DiagnosisTask.created_at >= today_start)
        )
        total_tasks_today = total_tasks_result.scalar() or 0
        
        # 今日完成任务数
        completed_tasks_result = await db.execute(
            select(func.count(DiagnosisTask.id))
            .where(
                and_(
                    DiagnosisTask.updated_at >= today_start,
                    DiagnosisTask.status == TaskStatus.COMPLETED
                )
            )
        )
        completed_tasks_today = completed_tasks_result.scalar() or 0
        
        # 今日失败任务数
        failed_tasks_result = await db.execute(
            select(func.count(DiagnosisTask.id))
            .where(
                and_(
                    DiagnosisTask.updated_at >= today_start,
                    DiagnosisTask.status == TaskStatus.FAILED
                )
            )
        )
        failed_tasks_today = failed_tasks_result.scalar() or 0
        
        # 平均任务执行时间（简化计算，实际应该基于任务执行记录）
        avg_task_duration = 0.0
        if completed_tasks_today > 0:
            # 这里简化处理，实际应该有专门的任务执行时间记录
            avg_task_duration = 120.0  # 假设平均2分钟
        
        return WorkerStatsResponse(
            total_workers=total_workers,
            online_workers=online_workers,
            busy_workers=busy_workers,
            total_tasks_today=total_tasks_today,
            completed_tasks_today=completed_tasks_today,
            failed_tasks_today=failed_tasks_today,
            avg_task_duration=avg_task_duration
        )
        
    except Exception as e:
        logger.error(f"获取Worker统计失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取Worker统计失败: {str(e)}"
        )

# Worker任务API
@router.get("/workers/{node_id}/tasks")
async def get_worker_tasks(
    node_id: str,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    task_status: Optional[str] = Query(None, description="任务状态过滤"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取Worker节点的任务列表"""
    try:
        # 检查Worker节点是否存在
        if node_id not in distributed_workers:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Worker节点不存在"
            )
        
        # 构建查询条件 - 查询所有分配给该Worker节点的任务（包括历史任务）
        query = select(DiagnosisTask).where(DiagnosisTask.assigned_worker == node_id)
        
        if task_status:
            try:
                status_enum = TaskStatus(task_status)
                query = query.where(DiagnosisTask.status == status_enum)
            except ValueError:
                pass
        
        # 分页
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size).order_by(DiagnosisTask.created_at.desc())
        
        result = await db.execute(query)
        tasks = result.scalars().all()
        
        # 转换为响应格式
        task_list = []
        for task in tasks:
            task_data = {
                "task_id": task.id,
                "task_name": task.name,
                "diagnosis_type": task.diagnosis_types[0] if task.diagnosis_types else None,
                "status": task.status.value,
                "assigned_at": task.created_at.isoformat(),
                "node_id": node_id,
                "total_runs": task.total_runs or 0,  # 总执行次数
                "success_runs": task.success_runs or 0,  # 成功执行次数
                "failed_runs": (task.total_runs or 0) - (task.success_runs or 0)  # 失败执行次数
            }
            
            # 添加可选字段
            if task.status == TaskStatus.RUNNING:
                task_data["started_at"] = task.updated_at.isoformat()
                task_data["progress"] = 50  # 简化处理
            elif task.status == TaskStatus.COMPLETED:
                task_data["started_at"] = task.created_at.isoformat()  # 使用创建时间作为开始时间
                task_data["completed_at"] = task.updated_at.isoformat()
                task_data["progress"] = 100
            elif task.status == TaskStatus.FAILED:
                task_data["started_at"] = task.created_at.isoformat()  # 使用创建时间作为开始时间
                task_data["error_message"] = "任务执行失败"  # 简化处理
                task_data["progress"] = 0
            
            task_list.append(task_data)
        
        return task_list
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取Worker任务失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取Worker任务失败: {str(e)}"
        )