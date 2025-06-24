import requests

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
        
        # 检查响应内容是否为空数组
        if media_proxies_response.text.strip() == '[]':
            print("\n媒体节点API返回空数组，但数据库中有媒体节点数据")
            
        # 获取摄像头列表
        cameras_response = requests.get(
            'http://localhost:8000/api/v1/cameras/',
            headers=headers
        )
        
        print("\n摄像头列表API响应:")
        print(f"状态码: {cameras_response.status_code}")
        print(f"响应内容: {cameras_response.text}")
        
        # 解析JSON响应
        try:
            cameras_data = cameras_response.json()
            print(f"\n解析后的摄像头数据结构:")
            print(f"类型: {type(cameras_data)}")
            if isinstance(cameras_data, dict):
                print(f"字段: {list(cameras_data.keys())}")
                if 'data' in cameras_data:
                    print(f"data字段类型: {type(cameras_data['data'])}")
                    if isinstance(cameras_data['data'], dict):
                        print(f"data字段内容: {list(cameras_data['data'].keys())}")
        except Exception as json_error:
            print(f"JSON解析错误: {json_error}")
            
    else:
        print("登录失败，无法获取token")
        print(f"登录响应: {login_response.text}")
        
except Exception as e:
    print(f"发生错误: {e}")