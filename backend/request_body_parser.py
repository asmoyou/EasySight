from fastapi import Request
import json
from typing import Optional, Dict, Any


async def parse_and_store_request_body(request: Request) -> Optional[Dict[str, Any]]:
    """
    解析并存储请求体到 request.state 中，供日志中间件使用
    """
    try:
        # 检查是否已经解析过
        if hasattr(request.state, 'parsed_body'):
            return request.state.parsed_body
        
        # 获取内容类型
        content_type = request.headers.get('content-type', '')
        
        # 初始化请求体
        request_body = None
        
        if 'application/json' in content_type:
            # 解析 JSON 请求体
            body_bytes = await request.body()
            if body_bytes:
                try:
                    request_body = json.loads(body_bytes.decode('utf-8'))
                except json.JSONDecodeError:
                    request_body = {'error': 'Invalid JSON format'}
        
        elif 'application/x-www-form-urlencoded' in content_type or 'multipart/form-data' in content_type:
            # 解析表单数据
            try:
                form_data = await request.form()
                request_body = dict(form_data)
            except Exception:
                request_body = {'error': 'Failed to parse form data'}
        
        # 存储到 request.state 中
        request.state.parsed_body = request_body
        
        return request_body
        
    except Exception as e:
        # 发生错误时，存储错误信息
        error_body = {'error': f'Failed to parse request body: {str(e)}'}
        request.state.parsed_body = error_body
        return error_body