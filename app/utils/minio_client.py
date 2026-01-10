import io
import asyncio
from minio import Minio
from fastapi import UploadFile
from app.settings import (
    MINIO_ENDPOINT, MINIO_ACCESS_KEY, MINIO_SECRET_KEY, 
    MINIO_BUCKET_NAME, MINIO_SECURE
)

class MinioClient:
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
        """[内部通用方法] 上传二进制数据"""
        def _put():
            cls.client.put_object(
                MINIO_BUCKET_NAME,
                object_name,
                io.BytesIO(data),
                length=len(data),
                content_type=content_type
            )

        await asyncio.to_thread(_put)

        protocol = "https" if MINIO_SECURE else "http"
        return f"{protocol}://{MINIO_ENDPOINT}/{MINIO_BUCKET_NAME}/{object_name}"

    @classmethod
    async def upload_file(cls, file: UploadFile, object_name: str) -> str:
        """上传 FastAPI 文件对象"""
        content = await file.read()
        c_type = file.content_type or "application/octet-stream"
        return await cls._upload_raw(content, object_name, c_type)

    @classmethod
    async def upload_bytes(cls, data: bytes, object_name: str, content_type: str) -> str:
        """直接上传 bytes (用于头像等)"""
        return await cls._upload_raw(data, object_name, content_type)

    @classmethod
    async def get_file_bytes(cls, object_name: str) -> bytes:
        """
        【修复 Bug 6】下载文件并返回二进制
        改进资源管理，确保连接正确释放
        """
        def _get():
            response = None
            data = None
            try:
                response = cls.client.get_object(MINIO_BUCKET_NAME, object_name)
                # 先读取数据
                data = response.read()
                return data
            except Exception as e:
                print(f"MinIO 下载异常 [{object_name}]: {e}")
                raise
            finally:
                # 【修复】确保资源释放
                if response:
                    try:
                        response.close()
                        response.release_conn()
                    except Exception as cleanup_error:
                        print(f"资源清理异常: {cleanup_error}")

        return await asyncio.to_thread(_get)