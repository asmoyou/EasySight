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
    PENDING = "pending"  # 待执行
    RUNNING = "running"  # 运行中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"  # 失败
    CANCELLED = "cancelled"  # 已取消

class DiagnosisTask(Base):
    __tablename__ = "diagnosis_tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, comment="任务名称")
    description = Column(Text, comment="任务描述")
    
    # 目标设备
    camera_ids = Column(JSON, default=list, comment="摄像头ID列表")
    camera_groups = Column(JSON, default=list, comment="摄像头分组列表")
    
    # 诊断配置
    diagnosis_types = Column(JSON, default=list, comment="诊断类型列表")
    diagnosis_config = Column(JSON, default=dict, comment="诊断配置参数")
    
    # 调度配置
    schedule_type = Column(String(20), default="manual", comment="调度类型(manual, cron, interval)")
    schedule_config = Column(JSON, default=dict, comment="调度配置")
    cron_expression = Column(String(100), comment="Cron表达式")
    interval_minutes = Column(Integer, comment="间隔分钟数")
    
    # 阈值配置
    threshold_config = Column(JSON, default=dict, comment="阈值配置")
    
    # 状态信息
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING, comment="任务状态")
    is_active = Column(Boolean, default=True, comment="是否启用")
    
    # 执行信息
    last_run_time = Column(DateTime(timezone=True), comment="最后执行时间")
    next_run_time = Column(DateTime(timezone=True), comment="下次执行时间")
    total_runs = Column(Integer, default=0, comment="总执行次数")
    success_runs = Column(Integer, default=0, comment="成功执行次数")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")
    created_by = Column(String(100), comment="创建人")
    
    def __repr__(self):
        return f"<DiagnosisTask(id={self.id}, name='{self.name}', status='{self.status}')>"

class DiagnosisResult(Base):
    __tablename__ = "diagnosis_results"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, nullable=False, comment="诊断任务ID")
    camera_id = Column(Integer, nullable=False, comment="摄像头ID")
    camera_name = Column(String(100), comment="摄像头名称")
    
    # 诊断信息
    diagnosis_type = Column(Enum(DiagnosisType), nullable=False, comment="诊断类型")
    diagnosis_status = Column(Enum(DiagnosisStatus), nullable=False, comment="诊断状态")
    
    # 检测结果
    score = Column(Float, comment="诊断分数")
    threshold = Column(Float, comment="阈值")
    is_abnormal = Column(Boolean, default=False, comment="是否异常")
    
    # 详细结果
    result_data = Column(JSON, default=dict, comment="详细结果数据")
    metrics = Column(JSON, default=dict, comment="指标数据")
    
    # 图像信息
    image_url = Column(String(500), comment="检测图像URL")
    thumbnail_url = Column(String(500), comment="缩略图URL")
    image_timestamp = Column(DateTime(timezone=True), comment="图像时间戳")
    
    # 处理信息
    processing_time = Column(Float, comment="处理时间(ms)")
    error_message = Column(Text, comment="错误信息")
    
    # 建议信息
    suggestions = Column(JSON, default=list, comment="改进建议")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    
    def __repr__(self):
        return f"<DiagnosisResult(id={self.id}, camera_id={self.camera_id}, type='{self.diagnosis_type}', status='{self.diagnosis_status}')>"

class DiagnosisAlarm(Base):
    __tablename__ = "diagnosis_alarms"
    
    id = Column(Integer, primary_key=True, index=True)
    result_id = Column(Integer, nullable=False, comment="诊断结果ID")
    task_id = Column(Integer, nullable=False, comment="诊断任务ID")
    camera_id = Column(Integer, nullable=False, comment="摄像头ID")
    
    # 告警信息
    alarm_type = Column(Enum(DiagnosisType), nullable=False, comment="告警类型")
    alarm_level = Column(String(20), default="warning", comment="告警级别")
    title = Column(String(200), nullable=False, comment="告警标题")
    description = Column(Text, comment="告警描述")
    
    # 设备信息
    camera_name = Column(String(100), comment="摄像头名称")
    camera_location = Column(String(200), comment="摄像头位置")
    
    # 检测数据
    detection_score = Column(Float, comment="检测分数")
    threshold_value = Column(Float, comment="阈值")
    
    # 媒体文件
    thumbnail_url = Column(String(500), comment="缩略图URL")
    image_urls = Column(JSON, default=list, comment="相关图片URL列表")
    
    # 状态信息
    is_read = Column(Boolean, default=False, comment="是否已读")
    is_resolved = Column(Boolean, default=False, comment="是否已解决")
    resolved_by = Column(String(100), comment="解决人")
    resolved_at = Column(DateTime(timezone=True), comment="解决时间")
    resolution_notes = Column(Text, comment="解决备注")
    
    # 通知状态
    is_notified = Column(Boolean, default=False, comment="是否已通知")
    notification_sent_at = Column(DateTime(timezone=True), comment="通知发送时间")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")

class DiagnosisTemplate(Base):
    __tablename__ = "diagnosis_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, comment="模板名称")
    description = Column(Text, comment="模板描述")
    
    # 模板配置
    diagnosis_types = Column(JSON, default=list, comment="诊断类型列表")
    default_config = Column(JSON, default=dict, comment="默认配置")
    threshold_config = Column(JSON, default=dict, comment="阈值配置")
    
    # 调度配置
    default_schedule = Column(JSON, default=dict, comment="默认调度配置")
    
    # 状态
    is_active = Column(Boolean, default=True, comment="是否启用")
    is_system = Column(Boolean, default=False, comment="是否系统模板")
    
    # 使用统计
    usage_count = Column(Integer, default=0, comment="使用次数")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")
    created_by = Column(String(100), comment="创建人")

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