import requests
import json

# 测试系统日志API
url = "http://localhost:8000/api/v1/system/logs/"
params = {
    "page": 1,
    "page_size": 50
}

try:
    # 不带认证的请求
    response = requests.get(url, params=params)
    print(f"状态码: {response.status_code}")
    print(f"响应内容: {response.text}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n成功获取日志数据:")
        print(f"总数: {data.get('total', 0)}")
        print(f"页数: {data.get('page', 0)}")
        print(f"页大小: {data.get('page_size', 0)}")
        print(f"日志条数: {len(data.get('logs', []))}")
        
        # 显示前几条日志
        logs = data.get('logs', [])
        if logs:
            print("\n前几条日志:")
            for i, log in enumerate(logs[:3]):
                print(f"日志 {i+1}: {log}")
    else:
        print(f"\n请求失败: {response.status_code}")
        print(f"错误信息: {response.text}")
        
except Exception as e:
    print(f"请求异常: {e}")