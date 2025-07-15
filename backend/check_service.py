import requests
import sys

try:
    response = requests.get('http://localhost:8000/health', timeout=5)
    if response.status_code == 200:
        print('后端服务正在运行:', response.json())
        
        # 检查Worker状态
        try:
            worker_response = requests.get('http://localhost:8000/api/v1/diagnosis/workers/status', timeout=5)
            if worker_response.status_code == 200:
                print('Worker池状态:', worker_response.json())
            else:
                print('Worker状态检查失败，状态码:', worker_response.status_code)
        except Exception as e:
            print('Worker状态检查异常:', str(e))
    else:
        print('后端服务异常，状态码:', response.status_code)
except Exception as e:
    print('后端服务未运行:', str(e))
    print('请先启动后端服务: python main.py')