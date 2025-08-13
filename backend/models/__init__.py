# Models package
from .user import User, UserLoginLog
from .role import Role, Permission, UserRole
from .camera import Camera, MediaProxy
from .system import SystemConfig, SystemLog
from .diagnosis import DiagnosisTask, DiagnosisResult, DiagnosisStatistics, NotificationChannel, AlarmRule
from .event import Event, EventStatistics
from .ai_algorithm import AIAlgorithm, AIService, AIModel, AIServiceLog, AITask

__all__ = [
    'User', 'UserLoginLog',
    'Role', 'Permission', 'UserRole', 
    'Camera', 'MediaProxy',
    'SystemConfig', 'SystemLog',
    'DiagnosisTask', 'DiagnosisResult', 'DiagnosisStatistics', 'NotificationChannel', 'AlarmRule',
    'Event', 'EventStatistics',
    'AIAlgorithm', 'AIService', 'AIModel', 'AIServiceLog', 'AITask'
]