#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建测试消息数据
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import sessionmaker
from database import sync_engine
from sqlalchemy import text
from datetime import datetime, timedelta
import random

# 创建数据库会话
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)

def create_test_messages():
    db = SessionLocal()
    try:
        # 获取所有用户ID
        result = db.execute(text("SELECT id FROM users"))
        user_ids = [row[0] for row in result.fetchall()]
        if not user_ids:
            print("没有找到用户，请先创建用户")
            return
        
        # 测试消息数据
        test_messages = [
            {
                "title": "系统维护通知",
                "content": "系统将于今晚22:00-24:00进行维护升级，期间可能影响正常使用，请提前做好准备。",
                "message_type": "system",
                "category": "maintenance"
            },
            {
                "title": "摄像头异常告警",
                "content": "摄像头设备 CAM-001 检测到异常，请及时检查设备状态。",
                "message_type": "alert",
                "category": "device"
            },
            {
                "title": "新功能上线",
                "content": "消息中心功能已正式上线，您可以在此查看系统通知、设备告警等重要信息。",
                "message_type": "info",
                "category": "feature"
            },
            {
                "title": "AI算法更新",
                "content": "智能识别算法已更新至v2.1版本，识别准确率提升15%，处理速度优化20%。",
                "message_type": "info",
                "category": "algorithm"
            },
            {
                "title": "存储空间不足",
                "content": "当前存储空间使用率已达85%，建议及时清理历史数据或扩容存储设备。",
                "message_type": "warning",
                "category": "storage"
            },
            {
                "title": "用户权限变更",
                "content": "您的账户权限已更新，新增了系统配置管理权限，请查看详细权限列表。",
                "message_type": "info",
                "category": "permission"
            },
            {
                "title": "设备离线告警",
                "content": "摄像头设备 CAM-003 已离线超过30分钟，请检查网络连接和设备状态。",
                "message_type": "alert",
                "category": "device"
            },
            {
                "title": "数据备份完成",
                "content": "今日数据备份任务已完成，备份文件大小：2.3GB，备份时间：23:30-23:45。",
                "message_type": "info",
                "category": "backup"
            },
            {
                "title": "安全扫描报告",
                "content": "系统安全扫描已完成，发现3个低风险项，建议及时处理。详细报告请查看安全中心。",
                "message_type": "warning",
                "category": "security"
            },
            {
                "title": "性能监控告警",
                "content": "CPU使用率持续超过80%已达10分钟，建议检查系统负载情况。",
                "message_type": "alert",
                "category": "performance"
            }
        ]
        
        # 为每个用户创建消息
        for user_id in user_ids:
            for i, msg_data in enumerate(test_messages):
                # 随机设置一些消息为已读
                is_read = random.choice([True, False, False])  # 1/3概率已读
                read_at = datetime.now() - timedelta(hours=random.randint(1, 48)) if is_read else None
                
                # 创建时间随机分布在过去7天内
                created_at = datetime.now() - timedelta(
                    days=random.randint(0, 7),
                    hours=random.randint(0, 23),
                    minutes=random.randint(0, 59)
                )
                
                # 直接使用SQL插入
                sql = text("""
                    INSERT INTO user_messages 
                    (title, content, message_type, category, receiver_id, sender_id, is_read, read_at, created_at, updated_at)
                    VALUES (:title, :content, :message_type, :category, :receiver_id, :sender_id, :is_read, :read_at, :created_at, :updated_at)
                """)
                
                db.execute(sql, {
                    'title': msg_data["title"],
                    'content': msg_data["content"],
                    'message_type': msg_data["message_type"],
                    'category': msg_data["category"],
                    'receiver_id': user_id,
                    'sender_id': 1,  # 假设系统用户ID为1
                    'is_read': is_read,
                    'read_at': read_at,
                    'created_at': created_at,
                    'updated_at': created_at
                })
        
        db.commit()
        print(f"成功为 {len(user_ids)} 个用户创建了 {len(test_messages)} 条测试消息")
        
    except Exception as e:
        db.rollback()
        print(f"创建测试消息失败: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    create_test_messages()