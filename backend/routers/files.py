from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from minio import Minio
from minio.error import S3Error
from typing import Optional, Dict, Any
import logging

from database import get_db, get_minio
from models.user import User
from models.ai_algorithm import AIAlgorithm
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


@router.post("/upload/algorithm-package")
async def upload_algorithm_package(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    file_service: FileUploadService = Depends(get_file_upload_service)
) -> Dict[str, Any]:
    """上传算法包"""
    try:
        result = await file_service.upload_algorithm_package(file, current_user.id)
        return {
            "message": "算法包上传成功",
            "data": result
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Algorithm package upload error: {e}")
        raise HTTPException(status_code=500, detail="算法包上传失败")


@router.post("/upload/model")
async def upload_model_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    file_service: FileUploadService = Depends(get_file_upload_service)
) -> Dict[str, Any]:
    """上传模型文件"""
    try:
        result = await file_service.upload_model_file(file, current_user.id)
        return {
            "message": "模型文件上传成功",
            "data": result
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Model file upload error: {e}")
        raise HTTPException(status_code=500, detail="模型文件上传失败")


@router.post("/install/algorithm-package")
async def install_algorithm_package(
    package_data: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """安装算法包"""
    try:
        # 从包数据中提取信息
        package_info = package_data.get("package_info", {})
        file_url = package_data.get("file_url", "")
        
        # 创建算法记录
        algorithm = AIAlgorithm(
            name=package_info.get("name", ""),
            version=package_info.get("version", "1.0.0"),
            type=package_info.get("type", "custom"),
            description=package_info.get("description", ""),
            author=package_info.get("author", current_user.username),
            tags=package_info.get("tags", []),
            config_schema=package_info.get("config_schema", {}),
            package_url=file_url,
            entry_point=package_info.get("entry_point", "main.py"),
            dependencies=package_info.get("dependencies", []),
            created_by=current_user.id,
            is_active=True
        )
        
        db.add(algorithm)
        db.commit()
        db.refresh(algorithm)
        
        return {
            "message": "算法包安装成功",
            "data": {
                "algorithm_id": algorithm.id,
                "name": algorithm.name,
                "version": algorithm.version,
                "type": algorithm.type
            }
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Algorithm package installation error: {e}")
        raise HTTPException(status_code=500, detail="算法包安装失败")