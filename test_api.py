import requests

print('开始测试API...')

try:
    # 登录获取token
    login_response = requests.post(
        'http://localhost:8000/api/v1/auth/login',
        json={'username': 'admin', 'password': 'admin123'}
    )
    login_data = login_response.json()
    token = login_data.get('access_token')
    
    if token:
        headers = {'Authorization': f'Bearer {token}'}
        
        # 获取媒体节点列表
        media_proxies_response = requests.get(
            'http://localhost:8000/api/v1/cameras/media-proxies/',
            headers=headers
        )
        
        print("\n媒体节点API响应:")
        print(f"状态码: {media_proxies_response.status_code}")
        print(f"响应内容: {media_proxies_response.text}")
        
        # 获取摄像头列表
        cameras_response = requests.get(
            'http://localhost:8000/api/v1/cameras/',
            headers=headers
        )
        
        print("\n摄像头列表API响应:")
        print(f"状态码: {cameras_response.status_code}")
        print(f"响应内容: {cameras_response.text}")
        
        # 尝试添加摄像头
        new_camera = {
            "name": "测试摄像头",
            "code": "test123",
            "ip": "192.168.1.100",
            "port": 554,
            "username": "admin",
            "password": "admin123",
            "rtsp_url": "rtsp://192.168.1.100:554/stream",
            "media_proxy_id": 1,
            "location": "测试位置"
        }
        
        add_camera_response = requests.post(
            'http://localhost:8000/api/v1/cameras/',
            json=new_camera,
            headers=headers
        )
        
        print("\n添加摄像头API响应:")
        print(f"状态码: {add_camera_response.status_code}")
        print(f"响应内容: {add_camera_response.text}")
        
    else:
        print("登录失败，无法获取token")
        print(f"登录响应: {login_response.text}")
        
except Exception as e:
    print(f"发生错误: {e}")