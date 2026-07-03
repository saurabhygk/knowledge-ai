import io
import structlog
from minio import Minio
from minio.error import S3Error
from app.config import settings

log = structlog.get_logger()


class StorageService:
    def __init__(self):
        self._client = Minio(
            endpoint=settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_secure,
        )
        self._bucket = settings.minio_bucket
        self._ensure_bucket()

    def _ensure_bucket(self) -> None:
        if not self._client.bucket_exists(self._bucket):
            self._client.make_bucket(self._bucket)
            log.info("created_bucket", bucket=self._bucket)

    def upload(self, key: str, data: bytes, content_type: str | None) -> str:
        try:
            self._client.put_object(
                self._bucket, key,
                io.BytesIO(data), len(data),
                content_type=content_type or "application/octet-stream",
            )
            log.info("uploaded_object", key=key, size=len(data))
            return key
        except S3Error as e:
            raise RuntimeError(f"Upload failed for {key}: {e}") from e

    def download(self, key: str) -> bytes:
        try:
            resp = self._client.get_object(self._bucket, key)
            data = resp.read()
            resp.close()
            resp.release_conn()
            return data
        except S3Error as e:
            raise RuntimeError(f"Download failed for {key}: {e}") from e

    def delete(self, key: str) -> None:
        try:
            self._client.remove_object(self._bucket, key)
        except S3Error as e:
            raise RuntimeError(f"Delete failed for {key}: {e}") from e
