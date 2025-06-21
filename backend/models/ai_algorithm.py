from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, Float, Enum
from sqlalchemy.sql import func
from database import Base
import enum

class AlgorithmType(enum.Enum):
    OBJECT_DETECTION = "object_detection"
    FACE_RECOGNITION = "face_recognition"
    BEHAVIOR_ANALYSIS = "behavior_analysis"
    VEHICLE_DETECTION = "vehicle_detection"
    INTRUSION_DETECTION = "intrusion_detection"
    FIRE_DETECTION = "fire_detection"
    SMOKE_DETECTION = "smoke_detection"
    CROWD_ANALYSIS = "crowd_analysis"
    ABNORMAL_BEHAVIOR = "abnormal_behavior"
    CUSTOM = "custom"

class AlgorithmStatus(enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    DEPRECATED = "deprecated"
    TESTING = "testing"

class ServiceStatus(enum.Enum):
    STOPPED = "stopped"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"
    STARTING = "starting"
    STOPPING = "stopping"

class ModelType(enum.Enum):
    PYTORCH = "pytorch"
    TENSORFLOW = "tensorflow"
    ONNX = "onnx"
    TENSORRT = "tensorrt"
    OPENVINO = "openvino"
    CUSTOM = "custom"

class AIAlgorithm(Base):
    __tablename__ = "ai_algorithms"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, comment="算法名称")
    code = Column(String(50), unique=True, index=True, nullable=False, comment="算法编码")
    version = Column(String(20), nullable=False, comment="算法版本")
    
    # 基本信息
    description = Column(Text, comment="算法描述")
    author = Column(String(100), comment="算法作者")
    algorithm_type = Column(Enum(AlgorithmType), nullable=False, comment="算法类型")
    
    # 文件信息
    file_path = Column(String(500), comment="算法文件路径")
    file_size = Column(Integer, comment="文件大小(字节)")
    file_hash = Column(String(64), comment="文件哈希值")
    
    # 配置信息
    config_schema = Column(JSON, default=dict, comment="配置参数模式")
    default_config = Column(JSON, default=dict, comment="默认配置参数")
    
    # 性能指标
    accuracy = Column(Float, comment="准确率")
    precision = Column(Float, comment="精确率")
    recall = Column(Float, comment="召回率")
    f1_score = Column(Float, comment="F1分数")
    inference_time = Column(Float, comment="推理时间(ms)")
    
    # 资源需求
    min_memory = Column(Integer, comment="最小内存需求(MB)")
    min_gpu_memory = Column(Integer, comment="最小GPU内存需求(MB)")
    cpu_cores = Column(Integer, comment="CPU核心数需求")
    gpu_required = Column(Boolean, default=False, comment="是否需要GPU")
    
    # 状态信息
    status = Column(Enum(AlgorithmStatus), default=AlgorithmStatus.DRAFT, comment="算法状态")
    is_active = Column(Boolean, default=True, comment="是否启用")
    download_count = Column(Integer, default=0, comment="下载次数")
    usage_count = Column(Integer, default=0, comment="使用次数")
    
    # 标签和分类
    tags = Column(JSON, default=list, comment="标签列表")
    categories = Column(JSON, default=list, comment="分类列表")
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")
    published_at = Column(DateTime(timezone=True), comment="发布时间")
    
    def __repr__(self):
        return f"<AIAlgorithm(id={self.id}, name='{self.name}', version='{self.version}', type='{self.algorithm_type}')>"

class AIService(Base):
    __tablename__ = "ai_services"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, comment="服务名称")
    camera_id = Column(Integer, nullable=False, comment="摄像头ID")
    algorithm_id = Column(Integer, nullable=False, comment="算法ID")
    
    # 配置信息
    config = Column(JSON, default=dict, comment="算法配置参数")
    roi_areas = Column(JSON, default=list, comment="感兴趣区域")
    
    # 生效时间配置
    schedule_config = Column(JSON, default=dict, comment="时间调度配置")
    is_24x7 = Column(Boolean, default=True, comment="是否24小时运行")
    
    # 告警配置
    alarm_enabled = Column(Boolean, default=True, comment="是否启用告警")
    alarm_threshold = Column(Float, default=0.8, comment="告警阈值")
    alarm_config = Column(JSON, default=dict, comment="告警配置")
    
    # 状态信息
    is_active = Column(Boolean, default=True, comment="是否启用")
    is_running = Column(Boolean, default=False, comment="是否运行中")
    last_detection_time = Column(DateTime(timezone=True), comment="最后检测时间")
    
    # 统计信息
    total_detections = Column(Integer, default=0, comment="总检测次数")
    total_alarms = Column(Integer, default=0, comment="总告警次数")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    description = Column(Text, comment="服务描述")

class AIModel(Base):
    __tablename__ = "ai_models"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, comment="模型名称")
    algorithm_id = Column(Integer, nullable=False, comment="所属算法ID")
    
    # 模型文件信息
    model_path = Column(String(500), comment="模型文件路径")
    model_size = Column(Integer, comment="模型文件大小")
    model_format = Column(String(20), comment="模型格式(onnx, pytorch, tensorflow等)")
    
    # 模型参数
    input_shape = Column(JSON, comment="输入形状")
    output_shape = Column(JSON, comment="输出形状")
    class_names = Column(JSON, default=list, comment="类别名称列表")
    
    # 训练信息
    training_dataset = Column(String(200), comment="训练数据集")
    training_epochs = Column(Integer, comment="训练轮数")
    training_accuracy = Column(Float, comment="训练准确率")
    validation_accuracy = Column(Float, comment="验证准确率")
    
    is_active = Column(Boolean, default=True, comment="是否启用")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")

class AIServiceLog(Base):
    __tablename__ = "ai_service_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    service_id = Column(Integer, nullable=False, comment="AI服务ID")
    camera_id = Column(Integer, nullable=False, comment="摄像头ID")
    algorithm_id = Column(Integer, nullable=False, comment="算法ID")
    
    # 检测结果
    detection_result = Column(JSON, comment="检测结果")
    confidence_score = Column(Float, comment="置信度分数")
    processing_time = Column(Float, comment="处理时间(ms)")
    
    # 图像信息
    image_path = Column(String(500), comment="图像文件路径")
    image_timestamp = Column(DateTime(timezone=True), comment="图像时间戳")
    
    # 是否触发告警
    is_alarm = Column(Boolean, default=False, comment="是否触发告警")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")