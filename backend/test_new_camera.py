import requests
import json
import random
import string

# 生成随机摄像头编码
def generate_random_code():
    return 'TEST_' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

# 测试登录
login_url = "http://localhost:8000/api/v1/auth/login"
login_data = {
    "username": "admin",
    "password": "admin123"
}

print("正在登录...")
login_response = requests.post(login_url, json=login_data)
print(f"登录状态码: {login_response.status_code}")

if login_response.status_code == 200:
    token = login_response.json()["access_token"]
    print(f"获取到token: {token[:50]}...")
    
    # 测试创建摄像头
    camera_url = "http://localhost:8000/api/v1/cameras/"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    camera_data = {
        "code": generate_random_code(),
        "name": "测试摄像头_新",
        "stream_url": "rtsp://test_new",
        "backup_stream_url": "",
        "camera_type": "ip_camera",
        "location": "测试位置_新",
        "ip_address": "192.168.1.101",
        "port": 554,
        "resolution": "1920x1080",
        "frame_rate": 25,
        "bitrate": 2048,
        "is_active": True,
        "is_recording": False,
        "alarm_enabled": False,
        "description": "测试摄像头_新"
    }
    
    print("\n正在创建摄像头...")
    print(f"摄像头数据: {json.dumps(camera_data, indent=2, ensure_ascii=False)}")
    
    camera_response = requests.post(camera_url, json=camera_data, headers=headers)
    print(f"创建摄像头状态码: {camera_response.status_code}")
    
    if camera_response.status_code == 201:
        print("创建摄像头成功!")
        print(f"响应数据: {json.dumps(camera_response.json(), indent=2, ensure_ascii=False)}")
    else:
        print(f"创建摄像头失败: {camera_response.text}")
else:
    print(f"登录失败: {login_response.text}")