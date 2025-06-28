#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
流媒体服务健康检查脚本
用于检查ZLMediaKit和流媒体服务的运行状态
"""

import requests
import sys
from datetime import datetime
from config import zlm_host, zlm_port, zlm_secret, MEDIA_NODE_PORT

# 服务配置
ZLM_HOST = "127.0.0.1"
MEDIA_SERVICE_HOST = "127.0.0.1"
MEDIA_SERVICE_PORT = 8000


def check_service(name, url, timeout=5):
    """检查服务状态"""
    try:
        response = requests.get(url, timeout=timeout)
        if response.status_code == 200:
            return {
                "service": name,
                "status": "✅ 正常",
                "status_code": response.status_code,
                "response_time": f"{response.elapsed.total_seconds():.3f}s",
                "details": "服务响应正常"
            }
        else:
            return {
                "service": name,
                "status": "⚠️ 异常",
                "status_code": response.status_code,
                "response_time": f"{response.elapsed.total_seconds():.3f}s",
                "details": f"HTTP状态码: {response.status_code}"
            }
    except requests.exceptions.ConnectionError:
        return {
            "service": name,
            "status": "❌ 连接失败",
            "status_code": "N/A",
            "response_time": "N/A",
            "details": "无法连接到服务"
        }
    except requests.exceptions.Timeout:
        return {
            "service": name,
            "status": "⏰ 超时",
            "status_code": "N/A",
            "response_time": "N/A",
            "details": f"请求超时 (>{timeout}s)"
        }
    except Exception as e:
        return {
            "service": name,
            "status": "❌ 错误",
            "status_code": "N/A",
            "response_time": "N/A",
            "details": str(e)
        }


def main():
    """主函数"""
    print("\n" + "="*80)
    print(f"流媒体服务健康检查报告 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    # 检查项目列表
    checks = [
        {
            "name": f"ZLMediaKit API (端口 {zlm_port})",
            "url": f"http://{zlm_host}:{zlm_port}/index/api/getServerConfig?secret={zlm_secret}"
        },
        {
            "name": f"EasySight主服务 API (端口 {MEDIA_SERVICE_PORT})",
            "url": f"http://{MEDIA_SERVICE_HOST}:{MEDIA_SERVICE_PORT}/health"
        },
        {
            "name": f"ZLMediaKit 媒体列表 (端口 {zlm_port})",
            "url": f"http://{zlm_host}:{zlm_port}/index/api/getMediaList?secret={zlm_secret}"
        }
    ]
    
    results = []
    
    # 执行检查
    for check in checks:
        print(f"\n检查 {check['name']}...")
        result = check_service(check['name'], check['url'])
        results.append(result)
        
        # 打印结果
        print(f"状态: {result['status']}")
        print(f"状态码: {result['status_code']}")
        print(f"响应时间: {result['response_time']}")
        print(f"详情: {result['details']}")
        print("-" * 40)
    
    # 统计结果
    total_checks = len(results)
    success_checks = len([r for r in results if "✅" in r['status']])
    
    print(f"\n📊 检查统计:")
    print(f"总检查项: {total_checks}")
    print(f"成功: {success_checks}")
    print(f"失败: {total_checks - success_checks}")
    print(f"成功率: {(success_checks/total_checks*100):.1f}%")
    
    # 端口配置信息
    print(f"\n🔧 端口配置信息:")
    print(f"ZLMediaKit HTTP API: {zlm_host}:{zlm_port}")
    print(f"EasySight 主服务 API: {MEDIA_SERVICE_HOST}:{MEDIA_SERVICE_PORT}")
    print(f"RTSP协议端口: 554 (摄像头推流)")
    print(f"RTMP协议端口: 1935 (直播推流)")
    
    if success_checks == total_checks:
        print("\n🎉 所有服务运行正常！")
        return 0
    else:
        print("\n⚠️  部分服务存在问题，请检查:")
        print("   1. 服务是否已启动")
        print("   2. 端口是否被占用")
        print("   3. 防火墙设置")
        print("   4. 配置文件是否正确")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)