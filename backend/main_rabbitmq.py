from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from contextlib import asynccontextmanager
import uvicorn
import asyncio
from routers import auth, users, cameras, ai_algorithms, events, system, files, messages, alarm_rules, notification_channels, dashboard, event_tasks
from routers import diagnosis_rabbitmq as diagnosis
from database import init_db
from config import settings
from utils.camera_monitor import camera_monitor
from tasks import start_metrics_collection, stop_metrics_collection
from ai_service_monitor import AIServiceMonitor
from middleware.dependency_logging_middleware import DependencyLoggingMiddleware
from middleware.logging_middleware import SystemLoggingMiddleware

# 导入RabbitMQ相关组件
from diagnosis.rabbitmq_scheduler import RabbitMQTaskScheduler
from rabbitmq_event_task_manager import RabbitMQEventTaskManager
from task_queue_manager import TaskQueueManager

# 全局AI服务监控器实例
ai_service_monitor = AIServiceMonitor()

# 初始化RabbitMQ组件
task_queue_manager = TaskQueueManager()
rabbitmq_scheduler = RabbitMQTaskScheduler()
rabbitmq_event_manager = RabbitMQEventTaskManager()

# 应用生命周期管理
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时初始化数据库
    await init_db()
    
    # 初始化RabbitMQ任务队列管理器
    try:
        await task_queue_manager.connect()
        print("RabbitMQ任务队列管理器已连接")
    except Exception as e:
        print(f"RabbitMQ连接失败: {e}")
        raise
    
    # 初始化RabbitMQ诊断调度器
    try:
        await rabbitmq_scheduler.start()
        print("RabbitMQ诊断任务调度器已启动")
    except Exception as e:
        print(f"RabbitMQ诊断调度器启动失败: {e}")
    
    # 启动摄像头监控服务
    asyncio.create_task(periodic_camera_monitor())
    
    # 启动AI服务监控器
    try:
        asyncio.create_task(ai_service_monitor.start())
        print("AI服务监控器已启动")
    except Exception as e:
        print(f"AI服务监控器启动失败: {e}")
    
    # 启动RabbitMQ事件任务管理器
    try:
        asyncio.create_task(rabbitmq_event_manager.start())
        print("RabbitMQ事件任务管理器已启动")
    except Exception as e:
        print(f"RabbitMQ事件任务管理器启动失败: {e}")
    
    # 启动系统指标收集器
    try:
        asyncio.create_task(start_metrics_collection())
        print("系统指标收集器已启动")
    except Exception as e:
        print(f"系统指标收集器启动失败: {e}")
    
    yield
    
    # 关闭时的清理工作
    try:
        await rabbitmq_scheduler.stop()
        print("RabbitMQ诊断调度器已关闭")
    except Exception as e:
        print(f"RabbitMQ诊断调度器关闭失败: {e}")
    
    try:
        await rabbitmq_event_manager.stop()
        print("RabbitMQ事件任务管理器已关闭")
    except Exception as e:
        print(f"RabbitMQ事件任务管理器关闭失败: {e}")
    
    try:
        await ai_service_monitor.stop()
        print("AI服务监控器已关闭")
    except Exception as e:
        print(f"AI服务监控器关闭失败: {e}")
        
    try:
        await stop_metrics_collection()
        print("系统指标收集器已关闭")
    except Exception as e:
        print(f"系统指标收集器关闭失败: {e}")
    
    try:
        await task_queue_manager.close()
        print("RabbitMQ连接已关闭")
    except Exception as e:
        print(f"RabbitMQ连接关闭失败: {e}")

async def periodic_camera_monitor():
    """定期监控摄像头状态"""
    while True:
        try:
            await camera_monitor.monitor_all_cameras()
            # 每30秒检查一次摄像头状态
            await asyncio.sleep(30)
        except Exception as e:
            print(f"Camera monitor error: {e}")
            # 出错时等待60秒再重试
            await asyncio.sleep(60)

# 创建FastAPI应用实例
app = FastAPI(
    title="EasySight 智能安防平台 (RabbitMQ版)",
    description="基于RabbitMQ的通用分布式智能安防平台 API",
    version="1.0.0-rabbitmq",
    lifespan=lifespan
)

# 添加完善的日志中间件
# 中间件会自动从配置类读取环境变量
app.add_middleware(SystemLoggingMiddleware)
# app.add_middleware(DependencyLoggingMiddleware)# 配置CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 安全认证
security = HTTPBearer()

# 设置RabbitMQ组件依赖
diagnosis.set_rabbitmq_components(task_queue_manager, rabbitmq_scheduler)

# 注册路由
app.include_router(auth.router, prefix="/api/v1/auth", tags=["认证"])
app.include_router(users.router, prefix="/api/v1/users", tags=["用户管理"])
app.include_router(cameras.router, prefix="/api/v1/cameras", tags=["摄像头管理"])
app.include_router(ai_algorithms.router, prefix="/api/v1/ai", tags=["AI应用中心"])
app.include_router(events.router, prefix="/api/v1/events", tags=["事件告警中心"])
app.include_router(event_tasks.router, prefix="/api/v1/event-tasks", tags=["事件任务管理"])
app.include_router(system.router, prefix="/api/v1/system", tags=["系统配置"])
app.include_router(dashboard.router, prefix="/api/v1/dashboard", tags=["仪表盘"])
app.include_router(diagnosis.router, prefix="/api/v1/diagnosis", tags=["智能诊断"])
# 注册无认证的Worker API路由
app.include_router(diagnosis.no_auth_router, prefix="/api/v1/diagnosis/worker", tags=["Worker无认证API"])
app.include_router(messages.router, tags=["消息管理"])

# 导入角色管理路由
from routers.roles import router as roles_router
app.include_router(roles_router, prefix="/api/v1/roles", tags=["角色管理"])

# 注册文件管理路由
app.include_router(files.router, prefix="/api/v1/files", tags=["文件管理"])

# 注册告警规则和通知渠道路由
app.include_router(alarm_rules.router, tags=["告警规则"])
app.include_router(notification_channels.router, tags=["通知渠道"])

# 添加RabbitMQ状态检查接口
@app.get("/api/v1/rabbitmq/status")
async def rabbitmq_status():
    """获取RabbitMQ连接状态"""
    try:
        is_connected = task_queue_manager.is_connected()
        queue_stats = await task_queue_manager.get_queue_info('diagnosis_tasks')
        return {
            "status": "connected" if is_connected else "disconnected",
            "queue_stats": queue_stats
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

@app.get("/")
async def root():
    return {
        "message": "EasySight 智能安防平台 API (RabbitMQ版)", 
        "version": "1.0.0-rabbitmq",
        "features": ["RabbitMQ任务队列", "实时任务分发", "事件驱动架构"]
    }

@app.get("/health")
async def health_check():
    rabbitmq_status = "connected" if task_queue_manager.is_connected() else "disconnected"
    return {
        "status": "healthy", 
        "message": "服务运行正常",
        "rabbitmq": rabbitmq_status
    }

if __name__ == "__main__":
    uvicorn.run(
        "main_rabbitmq:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )