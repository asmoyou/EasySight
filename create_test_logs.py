import asyncio
import sys
sys.path.append('backend')

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from models.system import SystemLog, LogLevel
from datetime import datetime
from config import Settings

settings = Settings()

async def create_test_logs():
    """创建测试日志数据"""
    # 将postgresql://转换为postgresql+asyncpg://以使用异步驱动
    async_db_url = settings.DATABASE_URL.replace('postgresql://', 'postgresql+asyncpg://')
    engine = create_async_engine(async_db_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # 创建测试日志
        test_logs = [
            SystemLog(
                level=LogLevel.INFO,
                module="system",
                action="user_login",
                message="用户登录成功",
                user_id=1,
                ip_address="192.168.1.100",
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                request_id="req_001",
                extra_data={"login_method": "password"},
                created_at=datetime.now()
            ),
            SystemLog(
                level=LogLevel.WARNING,
                module="camera",
                action="camera_disconnect",
                message="摄像头连接断开",
                ip_address="192.168.1.101",
                extra_data={"camera_id": "cam_001", "reason": "network_timeout"},
                created_at=datetime.now()
            ),
            SystemLog(
                level=LogLevel.ERROR,
                module="ai_algorithm",
                action="detection_failed",
                message="AI检测算法执行失败",
                extra_data={"algorithm_id": "yolo_v5", "error_code": "E001"},
                created_at=datetime.now()
            ),
            SystemLog(
                level=LogLevel.INFO,
                module="system",
                action="config_update",
                message="系统配置更新",
                user_id=1,
                ip_address="192.168.1.100",
                extra_data={"config_key": "max_cameras", "old_value": "10", "new_value": "20"},
                created_at=datetime.now()
            ),
            SystemLog(
                level=LogLevel.DEBUG,
                module="database",
                action="query_executed",
                message="数据库查询执行",
                extra_data={"query_time": "0.05s", "table": "system_logs"},
                created_at=datetime.now()
            )
        ]
        
        for log in test_logs:
            session.add(log)
        
        await session.commit()
        print(f"成功创建 {len(test_logs)} 条测试日志")
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(create_test_logs())