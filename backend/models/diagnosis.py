from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, Float, Enum
from sqlalchemy.sql import func
from database import Base
import enum

class DiagnosisType(enum.Enum):
    BRIGHTNESS = "brightness"  # 亮度检测
    BLUE_SCREEN = "blue_screen"  # 蓝屏检查
    CLARITY = "clarity"  # 清晰度检查
    SHAKE = "shake"  # 抖动检查
    FREEZE = "freeze"  # 冻结检测
    COLOR_CAST = "color_cast"  # 偏色检测
    OCCLUSION = "occlusion"  # 遮挡检测
    NOISE = "noise"  # 噪声检测
    CONTRAST = "contrast"  # 对比度检测
    MOSAIC = "mosaic"  # 马赛克检测
    FLOWER_SCREEN = "flower_screen"  # 花屏检测
    SIGNAL_LOSS = "signal_loss"  # 信号丢失
    LENS_DIRTY = "lens_dirty"  # 镜头脏污
    FOCUS_BLUR = "focus_blur"  # 焦点模糊

class DiagnosisStatus(enum.Enum):
    NORMAL = "normal"  # 正常
    WARNING = "warning"  # 警告
    ERROR = "error"  # 错误
    CRITICAL = "critical"  # 严重

class TaskStatus(enum.Enum):
    PENDING = "PENDING"  # 待执行
    RUNNING = "RUNNING"  # 运行中
    COMPLETED = "COMPLETED"  # 已完成
    FAILED = "FAILED"  # 失败
    CANCELLED = "CANCELLED"  # 已取消

class TaskType(enum.Enum):
    DIAGNOSIS = "DIAGNOSIS"  # 诊断任务
    AI_DETECTION = "AI_DETECTION"  # AI检测任务
    MONITORING = "MONITORING"  # 监控任务
    MAINTENANCE = "MAINTENANCE"  # 维护任务

class DiagnosisTask(Base):
    __tablename__ = "diagnosis_tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, comment="任务名称")
    description = Column(Text, comment="任务描述")
    
    # 任务类型
    task_type = Column(Enum(TaskType), default=TaskType.DIAGNOSIS, comment="任务类型")
    
    # 模板关联
    template_id = Column(Integer, comment="诊断模板ID")
    
    # 诊断配置 - 匹配实际数据库结构
    camera_ids = Column(JSON, default=list, comment="摄像头ID列表")
    camera_groups = Column(JSON, default=list, comment="摄像头组列表")
    diagnosis_types = Column(JSON, default=list, comment="诊断类型列表")
    diagnosis_config = Column(JSON, default=dict, comment="诊断配置参数")
    
    # 调度配置 - 匹配实际数据库结构
    schedule_type = Column(String(50), comment="调度类型")
    schedule_config = Column(JSON, default=dict, comment="调度配置")
    cron_expression = Column(String(100), comment="Cron表达式")
    interval_minutes = Column(Integer, comment="间隔分钟数")
    threshold_config = Column(JSON, default=dict, comment="阈值配置")
    
    # 状态信息
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING, comment="任务状态")
    is_active = Column(Boolean, default=True, comment="是否启用")
    enabled = Column(Boolean, default=True, comment="是否启用")
    assigned_worker = Column(String(100), comment="分配的worker节点ID")
    
    # 执行信息 - 匹配实际数据库结构
    started_at = Column(DateTime(timezone=True), comment="任务开始时间")
    last_run_time = Column(DateTime(timezone=True), comment="最后执行时间")
    next_run_time = Column(DateTime(timezone=True), comment="下次执行时间")
    total_runs = Column(Integer, default=0, comment="总执行次数")
    success_runs = Column(Integer, default=0, comment="成功执行次数")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")
    created_by = Column(String(50), comment="创建人ID")

class AlarmRule(Base):
    """告警规则模型"""
    __tablename__ = "alarm_rules"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, comment="规则名称")
    description = Column(Text, comment="规则描述")
    
    # 规则配置
    diagnosis_types = Column(JSON, default=list, comment="适用的诊断类型")
    camera_ids = Column(JSON, default=list, comment="适用的摄像头ID列表")
    camera_groups = Column(JSON, default=list, comment="适用的摄像头组")
    
    # 触发条件
    severity_level = Column(String(20), comment="触发的严重程度级别")
    threshold_config = Column(JSON, default=dict, comment="阈值配置")
    frequency_limit = Column(Integer, default=0, comment="频率限制(分钟内最多触发次数)")
    
    # 通知配置
    notification_channels = Column(JSON, default=list, comment="通知渠道")
    notification_template = Column(Text, comment="通知模板")
    
    # 状态
    is_enabled = Column(Boolean, default=True, comment="是否启用")
    priority = Column(Integer, default=1, comment="优先级")
    
    # 统计信息
    trigger_count = Column(Integer, default=0, comment="触发次数")
    last_triggered_at = Column(DateTime(timezone=True), comment="最后触发时间")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")
    created_by = Column(String(50), comment="创建人ID")

class NotificationChannel(Base):
    """通知渠道模型"""
    __tablename__ = "notification_channels"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, comment="渠道名称")
    type = Column(String(50), nullable=False, comment="渠道类型: email, sms, webhook, dingtalk, wechat")
    description = Column(Text, comment="渠道描述")
    
    # 配置信息
    config = Column(JSON, default=dict, comment="渠道配置")
    
    # 状态
    is_enabled = Column(Boolean, default=True, comment="是否启用")
    
    # 统计信息
    send_count = Column(Integer, default=0, comment="发送次数")
    success_count = Column(Integer, default=0, comment="成功次数")
    last_used_at = Column(DateTime(timezone=True), comment="最后使用时间")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")
    created_by = Column(String(50), comment="创建人ID")

class NotificationLog(Base):
    """通知日志模型"""
    __tablename__ = "notification_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    alarm_id = Column(Integer, comment="告警ID")
    rule_id = Column(Integer, comment="规则ID")
    channel_id = Column(Integer, comment="通知渠道ID")
    
    # 通知信息
    title = Column(String(200), comment="通知标题")
    content = Column(Text, comment="通知内容")
    recipients = Column(JSON, default=list, comment="接收人列表")
    
    # 发送状态
    status = Column(String(20), default="pending", comment="发送状态: pending, sent, failed")
    error_message = Column(Text, comment="错误信息")
    retry_count = Column(Integer, default=0, comment="重试次数")
    
    # 时间信息
    sent_at = Column(DateTime(timezone=True), comment="发送时间")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    created_by = Column(String(50), comment="创建人ID")
    
    def __repr__(self):
        return f"<DiagnosisTask(id={self.id}, name='{self.name}', status='{self.status}')>"

class DiagnosisResult(Base):
    __tablename__ = "diagnosis_results"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, nullable=False, comment="诊断任务ID")
    camera_id = Column(Integer, comment="摄像头ID")
    camera_name = Column(String(100), comment="摄像头名称")
    diagnosis_type = Column(String(50), comment="诊断类型")
    
    # 诊断状态 - 匹配数据库字段名
    diagnosis_status = Column(Enum(DiagnosisStatus), nullable=False, comment="诊断状态")
    score = Column(Float, comment="诊断分数")
    threshold = Column(Float, comment="阈值")
    is_abnormal = Column(Boolean, default=False, comment="是否异常")
    
    # 图像信息
    image_url = Column(String(500), comment="图像URL")
    thumbnail_url = Column(String(500), comment="缩略图URL")
    image_timestamp = Column(DateTime(timezone=True), comment="图像时间戳")
    
    # 处理信息
    processing_time = Column(Float, comment="处理时间(ms)")
    error_message = Column(Text, comment="错误信息")
    suggestions = Column(JSON, default=list, comment="建议")
    metrics = Column(JSON, default=dict, comment="指标数据")
    
    # 检测结果
    result_data = Column(JSON, default=dict, comment="详细结果数据")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    
    def __repr__(self):
        return f"<DiagnosisResult(id={self.id}, camera_id={self.camera_id}, type='{self.diagnosis_type}', status='{self.diagnosis_status}')>"

class DiagnosisAlarm(Base):
    __tablename__ = "diagnosis_alarms"
    
    id = Column(Integer, primary_key=True, index=True)
    result_id = Column(Integer, nullable=False, comment="诊断结果ID")
    
    # 告警信息
    alarm_type = Column(String(50), nullable=False, comment="告警类型")
    severity = Column(String(20), default="warning", comment="严重程度")
    title = Column(String(200), nullable=False, comment="告警标题")
    description = Column(Text, comment="告警描述")
    
    # 阈值配置
    threshold_config = Column(JSON, default=dict, comment="阈值配置")
    current_value = Column(Float, comment="当前值")
    threshold_value = Column(Float, comment="阈值")
    
    # 确认状态
    is_acknowledged = Column(Boolean, default=False, comment="是否已确认")
    acknowledged_by = Column(Integer, comment="确认人ID")
    acknowledged_at = Column(DateTime(timezone=True), comment="确认时间")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")

class DiagnosisTemplate(Base):
    __tablename__ = "diagnosis_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, comment="模板名称")
    description = Column(Text, comment="模板描述")
    
    # 模板配置 - 匹配实际数据库结构
    diagnosis_types = Column(JSON, default=list, comment="诊断类型列表")
    default_config = Column(JSON, default=dict, comment="默认配置")
    default_schedule = Column(JSON, default=dict, comment="默认调度配置")
    threshold_config = Column(JSON, default=dict, comment="阈值配置")
    
    # 状态 - 匹配实际数据库结构
    is_active = Column(Boolean, default=True, comment="是否启用")
    is_system = Column(Boolean, default=False, comment="是否系统模板")
    
    # 使用统计
    usage_count = Column(Integer, default=0, comment="使用次数")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")
    created_by = Column(String(50), comment="创建人ID")

class DiagnosisStatistics(Base):
    __tablename__ = "diagnosis_statistics"
    
    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime(timezone=True), nullable=False, comment="统计日期")
    
    # 统计维度
    camera_id = Column(Integer, comment="摄像头ID")
    diagnosis_type = Column(String(50), comment="诊断类型")
    
    # 统计数据
    total_checks = Column(Integer, default=0, comment="总检查次数")
    normal_count = Column(Integer, default=0, comment="正常次数")
    warning_count = Column(Integer, default=0, comment="警告次数")
    error_count = Column(Integer, default=0, comment="错误次数")
    critical_count = Column(Integer, default=0, comment="严重次数")
    
    # 性能指标
    avg_score = Column(Float, comment="平均分数")
    min_score = Column(Float, comment="最低分数")
    max_score = Column(Float, comment="最高分数")
    avg_processing_time = Column(Float, comment="平均处理时间")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")