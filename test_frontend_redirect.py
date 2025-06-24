import requests

# 测试前端修改后的API调用
def test_frontend_api_calls():
    print("测试修改后的前端API调用...")
    
    # 先登录获取token
    print("1. 登录获取token...")
    login_response = requests.post('http://localhost:8000/api/v1/auth/login', 
                                 json={"username": "admin", "password": "admin123"})
    
    if login_response.status_code != 200:
        print(f"登录失败: {login_response.status_code}")
        return
    
    token = login_response.json().get('access_token')
    headers = {'Authorization': f'Bearer {token}'}
    print(f"登录成功，获取到token: {token[:50]}...")
    
    print("\n2. 测试通过前端代理访问用户列表API (3000端口)...")
    try:
        # 模拟前端通过代理访问
        response = requests.get('http://localhost:3000/api/v1/users/?page=1&page_size=20', 
                              headers=headers, allow_redirects=False)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 307:
            print("❌ 仍然存在307重定向问题")
            print(f"重定向到: {response.headers.get('Location', 'None')}")
        elif response.status_code == 200:
            print("✅ 成功！没有重定向问题")
            data = response.json()
            if 'users' in data and len(data['users']) > 0:
                print(f"获取到 {len(data['users'])} 个用户")
                if 'token' in data['users'][0]:
                    print("✅ 用户数据包含token字段")
        else:
            print(f"❌ 请求失败，状态码: {response.status_code}")
            print(f"响应: {response.text}")
    except Exception as e:
        print(f"请求异常: {e}")
    
    print("\n3. 测试直接访问后端用户列表API (8000端口)...")
    try:
        response = requests.get('http://localhost:8000/api/v1/users/?page=1&page_size=20', 
                              headers=headers, allow_redirects=False)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ 直接访问后端成功")
            data = response.json()
            if 'users' in data and len(data['users']) > 0:
                print(f"获取到 {len(data['users'])} 个用户")
        else:
            print(f"❌ 直接访问后端失败，状态码: {response.status_code}")
    except Exception as e:
        print(f"直接访问异常: {e}")
    
    print("\n4. 对比测试 - 不带斜杠的URL...")
    try:
        response = requests.get('http://localhost:3000/api/v1/users?page=1&page_size=20', 
                              headers=headers, allow_redirects=False)
        print(f"不带斜杠 - 状态码: {response.status_code}")
        if response.status_code == 307:
            print("确认：不带斜杠仍会导致307重定向")
    except Exception as e:
        print(f"对比测试异常: {e}")

if __name__ == "__main__":
    test_frontend_api_calls()