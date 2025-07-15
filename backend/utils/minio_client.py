from minio import Minio
from datetime import timedelta
import io
from typing import Optional

class MinioClient:
    """简化的MinIO客户端，避免依赖冲突"""
    
    def __init__(self, endpoint: str, access_key: str, secret_key: str):
        self.client = Minio(endpoint, access_key, secret_key, secure=False)
    
    def ensure_bucket_exists(self, bucket_name: str):
        """确保桶存在，如果不存在则创建"""
        if not self.client.bucket_exists(bucket_name):
            self.client.make_bucket(bucket_name)
    
    def put_object(self, bucket_name: str, object_name: str, data: io.BytesIO, length: int) -> bool:
        """上传对象到MinIO"""
        try:
            self.client.put_object(bucket_name, object_name, data, length)
            return True
        except Exception as e:
            print(f"MinIO上传失败: {e}")
            return False
    
    def get_presigned_url(self, bucket_name: str, object_name: str, expiry: timedelta = timedelta(days=7)) -> Optional[str]:
        """获取预签名URL"""
        try:
            return self.client.presigned_get_object(bucket_name, object_name, expiry)
        except Exception as e:
            print(f"获取预签名URL失败: {e}")
            return None