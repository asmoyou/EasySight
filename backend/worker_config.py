import os
from typing import Optional
from pydantic_settings import BaseSettings

class WorkerConfig(BaseSettings):
    """Worker节点配置"""
    
    # 节点基本信息
    node_id: Optional[str] = None
    node_name: str = "worker-node"
    
    # Worker池配置
    worker_pool_size: int = 3
    max_concurrent_tasks: int = 3
    
    # 主节点连接配置
    master_host: str = "localhost"
    master_port: int = 8000
    master_api_base: str = "/api/v1"
    
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
    """生成唯一的节点ID"""
    import socket
    import uuid
    hostname = socket.gethostname()
    return f"{hostname}-{str(uuid.uuid4())[:8]}"

# 初始化配置
if not worker_config.node_id:
    worker_config.node_id = generate_node_id()