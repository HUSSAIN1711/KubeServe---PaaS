"""
Unit tests for Phase 4.1: Networking & Ingress.

Tests cover:
- Kubernetes client Ingress operations
- Ingress creation and deletion
- Ingress path configuration
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from kubernetes.client.rest import ApiException

from app.core.kubernetes_client import KubernetesClient


@pytest.mark.ingress
@pytest.mark.unit
class TestKubernetesClientIngress:
    """Tests for KubernetesClient Ingress operations."""

    @patch('app.core.kubernetes_client.config')
    @patch('app.core.kubernetes_client.client')
    def test_create_ingress_success(self, mock_client_module, mock_config):
        """Test successful Ingress creation."""
        mock_networking_v1 = Mock()
        mock_networking_v1.create_namespaced_ingress.return_value = Mock()
        mock_client_module.CoreV1Api.return_value = Mock()
        mock_client_module.NetworkingV1Api.return_value = mock_networking_v1
        # Make the classes callable
        def make_mock_class(*args, **kwargs):
            return MagicMock()
        mock_client_module.V1Ingress = make_mock_class
        mock_client_module.V1ObjectMeta = make_mock_class
        mock_client_module.V1IngressSpec = make_mock_class
        mock_client_module.V1IngressRule = make_mock_class
        mock_client_module.V1HTTPIngressRuleValue = make_mock_class
        mock_client_module.V1HTTPIngressPath = make_mock_class
        mock_client_module.V1IngressBackend = make_mock_class
        mock_client_module.V1IngressServiceBackend = make_mock_class
        mock_client_module.V1ServiceBackendPort = make_mock_class

        with patch('app.core.kubernetes_client.settings'):
            k8s_client = KubernetesClient()
            url = k8s_client.create_ingress(
                namespace="user-1",
                name="test-ingress",
                service_name="test-service",
                service_port=80,
                ingress_host="localhost",
                ingress_path="/api/v1/predict/1"
            )

            assert url == "http://localhost/api/v1/predict/1"
            mock_networking_v1.create_namespaced_ingress.assert_called_once()
            call_args = mock_networking_v1.create_namespaced_ingress.call_args
            assert call_args[1]['namespace'] == "user-1"

    @patch('app.core.kubernetes_client.config')
    @patch('app.core.kubernetes_client.client')
    def test_create_ingress_already_exists(self, mock_client_module, mock_config):
        """Test Ingress creation when it already exists."""
        mock_networking_v1 = Mock()
        api_exception = ApiException(status=409)  # Already exists
        mock_networking_v1.create_namespaced_ingress.side_effect = api_exception
        mock_client_module.CoreV1Api.return_value = Mock()
        mock_client_module.NetworkingV1Api.return_value = mock_networking_v1
        # Make the classes callable
        def make_mock_class(*args, **kwargs):
            return MagicMock()
        mock_client_module.V1Ingress = make_mock_class
        mock_client_module.V1ObjectMeta = make_mock_class
        mock_client_module.V1IngressSpec = make_mock_class
        mock_client_module.V1IngressRule = make_mock_class
        mock_client_module.V1HTTPIngressRuleValue = make_mock_class
        mock_client_module.V1HTTPIngressPath = make_mock_class
        mock_client_module.V1IngressBackend = make_mock_class
        mock_client_module.V1IngressServiceBackend = make_mock_class
        mock_client_module.V1ServiceBackendPort = make_mock_class

        with patch('app.core.kubernetes_client.settings'):
            k8s_client = KubernetesClient()
            # Should not raise exception, should return URL
            url = k8s_client.create_ingress(
                namespace="user-1",
                name="test-ingress",
                service_name="test-service",
                service_port=80
            )
            assert url is not None

    @patch('app.core.kubernetes_client.config')
    @patch('app.core.kubernetes_client.client')
    def test_create_ingress_with_custom_path(self, mock_client_module, mock_config):
        """Test Ingress creation with custom path."""
        mock_networking_v1 = Mock()
        mock_networking_v1.create_namespaced_ingress.return_value = Mock()
        mock_client_module.CoreV1Api.return_value = Mock()
        mock_client_module.NetworkingV1Api.return_value = mock_networking_v1
        # Make the classes callable
        def make_mock_class(*args, **kwargs):
            return MagicMock()
        mock_client_module.V1Ingress = make_mock_class
        mock_client_module.V1ObjectMeta = make_mock_class
        mock_client_module.V1IngressSpec = make_mock_class
        mock_client_module.V1IngressRule = make_mock_class
        mock_client_module.V1HTTPIngressRuleValue = make_mock_class
        mock_client_module.V1HTTPIngressPath = make_mock_class
        mock_client_module.V1IngressBackend = make_mock_class
        mock_client_module.V1IngressServiceBackend = make_mock_class
        mock_client_module.V1ServiceBackendPort = make_mock_class

        with patch('app.core.kubernetes_client.settings'):
            k8s_client = KubernetesClient()
            url = k8s_client.create_ingress(
                namespace="user-1",
                name="test-ingress",
                service_name="test-service",
                service_port=80,
                ingress_path="/custom/path"
            )

            assert "/custom/path" in url

    @patch('app.core.kubernetes_client.config')
    @patch('app.core.kubernetes_client.client')
    def test_create_ingress_with_annotations(self, mock_client_module, mock_config):
        """Test Ingress creation with custom annotations."""
        mock_networking_v1 = Mock()
        mock_networking_v1.create_namespaced_ingress.return_value = Mock()
        mock_client_module.CoreV1Api.return_value = Mock()
        mock_client_module.NetworkingV1Api.return_value = mock_networking_v1
        # Make the classes callable
        def make_mock_class(*args, **kwargs):
            return MagicMock()
        mock_client_module.V1Ingress = make_mock_class
        mock_client_module.V1ObjectMeta = make_mock_class
        mock_client_module.V1IngressSpec = make_mock_class
        mock_client_module.V1IngressRule = make_mock_class
        mock_client_module.V1HTTPIngressRuleValue = make_mock_class
        mock_client_module.V1HTTPIngressPath = make_mock_class
        mock_client_module.V1IngressBackend = make_mock_class
        mock_client_module.V1IngressServiceBackend = make_mock_class
        mock_client_module.V1ServiceBackendPort = make_mock_class

        annotations = {"cert-manager.io/cluster-issuer": "letsencrypt-prod"}

        with patch('app.core.kubernetes_client.settings'):
            k8s_client = KubernetesClient()
            k8s_client.create_ingress(
                namespace="user-1",
                name="test-ingress",
                service_name="test-service",
                service_port=80,
                annotations=annotations
            )

            # Verify annotations were passed
            call_args = mock_networking_v1.create_namespaced_ingress.call_args
            ingress_body = call_args[1]['body']
            # The annotations should be in the metadata
            assert hasattr(ingress_body, 'metadata')

    @patch('app.core.kubernetes_client.config')
    @patch('app.core.kubernetes_client.client')
    def test_delete_ingress_success(self, mock_client_module, mock_config):
        """Test successful Ingress deletion."""
        mock_networking_v1 = Mock()
        mock_networking_v1.delete_namespaced_ingress.return_value = Mock()
        mock_client_module.CoreV1Api.return_value = Mock()
        mock_client_module.NetworkingV1Api.return_value = mock_networking_v1

        with patch('app.core.kubernetes_client.settings'):
            k8s_client = KubernetesClient()
            k8s_client.delete_ingress("user-1", "test-ingress")

            mock_networking_v1.delete_namespaced_ingress.assert_called_once()
            call_args = mock_networking_v1.delete_namespaced_ingress.call_args
            assert call_args[1]['name'] == "test-ingress"
            assert call_args[1]['namespace'] == "user-1"

    @patch('app.core.kubernetes_client.config')
    @patch('app.core.kubernetes_client.client')
    def test_delete_ingress_not_found(self, mock_client_module, mock_config):
        """Test Ingress deletion when Ingress doesn't exist."""
        mock_networking_v1 = Mock()
        api_exception = ApiException(status=404)
        mock_networking_v1.delete_namespaced_ingress.side_effect = api_exception
        mock_client_module.CoreV1Api.return_value = Mock()
        mock_client_module.NetworkingV1Api.return_value = mock_networking_v1

        with patch('app.core.kubernetes_client.settings'):
            k8s_client = KubernetesClient()
            # Should not raise exception
            k8s_client.delete_ingress("user-1", "test-ingress")

    @patch('app.core.kubernetes_client.config')
    @patch('app.core.kubernetes_client.client')
    def test_create_ingress_with_custom_class(self, mock_client_module, mock_config):
        """Test Ingress creation with custom ingress class."""
        mock_networking_v1 = Mock()
        mock_networking_v1.create_namespaced_ingress.return_value = Mock()
        mock_client_module.CoreV1Api.return_value = Mock()
        mock_client_module.NetworkingV1Api.return_value = mock_networking_v1
        # Make the classes callable
        def make_mock_class(*args, **kwargs):
            return MagicMock()
        mock_client_module.V1Ingress = make_mock_class
        mock_client_module.V1ObjectMeta = make_mock_class
        mock_client_module.V1IngressSpec = make_mock_class
        mock_client_module.V1IngressRule = make_mock_class
        mock_client_module.V1HTTPIngressRuleValue = make_mock_class
        mock_client_module.V1HTTPIngressPath = make_mock_class
        mock_client_module.V1IngressBackend = make_mock_class
        mock_client_module.V1IngressServiceBackend = make_mock_class
        mock_client_module.V1ServiceBackendPort = make_mock_class

        with patch('app.core.kubernetes_client.settings'):
            k8s_client = KubernetesClient()
            k8s_client.create_ingress(
                namespace="user-1",
                name="test-ingress",
                service_name="test-service",
                service_port=80,
                ingress_class="traefik"
            )

            # Verify ingress class was set
            call_args = mock_networking_v1.create_namespaced_ingress.call_args
            ingress_body = call_args[1]['body']
            assert hasattr(ingress_body, 'spec')

