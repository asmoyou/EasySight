import asyncio
import json
from fastapi import FastAPI, Request, Depends
from fastapi.testclient import TestClient
from request_body_parser import parse_and_store_request_body

app = FastAPI()

@app.post("/test")
async def test_endpoint(request: Request, _: dict = Depends(parse_and_store_request_body)):
    """测试请求体解析"""
    parsed_body = getattr(request.state, 'parsed_body', None)
    return {
        "message": "Test successful",
        "parsed_body": parsed_body,
        "has_parsed_body": hasattr(request.state, 'parsed_body')
    }

if __name__ == "__main__":
    client = TestClient(app)
    
    # 测试JSON请求体
    test_data = {
        "code": "TEST_CAMERA_001",
        "name": "测试摄像头",
        "stream_url": "rtsp://test.example.com",
        "location": "测试位置"
    }
    
    print("测试JSON请求体解析...")
    response = client.post("/test", json=test_data)
    print(f"响应状态码: {response.status_code}")
    print(f"响应内容: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
    
    # 测试表单数据
    print("\n测试表单数据解析...")
    form_data = {
        "username": "admin",
        "password": "admin123",
        "remember_me": "true"
    }
    response = client.post("/test", data=form_data)
    print(f"响应状态码: {response.status_code}")
    print(f"响应内容: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")