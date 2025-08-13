#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
示例算法包打包脚本

此脚本用于将示例算法打包成可以上传到AI应用中心的zip文件
"""

import os
import zipfile
import json
import hashlib
from pathlib import Path
from datetime import datetime

def calculate_file_hash(file_path: Path) -> str:
    """计算文件的SHA256哈希值"""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def create_algorithm_package():
    """创建算法包"""
    # 定义路径
    script_dir = Path(__file__).parent
    algorithm_dir = script_dir / "example_algorithm"
    output_dir = script_dir / "packages"
    
    # 确保输出目录存在
    output_dir.mkdir(exist_ok=True)
    
    # 读取配置文件
    config_file = algorithm_dir / "config.json"
    if not config_file.exists():
        raise FileNotFoundError(f"配置文件不存在: {config_file}")
    
    with open(config_file, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    # 生成包文件名
    algorithm_code = config.get('code', 'example_algorithm')
    version = config.get('version', '1.0.0')
    package_name = f"{algorithm_code}_{version}.zip"
    package_path = output_dir / package_name
    
    print(f"开始打包算法: {config.get('name', '示例算法')}")
    print(f"版本: {version}")
    print(f"输出文件: {package_path}")
    
    # 要包含的文件列表
    files_to_include = [
        "__init__.py",
        "algorithm.py",
        "config.json",
        "README.md"
    ]
    
    # 创建zip文件
    with zipfile.ZipFile(package_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file_name in files_to_include:
            file_path = algorithm_dir / file_name
            if file_path.exists():
                # 添加文件到zip，保持相对路径
                zipf.write(file_path, file_name)
                print(f"添加文件: {file_name}")
            else:
                print(f"警告: 文件不存在，跳过: {file_name}")
    
    # 计算包文件的哈希值和大小
    package_hash = calculate_file_hash(package_path)
    package_size = package_path.stat().st_size
    
    print(f"\n打包完成!")
    print(f"包文件: {package_path}")
    print(f"文件大小: {package_size} 字节 ({package_size / 1024:.2f} KB)")
    print(f"SHA256哈希: {package_hash}")
    
    # 生成包信息文件
    package_info = {
        "name": config.get('name'),
        "code": algorithm_code,
        "version": version,
        "description": config.get('description'),
        "author": config.get('author'),
        "type": config.get('type'),
        "category": config.get('category'),
        "tags": config.get('tags', []),
        "file_info": {
            "filename": package_name,
            "size": package_size,
            "hash": package_hash,
            "created_at": datetime.now().isoformat()
        },
        "requirements": config.get('requirements'),
        "performance": config.get('performance'),
        "resource_requirements": config.get('resource_requirements'),
        "parameters": config.get('parameters'),
        "input_spec": config.get('input_spec'),
        "output_spec": config.get('output_spec')
    }
    
    # 保存包信息
    info_file = output_dir / f"{algorithm_code}_{version}_info.json"
    with open(info_file, 'w', encoding='utf-8') as f:
        json.dump(package_info, f, ensure_ascii=False, indent=2)
    
    print(f"包信息文件: {info_file}")
    
    return package_path, package_info

def create_upload_script():
    """创建上传脚本"""
    script_content = '''
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
        upload_url = f"{server_url}/api/v1/files/upload"
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
'''
    
    script_path = Path(__file__).parent / "upload_example_algorithm.py"
    with open(script_path, 'w', encoding='utf-8') as f:
        f.write(script_content)
    
    print(f"创建上传脚本: {script_path}")
    return script_path

def main():
    """主函数"""
    print("EasySight 示例算法包打包工具")
    print("=" * 40)
    
    try:
        # 创建算法包
        package_path, package_info = create_algorithm_package()
        
        # 创建上传脚本
        upload_script = create_upload_script()
        
        print("\n" + "=" * 40)
        print("打包完成!")
        print(f"\n算法包文件: {package_path}")
        print(f"上传脚本: {upload_script}")
        print("\n使用方法:")
        print(f"1. 启动EasySight服务器")
        print(f"2. 运行上传脚本: python {upload_script.name}")
        print(f"3. 或者通过Web界面上传: {package_path}")
        
    except Exception as e:
        print(f"打包失败: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()