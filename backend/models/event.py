from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, Float, Enum
from sqlalchemy.sql import func
from database import Base
import enum

class EventType(enum.Enum):
    INTRUSION = "intrusion"  # 入侵检测
    FIRE = "fire"  # 火灾检测
    SMOKE = "smoke"  # 烟雾检测
    VIOLENCE = "violence"  # 暴力行为
    CROWD = "crowd"  # 人群聚集
    VEHICLE = "vehicle"  # 车辆检测
    FACE = "face"  # 人脸识别
    ABNORMAL_BEHAVIOR = "abnormal_behavior"  # 异常行为
    OBJECT_LEFT = "object_left"  # 物品遗留
    OBJECT_REMOVED = "object_removed"  # 物品移除
    PERIMETER_BREACH = "perimeter_breach"  # 周界入侵
    LOITERING = "loitering"  # 徘徊检测
    SYSTEM_ERROR = "system_error"  # 系统错误
    DEVICE_OFFLINE = "device_offline"  # 设备离线
    CUSTOM = "custom"  # 自定义事件

class EventLevel(enum.Enum):
    LOW = "low"  # 低级
    MEDIUM = "medium"  # 中级
    HIGH = "high"  # 高级
    CRITICAL = "critical"  # 严重

class EventStatus(enum.Enum):
    PENDING = "pending"  # 待处理
    PROCESSING = "processing"  # 处理中
    RESOLVED = "resolved"  # 已解决
    IGNORED = "ignored"  # 已忽略
    FALSE_ALARM = "false_alarm"  # 误报

class Event(Base):
    __tablename__ = "events"
    
    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(String(50), unique=True, index=True, nullable=False, comment="事件唯一标识")
    
    # 基本信息
    event_type = Column(Enum(EventType), nullable=False, comment="事件类型")
    event_level = Column(Enum(EventLevel), default=EventLevel.MEDIUM, comment="事件级别")
    title = Column(String(200), nullable=False, comment="事件标题")
    description = Column(Text, comment="事件描述")
    
    # 设备信息
    camera_id = Column(Integer, nullable=False, comment="摄像头ID")
    camera_name = Column(String(100), comment="摄像头名称")
    camera_location = Column(String(200), comment="摄像头位置")
    
    # AI算法信息
    algorithm_id = Column(Integer, comment="触发算法ID")
    algorithm_name = Column(String(100), comment="算法名称")
    confidence_score = Column(Float, comment="置信度分数")
    
    # 位置信息
    longitude = Column(Float, comment="经度")
    latitude = Column(Float, comment="纬度")
    location_description = Column(String(200), comment="位置描述")
    
    # 检测区域
    detection_area = Column(JSON, comment="检测区域坐标")
    roi_name = Column(String(100), comment="感兴趣区域名称")
    
    # 媒体文件
    image_urls = Column(JSON, default=list, comment="相关图片URL列表")
    video_urls = Column(JSON, default=list, comment="相关视频URL列表")
    thumbnail_url = Column(String(500), comment="缩略图URL")
    
    # 检测对象信息
    detected_objects = Column(JSON, default=list, comment="检测到的对象列表")
    object_count = Column(Integer, default=0, comment="对象数量")
    
    # 状态信息
    status = Column(Enum(EventStatus), default=EventStatus.PENDING, comment="处理状态")
    is_read = Column(Boolean, default=False, comment="是否已读")
    is_important = Column(Boolean, default=False, comment="是否重要")
    
    # 处理信息
    assigned_to = Column(String(100), comment="分配给")
    processed_by = Column(String(100), comment="处理人")
    processed_at = Column(DateTime(timezone=True), comment="处理时间")
    resolution_notes = Column(Text, comment="处理备注")
    
    # 时间信息
    event_time = Column(DateTime(timezone=True), nullable=False, comment="事件发生时间")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 扩展信息
    event_metadata = Column(JSON, default=dict, comment="扩展元数据")
    tags = Column(JSON, default=list, comment="标签列表")
    
    def __repr__(self):
        return f"<Event(id={self.id}, event_id='{self.event_id}', type='{self.event_type}', level='{self.event_level}')>"

class EventRule(Base):
    __tablename__ = "event_rules"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, comment="规则名称")
    description = Column(Text, comment="规则描述")
    
    # 触发条件
    event_types = Column(JSON, default=list, comment="事件类型列表")
    camera_ids = Column(JSON, default=list, comment="摄像头ID列表")
    time_conditions = Column(JSON, default=dict, comment="时间条件")
    threshold_conditions = Column(JSON, default=dict, comment="阈值条件")
    
    # 动作配置
    actions = Column(JSON, default=list, comment="触发动作列表")
    notification_config = Column(JSON, default=dict, comment="通知配置")
    
    # 状态
    is_active = Column(Boolean, default=True, comment="是否启用")
    priority = Column(Integer, default=0, comment="优先级")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")

class EventNotification(Base):
    __tablename__ = "event_notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, nullable=False, comment="事件ID")
    
    # 通知信息
    notification_type = Column(String(50), comment="通知类型(email, sms, webhook等)")
    recipient = Column(String(200), comment="接收者")
    subject = Column(String(200), comment="主题")
    content = Column(Text, comment="通知内容")
    
    # 发送状态
    is_sent = Column(Boolean, default=False, comment="是否已发送")
    sent_at = Column(DateTime(timezone=True), comment="发送时间")
    retry_count = Column(Integer, default=0, comment="重试次数")
    error_message = Column(Text, comment="错误信息")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")

class EventStatistics(Base):
    __tablename__ = "event_statistics"
    
    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime(timezone=True), nullable=False, comment="统计日期")
    
    # 统计维度
    camera_id = Column(Integer, comment="摄像头ID")
    event_type = Column(String(50), comment="事件类型")
    event_level = Column(String(20), comment="事件级别")
    
    # 统计数据
    total_events = Column(Integer, default=0, comment="总事件数")
    resolved_events = Column(Integer, default=0, comment="已解决事件数")
    false_alarms = Column(Integer, default=0, comment="误报数")
    avg_response_time = Column(Float, comment="平均响应时间(分钟)")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")