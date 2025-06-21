from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, date

from database import get_db
from models.system import (
    SystemConfig, SystemVersion, DataRetentionPolicy, MessageCenter,
    SystemLog, SystemMetrics, License, LogLevel
)
from models.user import User
from routers.auth import get_current_user

router = APIRouter()

# Pydantic models
class SystemConfigCreate(BaseModel):
    key: str
    value: str
    category: str
    description: Optional[str] = None
    is_public: bool = False
    data_type: str = "string"
    validation_rule: Optional[str] = None

class SystemConfigUpdate(BaseModel):
    value: Optional[str] = None
    description: Optional[str] = None
    is_public: Optional[bool] = None
    validation_rule: Optional[str] = None

class SystemConfigResponse(BaseModel):
    id: int
    key: str
    value: str
    category: str
    description: Optional[str]
    is_public: bool
    data_type: str
    validation_rule: Optional[str]
    created_at: datetime
    updated_at: datetime

class SystemVersionResponse(BaseModel):
    id: int
    version: str
    release_date: date
    description: Optional[str]
    changelog: Optional[str]
    is_current: bool
    download_url: Optional[str]
    file_size: Optional[int]
    checksum: Optional[str]
    created_at: datetime

class DataRetentionPolicyCreate(BaseModel):
    data_type: str
    retention_days: int
    description: Optional[str] = None
    is_active: bool = True

class DataRetentionPolicyUpdate(BaseModel):
    retention_days: Optional[int] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None

class DataRetentionPolicyResponse(BaseModel):
    id: int
    data_type: str
    retention_days: int
    description: Optional[str]
    is_active: bool
    last_cleanup: Optional[datetime]
    created_at: datetime
    updated_at: datetime

class MessageCenterCreate(BaseModel):
    title: str
    content: str
    message_type: str = "info"
    target_users: List[int] = []
    is_broadcast: bool = False
    expires_at: Optional[datetime] = None

class MessageCenterResponse(BaseModel):
    id: int
    title: str
    content: str
    message_type: str
    target_users: List[int]
    is_broadcast: bool
    is_published: bool
    read_count: int
    total_recipients: int
    expires_at: Optional[datetime]
    published_at: Optional[datetime]
    created_by: int
    created_by_name: str
    created_at: datetime
    updated_at: datetime

class SystemLogResponse(BaseModel):
    id: int
    level: LogLevel
    module: str
    action: str
    message: str
    user_id: Optional[int]
    user_name: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]
    request_id: Optional[str]
    extra_data: Dict[str, Any]
    created_at: datetime

class SystemMetricsResponse(BaseModel):
    id: int
    metric_name: str
    metric_value: float
    metric_unit: Optional[str]
    tags: Dict[str, str]
    timestamp: datetime
    created_at: datetime

class LicenseResponse(BaseModel):
    id: int
    license_key: str
    product_name: str
    license_type: str
    max_users: Optional[int]
    max_cameras: Optional[int]
    features: List[str]
    issued_to: str
    issued_by: str
    issued_at: datetime
    expires_at: Optional[datetime]
    is_active: bool
    hardware_fingerprint: Optional[str]
    created_at: datetime
    updated_at: datetime

class SystemStatsResponse(BaseModel):
    total_configs: int
    active_policies: int
    unread_messages: int
    system_logs_today: int
    error_logs_today: int
    warning_logs_today: int
    current_version: str
    license_status: str
    license_expires_in_days: Optional[int]
    disk_usage: Dict[str, Any]
    memory_usage: Dict[str, Any]
    cpu_usage: float

# 系统配置管理
@router.get("/configs/", response_model=List[SystemConfigResponse])
async def get_system_configs(
    category: Optional[str] = Query(None, description="配置分类筛选"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    is_public: Optional[bool] = Query(None, description="是否公开"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取系统配置列表"""
    conditions = []
    
    if category:
        conditions.append(SystemConfig.category == category)
    
    if search:
        search_pattern = f"%{search}%"
        conditions.append(
            or_(
                SystemConfig.key.ilike(search_pattern),
                SystemConfig.description.ilike(search_pattern)
            )
        )
    
    if is_public is not None:
        conditions.append(SystemConfig.is_public == is_public)
    
    query = select(SystemConfig).order_by(SystemConfig.category, SystemConfig.key)
    if conditions:
        query = query.where(and_(*conditions))
    
    result = await db.execute(query)
    configs = result.scalars().all()
    
    return [SystemConfigResponse(
        id=config.id,
        key=config.key,
        value=config.value,
        category=config.category,
        description=config.description,
        is_public=config.is_public,
        data_type=config.data_type,
        validation_rule=config.validation_rule,
        created_at=config.created_at,
        updated_at=config.updated_at
    ) for config in configs]

@router.post("/configs/", response_model=SystemConfigResponse)
async def create_system_config(
    config_data: SystemConfigCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建系统配置"""
    # 检查配置键是否已存在
    result = await db.execute(select(SystemConfig).where(SystemConfig.key == config_data.key))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="配置键已存在"
        )
    
    config = SystemConfig(**config_data.dict())
    db.add(config)
    await db.commit()
    await db.refresh(config)
    
    return SystemConfigResponse(
        id=config.id,
        key=config.key,
        value=config.value,
        category=config.category,
        description=config.description,
        is_public=config.is_public,
        data_type=config.data_type,
        validation_rule=config.validation_rule,
        created_at=config.created_at,
        updated_at=config.updated_at
    )

@router.get("/configs/{config_id}", response_model=SystemConfigResponse)
async def get_system_config(
    config_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取系统配置详情"""
    result = await db.execute(select(SystemConfig).where(SystemConfig.id == config_id))
    config = result.scalar_one_or_none()
    
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="配置不存在"
        )
    
    return SystemConfigResponse(
        id=config.id,
        key=config.key,
        value=config.value,
        category=config.category,
        description=config.description,
        is_public=config.is_public,
        data_type=config.data_type,
        validation_rule=config.validation_rule,
        created_at=config.created_at,
        updated_at=config.updated_at
    )

@router.put("/configs/{config_id}", response_model=SystemConfigResponse)
async def update_system_config(
    config_id: int,
    config_data: SystemConfigUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新系统配置"""
    result = await db.execute(select(SystemConfig).where(SystemConfig.id == config_id))
    config = result.scalar_one_or_none()
    
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="配置不存在"
        )
    
    update_data = config_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(config, field, value)
    
    await db.commit()
    await db.refresh(config)
    
    return SystemConfigResponse(
        id=config.id,
        key=config.key,
        value=config.value,
        category=config.category,
        description=config.description,
        is_public=config.is_public,
        data_type=config.data_type,
        validation_rule=config.validation_rule,
        created_at=config.created_at,
        updated_at=config.updated_at
    )

@router.delete("/configs/{config_id}")
async def delete_system_config(
    config_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除系统配置"""
    result = await db.execute(select(SystemConfig).where(SystemConfig.id == config_id))
    config = result.scalar_one_or_none()
    
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="配置不存在"
        )
    
    await db.delete(config)
    await db.commit()
    
    return {"message": "配置删除成功"}

# 系统版本管理
@router.get("/versions/", response_model=List[SystemVersionResponse])
async def get_system_versions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取系统版本列表"""
    result = await db.execute(select(SystemVersion).order_by(desc(SystemVersion.release_date)))
    versions = result.scalars().all()
    
    return [SystemVersionResponse(
        id=version.id,
        version=version.version,
        release_date=version.release_date,
        description=version.description,
        changelog=version.changelog,
        is_current=version.is_current,
        download_url=version.download_url,
        file_size=version.file_size,
        checksum=version.checksum,
        created_at=version.created_at
    ) for version in versions]

@router.get("/versions/current", response_model=SystemVersionResponse)
async def get_current_version(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取当前系统版本"""
    result = await db.execute(select(SystemVersion).where(SystemVersion.is_current == True))
    version = result.scalar_one_or_none()
    
    if not version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="未找到当前版本信息"
        )
    
    return SystemVersionResponse(
        id=version.id,
        version=version.version,
        release_date=version.release_date,
        description=version.description,
        changelog=version.changelog,
        is_current=version.is_current,
        download_url=version.download_url,
        file_size=version.file_size,
        checksum=version.checksum,
        created_at=version.created_at
    )

# 数据保留策略管理
@router.get("/retention-policies/", response_model=List[DataRetentionPolicyResponse])
async def get_retention_policies(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取数据保留策略列表"""
    result = await db.execute(select(DataRetentionPolicy).order_by(DataRetentionPolicy.data_type))
    policies = result.scalars().all()
    
    return [DataRetentionPolicyResponse(
        id=policy.id,
        data_type=policy.data_type,
        retention_days=policy.retention_days,
        description=policy.description,
        is_active=policy.is_active,
        last_cleanup=policy.last_cleanup,
        created_at=policy.created_at,
        updated_at=policy.updated_at
    ) for policy in policies]

@router.post("/retention-policies/", response_model=DataRetentionPolicyResponse)
async def create_retention_policy(
    policy_data: DataRetentionPolicyCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建数据保留策略"""
    # 检查数据类型是否已存在策略
    result = await db.execute(select(DataRetentionPolicy).where(DataRetentionPolicy.data_type == policy_data.data_type))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该数据类型的保留策略已存在"
        )
    
    policy = DataRetentionPolicy(**policy_data.dict())
    db.add(policy)
    await db.commit()
    await db.refresh(policy)
    
    return DataRetentionPolicyResponse(
        id=policy.id,
        data_type=policy.data_type,
        retention_days=policy.retention_days,
        description=policy.description,
        is_active=policy.is_active,
        last_cleanup=policy.last_cleanup,
        created_at=policy.created_at,
        updated_at=policy.updated_at
    )

# 消息中心管理
@router.get("/messages/", response_model=List[MessageCenterResponse])
async def get_system_messages(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    message_type: Optional[str] = Query(None, description="消息类型筛选"),
    is_broadcast: Optional[bool] = Query(None, description="是否广播"),
    is_published: Optional[bool] = Query(None, description="是否已发布"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取系统消息列表"""
    conditions = []
    
    if message_type:
        conditions.append(MessageCenter.message_type == message_type)
    
    if is_broadcast is not None:
        conditions.append(MessageCenter.is_broadcast == is_broadcast)
    
    if is_published is not None:
        conditions.append(MessageCenter.is_published == is_published)
    
    query = select(MessageCenter).order_by(desc(MessageCenter.created_at))
    if conditions:
        query = query.where(and_(*conditions))
    
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    
    result = await db.execute(query)
    messages = result.scalars().all()
    
    # 获取创建者信息
    creator_map = {}
    if messages:
        creator_ids = [m.created_by for m in messages]
        creator_result = await db.execute(select(User).where(User.id.in_(creator_ids)))
        creators = creator_result.scalars().all()
        creator_map = {c.id: c.username for c in creators}
    
    return [MessageCenterResponse(
        id=message.id,
        title=message.title,
        content=message.content,
        message_type=message.message_type,
        target_users=message.target_users,
        is_broadcast=message.is_broadcast,
        is_published=message.is_published,
        read_count=message.read_count,
        total_recipients=message.total_recipients,
        expires_at=message.expires_at,
        published_at=message.published_at,
        created_by=message.created_by,
        created_by_name=creator_map.get(message.created_by, ""),
        created_at=message.created_at,
        updated_at=message.updated_at
    ) for message in messages]

@router.post("/messages/", response_model=MessageCenterResponse)
async def create_system_message(
    message_data: MessageCenterCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建系统消息"""
    # 验证目标用户是否存在
    if message_data.target_users and not message_data.is_broadcast:
        user_result = await db.execute(select(User.id).where(User.id.in_(message_data.target_users)))
        existing_ids = [row[0] for row in user_result.all()]
        invalid_ids = set(message_data.target_users) - set(existing_ids)
        if invalid_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"以下用户ID不存在: {list(invalid_ids)}"
            )
    
    message_dict = message_data.dict()
    message_dict['created_by'] = current_user.id
    
    # 如果是广播消息，计算总接收人数
    if message_data.is_broadcast:
        total_users_result = await db.execute(select(func.count(User.id)).where(User.is_active == True))
        message_dict['total_recipients'] = total_users_result.scalar()
    else:
        message_dict['total_recipients'] = len(message_data.target_users)
    
    message = MessageCenter(**message_dict)
    db.add(message)
    await db.commit()
    await db.refresh(message)
    
    return MessageCenterResponse(
        id=message.id,
        title=message.title,
        content=message.content,
        message_type=message.message_type,
        target_users=message.target_users,
        is_broadcast=message.is_broadcast,
        is_published=message.is_published,
        read_count=message.read_count,
        total_recipients=message.total_recipients,
        expires_at=message.expires_at,
        published_at=message.published_at,
        created_by=message.created_by,
        created_by_name=current_user.username,
        created_at=message.created_at,
        updated_at=message.updated_at
    )

# 系统日志管理
@router.get("/logs/", response_model=List[SystemLogResponse])
async def get_system_logs(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(50, ge=1, le=200, description="每页数量"),
    level: Optional[LogLevel] = Query(None, description="日志级别筛选"),
    module: Optional[str] = Query(None, description="模块筛选"),
    user_id: Optional[int] = Query(None, description="用户ID筛选"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取系统日志列表"""
    conditions = []
    
    if level:
        conditions.append(SystemLog.level == level)
    
    if module:
        conditions.append(SystemLog.module == module)
    
    if user_id:
        conditions.append(SystemLog.user_id == user_id)
    
    if start_date:
        conditions.append(SystemLog.created_at >= start_date)
    
    if end_date:
        end_datetime = datetime.combine(end_date, datetime.max.time())
        conditions.append(SystemLog.created_at <= end_datetime)
    
    if search:
        search_pattern = f"%{search}%"
        conditions.append(
            or_(
                SystemLog.action.ilike(search_pattern),
                SystemLog.message.ilike(search_pattern)
            )
        )
    
    query = select(SystemLog).order_by(desc(SystemLog.created_at))
    if conditions:
        query = query.where(and_(*conditions))
    
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    
    result = await db.execute(query)
    logs = result.scalars().all()
    
    # 获取用户信息
    user_map = {}
    if logs:
        user_ids = [log.user_id for log in logs if log.user_id]
        if user_ids:
            user_result = await db.execute(select(User).where(User.id.in_(user_ids)))
            users = user_result.scalars().all()
            user_map = {u.id: u.username for u in users}
    
    return [SystemLogResponse(
        id=log.id,
        level=log.level,
        module=log.module,
        action=log.action,
        message=log.message,
        user_id=log.user_id,
        user_name=user_map.get(log.user_id),
        ip_address=log.ip_address,
        user_agent=log.user_agent,
        request_id=log.request_id,
        extra_data=log.extra_data,
        created_at=log.created_at
    ) for log in logs]

# 系统指标管理
@router.get("/metrics/", response_model=List[SystemMetricsResponse])
async def get_system_metrics(
    metric_name: Optional[str] = Query(None, description="指标名称筛选"),
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    limit: int = Query(100, ge=1, le=1000, description="返回数量限制"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取系统指标数据"""
    conditions = []
    
    if metric_name:
        conditions.append(SystemMetrics.metric_name == metric_name)
    
    if start_time:
        conditions.append(SystemMetrics.timestamp >= start_time)
    
    if end_time:
        conditions.append(SystemMetrics.timestamp <= end_time)
    
    query = select(SystemMetrics).order_by(desc(SystemMetrics.timestamp))
    if conditions:
        query = query.where(and_(*conditions))
    
    query = query.limit(limit)
    
    result = await db.execute(query)
    metrics = result.scalars().all()
    
    return [SystemMetricsResponse(
        id=metric.id,
        metric_name=metric.metric_name,
        metric_value=metric.metric_value,
        metric_unit=metric.metric_unit,
        tags=metric.tags,
        timestamp=metric.timestamp,
        created_at=metric.created_at
    ) for metric in metrics]

# 许可证管理
@router.get("/license/", response_model=LicenseResponse)
async def get_license_info(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取许可证信息"""
    result = await db.execute(select(License).where(License.is_active == True).order_by(desc(License.created_at)))
    license_info = result.scalar_one_or_none()
    
    if not license_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="未找到有效的许可证"
        )
    
    return LicenseResponse(
        id=license_info.id,
        license_key=license_info.license_key,
        product_name=license_info.product_name,
        license_type=license_info.license_type,
        max_users=license_info.max_users,
        max_cameras=license_info.max_cameras,
        features=license_info.features,
        issued_to=license_info.issued_to,
        issued_by=license_info.issued_by,
        issued_at=license_info.issued_at,
        expires_at=license_info.expires_at,
        is_active=license_info.is_active,
        hardware_fingerprint=license_info.hardware_fingerprint,
        created_at=license_info.created_at,
        updated_at=license_info.updated_at
    )

# 系统统计
@router.get("/stats/overview", response_model=SystemStatsResponse)
async def get_system_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取系统统计信息"""
    import psutil
    from datetime import timedelta
    
    # 配置统计
    total_configs_result = await db.execute(select(func.count(SystemConfig.id)))
    total_configs = total_configs_result.scalar()
    
    # 活跃策略统计
    active_policies_result = await db.execute(select(func.count(DataRetentionPolicy.id)).where(DataRetentionPolicy.is_active == True))
    active_policies = active_policies_result.scalar()
    
    # 未读消息统计
    unread_messages_result = await db.execute(
        select(func.count(MessageCenter.id))
        .where(
            and_(
                MessageCenter.is_published == True,
                MessageCenter.read_count < MessageCenter.total_recipients
            )
        )
    )
    unread_messages = unread_messages_result.scalar()
    
    # 今日日志统计
    today = date.today()
    today_logs_result = await db.execute(
        select(func.count(SystemLog.id))
        .where(func.date(SystemLog.created_at) == today)
    )
    system_logs_today = today_logs_result.scalar()
    
    error_logs_result = await db.execute(
        select(func.count(SystemLog.id))
        .where(
            and_(
                func.date(SystemLog.created_at) == today,
                SystemLog.level == LogLevel.ERROR
            )
        )
    )
    error_logs_today = error_logs_result.scalar()
    
    warning_logs_result = await db.execute(
        select(func.count(SystemLog.id))
        .where(
            and_(
                func.date(SystemLog.created_at) == today,
                SystemLog.level == LogLevel.WARNING
            )
        )
    )
    warning_logs_today = warning_logs_result.scalar()
    
    # 当前版本
    version_result = await db.execute(select(SystemVersion).where(SystemVersion.is_current == True))
    current_version_obj = version_result.scalar_one_or_none()
    current_version = current_version_obj.version if current_version_obj else "未知"
    
    # 许可证状态
    license_result = await db.execute(select(License).where(License.is_active == True).order_by(desc(License.created_at)))
    license_info = license_result.scalar_one_or_none()
    
    license_status = "无效"
    license_expires_in_days = None
    
    if license_info:
        if license_info.expires_at:
            expires_in = (license_info.expires_at.date() - today).days
            license_expires_in_days = expires_in
            if expires_in > 30:
                license_status = "正常"
            elif expires_in > 0:
                license_status = "即将过期"
            else:
                license_status = "已过期"
        else:
            license_status = "永久"
    
    # 系统资源使用情况
    disk_usage = {
        "total": psutil.disk_usage('/').total,
        "used": psutil.disk_usage('/').used,
        "free": psutil.disk_usage('/').free,
        "percent": psutil.disk_usage('/').percent
    }
    
    memory_info = psutil.virtual_memory()
    memory_usage = {
        "total": memory_info.total,
        "used": memory_info.used,
        "available": memory_info.available,
        "percent": memory_info.percent
    }
    
    cpu_usage = psutil.cpu_percent(interval=1)
    
    return SystemStatsResponse(
        total_configs=total_configs,
        active_policies=active_policies,
        unread_messages=unread_messages,
        system_logs_today=system_logs_today,
        error_logs_today=error_logs_today,
        warning_logs_today=warning_logs_today,
        current_version=current_version,
        license_status=license_status,
        license_expires_in_days=license_expires_in_days,
        disk_usage=disk_usage,
        memory_usage=memory_usage,
        cpu_usage=cpu_usage
    )