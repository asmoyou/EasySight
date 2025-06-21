import asyncpg
import asyncio
import socket

def test_socket_connection():
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex(('127.0.0.1', 5432))
        sock.close()
        if result == 0:
            print('Socket connection to 127.0.0.1:5432 successful')
            return True
        else:
            print(f'Socket connection failed with code: {result}')
            return False
    except Exception as e:
        print(f'Socket connection failed: {e}')
        return False

async def test_db_connection():
    try:
        print('Testing asyncpg connection...')
        conn = await asyncpg.connect(
            host='127.0.0.1',
            port=5432,
            user='rotanova',
            password='RotaNova@2025',
            database='easysight'
        )
        print('Database connection successful')
        await conn.close()
        return True
    except Exception as e:
        print(f'Database connection failed: {e}')
        print(f'Error type: {type(e).__name__}')
        return False

if __name__ == '__main__':
    print('Testing socket connection first...')
    test_socket_connection()
    print('\nTesting asyncpg connection...')
    asyncio.run(test_db_connection())