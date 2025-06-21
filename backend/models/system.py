from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, Float
from sqlalchemy.sql import func
from database import Base
from enum import Enum

class LogLevel(str, Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class SystemConfig(Base):
    __tablename__ = "system_configs"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, index=True, nullable=False, comment="配置键")
    value = Column(Text, comment="配置值")
    value_type = Column(String(20), default="string", comment="值类型(string, int, float, bool, json)")
    category = Column(String(50), comment="配置分类")
    description = Column(Text, comment="配置描述")
    
    # 配置属性
    is_public = Column(Boolean, default=False, comment="是否公开(前端可访问)")
    is_editable = Column(Boolean, default=True, comment="是否可编辑")
    requires_restart = Column(Boolean, default=False, comment="是否需要重启")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")
    updated_by = Column(String(100), comment="更新人")

class SystemVersion(Base):
    __tablename__ = "system_versions"
    
    id = Column(Integer, primary_key=True, index=True)
    version = Column(String(20), nullable=False, comment="版本号")
    build_number = Column(String(50), comment="构建号")
    release_date = Column(DateTime(timezone=True), comment="发布日期")
    
    # 版本信息
    version_name = Column(String(100), comment="版本名称")
    description = Column(Text, comment="版本描述")
    changelog = Column(Text, comment="更新日志")
    
    # 组件版本
    frontend_version = Column(String(20), comment="前端版本")
    backend_version = Column(String(20), comment="后端版本")
    database_version = Column(String(20), comment="数据库版本")
    
    # 状态
    is_current = Column(Boolean, default=False, comment="是否当前版本")
    is_stable = Column(Boolean, default=True, comment="是否稳定版本")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")

class DataRetentionPolicy(Base):
    __tablename__ = "data_retention_policies"
    
    id = Column(Integer, primary_key=True, index=True)
    data_type = Column(String(50), nullable=False, comment="数据类型")
    retention_days = Column(Integer, nullable=False, comment="保留天数")
    
    # 策略配置
    auto_cleanup = Column(Boolean, default=True, comment="是否自动清理")
    cleanup_time = Column(String(10), default="02:00", comment="清理时间")
    archive_before_delete = Column(Boolean, default=False, comment="删除前是否归档")
    archive_location = Column(String(500), comment="归档位置")
    
    # 状态
    is_active = Column(Boolean, default=True, comment="是否启用")
    last_cleanup = Column(DateTime(timezone=True), comment="最后清理时间")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")

class MessageCenter(Base):
    __tablename__ = "message_centers"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, comment="消息中心名称")
    
    # 连接配置
    host = Column(String(100), nullable=False, comment="IP地址")
    port = Column(Integer, nullable=False, comment="端口")
    protocol = Column(String(20), default="http", comment="协议类型")
    
    # 认证配置
    username = Column(String(100), comment="用户名")
    password = Column(String(255), comment="密码")
    api_key = Column(String(255), comment="API密钥")
    
    # 事件配置
    enabled_event_types = Column(JSON, default=list, comment="启用的事件类型")
    event_filter = Column(JSON, default=dict, comment="事件过滤条件")
    
    # 格式配置
    message_format = Column(String(20), default="json", comment="消息格式")
    custom_template = Column(Text, comment="自定义模板")
    
    # 状态
    is_active = Column(Boolean, default=True, comment="是否启用")
    is_connected = Column(Boolean, default=False, comment="是否连接")
    last_heartbeat = Column(DateTime(timezone=True), comment="最后心跳时间")
    
    # 统计
    total_sent = Column(Integer, default=0, comment="总发送数")
    total_failed = Column(Integer, default=0, comment="总失败数")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")

class SystemLog(Base):
    __tablename__ = "system_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    level = Column(String(20), nullable=False, comment="日志级别")
    module = Column(String(50), comment="模块名称")
    message = Column(Text, nullable=False, comment="日志消息")
    
    # 详细信息
    details = Column(JSON, comment="详细信息")
    stack_trace = Column(Text, comment="堆栈跟踪")
    
    # 用户信息
    user_id = Column(Integer, comment="用户ID")
    username = Column(String(100), comment="用户名")
    ip_address = Column(String(45), comment="IP地址")
    user_agent = Column(Text, comment="用户代理")
    
    # 请求信息
    request_id = Column(String(50), comment="请求ID")
    request_method = Column(String(10), comment="请求方法")
    request_url = Column(String(500), comment="请求URL")
    response_status = Column(Integer, comment="响应状态码")
    response_time = Column(Float, comment="响应时间(ms)")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")

class SystemMetrics(Base):
    __tablename__ = "system_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    metric_name = Column(String(100), nullable=False, comment="指标名称")
    metric_value = Column(Float, nullable=False, comment="指标值")
    metric_unit = Column(String(20), comment="指标单位")
    
    # 维度信息
    dimensions = Column(JSON, default=dict, comment="维度信息")
    
    # 时间信息
    timestamp = Column(DateTime(timezone=True), nullable=False, comment="时间戳")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")

class License(Base):
    __tablename__ = "licenses"
    
    id = Column(Integer, primary_key=True, index=True)
    license_key = Column(String(500), unique=True, nullable=False, comment="许可证密钥")
    
    # 许可证信息
    product_name = Column(String(100), comment="产品名称")
    version = Column(String(20), comment="版本")
    customer_name = Column(String(100), comment="客户名称")
    customer_email = Column(String(100), comment="客户邮箱")
    
    # 限制信息
    max_cameras = Column(Integer, comment="最大摄像头数")
    max_users = Column(Integer, comment="最大用户数")
    max_ai_services = Column(Integer, comment="最大AI服务数")
    
    # 功能限制
    enabled_features = Column(JSON, default=list, comment="启用的功能列表")
    
    # 时间限制
    issued_at = Column(DateTime(timezone=True), comment="签发时间")
    expires_at = Column(DateTime(timezone=True), comment="过期时间")
    
    # 状态
    is_active = Column(Boolean, default=True, comment="是否激活")
    is_trial = Column(Boolean, default=False, comment="是否试用版")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")