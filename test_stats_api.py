import httpx
import json

def test_stats_api():
    """测试统计数据API"""
    try:
        # 先登录获取token
        login_data = {
            "username": "admin",
            "password": "admin123"
        }
        
        with httpx.Client() as client:
            # 登录
            login_response = client.post(
                "http://localhost:8000/api/v1/auth/login",
                json=login_data
            )
            
            if login_response.status_code != 200:
                print(f"登录失败: {login_response.status_code}")
                print(f"响应内容: {login_response.text}")
                return
            
            token_data = login_response.json()
            token = token_data.get("access_token")
            
            if not token:
                print("未获取到token")
                return
            
            # 设置认证头
            headers = {"Authorization": f"Bearer {token}"}
            
            # 测试统计数据API
            stats_response = client.get(
                "http://localhost:8000/api/v1/ai/stats/overview",
                headers=headers
            )
            
            print(f"统计API状态码: {stats_response.status_code}")
            
            if stats_response.status_code == 200:
                stats_data = stats_response.json()
                print("统计API响应数据:")
                print(json.dumps(stats_data, indent=2, ensure_ascii=False))
                
                # 检查字段
                print("\n字段检查:")
                print(f"total_count: {stats_data.get('total_count', '字段不存在')}")
                print(f"online_count: {stats_data.get('online_count', '字段不存在')}")
                print(f"processing_count: {stats_data.get('processing_count', '字段不存在')}")
                print(f"success_rate: {stats_data.get('success_rate', '字段不存在')}")
                
                # 检查是否有其他可能的字段名
                print("\n所有字段:")
                for key, value in stats_data.items():
                    print(f"{key}: {value}")
            else:
                print(f"统计API请求失败: {stats_response.text}")
                
    except Exception as e:
        print(f"测试失败: {e}")

if __name__ == "__main__":
    test_stats_api()