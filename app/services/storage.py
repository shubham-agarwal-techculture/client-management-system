"""Pluggable document storage backends."""

from __future__ import annotations

import os
import uuid
from abc import ABC, abstractmethod
from typing import Optional

from app.core.exceptions import StorageError


class StorageBackend(ABC):
    @abstractmethod
    async def save(
        self, file_data: bytes, filename: str, content_type: Optional[str] = None
    ) -> str:
        pass

    @abstractmethod
    async def get_url(
        self, storage_path: str, expires_in: int = 3600
    ) -> str:
        pass

    @abstractmethod
    async def delete(self, storage_path: str) -> None:
        pass


class LocalStorageBackend(StorageBackend):
    def __init__(self, base_path: str):
        self.base_path = base_path
        os.makedirs(self.base_path, exist_ok=True)

    def _full_path(self, storage_path: str) -> str:
        return os.path.normpath(os.path.join(self.base_path, storage_path))

    async def save(
        self, file_data: bytes, filename: str, content_type: Optional[str] = None
    ) -> str:
        ext = os.path.splitext(filename)[1]
        safe_name = f"{uuid.uuid4().hex}{ext}"
        storage_path = os.path.join("uploads", safe_name)
        full = self._full_path(storage_path)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        try:
            with open(full, "wb") as f:
                f.write(file_data)
        except OSError as exc:
            raise StorageError(f"Failed to write file: {exc}") from exc
        return storage_path

    async def get_url(self, storage_path: str, expires_in: int = 3600) -> str:
        full = self._full_path(storage_path)
        if not os.path.exists(full):
            raise StorageError(f"File not found: {storage_path}")
        return f"/api/v1/documents/download/{storage_path}"

    async def delete(self, storage_path: str) -> None:
        full = self._full_path(storage_path)
        try:
            if os.path.exists(full):
                os.remove(full)
        except OSError as exc:
            raise StorageError(f"Failed to delete file: {exc}") from exc


try:
    from botocore.exceptions import ClientError as BotoClientError
    import boto3

    class S3StorageBackend(StorageBackend):
        def __init__(
            self,
            bucket: str,
            region: str = "us-east-1",
            endpoint_url: Optional[str] = None,
            access_key: Optional[str] = None,
            secret_key: Optional[str] = None,
        ):
            self.bucket = bucket
            self.s3 = boto3.client(
                "s3",
                region_name=region,
                endpoint_url=endpoint_url,
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
            )

        async def save(
            self, file_data: bytes, filename: str, content_type: Optional[str] = None
        ) -> str:
            key = f"uploads/{uuid.uuid4().hex}{os.path.splitext(filename)[1]}"
            try:
                self.s3.put_object(
                    Bucket=self.bucket,
                    Key=key,
                    Body=file_data,
                    ContentType=content_type,
                )
            except BotoClientError as exc:
                raise StorageError(f"S3 upload failed: {exc}") from exc
            return key

        async def get_url(self, storage_path: str, expires_in: int = 3600) -> str:
            try:
                return self.s3.generate_presigned_url(
                    "get_object",
                    Params={"Bucket": self.bucket, "Key": storage_path},
                    ExpiresIn=expires_in,
                )
            except BotoClientError as exc:
                raise StorageError(f"S3 presigned URL failed: {exc}") from exc

        async def delete(self, storage_path: str) -> None:
            try:
                self.s3.delete_object(Bucket=self.bucket, Key=storage_path)
            except BotoClientError as exc:
                raise StorageError(f"S3 delete failed: {exc}") from exc

except ImportError:

    class S3StorageBackend(StorageBackend):
        def __init__(self, *args, **kwargs):
            raise StorageError(
                "S3 backend requested but `boto3` is not installed. "
                "Use STORAGE_BACKEND=local or install boto3."
            )

        async def save(self, *args, **kwargs):
            raise StorageError("S3 backend unavailable")

        async def get_url(self, *args, **kwargs):
            raise StorageError("S3 backend unavailable")

        async def delete(self, *args, **kwargs):
            raise StorageError("S3 backend unavailable")


def get_storage_backend() -> StorageBackend:
    from app.config import settings

    backend = settings.storage_backend.lower()
    if backend == "local":
        return LocalStorageBackend(settings.storage_local_path)
    if backend == "s3":
        return S3StorageBackend(
            bucket=settings.storage_s3_bucket or "",
            region=settings.storage_s3_region or "us-east-1",
            endpoint_url=settings.storage_s3_endpoint_url,
            access_key=settings.storage_s3_access_key,
            secret_key=settings.storage_s3_secret_key,
        )
    raise StorageError(f"Unknown storage backend: {backend}")