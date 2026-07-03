import io
import structlog
from minio import Minio
from minio.error import S3Error

from app.config import settings

log = structlog.get_logger()


class MinioStorageClient:
    def __init__(self):
        self._client = Minio(
            endpoint=settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_secure,
        )
        self._bucket = settings.minio_bucket

    def download(self, key: str) -> bytes:
        """Download an object and return its bytes."""
        try:
            response = self._client.get_object(self._bucket, key)
            data = response.read()
            response.close()
            response.release_conn()
            log.debug("downloaded_object", key=key, size_bytes=len(data))
            return data
        except S3Error as e:
            raise RuntimeError(f"Failed to download {key}: {e}") from e
