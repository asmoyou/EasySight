import asyncio
from database import AsyncSessionLocal
from models.ai_algorithm import AIModel
from sqlalchemy import select

async def check_models():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(AIModel))
        models = result.scalars().all()
        print(f'数据库中共有 {len(models)} 个模型记录')
        for m in models:
            print(f'模型ID: {m.id}, 名称: {m.name}, 路径: {m.model_path}, 大小: {m.model_size}')

if __name__ == "__main__":
    asyncio.run(check_models())