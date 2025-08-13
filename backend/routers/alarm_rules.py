from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, desc
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from pydantic import BaseModel, Field

from database import get_db
from models.diagnosis import AlarmRule, NotificationChannel, NotificationLog, DiagnosisAlarm
from models.user import User
from routers.auth import get_current_user

router = APIRouter(prefix="/api/v1/alarm-rules", tags=["告警规则"])

# Pydantic 模型
class AlarmRuleCreate(BaseModel):
    name: str = Field(..., description="规则名称")
    description: Optional[str] = Field(None, description="规则描述")
    diagnosis_types: List[str] = Field(default=[], description="适用的诊断类型")
    camera_ids: List[int] = Field(default=[], description="适用的摄像头ID列表")
    camera_groups: List[str] = Field(default=[], description="适用的摄像头组")
    severity_level: str = Field(description="触发的严重程度级别")
    threshold_config: Dict[str, Any] = Field(default={}, description="阈值配置")
    frequency_limit: int = Field(default=0, description="频率限制(分钟内最多触发次数)")
    notification_channels: List[int] = Field(default=[], description="通知渠道ID列表")
    notification_template: Optional[str] = Field(None, description="通知模板")
    is_enabled: bool = Field(default=True, description="是否启用")
    priority: int = Field(default=1, description="优先级")

class AlarmRuleUpdate(BaseModel):
    name: Optional[str] = Field(None, description="规则名称")
    description: Optional[str] = Field(None, description="规则描述")
    diagnosis_types: Optional[List[str]] = Field(None, description="适用的诊断类型")
    camera_ids: Optional[List[int]] = Field(None, description="适用的摄像头ID列表")
    camera_groups: Optional[List[str]] = Field(None, description="适用的摄像头组")
    severity_level: Optional[str] = Field(None, description="触发的严重程度级别")
    threshold_config: Optional[Dict[str, Any]] = Field(None, description="阈值配置")
    frequency_limit: Optional[int] = Field(None, description="频率限制")
    notification_channels: Optional[List[int]] = Field(None, description="通知渠道ID列表")
    notification_template: Optional[str] = Field(None, description="通知模板")
    is_enabled: Optional[bool] = Field(None, description="是否启用")
    priority: Optional[int] = Field(None, description="优先级")

class AlarmRuleResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    diagnosis_types: List[str]
    camera_ids: List[int]
    camera_groups: List[str]
    severity_level: str
    threshold_config: Dict[str, Any]
    frequency_limit: int
    notification_channels: List[int]
    notification_template: Optional[str]
    is_enabled: bool
    priority: int
    trigger_count: int
    last_triggered_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str]

@router.get("/", response_model=List[AlarmRuleResponse])
async def get_alarm_rules(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    is_enabled: Optional[bool] = Query(None, description="是否启用"),
    diagnosis_type: Optional[str] = Query(None, description="诊断类型筛选"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取告警规则列表"""
    conditions = []
    
    if is_enabled is not None:
        conditions.append(AlarmRule.is_enabled == is_enabled)
    
    if diagnosis_type:
        conditions.append(AlarmRule.diagnosis_types.contains([diagnosis_type]))
    
    # 构建查询
    query = select(AlarmRule)
    if conditions:
        query = query.where(and_(*conditions))
    
    # 分页
    offset = (page - 1) * page_size
    query = query.order_by(desc(AlarmRule.priority), desc(AlarmRule.created_at))
    query = query.offset(offset).limit(page_size)
    
    result = await db.execute(query)
    rules = result.scalars().all()
    
    return rules

@router.post("/", response_model=AlarmRuleResponse)
async def create_alarm_rule(
    rule_data: AlarmRuleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建告警规则"""
    # 检查规则名称是否重复
    result = await db.execute(
        select(AlarmRule).where(AlarmRule.name == rule_data.name)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="规则名称已存在"
        )
    
    # 验证通知渠道是否存在
    if rule_data.notification_channels:
        channel_result = await db.execute(
            select(NotificationChannel).where(
                NotificationChannel.id.in_(rule_data.notification_channels)
            )
        )
        existing_channels = [c.id for c in channel_result.scalars().all()]
        invalid_channels = set(rule_data.notification_channels) - set(existing_channels)
        if invalid_channels:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"通知渠道不存在: {list(invalid_channels)}"
            )
    
    # 创建规则
    rule = AlarmRule(
        **rule_data.dict(),
        created_by=str(current_user.id)
    )
    
    db.add(rule)
    await db.commit()
    await db.refresh(rule)
    
    return rule

@router.get("/{rule_id}", response_model=AlarmRuleResponse)
async def get_alarm_rule(
    rule_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取告警规则详情"""
    result = await db.execute(
        select(AlarmRule).where(AlarmRule.id == rule_id)
    )
    rule = result.scalar_one_or_none()
    
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="告警规则不存在"
        )
    
    return rule

@router.put("/{rule_id}", response_model=AlarmRuleResponse)
async def update_alarm_rule(
    rule_id: int,
    rule_data: AlarmRuleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新告警规则"""
    result = await db.execute(
        select(AlarmRule).where(AlarmRule.id == rule_id)
    )
    rule = result.scalar_one_or_none()
    
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="告警规则不存在"
        )
    
    # 检查名称重复（如果更新了名称）
    if rule_data.name and rule_data.name != rule.name:
        name_result = await db.execute(
            select(AlarmRule).where(
                and_(AlarmRule.name == rule_data.name, AlarmRule.id != rule_id)
            )
        )
        if name_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="规则名称已存在"
            )
    
    # 验证通知渠道
    if rule_data.notification_channels is not None:
        if rule_data.notification_channels:
            channel_result = await db.execute(
                select(NotificationChannel).where(
                    NotificationChannel.id.in_(rule_data.notification_channels)
                )
            )
            existing_channels = [c.id for c in channel_result.scalars().all()]
            invalid_channels = set(rule_data.notification_channels) - set(existing_channels)
            if invalid_channels:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"通知渠道不存在: {list(invalid_channels)}"
                )
    
    # 更新规则
    update_data = rule_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(rule, field, value)
    
    await db.commit()
    await db.refresh(rule)
    
    return rule

@router.delete("/{rule_id}")
async def delete_alarm_rule(
    rule_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除告警规则"""
    result = await db.execute(
        select(AlarmRule).where(AlarmRule.id == rule_id)
    )
    rule = result.scalar_one_or_none()
    
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="告警规则不存在"
        )
    
    await db.delete(rule)
    await db.commit()
    
    return {"message": "告警规则删除成功"}

@router.post("/{rule_id}/toggle")
async def toggle_alarm_rule(
    rule_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """切换告警规则启用状态"""
    result = await db.execute(
        select(AlarmRule).where(AlarmRule.id == rule_id)
    )
    rule = result.scalar_one_or_none()
    
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="告警规则不存在"
        )
    
    rule.is_enabled = not rule.is_enabled
    await db.commit()
    await db.refresh(rule)
    
    return {"message": f"告警规则已{'启用' if rule.is_enabled else '禁用'}"}

@router.get("/{rule_id}/statistics")
async def get_rule_statistics(
    rule_id: int,
    days: int = Query(30, ge=1, le=365, description="统计天数"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取告警规则统计信息"""
    result = await db.execute(
        select(AlarmRule).where(AlarmRule.id == rule_id)
    )
    rule = result.scalar_one_or_none()
    
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="告警规则不存在"
        )
    
    # 统计时间范围
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    # 统计通知日志
    log_result = await db.execute(
        select(
            func.count(NotificationLog.id).label('total_notifications'),
            func.sum(func.case((NotificationLog.status == 'sent', 1), else_=0)).label('success_notifications'),
            func.sum(func.case((NotificationLog.status == 'failed', 1), else_=0)).label('failed_notifications')
        ).where(
            and_(
                NotificationLog.rule_id == rule_id,
                NotificationLog.created_at >= start_date,
                NotificationLog.created_at <= end_date
            )
        )
    )
    log_stats = log_result.first()
    
    return {
        "rule_id": rule_id,
        "rule_name": rule.name,
        "total_triggers": rule.trigger_count,
        "last_triggered_at": rule.last_triggered_at,
        "period_days": days,
        "total_notifications": log_stats.total_notifications or 0,
        "success_notifications": log_stats.success_notifications or 0,
        "failed_notifications": log_stats.failed_notifications or 0,
        "success_rate": (
            (log_stats.success_notifications or 0) / (log_stats.total_notifications or 1) * 100
            if log_stats.total_notifications else 0
        )
    }