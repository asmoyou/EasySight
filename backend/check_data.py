import asyncio
from database import get_db
from models.diagnosis import DiagnosisResult
from sqlalchemy import select

async def check_data():
    async for db in get_db():
        result = await db.execute(select(DiagnosisResult))
        rows = result.scalars().all()
        print(f'数据库中的诊断结果数量: {len(rows)}')
        for row in rows:
            print(f'ID: {row.id}, Task ID: {row.task_id}, Status: {row.diagnosis_status}')
        break

if __name__ == "__main__":
    asyncio.run(check_data())