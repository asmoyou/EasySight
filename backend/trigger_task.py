#!/usr/bin/env python3
import requests
import json
from datetime import datetime, timezone

def trigger_task():
    # 登录获取token
    login_response = requests.post('http://localhost:8000/api/v1/auth/login', 
                                 json={'username': 'admin', 'password': 'admin123'})
    token = login_response.json()['access_token']
    headers = {'Authorization': f'Bearer {token}'}
    
    # 手动执行任务ID为3的清晰度检测任务
    task_id = 3
    
    print(f"当前时间: {datetime.now(timezone.utc)}")
    print(f"尝试手动执行任务 {task_id}...")
    
    # 手动执行任务
    execute_response = requests.post(
        f'http://localhost:8000/api/v1/diagnosis/tasks/{task_id}/run',
        headers=headers
    )
    
    if execute_response.status_code == 200:
        result = execute_response.json()
        print(f"任务执行成功: {result}")
    else:
        print(f"任务执行失败: {execute_response.status_code} - {execute_response.text}")
    
    # 检查任务状态
    status_response = requests.get(
        f'http://localhost:8000/api/v1/diagnosis/tasks/{task_id}',
        headers=headers
    )
    
    if status_response.status_code == 200:
        task_info = status_response.json()
        print(f"\n任务当前状态:")
        print(f"状态: {task_info.get('status')}")
        print(f"上次运行: {task_info.get('last_run')}")
        print(f"下次运行: {task_info.get('next_run')}")
        print(f"总运行次数: {task_info.get('run_count')}")
    else:
        print(f"获取任务状态失败: {status_response.status_code}")

if __name__ == "__main__":
    trigger_task()