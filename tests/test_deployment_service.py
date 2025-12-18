"""
Unit tests for Phase 3.3: The Deploy Endpoint (Helm deployment service).

Tests cover:
- Helm deployment service operations
- Deployment service integration with Helm
- Error handling and cleanup
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, call
from pathlib import Path
import subprocess

from app.services.deployment_service import HelmDeploymentService
from app.services.model_service import DeploymentService
from app.models.model import ModelVersionStatus
from app.schemas.model import DeploymentCreate


@pytest.mark.deployment
@pytest.mark.unit
class TestHelmDeploymentService:
    """Tests for HelmDeploymentService."""

    def test_service_initialization(self):
        """Test HelmDeploymentService initializes correctly."""
        service = HelmDeploymentService()
        assert service.chart_path.exists() or service.chart_path.parent.exists()
        assert service.chart_path.name == "model-serving"

    @patch('app.services.deployment_service.subprocess.run')
    def test_deploy_model_success(self, mock_subprocess):
        """Test successful model deployment via Helm."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Release deployed successfully"
        mock_result.stderr = ""
        mock_subprocess.return_value = mock_result

        service = HelmDeploymentService()
        
        with patch('app.services.deployment_service.settings') as mock_settings:
            mock_settings.MINIO_ENDPOINT = "localhost:9000"
            mock_settings.MINIO_ACCESS_KEY = "minioadmin"
            mock_settings.MINIO_SECRET_KEY = "minioadmin"
            mock_settings.MINIO_BUCKET_NAME = "kubeserve-models"
            mock_settings.MINIO_USE_SSL = False
            mock_settings.INGRESS_HOST = "localhost"
            mock_settings.INGRESS_BASE_PATH = "/api/v1/predict"

            result = service.deploy_model(
                release_name="test-release",
                namespace="user-1",
                s3_path="s3://bucket/model.joblib",
                s3_endpoint="minio:9000",
                s3_access_key="minioadmin",
                s3_secret_key="minioadmin",
                s3_bucket="bucket",
                replicas=2
            )

            assert result["release_name"] == "test-release"
            assert result["namespace"] == "user-1"
            assert result["url"] is not None
            assert "localhost" in result["url"]
            mock_subprocess.assert_called_once()

    @patch('app.services.deployment_service.subprocess.run')
    def test_deploy_model_helm_failure(self, mock_subprocess):
        """Test deployment failure when Helm install fails."""
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "Error: chart not found"
        mock_subprocess.return_value = mock_result

        service = HelmDeploymentService()
        
        with patch('app.services.deployment_service.settings'):
            with pytest.raises(subprocess.SubprocessError):
                service.deploy_model(
                    release_name="test-release",
                    namespace="user-1",
                    s3_path="s3://bucket/model.joblib",
                    s3_endpoint="minio:9000",
                    s3_access_key="minioadmin",
                    s3_secret_key="minioadmin",
                    s3_bucket="bucket"
                )

    @patch('app.services.deployment_service.subprocess.run')
    def test_undeploy_model_success(self, mock_subprocess):
        """Test successful model undeployment via Helm."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Release uninstalled"
        mock_result.stderr = ""
        mock_subprocess.return_value = mock_result

        service = HelmDeploymentService()
        service.undeploy_model("test-release", "user-1")

        mock_subprocess.assert_called_once()
        call_args = mock_subprocess.call_args[0][0]
        assert "uninstall" in call_args
        assert "test-release" in call_args
        assert "user-1" in call_args

    @patch('app.services.deployment_service.subprocess.run')
    def test_undeploy_model_not_found(self, mock_subprocess):
        """Test undeployment when release doesn't exist."""
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "Error: release not found"
        mock_subprocess.return_value = mock_result

        service = HelmDeploymentService()
        # Should not raise exception if release not found
        service.undeploy_model("test-release", "user-1")

    @patch('app.services.deployment_service.subprocess.run')
    def test_get_deployment_status(self, mock_subprocess):
        """Test getting deployment status."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = '{"status": "deployed"}'
        mock_result.stderr = ""
        mock_subprocess.return_value = mock_result

        service = HelmDeploymentService()
        status = service.get_deployment_status("test-release", "user-1")

        assert status["status"] == "deployed"
        mock_subprocess.assert_called_once()

    @patch('app.services.deployment_service.subprocess.run')
    def test_get_deployment_status_not_found(self, mock_subprocess):
        """Test getting status for non-existent deployment."""
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "Error: release not found"
        mock_subprocess.return_value = mock_result

        service = HelmDeploymentService()
        status = service.get_deployment_status("test-release", "user-1")

        assert status["status"] == "not_found"
        assert "error" in status

    @patch('app.services.deployment_service.subprocess.run')
    def test_deploy_model_with_custom_ingress_path(self, mock_subprocess):
        """Test deployment with custom ingress path."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Release deployed"
        mock_result.stderr = ""
        mock_subprocess.return_value = mock_result

        service = HelmDeploymentService()
        
        with patch('app.services.deployment_service.settings') as mock_settings:
            mock_settings.MINIO_ENDPOINT = "localhost:9000"
            mock_settings.INGRESS_HOST = "localhost"
            mock_settings.INGRESS_BASE_PATH = "/api/v1/predict"

            result = service.deploy_model(
                release_name="test-release",
                namespace="user-1",
                s3_path="s3://bucket/model.joblib",
                s3_endpoint="minio:9000",
                s3_access_key="minioadmin",
                s3_secret_key="minioadmin",
                s3_bucket="bucket",
                ingress_path="/api/v1/predict/123"
            )

            assert "/api/v1/predict/123" in result["url"]
            # Verify ingress path was passed to Helm
            call_args = mock_subprocess.call_args[0][0]
            assert any("ingress.hosts[0].paths[0].path=/api/v1/predict/123" in str(arg) for arg in call_args)


@pytest.mark.deployment
@pytest.mark.unit
class TestDeploymentServiceIntegration:
    """Tests for DeploymentService integration with Helm deployments."""

    @pytest.mark.asyncio
    async def test_create_deployment_triggers_helm_deploy(
        self, test_session, test_model_version_ready, test_user
    ):
        """Test that creating a deployment triggers Helm deployment."""
        from app.services.model_service import DeploymentService
        from app.schemas.model import DeploymentCreate

        # Ensure the model belongs to test_user
        test_model_version_ready.model.user_id = test_user.id
        test_session.add(test_model_version_ready.model)
        await test_session.commit()

        deployment_data = DeploymentCreate(
            version_id=test_model_version_ready.id,
            replicas=1
        )

        with patch('app.services.model_service.HelmDeploymentService') as mock_helm_class:
            mock_helm_service = Mock()
            mock_helm_class.return_value = mock_helm_service
            mock_helm_service.deploy_model.return_value = {
                "release_name": "test-release",
                "namespace": "user-1",
                "url": "http://localhost:30080/api/v1/predict/1"
            }

            service = DeploymentService(test_session)
            result = await service.create_deployment(deployment_data, user_id=test_user.id)

            # Verify Helm service was called
            mock_helm_service.deploy_model.assert_called_once()
            assert result.url is not None
            assert "localhost" in result.url

    @pytest.mark.asyncio
    async def test_create_deployment_handles_helm_failure(
        self, test_session, test_model_version_ready, test_user
    ):
        """Test that Helm deployment failure cleans up database record."""
        from app.services.model_service import DeploymentService
        from app.schemas.model import DeploymentCreate

        # Ensure the model belongs to test_user
        test_model_version_ready.model.user_id = test_user.id
        test_session.add(test_model_version_ready.model)
        await test_session.commit()

        deployment_data = DeploymentCreate(
            version_id=test_model_version_ready.id,
            replicas=1
        )

        with patch('app.services.model_service.HelmDeploymentService') as mock_helm_class:
            mock_helm_service = Mock()
            mock_helm_class.return_value = mock_helm_service
            mock_helm_service.deploy_model.side_effect = Exception("Helm install failed")

            service = DeploymentService(test_session)
            
            with pytest.raises(Exception) as exc_info:
                await service.create_deployment(deployment_data, user_id=test_user.id)
            
            assert "Failed to deploy model to Kubernetes" in str(exc_info.value)
            
            # Verify deployment was not created in database
            deployments = await service.repository.get_by_version_id(test_model_version_ready.id)
            assert len(deployments) == 0

    @pytest.mark.asyncio
    async def test_create_deployment_requires_s3_path(
        self, test_session, test_model_version, test_user
    ):
        """Test that deployment requires model version to have S3 path."""
        from app.services.model_service import DeploymentService
        from app.schemas.model import DeploymentCreate

        # Ensure the model belongs to test_user
        test_model_version.model.user_id = test_user.id
        # Ensure version has no S3 path
        test_model_version.s3_path = ""
        test_session.add(test_model_version.model)
        test_session.add(test_model_version)
        await test_session.commit()

        deployment_data = DeploymentCreate(
            version_id=test_model_version.id,
            replicas=1
        )

        service = DeploymentService(test_session)
        
        with pytest.raises(Exception) as exc_info:
            await service.create_deployment(deployment_data, user_id=test_user.id)
        
        assert "S3 path" in str(exc_info.value) or "upload" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_delete_deployment_triggers_helm_undeploy(
        self, test_session, test_deployment, test_user
    ):
        """Test that deleting a deployment triggers Helm undeployment."""
        from app.services.model_service import DeploymentService

        # Ensure ownership
        test_deployment.model_version.model.user_id = test_user.id
        test_session.add(test_deployment.model_version.model)
        await test_session.commit()

        with patch('app.services.model_service.HelmDeploymentService') as mock_helm_class:
            mock_helm_service = Mock()
            mock_helm_class.return_value = mock_helm_service

            service = DeploymentService(test_session)
            await service.delete_deployment(test_deployment.id, user_id=test_user.id)

            # Verify Helm service was called
            mock_helm_service.undeploy_model.assert_called_once()
            # undeploy_model is called with keyword arguments: release_name and namespace
            call_kwargs = mock_helm_service.undeploy_model.call_args[1]
            assert call_kwargs["release_name"] == test_deployment.k8s_service_name
            assert call_kwargs["namespace"] == f"user-{test_user.id}"

    @pytest.mark.asyncio
    async def test_delete_deployment_handles_helm_failure_gracefully(
        self, test_session, test_deployment, test_user
    ):
        """Test that Helm undeployment failure doesn't prevent database cleanup."""
        from app.services.model_service import DeploymentService

        # Ensure ownership
        test_deployment.model_version.model.user_id = test_user.id
        test_session.add(test_deployment.model_version.model)
        await test_session.commit()

        with patch('app.services.model_service.HelmDeploymentService') as mock_helm_class:
            mock_helm_service = Mock()
            mock_helm_class.return_value = mock_helm_service
            mock_helm_service.undeploy_model.side_effect = Exception("Helm uninstall failed")

            service = DeploymentService(test_session)
            # Should not raise exception
            await service.delete_deployment(test_deployment.id, user_id=test_user.id)

            # Verify deployment was deleted from database
            deployment = await service.repository.get_by_id(test_deployment.id)
            assert deployment is None

    @pytest.mark.asyncio
    async def test_create_deployment_parses_s3_path(
        self, test_session, test_model_version_ready, test_user
    ):
        """Test that S3 path is correctly parsed and passed to Helm."""
        from app.services.model_service import DeploymentService
        from app.schemas.model import DeploymentCreate

        # Ensure the model belongs to test_user
        test_model_version_ready.model.user_id = test_user.id
        # Set a specific S3 path
        test_model_version_ready.s3_path = "s3://kubeserve-models/user-1/model/v1/model.joblib"
        test_session.add(test_model_version_ready.model)
        test_session.add(test_model_version_ready)
        await test_session.commit()

        deployment_data = DeploymentCreate(
            version_id=test_model_version_ready.id,
            replicas=1
        )

        with patch('app.services.model_service.HelmDeploymentService') as mock_helm_class:
            mock_helm_service = Mock()
            mock_helm_class.return_value = mock_helm_service
            mock_helm_service.deploy_model.return_value = {
                "release_name": "test-release",
                "namespace": "user-1",
                "url": "http://localhost:30080/api/v1/predict/1"
            }

            service = DeploymentService(test_session)
            await service.create_deployment(deployment_data, user_id=test_user.id)

            # Verify S3 path was passed correctly
            call_args = mock_helm_service.deploy_model.call_args
            assert "s3://kubeserve-models" in call_args[1]["s3_path"]
            assert call_args[1]["s3_bucket"] == "kubeserve-models"

