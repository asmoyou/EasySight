#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通过API测试亮度诊断修复
"""

import requests
import json

def test_brightness_api():
    """通过API测试亮度诊断任务"""
    base_url = "http://localhost:8000"
    
    try:
        # 首先登录获取token
        login_data = {
            "username": "admin",
            "password": "admin123"
        }
        
        print("正在登录...")
        login_response = requests.post(
            f"{base_url}/api/v1/auth/login", 
            json=login_data,
            headers={"Content-Type": "application/json"}
        )
        
        if login_response.status_code != 200:
            print(f"❌ 登录失败: {login_response.status_code} - {login_response.text}")
            return
            
        token_data = login_response.json()
        access_token = token_data.get("access_token")
        
        if not access_token:
            print("❌ 未获取到访问令牌")
            return
            
        print("✅ 登录成功")
        
        # 设置认证头
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        # 执行诊断任务
        print("正在执行亮度诊断任务...")
        run_response = requests.post(f"{base_url}/api/v1/diagnosis/tasks/1/run", headers=headers)
        
        print(f"任务执行响应状态: {run_response.status_code}")
        print(f"任务执行响应内容: {run_response.text}")
        
        if run_response.status_code == 200:
            result = run_response.json()
            print("✅ 任务执行API调用成功")
            print(f"执行结果: {json.dumps(result, indent=2, ensure_ascii=False)}")
        else:
            print(f"❌ 任务执行失败: {run_response.status_code}")
            
        # 等待一下然后查看诊断结果
        import time
        print("等待3秒后查看诊断结果...")
        time.sleep(3)
        
        # 获取诊断结果
        results_response = requests.get(f"{base_url}/api/v1/diagnosis/results/?page=1&page_size=5", headers=headers)
        
        print(f"诊断结果响应状态: {results_response.status_code}")
        
        if results_response.status_code == 200:
            results = results_response.json()
            print("✅ 成功获取诊断结果")
            print(f"结果数量: {len(results.get('items', []))}")
            
            # 显示最新的几条结果
            for item in results.get('items', [])[:3]:
                print(f"- ID: {item.get('id')}, 类型: {item.get('diagnosis_type')}, 状态: {item.get('diagnosis_status')}, 分数: {item.get('score')}")
        else:
            print(f"❌ 获取诊断结果失败: {results_response.status_code} - {results_response.text}")
            
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_brightness_api()