from fastapi import Request, Depends
from typing import Optional, Dict, Any
import json
import logging

logger = logging.getLogger(__name__)

async def parse_and_store_request_body(request: Request) -> Optional[Dict[str, Any]]:
    """
    解析请求体并存储到request.state中，供日志中间件使用
    """
    try:
        content_type = request.headers.get("content-type", "")
        logger.debug(f"解析请求体，Content-Type: {content_type}")
        
        if "application/json" in content_type:
            # 对于JSON请求体，我们需要手动读取并解析
            body_bytes = await request.body()
            if body_bytes:
                try:
                    parsed_body = json.loads(body_bytes.decode('utf-8'))
                    request.state.parsed_body = parsed_body
                    logger.debug(f"成功解析JSON请求体: {parsed_body}")
                    return parsed_body
                except json.JSONDecodeError as e:
                    logger.warning(f"JSON解析失败: {e}")
                    request.state.parsed_body = None
            else:
                request.state.parsed_body = None
                logger.debug("请求体为空")
        elif "application/x-www-form-urlencoded" in content_type:
            # 对于表单数据，使用request.form()
            form_data = await request.form()
            parsed_body = dict(form_data)
            request.state.parsed_body = parsed_body
            logger.debug(f"成功解析表单数据: {parsed_body}")
            return parsed_body
        else:
            logger.debug(f"不支持的Content-Type: {content_type}")
            request.state.parsed_body = None
            
    except Exception as e:
        logger.error(f"解析请求体时出错: {e}")
        request.state.parsed_body = None
    
    return request.state.parsed_body

# 创建依赖函数
def get_request_body_dependency():
    """
    返回一个依赖函数，用于在路由中解析请求体
    """
    return Depends(parse_and_store_request_body)