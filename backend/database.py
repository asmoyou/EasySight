from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from redis import Redis
from minio import Minio
import aio_pika
from config import settings
import logging

logger = logging.getLogger(__name__)

# 异步数据库引擎
async_engine = create_async_engine(
    settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"),
    echo=settings.DEBUG,
    pool_pre_ping=True,
    pool_recycle=300
)

# 异步会话工厂
AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# 同步数据库引擎（用于Alembic迁移）
sync_engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    pool_recycle=300
)

# 同步会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)

# 数据库基类
Base = declarative_base()
metadata = MetaData()

# Redis连接
redis_client = Redis.from_url(settings.REDIS_URL, decode_responses=True)

# MinIO客户端
minio_client = Minio(
    settings.MINIO_ENDPOINT,
    access_key=settings.MINIO_ACCESS_KEY,
    secret_key=settings.MINIO_SECRET_KEY,
    secure=settings.MINIO_SECURE
)

# 数据库依赖注入
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            raise
        finally:
            await session.close()

# Redis依赖注入
def get_redis():
    return redis_client

# MinIO依赖注入
def get_minio():
    return minio_client

# RabbitMQ连接
async def get_rabbitmq_connection():
    try:
        connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
        return connection
    except Exception as e:
        logger.error(f"Failed to connect to RabbitMQ: {e}")
        raise

# 初始化数据库
async def init_db():
    """初始化数据库表和基础数据"""
    try:
        # 导入所有模型以确保它们被注册
        from models.user import User, UserSession, UserLoginLog
        from models.role import Role, Permission, UserRole
        from models.camera import Camera, CameraGroup, CameraGroupMember
        from models.ai_algorithm import AIAlgorithm, AIModel, AIService
        from models.event import Event, EventRule, EventNotification
        from models.diagnosis import DiagnosisTask, DiagnosisResult, DiagnosisAlarm, DiagnosisTemplate
        from models.system import SystemConfig, SystemVersion, DataRetentionPolicy, MessageCenter, SystemLog, SystemMetrics, License
        
        # 创建所有表
        try:
            async with async_engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.warning(f"Database connection failed: {e}")
        
        # 初始化MinIO存储桶
        try:
            if not minio_client.bucket_exists(settings.MINIO_BUCKET_NAME):
                minio_client.make_bucket(settings.MINIO_BUCKET_NAME)
                logger.info(f"Created MinIO bucket: {settings.MINIO_BUCKET_NAME}")
        except Exception as e:
            logger.warning(f"MinIO connection failed: {e}")
        
        # 测试Redis连接
        try:
            redis_client.ping()
            logger.info("Redis connection successful")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}")
        
        logger.info("Database initialization completed")
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        # 不再抛出异常，允许应用继续启动
        pass

# 关闭数据库连接
async def close_db():
    """关闭数据库连接"""
    await async_engine.dispose()
    redis_client.close()