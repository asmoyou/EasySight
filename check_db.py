import sqlite3

conn = sqlite3.connect('C:/PycharmProjects/EasySight/backend/easysight.db')
cursor = conn.cursor()

# 检查媒体代理表
try:
    cursor.execute("SELECT * FROM media_proxies")
    media_proxies = cursor.fetchall()
    
    # 获取列名
    column_names = [description[0] for description in cursor.description]
    
    print("\n媒体代理表结构:")
    print(column_names)
    
    print("\n媒体代理数据:")
    for proxy in media_proxies:
        print(proxy)
    
    # 检查摄像头表
    cursor.execute("SELECT id, code, name, stream_url, media_proxy_id, status FROM cameras LIMIT 5")
    cameras = cursor.fetchall()
    
    # 获取列名
    camera_columns = [description[0] for description in cursor.description]
    
    print("\n摄像头表数据(部分字段):")
    print(camera_columns)
    for camera in cameras:
        print(camera)
    
except Exception as e:
    print(f"查询出错: {e}")
finally:
    conn.close()