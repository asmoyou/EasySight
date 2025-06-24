from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker
import asyncpg
import config
from utils import logTool
from models import Base

# 设置日志
logger = logTool.StandardLogger('database')

# 异步数据库引擎
async_engine = create_async_engine(
    config.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"),
    echo=config.LOG_DEBUG,
    pool_pre_ping=True,
    pool_recycle=300
)

# 异步会话工厂
AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# 同步数据库引擎（用于初始化）
sync_engine = create_engine(
    config.DATABASE_URL,
    echo=config.LOG_DEBUG,
    pool_pre_ping=True,
    pool_recycle=300
)

# 同步会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)

# 数据库依赖注入
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            await session.close()

# 初始化数据库
async def init_db():
    """初始化数据库表"""
    try:
        # 创建所有表
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise

# 关闭数据库连接
async def close_db():
    """关闭数据库连接"""
    await async_engine.dispose()
    logger.info("Database connections closed")

# 测试数据库连接
async def test_connection():
    """测试数据库连接"""
    try:
        async with AsyncSessionLocal() as session:
            await session.execute("SELECT 1")
        logger.info("Database connection test successful")
        return True
    except Exception as e:
        logger.error(f"Database connection test failed: {e}")
        return False