"""
Unit tests for model registry (Phase 1.3).
Tests both happy path and sad path scenarios.
"""

import pytest
from httpx import AsyncClient
from unittest.mock import Mock, patch
from app.models.user import User
from app.models.model import Model, ModelVersion, Deployment
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
@pytest.mark.models
@pytest.mark.unit
class TestModelRegistryHappyPath:
    """Happy path tests for model registry."""

    async def test_create_model_success(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Test successful model creation."""
        response = await test_client.post(
            "/api/v1/models",
            headers=auth_headers,
            json={
                "name": "My ML Model",
                "type": "sklearn",
            },
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "My ML Model"
        assert data["type"] == "sklearn"
        assert "id" in data
        assert "user_id" in data
        assert "created_at" in data

    async def test_get_all_models(
        self, test_client: AsyncClient, auth_headers: dict, test_model: Model
    ):
        """Test getting all models for user."""
        response = await test_client.get(
            "/api/v1/models",
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert any(model["id"] == test_model.id for model in data)

    async def test_get_model_by_id(
        self, test_client: AsyncClient, auth_headers: dict, test_model: Model
    ):
        """Test getting a specific model."""
        response = await test_client.get(
            f"/api/v1/models/{test_model.id}",
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_model.id
        assert data["name"] == test_model.name

    async def test_delete_model(
        self, test_client: AsyncClient, auth_headers: dict, test_model: Model
    ):
        """Test deleting a model."""
        response = await test_client.delete(
            f"/api/v1/models/{test_model.id}",
            headers=auth_headers,
        )
        
        assert response.status_code == 204
        
        # Verify model is deleted
        get_response = await test_client.get(
            f"/api/v1/models/{test_model.id}",
            headers=auth_headers,
        )
        assert get_response.status_code == 404

    async def test_create_model_version_success(
        self, test_client: AsyncClient, auth_headers: dict, test_model: Model
    ):
        """Test successful model version creation."""
        response = await test_client.post(
            f"/api/v1/models/{test_model.id}/versions",
            headers=auth_headers,
            json={
                "version_tag": "v1",
                "s3_path": "s3://models/user/model/v1/model.joblib",
            },
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["version_tag"] == "v1"
        assert data["model_id"] == test_model.id
        assert data["status"] == "Building"
        assert "id" in data

    async def test_get_model_versions(
        self, test_client: AsyncClient, auth_headers: dict, test_model: Model, test_model_version: ModelVersion
    ):
        """Test getting all versions for a model."""
        response = await test_client.get(
            f"/api/v1/models/{test_model.id}/versions",
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert any(version["id"] == test_model_version.id for version in data)

    async def test_update_version_status(
        self, test_client: AsyncClient, auth_headers: dict, test_model_version: ModelVersion
    ):
        """Test updating model version status."""
        from app.models.model import ModelVersionStatus
        
        response = await test_client.patch(
            f"/api/v1/versions/{test_model_version.id}/status?status=Ready",
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "Ready"

    @patch('app.services.model_service.HelmDeploymentService')
    async def test_create_deployment_success(
        self, mock_helm_class, test_client: AsyncClient, auth_headers: dict, test_model_version: ModelVersion, test_session: AsyncSession
    ):
        """Test successful deployment creation."""
        # Mock Helm deployment service
        mock_helm_service = Mock()
        mock_helm_class.return_value = mock_helm_service
        mock_helm_service.deploy_model.return_value = {
            "release_name": f"model-{test_model_version.model_id}-{test_model_version.id}-model-serving",
            "namespace": "user-1",
            "url": "http://localhost:30080/api/v1/predict/1"
        }
        
        # Ensure version is Ready and has S3 path in database
        from app.models.model import ModelVersionStatus
        test_model_version.status = ModelVersionStatus.READY
        test_model_version.s3_path = "s3://kubeserve-models/user-1/test-model/v1/model.joblib"
        test_session.add(test_model_version)
        await test_session.commit()
        await test_session.refresh(test_model_version)
        
        # Ensure version is Ready via API
        await test_client.patch(
            f"/api/v1/versions/{test_model_version.id}/status?status=Ready",
            headers=auth_headers,
        )
        
        response = await test_client.post(
            f"/api/v1/versions/{test_model_version.id}/deployments",
            headers=auth_headers,
            json={
                "replicas": 2,
            },
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["version_id"] == test_model_version.id
        assert data["replicas"] == 2
        assert "k8s_service_name" in data
        assert "id" in data

    async def test_get_deployments(
        self, test_client: AsyncClient, auth_headers: dict, test_model_version: ModelVersion, test_deployment: Deployment
    ):
        """Test getting all deployments for a version."""
        response = await test_client.get(
            f"/api/v1/versions/{test_model_version.id}/deployments",
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    @patch('app.services.model_service.HelmDeploymentService')
    async def test_delete_deployment(
        self, mock_helm_class, test_client: AsyncClient, auth_headers: dict, test_deployment: Deployment
    ):
        """Test deleting a deployment."""
        # Mock Helm undeploy service
        mock_helm_service = Mock()
        mock_helm_class.return_value = mock_helm_service
        
        response = await test_client.delete(
            f"/api/v1/deployments/{test_deployment.id}",
            headers=auth_headers,
        )
        
        assert response.status_code == 204
        # Verify Helm undeploy was called
        mock_helm_service.undeploy_model.assert_called_once()


@pytest.mark.asyncio
@pytest.mark.models
@pytest.mark.unit
class TestModelRegistrySadPath:
    """Sad path tests for model registry."""

    async def test_create_model_unauthorized(self, test_client: AsyncClient):
        """Test creating model without authentication."""
        response = await test_client.post(
            "/api/v1/models",
            json={
                "name": "Unauthorized Model",
                "type": "sklearn",
            },
        )
        
        assert response.status_code == 403

    async def test_get_model_not_found(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Test getting non-existent model."""
        response = await test_client.get(
            "/api/v1/models/99999",
            headers=auth_headers,
        )
        
        assert response.status_code == 404

    async def test_get_model_other_user(
        self, test_client: AsyncClient, auth_headers: dict, test_user_2: User, test_session: AsyncSession
    ):
        """Test getting model owned by another user."""
        from app.models.model import Model
        
        # Create model for user 2
        other_model = Model(
            name="Other User Model",
            type="sklearn",
            user_id=test_user_2.id,
        )
        test_session.add(other_model)
        await test_session.commit()
        await test_session.refresh(other_model)
        
        # Try to access with user 1's token
        response = await test_client.get(
            f"/api/v1/models/{other_model.id}",
            headers=auth_headers,
        )
        
        assert response.status_code == 404  # Should not find it (ownership check)

    async def test_delete_model_not_found(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Test deleting non-existent model."""
        response = await test_client.delete(
            "/api/v1/models/99999",
            headers=auth_headers,
        )
        
        assert response.status_code == 404

    async def test_create_version_duplicate_tag(
        self, test_client: AsyncClient, auth_headers: dict, test_model: Model, test_model_version: ModelVersion
    ):
        """Test creating version with duplicate tag."""
        response = await test_client.post(
            f"/api/v1/models/{test_model.id}/versions",
            headers=auth_headers,
            json={
                "version_tag": test_model_version.version_tag,  # Duplicate
                "s3_path": "s3://models/user/model/v1/another.joblib",
            },
        )
        
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"].lower()

    async def test_create_version_invalid_model(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Test creating version for non-existent model."""
        response = await test_client.post(
            "/api/v1/models/99999/versions",
            headers=auth_headers,
            json={
                "version_tag": "v1",
                "s3_path": "s3://models/user/model/v1/model.joblib",
            },
        )
        
        assert response.status_code == 404

    async def test_create_deployment_not_ready(
        self, test_client: AsyncClient, auth_headers: dict, test_model_version: ModelVersion
    ):
        """Test creating deployment for version that's not Ready."""
        # Ensure version is Building
        await test_client.patch(
            f"/api/v1/versions/{test_model_version.id}/status?status=Building",
            headers=auth_headers,
        )
        
        response = await test_client.post(
            f"/api/v1/versions/{test_model_version.id}/deployments",
            headers=auth_headers,
            json={
                "replicas": 1,
            },
        )
        
        assert response.status_code == 400
        assert "ready" in response.json()["detail"].lower()

    async def test_create_deployment_invalid_version(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Test creating deployment for non-existent version."""
        response = await test_client.post(
            "/api/v1/versions/99999/deployments",
            headers=auth_headers,
            json={
                "replicas": 1,
            },
        )
        
        assert response.status_code == 404

    async def test_get_deployment_not_found(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Test getting non-existent deployment."""
        response = await test_client.get(
            "/api/v1/deployments/99999",
            headers=auth_headers,
        )
        
        assert response.status_code == 404

    async def test_delete_deployment_not_found(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Test deleting non-existent deployment."""
        response = await test_client.delete(
            "/api/v1/deployments/99999",
            headers=auth_headers,
        )
        
        assert response.status_code == 404

    async def test_create_model_invalid_type(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Test creating model with invalid type."""
        response = await test_client.post(
            "/api/v1/models",
            headers=auth_headers,
            json={
                "name": "Invalid Model",
                "type": "invalid_type",
            },
        )
        
        assert response.status_code == 422  # Validation error

    async def test_create_deployment_invalid_replicas(
        self, test_client: AsyncClient, auth_headers: dict, test_model_version: ModelVersion
    ):
        """Test creating deployment with invalid replica count."""
        # Ensure version is Ready
        await test_client.patch(
            f"/api/v1/versions/{test_model_version.id}/status?status=Ready",
            headers=auth_headers,
        )
        
        response = await test_client.post(
            f"/api/v1/versions/{test_model_version.id}/deployments",
            headers=auth_headers,
            json={
                "replicas": 0,  # Invalid: must be >= 1
            },
        )
        
        assert response.status_code == 422  # Validation error

