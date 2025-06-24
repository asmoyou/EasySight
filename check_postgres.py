import psycopg2

try:
    # 连接到PostgreSQL数据库
    conn = psycopg2.connect(
        host="127.0.0.1",
        port="5432",
        database="easysight",
        user="rotanova",
        password="RotaNova@2025"
    )
    cursor = conn.cursor()
    
    # 获取所有表名
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
    """)
    tables = cursor.fetchall()
    
    print('数据库中的表:')
    for table in tables:
        print(table[0])
    
    # 检查media_proxies表
    media_table_name = None
    for table_name in [row[0] for row in tables]:
        if 'media' in table_name.lower() and 'prox' in table_name.lower():
            media_table_name = table_name
            break
    
    if media_table_name:
        print(f"\n找到媒体代理表: {media_table_name}")
        
        # 获取表结构
        cursor.execute(f"""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = '{media_table_name}'
        """)
        columns = cursor.fetchall()
        
        print("表结构:")
        for col in columns:
            print(f"{col[0]} ({col[1]})")
        
        # 查询表中的数据
        cursor.execute(f"SELECT * FROM {media_table_name}")
        rows = cursor.fetchall()
        
        print(f"\n{media_table_name}表中的数据:")
        for row in rows:
            print(row)
    else:
        print("未找到媒体代理相关的表")
    
    # 检查cameras表
    camera_table_name = None
    for table_name in [row[0] for row in tables]:
        if 'camera' in table_name.lower():
            camera_table_name = table_name
            break
    
    if camera_table_name:
        print(f"\n找到摄像头表: {camera_table_name}")
        
        # 获取表结构
        cursor.execute(f"""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = '{camera_table_name}'
        """)
        columns = cursor.fetchall()
        
        print("表结构:")
        for col in columns:
            print(f"{col[0]} ({col[1]})")
        
        # 查询表中的数据
        cursor.execute(f"SELECT id, code, name, stream_url, media_proxy_id, status FROM {camera_table_name} LIMIT 5")
        rows = cursor.fetchall()
        
        print(f"\n{camera_table_name}表中的数据(部分字段):")
        for row in rows:
            print(row)
    else:
        print("未找到摄像头相关的表")
    
except Exception as e:
    print(f"查询出错: {e}")
finally:
    if 'conn' in locals() and conn:
        conn.close()