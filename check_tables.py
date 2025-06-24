import sqlite3

conn = sqlite3.connect('C:/PycharmProjects/EasySight/backend/easysight.db')
cursor = conn.cursor()

try:
    # 获取所有表名
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    
    print('数据库中的表:')
    for table in tables:
        print(table[0])
    
    # 如果有media_proxy表，检查其结构
    for table_name in [row[0] for row in tables]:
        if 'media' in table_name.lower() and 'proxy' in table_name.lower():
            print(f"\n找到媒体代理表: {table_name}")
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            print("表结构:")
            for col in columns:
                print(f"{col[1]} ({col[2]})")
            
            # 查询表中的数据
            cursor.execute(f"SELECT * FROM {table_name}")
            rows = cursor.fetchall()
            print(f"\n{table_name}表中的数据:")
            for row in rows:
                print(row)

except Exception as e:
    print(f"查询出错: {e}")
finally:
    conn.close()