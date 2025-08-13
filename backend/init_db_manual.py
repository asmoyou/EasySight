from sqlalchemy import create_engine
from database import Base
from config import settings
from models.user import User, UserSession, UserLoginLog
from models.camera import Camera, CameraGroup, MediaProxy, CameraPreset
from models.ai_algorithm import AIAlgorithm, AIService, AIModel, AIServiceLog
from models.event import Event, EventRule, EventNotification, EventStatistics
from models.event_task import EventTask, EventTaskLog, EventTaskRecovery
from models.system import SystemConfig, SystemVersion, DataRetentionPolicy, MessageCenter, SystemLog, SystemMetrics, License
from models.diagnosis import DiagnosisTask, DiagnosisResult, DiagnosisAlarm, DiagnosisTemplate, DiagnosisStatistics

def init_database():
    """手动初始化数据库表结构"""
    try:
        # 直接使用连接参数创建引擎
        from urllib.parse import quote_plus
        password = quote_plus('RotaNova@2025')
        engine = create_engine(
            f'postgresql+psycopg2://rotanova:{password}@127.0.0.1:5432/easysight'
        )
        
        # 创建所有表
        Base.metadata.create_all(bind=engine)
        
        print("Database tables created successfully!")
        
        # 检查创建的表
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print(f"Created tables: {tables}")
        
    except Exception as e:
        print(f"Error creating database tables: {e}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    init_database()