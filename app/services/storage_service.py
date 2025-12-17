"""
Storage service for handling model artifact uploads.
Contains business logic for file validation and S3 path generation.
"""

from typing import Tuple
from fastapi import HTTPException, status, UploadFile
from minio.error import S3Error

from app.core.storage import StorageClient


class StorageService:
    """Service for storage operations with business logic."""

    # File size limits (in bytes)
    MAX_MODEL_FILE_SIZE = 500 * 1024 * 1024  # 500 MB
    MAX_REQUIREMENTS_FILE_SIZE = 1024 * 1024  # 1 MB

    # Allowed file extensions
    ALLOWED_MODEL_EXTENSIONS = {".joblib", ".pkl", ".pickle"}
    ALLOWED_REQUIREMENTS_EXTENSIONS = {".txt"}

    def __init__(self):
        """Initialize storage service with Minio client."""
        self.storage_client = StorageClient()

    def _validate_file(
        self, file: UploadFile, max_size: int, allowed_extensions: set
    ) -> None:
        """
        Validate uploaded file.

        Args:
            file: Uploaded file
            max_size: Maximum file size in bytes
            allowed_extensions: Set of allowed file extensions

        Raises:
            HTTPException: If validation fails
        """
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File must have a filename",
            )

        # Check file extension
        file_ext = None
        for ext in allowed_extensions:
            if file.filename.lower().endswith(ext):
                file_ext = ext
                break

        if file_ext is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File extension not allowed. Allowed: {', '.join(allowed_extensions)}",
            )

        # Note: File size validation would need to read the file
        # We'll do this during upload

    def generate_s3_path(
        self, user_id: int, model_name: str, version_tag: str, filename: str
    ) -> str:
        """
        Generate S3 path for a model artifact.

        Format: models/{user_id}/{model_name}/{version_tag}/{filename}

        Args:
            user_id: User ID
            model_name: Model name (sanitized)
            version_tag: Version tag (e.g., v1, v2)
            filename: Original filename

        Returns:
            S3 object key (path)
        """
        # Sanitize model name (remove special characters, spaces -> underscores)
        sanitized_model_name = "".join(
            c if c.isalnum() or c in ("-", "_") else "_" for c in model_name
        ).lower()

        return f"models/{user_id}/{sanitized_model_name}/{version_tag}/{filename}"

    async def upload_model_artifacts(
        self,
        user_id: int,
        model_name: str,
        version_tag: str,
        model_file: UploadFile,
        requirements_file: UploadFile,
    ) -> Tuple[str, str]:
        """
        Upload model artifacts (model file and requirements.txt) to S3.

        Args:
            user_id: User ID
            model_name: Model name
            version_tag: Version tag
            model_file: Uploaded model file
            requirements_file: Uploaded requirements.txt file

        Returns:
            Tuple of (model_s3_path, requirements_s3_path)

        Raises:
            HTTPException: If validation or upload fails
        """
        # Validate files
        self._validate_file(
            model_file, self.MAX_MODEL_FILE_SIZE, self.ALLOWED_MODEL_EXTENSIONS
        )
        self._validate_file(
            requirements_file,
            self.MAX_REQUIREMENTS_FILE_SIZE,
            self.ALLOWED_REQUIREMENTS_EXTENSIONS,
        )

        # Read file contents
        try:
            model_content = await model_file.read()
            requirements_content = await requirements_file.read()

            # Check file sizes
            if len(model_content) > self.MAX_MODEL_FILE_SIZE:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Model file too large. Max size: {self.MAX_MODEL_FILE_SIZE / (1024*1024):.0f} MB",
                )

            if len(requirements_content) > self.MAX_REQUIREMENTS_FILE_SIZE:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Requirements file too large. Max size: {self.MAX_REQUIREMENTS_FILE_SIZE / (1024*1024):.0f} MB",
                )

            # Generate S3 paths
            model_s3_key = self.generate_s3_path(
                user_id, model_name, version_tag, model_file.filename
            )
            requirements_s3_key = self.generate_s3_path(
                user_id, model_name, version_tag, requirements_file.filename
            )

            # Upload files
            try:
                model_s3_path = self.storage_client.upload_file(
                    model_s3_key,
                    model_content,
                    content_type="application/octet-stream",
                )
                requirements_s3_path = self.storage_client.upload_file(
                    requirements_s3_key,
                    requirements_content,
                    content_type="text/plain",
                )
            except S3Error as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to upload files to storage: {str(e)}",
                ) from e

            return (model_s3_path, requirements_s3_path)

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error during file upload: {str(e)}",
            ) from e

