"""
Unit tests for Phase 1.4: Artifact Storage (Minio/S3 integration).

Tests cover:
- Storage client operations
- Storage service file validation and upload logic
- Upload endpoint functionality
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from io import BytesIO
from fastapi import UploadFile
from minio.error import S3Error

from app.core.storage import StorageClient
from app.services.storage_service import StorageService
from app.models.model import ModelVersionStatus


@pytest.mark.storage
@pytest.mark.unit
class TestStorageClient:
    """Tests for StorageClient (Minio wrapper)."""

    @patch('app.core.storage.Minio')
    def test_storage_client_initialization(self, mock_minio_class):
        """Test StorageClient initializes Minio client correctly."""
        mock_minio_instance = Mock()
        mock_minio_class.return_value = mock_minio_instance
        mock_minio_instance.bucket_exists.return_value = True

        with patch('app.core.storage.settings') as mock_settings:
            mock_settings.MINIO_ENDPOINT = "localhost:9000"
            mock_settings.MINIO_ACCESS_KEY = "minioadmin"
            mock_settings.MINIO_SECRET_KEY = "minioadmin"
            mock_settings.MINIO_USE_SSL = False
            mock_settings.MINIO_BUCKET_NAME = "kubeserve-models"

            client = StorageClient()

            mock_minio_class.assert_called_once_with(
                "localhost:9000",
                access_key="minioadmin",
                secret_key="minioadmin",
                secure=False,
            )
            mock_minio_instance.bucket_exists.assert_called_once_with("kubeserve-models")

    @patch('app.core.storage.Minio')
    def test_storage_client_creates_bucket_if_not_exists(self, mock_minio_class):
        """Test StorageClient creates bucket if it doesn't exist."""
        mock_minio_instance = Mock()
        mock_minio_class.return_value = mock_minio_instance
        mock_minio_instance.bucket_exists.return_value = False

        with patch('app.core.storage.settings') as mock_settings:
            mock_settings.MINIO_ENDPOINT = "localhost:9000"
            mock_settings.MINIO_ACCESS_KEY = "minioadmin"
            mock_settings.MINIO_SECRET_KEY = "minioadmin"
            mock_settings.MINIO_USE_SSL = False
            mock_settings.MINIO_BUCKET_NAME = "kubeserve-models"

            client = StorageClient()

            mock_minio_instance.make_bucket.assert_called_once_with("kubeserve-models")

    @patch('app.core.storage.Minio')
    def test_upload_file_success(self, mock_minio_class):
        """Test successful file upload."""
        mock_minio_instance = Mock()
        mock_minio_class.return_value = mock_minio_instance
        mock_minio_instance.bucket_exists.return_value = True

        with patch('app.core.storage.settings') as mock_settings:
            mock_settings.MINIO_ENDPOINT = "localhost:9000"
            mock_settings.MINIO_ACCESS_KEY = "minioadmin"
            mock_settings.MINIO_SECRET_KEY = "minioadmin"
            mock_settings.MINIO_USE_SSL = False
            mock_settings.MINIO_BUCKET_NAME = "kubeserve-models"

            client = StorageClient()
            file_data = b"test file content"
            s3_path = client.upload_file("models/1/test/v1/model.joblib", file_data)

            assert s3_path == "s3://kubeserve-models/models/1/test/v1/model.joblib"
            mock_minio_instance.put_object.assert_called_once()

    @patch('app.core.storage.Minio')
    def test_upload_file_failure(self, mock_minio_class):
        """Test file upload failure handling."""
        mock_minio_instance = Mock()
        mock_minio_class.return_value = mock_minio_instance
        mock_minio_instance.bucket_exists.return_value = True
        
        # Create a proper S3Error with all required parameters (positional)
        error_response = Mock()
        error_response.status = 500
        # S3Error requires: code, message, resource, request_id, host_id, response (all positional)
        original_error = S3Error(
            "UploadError",  # code
            "Upload failed",  # message
            "resource",  # resource
            "request_id",  # request_id
            "host_id",  # host_id
            error_response  # response
        )
        mock_minio_instance.put_object.side_effect = original_error

        with patch('app.core.storage.settings') as mock_settings:
            mock_settings.MINIO_ENDPOINT = "localhost:9000"
            mock_settings.MINIO_ACCESS_KEY = "minioadmin"
            mock_settings.MINIO_SECRET_KEY = "minioadmin"
            mock_settings.MINIO_USE_SSL = False
            mock_settings.MINIO_BUCKET_NAME = "kubeserve-models"

            client = StorageClient()
            file_data = b"test file content"

            with pytest.raises(S3Error) as exc_info:
                client.upload_file("models/1/test/v1/model.joblib", file_data)

            assert "Failed to upload file" in str(exc_info.value)

    @patch('app.core.storage.Minio')
    def test_file_exists(self, mock_minio_class):
        """Test file existence check."""
        mock_minio_instance = Mock()
        mock_minio_class.return_value = mock_minio_instance
        mock_minio_instance.bucket_exists.return_value = True
        mock_minio_instance.stat_object.return_value = Mock()

        with patch('app.core.storage.settings') as mock_settings:
            mock_settings.MINIO_ENDPOINT = "localhost:9000"
            mock_settings.MINIO_ACCESS_KEY = "minioadmin"
            mock_settings.MINIO_SECRET_KEY = "minioadmin"
            mock_settings.MINIO_USE_SSL = False
            mock_settings.MINIO_BUCKET_NAME = "kubeserve-models"

            client = StorageClient()
            exists = client.file_exists("models/1/test/v1/model.joblib")

            assert exists is True

    @patch('app.core.storage.Minio')
    def test_file_not_exists(self, mock_minio_class):
        """Test file non-existence check."""
        mock_minio_instance = Mock()
        mock_minio_class.return_value = mock_minio_instance
        mock_minio_instance.bucket_exists.return_value = True
        # Create a proper S3Error mock
        error_response = Mock()
        error_response.status = 404
        mock_minio_instance.stat_object.side_effect = S3Error(
            code="NoSuchKey",
            message="Not found",
            resource="resource",
            request_id="request_id",
            host_id="host_id",
            response=error_response
        )

        with patch('app.core.storage.settings') as mock_settings:
            mock_settings.MINIO_ENDPOINT = "localhost:9000"
            mock_settings.MINIO_ACCESS_KEY = "minioadmin"
            mock_settings.MINIO_SECRET_KEY = "minioadmin"
            mock_settings.MINIO_USE_SSL = False
            mock_settings.MINIO_BUCKET_NAME = "kubeserve-models"

            client = StorageClient()
            exists = client.file_exists("models/1/test/v1/model.joblib")

            assert exists is False


@pytest.mark.asyncio
@pytest.mark.storage
@pytest.mark.unit
class TestStorageService:
    """Tests for StorageService (business logic)."""

    @pytest.fixture
    def mock_storage_client(self):
        """Mock StorageClient for testing."""
        with patch('app.services.storage_service.StorageClient') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            yield mock_client

    def test_generate_s3_path(self, mock_storage_client):
        """Test S3 path generation."""
        service = StorageService()
        path = service.generate_s3_path(
            user_id=1,
            model_name="Test Model",
            version_tag="v1",
            filename="model.joblib"
        )

        assert path == "models/1/test_model/v1/model.joblib"

    def test_generate_s3_path_sanitization(self, mock_storage_client):
        """Test S3 path generation with special characters."""
        service = StorageService()
        path = service.generate_s3_path(
            user_id=1,
            model_name="My Test Model!@#",
            version_tag="v1.0",
            filename="model.joblib"
        )

        assert path == "models/1/my_test_model___/v1.0/model.joblib"
        assert "!" not in path
        assert "@" not in path
        assert "#" not in path

    async def test_validate_file_valid_model_file(self, mock_storage_client):
        """Test validation of valid model file."""
        service = StorageService()
        file = UploadFile(
            filename="model.joblib",
            file=BytesIO(b"test content")
        )

        # Should not raise
        service._validate_file(
            file,
            service.MAX_MODEL_FILE_SIZE,
            service.ALLOWED_MODEL_EXTENSIONS
        )

    async def test_validate_file_invalid_extension(self, mock_storage_client):
        """Test validation rejects invalid file extension."""
        from fastapi import HTTPException

        service = StorageService()
        file = UploadFile(
            filename="model.txt",
            file=BytesIO(b"test content")
        )

        with pytest.raises(HTTPException) as exc_info:
            service._validate_file(
                file,
                service.MAX_MODEL_FILE_SIZE,
                service.ALLOWED_MODEL_EXTENSIONS
            )

        assert exc_info.value.status_code == 400
        assert "extension not allowed" in exc_info.value.detail.lower()

    async def test_validate_file_no_filename(self, mock_storage_client):
        """Test validation rejects file without filename."""
        from fastapi import HTTPException

        service = StorageService()
        file = UploadFile(
            filename=None,
            file=BytesIO(b"test content")
        )

        with pytest.raises(HTTPException) as exc_info:
            service._validate_file(
                file,
                service.MAX_MODEL_FILE_SIZE,
                service.ALLOWED_MODEL_EXTENSIONS
            )

        assert exc_info.value.status_code == 400
        assert "filename" in exc_info.value.detail.lower()

    async def test_upload_model_artifacts_success(self, mock_storage_client):
        """Test successful model artifact upload."""
        service = StorageService()
        
        # Mock file reads
        model_file = UploadFile(
            filename="model.joblib",
            file=BytesIO(b"model content")
        )
        requirements_file = UploadFile(
            filename="requirements.txt",
            file=BytesIO(b"numpy==1.0.0")
        )

        # Mock storage client methods
        mock_storage_client.upload_file.side_effect = [
            "s3://kubeserve-models/models/1/test_model/v1/model.joblib",
            "s3://kubeserve-models/models/1/test_model/v1/requirements.txt"
        ]

        model_path, requirements_path = await service.upload_model_artifacts(
            user_id=1,
            model_name="Test Model",
            version_tag="v1",
            model_file=model_file,
            requirements_file=requirements_file,
        )

        assert model_path == "s3://kubeserve-models/models/1/test_model/v1/model.joblib"
        assert requirements_path == "s3://kubeserve-models/models/1/test_model/v1/requirements.txt"
        assert mock_storage_client.upload_file.call_count == 2

    async def test_upload_model_artifacts_file_too_large(self, mock_storage_client):
        """Test upload rejects file that's too large."""
        from fastapi import HTTPException

        service = StorageService()
        
        # Create file larger than max size
        large_content = b"x" * (service.MAX_MODEL_FILE_SIZE + 1)
        model_file = UploadFile(
            filename="model.joblib",
            file=BytesIO(large_content)
        )
        requirements_file = UploadFile(
            filename="requirements.txt",
            file=BytesIO(b"numpy==1.0.0")
        )

        with pytest.raises(HTTPException) as exc_info:
            await service.upload_model_artifacts(
                user_id=1,
                model_name="Test Model",
                version_tag="v1",
                model_file=model_file,
                requirements_file=requirements_file,
            )

        assert exc_info.value.status_code == 400
        assert "too large" in exc_info.value.detail.lower()

    async def test_upload_model_artifacts_s3_error(self, mock_storage_client):
        """Test upload handles S3 errors."""
        from fastapi import HTTPException

        service = StorageService()
        
        model_file = UploadFile(
            filename="model.joblib",
            file=BytesIO(b"model content")
        )
        requirements_file = UploadFile(
            filename="requirements.txt",
            file=BytesIO(b"numpy==1.0.0")
        )

        # Mock S3 error
        error_response = Mock()
        error_response.status = 500
        mock_storage_client.upload_file.side_effect = S3Error(
            code="ConnectionError",
            message="Connection failed",
            resource="resource",
            request_id="request_id",
            host_id="host_id",
            response=error_response
        )

        with pytest.raises(HTTPException) as exc_info:
            await service.upload_model_artifacts(
                user_id=1,
                model_name="Test Model",
                version_tag="v1",
                model_file=model_file,
                requirements_file=requirements_file,
            )

        assert exc_info.value.status_code == 500
        assert "storage" in exc_info.value.detail.lower()


@pytest.mark.asyncio
@pytest.mark.storage
@pytest.mark.unit
class TestUploadEndpoint:
    """Tests for upload endpoint."""

    async def test_upload_success(
        self, test_client, auth_headers, test_model, test_model_version
    ):
        """Test successful model artifact upload."""
        # Create mock files
        model_content = b"fake model content"
        requirements_content = b"numpy==1.0.0\npandas==2.0.0"

        # Mock the storage service
        with patch('app.api.v1.models.StorageService') as mock_storage_service_class:
            mock_storage_service = Mock()
            mock_storage_service_class.return_value = mock_storage_service
            mock_storage_service.upload_model_artifacts = AsyncMock(
                return_value=(
                    "s3://kubeserve-models/models/1/test_model/v1/model.joblib",
                    "s3://kubeserve-models/models/1/test_model/v1/requirements.txt"
                )
            )

            # Prepare multipart form data
            files = {
                "model_file": ("model.joblib", BytesIO(model_content), "application/octet-stream"),
                "requirements_file": ("requirements.txt", BytesIO(requirements_content), "text/plain")
            }

            response = await test_client.post(
                f"/api/v1/versions/{test_model_version.id}/upload",
                headers=auth_headers,
                files=files,
            )

            assert response.status_code == 200
            data = response.json()
            assert data["s3_path"] == "s3://kubeserve-models/models/1/test_model/v1/model.joblib"
            assert data["id"] == test_model_version.id

    async def test_upload_unauthorized(self, test_client, test_model_version):
        """Test upload without authentication."""
        model_content = b"fake model content"
        requirements_content = b"numpy==1.0.0"

        files = {
            "model_file": ("model.joblib", BytesIO(model_content), "application/octet-stream"),
            "requirements_file": ("requirements.txt", BytesIO(requirements_content), "text/plain")
        }

        response = await test_client.post(
            f"/api/v1/versions/{test_model_version.id}/upload",
            files=files,
        )

        assert response.status_code == 403

    async def test_upload_invalid_version(
        self, test_client, auth_headers
    ):
        """Test upload to non-existent version."""
        model_content = b"fake model content"
        requirements_content = b"numpy==1.0.0"

        with patch('app.api.v1.models.StorageService'):
            files = {
                "model_file": ("model.joblib", BytesIO(model_content), "application/octet-stream"),
                "requirements_file": ("requirements.txt", BytesIO(requirements_content), "text/plain")
            }

            response = await test_client.post(
                "/api/v1/versions/99999/upload",
                headers=auth_headers,
                files=files,
            )

            assert response.status_code == 404

    async def test_upload_other_user_version(
        self, test_client, auth_headers, test_user_2, test_session
    ):
        """Test upload to version owned by another user."""
        from app.models.model import Model, ModelVersion, ModelType, ModelVersionStatus

        # Create model for user 2
        other_model = Model(
            name="Other User Model",
            type=ModelType.SKLEARN,
            user_id=test_user_2.id,
        )
        test_session.add(other_model)
        await test_session.commit()
        await test_session.refresh(other_model)

        other_version = ModelVersion(
            model_id=other_model.id,
            version_tag="v1",
            s3_path="",
            status=ModelVersionStatus.BUILDING,
        )
        test_session.add(other_version)
        await test_session.commit()
        await test_session.refresh(other_version)

        model_content = b"fake model content"
        requirements_content = b"numpy==1.0.0"

        with patch('app.api.v1.models.StorageService'):
            files = {
                "model_file": ("model.joblib", BytesIO(model_content), "application/octet-stream"),
                "requirements_file": ("requirements.txt", BytesIO(requirements_content), "text/plain")
            }

            response = await test_client.post(
                f"/api/v1/versions/{other_version.id}/upload",
                headers=auth_headers,
                files=files,
            )

            # Should return 403 Forbidden (access denied) or 404 Not Found
            # Both are acceptable - 403 is more accurate for unauthorized access
            assert response.status_code in [403, 404]

    async def test_upload_invalid_file_type(
        self, test_client, auth_headers, test_model_version
    ):
        """Test upload with invalid file type."""
        model_content = b"fake model content"
        requirements_content = b"numpy==1.0.0"

        # Use invalid extension for model file
        files = {
            "model_file": ("model.txt", BytesIO(model_content), "text/plain"),
            "requirements_file": ("requirements.txt", BytesIO(requirements_content), "text/plain")
        }

        response = await test_client.post(
            f"/api/v1/versions/{test_model_version.id}/upload",
            headers=auth_headers,
            files=files,
        )

        assert response.status_code == 400
        assert "extension" in response.json()["detail"].lower()

