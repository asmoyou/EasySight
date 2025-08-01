from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, date, timedelta

from database import get_db
from models.event import Event, EventRule, EventNotification, EventStatistics, EventType, EventLevel, EventStatus
from models.user import User
from routers.auth import get_current_user

router = APIRouter()

# Pydantic models
class EventCreate(BaseModel):
    event_type: EventType
    event_level: EventLevel = EventLevel.MEDIUM
    title: str
    description: Optional[str] = None
    camera_id: int
    camera_name: Optional[str] = None
    camera_location: Optional[str] = None
    algorithm_id: Optional[int] = None
    algorithm_name: Optional[str] = None
    confidence_score: Optional[float] = None
    longitude: Optional[float] = None
    latitude: Optional[float] = None
    location_description: Optional[str] = None
    detection_area: Optional[Dict[str, Any]] = None
    roi_name: Optional[str] = None
    image_urls: List[str] = []
    video_urls: List[str] = []
    thumbnail_url: Optional[str] = None
    detected_objects: List[Dict[str, Any]] = []
    object_count: int = 0
    event_time: datetime
    event_metadata: Dict[str, Any] = {}
    tags: List[str] = []

class EventUpdate(BaseModel):
    event_type: Optional[EventType] = None
    event_level: Optional[EventLevel] = None
    title: Optional[str] = None
    description: Optional[str] = None
    camera_id: Optional[int] = None
    camera_name: Optional[str] = None
    camera_location: Optional[str] = None
    algorithm_id: Optional[int] = None
    algorithm_name: Optional[str] = None
    confidence_score: Optional[float] = None
    longitude: Optional[float] = None
    latitude: Optional[float] = None
    location_description: Optional[str] = None
    detection_area: Optional[Dict[str, Any]] = None
    roi_name: Optional[str] = None
    image_urls: Optional[List[str]] = None
    video_urls: Optional[List[str]] = None
    thumbnail_url: Optional[str] = None
    detected_objects: Optional[List[Dict[str, Any]]] = None
    object_count: Optional[int] = None
    status: Optional[EventStatus] = None
    is_read: Optional[bool] = None
    is_important: Optional[bool] = None
    assigned_to: Optional[str] = None
    processed_by: Optional[str] = None
    processed_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None
    event_time: Optional[datetime] = None
    event_metadata: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None

class EventResponse(BaseModel):
    id: int
    event_id: str
    event_type: EventType
    event_level: EventLevel
    status: EventStatus
    title: str
    description: Optional[str]
    camera_id: int
    camera_name: Optional[str]
    camera_location: Optional[str]
    algorithm_id: Optional[int]
    algorithm_name: Optional[str]
    confidence_score: Optional[float]
    longitude: Optional[float]
    latitude: Optional[float]
    location_description: Optional[str]
    detection_area: Optional[Dict[str, Any]]
    roi_name: Optional[str]
    image_urls: List[str]
    video_urls: List[str]
    thumbnail_url: Optional[str]
    detected_objects: List[Dict[str, Any]]
    object_count: int
    is_read: bool
    is_important: bool
    assigned_to: Optional[str]
    processed_by: Optional[str]
    processed_at: Optional[datetime]
    resolution_notes: Optional[str]
    event_time: datetime
    created_at: datetime
    updated_at: datetime
    event_metadata: Dict[str, Any]
    tags: List[str]

class EventListResponse(BaseModel):
    events: List[EventResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

class EventRuleCreate(BaseModel):
    name: str
    event_type: EventType
    conditions: Dict[str, Any]
    actions: Dict[str, Any]
    is_active: bool = True
    priority: int = 0
    description: Optional[str] = None

class EventRuleUpdate(BaseModel):
    name: Optional[str] = None
    conditions: Optional[Dict[str, Any]] = None
    actions: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None
    priority: Optional[int] = None
    description: Optional[str] = None

class EventRuleResponse(BaseModel):
    id: int
    name: str
    event_type: EventType
    conditions: Dict[str, Any]
    actions: Dict[str, Any]
    is_active: bool
    priority: int
    trigger_count: int
    last_triggered: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    description: Optional[str]

class EventNotificationCreate(BaseModel):
    event_id: int
    notification_type: str
    recipient: str
    title: str
    content: str
    config: Dict[str, Any] = {}

class EventNotificationResponse(BaseModel):
    id: int
    event_id: int
    notification_type: str
    recipient: str
    title: str
    content: str
    config: Dict[str, Any]
    status: str
    sent_at: Optional[datetime]
    error_message: Optional[str]
    created_at: datetime

class EventStatsResponse(BaseModel):
    total_events: int
    pending_events: int
    handled_events: int
    critical_events: int
    warning_events: int
    info_events: int
    today_events: int
    by_type: Dict[str, int]
    by_level: Dict[str, int]
    by_status: Dict[str, int]
    trend_data: List[Dict[str, Any]]

class EventTrendData(BaseModel):
    date: str
    count: int
    critical_count: int
    warning_count: int
    info_count: int

# 事件管理
@router.get("/", response_model=EventListResponse)
@router.get("", response_model=EventListResponse)  # 支持不带尾部斜杠的URL
async def get_events(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    event_type: Optional[EventType] = Query(None, description="事件类型筛选"),
    event_level: Optional[EventLevel] = Query(None, description="事件级别筛选"),
    status: Optional[EventStatus] = Query(None, description="事件状态筛选"),
    camera_id: Optional[int] = Query(None, description="摄像头ID筛选"),
    camera_name: Optional[str] = Query(None, description="摄像头名称筛选"),
    algorithm_name: Optional[str] = Query(None, description="算法名称筛选"),
    is_read: Optional[bool] = Query(None, description="是否已读筛选"),
    is_ongoing: Optional[bool] = Query(None, description="是否正在进行中筛选"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取事件列表"""
    conditions = []
    
    if search:
        search_pattern = f"%{search}%"
        conditions.append(
            or_(
                Event.title.ilike(search_pattern),
                Event.description.ilike(search_pattern),
                Event.camera_name.ilike(search_pattern),
                Event.camera_location.ilike(search_pattern),
                Event.algorithm_name.ilike(search_pattern)
            )
        )
    
    if event_type:
        conditions.append(Event.event_type == event_type)
    
    if event_level:
        conditions.append(Event.event_level == event_level)
    
    if status:
        conditions.append(Event.status == status)
    
    if camera_id:
        conditions.append(Event.camera_id == camera_id)
    
    if camera_name:
        conditions.append(Event.camera_name.ilike(f"%{camera_name}%"))
    
    if algorithm_name:
        conditions.append(Event.algorithm_name.ilike(f"%{algorithm_name}%"))
    
    if is_read is not None:
        conditions.append(Event.is_read == is_read)
    
    if is_ongoing is not None:
        conditions.append(Event.is_ongoing == is_ongoing)
    
    if start_date:
        conditions.append(Event.created_at >= start_date)
    
    if end_date:
        end_datetime = datetime.combine(end_date, datetime.max.time())
        conditions.append(Event.created_at <= end_datetime)
    
    # 计算总数
    count_query = select(func.count(Event.id))
    if conditions:
        count_query = count_query.where(and_(*conditions))
    
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # 查询事件列表
    query = select(Event).order_by(desc(Event.created_at))
    if conditions:
        query = query.where(and_(*conditions))
    
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    
    result = await db.execute(query)
    events = result.scalars().all()
    
    total_pages = (total + page_size - 1) // page_size
    
    return EventListResponse(
        events=[EventResponse(
            id=event.id,
            event_id=event.event_id,
            event_type=event.event_type,
            event_level=event.event_level,
            status=event.status,
            title=event.title,
            description=event.description,
            camera_id=event.camera_id,
            camera_name=event.camera_name,
            camera_location=event.camera_location,
            algorithm_id=event.algorithm_id,
            algorithm_name=event.algorithm_name,
            confidence_score=event.confidence_score,
            longitude=event.longitude,
            latitude=event.latitude,
            location_description=event.location_description,
            detection_area=event.detection_area,
            roi_name=event.roi_name,
            image_urls=event.image_urls or [],
            video_urls=event.video_urls or [],
            thumbnail_url=event.thumbnail_url,
            detected_objects=event.detected_objects or [],
            object_count=event.object_count,
            is_read=event.is_read,
            is_important=event.is_important,
            assigned_to=event.assigned_to,
            processed_by=event.processed_by,
            processed_at=event.processed_at,
            resolution_notes=event.resolution_notes,
            event_time=event.event_time,
            created_at=event.created_at,
            updated_at=event.updated_at,
            event_metadata=event.event_metadata or {},
            tags=event.tags or []
        ) for event in events],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )

@router.post("/", response_model=EventResponse)
async def create_event(
    event_data: EventCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建事件"""
    import uuid
    from datetime import datetime
    
    # 生成唯一事件ID
    event_id = f"EVT-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
    
    event_dict = event_data.dict()
    event_dict['event_id'] = event_id
    
    event = Event(**event_dict)
    db.add(event)
    await db.commit()
    await db.refresh(event)
    
    return EventResponse(
        id=event.id,
        event_id=event.event_id,
        event_type=event.event_type,
        event_level=event.event_level,
        status=event.status,
        title=event.title,
        description=event.description,
        camera_id=event.camera_id,
        camera_name=event.camera_name,
        camera_location=event.camera_location,
        algorithm_id=event.algorithm_id,
        algorithm_name=event.algorithm_name,
        confidence_score=event.confidence_score,
        longitude=event.longitude,
        latitude=event.latitude,
        location_description=event.location_description,
        detection_area=event.detection_area,
        roi_name=event.roi_name,
        image_urls=event.image_urls or [],
        video_urls=event.video_urls or [],
        thumbnail_url=event.thumbnail_url,
        detected_objects=event.detected_objects or [],
        object_count=event.object_count,
        is_read=event.is_read,
        is_important=event.is_important,
        assigned_to=event.assigned_to,
        processed_by=event.processed_by,
        processed_at=event.processed_at,
        resolution_notes=event.resolution_notes,
        event_time=event.event_time,
        created_at=event.created_at,
        updated_at=event.updated_at,
        event_metadata=event.event_metadata or {},
        tags=event.tags or []
    )

@router.get("/{event_id}", response_model=EventResponse)
async def get_event(
    event_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取事件详情"""
    result = await db.execute(select(Event).where(Event.id == event_id))
    event = result.scalar_one_or_none()
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="事件不存在"
        )
    
    return EventResponse(
        id=event.id,
        event_id=event.event_id,
        event_type=event.event_type,
        event_level=event.event_level,
        status=event.status,
        title=event.title,
        description=event.description,
        camera_id=event.camera_id,
        camera_name=event.camera_name,
        camera_location=event.camera_location,
        algorithm_id=event.algorithm_id,
        algorithm_name=event.algorithm_name,
        confidence_score=event.confidence_score,
        longitude=event.longitude,
        latitude=event.latitude,
        location_description=event.location_description,
        detection_area=event.detection_area,
        roi_name=event.roi_name,
        image_urls=event.image_urls or [],
        video_urls=event.video_urls or [],
        thumbnail_url=event.thumbnail_url,
        detected_objects=event.detected_objects or [],
        object_count=event.object_count,
        is_read=event.is_read,
        is_important=event.is_important,
        assigned_to=event.assigned_to,
        processed_by=event.processed_by,
        processed_at=event.processed_at,
        resolution_notes=event.resolution_notes,
        event_time=event.event_time,
        created_at=event.created_at,
        updated_at=event.updated_at,
        event_metadata=event.event_metadata or {},
        tags=event.tags or []
    )

@router.put("/{event_id}", response_model=EventResponse)
async def update_event(
    event_id: int,
    event_data: EventUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新事件"""
    result = await db.execute(select(Event).where(Event.id == event_id))
    event = result.scalar_one_or_none()
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="事件不存在"
        )
    
    # 更新事件信息
    update_data = event_data.dict(exclude_unset=True)
    
    # 如果状态变为确认报警或误报，自动设置处理人和处理时间
    if update_data.get('status') in [EventStatus.CONFIRMED, EventStatus.FALSE_ALARM] and not event.processed_by:
        update_data['processed_by'] = current_user.username
        update_data['processed_at'] = datetime.utcnow()
    
    for field, value in update_data.items():
        setattr(event, field, value)
    
    await db.commit()
    await db.refresh(event)
    
    return EventResponse(
        id=event.id,
        event_id=event.event_id,
        event_type=event.event_type,
        event_level=event.event_level,
        status=event.status,
        title=event.title,
        description=event.description,
        camera_id=event.camera_id,
        camera_name=event.camera_name,
        camera_location=event.camera_location,
        algorithm_id=event.algorithm_id,
        algorithm_name=event.algorithm_name,
        confidence_score=event.confidence_score,
        longitude=event.longitude,
        latitude=event.latitude,
        location_description=event.location_description,
        detection_area=event.detection_area,
        roi_name=event.roi_name,
        image_urls=event.image_urls or [],
        video_urls=event.video_urls or [],
        thumbnail_url=event.thumbnail_url,
        detected_objects=event.detected_objects or [],
        object_count=event.object_count,
        is_read=event.is_read,
        is_important=event.is_important,
        assigned_to=event.assigned_to,
        processed_by=event.processed_by,
        processed_at=event.processed_at,
        resolution_notes=event.resolution_notes,
        event_time=event.event_time,
        created_at=event.created_at,
        updated_at=event.updated_at,
        event_metadata=event.event_metadata or {},
        tags=event.tags or []
    )

@router.delete("/{event_id}")
async def delete_event(
    event_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除事件"""
    result = await db.execute(select(Event).where(Event.id == event_id))
    event = result.scalar_one_or_none()
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="事件不存在"
        )
    
    await db.delete(event)
    await db.commit()
    
    return {"message": "事件删除成功"}

# 事件状态处理相关模型
class EventStatusUpdate(BaseModel):
    resolution_notes: Optional[str] = None

@router.post("/{event_id}/confirm", response_model=EventResponse)
async def confirm_event(
    event_id: int,
    status_data: EventStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """确认报警"""
    result = await db.execute(select(Event).where(Event.id == event_id))
    event = result.scalar_one_or_none()
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="事件不存在"
        )
    
    if event.status != EventStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只能确认待处理状态的事件"
        )
    
    event.status = EventStatus.CONFIRMED
    event.processed_by = current_user.username
    event.processed_at = datetime.utcnow()
    if status_data.resolution_notes:
        event.resolution_notes = status_data.resolution_notes
    
    await db.commit()
    await db.refresh(event)
    
    return EventResponse(
        id=event.id,
        event_id=event.event_id,
        event_type=event.event_type,
        event_level=event.event_level,
        status=event.status,
        title=event.title,
        description=event.description,
        camera_id=event.camera_id,
        camera_name=event.camera_name,
        camera_location=event.camera_location,
        algorithm_id=event.algorithm_id,
        algorithm_name=event.algorithm_name,
        confidence_score=event.confidence_score,
        longitude=event.longitude,
        latitude=event.latitude,
        location_description=event.location_description,
        detection_area=event.detection_area,
        roi_name=event.roi_name,
        image_urls=event.image_urls or [],
        video_urls=event.video_urls or [],
        thumbnail_url=event.thumbnail_url,
        detected_objects=event.detected_objects or [],
        object_count=event.object_count,
        is_read=event.is_read,
        is_important=event.is_important,
        assigned_to=event.assigned_to,
        processed_by=event.processed_by,
        processed_at=event.processed_at,
        resolution_notes=event.resolution_notes,
        event_time=event.event_time,
        created_at=event.created_at,
        updated_at=event.updated_at,
        event_metadata=event.event_metadata or {},
        tags=event.tags or []
    )

@router.post("/{event_id}/false-alarm", response_model=EventResponse)
async def mark_false_alarm(
    event_id: int,
    status_data: EventStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """标记为误报"""
    result = await db.execute(select(Event).where(Event.id == event_id))
    event = result.scalar_one_or_none()
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="事件不存在"
        )
    
    if event.status != EventStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只能标记待处理状态的事件为误报"
        )
    
    event.status = EventStatus.FALSE_ALARM
    event.processed_by = current_user.username
    event.processed_at = datetime.utcnow()
    if status_data.resolution_notes:
        event.resolution_notes = status_data.resolution_notes
    
    await db.commit()
    await db.refresh(event)
    
    return EventResponse(
        id=event.id,
        event_id=event.event_id,
        event_type=event.event_type,
        event_level=event.event_level,
        status=event.status,
        title=event.title,
        description=event.description,
        camera_id=event.camera_id,
        camera_name=event.camera_name,
        camera_location=event.camera_location,
        algorithm_id=event.algorithm_id,
        algorithm_name=event.algorithm_name,
        confidence_score=event.confidence_score,
        longitude=event.longitude,
        latitude=event.latitude,
        location_description=event.location_description,
        detection_area=event.detection_area,
        roi_name=event.roi_name,
        image_urls=event.image_urls or [],
        video_urls=event.video_urls or [],
        thumbnail_url=event.thumbnail_url,
        detected_objects=event.detected_objects or [],
        object_count=event.object_count,
        is_read=event.is_read,
        is_important=event.is_important,
        assigned_to=event.assigned_to,
        processed_by=event.processed_by,
        processed_at=event.processed_at,
        resolution_notes=event.resolution_notes,
        event_time=event.event_time,
        created_at=event.created_at,
        updated_at=event.updated_at,
        event_metadata=event.event_metadata or {},
        tags=event.tags or []
    )

@router.post("/{event_id}/mark-read")
async def mark_event_read(
    event_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """标记事件为已读"""
    result = await db.execute(select(Event).where(Event.id == event_id))
    event = result.scalar_one_or_none()
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="事件不存在"
        )
    
    event.is_read = True
    await db.commit()
    
    return {"message": "事件已标记为已读"}

# 事件规则管理
@router.get("/rules/", response_model=List[EventRuleResponse])
async def get_event_rules(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    event_type: Optional[EventType] = Query(None, description="事件类型筛选"),
    is_active: Optional[bool] = Query(None, description="是否启用"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取事件规则列表"""
    conditions = []
    
    if search:
        search_pattern = f"%{search}%"
        conditions.append(
            or_(
                EventRule.name.ilike(search_pattern),
                EventRule.description.ilike(search_pattern)
            )
        )
    
    if event_type:
        conditions.append(EventRule.event_type == event_type)
    
    if is_active is not None:
        conditions.append(EventRule.is_active == is_active)
    
    query = select(EventRule).order_by(EventRule.priority.desc(), EventRule.created_at.desc())
    if conditions:
        query = query.where(and_(*conditions))
    
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    
    result = await db.execute(query)
    rules = result.scalars().all()
    
    return [EventRuleResponse(
        id=rule.id,
        name=rule.name,
        event_type=rule.event_type,
        conditions=rule.conditions,
        actions=rule.actions,
        is_active=rule.is_active,
        priority=rule.priority,
        trigger_count=rule.trigger_count,
        last_triggered=rule.last_triggered,
        created_at=rule.created_at,
        updated_at=rule.updated_at,
        description=rule.description
    ) for rule in rules]

@router.post("/rules/", response_model=EventRuleResponse)
async def create_event_rule(
    rule_data: EventRuleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建事件规则"""
    rule = EventRule(**rule_data.dict())
    db.add(rule)
    await db.commit()
    await db.refresh(rule)
    
    return EventRuleResponse(
        id=rule.id,
        name=rule.name,
        event_type=rule.event_type,
        conditions=rule.conditions,
        actions=rule.actions,
        is_active=rule.is_active,
        priority=rule.priority,
        trigger_count=rule.trigger_count,
        last_triggered=rule.last_triggered,
        created_at=rule.created_at,
        updated_at=rule.updated_at,
        description=rule.description
    )

# 事件统计
@router.get("/stats/overview", response_model=EventStatsResponse)
async def get_event_stats(
    days: int = Query(7, ge=1, le=30, description="统计天数"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取事件统计信息"""
    # 总事件数
    total_result = await db.execute(select(func.count(Event.id)))
    total_events = total_result.scalar()
    
    # 待处理事件数
    pending_result = await db.execute(select(func.count(Event.id)).where(Event.status == EventStatus.PENDING))
    pending_events = pending_result.scalar()
    
    # 已处理事件数
    handled_result = await db.execute(select(func.count(Event.id)).where(Event.status == EventStatus.HANDLED))
    handled_events = handled_result.scalar()
    
    # 各级别事件数
    critical_result = await db.execute(select(func.count(Event.id)).where(Event.level == EventLevel.CRITICAL))
    critical_events = critical_result.scalar()
    
    warning_result = await db.execute(select(func.count(Event.id)).where(Event.level == EventLevel.WARNING))
    warning_events = warning_result.scalar()
    
    info_result = await db.execute(select(func.count(Event.id)).where(Event.level == EventLevel.INFO))
    info_events = info_result.scalar()
    
    # 今日事件数
    today = date.today()
    today_result = await db.execute(
        select(func.count(Event.id))
        .where(func.date(Event.created_at) == today)
    )
    today_events = today_result.scalar()
    
    # 按类型统计
    type_result = await db.execute(
        select(Event.event_type, func.count(Event.id))
        .group_by(Event.event_type)
    )
    by_type = {str(row[0].value): row[1] for row in type_result.all()}
    
    # 按级别统计
    level_result = await db.execute(
        select(Event.level, func.count(Event.id))
        .group_by(Event.level)
    )
    by_level = {str(row[0].value): row[1] for row in level_result.all()}
    
    # 按状态统计
    status_result = await db.execute(
        select(Event.status, func.count(Event.id))
        .group_by(Event.status)
    )
    by_status = {str(row[0].value): row[1] for row in status_result.all()}
    
    # 趋势数据
    trend_data = []
    for i in range(days):
        target_date = today - timedelta(days=i)
        
        # 当日总数
        daily_result = await db.execute(
            select(func.count(Event.id))
            .where(func.date(Event.created_at) == target_date)
        )
        daily_count = daily_result.scalar()
        
        # 当日各级别数量
        critical_daily = await db.execute(
            select(func.count(Event.id))
            .where(
                and_(
                    func.date(Event.created_at) == target_date,
                    Event.level == EventLevel.CRITICAL
                )
            )
        )
        critical_count = critical_daily.scalar()
        
        warning_daily = await db.execute(
            select(func.count(Event.id))
            .where(
                and_(
                    func.date(Event.created_at) == target_date,
                    Event.level == EventLevel.WARNING
                )
            )
        )
        warning_count = warning_daily.scalar()
        
        info_daily = await db.execute(
            select(func.count(Event.id))
            .where(
                and_(
                    func.date(Event.created_at) == target_date,
                    Event.level == EventLevel.INFO
                )
            )
        )
        info_count = info_daily.scalar()
        
        trend_data.append({
            "date": target_date.strftime("%Y-%m-%d"),
            "count": daily_count,
            "critical_count": critical_count,
            "warning_count": warning_count,
            "info_count": info_count
        })
    
    trend_data.reverse()  # 按时间正序排列
    
    return EventStatsResponse(
        total_events=total_events,
        pending_events=pending_events,
        handled_events=handled_events,
        critical_events=critical_events,
        warning_events=warning_events,
        info_events=info_events,
        today_events=today_events,
        by_type=by_type,
        by_level=by_level,
        by_status=by_status,
        trend_data=trend_data
    )

# 事件通知管理
@router.get("/notifications/", response_model=List[EventNotificationResponse])
async def get_event_notifications(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    event_id: Optional[int] = Query(None, description="事件ID筛选"),
    notification_type: Optional[str] = Query(None, description="通知类型筛选"),
    status: Optional[str] = Query(None, description="状态筛选"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取事件通知列表"""
    conditions = []
    
    if event_id:
        conditions.append(EventNotification.event_id == event_id)
    
    if notification_type:
        conditions.append(EventNotification.notification_type == notification_type)
    
    if status:
        conditions.append(EventNotification.status == status)
    
    query = select(EventNotification).order_by(desc(EventNotification.created_at))
    if conditions:
        query = query.where(and_(*conditions))
    
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    
    result = await db.execute(query)
    notifications = result.scalars().all()
    
    return [EventNotificationResponse(
        id=notification.id,
        event_id=notification.event_id,
        notification_type=notification.notification_type,
        recipient=notification.recipient,
        title=notification.title,
        content=notification.content,
        config=notification.config,
        status=notification.status,
        sent_at=notification.sent_at,
        error_message=notification.error_message,
        created_at=notification.created_at
    ) for notification in notifications]

@router.post("/notifications/", response_model=EventNotificationResponse)
async def create_event_notification(
    notification_data: EventNotificationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建事件通知"""
    # 验证事件是否存在
    event_result = await db.execute(select(Event).where(Event.id == notification_data.event_id))
    if not event_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="指定的事件不存在"
        )
    
    notification = EventNotification(**notification_data.dict())
    db.add(notification)
    await db.commit()
    await db.refresh(notification)
    
    return EventNotificationResponse(
        id=notification.id,
        event_id=notification.event_id,
        notification_type=notification.notification_type,
        recipient=notification.recipient,
        title=notification.title,
        content=notification.content,
        config=notification.config,
        status=notification.status,
        sent_at=notification.sent_at,
        error_message=notification.error_message,
        created_at=notification.created_at
    )