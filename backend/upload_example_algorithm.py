
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
算法包上传脚本

使用此脚本将打包好的算法上传到AI应用中心
"""

import requests
import json
from pathlib import Path

def upload_algorithm_package(package_path, server_url="http://localhost:8000", token=None):
    """上传算法包到服务器"""
    
    # 准备上传文件
    with open(package_path, 'rb') as f:
        files = {'file': (package_path.name, f, 'application/zip')}
        
        # 准备请求头
        headers = {}
        if token:
            headers['Authorization'] = f'Bearer {token}'
        
        # 上传文件
        upload_url = f"{server_url}/api/v1/files/upload/algorithm-package"
        print(f"上传算法包到: {upload_url}")
        
        response = requests.post(upload_url, files=files, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            print(f"上传成功: {result}")
            return result
        else:
            print(f"上传失败: {response.status_code} - {response.text}")
            return None

def install_algorithm_package(file_id, server_url="http://localhost:8000", token=None):
    """安装算法包"""
    
    # 准备请求头
    headers = {'Content-Type': 'application/json'}
    if token:
        headers['Authorization'] = f'Bearer {token}'
    
    # 安装算法包
    install_url = f"{server_url}/api/v1/files/install-algorithm"
    data = {'file_id': file_id}
    
    print(f"安装算法包: {install_url}")
    
    response = requests.post(install_url, json=data, headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        print(f"安装成功: {result}")
        return result
    else:
        print(f"安装失败: {response.status_code} - {response.text}")
        return None

def main():
    """主函数"""
    # 查找包文件
    packages_dir = Path(__file__).parent / "packages"
    package_files = list(packages_dir.glob("example_algorithm_*.zip"))
    
    if not package_files:
        print("未找到算法包文件，请先运行 package_example_algorithm.py")
        return
    
    # 使用最新的包文件
    package_path = max(package_files, key=lambda p: p.stat().st_mtime)
    print(f"使用算法包: {package_path}")
    
    # 上传算法包
    upload_result = upload_algorithm_package(package_path)
    if upload_result:
        file_id = upload_result.get('id')
        if file_id:
            # 安装算法包
            install_result = install_algorithm_package(file_id)
            if install_result:
                print("算法包上传和安装完成!")
            else:
                print("算法包安装失败")
        else:
            print("未获取到文件ID")
    else:
        print("算法包上传失败")

if __name__ == "__main__":
    main()
