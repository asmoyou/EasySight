from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc, case
from pydantic import BaseModel
from typing import Dict, Any, List
from datetime import datetime, timedelta
import psutil
import time
import asyncio

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
    """获取仪表盘概览数据（优化版本，带缓存）"""
    
    global _dashboard_cache
    
    # 生成缓存键
    cache_key = f"dashboard_overview_{days}"
    current_time = time.time()
    
    # 检查缓存是否有效
    if (cache_key in _dashboard_cache and 
        current_time - _dashboard_cache[cache_key]['timestamp'] < _cache_timeout):
        return _dashboard_cache[cache_key]['data']
    
    # 并发执行所有数据获取操作以提升性能
    stats, event_trend, camera_status, recent_events = await asyncio.gather(
        get_dashboard_stats(db),
        get_event_trend_data(db, days),
        get_camera_status_data(db),
        get_recent_events(db, limit=10)
    )
    
    response = DashboardResponse(
        stats=stats,
        event_trend=event_trend,
        camera_status=camera_status,
        recent_events=recent_events,
        last_updated=datetime.now()
    )
    
    # 更新缓存
    _dashboard_cache[cache_key] = {
        'data': response,
        'timestamp': current_time
    }
    
    # 清理过期缓存（简单的清理策略）
    expired_keys = [
        key for key, value in _dashboard_cache.items()
        if current_time - value['timestamp'] > _cache_timeout * 2
    ]
    for key in expired_keys:
        del _dashboard_cache[key]
    
    return response

async def get_dashboard_stats(db: AsyncSession) -> DashboardStats:
    """获取仪表盘统计数据（优化版本）"""
    
    today = datetime.now().date()
    
    # 并发执行所有查询以提升性能
    async def get_camera_stats():
        """获取摄像头统计"""
        result = await db.execute(
            select(
                func.count(Camera.id).label('total'),
                func.sum(case((Camera.status == CameraStatus.ONLINE, 1), else_=0)).label('online')
            )
        )
        row = result.first()
        total = row.total or 0
        online = row.online or 0
        return total, online, total - online
    
    async def get_event_stats():
        """获取事件统计"""
        result = await db.execute(
            select(
                func.count(Event.id).label('total'),
                func.sum(case((func.date(Event.created_at) == today, 1), else_=0)).label('today'),
                func.sum(case((Event.status == EventStatus.PENDING, 1), else_=0)).label('unhandled')
            )
        )
        row = result.first()
        return row.total or 0, row.today or 0, row.unhandled or 0
    
    async def get_task_stats():
        """获取诊断任务统计"""
        result = await db.execute(
            select(
                func.sum(case((
                    DiagnosisTask.status.in_([TaskStatus.PENDING, TaskStatus.RUNNING]), 1
                ), else_=0)).label('running'),
                func.sum(case((
                    and_(
                        func.date(DiagnosisTask.updated_at) == today,
                        DiagnosisTask.status == TaskStatus.COMPLETED
                    ), 1
                ), else_=0)).label('completed_today'),
                func.sum(case((
                    and_(
                        func.date(DiagnosisTask.updated_at) == today,
                        DiagnosisTask.status == TaskStatus.FAILED
                    ), 1
                ), else_=0)).label('failed_today')
            )
        )
        row = result.first()
        return row.running or 0, row.completed_today or 0, row.failed_today or 0
    
    async def get_algorithm_stats():
        """获取AI算法统计"""
        result = await db.execute(
            select(
                func.count(AIAlgorithm.id).label('total'),
                func.sum(case((AIAlgorithm.is_active == True, 1), else_=0)).label('active')
            )
        )
        row = result.first()
        return row.total or 0, row.active or 0
    
    # 并发执行所有数据库查询
    (
        (total_cameras, online_cameras, offline_cameras),
        (total_events, today_events, unhandled_events),
        (running_tasks, completed_tasks_today, failed_tasks_today),
        (total_algorithms, active_algorithms)
    ) = await asyncio.gather(
        get_camera_stats(),
        get_event_stats(),
        get_task_stats(),
        get_algorithm_stats()
    )
    
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
    """获取事件趋势数据（优化版本）"""
    
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days-1)
    
    # 并发获取事件创建和处理数据
    async def get_event_counts():
        result = await db.execute(
            select(
                func.date(Event.created_at).label('date'),
                func.count(Event.id).label('event_count')
            ).where(
                func.date(Event.created_at).between(start_date, end_date)
            ).group_by(
                func.date(Event.created_at)
            )
        )
        return {row.date: row.event_count for row in result.all()}
    
    async def get_handled_counts():
        result = await db.execute(
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
            )
        )
        return {row.date: row.handled_count for row in result.all()}
    
    # 并发执行两个查询
    event_count_map, handled_count_map = await asyncio.gather(
        get_event_counts(),
        get_handled_counts()
    )
    
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

# 全局变量用于存储上次网络统计数据
_last_network_stats = None
_last_network_time = None

# 缓存变量用于优化仪表盘性能
_dashboard_cache = {}
_cache_timeout = 30  # 缓存30秒

def get_system_health() -> Dict[str, Any]:
    """获取系统健康状态"""
    global _last_network_stats, _last_network_time
    
    try:
        # CPU使用率
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # 内存使用率
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        
        # 磁盘使用率
        disk = psutil.disk_usage('/')
        disk_percent = disk.percent
        
        # 网络状态 - 计算实时速度
        current_network = psutil.net_io_counters()
        current_time = time.time()
        
        network_sent_rate = 0.0  # KB/s
        network_recv_rate = 0.0  # KB/s
        
        if _last_network_stats and _last_network_time:
            time_diff = current_time - _last_network_time
            if time_diff > 0:
                # 计算速度 (字节/秒 -> KB/s)
                sent_diff = current_network.bytes_sent - _last_network_stats.bytes_sent
                recv_diff = current_network.bytes_recv - _last_network_stats.bytes_recv
                network_sent_rate = (sent_diff / time_diff) / 1024  # KB/s
                network_recv_rate = (recv_diff / time_diff) / 1024  # KB/s
        
        # 更新上次统计数据
        _last_network_stats = current_network
        _last_network_time = current_time
        
        return {
            "cpu_percent": round(cpu_percent, 2),
            "memory_percent": round(memory_percent, 2),
            "disk_percent": round(disk_percent, 2),
            "network_sent": round(network_sent_rate, 2),  # KB/s
            "network_recv": round(network_recv_rate, 2),  # KB/s
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