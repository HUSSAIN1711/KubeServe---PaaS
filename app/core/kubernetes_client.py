"""
Kubernetes client wrapper for namespace and resource management.
Handles namespace creation, ResourceQuotas, and NetworkPolicies.
"""

import logging
from typing import Optional
from kubernetes import client, config
from kubernetes.client.rest import ApiException
from typing import List, Dict, Optional

from app.config import settings

logger = logging.getLogger(__name__)


class KubernetesClient:
    """
    Wrapper around Kubernetes Python client for namespace operations.
    Handles namespace creation, ResourceQuotas, and NetworkPolicies.
    """

    def __init__(self):
        """Initialize Kubernetes client with configuration."""
        try:
            if settings.KUBECONFIG:
                config.load_kube_config(config_file=settings.KUBECONFIG)
            else:
                config.load_kube_config()  # Uses default ~/.kube/config
            logger.info("Kubernetes client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to load Kubernetes config: {str(e)}")
            raise

        self.core_v1 = client.CoreV1Api()
        self.networking_v1 = client.NetworkingV1Api()

    def namespace_exists(self, namespace: str) -> bool:
        """
        Check if a namespace exists.

        Args:
            namespace: Namespace name

        Returns:
            True if namespace exists, False otherwise
        """
        try:
            self.core_v1.read_namespace(name=namespace)
            return True
        except ApiException as e:
            if e.status == 404:
                return False
            raise

    def create_namespace(self, namespace: str, labels: Optional[dict] = None) -> None:
        """
        Create a Kubernetes namespace.

        Args:
            namespace: Namespace name
            labels: Optional labels to add to the namespace

        Raises:
            ApiException: If namespace creation fails
        """
        if self.namespace_exists(namespace):
            logger.info(f"Namespace {namespace} already exists")
            return

        namespace_body = client.V1Namespace(
            metadata=client.V1ObjectMeta(
                name=namespace,
                labels=labels or {}
            )
        )

        try:
            self.core_v1.create_namespace(body=namespace_body)
            logger.info(f"Created namespace: {namespace}")
        except ApiException as e:
            if e.status == 409:  # Already exists
                logger.info(f"Namespace {namespace} already exists")
            else:
                logger.error(f"Failed to create namespace {namespace}: {str(e)}")
                raise

    def create_resource_quota(
        self,
        namespace: str,
        cpu_limit: str = "2",
        memory_limit: str = "4Gi",
        pods_limit: int = 5
    ) -> None:
        """
        Create a ResourceQuota for a namespace.

        Args:
            namespace: Namespace name
            cpu_limit: CPU limit (e.g., "2" for 2 cores)
            memory_limit: Memory limit (e.g., "4Gi" for 4 GiB)
            pods_limit: Maximum number of pods

        Raises:
            ApiException: If ResourceQuota creation fails
        """
        resource_quota = client.V1ResourceQuota(
            metadata=client.V1ObjectMeta(
                name="user-resource-quota",
                namespace=namespace
            ),
            spec=client.V1ResourceQuotaSpec(
                hard={
                    "requests.cpu": cpu_limit,
                    "limits.cpu": cpu_limit,
                    "requests.memory": memory_limit,
                    "limits.memory": memory_limit,
                    "pods": str(pods_limit)
                }
            )
        )

        try:
            self.core_v1.create_namespaced_resource_quota(
                namespace=namespace,
                body=resource_quota
            )
            logger.info(f"Created ResourceQuota for namespace {namespace}")
        except ApiException as e:
            if e.status == 409:  # Already exists
                logger.info(f"ResourceQuota for namespace {namespace} already exists")
            else:
                logger.error(f"Failed to create ResourceQuota for {namespace}: {str(e)}")
                raise

    def create_network_policy(
        self,
        namespace: str,
        minio_endpoint: str,
        minio_port: int = 9000
    ) -> None:
        """
        Create a NetworkPolicy that:
        - Denies all egress by default
        - Allows egress to Minio (for model download)
        - Allows egress to PyPI (for pip install)

        Args:
            namespace: Namespace name
            minio_endpoint: Minio endpoint hostname/IP
            minio_port: Minio port (default: 9000)

        Raises:
            ApiException: If NetworkPolicy creation fails
        """
        # Parse minio endpoint to get hostname/IP
        # Handle both "localhost:9000" and "minio.example.com" formats
        minio_host = minio_endpoint.split(":")[0] if ":" in minio_endpoint else minio_endpoint

        network_policy = client.V1NetworkPolicy(
            metadata=client.V1ObjectMeta(
                name="deny-all-egress-allow-minio-pypi",
                namespace=namespace
            ),
            spec=client.V1NetworkPolicySpec(
                pod_selector={},  # Applies to all pods in namespace
                policy_types=["Egress"],
                egress=[
                    # Allow DNS (required for all network operations)
                    client.V1NetworkPolicyEgressRule(
                        to=[],
                        ports=[
                            client.V1NetworkPolicyPort(protocol="UDP", port=53),
                            client.V1NetworkPolicyPort(protocol="TCP", port=53)
                        ]
                    ),
                    # Allow egress to Minio
                    client.V1NetworkPolicyEgressRule(
                        to=[],
                        ports=[
                            client.V1NetworkPolicyPort(protocol="TCP", port=minio_port)
                        ]
                    ),
                    # Allow HTTPS (port 443) for PyPI and other secure services
                    # This allows pip install from pypi.org
                    client.V1NetworkPolicyEgressRule(
                        to=[],
                        ports=[
                            client.V1NetworkPolicyPort(protocol="TCP", port=443)
                        ]
                    )
                ]
            )
        )

        try:
            self.networking_v1.create_namespaced_network_policy(
                namespace=namespace,
                body=network_policy
            )
            logger.info(f"Created NetworkPolicy for namespace {namespace}")
        except ApiException as e:
            if e.status == 409:  # Already exists
                logger.info(f"NetworkPolicy for namespace {namespace} already exists")
            else:
                logger.error(f"Failed to create NetworkPolicy for {namespace}: {str(e)}")
                raise

    def setup_user_namespace(
        self,
        user_id: int,
        minio_endpoint: Optional[str] = None
    ) -> str:
        """
        Set up a complete isolated namespace for a user.
        Creates namespace, ResourceQuota, and NetworkPolicy.

        Args:
            user_id: User ID
            minio_endpoint: Minio endpoint (defaults to settings.MINIO_ENDPOINT)

        Returns:
            Namespace name

        Raises:
            ApiException: If any Kubernetes operation fails
        """
        namespace = f"user-{user_id}"
        minio_endpoint = minio_endpoint or settings.MINIO_ENDPOINT

        # Create namespace
        self.create_namespace(
            namespace,
            labels={
                "kubeserve.io/user-id": str(user_id),
                "kubeserve.io/managed-by": "kubeserve"
            }
        )

        # Create ResourceQuota
        self.create_resource_quota(namespace)

        # Create NetworkPolicy
        self.create_network_policy(namespace, minio_endpoint)

        logger.info(f"Successfully set up namespace {namespace} for user {user_id}")
        return namespace

    def delete_namespace(self, namespace: str) -> None:
        """
        Delete a Kubernetes namespace.

        Args:
            namespace: Namespace name

        Raises:
            ApiException: If namespace deletion fails
        """
        try:
            self.core_v1.delete_namespace(name=namespace)
            logger.info(f"Deleted namespace: {namespace}")
        except ApiException as e:
            if e.status == 404:
                logger.info(f"Namespace {namespace} does not exist")
            else:
                logger.error(f"Failed to delete namespace {namespace}: {str(e)}")
                raise

    def create_ingress(
        self,
        namespace: str,
        name: str,
        service_name: str,
        service_port: int,
        ingress_host: str = "localhost",
        ingress_path: str = "/api/v1/predict",
        ingress_class: str = "nginx",
        annotations: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Create an Ingress resource to expose a service.

        Args:
            namespace: Namespace name
            name: Ingress name
            service_name: Name of the service to route to
            service_port: Port of the service
            ingress_host: Hostname for the ingress (default: localhost)
            ingress_path: Path prefix for routing (default: /api/v1/predict)
            ingress_class: Ingress class name (default: nginx)
            annotations: Optional annotations for the ingress

        Returns:
            Ingress URL (e.g., http://localhost/api/v1/predict/{deployment_id})

        Raises:
            ApiException: If Ingress creation fails
        """
        ingress = client.V1Ingress(
            metadata=client.V1ObjectMeta(
                name=name,
                namespace=namespace,
                annotations=annotations or {}
            ),
            spec=client.V1IngressSpec(
                ingress_class_name=ingress_class,
                rules=[
                    client.V1IngressRule(
                        host=ingress_host,
                        http=client.V1HTTPIngressRuleValue(
                            paths=[
                                client.V1HTTPIngressPath(
                                    path=ingress_path,
                                    path_type="Prefix",
                                    backend=client.V1IngressBackend(
                                        service=client.V1IngressServiceBackend(
                                            name=service_name,
                                            port=client.V1ServiceBackendPort(
                                                number=service_port
                                            )
                                        )
                                    )
                                )
                            ]
                        )
                    )
                ]
            )
        )

        try:
            self.networking_v1.create_namespaced_ingress(
                namespace=namespace,
                body=ingress
            )
            logger.info(f"Created Ingress {name} in namespace {namespace}")
            # Return the URL (for localhost, we'll use the NodePort)
            return f"http://{ingress_host}{ingress_path}"
        except ApiException as e:
            if e.status == 409:  # Already exists
                logger.info(f"Ingress {name} in namespace {namespace} already exists")
                return f"http://{ingress_host}{ingress_path}"
            else:
                logger.error(f"Failed to create Ingress {name}: {str(e)}")
                raise

    def delete_ingress(self, namespace: str, name: str) -> None:
        """
        Delete an Ingress resource.

        Args:
            namespace: Namespace name
            name: Ingress name

        Raises:
            ApiException: If Ingress deletion fails
        """
        try:
            self.networking_v1.delete_namespaced_ingress(
                name=name,
                namespace=namespace
            )
            logger.info(f"Deleted Ingress {name} from namespace {namespace}")
        except ApiException as e:
            if e.status == 404:
                logger.info(f"Ingress {name} in namespace {namespace} does not exist")
            else:
                logger.error(f"Failed to delete Ingress {name}: {str(e)}")
                raise

