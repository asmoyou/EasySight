from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

from database import get_db
from models.user import User, UserLoginLog
from routers.auth import get_current_user
from config import settings

router = APIRouter()

# Pydantic models
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    phone: Optional[str] = None
    roles: List[str] = ["user"]
    permissions: List[str] = []
    language: str = "zh-CN"
    description: Optional[str] = None

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    phone: Optional[str] = None
    avatar: Optional[str] = None
    roles: Optional[List[str]] = None
    permissions: Optional[List[str]] = None
    language: Optional[str] = None
    timezone: Optional[str] = None
    is_active: Optional[bool] = None
    description: Optional[str] = None

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: Optional[str]
    phone: Optional[str]
    avatar: Optional[str]
    roles: List[str]
    permissions: List[str]
    language: str
    timezone: str
    is_active: bool
    is_superuser: bool
    is_verified: bool
    last_login: Optional[datetime]
    login_count: int
    created_at: datetime
    updated_at: datetime
    description: Optional[str]

class UserListResponse(BaseModel):
    users: List[UserResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

class PasswordReset(BaseModel):
    new_password: str

class UserStats(BaseModel):
    total_users: int
    active_users: int
    inactive_users: int
    verified_users: int
    unverified_users: int
    recent_logins: int

# 权限检查装饰器
def require_admin(current_user: User = Depends(get_current_user)):
    if not current_user.is_superuser and "admin" not in current_user.roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    return current_user

@router.get("/", response_model=UserListResponse)
async def get_users(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    role: Optional[str] = Query(None, description="角色筛选"),
    is_active: Optional[bool] = Query(None, description="状态筛选"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """获取用户列表"""
    # 构建查询条件
    conditions = []
    
    if search:
        search_pattern = f"%{search}%"
        conditions.append(
            or_(
                User.username.ilike(search_pattern),
                User.email.ilike(search_pattern),
                User.full_name.ilike(search_pattern)
            )
        )
    
    if role:
        conditions.append(User.roles.contains([role]))
    
    if is_active is not None:
        conditions.append(User.is_active == is_active)
    
    # 计算总数
    count_query = select(func.count(User.id))
    if conditions:
        count_query = count_query.where(and_(*conditions))
    
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # 查询用户列表
    query = select(User).order_by(User.created_at.desc())
    if conditions:
        query = query.where(and_(*conditions))
    
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    
    result = await db.execute(query)
    users = result.scalars().all()
    
    total_pages = (total + page_size - 1) // page_size
    
    return UserListResponse(
        users=[UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            phone=user.phone,
            avatar=user.avatar,
            roles=user.roles,
            permissions=user.permissions,
            language=user.language,
            timezone=user.timezone,
            is_active=user.is_active,
            is_superuser=user.is_superuser,
            is_verified=user.is_verified,
            last_login=user.last_login,
            login_count=user.login_count,
            created_at=user.created_at,
            updated_at=user.updated_at,
            description=user.description
        ) for user in users],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )

@router.post("/", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """创建用户"""
    # 检查用户名是否已存在
    result = await db.execute(select(User).where(User.username == user_data.username))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在"
        )
    
    # 检查邮箱是否已存在
    result = await db.execute(select(User).where(User.email == user_data.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="邮箱已存在"
        )
    
    # 创建新用户
    user = User(
        username=user_data.username,
        email=user_data.email,
        full_name=user_data.full_name,
        phone=user_data.phone,
        roles=user_data.roles,
        permissions=user_data.permissions,
        language=user_data.language,
        description=user_data.description
    )
    user.set_password(user_data.password)
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        phone=user.phone,
        avatar=user.avatar,
        roles=user.roles,
        permissions=user.permissions,
        language=user.language,
        timezone=user.timezone,
        is_active=user.is_active,
        is_superuser=user.is_superuser,
        is_verified=user.is_verified,
        last_login=user.last_login,
        login_count=user.login_count,
        created_at=user.created_at,
        updated_at=user.updated_at,
        description=user.description
    )

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取用户详情"""
    # 检查权限：管理员可以查看所有用户，普通用户只能查看自己
    if not current_user.is_superuser and "admin" not in current_user.roles and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足"
        )
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        phone=user.phone,
        avatar=user.avatar,
        roles=user.roles,
        permissions=user.permissions,
        language=user.language,
        timezone=user.timezone,
        is_active=user.is_active,
        is_superuser=user.is_superuser,
        is_verified=user.is_verified,
        last_login=user.last_login,
        login_count=user.login_count,
        created_at=user.created_at,
        updated_at=user.updated_at,
        description=user.description
    )

@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新用户信息"""
    # 检查权限
    if not current_user.is_superuser and "admin" not in current_user.roles and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足"
        )
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 检查邮箱是否已被其他用户使用
    if user_data.email and user_data.email != user.email:
        result = await db.execute(select(User).where(and_(User.email == user_data.email, User.id != user_id)))
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱已被其他用户使用"
            )
    
    # 更新用户信息
    update_data = user_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)
    
    await db.commit()
    await db.refresh(user)
    
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        phone=user.phone,
        avatar=user.avatar,
        roles=user.roles,
        permissions=user.permissions,
        language=user.language,
        timezone=user.timezone,
        is_active=user.is_active,
        is_superuser=user.is_superuser,
        is_verified=user.is_verified,
        last_login=user.last_login,
        login_count=user.login_count,
        created_at=user.created_at,
        updated_at=user.updated_at,
        description=user.description
    )

@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """删除用户"""
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能删除自己"
        )
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    await db.delete(user)
    await db.commit()
    
    return {"message": "用户删除成功"}

@router.post("/{user_id}/reset-password")
async def reset_user_password(
    user_id: int,
    password_data: PasswordReset,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """重置用户密码"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    user.set_password(password_data.new_password)
    await db.commit()
    
    return {"message": "密码重置成功"}

@router.get("/stats/overview", response_model=UserStats)
async def get_user_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """获取用户统计信息"""
    # 总用户数
    total_result = await db.execute(select(func.count(User.id)))
    total_users = total_result.scalar()
    
    # 活跃用户数
    active_result = await db.execute(select(func.count(User.id)).where(User.is_active == True))
    active_users = active_result.scalar()
    
    # 非活跃用户数
    inactive_users = total_users - active_users
    
    # 已验证用户数
    verified_result = await db.execute(select(func.count(User.id)).where(User.is_verified == True))
    verified_users = verified_result.scalar()
    
    # 未验证用户数
    unverified_users = total_users - verified_users
    
    # 最近7天登录用户数
    from datetime import datetime, timedelta
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    recent_result = await db.execute(
        select(func.count(func.distinct(UserLoginLog.user_id)))
        .where(and_(
            UserLoginLog.login_time >= seven_days_ago,
            UserLoginLog.login_result == "success"
        ))
    )
    recent_logins = recent_result.scalar()
    
    return UserStats(
        total_users=total_users,
        active_users=active_users,
        inactive_users=inactive_users,
        verified_users=verified_users,
        unverified_users=unverified_users,
        recent_logins=recent_logins
    )