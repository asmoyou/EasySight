from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from datetime import datetime, timedelta
from jose import JWTError, jwt
from pydantic import BaseModel, EmailStr
from typing import Optional

from database import get_db
from models.user import User, UserSession, UserLoginLog
from models.role import Role, UserRole
from config import settings

router = APIRouter()
security = HTTPBearer()

# Pydantic models
class LoginRequest(BaseModel):
    username: str
    password: str
    remember_me: bool = False

class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user_info: dict

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    phone: Optional[str] = None

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str

class UpdateProfileRequest(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    department: Optional[str] = None

class UserInfo(BaseModel):
    id: int
    username: str
    email: str
    full_name: Optional[str]
    phone: Optional[str]
    avatar: Optional[str]
    role: str
    roles: list
    permissions: list
    page_permissions: dict
    language: str
    is_active: bool
    last_login: Optional[datetime]
    created_at: datetime

# Helper function to get user roles and permissions
async def get_user_roles_and_permissions(user: User, db: AsyncSession):
    """获取用户的角色和页面权限"""
    # 查询用户的角色
    query = select(Role).join(UserRole).where(
        and_(
            UserRole.user_id == user.id,
            UserRole.is_active == True,
            Role.is_active == True
        )
    )
    result = await db.execute(query)
    roles = result.scalars().all()
    
    # 合并所有角色的权限
    all_permissions = set()
    all_page_permissions = {}
    
    for role in roles:
        # 添加角色权限
        if role.permissions:
            all_permissions.update(role.permissions)
        
        # 合并页面权限（允许访问的页面）
        if role.page_permissions:
            for page_path, allowed in role.page_permissions.items():
                if allowed:
                    all_page_permissions[page_path] = True
    
    return {
        "roles": [role.name for role in roles],
        "permissions": list(all_permissions),
        "page_permissions": all_page_permissions
    }

# JWT token functions
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: AsyncSession = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(credentials.credentials, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    if user is None:
        raise credentials_exception
    return user

@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    """用户登录"""
    # 查找用户
    result = await db.execute(select(User).where(User.username == request.username))
    user = result.scalar_one_or_none()
    
    if not user:
        # 用户不存在，记录登录失败日志
        login_log = UserLoginLog(
            user_id=None,
            username=request.username,
            login_result="failed",
            failure_reason="User not found"
        )
        db.add(login_log)
        await db.commit()
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )
    
    if not user.verify_password(request.password):
        # 密码错误，记录登录失败日志
        login_log = UserLoginLog(
            user_id=user.id,
            username=request.username,
            login_result="failed",
            failure_reason="Invalid password"
        )
        db.add(login_log)
        await db.commit()
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="账户已被禁用"
        )
    
    # 创建访问令牌
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    if request.remember_me:
        access_token_expires = timedelta(days=7)  # 记住我：7天
    
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(data={"sub": user.username})
    
    # 获取用户的角色和权限信息
    user_roles_permissions = await get_user_roles_and_permissions(user, db)
    
    # 更新用户登录信息
    user.last_login = datetime.utcnow()
    user.login_count += 1
    
    # 记录登录成功日志
    login_log = UserLoginLog(
        user_id=user.id,
        username=user.username,
        login_result="success"
    )
    db.add(login_log)
    
    await db.commit()
    
    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=int(access_token_expires.total_seconds()),
        user_info={
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "avatar": user.avatar,
            "role": user_roles_permissions["roles"][0] if user_roles_permissions["roles"] else "viewer",
            "roles": user_roles_permissions["roles"],
            "permissions": user_roles_permissions["permissions"],
            "page_permissions": user_roles_permissions["page_permissions"],
            "language": user.language
        }
    )

@router.post("/refresh", response_model=LoginResponse)
async def refresh_token(request: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    """刷新访问令牌"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid refresh token"
    )
    
    try:
        payload = jwt.decode(request.refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        token_type: str = payload.get("type")
        if username is None or token_type != "refresh":
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise credentials_exception
    
    # 创建新的访问令牌
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    # 获取用户的角色和权限信息
    user_roles_permissions = await get_user_roles_and_permissions(user, db)
    
    return LoginResponse(
        access_token=access_token,
        refresh_token=request.refresh_token,  # 刷新令牌保持不变
        expires_in=int(access_token_expires.total_seconds()),
        user_info={
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "avatar": user.avatar,
            "role": user_roles_permissions["roles"][0] if user_roles_permissions["roles"] else "viewer",
            "roles": user_roles_permissions["roles"],
            "permissions": user_roles_permissions["permissions"],
            "page_permissions": user_roles_permissions["page_permissions"],
            "language": user.language
        }
    )

@router.post("/logout")
async def logout():
    """用户登出"""
    # 这里可以实现令牌黑名单机制
    # 注意：logout接口不需要权限验证，因为在token失效时也需要能够调用
    return {"message": "登出成功"}

@router.get("/me", response_model=UserInfo)
async def get_current_user_info(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """获取当前用户信息"""
    # 获取用户的角色和权限信息
    user_roles_permissions = await get_user_roles_and_permissions(current_user, db)
    
    return UserInfo(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        full_name=current_user.full_name,
        phone=current_user.phone,
        avatar=current_user.avatar,
        role=user_roles_permissions["roles"][0] if user_roles_permissions["roles"] else "viewer",
        roles=user_roles_permissions["roles"],
        permissions=user_roles_permissions["permissions"],
        page_permissions=user_roles_permissions["page_permissions"],
        language=current_user.language,
        is_active=current_user.is_active,
        last_login=current_user.last_login,
        created_at=current_user.created_at
    )

@router.post("/change-password")
async def change_password(
    request: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """修改密码"""
    if not current_user.verify_password(request.old_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="原密码错误"
        )
    
    current_user.set_password(request.new_password)
    await db.commit()
    
    return {"message": "密码修改成功"}

@router.put("/me", response_model=UserInfo)
async def update_current_user_profile(
    request: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """更新当前用户信息"""
    # 检查邮箱是否已被其他用户使用
    if request.email and request.email != current_user.email:
        result = await db.execute(select(User).where(and_(User.email == request.email, User.id != current_user.id)))
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱已被其他用户使用"
            )
    
    # 更新用户信息
    if request.full_name is not None:
        current_user.full_name = request.full_name
    if request.email is not None:
        current_user.email = request.email
    if request.phone is not None:
        current_user.phone = request.phone
    if request.department is not None:
        current_user.department = request.department
    
    await db.commit()
    await db.refresh(current_user)
    
    # 获取用户的角色和权限信息
    user_roles_permissions = await get_user_roles_and_permissions(current_user, db)
    
    return UserInfo(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        full_name=current_user.full_name,
        phone=current_user.phone,
        avatar=current_user.avatar,
        role=user_roles_permissions["roles"][0] if user_roles_permissions["roles"] else "viewer",
        roles=user_roles_permissions["roles"],
        permissions=user_roles_permissions["permissions"],
        page_permissions=user_roles_permissions["page_permissions"],
        language=current_user.language,
        is_active=current_user.is_active,
        last_login=current_user.last_login,
        created_at=current_user.created_at
    )

@router.post("/register", response_model=UserInfo)
async def register(request: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """用户注册"""
    # 检查用户名是否已存在
    result = await db.execute(select(User).where(User.username == request.username))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在"
        )
    
    # 检查邮箱是否已存在
    result = await db.execute(select(User).where(User.email == request.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="邮箱已存在"
        )
    
    # 创建新用户
    user = User(
        username=request.username,
        email=request.email,
        full_name=request.full_name,
        phone=request.phone
    )
    user.set_password(request.password)
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    # 获取用户角色和权限信息
    user_roles_permissions = await get_user_roles_and_permissions(user, db)
    
    return UserInfo(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        phone=user.phone,
        avatar=user.avatar,
        role=user_roles_permissions["roles"][0] if user_roles_permissions["roles"] else "viewer",
        roles=user_roles_permissions["roles"],
        permissions=user_roles_permissions["permissions"],
        page_permissions=user_roles_permissions["page_permissions"],
        language=user.language,
        is_active=user.is_active,
        last_login=user.last_login,
        created_at=user.created_at
    )