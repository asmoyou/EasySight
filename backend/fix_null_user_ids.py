import asyncio
from database import async_engine
from sqlalchemy import text

async def fix_nulls():
    async with async_engine.connect() as conn:
        # 删除user_id为NULL的记录
        result = await conn.execute(text('DELETE FROM user_login_logs WHERE user_id IS NULL'))
        await conn.commit()
        print(f'已删除{result.rowcount}条user_id为NULL的记录')

if __name__ == '__main__':
    asyncio.run(fix_nulls())