import os
from typing import Optional
from pydantic_settings import BaseSettings

class WorkerConfig(BaseSettings):
    """Worker节点配置"""
    
    # 节点基本信息
    node_id: Optional[str] = None
    node_name: str = "worker-node"
    
    # Worker池配置
    worker_pool_size: int = 12
    max_concurrent_tasks: int = 12
    
    # 主节点连接配置
    master_host: str = "localhost"
    master_port: int = 8000
    master_api_base: str = "/api/v1/diagnosis"
    
    # 数据库连接配置（如果worker需要直接访问数据库）
    database_url: Optional[str] = None
    
    # Redis配置（用于任务队列和节点通信）
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: Optional[str] = None
    
    # 心跳配置
    heartbeat_interval: int = 30  # 秒
    heartbeat_timeout: int = 90   # 秒
    
    # 任务拉取配置
    task_poll_interval: int = 5   # 秒
    task_batch_size: int = 1      # 每次拉取的任务数量
    
    # 日志配置
    log_level: str = "INFO"
    log_file: Optional[str] = None
    
    # 安全配置
    api_token: Optional[str] = None
    
    class Config:
        env_prefix = "WORKER_"
        env_file = ".env"

# 全局配置实例
worker_config = WorkerConfig()

# 生成节点ID
def generate_node_id() -> str:
    """生成基于机器特征的稳定节点ID"""
    import socket
    import hashlib
    import platform
    
    # 使用主机名和MAC地址生成稳定的节点ID
    hostname = socket.gethostname()
    try:
        import uuid
        mac = hex(uuid.getnode())[2:]
    except:
        mac = "unknown"
    
    # 创建稳定的哈希值
    unique_string = f"{hostname}-{mac}-{platform.machine()}"
    hash_value = hashlib.md5(unique_string.encode()).hexdigest()[:8]
    return f"{hostname}-{hash_value}"

# 初始化配置
if not worker_config.node_id:
    worker_config.node_id = generate_node_id()