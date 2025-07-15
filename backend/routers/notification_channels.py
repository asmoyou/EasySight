from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, desc
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from pydantic import BaseModel, Field, validator
import json

from database import get_db
from models.diagnosis import NotificationChannel, NotificationLog
from models.user import User
from routers.auth import get_current_user

router = APIRouter(prefix="/api/v1/notification-channels", tags=["通知渠道"])

# Pydantic 模型
class NotificationChannelCreate(BaseModel):
    name: str = Field(..., description="渠道名称")
    type: str = Field(..., description="渠道类型")
    description: Optional[str] = Field(None, description="渠道描述")
    config: Dict[str, Any] = Field(default={}, description="渠道配置")
    is_enabled: bool = Field(default=True, description="是否启用")
    
    @validator('type')
    def validate_type(cls, v):
        allowed_types = ['email', 'sms', 'webhook', 'dingtalk', 'wechat']
        if v not in allowed_types:
            raise ValueError(f'渠道类型必须是: {", ".join(allowed_types)}')
        return v
    
    @validator('config')
    def validate_config(cls, v, values):
        channel_type = values.get('type')
        if not channel_type:
            return v
            
        # 根据渠道类型验证配置
        if channel_type == 'email':
            required_fields = ['smtp_server', 'smtp_port', 'username', 'password', 'recipients']
        elif channel_type == 'sms':
            required_fields = ['api_key', 'api_secret', 'phone_numbers']
        elif channel_type == 'webhook':
            required_fields = ['url', 'method']
        elif channel_type == 'dingtalk':
            required_fields = ['webhook_url', 'secret']
        elif channel_type == 'wechat':
            required_fields = ['corp_id', 'corp_secret', 'agent_id']
        else:
            return v
            
        missing_fields = [field for field in required_fields if field not in v]
        if missing_fields:
            raise ValueError(f'{channel_type}渠道缺少必需配置: {", ".join(missing_fields)}')
            
        return v

class NotificationChannelUpdate(BaseModel):
    name: Optional[str] = Field(None, description="渠道名称")
    description: Optional[str] = Field(None, description="渠道描述")
    config: Optional[Dict[str, Any]] = Field(None, description="渠道配置")
    is_enabled: Optional[bool] = Field(None, description="是否启用")

class NotificationChannelResponse(BaseModel):
    id: int
    name: str
    type: str
    description: Optional[str]
    config: Dict[str, Any]
    is_enabled: bool
    send_count: int
    success_count: int
    last_used_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str]

class TestNotificationRequest(BaseModel):
    title: str = Field(..., description="测试标题")
    content: str = Field(..., description="测试内容")
    recipients: Optional[List[str]] = Field(None, description="接收人列表")

@router.get("/", response_model=List[NotificationChannelResponse])
async def get_notification_channels(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    type: Optional[str] = Query(None, description="渠道类型筛选"),
    is_enabled: Optional[bool] = Query(None, description="是否启用"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取通知渠道列表"""
    conditions = []
    
    if type:
        conditions.append(NotificationChannel.type == type)
    
    if is_enabled is not None:
        conditions.append(NotificationChannel.is_enabled == is_enabled)
    
    # 构建查询
    query = select(NotificationChannel)
    if conditions:
        query = query.where(and_(*conditions))
    
    # 分页
    offset = (page - 1) * page_size
    query = query.order_by(desc(NotificationChannel.created_at))
    query = query.offset(offset).limit(page_size)
    
    result = await db.execute(query)
    channels = result.scalars().all()
    
    # 隐藏敏感配置信息
    for channel in channels:
        if 'password' in channel.config:
            channel.config['password'] = '***'
        if 'api_secret' in channel.config:
            channel.config['api_secret'] = '***'
        if 'secret' in channel.config:
            channel.config['secret'] = '***'
        if 'corp_secret' in channel.config:
            channel.config['corp_secret'] = '***'
    
    return channels

@router.post("/", response_model=NotificationChannelResponse)
async def create_notification_channel(
    channel_data: NotificationChannelCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建通知渠道"""
    # 检查渠道名称是否重复
    result = await db.execute(
        select(NotificationChannel).where(NotificationChannel.name == channel_data.name)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="渠道名称已存在"
        )
    
    # 创建渠道
    channel = NotificationChannel(
        **channel_data.dict(),
        created_by=str(current_user.id)
    )
    
    db.add(channel)
    await db.commit()
    await db.refresh(channel)
    
    # 隐藏敏感信息
    if 'password' in channel.config:
        channel.config['password'] = '***'
    if 'api_secret' in channel.config:
        channel.config['api_secret'] = '***'
    if 'secret' in channel.config:
        channel.config['secret'] = '***'
    if 'corp_secret' in channel.config:
        channel.config['corp_secret'] = '***'
    
    return channel

@router.get("/{channel_id}", response_model=NotificationChannelResponse)
async def get_notification_channel(
    channel_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取通知渠道详情"""
    result = await db.execute(
        select(NotificationChannel).where(NotificationChannel.id == channel_id)
    )
    channel = result.scalar_one_or_none()
    
    if not channel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="通知渠道不存在"
        )
    
    # 隐藏敏感信息
    if 'password' in channel.config:
        channel.config['password'] = '***'
    if 'api_secret' in channel.config:
        channel.config['api_secret'] = '***'
    if 'secret' in channel.config:
        channel.config['secret'] = '***'
    if 'corp_secret' in channel.config:
        channel.config['corp_secret'] = '***'
    
    return channel

@router.put("/{channel_id}", response_model=NotificationChannelResponse)
async def update_notification_channel(
    channel_id: int,
    channel_data: NotificationChannelUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新通知渠道"""
    result = await db.execute(
        select(NotificationChannel).where(NotificationChannel.id == channel_id)
    )
    channel = result.scalar_one_or_none()
    
    if not channel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="通知渠道不存在"
        )
    
    # 检查名称重复（如果更新了名称）
    if channel_data.name and channel_data.name != channel.name:
        name_result = await db.execute(
            select(NotificationChannel).where(
                and_(NotificationChannel.name == channel_data.name, NotificationChannel.id != channel_id)
            )
        )
        if name_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="渠道名称已存在"
            )
    
    # 更新渠道
    update_data = channel_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(channel, field, value)
    
    await db.commit()
    await db.refresh(channel)
    
    # 隐藏敏感信息
    if 'password' in channel.config:
        channel.config['password'] = '***'
    if 'api_secret' in channel.config:
        channel.config['api_secret'] = '***'
    if 'secret' in channel.config:
        channel.config['secret'] = '***'
    if 'corp_secret' in channel.config:
        channel.config['corp_secret'] = '***'
    
    return channel

@router.delete("/{channel_id}")
async def delete_notification_channel(
    channel_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除通知渠道"""
    result = await db.execute(
        select(NotificationChannel).where(NotificationChannel.id == channel_id)
    )
    channel = result.scalar_one_or_none()
    
    if not channel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="通知渠道不存在"
        )
    
    await db.delete(channel)
    await db.commit()
    
    return {"message": "通知渠道删除成功"}

@router.post("/{channel_id}/test")
async def test_notification_channel(
    channel_id: int,
    test_data: TestNotificationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """测试通知渠道"""
    result = await db.execute(
        select(NotificationChannel).where(NotificationChannel.id == channel_id)
    )
    channel = result.scalar_one_or_none()
    
    if not channel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="通知渠道不存在"
        )
    
    if not channel.is_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="通知渠道已禁用"
        )
    
    # 这里应该调用实际的通知发送服务
    # 目前只是模拟测试
    try:
        # 创建测试日志
        log = NotificationLog(
            channel_id=channel_id,
            title=test_data.title,
            content=test_data.content,
            recipients=test_data.recipients or [],
            status="sent",
            sent_at=datetime.now()
        )
        
        db.add(log)
        
        # 更新渠道统计
        channel.send_count += 1
        channel.success_count += 1
        channel.last_used_at = datetime.now()
        
        await db.commit()
        
        return {"message": "测试通知发送成功"}
        
    except Exception as e:
        # 创建失败日志
        log = NotificationLog(
            channel_id=channel_id,
            title=test_data.title,
            content=test_data.content,
            recipients=test_data.recipients or [],
            status="failed",
            error_message=str(e)
        )
        
        db.add(log)
        channel.send_count += 1
        
        await db.commit()
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"测试通知发送失败: {str(e)}"
        )

@router.get("/{channel_id}/logs")
async def get_channel_logs(
    channel_id: int,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    status: Optional[str] = Query(None, description="发送状态筛选"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取通知渠道日志"""
    # 验证渠道存在
    channel_result = await db.execute(
        select(NotificationChannel).where(NotificationChannel.id == channel_id)
    )
    if not channel_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="通知渠道不存在"
        )
    
    conditions = [NotificationLog.channel_id == channel_id]
    
    if status:
        conditions.append(NotificationLog.status == status)
    
    # 构建查询
    query = select(NotificationLog).where(and_(*conditions))
    
    # 分页
    offset = (page - 1) * page_size
    query = query.order_by(desc(NotificationLog.created_at))
    query = query.offset(offset).limit(page_size)
    
    result = await db.execute(query)
    logs = result.scalars().all()
    
    return logs

@router.get("/{channel_id}/statistics")
async def get_channel_statistics(
    channel_id: int,
    days: int = Query(30, ge=1, le=365, description="统计天数"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取通知渠道统计信息"""
    # 验证渠道存在
    channel_result = await db.execute(
        select(NotificationChannel).where(NotificationChannel.id == channel_id)
    )
    channel = channel_result.scalar_one_or_none()
    if not channel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="通知渠道不存在"
        )
    
    # 统计时间范围
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    # 统计通知日志
    log_result = await db.execute(
        select(
            func.count(NotificationLog.id).label('total_notifications'),
            func.sum(func.case((NotificationLog.status == 'sent', 1), else_=0)).label('success_notifications'),
            func.sum(func.case((NotificationLog.status == 'failed', 1), else_=0)).label('failed_notifications'),
            func.sum(func.case((NotificationLog.status == 'pending', 1), else_=0)).label('pending_notifications')
        ).where(
            and_(
                NotificationLog.channel_id == channel_id,
                NotificationLog.created_at >= start_date,
                NotificationLog.created_at <= end_date
            )
        )
    )
    log_stats = log_result.first()
    
    return {
        "channel_id": channel_id,
        "channel_name": channel.name,
        "channel_type": channel.type,
        "total_send_count": channel.send_count,
        "total_success_count": channel.success_count,
        "last_used_at": channel.last_used_at,
        "period_days": days,
        "period_total": log_stats.total_notifications or 0,
        "period_success": log_stats.success_notifications or 0,
        "period_failed": log_stats.failed_notifications or 0,
        "period_pending": log_stats.pending_notifications or 0,
        "success_rate": (
            (log_stats.success_notifications or 0) / (log_stats.total_notifications or 1) * 100
            if log_stats.total_notifications else 0
        )
    }