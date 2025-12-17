"""
Minio/S3 storage client wrapper.
Handles connection and basic operations with Minio (S3-compatible storage).
"""

from minio import Minio
from minio.error import S3Error
from typing import BinaryIO, Optional
import io

from app.config import settings


class StorageClient:
    """
    Wrapper around Minio client for S3-compatible storage operations.
    Handles bucket creation and file uploads.
    """

    def __init__(self):
        """Initialize Minio client with settings."""
        self.client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_USE_SSL,
        )
        self.bucket_name = settings.MINIO_BUCKET_NAME
        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self) -> None:
        """
        Ensure the bucket exists, create it if it doesn't.

        Raises:
            S3Error: If bucket creation fails
        """
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
        except S3Error as e:
            # Re-raise with more context
            raise S3Error(
                f"Failed to ensure bucket '{self.bucket_name}' exists: {str(e)}"
            ) from e

    def upload_file(
        self,
        object_name: str,
        file_data: bytes,
        content_type: str = "application/octet-stream",
        length: Optional[int] = None,
    ) -> str:
        """
        Upload a file to S3/Minio.

        Args:
            object_name: S3 object key (path)
            file_data: File content as bytes
            content_type: MIME type of the file
            length: Length of file data (if None, uses len(file_data))

        Returns:
            S3 path (s3://bucket/object_name)

        Raises:
            S3Error: If upload fails
        """
        if length is None:
            length = len(file_data)

        try:
            file_obj = io.BytesIO(file_data)
            self.client.put_object(
                self.bucket_name,
                object_name,
                file_obj,
                length=length,
                content_type=content_type,
            )
            return f"s3://{self.bucket_name}/{object_name}"
        except S3Error as e:
            # Re-raise the original S3Error with additional context in message
            # S3Error requires all parameters, so we preserve the original error
            raise S3Error(
                code=getattr(e, 'code', 'UploadError'),
                message=f"Failed to upload file '{object_name}': {getattr(e, 'message', str(e))}",
                resource=getattr(e, 'resource', object_name),
                request_id=getattr(e, 'request_id', None),
                host_id=getattr(e, 'host_id', None),
                response=getattr(e, 'response', None)
            ) from e

    def get_file(self, object_name: str) -> bytes:
        """
        Download a file from S3/Minio.

        Args:
            object_name: S3 object key (path)

        Returns:
            File content as bytes

        Raises:
            S3Error: If download fails
        """
        try:
            response = self.client.get_object(self.bucket_name, object_name)
            return response.read()
        except S3Error as e:
            # Re-raise the original S3Error with additional context
            raise S3Error(
                code=getattr(e, 'code', 'GetError'),
                message=f"Failed to get file '{object_name}': {getattr(e, 'message', str(e))}",
                resource=getattr(e, 'resource', object_name),
                request_id=getattr(e, 'request_id', None),
                host_id=getattr(e, 'host_id', None),
                response=getattr(e, 'response', None)
            ) from e
        finally:
            response.close()
            response.release_conn()

    def delete_file(self, object_name: str) -> None:
        """
        Delete a file from S3/Minio.

        Args:
            object_name: S3 object key (path)

        Raises:
            S3Error: If deletion fails
        """
        try:
            self.client.remove_object(self.bucket_name, object_name)
        except S3Error as e:
            # Re-raise the original S3Error with additional context
            raise S3Error(
                code=getattr(e, 'code', 'DeleteError'),
                message=f"Failed to delete file '{object_name}': {getattr(e, 'message', str(e))}",
                resource=getattr(e, 'resource', object_name),
                request_id=getattr(e, 'request_id', None),
                host_id=getattr(e, 'host_id', None),
                response=getattr(e, 'response', None)
            ) from e

    def file_exists(self, object_name: str) -> bool:
        """
        Check if a file exists in S3/Minio.

        Args:
            object_name: S3 object key (path)

        Returns:
            True if file exists, False otherwise
        """
        try:
            self.client.stat_object(self.bucket_name, object_name)
            return True
        except S3Error:
            return False

