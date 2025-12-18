"""
Unit tests for Phase 3.1: Namespace Isolation (Kubernetes operations).

Tests cover:
- Kubernetes client namespace operations
- ResourceQuota creation
- NetworkPolicy creation
- User namespace setup integration
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from kubernetes.client.rest import ApiException

from app.core.kubernetes_client import KubernetesClient


@pytest.mark.kubernetes
@pytest.mark.unit
class TestKubernetesClient:
    """Tests for KubernetesClient."""

    @patch('app.core.kubernetes_client.config')
    @patch('app.core.kubernetes_client.client')
    def test_client_initialization(self, mock_client_module, mock_config):
        """Test KubernetesClient initializes correctly."""
        mock_core_v1 = Mock()
        mock_networking_v1 = Mock()
        mock_client_module.CoreV1Api.return_value = mock_core_v1
        mock_client_module.NetworkingV1Api.return_value = mock_networking_v1

        with patch('app.core.kubernetes_client.settings') as mock_settings:
            mock_settings.KUBECONFIG = None

            k8s_client = KubernetesClient()

            mock_config.load_kube_config.assert_called_once()
            assert k8s_client.core_v1 == mock_core_v1
            assert k8s_client.networking_v1 == mock_networking_v1

    @patch('app.core.kubernetes_client.config')
    @patch('app.core.kubernetes_client.client')
    def test_client_initialization_with_custom_kubeconfig(self, mock_client_module, mock_config):
        """Test KubernetesClient initializes with custom kubeconfig path."""
        mock_core_v1 = Mock()
        mock_networking_v1 = Mock()
        mock_client_module.CoreV1Api.return_value = mock_core_v1
        mock_client_module.NetworkingV1Api.return_value = mock_networking_v1

        with patch('app.core.kubernetes_client.settings') as mock_settings:
            mock_settings.KUBECONFIG = "/custom/path/kubeconfig"

            k8s_client = KubernetesClient()

            mock_config.load_kube_config.assert_called_once_with(config_file="/custom/path/kubeconfig")

    @patch('app.core.kubernetes_client.config')
    @patch('app.core.kubernetes_client.client')
    def test_namespace_exists_true(self, mock_client_module, mock_config):
        """Test namespace_exists returns True when namespace exists."""
        mock_core_v1 = Mock()
        mock_core_v1.read_namespace.return_value = Mock()
        mock_client_module.CoreV1Api.return_value = mock_core_v1
        mock_client_module.NetworkingV1Api.return_value = Mock()

        with patch('app.core.kubernetes_client.settings'):
            k8s_client = KubernetesClient()
            exists = k8s_client.namespace_exists("user-1")

            assert exists is True
            mock_core_v1.read_namespace.assert_called_once_with(name="user-1")

    @patch('app.core.kubernetes_client.config')
    @patch('app.core.kubernetes_client.client')
    def test_namespace_exists_false(self, mock_client_module, mock_config):
        """Test namespace_exists returns False when namespace doesn't exist."""
        mock_core_v1 = Mock()
        api_exception = ApiException(status=404)
        mock_core_v1.read_namespace.side_effect = api_exception
        mock_client_module.CoreV1Api.return_value = mock_core_v1
        mock_client_module.NetworkingV1Api.return_value = Mock()

        with patch('app.core.kubernetes_client.settings'):
            k8s_client = KubernetesClient()
            exists = k8s_client.namespace_exists("user-1")

            assert exists is False

    @patch('app.core.kubernetes_client.config')
    @patch('app.core.kubernetes_client.client')
    def test_create_namespace_success(self, mock_client_module, mock_config):
        """Test successful namespace creation."""
        mock_core_v1 = Mock()
        mock_core_v1.read_namespace.side_effect = ApiException(status=404)  # Doesn't exist
        mock_core_v1.create_namespace.return_value = Mock()
        mock_client_module.CoreV1Api.return_value = mock_core_v1
        mock_client_module.NetworkingV1Api.return_value = Mock()
        mock_client_module.V1Namespace = Mock
        mock_client_module.V1ObjectMeta = Mock

        with patch('app.core.kubernetes_client.settings'):
            k8s_client = KubernetesClient()
            k8s_client.create_namespace("user-1", labels={"test": "label"})

            mock_core_v1.create_namespace.assert_called_once()

    @patch('app.core.kubernetes_client.config')
    @patch('app.core.kubernetes_client.client')
    def test_create_namespace_already_exists(self, mock_client_module, mock_config):
        """Test namespace creation when namespace already exists."""
        mock_core_v1 = Mock()
        mock_core_v1.read_namespace.return_value = Mock()  # Exists
        mock_client_module.CoreV1Api.return_value = mock_core_v1
        mock_client_module.NetworkingV1Api.return_value = Mock()

        with patch('app.core.kubernetes_client.settings'):
            k8s_client = KubernetesClient()
            k8s_client.create_namespace("user-1")

            # Should not call create_namespace if it already exists
            mock_core_v1.create_namespace.assert_not_called()

    @patch('app.core.kubernetes_client.config')
    @patch('app.core.kubernetes_client.client')
    def test_create_resource_quota_success(self, mock_client_module, mock_config):
        """Test successful ResourceQuota creation."""
        mock_core_v1 = Mock()
        mock_core_v1.create_namespaced_resource_quota.return_value = Mock()
        mock_client_module.CoreV1Api.return_value = mock_core_v1
        mock_client_module.NetworkingV1Api.return_value = Mock()
        # Make the classes callable - use a factory function that returns a MagicMock
        def make_mock_class(*args, **kwargs):
            return MagicMock()
        mock_client_module.V1ResourceQuota = make_mock_class
        mock_client_module.V1ObjectMeta = make_mock_class
        mock_client_module.V1ResourceQuotaSpec = make_mock_class

        with patch('app.core.kubernetes_client.settings'):
            k8s_client = KubernetesClient()
            k8s_client.create_resource_quota("user-1", cpu_limit="2", memory_limit="4Gi", pods_limit=5)

            mock_core_v1.create_namespaced_resource_quota.assert_called_once()
            call_args = mock_core_v1.create_namespaced_resource_quota.call_args
            assert call_args[1]['namespace'] == "user-1"

    @patch('app.core.kubernetes_client.config')
    @patch('app.core.kubernetes_client.client')
    def test_create_resource_quota_already_exists(self, mock_client_module, mock_config):
        """Test ResourceQuota creation when it already exists."""
        mock_core_v1 = Mock()
        api_exception = ApiException(status=409)  # Already exists
        mock_core_v1.create_namespaced_resource_quota.side_effect = api_exception
        mock_client_module.CoreV1Api.return_value = mock_core_v1
        mock_client_module.NetworkingV1Api.return_value = Mock()
        # Make the classes callable - use a factory function that returns a MagicMock
        def make_mock_class(*args, **kwargs):
            return MagicMock()
        mock_client_module.V1ResourceQuota = make_mock_class
        mock_client_module.V1ObjectMeta = make_mock_class
        mock_client_module.V1ResourceQuotaSpec = make_mock_class

        with patch('app.core.kubernetes_client.settings'):
            k8s_client = KubernetesClient()
            # Should not raise exception
            k8s_client.create_resource_quota("user-1")

    @patch('app.core.kubernetes_client.config')
    @patch('app.core.kubernetes_client.client')
    def test_create_network_policy_success(self, mock_client_module, mock_config):
        """Test successful NetworkPolicy creation."""
        mock_networking_v1 = Mock()
        mock_networking_v1.create_namespaced_network_policy.return_value = Mock()
        mock_client_module.CoreV1Api.return_value = Mock()
        mock_client_module.NetworkingV1Api.return_value = mock_networking_v1
        # Make the classes callable - use a factory function that returns a MagicMock
        def make_mock_class(*args, **kwargs):
            return MagicMock()
        mock_client_module.V1NetworkPolicy = make_mock_class
        mock_client_module.V1ObjectMeta = make_mock_class
        mock_client_module.V1NetworkPolicySpec = make_mock_class
        mock_client_module.V1NetworkPolicyEgressRule = make_mock_class
        mock_client_module.V1NetworkPolicyPort = make_mock_class

        with patch('app.core.kubernetes_client.settings') as mock_settings:
            mock_settings.MINIO_ENDPOINT = "localhost:9000"
            k8s_client = KubernetesClient()
            k8s_client.create_network_policy("user-1", "localhost:9000", minio_port=9000)

            mock_networking_v1.create_namespaced_network_policy.assert_called_once()
            call_args = mock_networking_v1.create_namespaced_network_policy.call_args
            assert call_args[1]['namespace'] == "user-1"

    @patch('app.core.kubernetes_client.config')
    @patch('app.core.kubernetes_client.client')
    def test_setup_user_namespace_complete(self, mock_client_module, mock_config):
        """Test complete user namespace setup."""
        mock_core_v1 = Mock()
        mock_networking_v1 = Mock()
        # Namespace doesn't exist
        mock_core_v1.read_namespace.side_effect = ApiException(status=404)
        mock_core_v1.create_namespace.return_value = Mock()
        mock_core_v1.create_namespaced_resource_quota.return_value = Mock()
        mock_networking_v1.create_namespaced_network_policy.return_value = Mock()
        mock_client_module.CoreV1Api.return_value = mock_core_v1
        mock_client_module.NetworkingV1Api.return_value = mock_networking_v1
        # Make the classes callable - use a factory function that returns a MagicMock
        def make_mock_class(*args, **kwargs):
            return MagicMock()
        mock_client_module.V1Namespace = make_mock_class
        mock_client_module.V1ObjectMeta = make_mock_class
        mock_client_module.V1ResourceQuota = make_mock_class
        mock_client_module.V1ResourceQuotaSpec = make_mock_class
        mock_client_module.V1NetworkPolicy = make_mock_class
        mock_client_module.V1NetworkPolicySpec = make_mock_class
        mock_client_module.V1NetworkPolicyEgressRule = make_mock_class
        mock_client_module.V1NetworkPolicyPort = make_mock_class

        with patch('app.core.kubernetes_client.settings') as mock_settings:
            mock_settings.MINIO_ENDPOINT = "localhost:9000"
            k8s_client = KubernetesClient()
            namespace = k8s_client.setup_user_namespace(user_id=1)

            assert namespace == "user-1"
            mock_core_v1.create_namespace.assert_called_once()
            mock_core_v1.create_namespaced_resource_quota.assert_called_once()
            mock_networking_v1.create_namespaced_network_policy.assert_called_once()

    @patch('app.core.kubernetes_client.config')
    @patch('app.core.kubernetes_client.client')
    def test_delete_namespace_success(self, mock_client_module, mock_config):
        """Test successful namespace deletion."""
        mock_core_v1 = Mock()
        mock_core_v1.delete_namespace.return_value = Mock()
        mock_client_module.CoreV1Api.return_value = mock_core_v1
        mock_client_module.NetworkingV1Api.return_value = Mock()

        with patch('app.core.kubernetes_client.settings'):
            k8s_client = KubernetesClient()
            k8s_client.delete_namespace("user-1")

            mock_core_v1.delete_namespace.assert_called_once_with(name="user-1")

    @patch('app.core.kubernetes_client.config')
    @patch('app.core.kubernetes_client.client')
    def test_delete_namespace_not_found(self, mock_client_module, mock_config):
        """Test namespace deletion when namespace doesn't exist."""
        mock_core_v1 = Mock()
        api_exception = ApiException(status=404)
        mock_core_v1.delete_namespace.side_effect = api_exception
        mock_client_module.CoreV1Api.return_value = mock_core_v1
        mock_client_module.NetworkingV1Api.return_value = Mock()

        with patch('app.core.kubernetes_client.settings'):
            k8s_client = KubernetesClient()
            # Should not raise exception
            k8s_client.delete_namespace("user-1")


@pytest.mark.kubernetes
@pytest.mark.unit
class TestUserServiceNamespaceIntegration:
    """Tests for user service integration with Kubernetes namespace creation."""

    @pytest.mark.asyncio
    async def test_create_user_creates_namespace(
        self, test_client
    ):
        """Test that user registration creates Kubernetes namespace."""
        with patch('app.core.kubernetes_client.KubernetesClient') as mock_k8s_class:
            mock_k8s_client = Mock()
            mock_k8s_class.return_value = mock_k8s_client
            mock_k8s_client.setup_user_namespace.return_value = "user-1"

            response = await test_client.post(
                "/api/v1/auth/register",
                json={
                    "email": "newuser@example.com",
                    "password": "securepass123",
                },
            )

            assert response.status_code == 201
            # Verify Kubernetes client was called
            mock_k8s_client.setup_user_namespace.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_user_handles_k8s_failure_gracefully(
        self, test_client
    ):
        """Test that user creation succeeds even if Kubernetes fails."""
        with patch('app.core.kubernetes_client.KubernetesClient') as mock_k8s_class:
            mock_k8s_client = Mock()
            mock_k8s_class.return_value = mock_k8s_client
            mock_k8s_client.setup_user_namespace.side_effect = Exception("K8s unavailable")

            response = await test_client.post(
                "/api/v1/auth/register",
                json={
                    "email": "newuser2@example.com",
                    "password": "securepass123",
                },
            )

            # User should still be created
            assert response.status_code == 201
            data = response.json()
            assert data["email"] == "newuser2@example.com"

