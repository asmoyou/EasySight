from fastapi import Request, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from models.system import SystemLog
from models.user import User
from routers.auth import get_current_user_from_token
import time
import uuid
import json
from typing import Optional
from datetime import datetime

class RequestLogger:
    """请求日志记录器"""
    
    def __init__(self):
        # 需要记录日志的路径模式
        self.log_paths = [
            "/api/v1/users",
            "/api/v1/cameras", 
            "/api/v1/ai",
            "/api/v1/events",
            "/api/v1/system",
            "/api/v1/diagnosis",
            "/api/v1/roles",
            "/api/v1/files"
        ]
        
        # 排除的路径
        self.exclude_paths = [
            "/api/v1/auth/login",
            "/api/v1/auth/refresh",
            "/api/v1/diagnosis/worker/heartbeat",  # 排除心跳请求
            "/api/v1/diagnosis/worker/",  # 排除所有worker相关请求
            "/api/v1/messages/unread-count",
            "/health",
            "/docs",
            "/openapi.json"
        ]
        
        # 精确匹配的排除路径（只匹配根路径）
        self.exact_exclude_paths = ["/"]
        
        # 只记录这些HTTP方法
        self.log_methods = ["POST", "PUT", "PATCH", "DELETE"]
        print(f"[请求日志器] 初始化完成 - 监控路径: {self.log_paths}")
        print(f"[请求日志器] 初始化完成 - 监控方法: {self.log_methods}")
    
    def should_log_request(self, request: Request) -> bool:
        """判断是否应该记录此请求"""
        path = request.url.path
        method = request.method
        
        # 检查是否在精确排除列表中
        if path in self.exact_exclude_paths:
            return False
        
        # 检查是否在前缀排除列表中
        excluded_matches = [exclude for exclude in self.exclude_paths if path.startswith(exclude)]
        if excluded_matches:
            return False
        
        # 检查是否在需要记录的路径中
        path_matches = [log_path for log_path in self.log_paths if path.startswith(log_path)]
        if not path_matches:
            return False
        
        # 检查是否是需要记录的HTTP方法
        if method not in self.log_methods:
            return False
        
        return True
    
    async def get_current_user(self, request: Request) -> Optional[User]:
        """获取当前用户信息"""
        try:
            authorization = request.headers.get("Authorization")
            if not authorization or not authorization.startswith("Bearer "):
                return None
            
            token = authorization.split(" ")[1]
            user = await get_current_user_from_token(token)
            return user
        except Exception as e:
            print(f"[请求日志器] 获取用户信息失败: {e}")
            return None
    
    async def log_request(self, request: Request, response_status: int, 
                         process_time: float, current_user: Optional[User],
                         db: AsyncSession):
        """记录请求日志"""
        try:
            # 获取客户端IP
            client_ip = request.client.host if request.client else "unknown"
            
            # 解析页面功能
            module, page_function = self._parse_request_info(request)
            
            # 获取请求体数据
            request_body = await self._get_request_body(request)
            
            # 构建额外数据
            extra_data = {
                "method": request.method,
                "path": str(request.url.path),
                "query_params": dict(request.query_params),
                "user_agent": request.headers.get("user-agent", ""),
                "response_status": response_status,
                "process_time_ms": round(process_time, 2)
            }
            
            # 添加请求体数据
            if request_body:
                extra_data["request_body"] = request_body
            
            # 创建日志记录
            log_entry = SystemLog(
                level="info",
                module=module,
                action="api_request",
                message=f"{request.method} {request.url.path}",
                page_function=page_function,
                user_id=current_user.id if current_user else None,
                ip_address=client_ip,
                extra_data=extra_data
                # 移除created_at，让数据库自动设置时区正确的时间
            )
            
            db.add(log_entry)
            await db.commit()
            print(f"[请求日志器] 日志记录成功: {request.method} {request.url.path}, 模块: {module}, 页面功能: {page_function}")
            
        except Exception as e:
            print(f"[请求日志器] 记录日志失败: {e}")
            await db.rollback()
    
    def _parse_request_info(self, request: Request):
        """解析请求信息，返回模块和页面功能描述"""
        path = request.url.path
        method = request.method
        
        # 初始化默认值
        module = "system"
        page_function = "未知操作"
        
        # 根据路径解析模块和页面功能
        if "/users" in path:
            module = "user"
            if "/login" in path:
                page_function = "用户登录"
            elif "/logout" in path:
                page_function = "用户登出"
            elif method == "POST":
                page_function = "创建用户"
            elif method == "PUT" or method == "PATCH":
                page_function = "更新用户"
            elif method == "DELETE":
                page_function = "删除用户"
            else:
                page_function = "用户管理"
        elif "/cameras" in path:
            module = "camera"
            if method == "POST":
                page_function = "创建摄像头"
            elif method == "PUT" or method == "PATCH":
                page_function = "更新摄像头"
            elif method == "DELETE":
                page_function = "删除摄像头"
            else:
                page_function = "摄像头管理"
        elif "/ai" in path:
            module = "ai"
            if "/models" in path:
                if method == "POST":
                    page_function = "创建AI模型"
                elif method == "PUT" or method == "PATCH":
                    page_function = "更新AI模型"
                elif method == "DELETE":
                    page_function = "删除AI模型"
                else:
                    page_function = "AI模型管理"
            elif "/services" in path:
                if method == "POST":
                    page_function = "创建AI服务"
                elif method == "PUT" or method == "PATCH":
                    page_function = "更新AI服务"
                elif method == "DELETE":
                    page_function = "删除AI服务"
                else:
                    page_function = "AI服务管理"
            else:
                page_function = "AI管理"
        elif "/events" in path:
            module = "event"
            if "/tasks" in path:
                if method == "POST":
                    page_function = "创建事件任务"
                elif method == "PUT" or method == "PATCH":
                    page_function = "更新事件任务"
                elif method == "DELETE":
                    page_function = "删除事件任务"
                else:
                    page_function = "事件任务管理"
            else:
                page_function = "事件管理"
        elif "/system" in path:
            module = "system"
            if "/config" in path:
                page_function = "系统配置"
            elif "/logs" in path:
                page_function = "系统日志"
            else:
                page_function = "系统管理"
        elif "/diagnosis" in path:
            module = "diagnosis"
            page_function = "系统诊断"
        elif "/roles" in path:
            module = "role"
            if method == "POST":
                page_function = "创建角色"
            elif method == "PUT" or method == "PATCH":
                page_function = "更新角色"
            elif method == "DELETE":
                page_function = "删除角色"
            else:
                page_function = "角色管理"
        elif "/files" in path:
            module = "file"
            if method == "POST":
                page_function = "上传文件"
            elif method == "DELETE":
                page_function = "删除文件"
            else:
                page_function = "文件管理"
        
        return module, page_function
    
    async def _get_request_body(self, request: Request):
        """获取请求体数据"""
        try:
            # 只处理有请求体的方法
            if request.method not in ["POST", "PUT", "PATCH"]:
                return None
            
            # 检查Content-Type
            content_type = request.headers.get("content-type", "")
            
            # 如果是JSON数据
            if "application/json" in content_type:
                # 由于request.body()只能读取一次，我们需要从request.state中获取
                # 这需要在中间件中预先读取并存储
                if hasattr(request.state, 'body_data'):
                    return request.state.body_data
                else:
                    # 尝试读取body（可能已经被消费）
                    try:
                        body = await request.body()
                        if body:
                            import json
                            return json.loads(body.decode('utf-8'))
                    except Exception:
                        return None
            
            # 如果是表单数据
            elif "application/x-www-form-urlencoded" in content_type or "multipart/form-data" in content_type:
                if hasattr(request.state, 'form_data'):
                    return dict(request.state.form_data)
                else:
                    try:
                        form = await request.form()
                        return dict(form)
                    except Exception:
                        return None
            
            return None
            
        except Exception as e:
            print(f"[请求日志器] 获取请求体失败: {e}")
            return None
 
 # 全局请求日志器实例
request_logger = RequestLogger()

async def log_request_dependency(request: Request, db: AsyncSession = Depends(get_db)):
    """请求日志记录依赖"""
    if not request_logger.should_log_request(request):
        return
    
    # 记录开始时间
    start_time = time.time()
    
    # 获取用户信息
    current_user = await request_logger.get_current_user(request)
    print(f"[请求日志器] 获取到用户: {current_user.username if current_user else '无'}")
    
    # 将信息存储到request.state中，供后续使用
    request.state.log_start_time = start_time
    request.state.log_user = current_user
    request.state.should_log = True

async def complete_log_request(request: Request, response_status: int, db: AsyncSession = Depends(get_db)):
    """完成请求日志记录"""
    if not hasattr(request.state, 'should_log') or not request.state.should_log:
        return
    
    # 计算处理时间
    process_time = (time.time() - request.state.log_start_time) * 1000
    
    # 记录日志
    await request_logger.log_request(
        request=request,
        response_status=response_status,
        process_time=process_time,
        current_user=request.state.log_user,
        db=db
    )