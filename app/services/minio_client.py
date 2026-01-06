import asyncio
from io import BytesIO
from urllib.parse import urlparse

from minio import Minio
from minio.error import S3Error

from app.config import settings


class MinioService:
    def __init__(self) -> None:
        self._client = Minio(
            settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=False,
        )
        self._bucket = settings.minio_bucket
        self._base_url = self._normalize_endpoint(settings.minio_endpoint)
        self._ensure_bucket()

    def _ensure_bucket(self) -> None:
        if not self._client.bucket_exists(self._bucket):
            self._client.make_bucket(self._bucket)

    async def upload_file(self, content: bytes, filename: str, content_type: str) -> str:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None, lambda: self._put_object(BytesIO(content), filename, content_type)
        )

    def _put_object(self, stream: BytesIO, filename: str, content_type: str) -> str:
        try:
            result = self._client.put_object(
                self._bucket,
                filename,
                data=stream,
                length=stream.getbuffer().nbytes,
                content_type=content_type,
            )
            return f"{self._base_url}/{self._bucket}/{result.object_name}"
        except S3Error as exc:
            raise RuntimeError(f"Failed to upload to MinIO: {exc}") from exc

    def _normalize_endpoint(self, endpoint: str) -> str:
        parsed = urlparse(endpoint)
        if not parsed.scheme:
            return f"http://{endpoint}"
        return f"{parsed.scheme}://{parsed.netloc or parsed.path}"
