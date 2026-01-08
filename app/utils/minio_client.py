from minio import Minio
from minio.error import S3Error
import io
import asyncio
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
        """初始化：如果桶不存在就创建"""
        def _ensure_bucket():
            if not cls.client.bucket_exists(MINIO_BUCKET_NAME):
                cls.client.make_bucket(MINIO_BUCKET_NAME)
        # 在线程池中运行，避免阻塞
        await asyncio.to_thread(_ensure_bucket)

    @classmethod
    async def upload_file(cls, file: UploadFile, object_name: str) -> str:
        """
        上传文件到 MinIO
        :param file: FastAPI 的 UploadFile 对象
        :param object_name: 在 MinIO 中的文件名 (例如: 2023/10/resume_1.pdf)
        :return: 文件的访问 URL
        """
        # 读取文件内容为 bytes
        content = await file.read()
        file_size = len(content)
        data_stream = io.BytesIO(content)

        def _upload():
            cls.client.put_object(
                MINIO_BUCKET_NAME,
                object_name,
                data_stream,
                length=file_size,
                content_type=file.content_type # type: ignore
            )
        
        await asyncio.to_thread(_upload)
        
        # 拼接返回 URL (如果是本地开发，通常是 http://IP:9000/bucket/filename)
        # 注意：生产环境可能需要拼接外部域名的 URL
        protocol = "https" if MINIO_SECURE else "http"
        return f"{protocol}://{MINIO_ENDPOINT}/{MINIO_BUCKET_NAME}/{object_name}"

    @classmethod
    async def get_file_content(cls, object_name: str) -> str:
        """
        获取文件内容（主要用于读取文本/Markdown 格式的简历给 AI）
        注意：如果是 PDF/Word，这里需要额外的解析库（如 pdfplumber），
        为了简化 MVP，这里假设上传的是文本或 Markdown，或者你已经在外部转成了文本。
        """
        def _get():
            try:
                response = None
                response = cls.client.get_object(MINIO_BUCKET_NAME, object_name)
                return response.read().decode('utf-8')
            finally:
                if response:
                    response.close()
                
        return await asyncio.to_thread(_get)
    @classmethod
    async def get_file_bytes(cls, object_name: str) -> bytes:
        """从 MinIO 下载文件并返回二进制数据 (用于 PDF 解析)"""
        def _get():
            response = None
            try:
                response = cls.client.get_object(MINIO_BUCKET_NAME, object_name)
                return response.read() # 返回 bytes，不要 decode
            except Exception as e:
                print(f"MinIO 下载失败: {e}")
                return None
            finally:
                if response:
                    response.close()
                    response.release_conn()

        return await asyncio.to_thread(_get) # type: ignore
    
    # 顺便加一个上传 bytes 的方法，用于上传提取出来的头像
    @classmethod
    async def upload_bytes(cls, data: bytes, object_name: str, content_type: str) -> str:
        data_stream = io.BytesIO(data)
        data_len = len(data)
        
        def _put():
            cls.client.put_object(
                MINIO_BUCKET_NAME,
                object_name,
                data_stream,
                length=data_len,
                content_type=content_type
            )
        
        await asyncio.to_thread(_put)
        
        protocol = "https" if MINIO_SECURE else "http"
        return f"{protocol}://{MINIO_ENDPOINT}/{MINIO_BUCKET_NAME}/{object_name}"