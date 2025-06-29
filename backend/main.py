from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from contextlib import asynccontextmanager
import uvicorn
import asyncio
import logging
from routers import auth, users, cameras, ai_algorithms, events, system, diagnosis, files, messages
from database import init_db
from config import settings
from utils.camera_monitor import camera_monitor

# 全局任务管理
background_tasks = set()

# 摄像头状态监控任务
async def camera_monitoring_task():
    """摄像头状态监控后台任务"""
    while True:
        try:
            await camera_monitor.monitor_all_cameras()
            # 每30秒检查一次
            await asyncio.sleep(30)
        except Exception as e:
            logging.error(f"Camera monitoring task error: {e}")
            await asyncio.sleep(60)  # 出错时等待更长时间

# 应用生命周期管理
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时初始化数据库
    await init_db()
    
    # 启动摄像头监控任务
    task = asyncio.create_task(camera_monitoring_task())
    background_tasks.add(task)
    task.add_done_callback(background_tasks.discard)
    
    logging.info("Camera monitoring task started")
    
    yield
    
    # 关闭时的清理工作
    for task in background_tasks:
        task.cancel()
    await asyncio.gather(*background_tasks, return_exceptions=True)
    logging.info("Background tasks stopped")

# 创建FastAPI应用实例
app = FastAPI(
    title="EasySight 智能安防平台",
    description="通用分布式智能安防平台 API",
    version="1.0.0",
    lifespan=lifespan
)

# 配置CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 安全认证
security = HTTPBearer()

# 注册路由
app.include_router(auth.router, prefix="/api/v1/auth", tags=["认证"])
app.include_router(users.router, prefix="/api/v1/users", tags=["用户管理"])
app.include_router(cameras.router, prefix="/api/v1/cameras", tags=["摄像头管理"])
app.include_router(ai_algorithms.router, prefix="/api/v1/ai", tags=["AI应用中心"])
app.include_router(events.router, prefix="/api/v1/events", tags=["事件告警中心"])
app.include_router(system.router, prefix="/api/v1/system", tags=["系统配置"])
app.include_router(diagnosis.router, prefix="/api/v1/diagnosis", tags=["智能诊断"])
app.include_router(messages.router, tags=["消息管理"])

# 导入角色管理路由
from routers.roles import router as roles_router
app.include_router(roles_router, prefix="/api/v1/roles", tags=["角色管理"])

# 注册文件管理路由
app.include_router(files.router, prefix="/api/v1/files", tags=["文件管理"])

@app.get("/")
async def root():
    return {"message": "EasySight 智能安防平台 API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "服务运行正常"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )