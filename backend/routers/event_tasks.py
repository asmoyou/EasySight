from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, date, timedelta

from database import get_db
from models.event_task import EventTask, EventTaskStatus, EventTaskType, EventTaskLog, EventTaskRecovery
from models.user import User
from routers.auth import get_current_user
from rabbitmq_event_task_manager import rabbitmq_event_task_manager as event_task_manager

router = APIRouter()

# Pydantic models
class EventTaskCreate(BaseModel):
    name: str
    description: Optional[str] = None
    ai_service_id: int
    task_type: EventTaskType = EventTaskType.CONTINUOUS
    detection_config: Dict[str, Any] = {}
    roi_areas: List[Dict[str, Any]] = []
    alarm_threshold: float = 0.5
    schedule_config: Dict[str, Any] = {}
    check_interval: int = 5
    auto_recovery: bool = True
    max_retry_count: int = 3
    recovery_interval: int = 60
    metadata: Dict[str, Any] = {}
    tags: List[str] = []

class EventTaskUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    task_type: Optional[EventTaskType] = None
    detection_config: Optional[Dict[str, Any]] = None
    roi_areas: Optional[List[Dict[str, Any]]] = None
    alarm_threshold: Optional[float] = None
    schedule_config: Optional[Dict[str, Any]] = None
    check_interval: Optional[int] = None
    auto_recovery: Optional[bool] = None
    max_retry_count: Optional[int] = None
    recovery_interval: Optional[int] = None
    is_active: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None

class EventTaskResponse(BaseModel):
    id: int
    task_id: str
    name: str
    description: Optional[str]
    task_type: EventTaskType
    status: EventTaskStatus
    is_active: bool
    ai_service_id: int
    camera_id: int
    camera_name: Optional[str]
    algorithm_id: Optional[int]
    algorithm_name: Optional[str]
    model_id: Optional[int]
    model_name: Optional[str]
    detection_config: Dict[str, Any]
    roi_areas: List[Dict[str, Any]]
    alarm_threshold: float
    schedule_config: Dict[str, Any]
    check_interval: int
    assigned_worker: Optional[str]
    worker_heartbeat: Optional[datetime]
    total_detections: int
    success_detections: int
    failed_detections: int
    total_events: int
    avg_processing_time: Optional[float]
    last_detection_time: Optional[datetime]
    last_event_time: Optional[datetime]
    last_error: Optional[str]
    error_count: int
    auto_recovery: bool
    max_retry_count: int
    retry_count: int
    recovery_interval: int
    started_at: Optional[datetime]
    stopped_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str]
    metadata: Dict[str, Any]
    tags: List[str]

class EventTaskListResponse(BaseModel):
    tasks: List[EventTaskResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

class EventTaskLogResponse(BaseModel):
    id: int
    task_id: int
    log_type: str
    log_level: str
    message: str
    details: Dict[str, Any]
    worker_id: Optional[str]
    processing_time: Optional[float]
    detection_result: Dict[str, Any]
    event_count: int
    created_at: datetime

class EventTaskStatsResponse(BaseModel):
    total_tasks: int
    running_tasks: int
    stopped_tasks: int
    failed_tasks: int
    pending_tasks: int
    total_detections: int
    total_events: int
    avg_processing_time: Optional[float]
    success_rate: float
    by_status: Dict[str, int]
    by_type: Dict[str, int]

@router.get("/", response_model=EventTaskListResponse)
@router.get("", response_model=EventTaskListResponse)
async def get_event_tasks(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    status: Optional[EventTaskStatus] = Query(None, description="任务状态筛选"),
    task_type: Optional[EventTaskType] = Query(None, description="任务类型筛选"),
    ai_service_id: Optional[int] = Query(None, description="AI服务ID筛选"),
    camera_id: Optional[int] = Query(None, description="摄像头ID筛选"),
    is_active: Optional[bool] = Query(None, description="是否启用筛选"),
    assigned_worker: Optional[str] = Query(None, description="Worker筛选"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取事件任务列表"""
    try:
        # 构建查询条件
        query = select(EventTask)
        count_query = select(func.count(EventTask.id))
        
        conditions = []
        
        if search:
            search_condition = or_(
                EventTask.name.ilike(f"%{search}%"),
                EventTask.description.ilike(f"%{search}%"),
                EventTask.camera_name.ilike(f"%{search}%"),
                EventTask.algorithm_name.ilike(f"%{search}%")
            )
            conditions.append(search_condition)
            
        if status:
            conditions.append(EventTask.status == status)
            
        if task_type:
            conditions.append(EventTask.task_type == task_type)
            
        if ai_service_id:
            conditions.append(EventTask.ai_service_id == ai_service_id)
            
        if camera_id:
            conditions.append(EventTask.camera_id == camera_id)
            
        if is_active is not None:
            conditions.append(EventTask.is_active == is_active)
            
        if assigned_worker:
            conditions.append(EventTask.assigned_worker.ilike(f"%{assigned_worker}%"))
            
        if start_date:
            conditions.append(EventTask.created_at >= start_date)
            
        if end_date:
            end_datetime = datetime.combine(end_date, datetime.max.time())
            conditions.append(EventTask.created_at <= end_datetime)
            
        if conditions:
            query = query.where(and_(*conditions))
            count_query = count_query.where(and_(*conditions))
            
        # 获取总数
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        
        # 分页查询
        offset = (page - 1) * page_size
        query = query.order_by(desc(EventTask.created_at)).offset(offset).limit(page_size)
        
        result = await db.execute(query)
        tasks = result.scalars().all()
        
        total_pages = (total + page_size - 1) // page_size
        
        return EventTaskListResponse(
            tasks=[EventTaskResponse.model_validate(task.__dict__) for task in tasks],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取事件任务列表失败: {str(e)}"
        )

@router.post("/", response_model=EventTaskResponse)
async def create_event_task(
    task_data: EventTaskCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建事件任务"""
    try:
        # 使用事件任务管理器创建任务
        task_id = await event_task_manager.create_task_from_service(
            task_data.ai_service_id, 
            current_user.username
        )
        
        if not task_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="创建事件任务失败"
            )
            
        # 获取创建的任务
        result = await db.execute(
            select(EventTask).where(EventTask.id == task_id)
        )
        task = result.scalar_one_or_none()
        
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="任务创建后未找到"
            )
            
        return EventTaskResponse.model_validate(task.__dict__)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建事件任务失败: {str(e)}"
        )

@router.get("/{task_id}", response_model=EventTaskResponse)
async def get_event_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取事件任务详情"""
    try:
        result = await db.execute(
            select(EventTask).where(EventTask.id == task_id)
        )
        task = result.scalar_one_or_none()
        
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="事件任务不存在"
            )
            
        return EventTaskResponse.model_validate(task.__dict__)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取事件任务详情失败: {str(e)}"
        )

@router.put("/{task_id}", response_model=EventTaskResponse)
async def update_event_task(
    task_id: int,
    task_data: EventTaskUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新事件任务"""
    try:
        result = await db.execute(
            select(EventTask).where(EventTask.id == task_id)
        )
        task = result.scalar_one_or_none()
        
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="事件任务不存在"
            )
            
        # 更新任务字段
        update_data = task_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(task, field, value)
            
        task.updated_at = datetime.now()
        
        await db.commit()
        await db.refresh(task)
        
        return EventTaskResponse.model_validate(task.__dict__)
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新事件任务失败: {str(e)}"
        )

@router.delete("/{task_id}")
async def delete_event_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除事件任务"""
    try:
        result = await db.execute(
            select(EventTask).where(EventTask.id == task_id)
        )
        task = result.scalar_one_or_none()
        
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="事件任务不存在"
            )
            
        # 如果任务正在运行，先停止
        if task.status == EventTaskStatus.RUNNING:
            await event_task_manager.stop_task(task_id, "任务删除")
            
        await db.delete(task)
        await db.commit()
        
        return {"message": "事件任务删除成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除事件任务失败: {str(e)}"
        )

@router.post("/{task_id}/start")
async def start_event_task(
    task_id: int,
    worker_id: Optional[str] = Query(None, description="指定Worker ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """启动事件任务"""
    try:
        success = await event_task_manager.start_task(task_id, worker_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="启动事件任务失败"
            )
            
        return {"message": "事件任务启动成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"启动事件任务失败: {str(e)}"
        )

@router.post("/{task_id}/stop")
async def stop_event_task(
    task_id: int,
    reason: Optional[str] = Query("手动停止", description="停止原因"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """停止事件任务"""
    try:
        success = await event_task_manager.stop_task(task_id, reason)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="停止事件任务失败"
            )
            
        return {"message": "事件任务停止成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"停止事件任务失败: {str(e)}"
        )

@router.get("/{task_id}/logs", response_model=List[EventTaskLogResponse])
async def get_event_task_logs(
    task_id: int,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(50, ge=1, le=200, description="每页数量"),
    log_type: Optional[str] = Query(None, description="日志类型筛选"),
    log_level: Optional[str] = Query(None, description="日志级别筛选"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取事件任务日志"""
    try:
        # 验证任务存在
        task_result = await db.execute(
            select(EventTask).where(EventTask.id == task_id)
        )
        if not task_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="事件任务不存在"
            )
            
        # 构建查询条件
        query = select(EventTaskLog).where(EventTaskLog.task_id == task_id)
        
        conditions = []
        
        if log_type:
            conditions.append(EventTaskLog.log_type == log_type)
            
        if log_level:
            conditions.append(EventTaskLog.log_level == log_level)
            
        if start_date:
            conditions.append(EventTaskLog.created_at >= start_date)
            
        if end_date:
            end_datetime = datetime.combine(end_date, datetime.max.time())
            conditions.append(EventTaskLog.created_at <= end_datetime)
            
        if conditions:
            query = query.where(and_(*conditions))
            
        # 分页查询
        offset = (page - 1) * page_size
        query = query.order_by(desc(EventTaskLog.created_at)).offset(offset).limit(page_size)
        
        result = await db.execute(query)
        logs = result.scalars().all()
        
        return [EventTaskLogResponse.model_validate(log.__dict__) for log in logs]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取事件任务日志失败: {str(e)}"
        )

@router.get("/stats/overview", response_model=EventTaskStatsResponse)
async def get_event_task_stats(
    days: int = Query(7, ge=1, le=30, description="统计天数"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取事件任务统计信息"""
    try:
        # 时间范围
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # 总任务数
        total_result = await db.execute(
            select(func.count(EventTask.id))
        )
        total_tasks = total_result.scalar() or 0
        
        # 按状态统计
        status_result = await db.execute(
            select(EventTask.status, func.count(EventTask.id))
            .group_by(EventTask.status)
        )
        status_stats = {status.value: count for status, count in status_result.all()}
        
        # 按类型统计
        type_result = await db.execute(
            select(EventTask.task_type, func.count(EventTask.id))
            .group_by(EventTask.task_type)
        )
        type_stats = {task_type.value: count for task_type, count in type_result.all()}
        
        # 检测统计
        detection_result = await db.execute(
            select(
                func.sum(EventTask.total_detections),
                func.sum(EventTask.total_events),
                func.avg(EventTask.avg_processing_time)
            ).where(
                EventTask.created_at >= start_date
            )
        )
        detection_stats = detection_result.first()
        
        total_detections = detection_stats[0] or 0
        total_events = detection_stats[1] or 0
        avg_processing_time = detection_stats[2]
        
        # 成功率计算
        success_result = await db.execute(
            select(
                func.sum(EventTask.success_detections),
                func.sum(EventTask.total_detections)
            ).where(
                EventTask.created_at >= start_date
            )
        )
        success_stats = success_result.first()
        success_detections = success_stats[0] or 0
        total_detections_for_rate = success_stats[1] or 0
        
        success_rate = (success_detections / total_detections_for_rate * 100) if total_detections_for_rate > 0 else 0
        
        return EventTaskStatsResponse(
            total_tasks=total_tasks,
            running_tasks=status_stats.get(EventTaskStatus.RUNNING.value, 0),
            stopped_tasks=status_stats.get(EventTaskStatus.STOPPED.value, 0),
            failed_tasks=status_stats.get(EventTaskStatus.FAILED.value, 0),
            pending_tasks=status_stats.get(EventTaskStatus.PENDING.value, 0),
            total_detections=total_detections,
            total_events=total_events,
            avg_processing_time=avg_processing_time,
            success_rate=round(success_rate, 2),
            by_status=status_stats,
            by_type=type_stats
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取事件任务统计失败: {str(e)}"
        )

@router.get("/running/list")
async def get_running_tasks(
    current_user: User = Depends(get_current_user)
):
    """获取当前运行中的任务列表"""
    try:
        running_tasks = await event_task_manager.get_running_tasks()
        return {
            "running_tasks": running_tasks,
            "count": len(running_tasks)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取运行中任务失败: {str(e)}"
        )

# Worker节点任务获取API（无认证）
@router.get("/worker/tasks/fetch", dependencies=[])
async def fetch_event_tasks_for_worker(
    node_id: str = Query(..., description="Worker节点ID"),
    batch_size: int = Query(1, ge=1, le=10, description="批量获取任务数量"),
    db: AsyncSession = Depends(get_db)
):
    """为分布式Worker节点获取待执行的事件任务"""
    try:
        # 查找状态为PENDING且分配给该worker或未分配的事件任务
        query = select(EventTask).where(
            and_(
                EventTask.is_active == True,
                EventTask.status == EventTaskStatus.PENDING,
                or_(
                    EventTask.assigned_worker == node_id,
                    EventTask.assigned_worker.is_(None)
                )
            )
        ).limit(batch_size)
        
        result = await db.execute(query)
        tasks = result.scalars().all()
        
        # 将任务标记为运行中并分配给该worker
        task_list = []
        for task in tasks:
            task.status = EventTaskStatus.RUNNING
            task.assigned_worker = node_id
            task.worker_heartbeat = datetime.now()
            task_list.append({
                "id": task.id,
                "task_id": task.task_id,
                "name": task.name,
                "task_type": task.task_type.value,
                "ai_service_id": task.ai_service_id,
                "camera_id": task.camera_id,
                "camera_name": task.camera_name,
                "algorithm_id": task.algorithm_id,
                "algorithm_name": task.algorithm_name,
                "model_id": task.model_id,
                "model_name": task.model_name,
                "detection_config": task.detection_config,
                "roi_areas": task.roi_areas,
                "alarm_threshold": task.alarm_threshold,
                "check_interval": task.check_interval,
                "assigned_node": node_id
            })
        
        await db.commit()
        
        return {
            "tasks": task_list,
            "total_available": len(task_list)
        }
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取事件任务失败: {str(e)}"
        )

@router.post("/worker/tasks/{task_id}/complete")
async def complete_event_task(
    task_id: int,
    result_data: Dict[str, Any],
    node_id: str = Query(..., description="Worker节点ID"),
    db: AsyncSession = Depends(get_db)
):
    """分布式Worker节点完成事件任务后的回调"""
    try:
        # 查询任务
        result = await db.execute(
            select(EventTask).where(EventTask.id == task_id)
        )
        task = result.scalar_one_or_none()
        
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="事件任务不存在"
            )
        
        # 更新任务状态和统计信息
        task.status = EventTaskStatus.COMPLETED if result_data.get("success", False) else EventTaskStatus.FAILED
        task.last_detection_time = datetime.now()
        
        # 更新检测统计
        if result_data.get("success", False):
            task.success_detections += 1
            task.total_detections += 1
            if result_data.get("events_detected", 0) > 0:
                task.total_events += result_data.get("events_detected", 0)
                task.last_event_time = datetime.now()
        else:
            task.failed_detections += 1
            task.error_count += 1
            task.last_error = result_data.get("error_message")
        
        # 更新处理时间
        if result_data.get("processing_time"):
            if task.avg_processing_time:
                task.avg_processing_time = (task.avg_processing_time + result_data.get("processing_time")) / 2
            else:
                task.avg_processing_time = result_data.get("processing_time")
        
        task.updated_at = datetime.now()
        
        # 记录任务日志
        from models.event_task import EventTaskLog
        log = EventTaskLog(
            task_id=task_id,
            log_type="execution",
            log_level="INFO" if result_data.get("success", False) else "ERROR",
            message=f"任务执行{'成功' if result_data.get('success', False) else '失败'}",
            details=result_data,
            worker_id=node_id,
            processing_time=result_data.get("processing_time"),
            detection_result=result_data.get("detection_result", {}),
            event_count=result_data.get("events_detected", 0)
        )
        db.add(log)
        
        await db.commit()
        
        return {"message": "事件任务完成状态已更新"}
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新事件任务完成状态失败: {str(e)}"
        )

@router.post("/worker/tasks/{task_id}/heartbeat")
async def update_event_task_heartbeat(
    task_id: int,
    node_id: str = Query(..., description="Worker节点ID"),
    db: AsyncSession = Depends(get_db)
):
    """Worker节点更新事件任务心跳"""
    try:
        result = await db.execute(
            select(EventTask).where(
                and_(
                    EventTask.id == task_id,
                    EventTask.assigned_worker == node_id
                )
            )
        )
        task = result.scalar_one_or_none()
        
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="事件任务不存在或未分配给该Worker"
            )
        
        task.worker_heartbeat = datetime.now()
        await db.commit()
        
        return {"message": "心跳更新成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新心跳失败: {str(e)}"
        )