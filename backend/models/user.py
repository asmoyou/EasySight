from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False, comment="用户名")
    email = Column(String(100), unique=True, index=True, nullable=False, comment="邮箱")
    hashed_password = Column(String(255), nullable=False, comment="加密密码")
    full_name = Column(String(100), comment="全名")
    phone = Column(String(20), comment="电话号码")
    avatar = Column(String(255), comment="头像URL")
    
    # 用户状态
    is_active = Column(Boolean, default=True, comment="是否激活")
    is_superuser = Column(Boolean, default=False, comment="是否超级管理员")
    is_verified = Column(Boolean, default=False, comment="是否已验证")
    
    # 权限相关 - 通过UserRole关联表管理角色
    permissions = Column(JSON, default=list, comment="用户权限列表")
    
    # 关联关系
    user_roles = relationship("UserRole", back_populates="user", cascade="all, delete-orphan", foreign_keys="UserRole.user_id")
    
    # 多语言设置
    language = Column(String(10), default="zh-CN", comment="用户语言偏好")
    timezone = Column(String(50), default="Asia/Shanghai", comment="时区")
    
    # 登录信息
    last_login = Column(DateTime(timezone=True), comment="最后登录时间")
    login_count = Column(Integer, default=0, comment="登录次数")
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 备注信息
    description = Column(Text, comment="用户描述")
    
    def verify_password(self, password: str) -> bool:
        """验证密码"""
        return pwd_context.verify(password, self.hashed_password)
    
    def set_password(self, password: str):
        """设置密码"""
        self.hashed_password = pwd_context.hash(password)
    
    @classmethod
    def hash_password(cls, password: str) -> str:
        """加密密码"""
        return pwd_context.hash(password)
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"

class UserSession(Base):
    __tablename__ = "user_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True, comment="用户ID")
    session_token = Column(String(255), unique=True, index=True, nullable=False, comment="会话令牌")
    refresh_token = Column(String(255), unique=True, index=True, comment="刷新令牌")
    ip_address = Column(String(45), comment="IP地址")
    user_agent = Column(Text, comment="用户代理")
    expires_at = Column(DateTime(timezone=True), nullable=False, comment="过期时间")
    is_active = Column(Boolean, default=True, comment="是否活跃")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")

class UserLoginLog(Base):
    __tablename__ = "user_login_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, comment="用户ID")
    username = Column(String(50), comment="用户名")
    ip_address = Column(String(45), comment="IP地址")
    user_agent = Column(Text, comment="用户代理")
    login_time = Column(DateTime(timezone=True), server_default=func.now(), comment="登录时间")
    login_result = Column(String(20), comment="登录结果：success/failed")
    failure_reason = Column(String(100), comment="失败原因")
    location = Column(String(100), comment="登录地点")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")