import asyncio
from database import get_db
from models.camera import Camera
from sqlalchemy import select

async def check_camera_status():
    async for db in get_db():
        try:
            result = await db.execute(
                select(Camera.id, Camera.name, Camera.status, Camera.stream_url)
                .where(Camera.is_active == True)
            )
            cameras = result.all()
            print('Current camera statuses:')
            for camera in cameras:
                print(f'ID: {camera.id}, Name: {camera.name}, Status: {camera.status}, Stream: {camera.stream_url}')
            break
        except Exception as e:
            print(f'Error: {e}')
            break

if __name__ == '__main__':
    asyncio.run(check_camera_status())