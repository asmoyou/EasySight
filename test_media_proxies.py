import requests
import json

try:
    # 测试媒体代理接口
    response = requests.get('http://localhost:8000/api/v1/cameras/media-proxies')
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")