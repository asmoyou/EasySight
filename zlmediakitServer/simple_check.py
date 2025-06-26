import psycopg2
import sys

try:
    # 连接数据库
    conn = psycopg2.connect(
        host="localhost",
        database="easysight",
        user="postgres",
        password="123456",
        port="5432"
    )
    
    cursor = conn.cursor()
    
    # 查询媒体代理的监控数据
    cursor.execute("""
        SELECT id, name, ip_address, port, is_online, 
               cpu_usage, memory_usage, bandwidth_usage, current_connections,
               last_heartbeat, created_at, updated_at
        FROM media_proxies 
        WHERE ip_address = '127.0.0.1' AND port = 18080
    """)
    
    results = cursor.fetchall()
    
    if results:
        for row in results:
            print(f"ID: {row[0]}")
            print(f"Name: {row[1]}")
            print(f"IP:Port: {row[2]}:{row[3]}")
            print(f"Online: {row[4]}")
            print(f"CPU Usage: {row[5]}")
            print(f"Memory Usage: {row[6]}")
            print(f"Bandwidth Usage: {row[7]}")
            print(f"Current Connections: {row[8]}")
            print(f"Last Heartbeat: {row[9]}")
            print(f"Created At: {row[10]}")
            print(f"Updated At: {row[11]}")
            print("-" * 50)
    else:
        print("No media proxy found for 127.0.0.1:18080")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)