from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, Float, Enum
from sqlalchemy.sql import func
from database import Base
import enum

class CameraStatus(enum.Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    MAINTENANCE = "maintenance"
    ERROR = "error"

class CameraType(enum.Enum):
    IP_CAMERA = "ip_camera"
    ANALOG_CAMERA = "analog_camera"
    USB_CAMERA = "usb_camera"
    RTSP_STREAM = "rtsp_stream"
    HTTP_STREAM = "http_stream"

class Camera(Base):
    __tablename__ = "cameras"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, index=True, nullable=False, comment="摄像头编码")
    name = Column(String(100), nullable=False, comment="摄像头名称")
    
    # 视频源配置
    stream_url = Column(String(500), nullable=False, comment="视频源地址")
    backup_stream_url = Column(String(500), comment="备用视频源地址")
    camera_type = Column(Enum(CameraType), default=CameraType.IP_CAMERA, comment="摄像头类型")
    
    # 媒体代理配置
    media_proxy_id = Column(Integer, comment="媒体代理ID")
    media_proxy_name = Column(String(100), comment="媒体代理名称")
    
    # 位置信息
    location = Column(String(200), comment="安装位置")
    longitude = Column(Float, comment="经度")
    latitude = Column(Float, comment="纬度")
    altitude = Column(Float, comment="海拔")
    
    # 设备信息
    manufacturer = Column(String(100), comment="制造商")
    model = Column(String(100), comment="型号")
    firmware_version = Column(String(50), comment="固件版本")
    ip_address = Column(String(45), comment="IP地址")
    port = Column(Integer, comment="端口")
    username = Column(String(50), comment="用户名")
    password = Column(String(100), comment="密码")
    
    # 视频参数
    resolution = Column(String(20), comment="分辨率")
    frame_rate = Column(Integer, comment="帧率")
    bitrate = Column(Integer, comment="码率")
    
    # 状态信息
    status = Column(Enum(CameraStatus), default=CameraStatus.OFFLINE, comment="设备状态")
    is_active = Column(Boolean, default=True, comment="是否启用")
    is_recording = Column(Boolean, default=False, comment="是否录像")
    
    # 自定义属性
    custom_attributes = Column(JSON, default=dict, comment="自定义属性标签与数值")
    
    # 告警配置
    alarm_enabled = Column(Boolean, default=True, comment="是否启用告警")
    alarm_config = Column(JSON, default=dict, comment="告警配置")
    
    # 时间戳
    last_heartbeat = Column(DateTime(timezone=True), comment="最后心跳时间")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 备注信息
    description = Column(Text, comment="设备描述")
    
    def __repr__(self):
        return f"<Camera(id={self.id}, code='{self.code}', name='{self.name}', status='{self.status}')>"

class CameraGroup(Base):
    __tablename__ = "camera_groups"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, comment="分组名称")
    description = Column(Text, comment="分组描述")
    camera_ids = Column(JSON, default=list, comment="摄像头ID列表")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")

class MediaProxy(Base):
    __tablename__ = "media_proxies"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, comment="节点名称")
    ip_address = Column(String(45), nullable=False, comment="节点IP")
    port = Column(Integer, nullable=False, comment="节点端口")
    secret_key = Column(String(255), comment="密钥")
    
    # 状态信息
    is_online = Column(Boolean, default=False, comment="在线状态")
    cpu_usage = Column(Float, comment="CPU使用率")
    memory_usage = Column(Float, comment="内存使用率")
    bandwidth_usage = Column(Float, comment="带宽使用率")
    
    # 配置信息
    max_connections = Column(Integer, default=100, comment="最大连接数")
    current_connections = Column(Integer, default=0, comment="当前连接数")
    
    last_heartbeat = Column(DateTime(timezone=True), comment="最后心跳时间")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    description = Column(Text, comment="节点描述")

class CameraPreset(Base):
    __tablename__ = "camera_presets"
    
    id = Column(Integer, primary_key=True, index=True)
    camera_id = Column(Integer, nullable=False, comment="摄像头ID")
    name = Column(String(100), nullable=False, comment="预置位名称")
    preset_number = Column(Integer, comment="预置位编号")
    
    # PTZ参数
    pan = Column(Float, comment="水平角度")
    tilt = Column(Float, comment="垂直角度")
    zoom = Column(Float, comment="缩放倍数")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")