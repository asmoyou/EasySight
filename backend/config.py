from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # 数据库配置
    DATABASE_URL: str = "postgresql://rotanova:RotaNova%402025@127.0.0.1:5432/easysight"
    
    # Redis配置
    REDIS_URL: str = "redis://127.0.0.1:6379/0"
    
    # MinIO配置
    MINIO_ENDPOINT: str = "127.0.0.1:9000"
    MINIO_ACCESS_KEY: str = "rotanova"
    MINIO_SECRET_KEY: str = "RotaNova@2025"
    MINIO_BUCKET_NAME: str = "easysight"
    MINIO_SECURE: bool = False
    
    # RabbitMQ配置
    RABBITMQ_URL: str = "amqp://rotanova:RotaNova@2025@127.0.0.1:5672/"
    
    # JWT配置
    SECRET_KEY: str = "your-secret-key-here-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # 应用配置
    APP_NAME: str = "EasySight"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # 文件上传配置
    MAX_FILE_SIZE: int = 100 * 1024 * 1024  # 100MB
    ALLOWED_FILE_TYPES: list = [".jpg", ".jpeg", ".png", ".mp4", ".avi", ".mov"]
    
    # 分页配置
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100
    
    # 多语言配置
    DEFAULT_LANGUAGE: str = "zh-CN"
    SUPPORTED_LANGUAGES: list = ["zh-CN", "en-US"]
    
    # 数据保留配置
    DEFAULT_DATA_RETENTION_DAYS: int = 30
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()