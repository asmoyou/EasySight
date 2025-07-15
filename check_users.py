#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查数据库中的用户信息
"""

import sqlite3
import os

def check_users():
    """检查数据库中的用户"""
    db_path = os.path.join(os.path.dirname(__file__), 'backend', 'easysight.db')
    
    if not os.path.exists(db_path):
        print(f"❌ 数据库文件不存在: {db_path}")
        return
        
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 首先查看所有表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        print("数据库中的表:")
        for table in tables:
            print(f"- {table[0]}")
            
        # 如果有user相关的表，查询其内容
        for table in tables:
            table_name = table[0]
            if 'user' in table_name.lower():
                print(f"\n查询表 {table_name}:")
                cursor.execute(f"SELECT * FROM {table_name}")
                rows = cursor.fetchall()
                
                # 获取列名
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = cursor.fetchall()
                column_names = [col[1] for col in columns]
                print(f"列: {column_names}")
                
                for row in rows:
                    print(f"数据: {row}")
            
        conn.close()
        
    except Exception as e:
        print(f"❌ 查询用户失败: {str(e)}")

if __name__ == "__main__":
    check_users()