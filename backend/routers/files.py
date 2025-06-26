from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from minio import Minio
from minio.error import S3Error
from typing import Optional
import logging

from database import get_db, get_minio
from models.user import User
from routers.auth import get_current_user
from utils.file_upload import get_file_upload_service, FileUploadService
from config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/upload/avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    file_service: FileUploadService = Depends(get_file_upload_service)
):
    """上传用户头像"""
    try:
        # 如果用户已有头像，先删除旧头像
        if current_user.avatar:
            await file_service.delete_avatar(current_user.avatar)
        
        # 上传新头像
        avatar_url = await file_service.upload_avatar(file, current_user.id)
        
        # 更新用户头像URL
        current_user.avatar = avatar_url
        db.add(current_user)
        await db.commit()
        await db.refresh(current_user)
        
        return {
            "message": "头像上传成功",
            "avatar_url": avatar_url
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Avatar upload failed: {e}")
        raise HTTPException(status_code=500, detail="头像上传失败")

@router.get("/{file_path:path}")
async def get_file(
    file_path: str,
    minio_client: Minio = Depends(get_minio)
):
    """获取文件内容"""
    try:
        # 从MinIO获取文件
        response = minio_client.get_object(
            bucket_name=settings.MINIO_BUCKET_NAME,
            object_name=file_path
        )
        
        # 获取文件信息
        stat = minio_client.stat_object(
            bucket_name=settings.MINIO_BUCKET_NAME,
            object_name=file_path
        )
        
        # 确定内容类型
        content_type = stat.content_type or "application/octet-stream"
        
        # 返回文件流
        def iterfile():
            try:
                while True:
                    chunk = response.read(8192)
                    if not chunk:
                        break
                    yield chunk
            finally:
                response.close()
                response.release_conn()
        
        return StreamingResponse(
            iterfile(),
            media_type=content_type,
            headers={
                "Content-Length": str(stat.size),
                "Cache-Control": "public, max-age=3600",  # 缓存1小时
                "ETag": stat.etag
            }
        )
        
    except S3Error as e:
        if e.code == "NoSuchKey":
            raise HTTPException(status_code=404, detail="文件不存在")
        logger.error(f"MinIO error: {e}")
        raise HTTPException(status_code=500, detail="文件访问失败")
    except Exception as e:
        logger.error(f"File access error: {e}")
        raise HTTPException(status_code=500, detail="文件访问失败")

@router.delete("/avatar")
async def delete_avatar(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    file_service: FileUploadService = Depends(get_file_upload_service)
):
    """删除用户头像"""
    try:
        if not current_user.avatar:
            raise HTTPException(status_code=400, detail="用户没有设置头像")
        
        # 删除文件
        success = await file_service.delete_avatar(current_user.avatar)
        if not success:
            logger.warning(f"Failed to delete avatar file: {current_user.avatar}")
        
        # 清除用户头像URL
        current_user.avatar = None
        db.add(current_user)
        await db.commit()
        
        return {"message": "头像删除成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Avatar deletion failed: {e}")
        raise HTTPException(status_code=500, detail="头像删除失败")