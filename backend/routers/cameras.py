from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

from database import get_db
from models.camera import Camera, CameraGroup, MediaProxy, CameraPreset, CameraStatus, CameraType
from models.user import User
from routers.auth import get_current_user

router = APIRouter()

# Pydantic models
class CameraCreate(BaseModel):
    code: str
    name: str
    stream_url: str
    backup_stream_url: Optional[str] = None
    camera_type: CameraType = CameraType.IP_CAMERA
    media_proxy_id: Optional[int] = None
    location: Optional[str] = None
    longitude: Optional[float] = None
    latitude: Optional[float] = None
    altitude: Optional[float] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    firmware_version: Optional[str] = None
    ip_address: Optional[str] = None
    port: Optional[int] = None
    username: Optional[str] = None
    password: Optional[str] = None
    resolution: Optional[str] = None
    frame_rate: Optional[int] = None
    bitrate: Optional[int] = None
    custom_attributes: Dict[str, Any] = {}
    alarm_enabled: bool = True
    alarm_config: Dict[str, Any] = {}
    description: Optional[str] = None

class CameraUpdate(BaseModel):
    name: Optional[str] = None
    stream_url: Optional[str] = None
    backup_stream_url: Optional[str] = None
    camera_type: Optional[CameraType] = None
    media_proxy_id: Optional[int] = None
    location: Optional[str] = None
    longitude: Optional[float] = None
    latitude: Optional[float] = None
    altitude: Optional[float] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    firmware_version: Optional[str] = None
    ip_address: Optional[str] = None
    port: Optional[int] = None
    username: Optional[str] = None
    password: Optional[str] = None
    resolution: Optional[str] = None
    frame_rate: Optional[int] = None
    bitrate: Optional[int] = None
    status: Optional[CameraStatus] = None
    is_active: Optional[bool] = None
    is_recording: Optional[bool] = None
    custom_attributes: Optional[Dict[str, Any]] = None
    alarm_enabled: Optional[bool] = None
    alarm_config: Optional[Dict[str, Any]] = None
    description: Optional[str] = None

class CameraResponse(BaseModel):
    id: int
    code: str
    name: str
    stream_url: str
    backup_stream_url: Optional[str]
    camera_type: CameraType
    media_proxy_id: Optional[int]
    media_proxy_name: Optional[str]
    location: Optional[str]
    longitude: Optional[float]
    latitude: Optional[float]
    altitude: Optional[float]
    manufacturer: Optional[str]
    model: Optional[str]
    firmware_version: Optional[str]
    ip_address: Optional[str]
    port: Optional[int]
    resolution: Optional[str]
    frame_rate: Optional[int]
    bitrate: Optional[int]
    status: CameraStatus
    is_active: bool
    is_recording: bool
    custom_attributes: Dict[str, Any]
    alarm_enabled: bool
    alarm_config: Dict[str, Any]
    last_heartbeat: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    description: Optional[str]

class CameraListResponse(BaseModel):
    cameras: List[CameraResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

class MediaProxyCreate(BaseModel):
    name: str
    ip_address: str
    port: int
    secret_key: Optional[str] = None
    max_connections: int = 100
    description: Optional[str] = None

class MediaProxyUpdate(BaseModel):
    name: Optional[str] = None
    ip_address: Optional[str] = None
    port: Optional[int] = None
    secret_key: Optional[str] = None
    max_connections: Optional[int] = None
    is_online: Optional[bool] = None
    description: Optional[str] = None

class MediaProxyResponse(BaseModel):
    id: int
    name: str
    ip_address: str
    port: int
    is_online: bool
    cpu_usage: Optional[float]
    memory_usage: Optional[float]
    bandwidth_usage: Optional[float]
    max_connections: int
    current_connections: Optional[int]
    last_heartbeat: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    description: Optional[str]

class CameraGroupCreate(BaseModel):
    name: str
    description: Optional[str] = None
    camera_ids: List[int] = []

class CameraGroupUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    camera_ids: Optional[List[int]] = None

class CameraGroupResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    camera_ids: List[int]
    camera_count: int
    created_at: datetime
    updated_at: datetime

class CameraStats(BaseModel):
    total_cameras: int
    online_cameras: int
    offline_cameras: int
    recording_cameras: int
    alarm_enabled_cameras: int
    by_type: Dict[str, int]
    by_status: Dict[str, int]

@router.get("/", response_model=CameraListResponse)
async def get_cameras(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    status: Optional[CameraStatus] = Query(None, description="状态筛选"),
    camera_type: Optional[CameraType] = Query(None, description="类型筛选"),
    is_active: Optional[bool] = Query(None, description="是否启用"),
    location: Optional[str] = Query(None, description="位置筛选"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取摄像头列表"""
    # 构建查询条件
    conditions = []
    
    if search:
        search_pattern = f"%{search}%"
        conditions.append(
            or_(
                Camera.code.ilike(search_pattern),
                Camera.name.ilike(search_pattern),
                Camera.location.ilike(search_pattern),
                Camera.ip_address.ilike(search_pattern)
            )
        )
    
    if status:
        conditions.append(Camera.status == status)
    
    if camera_type:
        conditions.append(Camera.camera_type == camera_type)
    
    if is_active is not None:
        conditions.append(Camera.is_active == is_active)
    
    if location:
        conditions.append(Camera.location.ilike(f"%{location}%"))
    
    # 计算总数
    count_query = select(func.count(Camera.id))
    if conditions:
        count_query = count_query.where(and_(*conditions))
    
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # 查询摄像头列表
    query = select(Camera).order_by(Camera.created_at.desc())
    if conditions:
        query = query.where(and_(*conditions))
    
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    
    result = await db.execute(query)
    cameras = result.scalars().all()
    
    # 获取媒体代理信息
    media_proxy_map = {}
    if cameras:
        proxy_ids = [c.media_proxy_id for c in cameras if c.media_proxy_id]
        if proxy_ids:
            proxy_result = await db.execute(select(MediaProxy).where(MediaProxy.id.in_(proxy_ids)))
            proxies = proxy_result.scalars().all()
            media_proxy_map = {p.id: p.name for p in proxies}
    
    total_pages = (total + page_size - 1) // page_size
    
    return CameraListResponse(
        cameras=[CameraResponse(
            id=camera.id,
            code=camera.code,
            name=camera.name,
            stream_url=camera.stream_url,
            backup_stream_url=camera.backup_stream_url,
            camera_type=camera.camera_type,
            media_proxy_id=camera.media_proxy_id,
            media_proxy_name=media_proxy_map.get(camera.media_proxy_id),
            location=camera.location,
            longitude=camera.longitude,
            latitude=camera.latitude,
            altitude=camera.altitude,
            manufacturer=camera.manufacturer,
            model=camera.model,
            firmware_version=camera.firmware_version,
            ip_address=camera.ip_address,
            port=camera.port,
            resolution=camera.resolution,
            frame_rate=camera.frame_rate,
            bitrate=camera.bitrate,
            status=camera.status,
            is_active=camera.is_active,
            is_recording=camera.is_recording,
            custom_attributes=camera.custom_attributes,
            alarm_enabled=camera.alarm_enabled,
            alarm_config=camera.alarm_config,
            last_heartbeat=camera.last_heartbeat,
            created_at=camera.created_at,
            updated_at=camera.updated_at,
            description=camera.description
        ) for camera in cameras],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )

@router.post("/", response_model=CameraResponse)
async def create_camera(
    camera_data: CameraCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建摄像头"""
    # 检查编码是否已存在
    result = await db.execute(select(Camera).where(Camera.code == camera_data.code))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="摄像头编码已存在"
        )
    
    # 验证媒体代理是否存在
    if camera_data.media_proxy_id:
        proxy_result = await db.execute(select(MediaProxy).where(MediaProxy.id == camera_data.media_proxy_id))
        if not proxy_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="指定的媒体代理不存在"
            )
    
    # 创建摄像头
    camera = Camera(**camera_data.dict())
    db.add(camera)
    await db.commit()
    await db.refresh(camera)
    
    # 获取媒体代理名称
    media_proxy_name = None
    if camera.media_proxy_id:
        proxy_result = await db.execute(select(MediaProxy).where(MediaProxy.id == camera.media_proxy_id))
        proxy = proxy_result.scalar_one_or_none()
        if proxy:
            media_proxy_name = proxy.name
    
    return CameraResponse(
        id=camera.id,
        code=camera.code,
        name=camera.name,
        stream_url=camera.stream_url,
        backup_stream_url=camera.backup_stream_url,
        camera_type=camera.camera_type,
        media_proxy_id=camera.media_proxy_id,
        media_proxy_name=media_proxy_name,
        location=camera.location,
        longitude=camera.longitude,
        latitude=camera.latitude,
        altitude=camera.altitude,
        manufacturer=camera.manufacturer,
        model=camera.model,
        firmware_version=camera.firmware_version,
        ip_address=camera.ip_address,
        port=camera.port,
        resolution=camera.resolution,
        frame_rate=camera.frame_rate,
        bitrate=camera.bitrate,
        status=camera.status,
        is_active=camera.is_active,
        is_recording=camera.is_recording,
        custom_attributes=camera.custom_attributes,
        alarm_enabled=camera.alarm_enabled,
        alarm_config=camera.alarm_config,
        last_heartbeat=camera.last_heartbeat,
        created_at=camera.created_at,
        updated_at=camera.updated_at,
        description=camera.description
    )

@router.get("/{camera_id}", response_model=CameraResponse)
async def get_camera(
    camera_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取摄像头详情"""
    result = await db.execute(select(Camera).where(Camera.id == camera_id))
    camera = result.scalar_one_or_none()
    
    if not camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="摄像头不存在"
        )
    
    # 获取媒体代理名称
    media_proxy_name = None
    if camera.media_proxy_id:
        proxy_result = await db.execute(select(MediaProxy).where(MediaProxy.id == camera.media_proxy_id))
        proxy = proxy_result.scalar_one_or_none()
        if proxy:
            media_proxy_name = proxy.name
    
    return CameraResponse(
        id=camera.id,
        code=camera.code,
        name=camera.name,
        stream_url=camera.stream_url,
        backup_stream_url=camera.backup_stream_url,
        camera_type=camera.camera_type,
        media_proxy_id=camera.media_proxy_id,
        media_proxy_name=media_proxy_name,
        location=camera.location,
        longitude=camera.longitude,
        latitude=camera.latitude,
        altitude=camera.altitude,
        manufacturer=camera.manufacturer,
        model=camera.model,
        firmware_version=camera.firmware_version,
        ip_address=camera.ip_address,
        port=camera.port,
        resolution=camera.resolution,
        frame_rate=camera.frame_rate,
        bitrate=camera.bitrate,
        status=camera.status,
        is_active=camera.is_active,
        is_recording=camera.is_recording,
        custom_attributes=camera.custom_attributes,
        alarm_enabled=camera.alarm_enabled,
        alarm_config=camera.alarm_config,
        last_heartbeat=camera.last_heartbeat,
        created_at=camera.created_at,
        updated_at=camera.updated_at,
        description=camera.description
    )

@router.put("/{camera_id}", response_model=CameraResponse)
async def update_camera(
    camera_id: int,
    camera_data: CameraUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新摄像头信息"""
    result = await db.execute(select(Camera).where(Camera.id == camera_id))
    camera = result.scalar_one_or_none()
    
    if not camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="摄像头不存在"
        )
    
    # 验证媒体代理是否存在
    if camera_data.media_proxy_id:
        proxy_result = await db.execute(select(MediaProxy).where(MediaProxy.id == camera_data.media_proxy_id))
        if not proxy_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="指定的媒体代理不存在"
            )
    
    # 更新摄像头信息
    update_data = camera_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(camera, field, value)
    
    await db.commit()
    await db.refresh(camera)
    
    # 获取媒体代理名称
    media_proxy_name = None
    if camera.media_proxy_id:
        proxy_result = await db.execute(select(MediaProxy).where(MediaProxy.id == camera.media_proxy_id))
        proxy = proxy_result.scalar_one_or_none()
        if proxy:
            media_proxy_name = proxy.name
    
    return CameraResponse(
        id=camera.id,
        code=camera.code,
        name=camera.name,
        stream_url=camera.stream_url,
        backup_stream_url=camera.backup_stream_url,
        camera_type=camera.camera_type,
        media_proxy_id=camera.media_proxy_id,
        media_proxy_name=media_proxy_name,
        location=camera.location,
        longitude=camera.longitude,
        latitude=camera.latitude,
        altitude=camera.altitude,
        manufacturer=camera.manufacturer,
        model=camera.model,
        firmware_version=camera.firmware_version,
        ip_address=camera.ip_address,
        port=camera.port,
        resolution=camera.resolution,
        frame_rate=camera.frame_rate,
        bitrate=camera.bitrate,
        status=camera.status,
        is_active=camera.is_active,
        is_recording=camera.is_recording,
        custom_attributes=camera.custom_attributes,
        alarm_enabled=camera.alarm_enabled,
        alarm_config=camera.alarm_config,
        last_heartbeat=camera.last_heartbeat,
        created_at=camera.created_at,
        updated_at=camera.updated_at,
        description=camera.description
    )

@router.delete("/{camera_id}")
async def delete_camera(
    camera_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除摄像头"""
    result = await db.execute(select(Camera).where(Camera.id == camera_id))
    camera = result.scalar_one_or_none()
    
    if not camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="摄像头不存在"
        )
    
    await db.delete(camera)
    await db.commit()
    
    return {"message": "摄像头删除成功"}

@router.get("/stats/overview", response_model=CameraStats)
async def get_camera_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取摄像头统计信息"""
    # 总摄像头数
    total_result = await db.execute(select(func.count(Camera.id)))
    total_cameras = total_result.scalar()
    
    # 在线摄像头数
    online_result = await db.execute(select(func.count(Camera.id)).where(Camera.status == CameraStatus.ONLINE))
    online_cameras = online_result.scalar()
    
    # 离线摄像头数
    offline_result = await db.execute(select(func.count(Camera.id)).where(Camera.status == CameraStatus.OFFLINE))
    offline_cameras = offline_result.scalar()
    
    # 录像摄像头数
    recording_result = await db.execute(select(func.count(Camera.id)).where(Camera.is_recording == True))
    recording_cameras = recording_result.scalar()
    
    # 启用告警的摄像头数
    alarm_result = await db.execute(select(func.count(Camera.id)).where(Camera.alarm_enabled == True))
    alarm_enabled_cameras = alarm_result.scalar()
    
    # 按类型统计
    type_result = await db.execute(
        select(Camera.camera_type, func.count(Camera.id))
        .group_by(Camera.camera_type)
    )
    by_type = {str(row[0].value): row[1] for row in type_result.all()}
    
    # 按状态统计
    status_result = await db.execute(
        select(Camera.status, func.count(Camera.id))
        .group_by(Camera.status)
    )
    by_status = {str(row[0].value): row[1] for row in status_result.all()}
    
    return CameraStats(
        total_cameras=total_cameras,
        online_cameras=online_cameras,
        offline_cameras=offline_cameras,
        recording_cameras=recording_cameras,
        alarm_enabled_cameras=alarm_enabled_cameras,
        by_type=by_type,
        by_status=by_status
    )

# 媒体代理管理
@router.get("/media-proxies/", response_model=List[MediaProxyResponse])
async def get_media_proxies(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取媒体代理列表"""
    result = await db.execute(select(MediaProxy).order_by(MediaProxy.created_at.desc()))
    proxies = result.scalars().all()
    
    return [MediaProxyResponse(
        id=proxy.id,
        name=proxy.name,
        ip_address=proxy.ip_address,
        port=proxy.port,
        is_online=proxy.is_online,
        cpu_usage=proxy.cpu_usage,
        memory_usage=proxy.memory_usage,
        bandwidth_usage=proxy.bandwidth_usage,
        max_connections=proxy.max_connections,
        current_connections=proxy.current_connections,
        last_heartbeat=proxy.last_heartbeat,
        created_at=proxy.created_at,
        updated_at=proxy.updated_at,
        description=proxy.description
    ) for proxy in proxies]

@router.post("/media-proxies/", response_model=MediaProxyResponse)
async def create_media_proxy(
    proxy_data: MediaProxyCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建媒体代理"""
    # 检查IP和端口是否已存在
    result = await db.execute(
        select(MediaProxy).where(
            and_(
                MediaProxy.ip_address == proxy_data.ip_address,
                MediaProxy.port == proxy_data.port
            )
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该IP和端口的媒体代理已存在"
        )
    
    proxy = MediaProxy(**proxy_data.dict())
    db.add(proxy)
    await db.commit()
    await db.refresh(proxy)
    
    return MediaProxyResponse(
        id=proxy.id,
        name=proxy.name,
        ip_address=proxy.ip_address,
        port=proxy.port,
        is_online=proxy.is_online,
        cpu_usage=proxy.cpu_usage,
        memory_usage=proxy.memory_usage,
        bandwidth_usage=proxy.bandwidth_usage,
        max_connections=proxy.max_connections,
        current_connections=proxy.current_connections,
        last_heartbeat=proxy.last_heartbeat,
        created_at=proxy.created_at,
        updated_at=proxy.updated_at,
        description=proxy.description
    )

# 摄像头分组管理
@router.get("/groups/", response_model=List[CameraGroupResponse])
async def get_camera_groups(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取摄像头分组列表"""
    result = await db.execute(select(CameraGroup).order_by(CameraGroup.created_at.desc()))
    groups = result.scalars().all()
    
    return [CameraGroupResponse(
        id=group.id,
        name=group.name,
        description=group.description,
        camera_ids=group.camera_ids,
        camera_count=len(group.camera_ids),
        created_at=group.created_at,
        updated_at=group.updated_at
    ) for group in groups]

@router.post("/groups/", response_model=CameraGroupResponse)
async def create_camera_group(
    group_data: CameraGroupCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建摄像头分组"""
    # 验证摄像头ID是否存在
    if group_data.camera_ids:
        camera_result = await db.execute(select(Camera.id).where(Camera.id.in_(group_data.camera_ids)))
        existing_ids = [row[0] for row in camera_result.all()]
        invalid_ids = set(group_data.camera_ids) - set(existing_ids)
        if invalid_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"以下摄像头ID不存在: {list(invalid_ids)}"
            )
    
    group = CameraGroup(**group_data.dict())
    db.add(group)
    await db.commit()
    await db.refresh(group)
    
    return CameraGroupResponse(
        id=group.id,
        name=group.name,
        description=group.description,
        camera_ids=group.camera_ids,
        camera_count=len(group.camera_ids),
        created_at=group.created_at,
        updated_at=group.updated_at
    )

@router.put("/groups/{group_id}", response_model=CameraGroupResponse)
async def update_camera_group(
    group_id: int,
    group_data: CameraGroupUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新摄像头分组"""
    # 查找分组
    result = await db.execute(select(CameraGroup).where(CameraGroup.id == group_id))
    group = result.scalar_one_or_none()
    
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="分组不存在"
        )
    
    # 验证摄像头ID是否存在
    if group_data.camera_ids is not None:
        camera_result = await db.execute(select(Camera.id).where(Camera.id.in_(group_data.camera_ids)))
        existing_ids = [row[0] for row in camera_result.all()]
        invalid_ids = set(group_data.camera_ids) - set(existing_ids)
        if invalid_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"以下摄像头ID不存在: {list(invalid_ids)}"
            )
    
    # 更新分组信息
    update_data = group_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(group, field, value)
    
    await db.commit()
    await db.refresh(group)
    
    return CameraGroupResponse(
        id=group.id,
        name=group.name,
        description=group.description,
        camera_ids=group.camera_ids,
        camera_count=len(group.camera_ids),
        created_at=group.created_at,
        updated_at=group.updated_at
    )

@router.delete("/groups/{group_id}")
async def delete_camera_group(
    group_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除摄像头分组"""
    # 查找分组
    result = await db.execute(select(CameraGroup).where(CameraGroup.id == group_id))
    group = result.scalar_one_or_none()
    
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="分组不存在"
        )
    
    await db.delete(group)
    await db.commit()
    
    return {"message": "分组删除成功"}

@router.get("/groups/{group_id}/cameras", response_model=CameraListResponse)
async def get_group_cameras(
    group_id: int,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取分组下的摄像头列表"""
    # 查找分组
    result = await db.execute(select(CameraGroup).where(CameraGroup.id == group_id))
    group = result.scalar_one_or_none()
    
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="分组不存在"
        )
    
    if not group.camera_ids:
        return CameraListResponse(
            cameras=[],
            total=0,
            page=page,
            page_size=page_size,
            total_pages=0
        )
    
    # 计算分页
    offset = (page - 1) * page_size
    
    # 查询分组下的摄像头
    query = select(Camera).where(Camera.id.in_(group.camera_ids))
    
    # 获取总数
    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = count_result.scalar()
    
    # 获取分页数据
    result = await db.execute(query.offset(offset).limit(page_size))
    cameras = result.scalars().all()
    
    # 获取媒体代理信息
    media_proxy_ids = [camera.media_proxy_id for camera in cameras if camera.media_proxy_id]
    media_proxies = {}
    if media_proxy_ids:
        proxy_result = await db.execute(select(MediaProxy).where(MediaProxy.id.in_(media_proxy_ids)))
        for proxy in proxy_result.scalars().all():
            media_proxies[proxy.id] = proxy.name
    
    camera_responses = []
    for camera in cameras:
        camera_responses.append(CameraResponse(
            id=camera.id,
            code=camera.code,
            name=camera.name,
            stream_url=camera.stream_url,
            backup_stream_url=camera.backup_stream_url,
            camera_type=camera.camera_type,
            media_proxy_id=camera.media_proxy_id,
            media_proxy_name=media_proxies.get(camera.media_proxy_id),
            location=camera.location,
            longitude=camera.longitude,
            latitude=camera.latitude,
            altitude=camera.altitude,
            manufacturer=camera.manufacturer,
            model=camera.model,
            firmware_version=camera.firmware_version,
            ip_address=camera.ip_address,
            port=camera.port,
            resolution=camera.resolution,
            frame_rate=camera.frame_rate,
            bitrate=camera.bitrate,
            status=camera.status,
            is_active=camera.is_active,
            is_recording=camera.is_recording,
            custom_attributes=camera.custom_attributes,
            alarm_enabled=camera.alarm_enabled,
            alarm_config=camera.alarm_config,
            last_heartbeat=camera.last_heartbeat,
            created_at=camera.created_at,
            updated_at=camera.updated_at,
            description=camera.description
        ))
    
    total_pages = (total + page_size - 1) // page_size
    
    return CameraListResponse(
        cameras=camera_responses,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )