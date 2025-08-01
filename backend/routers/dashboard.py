from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc
from pydantic import BaseModel
from typing import Dict, Any, List
from datetime import datetime, timedelta
import psutil

from database import get_db
from models.user import User
from models.camera import Camera, CameraStatus
from models.event import Event, EventStatus
from models.diagnosis import DiagnosisTask, TaskStatus
from models.ai_algorithm import AIAlgorithm
from routers.auth import get_current_user

router = APIRouter()

# Pydantic models
class DashboardStats(BaseModel):
    """仪表盘统计数据"""
    total_cameras: int
    online_cameras: int
    offline_cameras: int
    total_events: int
    today_events: int
    unhandled_events: int
    running_tasks: int
    completed_tasks_today: int
    failed_tasks_today: int
    total_algorithms: int
    active_algorithms: int
    system_health: Dict[str, Any]

class EventTrendData(BaseModel):
    """事件趋势数据"""
    date: str
    event_count: int
    handled_count: int

class CameraStatusData(BaseModel):
    """摄像头状态分布数据"""
    status: str
    count: int
    percentage: float

class RecentEvent(BaseModel):
    """最近事件数据"""
    id: int
    title: str
    camera_name: str
    level: str
    status: str
    created_at: datetime

class DashboardResponse(BaseModel):
    """仪表盘响应数据"""
    stats: DashboardStats
    event_trend: List[EventTrendData]
    camera_status: List[CameraStatusData]
    recent_events: List[RecentEvent]
    last_updated: datetime

@router.get("/overview", response_model=DashboardResponse)
async def get_dashboard_overview(
    days: int = 7,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取仪表盘概览数据"""
    
    # 获取基础统计数据
    stats = await get_dashboard_stats(db)
    
    # 获取事件趋势数据
    event_trend = await get_event_trend_data(db, days)
    
    # 获取摄像头状态分布
    camera_status = await get_camera_status_data(db)
    
    # 获取最近事件
    recent_events = await get_recent_events(db, limit=10)
    
    return DashboardResponse(
        stats=stats,
        event_trend=event_trend,
        camera_status=camera_status,
        recent_events=recent_events,
        last_updated=datetime.now()
    )

async def get_dashboard_stats(db: AsyncSession) -> DashboardStats:
    """获取仪表盘统计数据"""
    
    # 摄像头统计
    total_cameras_result = await db.execute(select(func.count(Camera.id)))
    total_cameras = total_cameras_result.scalar() or 0
    
    online_cameras_result = await db.execute(
        select(func.count(Camera.id)).where(Camera.status == CameraStatus.ONLINE)
    )
    online_cameras = online_cameras_result.scalar() or 0
    
    offline_cameras = total_cameras - online_cameras
    
    # 事件统计
    total_events_result = await db.execute(select(func.count(Event.id)))
    total_events = total_events_result.scalar() or 0
    
    today = datetime.now().date()
    today_events_result = await db.execute(
        select(func.count(Event.id)).where(
            func.date(Event.created_at) == today
        )
    )
    today_events = today_events_result.scalar() or 0
    
    unhandled_events_result = await db.execute(
        select(func.count(Event.id)).where(
            Event.status == EventStatus.PENDING
        )
    )
    unhandled_events = unhandled_events_result.scalar() or 0
    
    # 诊断任务统计
    running_tasks_result = await db.execute(
        select(func.count(DiagnosisTask.id)).where(
            DiagnosisTask.status.in_([TaskStatus.PENDING, TaskStatus.RUNNING])
        )
    )
    running_tasks = running_tasks_result.scalar() or 0
    
    completed_tasks_today_result = await db.execute(
        select(func.count(DiagnosisTask.id)).where(
            and_(
                func.date(DiagnosisTask.updated_at) == today,
                DiagnosisTask.status == TaskStatus.COMPLETED
            )
        )
    )
    completed_tasks_today = completed_tasks_today_result.scalar() or 0
    
    failed_tasks_today_result = await db.execute(
        select(func.count(DiagnosisTask.id)).where(
            and_(
                func.date(DiagnosisTask.updated_at) == today,
                DiagnosisTask.status == TaskStatus.FAILED
            )
        )
    )
    failed_tasks_today = failed_tasks_today_result.scalar() or 0
    
    # AI算法统计
    total_algorithms_result = await db.execute(select(func.count(AIAlgorithm.id)))
    total_algorithms = total_algorithms_result.scalar() or 0
    
    active_algorithms_result = await db.execute(
        select(func.count(AIAlgorithm.id)).where(AIAlgorithm.is_active == True)
    )
    active_algorithms = active_algorithms_result.scalar() or 0
    
    # 系统健康状态
    system_health = get_system_health()
    
    return DashboardStats(
        total_cameras=total_cameras,
        online_cameras=online_cameras,
        offline_cameras=offline_cameras,
        total_events=total_events,
        today_events=today_events,
        unhandled_events=unhandled_events,
        running_tasks=running_tasks,
        completed_tasks_today=completed_tasks_today,
        failed_tasks_today=failed_tasks_today,
        total_algorithms=total_algorithms,
        active_algorithms=active_algorithms,
        system_health=system_health
    )

async def get_event_trend_data(db: AsyncSession, days: int) -> List[EventTrendData]:
    """获取事件趋势数据"""
    
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days-1)
    
    # 获取每日事件数量
    event_counts_result = await db.execute(
        select(
            func.date(Event.created_at).label('date'),
            func.count(Event.id).label('event_count')
        ).where(
            func.date(Event.created_at).between(start_date, end_date)
        ).group_by(
            func.date(Event.created_at)
        ).order_by(
            func.date(Event.created_at)
        )
    )
    event_counts = event_counts_result.all()
    
    # 获取每日处理数量
    handled_counts_result = await db.execute(
        select(
            func.date(Event.updated_at).label('date'),
            func.count(Event.id).label('handled_count')
        ).where(
            and_(
                func.date(Event.updated_at).between(start_date, end_date),
                Event.status.in_([EventStatus.RESOLVED, EventStatus.FALSE_ALARM, EventStatus.IGNORED])
            )
        ).group_by(
            func.date(Event.updated_at)
        ).order_by(
            func.date(Event.updated_at)
        )
    )
    handled_counts = handled_counts_result.all()
    
    # 创建日期到数量的映射
    event_count_map = {row.date: row.event_count for row in event_counts}
    handled_count_map = {row.date: row.handled_count for row in handled_counts}
    
    # 生成完整的日期序列
    trend_data = []
    current_date = start_date
    while current_date <= end_date:
        trend_data.append(EventTrendData(
            date=current_date.strftime('%Y-%m-%d'),
            event_count=event_count_map.get(current_date, 0),
            handled_count=handled_count_map.get(current_date, 0)
        ))
        current_date += timedelta(days=1)
    
    return trend_data

async def get_camera_status_data(db: AsyncSession) -> List[CameraStatusData]:
    """获取摄像头状态分布数据"""
    
    status_counts_result = await db.execute(
        select(
            Camera.status,
            func.count(Camera.id).label('count')
        ).group_by(Camera.status)
    )
    status_counts = status_counts_result.all()
    
    total_cameras = sum(row.count for row in status_counts)
    
    status_data = []
    for row in status_counts:
        percentage = (row.count / total_cameras * 100) if total_cameras > 0 else 0
        status_data.append(CameraStatusData(
            status=row.status,
            count=row.count,
            percentage=round(percentage, 2)
        ))
    
    return status_data

async def get_recent_events(db: AsyncSession, limit: int = 10) -> List[RecentEvent]:
    """获取最近事件数据"""
    
    events_result = await db.execute(
        select(Event, Camera.name.label('camera_name'))
        .join(Camera, Event.camera_id == Camera.id, isouter=True)
        .order_by(desc(Event.created_at))
        .limit(limit)
    )
    events = events_result.all()
    
    recent_events = []
    for event, camera_name in events:
        recent_events.append(RecentEvent(
            id=event.id,
            title=event.title or "未知事件",
            camera_name=camera_name or "未知摄像头",
            level=event.level or "info",
            status=event.status or "pending",
            created_at=event.created_at
        ))
    
    return recent_events

def get_system_health() -> Dict[str, Any]:
    """获取系统健康状态"""
    
    try:
        # CPU使用率
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # 内存使用率
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        
        # 磁盘使用率
        disk = psutil.disk_usage('/')
        disk_percent = disk.percent
        
        # 网络状态
        network = psutil.net_io_counters()
        
        return {
            "cpu_percent": round(cpu_percent, 2),
            "memory_percent": round(memory_percent, 2),
            "disk_percent": round(disk_percent, 2),
            "network_sent": network.bytes_sent,
            "network_recv": network.bytes_recv,
            "status": "healthy" if cpu_percent < 80 and memory_percent < 80 and disk_percent < 90 else "warning"
        }
    except Exception as e:
        return {
            "cpu_percent": 0,
            "memory_percent": 0,
            "disk_percent": 0,
            "network_sent": 0,
            "network_recv": 0,
            "status": "error",
            "error": str(e)
        }

@router.get("/system-health")
async def get_system_health_endpoint(
    current_user: User = Depends(get_current_user)
):
    """获取系统健康状态"""
    return get_system_health()