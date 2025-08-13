from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, Float, Enum, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base
import enum

class EventTaskStatus(enum.Enum):
    PENDING = "PENDING"  # 待启动
    RUNNING = "RUNNING"  # 运行中
    STOPPED = "STOPPED"  # 已停止
    FAILED = "FAILED"    # 失败
    PAUSED = "PAUSED"    # 暂停

class EventTaskType(enum.Enum):
    CONTINUOUS = "CONTINUOUS"  # 连续检测
    SCHEDULED = "SCHEDULED"    # 定时检测
    TRIGGERED = "TRIGGERED"    # 触发检测

class EventTask(Base):
    """事件检测任务模型 - 独立于诊断任务的事件任务管理"""
    __tablename__ = "event_tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String(50), unique=True, index=True, nullable=False, comment="任务唯一标识")
    name = Column(String(100), nullable=False, comment="任务名称")
    description = Column(Text, comment="任务描述")
    
    # 任务类型和状态
    task_type = Column(Enum(EventTaskType), default=EventTaskType.CONTINUOUS, comment="任务类型")
    status = Column(Enum(EventTaskStatus), default=EventTaskStatus.PENDING, comment="任务状态")
    is_active = Column(Boolean, default=True, comment="是否启用")
    
    # 关联的AI服务
    ai_service_id = Column(Integer, ForeignKey('ai_services.id'), nullable=False, comment="AI服务ID")
    camera_id = Column(Integer, nullable=False, comment="摄像头ID")
    camera_name = Column(String(100), comment="摄像头名称")
    
    # 算法配置
    algorithm_id = Column(Integer, comment="算法ID")
    algorithm_name = Column(String(100), comment="算法名称")
    model_id = Column(Integer, comment="模型ID")
    model_name = Column(String(100), comment="模型名称")
    
    # 检测配置
    detection_config = Column(JSON, default=dict, comment="检测配置参数")
    roi_areas = Column(JSON, default=list, comment="感兴趣区域")
    alarm_threshold = Column(Float, default=0.5, comment="告警阈值")
    
    # 调度配置
    schedule_config = Column(JSON, default=dict, comment="调度配置")
    check_interval = Column(Integer, default=5, comment="检测间隔(秒)")
    
    # Worker分配
    assigned_worker = Column(String(100), comment="分配的Worker节点ID")
    worker_heartbeat = Column(DateTime(timezone=True), comment="Worker心跳时间")
    
    # 执行统计
    total_detections = Column(Integer, default=0, comment="总检测次数")
    success_detections = Column(Integer, default=0, comment="成功检测次数")
    failed_detections = Column(Integer, default=0, comment="失败检测次数")
    total_events = Column(Integer, default=0, comment="总事件数")
    
    # 性能统计
    avg_processing_time = Column(Float, comment="平均处理时间(ms)")
    last_detection_time = Column(DateTime(timezone=True), comment="最后检测时间")
    last_event_time = Column(DateTime(timezone=True), comment="最后事件时间")
    
    # 错误信息
    last_error = Column(Text, comment="最后错误信息")
    error_count = Column(Integer, default=0, comment="错误次数")
    
    # 自动恢复配置
    auto_recovery = Column(Boolean, default=True, comment="是否自动恢复")
    max_retry_count = Column(Integer, default=3, comment="最大重试次数")
    retry_count = Column(Integer, default=0, comment="当前重试次数")
    recovery_interval = Column(Integer, default=60, comment="恢复间隔(秒)")
    next_retry_at = Column(DateTime(timezone=True), comment="下次重试时间")
    
    # 时间信息
    started_at = Column(DateTime(timezone=True), comment="启动时间")
    stopped_at = Column(DateTime(timezone=True), comment="停止时间")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")
    created_by = Column(String(50), comment="创建人ID")
    
    # 扩展信息
    task_metadata = Column(JSON, default=dict, comment="扩展元数据")
    tags = Column(JSON, default=list, comment="标签列表")
    
    def __repr__(self):
        return f"<EventTask(id={self.id}, task_id='{self.task_id}', name='{self.name}', status='{self.status}')>"

class EventTaskLog(Base):
    """事件任务执行日志"""
    __tablename__ = "event_task_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey('event_tasks.id'), nullable=False, comment="任务ID")
    
    # 日志类型
    log_type = Column(String(50), nullable=False, comment="日志类型: start, stop, detection, error, recovery")
    log_level = Column(String(20), default="INFO", comment="日志级别")
    
    # 日志内容
    message = Column(Text, nullable=False, comment="日志消息")
    details = Column(JSON, default=dict, comment="详细信息")
    
    # 执行信息
    worker_id = Column(String(100), comment="执行的Worker ID")
    processing_time = Column(Float, comment="处理时间(ms)")
    
    # 检测结果(如果是检测日志)
    detection_result = Column(JSON, default=dict, comment="检测结果")
    event_count = Column(Integer, default=0, comment="检测到的事件数量")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    
    def __repr__(self):
        return f"<EventTaskLog(id={self.id}, task_id={self.task_id}, type='{self.log_type}', level='{self.log_level}')>"

class EventTaskRecovery(Base):
    """事件任务恢复记录"""
    __tablename__ = "event_task_recoveries"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey('event_tasks.id'), nullable=False, comment="任务ID")
    
    # 恢复信息
    recovery_reason = Column(String(100), nullable=False, comment="恢复原因")
    failure_reason = Column(Text, comment="失败原因")
    recovery_action = Column(String(50), comment="恢复动作")
    
    # 恢复结果
    is_successful = Column(Boolean, default=False, comment="是否恢复成功")
    error_message = Column(Text, comment="恢复错误信息")
    
    # 时间信息
    failure_time = Column(DateTime(timezone=True), comment="失败时间")
    recovery_time = Column(DateTime(timezone=True), comment="恢复时间")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    
    def __repr__(self):
        return f"<EventTaskRecovery(id={self.id}, task_id={self.task_id}, successful={self.is_successful}')>"