import psycopg2

try:
    conn = psycopg2.connect(
        host='127.0.0.1',
        port=5432,
        database='easysight',
        user='rotanova',
        password='RotaNova@2025'
    )
    print('psycopg2 connection successful')
    conn.close()
except Exception as e:
    print(f'psycopg2 connection failed: {e}')
    print(f'Error type: {type(e).__name__}')