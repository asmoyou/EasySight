#!/usr/bin/env python3
"""
清理旧版本的无用代码文件

这个脚本会删除以下旧版本文件：
1. 旧版本的主启动文件
2. 旧版本的Worker文件
3. 旧版本的调度器文件
4. 旧版本的路由文件
5. 测试和调试文件
"""

import os
import shutil
from pathlib import Path

# 需要删除的文件列表
FILES_TO_DELETE = [
    # 旧版本主文件
    "main.py",  # 旧版本，现在使用 main_rabbitmq.py
    
    # 旧版本Worker文件
    "distributed_worker.py",  # 旧版本，现在使用 rabbitmq_distributed_worker.py
    "diagnosis/worker.py",   # 旧版本Worker
    
    # 旧版本调度器
    "diagnosis/scheduler.py", # 旧版本调度器，现在使用 rabbitmq_scheduler.py
    
    # 旧版本路由
    "routers/diagnosis.py",  # 旧版本诊断路由，现在使用 diagnosis_rabbitmq.py
    
    # 旧版本事件任务管理器
    "event_task_manager.py", # 旧版本，现在使用 rabbitmq_event_task_manager.py
    
    # 测试和调试文件
    "simple_test.py",
    "test_api_direct.py",
    "test_event_task_worker.py",
    "test_improved_system.py",
    "test_node_id.py",
    "test_worker_debug.py",
    "test_worker_fetch.py",
    "test_worker_registration.py",
    "debug_workers.py",
    
    # 检查脚本（已完成功能）
    "check_event_services.py",
    "check_event_task_assignment.py",
    "check_task.py",
    "check_task_detail.py",
    "check_tasks.py",
    
    # 手动运行脚本
    "manual_run_task.py",
    "trigger_task.py",
    
    # 修复脚本（已完成功能）
    "fix_task_assignment.py",
    "reset_event_task_status.py",
    
    # 启用任务脚本
    "enable_task.py",
    
    # 创建事件任务脚本
    "create_event_task_for_service.py",
]

# 需要删除的目录列表
DIRECTORIES_TO_DELETE = [
    # 空的或无用的目录可以在这里添加
]

def main():
    """主函数"""
    backend_dir = Path(__file__).parent
    print(f"Backend目录: {backend_dir}")
    print("开始清理旧版本文件...")
    
    deleted_files = []
    not_found_files = []
    
    # 删除文件
    for file_path in FILES_TO_DELETE:
        full_path = backend_dir / file_path
        if full_path.exists():
            try:
                if full_path.is_file():
                    full_path.unlink()
                    deleted_files.append(str(file_path))
                    print(f"✓ 已删除文件: {file_path}")
                else:
                    print(f"⚠ 跳过非文件: {file_path}")
            except Exception as e:
                print(f"✗ 删除文件失败 {file_path}: {e}")
        else:
            not_found_files.append(str(file_path))
            print(f"- 文件不存在: {file_path}")
    
    # 删除目录
    for dir_path in DIRECTORIES_TO_DELETE:
        full_path = backend_dir / dir_path
        if full_path.exists():
            try:
                if full_path.is_dir():
                    shutil.rmtree(full_path)
                    deleted_files.append(str(dir_path))
                    print(f"✓ 已删除目录: {dir_path}")
                else:
                    print(f"⚠ 跳过非目录: {dir_path}")
            except Exception as e:
                print(f"✗ 删除目录失败 {dir_path}: {e}")
        else:
            not_found_files.append(str(dir_path))
            print(f"- 目录不存在: {dir_path}")
    
    print("\n=== 清理结果 ===")
    print(f"成功删除: {len(deleted_files)} 个文件/目录")
    print(f"未找到: {len(not_found_files)} 个文件/目录")
    
    if deleted_files:
        print("\n已删除的文件/目录:")
        for item in deleted_files:
            print(f"  - {item}")
    
    print("\n清理完成！")
    print("\n注意: 请确保以下RabbitMQ版本文件正常工作:")
    print("  - main_rabbitmq.py (主启动文件)")
    print("  - start_distributed_worker.py (Worker启动脚本)")
    print("  - rabbitmq_distributed_worker.py (RabbitMQ Worker)")
    print("  - diagnosis/rabbitmq_scheduler.py (RabbitMQ调度器)")
    print("  - routers/diagnosis_rabbitmq.py (RabbitMQ诊断路由)")
    print("  - rabbitmq_event_task_manager.py (RabbitMQ事件任务管理器)")

if __name__ == "__main__":
    main()