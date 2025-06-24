from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

from database import get_db
from models.role import Role, Permission, UserRole
from models.user import User
from routers.auth import get_current_user
from routers.users import require_admin

router = APIRouter()

# Pydantic models
class RoleCreate(BaseModel):
    name: str
    display_name: str
    description: Optional[str] = None
    permissions: List[str] = []
    page_permissions: Dict[str, Any] = {}

class RoleUpdate(BaseModel):
    display_name: Optional[str] = None
    description: Optional[str] = None
    permissions: Optional[List[str]] = None
    page_permissions: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None

class RoleResponse(BaseModel):
    id: int
    name: str
    display_name: str
    description: Optional[str]
    permissions: List[str]
    page_permissions: Dict[str, Any]
    is_active: bool
    is_system: bool
    created_at: datetime
    updated_at: datetime
    user_count: Optional[int] = 0

class PermissionCreate(BaseModel):
    name: str
    display_name: str
    description: Optional[str] = None
    category: Optional[str] = None
    module: Optional[str] = None
    permission_type: str = "action"

class PermissionUpdate(BaseModel):
    display_name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    module: Optional[str] = None
    permission_type: Optional[str] = None
    is_active: Optional[bool] = None

class PermissionResponse(BaseModel):
    id: int
    name: str
    display_name: str
    description: Optional[str]
    category: Optional[str]
    module: Optional[str]
    permission_type: str
    is_active: bool
    is_system: bool
    created_at: datetime
    updated_at: datetime

class UserRoleAssign(BaseModel):
    user_id: int
    role_ids: List[int]
    expires_at: Optional[datetime] = None

class PagePermissionConfig(BaseModel):
    """页面权限配置"""
    page_path: str
    permissions: List[str]
    allow_access: bool = True

# 角色管理接口
@router.get("/", response_model=Dict[str, Any])
async def get_roles(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """获取角色列表"""
    # 构建查询条件
    conditions = []
    if search:
        conditions.append(
            or_(
                Role.name.ilike(f"%{search}%"),
                Role.display_name.ilike(f"%{search}%"),
                Role.description.ilike(f"%{search}%")
            )
        )
    if is_active is not None:
        conditions.append(Role.is_active == is_active)
    
    # 查询总数
    count_query = select(func.count(Role.id))
    if conditions:
        count_query = count_query.where(and_(*conditions))
    
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # 查询角色列表
    query = select(Role).order_by(desc(Role.created_at))
    if conditions:
        query = query.where(and_(*conditions))
    
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    roles = result.scalars().all()
    
    # 获取每个角色的用户数量
    role_data = []
    for role in roles:
        # 查询使用该角色的用户数量
        user_count_query = select(func.count(UserRole.id)).where(
            and_(UserRole.role_id == role.id, UserRole.is_active == True)
        )
        user_count_result = await db.execute(user_count_query)
        user_count = user_count_result.scalar()
        
        role_dict = {
            "id": role.id,
            "name": role.name,
            "display_name": role.display_name,
            "description": role.description,
            "permissions": role.permissions or [],
            "page_permissions": role.page_permissions or {},
            "is_active": role.is_active,
            "is_system": role.is_system,
            "created_at": role.created_at,
            "updated_at": role.updated_at,
            "user_count": user_count
        }
        role_data.append(role_dict)
    
    return {
        "data": role_data,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size
    }

@router.post("/", response_model=RoleResponse)
async def create_role(
    role_data: RoleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """创建角色"""
    # 检查角色名是否已存在
    result = await db.execute(select(Role).where(Role.name == role_data.name))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="角色名已存在"
        )
    
    # 创建角色
    role = Role(
        name=role_data.name,
        display_name=role_data.display_name,
        description=role_data.description,
        permissions=role_data.permissions,
        page_permissions=role_data.page_permissions
    )
    
    db.add(role)
    await db.commit()
    await db.refresh(role)
    
    return RoleResponse(
        id=role.id,
        name=role.name,
        display_name=role.display_name,
        description=role.description,
        permissions=role.permissions or [],
        page_permissions=role.page_permissions or {},
        is_active=role.is_active,
        is_system=role.is_system,
        created_at=role.created_at,
        updated_at=role.updated_at
    )

@router.get("/{role_id}", response_model=RoleResponse)
async def get_role(
    role_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """获取角色详情"""
    result = await db.execute(select(Role).where(Role.id == role_id))
    role = result.scalar_one_or_none()
    
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="角色不存在"
        )
    
    return RoleResponse(
        id=role.id,
        name=role.name,
        display_name=role.display_name,
        description=role.description,
        permissions=role.permissions or [],
        page_permissions=role.page_permissions or {},
        is_active=role.is_active,
        is_system=role.is_system,
        created_at=role.created_at,
        updated_at=role.updated_at
    )

@router.put("/{role_id}", response_model=RoleResponse)
async def update_role(
    role_id: int,
    role_data: RoleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """更新角色"""
    result = await db.execute(select(Role).where(Role.id == role_id))
    role = result.scalar_one_or_none()
    
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="角色不存在"
        )
    
    # 检查是否为系统角色
    if role.is_system:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="系统角色不允许修改"
        )
    
    # 更新角色信息
    update_data = role_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(role, field, value)
    
    await db.commit()
    await db.refresh(role)
    
    return RoleResponse(
        id=role.id,
        name=role.name,
        display_name=role.display_name,
        description=role.description,
        permissions=role.permissions or [],
        page_permissions=role.page_permissions or {},
        is_active=role.is_active,
        is_system=role.is_system,
        created_at=role.created_at,
        updated_at=role.updated_at
    )

@router.delete("/{role_id}")
async def delete_role(
    role_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """删除角色"""
    result = await db.execute(select(Role).where(Role.id == role_id))
    role = result.scalar_one_or_none()
    
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="角色不存在"
        )
    
    # 检查是否为系统角色
    if role.is_system:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="系统角色不允许删除"
        )
    
    # 检查是否有用户使用该角色
    user_role_result = await db.execute(
        select(UserRole).where(and_(UserRole.role_id == role_id, UserRole.is_active == True))
    )
    if user_role_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该角色正在被用户使用，无法删除"
        )
    
    await db.delete(role)
    await db.commit()
    
    return {"message": "角色删除成功"}

# 权限管理接口
@router.get("/permissions/", response_model=List[PermissionResponse])
async def get_permissions(
    category: Optional[str] = Query(None),
    module: Optional[str] = Query(None),
    permission_type: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """获取权限列表"""
    conditions = []
    if category:
        conditions.append(Permission.category == category)
    if module:
        conditions.append(Permission.module == module)
    if permission_type:
        conditions.append(Permission.permission_type == permission_type)
    if is_active is not None:
        conditions.append(Permission.is_active == is_active)
    
    query = select(Permission).order_by(Permission.category, Permission.module, Permission.name)
    if conditions:
        query = query.where(and_(*conditions))
    
    result = await db.execute(query)
    permissions = result.scalars().all()
    
    return [
        PermissionResponse(
            id=perm.id,
            name=perm.name,
            display_name=perm.display_name,
            description=perm.description,
            category=perm.category,
            module=perm.module,
            permission_type=perm.permission_type,
            is_active=perm.is_active,
            is_system=perm.is_system,
            created_at=perm.created_at,
            updated_at=perm.updated_at
        )
        for perm in permissions
    ]

@router.post("/permissions/", response_model=PermissionResponse)
async def create_permission(
    permission_data: PermissionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """创建权限"""
    # 检查权限名是否已存在
    result = await db.execute(select(Permission).where(Permission.name == permission_data.name))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="权限名已存在"
        )
    
    permission = Permission(**permission_data.dict())
    db.add(permission)
    await db.commit()
    await db.refresh(permission)
    
    return PermissionResponse(
        id=permission.id,
        name=permission.name,
        display_name=permission.display_name,
        description=permission.description,
        category=permission.category,
        module=permission.module,
        permission_type=permission.permission_type,
        is_active=permission.is_active,
        is_system=permission.is_system,
        created_at=permission.created_at,
        updated_at=permission.updated_at
    )

# 用户角色分配接口
@router.post("/assign")
async def assign_user_roles(
    assignment: UserRoleAssign,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """分配用户角色"""
    # 检查用户是否存在
    user_result = await db.execute(select(User).where(User.id == assignment.user_id))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 检查角色是否存在
    for role_id in assignment.role_ids:
        role_result = await db.execute(select(Role).where(Role.id == role_id))
        if not role_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"角色ID {role_id} 不存在"
            )
    
    # 删除用户现有的角色分配
    await db.execute(
        select(UserRole).where(UserRole.user_id == assignment.user_id)
    )
    existing_roles = await db.execute(
        select(UserRole).where(UserRole.user_id == assignment.user_id)
    )
    for existing_role in existing_roles.scalars().all():
        await db.delete(existing_role)
    
    # 分配新角色
    for role_id in assignment.role_ids:
        user_role = UserRole(
            user_id=assignment.user_id,
            role_id=role_id,
            assigned_by=current_user.id,
            expires_at=assignment.expires_at
        )
        db.add(user_role)
    
    await db.commit()
    
    return {"message": "角色分配成功"}

@router.get("/user/{user_id}/roles")
async def get_user_roles(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """获取用户的角色列表"""
    # 查询用户角色
    query = select(Role).join(UserRole).where(
        and_(
            UserRole.user_id == user_id,
            UserRole.is_active == True
        )
    )
    result = await db.execute(query)
    roles = result.scalars().all()
    
    return [
        {
            "id": role.id,
            "name": role.name,
            "display_name": role.display_name,
            "description": role.description
        }
        for role in roles
    ]