import asyncio
import time
import uuid
import re
import json
import logging
from typing import Optional, Dict, Any
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request as StarletteRequest
from .logging_config import LoggingConfig, logging_config
from database import AsyncSessionLocal

# 配置日志
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
# 添加控制台处理器
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

perf_logger = logging.getLogger("middleware.performance")

# API路由映射配置
API_ROUTE_MAPPING = {
    # 认证模块
    r'^/api/v1/auth/login$': {'module': 'auth', 'action': 'login', 'function': '用户登录'},
    r'^/api/v1/auth/logout$': {'module': 'auth', 'action': 'logout', 'function': '用户登出'},
    r'^/api/v1/auth/refresh$': {'module': 'auth', 'action': 'refresh_token', 'function': '刷新令牌'},
    
    # 摄像头模块
    r'^/api/v1/cameras/?$': {
        'GET': {'module': 'camera', 'action': 'list', 'function': '获取摄像头列表'},
        'POST': {'module': 'camera', 'action': 'create', 'function': '创建摄像头'}
    },
    r'^/api/v1/cameras/([0-9]+)/?$': {
        'GET': {'module': 'camera', 'action': 'get', 'function': '获取摄像头详情'},
        'PUT': {'module': 'camera', 'action': 'update', 'function': '更新摄像头'},
        'DELETE': {'module': 'camera', 'action': 'delete', 'function': '删除摄像头'}
    },
    r'^/api/v1/cameras/([0-9]+)/status/?$': {'module': 'camera', 'action': 'update_status', 'function': '更新摄像头状态'},
    r'^/api/v1/cameras/stats/?$': {'module': 'camera', 'action': 'stats', 'function': '获取摄像头统计'},
    r'^/api/v1/cameras/media-proxies/?$': {
        'GET': {'module': 'camera', 'action': 'list_proxies', 'function': '获取媒体代理列表'},
        'POST': {'module': 'camera', 'action': 'create_proxy', 'function': '创建媒体代理'}
    },
    
    # 用户模块
    r'^/api/v1/users/?$': {
        'GET': {'module': 'user', 'action': 'list', 'function': '获取用户列表'},
        'POST': {'module': 'user', 'action': 'create', 'function': '创建用户'}
    },
    r'^/api/v1/users/([0-9]+)/?$': {
        'GET': {'module': 'user', 'action': 'get', 'function': '获取用户详情'},
        'PUT': {'module': 'user', 'action': 'update', 'function': '更新用户'},
        'DELETE': {'module': 'user', 'action': 'delete', 'function': '删除用户'}
    },
    
    # AI模块
    r'^/api/v1/ai/models/?$': {
        'GET': {'module': 'ai', 'action': 'list_models', 'function': '获取AI模型列表'},
        'POST': {'module': 'ai', 'action': 'create_model', 'function': '创建AI模型'}
    },
    r'^/api/v1/ai/models/([0-9]+)/?$': {
        'GET': {'module': 'ai', 'action': 'get_model', 'function': '获取AI模型详情'},
        'PUT': {'module': 'ai', 'action': 'update_model', 'function': '更新AI模型'},
        'DELETE': {'module': 'ai', 'action': 'delete_model', 'function': '删除AI模型'}
    },
    
    # 事件模块
    r'^/api/v1/events/?$': {
        'GET': {'module': 'event', 'action': 'list', 'function': '获取事件列表'},
        'POST': {'module': 'event', 'action': 'create', 'function': '创建事件'}
    },
    r'^/api/v1/events/([0-9]+)/?$': {
        'GET': {'module': 'event', 'action': 'get', 'function': '获取事件详情'},
        'PUT': {'module': 'event', 'action': 'update', 'function': '更新事件'},
        'DELETE': {'module': 'event', 'action': 'delete', 'function': '删除事件'}
    },
    
    # 系统模块
    r'^/api/v1/system/info/?$': {'module': 'system', 'action': 'get_info', 'function': '获取系统信息'},
    r'^/api/v1/system/settings/?$': {
        'GET': {'module': 'system', 'action': 'get_settings', 'function': '获取系统设置'},
        'PUT': {'module': 'system', 'action': 'update_settings', 'function': '更新系统设置'}
    },
    
    # 诊断模块
    r'^/api/v1/diagnosis/health/?$': {'module': 'diagnosis', 'action': 'health_check', 'function': '健康检查'},
    r'^/api/v1/diagnosis/logs/?$': {'module': 'diagnosis', 'action': 'get_logs', 'function': '获取日志'},
    
    # 角色模块
    r'^/api/v1/roles/?$': {
        'GET': {'module': 'role', 'action': 'list', 'function': '获取角色列表'},
        'POST': {'module': 'role', 'action': 'create', 'function': '创建角色'}
    },
    r'^/api/v1/roles/([0-9]+)/?$': {
        'GET': {'module': 'role', 'action': 'get', 'function': '获取角色详情'},
        'PUT': {'module': 'role', 'action': 'update', 'function': '更新角色'},
        'DELETE': {'module': 'role', 'action': 'delete', 'function': '删除角色'}
    },
    
    # 文件模块
    r'^/api/v1/files/upload/?$': {'module': 'file', 'action': 'upload', 'function': '文件上传'},
    r'^/api/v1/files/([0-9]+)/?$': {
        'GET': {'module': 'file', 'action': 'get', 'function': '获取文件'},
        'DELETE': {'module': 'file', 'action': 'delete', 'function': '删除文件'}
    }
}

def get_route_info(path: str, method: str) -> Optional[Dict[str, str]]:
    """根据路径和方法获取路由信息"""
    for pattern, config in API_ROUTE_MAPPING.items():
        if re.match(pattern, path):
            if isinstance(config, dict) and method in config:
                return config[method]
            elif isinstance(config, dict) and 'module' in config:
                return config
    return None

class SystemLoggingMiddleware(BaseHTTPMiddleware):
    """系统日志中间件"""
    
    def __init__(self, app, config: LoggingConfig = None, enable_db_logging: bool = True):
        super().__init__(app)
        self.config = config or logging_config
        self.enable_db_logging = enable_db_logging
        
        # 打印初始化信息
        logger.info(f"[请求日志器] 初始化完成 - 排除路径: {self.config.excluded_paths}")
        logger.info(f"[请求日志器] 初始化完成 - 数据库日志: {self.enable_db_logging}")
    
    def _get_client_ip(self, request: Request) -> str:
        """获取客户端IP地址"""
        # 优先从X-Forwarded-For头获取
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        # 其次从X-Real-IP头获取
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # 最后从客户端地址获取
        if request.client:
            return request.client.host
        
        return "unknown"
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        request_id = str(uuid.uuid4())
        
        # 检查是否需要记录此请求
        if not self.config.should_log_request(request.url.path, request.method):
            return await call_next(request)
        
        # 获取客户端信息
        client_ip = self._get_client_ip(request)
        user_agent = request.headers.get("user-agent", "")
        
        # 获取路由信息
        route_info = get_route_info(request.url.path, request.method)
        
        # 获取请求参数
        request_params = dict(request.query_params) if request.query_params else {}
        
        # 获取请求体（从依赖注入或处理后获取）
        request_body = None
        if request.method in ["POST", "PUT", "PATCH"]:
            # 标记需要记录请求体，实际解析在请求处理后进行
            request.state.should_log_body = True
        
        logger.debug(f"最终请求体数据: {request_body}")
        logger.debug(f"请求参数: {request_params}")
        logger.debug(f"条件判断: request_params={bool(request_params and len(request_params) > 0)}, request_body={bool(request_body)}")
        
        # 获取用户信息（从JWT token）
        user_id = None
        username = None
        try:
            from routers.auth import get_current_user_from_token
            auth_header = request.headers.get("authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]
                user = await get_current_user_from_token(token)
                if user:
                    user_id = user.id
                    username = user.username
                    # 设置到request.state供其他地方使用
                    request.state.user_id = user_id
                    request.state.username = username
        except Exception as e:
            logger.debug(f"Failed to get user from token: {e}")
        
        try:
            # 处理请求
            response = await call_next(request)
            
            # 在请求处理完成后获取已解析的请求体
            if hasattr(request.state, 'parsed_body'):
                request_body = request.state.parsed_body
                logger.debug(f"从request.state获取到请求体: {request_body}")
            else:
                logger.debug("request.state中没有parsed_body")
            
            # 计算响应时间
            process_time = (time.time() - start_time) * 1000  # 转换为毫秒
            
            # 记录标准日志
            log_message = (
                f"{request.method} {request.url.path} - "
                f"Status: {response.status_code} - "
                f"Time: {process_time:.1f}ms - "
                f"Client: {client_ip} - "
                f"RequestID: {request_id}"
            )
            
            if response.status_code >= 400:
                logger.warning(log_message)
            else:
                logger.info(log_message)
            
            # 异步记录到数据库
            if self.enable_db_logging:
                asyncio.create_task(
                    self._log_to_database(
                        request_id=request_id,
                        method=request.method,
                        url=str(request.url),
                        status_code=response.status_code,
                        response_time=process_time,
                        client_ip=client_ip,
                        user_agent=user_agent,
                        user_id=user_id,
                        username=username,
                        route_info=route_info,
                        request_params=request_params,
                        request_body=request_body
                    )
                )
            
            return response
            
        except Exception as e:
            # 计算响应时间
            process_time = (time.time() - start_time) * 1000
            
            # 记录错误日志
            logger.error(
                f"{request.method} {request.url.path} - "
                f"Error: {str(e)} - "
                f"Time: {process_time:.1f}ms - "
                f"Client: {client_ip} - "
                f"RequestID: {request_id}"
            )
            
            # 异步记录错误到数据库
            if self.enable_db_logging:
                asyncio.create_task(
                    self._log_error_to_database(
                        request_id=request_id,
                        method=request.method,
                        url=str(request.url),
                        error_message=str(e),
                        response_time=process_time,
                        client_ip=client_ip,
                        user_agent=user_agent,
                        user_id=user_id,
                        username=username,
                        route_info=route_info,
                        request_params=request_params,
                        request_body=request_body
                    )
                )
            
            raise
    
    async def _log_to_database(self, **kwargs):
        """异步记录请求日志到数据库"""
        try:
            async with AsyncSessionLocal() as session:
                from models.system import SystemLog
                
                log_entry = SystemLog(
                    request_id=kwargs['request_id'],
                    request_method=kwargs['method'],
                    request_url=kwargs['url'],
                    response_status=kwargs['status_code'],
                    response_time=kwargs['response_time'],
                    ip_address=kwargs['client_ip'],
                    user_agent=kwargs['user_agent'],
                    user_id=kwargs.get('user_id'),
                    username=kwargs.get('username'),
                    module=kwargs['route_info']['module'] if kwargs['route_info'] else None,
                    action=kwargs['route_info']['action'] if kwargs['route_info'] else None,
                    page_function=kwargs['route_info']['function'] if kwargs['route_info'] else None,
                    level="info",
                    message=f"{kwargs['method']} {kwargs['url']} - {kwargs['status_code']}",
                    extra_data={
                        'request_params': kwargs['request_params'],
                        'request_body': kwargs['request_body'],
                        'debug_info': f"params_exist: {bool(kwargs.get('request_params'))}, body_exist: {bool(kwargs.get('request_body'))}"
                    }
                )
                
                session.add(log_entry)
                await session.commit()
                
        except Exception as e:
            logger.error(f"Failed to log to database: {e}")
    
    async def _log_error_to_database(self, **kwargs):
        """异步记录错误日志到数据库"""
        try:
            async with AsyncSessionLocal() as session:
                from models.system import SystemLog
                
                log_entry = SystemLog(
                    request_id=kwargs['request_id'],
                    request_method=kwargs['method'],
                    request_url=kwargs['url'],
                    response_status=500,  # 错误状态码
                    response_time=kwargs['response_time'],
                    ip_address=kwargs['client_ip'],
                    user_agent=kwargs['user_agent'],
                    user_id=kwargs.get('user_id'),
                    username=kwargs.get('username'),
                    module=kwargs['route_info']['module'] if kwargs['route_info'] else None,
                    action=kwargs['route_info']['action'] if kwargs['route_info'] else None,
                    page_function=kwargs['route_info']['function'] if kwargs['route_info'] else None,
                    level="error",
                    message=f"{kwargs['method']} {kwargs['url']} - Error: {kwargs['error_message']}",
                    extra_data={
                        'request_params': kwargs['request_params'],
                        'request_body': kwargs['request_body'],
                        'error_message': kwargs['error_message']
                    }
                )
                
                session.add(log_entry)
                await session.commit()
                
        except Exception as e:
            logger.error(f"Failed to log error to database: {e}")