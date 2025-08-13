from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON, Enum
from sqlalchemy.sql import func
from database import Base
import enum

class WorkerStatus(enum.Enum):
    ONLINE = "online"      # 在线
    OFFLINE = "offline"    # 离线
    BUSY = "busy"          # 忙碌
    ERROR = "error"        # 错误
    MAINTENANCE = "maintenance"  # 维护中

class Worker(Base):
    """Worker节点模型"""
    __tablename__ = "workers"
    
    id = Column(Integer, primary_key=True, index=True)
    worker_id = Column(String(100), unique=True, nullable=False, comment="Worker唯一标识")
    host = Column(String(100), nullable=False, comment="主机地址")
    port = Column(Integer, nullable=False, comment="端口号")
    
    # 能力配置
    max_concurrent_tasks = Column(Integer, default=3, comment="最大并发任务数")
    current_tasks = Column(Integer, default=0, comment="当前任务数")
    capabilities = Column(JSON, default=list, comment="支持的能力列表")
    
    # 状态信息
    status = Column(Enum(WorkerStatus), default=WorkerStatus.OFFLINE, comment="Worker状态")
    last_heartbeat = Column(DateTime(timezone=True), comment="最后心跳时间")
    
    # 统计信息
    total_tasks_processed = Column(Integer, default=0, comment="总处理任务数")
    successful_tasks = Column(Integer, default=0, comment="成功任务数")
    failed_tasks = Column(Integer, default=0, comment="失败任务数")
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    def __repr__(self):
        return f"<Worker(worker_id='{self.worker_id}', status='{self.status}', host='{self.host}:{self.port}')>"
    
    @property
    def is_available(self):
        """检查Worker是否可用"""
        return (
            self.status == WorkerStatus.ONLINE and 
            self.current_tasks < self.max_concurrent_tasks
        )
    
    @property
    def load_percentage(self):
        """获取负载百分比"""
        if self.max_concurrent_tasks == 0:
            return 0
        return (self.current_tasks / self.max_concurrent_tasks) * 100
    
    @property
    def success_rate(self):
        """获取成功率"""
        if self.total_tasks_processed == 0:
            return 0
        return (self.successful_tasks / self.total_tasks_processed) * 100