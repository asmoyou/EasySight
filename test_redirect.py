import requests

# 测试307重定向问题
def test_redirect_issue():
    # 测试前端代理的请求
    print("测试前端代理请求 (3000端口):")
    try:
        response = requests.get('http://localhost:3000/api/v1/users?page=1&page_size=20', 
                              allow_redirects=False)
        print(f"状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        if 'Location' in response.headers:
            print(f"重定向到: {response.headers['Location']}")
        if response.status_code == 307:
            print("发现307重定向！")
    except Exception as e:
        print(f"请求失败: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # 测试直接访问后端 - 不带尾部斜杠
    print("测试直接访问后端 - 不带尾部斜杠 (8000端口):")
    try:
        response = requests.get('http://localhost:8000/api/v1/users?page=1&page_size=20', 
                              allow_redirects=False)
        print(f"状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        if 'Location' in response.headers:
            print(f"重定向到: {response.headers['Location']}")
        if response.status_code == 307:
            print("发现307重定向！这说明FastAPI自动重定向到带斜杠的URL")
    except Exception as e:
        print(f"请求失败: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # 测试带尾部斜杠的请求
    print("测试带尾部斜杠的请求:")
    try:
        response = requests.get('http://localhost:8000/api/v1/users/?page=1&page_size=20', 
                              allow_redirects=False)
        print(f"状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        if 'Location' in response.headers:
            print(f"重定向到: {response.headers['Location']}")
    except Exception as e:
        print(f"请求失败: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # 测试带认证的请求
    print("测试带认证的请求:")
    try:
        # 先登录获取token
        login_response = requests.post('http://localhost:8000/api/v1/auth/login', 
                                     json={"username": "admin", "password": "admin123"})
        if login_response.status_code == 200:
            token = login_response.json().get('access_token')
            headers = {'Authorization': f'Bearer {token}'}
            
            # 测试不带斜杠的认证请求
            response = requests.get('http://localhost:8000/api/v1/users?page=1&page_size=20', 
                                  headers=headers, allow_redirects=False)
            print(f"不带斜杠 - 状态码: {response.status_code}")
            if 'Location' in response.headers:
                print(f"重定向到: {response.headers['Location']}")
            
            # 测试带斜杠的认证请求
            response = requests.get('http://localhost:8000/api/v1/users/?page=1&page_size=20', 
                                  headers=headers, allow_redirects=False)
            print(f"带斜杠 - 状态码: {response.status_code}")
            if response.status_code == 200:
                print("带斜杠的请求成功！")
        else:
            print(f"登录失败: {login_response.status_code}")
    except Exception as e:
        print(f"认证测试失败: {e}")

if __name__ == "__main__":
    test_redirect_issue()