import io
import asyncio
from minio import Minio
from fastapi import UploadFile
from app.settings import (
    MINIO_ENDPOINT, MINIO_ACCESS_KEY, MINIO_SECRET_KEY, 
    MINIO_BUCKET_NAME, MINIO_SECURE
)

class MinioClient:
    # 初始化客户端
    client = Minio(
        MINIO_ENDPOINT,
        access_key=MINIO_ACCESS_KEY,
        secret_key=MINIO_SECRET_KEY,
        secure=MINIO_SECURE
    )

    @classmethod
    async def init_bucket(cls):
        """初始化：确保桶存在"""
        def _ensure():
            if not cls.client.bucket_exists(MINIO_BUCKET_NAME):
                cls.client.make_bucket(MINIO_BUCKET_NAME)
        await asyncio.to_thread(_ensure)

    @classmethod
    async def _upload_raw(cls, data: bytes, object_name: str, content_type: str) -> str:
        """
        [内部通用方法] 上传二进制数据
        """
        def _put():
            cls.client.put_object(
                MINIO_BUCKET_NAME,
                object_name,
                io.BytesIO(data),
                length=len(data),
                content_type=content_type
            )
        
        await asyncio.to_thread(_put)
        
        # 拼接访问地址
        protocol = "https" if MINIO_SECURE else "http"
        return f"{protocol}://{MINIO_ENDPOINT}/{MINIO_BUCKET_NAME}/{object_name}"

    @classmethod
    async def upload_file(cls, file: UploadFile, object_name: str) -> str:
        """上传 FastAPI 文件对象"""
        content = await file.read()
        # 处理可能缺失的 content_type
        c_type = file.content_type or "application/octet-stream"
        return await cls._upload_raw(content, object_name, c_type)

    @classmethod
    async def upload_bytes(cls, data: bytes, object_name: str, content_type: str) -> str:
        """直接上传 bytes (用于头像等)"""
        return await cls._upload_raw(data, object_name, content_type)

    @classmethod
    async def get_file_bytes(cls, object_name: str) -> bytes:
        """下载文件并返回二进制 (用于 PDF 解析)"""
        def _get():
            response = None
            try:
                response = cls.client.get_object(MINIO_BUCKET_NAME, object_name)
                return response.read()
            except Exception as e:
                print(f"MinIO 下载异常: {e}")
                raise  # 抛出异常让业务层感知
            finally:
                if response:
                    response.close()
                    response.release_conn()

        return await asyncio.to_thread(_get)
