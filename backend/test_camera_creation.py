import requests
import json

# 测试创建摄像头功能，验证日志记录
def test_camera_creation():
    base_url = "http://localhost:8000"
    
    # 1. 登录获取token
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    print("正在登录...")
    login_response = requests.post(f"{base_url}/api/v1/auth/login", json=login_data)
    print(f"登录状态码: {login_response.status_code}")
    
    if login_response.status_code != 200:
        print(f"登录失败: {login_response.text}")
        return
    
    token = login_response.json()["access_token"]
    print(f"获取到token: {token[:50]}...")
    
    # 2. 创建摄像头
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    camera_data = {
        "alarm_enabled": False,
        "backup_stream_url": "",
        "bitrate": 2048,
        "camera_type": "ip_camera",
        "code": "TEST124",
        "description": "测试摄像头",
        "frame_rate": 25,
        "ip_address": "192.168.1.100",
        "is_active": True,
        "is_recording": False,
        "location": "测试位置",
        "name": "测试摄像头123",
        "port": 554,
        "resolution": "1920x1080",
        "stream_url": "rtsp://test123"
    }
    
    print("正在创建摄像头...")
    print(f"摄像头数据: {json.dumps(camera_data, indent=2, ensure_ascii=False)}")
    
    create_response = requests.post(f"{base_url}/api/v1/cameras/", json=camera_data, headers=headers)
    print(f"创建摄像头状态码: {create_response.status_code}")
    
    if create_response.status_code == 201:
        response_data = create_response.json()
        print(f"摄像头创建成功，ID: {response_data.get('id')}")
        print(f"请求ID应该会在日志中记录，请检查数据库日志")
    else:
        print(f"创建摄像头失败: {create_response.text}")

if __name__ == "__main__":
    test_camera_creation()