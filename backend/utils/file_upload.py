import os
import uuid
import io
from typing import Optional
from fastapi import UploadFile, HTTPException, Depends
from minio import Minio
from minio.error import S3Error
from config import settings
from database import get_minio
import logging

logger = logging.getLogger(__name__)

class FileUploadService:
    """文件上传服务类"""
    
    def __init__(self, minio_client: Minio):
        self.minio_client = minio_client
        self.bucket_name = settings.MINIO_BUCKET_NAME
    
    async def upload_avatar(self, file: UploadFile, user_id: int) -> str:
        """上传用户头像
        
        Args:
            file: 上传的文件
            user_id: 用户ID
            
        Returns:
            str: 文件的URL路径
            
        Raises:
            HTTPException: 文件上传失败时抛出异常
        """
        # 验证文件类型
        if not self._is_valid_image(file):
            raise HTTPException(status_code=400, detail="只支持 JPG, JPEG, PNG, GIF 格式的图片")
        
        # 验证文件大小 (5MB)
        if file.size and file.size > 5 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="文件大小不能超过5MB")
        
        try:
            # 生成唯一文件名
            file_extension = self._get_file_extension(file.filename)
            unique_filename = f"avatars/{user_id}/{uuid.uuid4().hex}{file_extension}"
            
            # 读取文件内容
            file_content = await file.read()
            
            # 上传到MinIO
            self.minio_client.put_object(
                bucket_name=self.bucket_name,
                object_name=unique_filename,
                data=io.BytesIO(file_content),
                length=len(file_content),
                content_type=file.content_type or "application/octet-stream"
            )
            
            # 返回文件URL
            file_url = f"/api/v1/files/{unique_filename}"
            logger.info(f"Avatar uploaded successfully for user {user_id}: {file_url}")
            return file_url
            
        except S3Error as e:
            logger.error(f"MinIO upload error: {e}")
            raise HTTPException(status_code=500, detail="文件上传失败")
        except Exception as e:
            logger.error(f"Unexpected error during file upload: {e}")
            raise HTTPException(status_code=500, detail="文件上传失败")
    
    async def delete_avatar(self, file_path: str) -> bool:
        """删除头像文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            bool: 删除是否成功
        """
        try:
            # 从URL中提取对象名称
            object_name = file_path.replace("/api/v1/files/", "")
            
            # 从MinIO删除文件
            self.minio_client.remove_object(
                bucket_name=self.bucket_name,
                object_name=object_name
            )
            
            logger.info(f"Avatar deleted successfully: {file_path}")
            return True
            
        except S3Error as e:
            logger.error(f"MinIO delete error: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during file deletion: {e}")
            return False
    
    def _is_valid_image(self, file: UploadFile) -> bool:
        """验证是否为有效的图片文件"""
        if not file.filename:
            return False
        
        valid_extensions = {".jpg", ".jpeg", ".png", ".gif"}
        file_extension = self._get_file_extension(file.filename).lower()
        
        # 检查文件扩展名
        if file_extension not in valid_extensions:
            return False
        
        # 检查MIME类型
        valid_mime_types = {
            "image/jpeg", "image/jpg", "image/png", "image/gif"
        }
        if file.content_type and file.content_type not in valid_mime_types:
            return False
        
        return True
    
    def _get_file_extension(self, filename: Optional[str]) -> str:
        """获取文件扩展名"""
        if not filename:
            return ""
        return os.path.splitext(filename)[1]


# 依赖注入函数
def get_file_upload_service(minio_client = Depends(get_minio)) -> FileUploadService:
    """获取文件上传服务实例"""
    return FileUploadService(minio_client)