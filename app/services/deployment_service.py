"""
Deployment service for managing Kubernetes deployments via Helm.
Handles Helm install/uninstall operations and Ingress creation.
"""

import logging
import subprocess
import os
from pathlib import Path
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.kubernetes_client import KubernetesClient

logger = logging.getLogger(__name__)


class HelmDeploymentService:
    """
    Service for deploying models to Kubernetes using Helm.
    Handles Helm install/uninstall operations.
    """

    def __init__(self):
        """Initialize Helm deployment service."""
        self.chart_path = Path(__file__).parent.parent.parent / "charts" / "model-serving"
        self.k8s_client = KubernetesClient()

    def _run_helm_command(
        self,
        command: list[str],
        timeout: int = 300
    ) -> tuple[int, str, str]:
        """
        Run a Helm command and return the result.

        Args:
            command: Helm command as list of strings
            timeout: Command timeout in seconds

        Returns:
            Tuple of (return_code, stdout, stderr)

        Raises:
            subprocess.TimeoutExpired: If command times out
            subprocess.SubprocessError: If command fails
        """
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired as e:
            logger.error(f"Helm command timed out: {' '.join(command)}")
            raise
        except subprocess.SubprocessError as e:
            logger.error(f"Helm command failed: {' '.join(command)}: {str(e)}")
            raise

    def deploy_model(
        self,
        release_name: str,
        namespace: str,
        s3_path: str,
        s3_endpoint: str,
        s3_access_key: str,
        s3_secret_key: str,
        s3_bucket: str,
        s3_use_ssl: bool = False,
        replicas: int = 1,
        image_repository: Optional[str] = None,
        image_tag: str = "latest",
        ingress_enabled: bool = True,
        ingress_host: Optional[str] = None,
        ingress_path: Optional[str] = None
    ) -> dict:
        """
        Deploy a model using Helm.

        Args:
            release_name: Helm release name
            namespace: Kubernetes namespace
            s3_path: S3 path to model file
            s3_endpoint: S3 endpoint (e.g., minio:9000)
            s3_access_key: S3 access key
            s3_secret_key: S3 secret key
            s3_bucket: S3 bucket name
            s3_use_ssl: Use SSL for S3
            replicas: Number of replicas
            image_repository: Docker image repository (defaults to settings)
            image_tag: Docker image tag
            ingress_enabled: Enable Ingress creation
            ingress_host: Ingress hostname (defaults to settings.INGRESS_HOST)
            ingress_path: Ingress path (defaults to settings.INGRESS_BASE_PATH/{release_name})

        Returns:
            Dictionary with deployment information including URL

        Raises:
            subprocess.SubprocessError: If Helm install fails
        """
        if not self.chart_path.exists():
            raise ValueError(f"Helm chart not found at {self.chart_path}")

        image_repository = image_repository or f"{settings.MINIO_ENDPOINT.split(':')[0]}:5001/kubeserve-base"
        ingress_host = ingress_host or settings.INGRESS_HOST
        ingress_path = ingress_path or f"{settings.INGRESS_BASE_PATH}/{release_name}"

        # Build Helm install command
        helm_command = [
            "helm",
            "install",
            release_name,
            str(self.chart_path),
            "--namespace", namespace,
            "--create-namespace",
            "--set", f"model.s3Path={s3_path}",
            "--set", f"model.s3Endpoint={s3_endpoint}",
            "--set", f"model.s3AccessKey={s3_access_key}",
            "--set", f"model.s3SecretKey={s3_secret_key}",
            "--set", f"model.s3Bucket={s3_bucket}",
            "--set", f"model.s3UseSSL={str(s3_use_ssl).lower()}",
            "--set", f"deployment.replicas={replicas}",
            "--set", f"deployment.image.repository={image_repository}",
            "--set", f"deployment.image.tag={image_tag}",
            "--set", f"ingress.enabled={str(ingress_enabled).lower()}",
            "--set", f"ingress.hosts[0].host={ingress_host}",
            "--set", f"ingress.hosts[0].paths[0].path={ingress_path}",
            "--set", f"ingress.hosts[0].paths[0].pathType=Prefix",
            "--set", "monitoring.serviceMonitor.enabled=true",
        ]

        logger.info(f"Deploying model with Helm: {' '.join(helm_command)}")

        # Run Helm install
        returncode, stdout, stderr = self._run_helm_command(helm_command)

        if returncode != 0:
            error_msg = f"Helm install failed: {stderr}"
            logger.error(error_msg)
            raise subprocess.SubprocessError(error_msg)

        logger.info(f"Helm install successful for release {release_name}")
        logger.debug(f"Helm output: {stdout}")

        # Construct the public URL
        # For localhost, we'll use the NodePort (30080) or the ingress host
        if ingress_enabled:
            url = f"http://{ingress_host}:30080{ingress_path}"
        else:
            url = None

        return {
            "release_name": release_name,
            "namespace": namespace,
            "url": url,
            "stdout": stdout
        }

    def undeploy_model(
        self,
        release_name: str,
        namespace: str
    ) -> None:
        """
        Undeploy a model by uninstalling the Helm release.

        Args:
            release_name: Helm release name
            namespace: Kubernetes namespace

        Raises:
            subprocess.SubprocessError: If Helm uninstall fails
        """
        helm_command = [
            "helm",
            "uninstall",
            release_name,
            "--namespace", namespace
        ]

        logger.info(f"Undeploying model with Helm: {' '.join(helm_command)}")

        returncode, stdout, stderr = self._run_helm_command(helm_command)

        if returncode != 0:
            # If release doesn't exist, that's okay (idempotent)
            if "not found" in stderr.lower():
                logger.info(f"Helm release {release_name} not found, skipping uninstall")
                return
            error_msg = f"Helm uninstall failed: {stderr}"
            logger.error(error_msg)
            raise subprocess.SubprocessError(error_msg)

        logger.info(f"Helm uninstall successful for release {release_name}")

    def get_deployment_status(
        self,
        release_name: str,
        namespace: str
    ) -> dict:
        """
        Get the status of a Helm deployment.

        Args:
            release_name: Helm release name
            namespace: Kubernetes namespace

        Returns:
            Dictionary with deployment status information
        """
        helm_command = [
            "helm",
            "status",
            release_name,
            "--namespace", namespace,
            "--output", "json"
        ]

        returncode, stdout, stderr = self._run_helm_command(helm_command)

        if returncode != 0:
            return {
                "status": "not_found",
                "error": stderr
            }

        # Parse JSON output (simplified - in production, use proper JSON parsing)
        return {
            "status": "deployed",
            "output": stdout
        }

