from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base

class Role(Base):
    """角色模型"""
    __tablename__ = "roles"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, index=True, nullable=False, comment="角色名称")
    display_name = Column(String(100), nullable=False, comment="显示名称")
    description = Column(Text, comment="角色描述")
    
    # 角色状态
    is_active = Column(Boolean, default=True, comment="是否启用")
    is_system = Column(Boolean, default=False, comment="是否系统角色")
    
    # 权限配置
    permissions = Column(JSON, default=list, comment="角色权限列表")
    
    # 页面权限配置
    page_permissions = Column(JSON, default=dict, comment="页面权限配置")
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 关联关系
    user_roles = relationship("UserRole", back_populates="role", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Role(id={self.id}, name='{self.name}', display_name='{self.display_name}')>"

class Permission(Base):
    """权限模型"""
    __tablename__ = "permissions"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False, comment="权限名称")
    display_name = Column(String(100), nullable=False, comment="显示名称")
    description = Column(Text, comment="权限描述")
    
    # 权限分类
    category = Column(String(50), comment="权限分类")
    module = Column(String(50), comment="所属模块")
    
    # 权限类型：page(页面权限), action(操作权限), data(数据权限)
    permission_type = Column(String(20), default="action", comment="权限类型")
    
    # 权限状态
    is_active = Column(Boolean, default=True, comment="是否启用")
    is_system = Column(Boolean, default=False, comment="是否系统权限")
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    def __repr__(self):
        return f"<Permission(id={self.id}, name='{self.name}', display_name='{self.display_name}')>"

class UserRole(Base):
    """用户角色关联模型"""
    __tablename__ = "user_roles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="用户ID")
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False, comment="角色ID")
    
    # 分配信息
    assigned_by = Column(Integer, ForeignKey("users.id"), comment="分配者ID")
    assigned_at = Column(DateTime(timezone=True), server_default=func.now(), comment="分配时间")
    
    # 有效期
    expires_at = Column(DateTime(timezone=True), comment="过期时间")
    is_active = Column(Boolean, default=True, comment="是否有效")
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 关联关系
    user = relationship("User", back_populates="user_roles", foreign_keys=[user_id])
    role = relationship("Role", back_populates="user_roles")
    
    def __repr__(self):
        return f"<UserRole(id={self.id}, user_id={self.user_id}, role_id={self.role_id})>"