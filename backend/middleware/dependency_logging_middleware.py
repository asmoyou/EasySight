from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from middleware.request_logger import request_logger
from database import get_db
import time

class DependencyLoggingMiddleware(BaseHTTPMiddleware):
    """基于依赖注入的日志记录中间件"""
    
    def __init__(self, app):
        super().__init__(app)
        pass
    
    async def dispatch(self, request: Request, call_next):
        # 检查是否需要记录日志
        should_log = request_logger.should_log_request(request)
        
        if should_log:
            # 记录开始时间
            start_time = time.time()
             
            # 获取用户信息
            current_user = await request_logger.get_current_user(request)
            
            # 暂时禁用请求体缓存以避免超时问题
            # await self._cache_request_body(request)
            
            # 将信息存储到request.state中
            request.state.log_start_time = start_time
            request.state.log_user = current_user
            request.state.should_log = True
        
        # 处理请求
        response = await call_next(request)
        
        if should_log and hasattr(request.state, 'should_log') and request.state.should_log:
            # 计算处理时间
            process_time = (time.time() - request.state.log_start_time) * 1000
            
            # 获取数据库会话并记录日志
            try:
                from database import AsyncSessionLocal
                async with AsyncSessionLocal() as db:
                    await request_logger.log_request(
                        request=request,
                        response_status=response.status_code,
                        process_time=process_time,
                        current_user=request.state.log_user,
                        db=db
                    )
            except Exception as e:
                print(f"[依赖日志中间件] 记录日志失败: {e}")
                import traceback
                traceback.print_exc()
        
        return response
    
    async def _cache_request_body(self, request: Request):
        """缓存请求体数据"""
        try:
            # 只处理有请求体的方法
            if request.method not in ["POST", "PUT", "PATCH"]:
                return
            
            content_type = request.headers.get("content-type", "")
            
            # 处理JSON数据
            if "application/json" in content_type:
                # 使用更安全的方式读取请求体
                body_bytes = b""
                async for chunk in request.stream():
                    body_bytes += chunk
                
                if body_bytes:
                    # 将原始字节存储到request.state，供后续使用
                    request.state.cached_body = body_bytes
                    
                    # 解析JSON并存储到request.state
                    import json
                    body_data = json.loads(body_bytes.decode('utf-8'))
                    request.state.body_data = body_data
                    
            # 处理表单数据 - 暂时跳过，因为form()也会消费请求体
            # elif "application/x-www-form-urlencoded" in content_type or "multipart/form-data" in content_type:
            #     form_data = await request.form()
            #     request.state.form_data = form_data
                
        except Exception as e:
            print(f"[依赖日志中间件] 缓存请求体失败: {e}")
            # 不抛出异常，继续处理请求