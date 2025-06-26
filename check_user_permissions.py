import asyncio
import aiohttp
import json

async def check_user_permissions():
    """检查用户权限数据"""
    base_url = "http://localhost:8000/api/v1"
    
    # 模拟登录获取token
    login_data = {
        "username": "admin",  # 假设使用admin用户
        "password": "admin123"  # 请根据实际密码修改
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            # 登录
            async with session.post(f"{base_url}/auth/login", json=login_data) as response:
                if response.status == 200:
                    login_result = await response.json()
                    print("登录成功!")
                    print(f"Token: {login_result['access_token'][:50]}...")
                    
                    user_info = login_result['user_info']
                    print(f"\n用户信息:")
                    print(f"用户名: {user_info['username']}")
                    print(f"角色: {user_info['role']}")
                    print(f"所有角色: {user_info['roles']}")
                    print(f"\n权限列表:")
                    for perm in user_info['permissions']:
                        print(f"  - {perm}")
                    
                    print(f"\n页面权限:")
                    page_perms = user_info['page_permissions']
                    if page_perms:
                        for page, allowed in page_perms.items():
                            print(f"  {page}: {allowed}")
                    else:
                        print("  没有页面权限数据!")
                    
                    # 使用token获取当前用户信息
                    headers = {"Authorization": f"Bearer {login_result['access_token']}"}
                    async with session.get(f"{base_url}/auth/me", headers=headers) as me_response:
                        if me_response.status == 200:
                            me_data = await me_response.json()
                            print(f"\n通过/auth/me获取的页面权限:")
                            me_page_perms = me_data.get('page_permissions', {})
                            if me_page_perms:
                                for page, allowed in me_page_perms.items():
                                    print(f"  {page}: {allowed}")
                            else:
                                print("  没有页面权限数据!")
                        else:
                            print(f"获取用户信息失败: {me_response.status}")
                            print(await me_response.text())
                    
                else:
                    print(f"登录失败: {response.status}")
                    print(await response.text())
                    
        except Exception as e:
            print(f"请求失败: {e}")

if __name__ == "__main__":
    asyncio.run(check_user_permissions())