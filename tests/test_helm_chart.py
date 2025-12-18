"""
Unit tests for Phase 3.2: Helm Chart Factory.

Tests cover:
- Helm chart structure validation
- Template rendering with different values
- Required values validation

Note: These tests don't require the app to be imported, so they can run independently.
"""

import pytest
import yaml
import os
from pathlib import Path

# Don't import app modules to avoid .env file dependency


@pytest.mark.helm
@pytest.mark.unit
class TestHelmChartStructure:
    """Tests for Helm chart structure and files."""

    def test_chart_yaml_exists(self):
        """Test that Chart.yaml exists and is valid."""
        chart_path = Path("charts/model-serving/Chart.yaml")
        assert chart_path.exists(), "Chart.yaml should exist"

        with open(chart_path) as f:
            chart_data = yaml.safe_load(f)

        assert chart_data["name"] == "model-serving"
        assert chart_data["version"] is not None
        assert chart_data["type"] == "application"

    def test_values_yaml_exists(self):
        """Test that values.yaml exists and is valid."""
        values_path = Path("charts/model-serving/values.yaml")
        assert values_path.exists(), "values.yaml should exist"

        with open(values_path) as f:
            values_data = yaml.safe_load(f)

        # Check required sections exist
        assert "model" in values_data
        assert "deployment" in values_data
        assert "service" in values_data
        assert "autoscaling" in values_data

    def test_required_templates_exist(self):
        """Test that all required template files exist."""
        templates_dir = Path("charts/model-serving/templates")
        assert templates_dir.exists(), "templates directory should exist"

        required_templates = [
            "deployment.yaml",
            "service.yaml",
            "hpa.yaml",
            "_helpers.tpl",
        ]

        for template in required_templates:
            template_path = templates_dir / template
            assert template_path.exists(), f"{template} should exist"

    def test_deployment_template_structure(self):
        """Test that deployment template has required components."""
        deployment_path = Path("charts/model-serving/templates/deployment.yaml")
        with open(deployment_path) as f:
            content = f.read()

        # Check for init container
        assert "initContainers" in content
        assert "download-model" in content
        assert "minio/mc" in content

        # Check for main container
        assert "inference-server" in content
        assert ".Values.deployment.image.repository" in content
        assert ".Values.deployment.image.tag" in content

        # Check for health probes (they're templated from values.yaml)
        assert "livenessProbe" in content
        assert "readinessProbe" in content
        # The probes are templated using toYaml, so check for that
        assert "toYaml" in content or ".Values.deployment.livenessProbe" in content

        # Check for volume mounts
        assert "model-storage" in content
        assert "emptyDir" in content

    def test_service_template_structure(self):
        """Test that service template has required components."""
        service_path = Path("charts/model-serving/templates/service.yaml")
        with open(service_path) as f:
            content = f.read()

        assert "kind: Service" in content
        assert ".Values.service.type" in content
        assert ".Values.service.port" in content

    def test_hpa_template_structure(self):
        """Test that HPA template has required components."""
        hpa_path = Path("charts/model-serving/templates/hpa.yaml")
        with open(hpa_path) as f:
            content = f.read()

        assert "kind: HorizontalPodAutoscaler" in content
        assert "autoscaling/v2" in content
        assert "minReplicas" in content
        assert "maxReplicas" in content
        assert "targetCPUUtilizationPercentage" in content

    def test_helpers_template_exists(self):
        """Test that helpers template exists with required functions."""
        helpers_path = Path("charts/model-serving/templates/_helpers.tpl")
        with open(helpers_path) as f:
            content = f.read()

        # Check for required helper functions
        assert "model-serving.name" in content
        assert "model-serving.fullname" in content
        assert "model-serving.labels" in content
        assert "model-serving.selectorLabels" in content


@pytest.mark.helm
@pytest.mark.unit
class TestHelmChartValues:
    """Tests for Helm chart values validation."""

    def test_default_values_are_valid(self):
        """Test that default values.yaml is valid YAML and has correct structure."""
        values_path = Path("charts/model-serving/values.yaml")
        with open(values_path) as f:
            values = yaml.safe_load(f)

        # Validate model section
        assert "s3Path" in values["model"]
        assert "s3Endpoint" in values["model"]
        assert "s3AccessKey" in values["model"]
        assert "s3SecretKey" in values["model"]

        # Validate deployment section
        assert "replicas" in values["deployment"]
        assert "image" in values["deployment"]
        assert "resources" in values["deployment"]
        assert "livenessProbe" in values["deployment"]
        assert "readinessProbe" in values["deployment"]

        # Validate service section
        assert "type" in values["service"]
        assert "port" in values["service"]

        # Validate autoscaling section
        assert "enabled" in values["autoscaling"]
        assert "minReplicas" in values["autoscaling"]
        assert "maxReplicas" in values["autoscaling"]

    def test_default_resource_limits(self):
        """Test that default resource limits are reasonable."""
        values_path = Path("charts/model-serving/values.yaml")
        with open(values_path) as f:
            values = yaml.safe_load(f)

        resources = values["deployment"]["resources"]
        
        # Check requests exist
        assert "requests" in resources
        assert "cpu" in resources["requests"]
        assert "memory" in resources["requests"]
        
        # Check limits exist
        assert "limits" in resources
        assert "cpu" in resources["limits"]
        assert "memory" in resources["limits"]

    def test_default_health_probes(self):
        """Test that default health probes are configured."""
        values_path = Path("charts/model-serving/values.yaml")
        with open(values_path) as f:
            values = yaml.safe_load(f)

        liveness = values["deployment"]["livenessProbe"]
        readiness = values["deployment"]["readinessProbe"]

        # Check liveness probe
        assert "httpGet" in liveness
        assert liveness["httpGet"]["path"] == "/health"
        assert liveness["httpGet"]["port"] == 80
        assert "initialDelaySeconds" in liveness

        # Check readiness probe
        assert "httpGet" in readiness
        assert readiness["httpGet"]["path"] == "/health"
        assert readiness["httpGet"]["port"] == 80
        assert "initialDelaySeconds" in readiness


@pytest.mark.helm
@pytest.mark.unit
class TestHelmChartTemplates:
    """Tests for Helm chart template rendering."""

    def test_deployment_template_uses_values(self):
        """Test that deployment template correctly uses values."""
        deployment_path = Path("charts/model-serving/templates/deployment.yaml")
        with open(deployment_path) as f:
            content = f.read()

        # Check template uses values
        assert "{{ .Values.deployment.replicas }}" in content
        assert "{{ .Values.deployment.image.repository }}" in content
        assert "{{ .Values.model.s3Path }}" in content
        assert "{{ .Values.model.s3Endpoint }}" in content

    def test_service_template_uses_values(self):
        """Test that service template correctly uses values."""
        service_path = Path("charts/model-serving/templates/service.yaml")
        with open(service_path) as f:
            content = f.read()

        assert "{{ .Values.service.type }}" in content
        assert "{{ .Values.service.port }}" in content

    def test_hpa_template_uses_values(self):
        """Test that HPA template correctly uses values."""
        hpa_path = Path("charts/model-serving/templates/hpa.yaml")
        with open(hpa_path) as f:
            content = f.read()

        assert ".Values.autoscaling.enabled" in content
        assert ".Values.autoscaling.minReplicas" in content
        assert ".Values.autoscaling.maxReplicas" in content
        assert ".Values.autoscaling.targetCPUUtilizationPercentage" in content

    def test_init_container_handles_ssl(self):
        """Test that init container script handles SSL configuration."""
        deployment_path = Path("charts/model-serving/templates/deployment.yaml")
        with open(deployment_path) as f:
            content = f.read()

        # Check for SSL handling
        assert "{{- if .Values.model.s3UseSSL }}" in content
        assert "PROTOCOL" in content
        assert "https" in content
        assert "http" in content

    def test_helpers_used_in_templates(self):
        """Test that helper functions are used in templates."""
        deployment_path = Path("charts/model-serving/templates/deployment.yaml")
        service_path = Path("charts/model-serving/templates/service.yaml")
        hpa_path = Path("charts/model-serving/templates/hpa.yaml")

        for path in [deployment_path, service_path, hpa_path]:
            with open(path) as f:
                content = f.read()
                # Check for helper function usage
                assert "include \"model-serving.fullname\"" in content or "include \"model-serving.labels\"" in content

