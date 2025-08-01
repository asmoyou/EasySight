import os
import uuid
import io
import zipfile
import json
import tempfile
from typing import Optional, Dict, Any, List
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
    
    async def upload_algorithm_package(self, file: UploadFile, user_id: int) -> Dict[str, Any]:
        """上传算法包
        
        Args:
            file: 上传的算法包文件
            user_id: 用户ID
            
        Returns:
            Dict[str, Any]: 包含文件信息和解析结果的字典
            
        Raises:
            HTTPException: 文件上传或解析失败时抛出异常
        """
        # 验证文件类型
        if not self._is_valid_algorithm_package(file):
            raise HTTPException(status_code=400, detail="只支持 ZIP 格式的算法包")
        
        # 验证文件大小 (100MB)
        if file.size and file.size > 100 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="算法包大小不能超过100MB")
        
        try:
            # 生成唯一文件名
            file_extension = self._get_file_extension(file.filename)
            unique_filename = f"algorithms/{user_id}/{uuid.uuid4().hex}{file_extension}"
            
            # 读取文件内容
            file_content = await file.read()
            
            # 解析算法包
            package_info = await self._parse_algorithm_package(file_content)
            
            # 上传到MinIO
            self.minio_client.put_object(
                bucket_name=self.bucket_name,
                object_name=unique_filename,
                data=io.BytesIO(file_content),
                length=len(file_content),
                content_type="application/zip"
            )
            
            # 返回文件信息和解析结果
            result = {
                "file_url": f"/api/v1/files/{unique_filename}",
                "file_size": len(file_content),
                "package_info": package_info
            }
            
            logger.info(f"Algorithm package uploaded successfully for user {user_id}: {unique_filename}")
            return result
            
        except HTTPException:
            raise
        except S3Error as e:
            logger.error(f"MinIO upload error: {e}")
            raise HTTPException(status_code=500, detail="算法包上传失败")
        except Exception as e:
            logger.error(f"Unexpected error during algorithm package upload: {e}")
            raise HTTPException(status_code=500, detail="算法包上传失败")
    
    async def upload_model_file(self, file: UploadFile, user_id: int) -> Dict[str, Any]:
        """上传模型文件
        
        Args:
            file: 上传的模型文件
            user_id: 用户ID
            
        Returns:
            Dict[str, Any]: 包含文件信息的字典
            
        Raises:
            HTTPException: 文件上传失败时抛出异常
        """
        # 验证文件类型
        if not self._is_valid_model_file(file):
            raise HTTPException(status_code=400, detail="不支持的模型文件格式")
        
        # 验证文件大小 (500MB)
        if file.size and file.size > 500 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="模型文件大小不能超过500MB")
        
        try:
            # 生成唯一文件名
            file_extension = self._get_file_extension(file.filename)
            unique_filename = f"models/{user_id}/{uuid.uuid4().hex}{file_extension}"
            
            # 读取文件内容
            file_content = await file.read()
            
            # 上传到MinIO
            self.minio_client.put_object(
                bucket_name=self.bucket_name,
                object_name=unique_filename,
                data=io.BytesIO(file_content),
                length=len(file_content),
                content_type="application/octet-stream"
            )
            
            # 返回文件信息
            result = {
                "file_url": f"/api/v1/files/{unique_filename}",
                "file_size": len(file_content),
                "file_name": file.filename
            }
            
            logger.info(f"Model file uploaded successfully for user {user_id}: {unique_filename}")
            return result
            
        except S3Error as e:
            logger.error(f"MinIO upload error: {e}")
            raise HTTPException(status_code=500, detail="模型文件上传失败")
        except Exception as e:
            logger.error(f"Unexpected error during model file upload: {e}")
            raise HTTPException(status_code=500, detail="模型文件上传失败")
    
    def _is_valid_algorithm_package(self, file: UploadFile) -> bool:
        """验证是否为有效的算法包文件"""
        if not file.filename:
            return False
        
        file_extension = self._get_file_extension(file.filename).lower()
        return file_extension == ".zip"
    
    def _is_valid_model_file(self, file: UploadFile) -> bool:
        """验证是否为有效的模型文件"""
        if not file.filename:
            return False
        
        valid_extensions = {".pth", ".pt", ".pb", ".h5", ".onnx", ".xml", ".bin", ".trt", ".engine"}
        file_extension = self._get_file_extension(file.filename).lower()
        return file_extension in valid_extensions
    
    async def _parse_algorithm_package(self, file_content: bytes) -> Dict[str, Any]:
        """解析算法包内容
        
        Args:
            file_content: 算法包文件内容
            
        Returns:
            Dict[str, Any]: 解析结果
            
        Raises:
            HTTPException: 解析失败时抛出异常
        """
        try:
            with tempfile.NamedTemporaryFile() as temp_file:
                temp_file.write(file_content)
                temp_file.flush()
                
                with zipfile.ZipFile(temp_file.name, 'r') as zip_file:
                    # 检查必需文件
                    required_files = ['algorithm.json', 'main.py']
                    file_list = zip_file.namelist()
                    
                    missing_files = [f for f in required_files if f not in file_list]
                    if missing_files:
                        raise HTTPException(
                            status_code=400, 
                            detail=f"算法包缺少必需文件: {', '.join(missing_files)}"
                        )
                    
                    # 读取算法配置
                    try:
                        with zip_file.open('algorithm.json') as config_file:
                            config_content = config_file.read().decode('utf-8')
                            algorithm_config = json.loads(config_content)
                    except json.JSONDecodeError:
                        raise HTTPException(status_code=400, detail="algorithm.json 格式错误")
                    
                    # 验证配置格式
                    required_config_fields = ['name', 'version', 'type', 'description']
                    missing_config_fields = [f for f in required_config_fields if f not in algorithm_config]
                    if missing_config_fields:
                        raise HTTPException(
                            status_code=400,
                            detail=f"algorithm.json 缺少必需字段: {', '.join(missing_config_fields)}"
                        )
                    
                    # 获取文件列表和依赖
                    dependencies = algorithm_config.get('dependencies', [])
                    models = algorithm_config.get('models', [])
                    
                    return {
                        "name": algorithm_config['name'],
                        "version": algorithm_config['version'],
                        "type": algorithm_config['type'],
                        "description": algorithm_config['description'],
                        "author": algorithm_config.get('author', ''),
                        "tags": algorithm_config.get('tags', []),
                        "dependencies": dependencies,
                        "models": models,
                        "files": file_list,
                        "entry_point": algorithm_config.get('entry_point', 'main.py'),
                        "config_schema": algorithm_config.get('config_schema', {})
                    }
                    
        except zipfile.BadZipFile:
            raise HTTPException(status_code=400, detail="无效的ZIP文件")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error parsing algorithm package: {e}")
            raise HTTPException(status_code=500, detail="算法包解析失败")


# 依赖注入函数
def get_file_upload_service(minio_client = Depends(get_minio)) -> FileUploadService:
    """获取文件上传服务实例"""
    return FileUploadService(minio_client)