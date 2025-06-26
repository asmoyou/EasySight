from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, desc
from sqlalchemy.orm import selectinload
from pydantic import BaseModel

from database import get_db
from models.user import User, UserMessage
from routers.auth import get_current_user

router = APIRouter(prefix="/api/v1/messages", tags=["messages"])

# Pydantic 模型
class MessageCreate(BaseModel):
    title: str
    content: str
    message_type: str = "info"
    receiver_id: int
    category: str = "user"
    extra_data: Optional[dict] = None

class MessageResponse(BaseModel):
    id: int
    title: str
    content: str
    message_type: str
    sender_id: Optional[int]
    receiver_id: int
    is_read: bool
    read_at: Optional[datetime]
    category: str
    extra_data: Optional[dict]
    created_at: datetime
    updated_at: datetime
    sender_name: Optional[str] = None

class MessageListResponse(BaseModel):
    messages: List[MessageResponse]
    total: int
    unread_count: int

class MessageMarkReadRequest(BaseModel):
    message_ids: List[int]

@router.get("/", response_model=MessageListResponse)
async def get_user_messages(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    category: Optional[str] = Query(None, description="消息分类筛选"),
    is_read: Optional[bool] = Query(None, description="是否已读筛选"),
    message_type: Optional[str] = Query(None, description="消息类型筛选"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取当前用户的消息列表"""
    conditions = [UserMessage.receiver_id == current_user.id]
    
    if category:
        conditions.append(UserMessage.category == category)
    if is_read is not None:
        conditions.append(UserMessage.is_read == is_read)
    if message_type:
        conditions.append(UserMessage.message_type == message_type)
    
    # 获取总数
    total_query = select(func.count(UserMessage.id)).where(and_(*conditions))
    total_result = await db.execute(total_query)
    total = total_result.scalar()
    
    # 获取未读数量
    unread_query = select(func.count(UserMessage.id)).where(
        and_(UserMessage.receiver_id == current_user.id, UserMessage.is_read == False)
    )
    unread_result = await db.execute(unread_query)
    unread_count = unread_result.scalar()
    
    # 获取消息列表
    offset = (page - 1) * page_size
    query = (
        select(UserMessage)
        .options(selectinload(UserMessage.sender))
        .where(and_(*conditions))
        .order_by(desc(UserMessage.created_at))
        .offset(offset)
        .limit(page_size)
    )
    
    result = await db.execute(query)
    messages = result.scalars().all()
    
    message_responses = []
    for message in messages:
        message_responses.append(MessageResponse(
            id=message.id,
            title=message.title,
            content=message.content,
            message_type=message.message_type,
            sender_id=message.sender_id,
            receiver_id=message.receiver_id,
            is_read=message.is_read,
            read_at=message.read_at,
            category=message.category,
            extra_data=message.extra_data,
            created_at=message.created_at,
            updated_at=message.updated_at,
            sender_name=message.sender.username if message.sender else "系统"
        ))
    
    return MessageListResponse(
        messages=message_responses,
        total=total,
        unread_count=unread_count
    )

@router.get("/unread-count")
async def get_unread_count(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取未读消息数量"""
    query = select(func.count(UserMessage.id)).where(
        and_(UserMessage.receiver_id == current_user.id, UserMessage.is_read == False)
    )
    result = await db.execute(query)
    count = result.scalar()
    return {"unread_count": count}

@router.post("/", response_model=MessageResponse)
async def create_message(
    message_data: MessageCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建消息（发送给其他用户）"""
    # 验证接收者是否存在
    receiver_query = select(User).where(User.id == message_data.receiver_id)
    receiver_result = await db.execute(receiver_query)
    receiver = receiver_result.scalar_one_or_none()
    
    if not receiver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="接收者不存在"
        )
    
    # 创建消息
    message = UserMessage(
        title=message_data.title,
        content=message_data.content,
        message_type=message_data.message_type,
        sender_id=current_user.id,
        receiver_id=message_data.receiver_id,
        category=message_data.category,
        extra_data=message_data.extra_data
    )
    
    db.add(message)
    await db.commit()
    await db.refresh(message)
    
    return MessageResponse(
        id=message.id,
        title=message.title,
        content=message.content,
        message_type=message.message_type,
        sender_id=message.sender_id,
        receiver_id=message.receiver_id,
        is_read=message.is_read,
        read_at=message.read_at,
        category=message.category,
        extra_data=message.extra_data,
        created_at=message.created_at,
        updated_at=message.updated_at,
        sender_name=current_user.username
    )

@router.put("/mark-read", response_model=dict)
async def mark_messages_read(
    request: MessageMarkReadRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """标记消息为已读"""
    # 验证消息是否属于当前用户
    query = select(UserMessage).where(
        and_(
            UserMessage.id.in_(request.message_ids),
            UserMessage.receiver_id == current_user.id
        )
    )
    result = await db.execute(query)
    messages = result.scalars().all()
    
    if len(messages) != len(request.message_ids):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="部分消息不存在或不属于当前用户"
        )
    
    # 更新消息状态
    for message in messages:
        if not message.is_read:
            message.is_read = True
            message.read_at = datetime.utcnow()
    
    await db.commit()
    
    return {"message": f"成功标记 {len(messages)} 条消息为已读"}

@router.put("/mark-all-read", response_model=dict)
async def mark_all_messages_read(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """标记所有消息为已读"""
    query = select(UserMessage).where(
        and_(
            UserMessage.receiver_id == current_user.id,
            UserMessage.is_read == False
        )
    )
    result = await db.execute(query)
    messages = result.scalars().all()
    
    # 更新消息状态
    for message in messages:
        message.is_read = True
        message.read_at = datetime.utcnow()
    
    await db.commit()
    
    return {"message": f"成功标记 {len(messages)} 条消息为已读"}

@router.get("/{message_id}", response_model=MessageResponse)
async def get_message(
    message_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取单条消息详情"""
    query = (
        select(UserMessage)
        .options(selectinload(UserMessage.sender))
        .where(
            and_(
                UserMessage.id == message_id,
                UserMessage.receiver_id == current_user.id
            )
        )
    )
    result = await db.execute(query)
    message = result.scalar_one_or_none()
    
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="消息不存在"
        )
    
    # 如果消息未读，标记为已读
    if not message.is_read:
        message.is_read = True
        message.read_at = datetime.utcnow()
        await db.commit()
    
    return MessageResponse(
        id=message.id,
        title=message.title,
        content=message.content,
        message_type=message.message_type,
        sender_id=message.sender_id,
        receiver_id=message.receiver_id,
        is_read=message.is_read,
        read_at=message.read_at,
        category=message.category,
        extra_data=message.extra_data,
        created_at=message.created_at,
        updated_at=message.updated_at,
        sender_name=message.sender.username if message.sender else "系统"
    )

@router.delete("/{message_id}", response_model=dict)
async def delete_message(
    message_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除消息"""
    query = select(UserMessage).where(
        and_(
            UserMessage.id == message_id,
            UserMessage.receiver_id == current_user.id
        )
    )
    result = await db.execute(query)
    message = result.scalar_one_or_none()
    
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="消息不存在"
        )
    
    await db.delete(message)
    await db.commit()
    
    return {"message": "消息删除成功"}