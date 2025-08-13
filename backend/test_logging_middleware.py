#!/usr/bin/env python3
"""
日志中间件测试脚本
用于验证SystemLoggingMiddleware和DependencyLoggingMiddleware的功能
"""

import asyncio
import aiohttp
import json
from datetime import datetime


class LoggingMiddlewareTest:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.session = None
        self.access_token = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def login(self, username="admin", password="admin123"):
        """登录获取访问令牌"""
        login_data = {
            "username": username,
            "password": password
        }
        
        try:
            async with self.session.post(
                f"{self.base_url}/api/v1/auth/login",
                json=login_data,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    self.access_token = data.get("access_token")
                    print(f"✅ 登录成功，获取到访问令牌")
                    return True
                else:
                    print(f"❌ 登录失败，状态码: {response.status}")
                    return False
        except Exception as e:
            print(f"❌ 登录请求异常: {e}")
            return False
    
    async def test_unauthorized_request(self):
        """测试未授权请求（应该记录401错误）"""
        print("\n🔍 测试未授权请求...")
        try:
            async with self.session.get(
                f"{self.base_url}/api/v1/cameras/",
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                print(f"📊 状态码: {response.status} (预期: 401)")
                return response.status == 401
        except Exception as e:
            print(f"❌ 请求异常: {e}")
            return False
    
    async def test_authorized_request(self):
        """测试授权请求（应该记录200成功）"""
        if not self.access_token:
            print("❌ 没有访问令牌，无法测试授权请求")
            return False
        
        print("\n🔍 测试授权请求...")
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        try:
            async with self.session.get(
                f"{self.base_url}/api/v1/cameras/",
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                print(f"📊 状态码: {response.status} (预期: 200)")
                if response.status == 200:
                    data = await response.json()
                    print(f"📋 返回数据: {len(data) if isinstance(data, list) else 'N/A'} 个摄像头")
                return response.status == 200
        except Exception as e:
            print(f"❌ 请求异常: {e}")
            return False
    
    async def test_post_request(self):
        """测试POST请求（创建摄像头）"""
        if not self.access_token:
            print("❌ 没有访问令牌，无法测试POST请求")
            return False
        
        print("\n🔍 测试POST请求...")
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        camera_data = {
            "name": f"测试摄像头_{datetime.now().strftime('%H%M%S')}",
            "stream_url": "rtsp://test.example.com/stream",
            "location": "测试位置",
            "description": "日志中间件测试摄像头"
        }
        
        try:
            async with self.session.post(
                f"{self.base_url}/api/v1/cameras/",
                headers=headers,
                json=camera_data,
                timeout=aiohttp.ClientTimeout(total=15)
            ) as response:
                print(f"📊 状态码: {response.status}")
                if response.status in [200, 201]:
                    data = await response.json()
                    print(f"✅ 摄像头创建成功，ID: {data.get('id', 'N/A')}")
                    return True
                else:
                    error_text = await response.text()
                    print(f"❌ 创建失败: {error_text[:200]}")
                    return False
        except Exception as e:
            print(f"❌ 请求异常: {e}")
            return False
    
    async def test_slow_request(self):
        """测试慢请求（通过添加延迟参数）"""
        if not self.access_token:
            print("❌ 没有访问令牌，无法测试慢请求")
            return False
        
        print("\n🔍 测试慢请求（模拟）...")
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        try:
            # 发送多个并发请求来模拟负载
            tasks = []
            for i in range(3):
                task = self.session.get(
                    f"{self.base_url}/api/v1/cameras/",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                )
                tasks.append(task)
            
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            success_count = sum(1 for r in responses if hasattr(r, 'status') and r.status == 200)
            print(f"📊 并发请求完成: {success_count}/3 成功")
            
            # 关闭响应
            for response in responses:
                if hasattr(response, 'close'):
                    response.close()
            
            return success_count > 0
        except Exception as e:
            print(f"❌ 慢请求测试异常: {e}")
            return False
    
    async def run_all_tests(self):
        """运行所有测试"""
        print("🚀 开始日志中间件功能测试")
        print(f"🌐 测试服务器: {self.base_url}")
        print(f"⏰ 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        results = []
        
        # 测试未授权请求
        results.append(await self.test_unauthorized_request())
        
        # 登录
        login_success = await self.login()
        if not login_success:
            print("❌ 登录失败，跳过需要授权的测试")
            return False
        
        # 测试授权请求
        results.append(await self.test_authorized_request())
        
        # 测试POST请求
        results.append(await self.test_post_request())
        
        # 测试慢请求
        results.append(await self.test_slow_request())
        
        # 总结
        success_count = sum(results)
        total_count = len(results)
        
        print(f"\n📈 测试总结:")
        print(f"✅ 成功: {success_count}/{total_count}")
        print(f"❌ 失败: {total_count - success_count}/{total_count}")
        
        if success_count == total_count:
            print("🎉 所有测试通过！日志中间件工作正常")
        else:
            print("⚠️  部分测试失败，请检查日志")
        
        print("\n💡 提示: 请检查服务器日志和数据库中的system_logs表来验证日志记录功能")
        
        return success_count == total_count


async def main():
    """主函数"""
    async with LoggingMiddlewareTest() as tester:
        await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())