#!/usr/bin/env python3
import requests
import json
from datetime import datetime

def check_cron_tasks():
    # 登录获取token
    login_response = requests.post('http://localhost:8000/api/v1/auth/login', 
                                 json={'username': 'admin', 'password': 'admin123'})
    token = login_response.json()['access_token']
    
    # 获取所有任务
    task_response = requests.get('http://localhost:8000/api/v1/diagnosis/tasks', 
                               headers={'Authorization': f'Bearer {token}'})
    
    response_data = task_response.json()
    print(f"API响应结构: {type(response_data)}")
    print(f"响应内容: {response_data}")
    
    # 处理不同的响应格式
    if isinstance(response_data, dict) and 'items' in response_data:
        all_tasks = response_data['items']
    elif isinstance(response_data, list):
        all_tasks = response_data
    else:
        print("未知的响应格式")
        return
    
    # 筛选每分钟执行的cron任务
    tasks = []
    for t in all_tasks:
        schedule_config = t.get('schedule_config', {})
        cron_expr = schedule_config.get('cron_expression', '')
        if cron_expr and '*/1' in cron_expr:
            tasks.append(t)
    
    print(f"当前时间: {datetime.now()}")
    print(f"找到 {len(tasks)} 个每分钟执行的cron任务:")
    print("-" * 80)
    
    for t in tasks:
        print(f"ID: {t['id']}")
        print(f"名称: {t['name']}")
        schedule_config = t.get('schedule_config', {})
        print(f"Cron表达式: {schedule_config.get('cron_expression')}")
        print(f"状态: {t['status']}")
        print(f"激活: {t['is_active']}")
        print(f"是否定时: {t.get('is_scheduled')}")
        print(f"上次运行: {t.get('last_run')}")
        print(f"下次运行: {t.get('next_run')}")
        print(f"总运行次数: {t.get('run_count', 0)}")
        print(f"成功次数: {t.get('success_count', 0)}")
        print(f"调度配置: {schedule_config}")
        print("-" * 40)

if __name__ == "__main__":
    check_cron_tasks()