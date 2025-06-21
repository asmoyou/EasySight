from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, date, timedelta

from database import get_db
from models.diagnosis import (
    DiagnosisTask, DiagnosisResult, DiagnosisAlarm, DiagnosisTemplate, DiagnosisStatistics,
    DiagnosisType, DiagnosisStatus, TaskStatus
)
from models.user import User
from routers.auth import get_current_user

router = APIRouter()

# Pydantic models
class DiagnosisTaskCreate(BaseModel):
    name: str
    diagnosis_type: DiagnosisType
    target_id: int
    target_type: str
    template_id: Optional[int] = None
    config: Dict[str, Any] = {}
    schedule_config: Dict[str, Any] = {}
    is_scheduled: bool = False
    description: Optional[str] = None

class DiagnosisTaskUpdate(BaseModel):
    name: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    schedule_config: Optional[Dict[str, Any]] = None
    is_scheduled: Optional[bool] = None
    is_active: Optional[bool] = None
    description: Optional[str] = None

class DiagnosisTaskResponse(BaseModel):
    id: int
    name: str
    diagnosis_type: DiagnosisType
    target_id: int
    target_type: str
    template_id: Optional[int]
    template_name: Optional[str]
    config: Dict[str, Any]
    schedule_config: Dict[str, Any]
    status: TaskStatus
    is_scheduled: bool
    is_active: bool
    last_run: Optional[datetime]
    next_run: Optional[datetime]
    run_count: int
    success_count: int
    error_count: int
    created_by: int
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
    status: DiagnosisStatus
    result_data: Dict[str, Any]
    score: Optional[float]
    issues_found: List[Dict[str, Any]]
    recommendations: List[str]
    execution_time: Optional[float]
    error_message: Optional[str]
    created_at: datetime

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
    diagnosis_type: DiagnosisType
    config_template: Dict[str, Any]
    default_schedule: Dict[str, Any]
    threshold_config: Dict[str, Any]
    is_active: bool
    is_public: bool
    usage_count: int
    created_by: int
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
        conditions.append(DiagnosisTask.diagnosis_type == diagnosis_type)
    
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
    
    # 获取模板和创建者信息
    template_map = {}
    creator_map = {}
    
    if tasks:
        template_ids = [t.template_id for t in tasks if t.template_id]
        if template_ids:
            template_result = await db.execute(select(DiagnosisTemplate).where(DiagnosisTemplate.id.in_(template_ids)))
            templates = template_result.scalars().all()
            template_map = {t.id: t.name for t in templates}
        
        creator_ids = [t.created_by for t in tasks]
        creator_result = await db.execute(select(User).where(User.id.in_(creator_ids)))
        creators = creator_result.scalars().all()
        creator_map = {c.id: c.username for c in creators}
    
    return [DiagnosisTaskResponse(
        id=task.id,
        name=task.name,
        diagnosis_type=task.diagnosis_type,
        target_id=task.target_id,
        target_type=task.target_type,
        template_id=task.template_id,
        template_name=template_map.get(task.template_id),
        config=task.config,
        schedule_config=task.schedule_config,
        status=task.status,
        is_scheduled=task.is_scheduled,
        is_active=task.is_active,
        last_run=task.last_run,
        next_run=task.next_run,
        run_count=task.run_count,
        success_count=task.success_count,
        error_count=task.error_count,
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
    task_dict['created_by'] = current_user.id
    
    task = DiagnosisTask(**task_dict)
    db.add(task)
    await db.commit()
    await db.refresh(task)
    
    return DiagnosisTaskResponse(
        id=task.id,
        name=task.name,
        diagnosis_type=task.diagnosis_type,
        target_id=task.target_id,
        target_type=task.target_type,
        template_id=task.template_id,
        template_name=template_name,
        config=task.config,
        schedule_config=task.schedule_config,
        status=task.status,
        is_scheduled=task.is_scheduled,
        is_active=task.is_active,
        last_run=task.last_run,
        next_run=task.next_run,
        run_count=task.run_count,
        success_count=task.success_count,
        error_count=task.error_count,
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
    if task.template_id:
        template_result = await db.execute(select(DiagnosisTemplate).where(DiagnosisTemplate.id == task.template_id))
        template = template_result.scalar_one_or_none()
        if template:
            template_name = template.name
    
    creator_result = await db.execute(select(User).where(User.id == task.created_by))
    creator = creator_result.scalar_one_or_none()
    creator_name = creator.username if creator else ""
    
    return DiagnosisTaskResponse(
        id=task.id,
        name=task.name,
        diagnosis_type=task.diagnosis_type,
        target_id=task.target_id,
        target_type=task.target_type,
        template_id=task.template_id,
        template_name=template_name,
        config=task.config,
        schedule_config=task.schedule_config,
        status=task.status,
        is_scheduled=task.is_scheduled,
        is_active=task.is_active,
        last_run=task.last_run,
        next_run=task.next_run,
        run_count=task.run_count,
        success_count=task.success_count,
        error_count=task.error_count,
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
    for field, value in update_data.items():
        setattr(task, field, value)
    
    await db.commit()
    await db.refresh(task)
    
    # 获取相关信息
    template_name = None
    if task.template_id:
        template_result = await db.execute(select(DiagnosisTemplate).where(DiagnosisTemplate.id == task.template_id))
        template = template_result.scalar_one_or_none()
        if template:
            template_name = template.name
    
    creator_result = await db.execute(select(User).where(User.id == task.created_by))
    creator = creator_result.scalar_one_or_none()
    creator_name = creator.username if creator else ""
    
    return DiagnosisTaskResponse(
        id=task.id,
        name=task.name,
        diagnosis_type=task.diagnosis_type,
        target_id=task.target_id,
        target_type=task.target_type,
        template_id=task.template_id,
        template_name=template_name,
        config=task.config,
        schedule_config=task.schedule_config,
        status=task.status,
        is_scheduled=task.is_scheduled,
        is_active=task.is_active,
        last_run=task.last_run,
        next_run=task.next_run,
        run_count=task.run_count,
        success_count=task.success_count,
        error_count=task.error_count,
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
    task.last_run = datetime.utcnow()
    task.run_count += 1
    
    await db.commit()
    
    # 这里应该触发实际的诊断执行逻辑
    # 为了演示，我们只是返回成功消息
    
    return {"message": "诊断任务已开始执行"}

# 诊断结果管理
@router.get("/results/", response_model=List[DiagnosisResultResponse])
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
        conditions.append(DiagnosisResult.status == status)
    
    if start_date:
        conditions.append(DiagnosisResult.created_at >= start_date)
    
    if end_date:
        end_datetime = datetime.combine(end_date, datetime.max.time())
        conditions.append(DiagnosisResult.created_at <= end_datetime)
    
    query = select(DiagnosisResult).order_by(desc(DiagnosisResult.created_at))
    if conditions:
        query = query.where(and_(*conditions))
    
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    
    result = await db.execute(query)
    results = result.scalars().all()
    
    # 获取任务信息
    task_map = {}
    if results:
        task_ids = [r.task_id for r in results]
        task_result = await db.execute(select(DiagnosisTask).where(DiagnosisTask.id.in_(task_ids)))
        tasks = task_result.scalars().all()
        task_map = {t.id: t.name for t in tasks}
    
    return [DiagnosisResultResponse(
        id=result.id,
        task_id=result.task_id,
        task_name=task_map.get(result.task_id, ""),
        status=result.status,
        result_data=result.result_data,
        score=result.score,
        issues_found=result.issues_found,
        recommendations=result.recommendations,
        execution_time=result.execution_time,
        error_message=result.error_message,
        created_at=result.created_at
    ) for result in results]

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
    
    return DiagnosisResultResponse(
        id=result.id,
        task_id=result.task_id,
        task_name=task.name,
        status=result.status,
        result_data=result.result_data,
        score=result.score,
        issues_found=result.issues_found,
        recommendations=result.recommendations,
        execution_time=result.execution_time,
        error_message=result.error_message,
        created_at=result.created_at
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
    
    # 获取任务和确认人信息
    task_map = {}
    acknowledger_map = {}
    
    if alarms:
        # 通过结果获取任务信息
        result_ids = [a.result_id for a in alarms]
        result_task_result = await db.execute(
            select(DiagnosisResult.id, DiagnosisResult.task_id)
            .where(DiagnosisResult.id.in_(result_ids))
        )
        result_task_map = {row[0]: row[1] for row in result_task_result.all()}
        
        task_ids = list(result_task_map.values())
        if task_ids:
            task_result = await db.execute(select(DiagnosisTask).where(DiagnosisTask.id.in_(task_ids)))
            tasks = task_result.scalars().all()
            task_name_map = {t.id: t.name for t in tasks}
            task_map = {result_id: task_name_map.get(task_id, "") for result_id, task_id in result_task_map.items()}
        
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
        created_at=alarm.created_at
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
    
    if diagnosis_type:
        conditions.append(DiagnosisTemplate.diagnosis_type == diagnosis_type)
    
    if is_public is not None:
        conditions.append(DiagnosisTemplate.is_public == is_public)
    
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
        creator_ids = [t.created_by for t in templates]
        creator_result = await db.execute(select(User).where(User.id.in_(creator_ids)))
        creators = creator_result.scalars().all()
        creator_map = {c.id: c.username for c in creators}
    
    return [DiagnosisTemplateResponse(
        id=template.id,
        name=template.name,
        diagnosis_type=template.diagnosis_type,
        config_template=template.config_template,
        default_schedule=template.default_schedule,
        threshold_config=template.threshold_config,
        is_active=template.is_active,
        is_public=template.is_public,
        usage_count=template.usage_count,
        created_by=template.created_by,
        created_by_name=creator_map.get(template.created_by, ""),
        created_at=template.created_at,
        updated_at=template.updated_at,
        description=template.description
    ) for template in templates]

@router.post("/templates/", response_model=DiagnosisTemplateResponse)
async def create_diagnosis_template(
    template_data: DiagnosisTemplateCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建诊断模板"""
    template_dict = template_data.dict()
    template_dict['created_by'] = current_user.id
    
    template = DiagnosisTemplate(**template_dict)
    db.add(template)
    await db.commit()
    await db.refresh(template)
    
    return DiagnosisTemplateResponse(
        id=template.id,
        name=template.name,
        diagnosis_type=template.diagnosis_type,
        config_template=template.config_template,
        default_schedule=template.default_schedule,
        threshold_config=template.threshold_config,
        is_active=template.is_active,
        is_public=template.is_public,
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
    
    scheduled_tasks_result = await db.execute(select(func.count(DiagnosisTask.id)).where(DiagnosisTask.is_scheduled == True))
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
    
    # 按类型统计
    type_result = await db.execute(
        select(DiagnosisTask.diagnosis_type, func.count(DiagnosisTask.id))
        .group_by(DiagnosisTask.diagnosis_type)
    )
    by_type = {str(row[0].value): row[1] for row in type_result.all()}
    
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