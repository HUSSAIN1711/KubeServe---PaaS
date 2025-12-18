"""
Unit tests for Phase 5.1: Observability - Metrics.

Tests cover:
- Custom Prometheus metrics in inference server
- Metric collection and exposure
- ServiceMonitor template validation
"""

import pytest
import json
import os
import sys
from pathlib import Path

# Add inference-server to path for imports (for potential future use)
INFERENCE_SERVER_PATH = Path(__file__).parent.parent / "inference-server"
sys.path.insert(0, str(INFERENCE_SERVER_PATH))


@pytest.mark.metrics
@pytest.mark.unit
class TestInferenceServerMetrics:
    """Tests for custom metrics in the inference server."""

    def test_metrics_defined_in_code(self):
        """Test that custom metrics are defined in the inference server code."""
        main_path = INFERENCE_SERVER_PATH / "main.py"
        assert main_path.exists()
        
        content = main_path.read_text()
        
        # Check for metric definitions
        assert "prediction_latency_histogram" in content
        assert "prediction_counter" in content
        assert "Histogram" in content
        assert "Counter" in content

    def test_prediction_latency_histogram_configuration(self):
        """Test that prediction_latency_histogram is configured correctly."""
        main_path = INFERENCE_SERVER_PATH / "main.py"
        content = main_path.read_text()
        
        # Check for histogram configuration
        assert "prediction_latency_ms" in content
        assert "Prediction latency in milliseconds" in content
        assert "buckets=" in content

    def test_prediction_counter_configuration(self):
        """Test that prediction_counter is configured correctly."""
        main_path = INFERENCE_SERVER_PATH / "main.py"
        content = main_path.read_text()
        
        # Check for counter configuration
        assert "predictions_total" in content
        assert "Total number of predictions" in content
        assert "status" in content  # Label name

    def test_metrics_used_in_predict_endpoint(self):
        """Test that metrics are used in the predict endpoint."""
        main_path = INFERENCE_SERVER_PATH / "main.py"
        content = main_path.read_text()
        
        # Check that metrics are observed/incremented
        assert "prediction_latency_histogram.observe" in content
        assert "prediction_counter.labels" in content
        assert "status='success'" in content
        assert "status='error'" in content

    def test_metrics_endpoint_exposed(self):
        """Test that metrics endpoint is configured."""
        main_path = INFERENCE_SERVER_PATH / "main.py"
        content = main_path.read_text()
        
        # Check for prometheus-fastapi-instrumentator usage
        assert "Instrumentator" in content
        assert "instrument" in content
        assert "expose" in content

    @pytest.mark.skipif(
        not (INFERENCE_SERVER_PATH / "main.py").exists(),
        reason="Inference server main.py not found"
    )
    def test_metrics_buckets_defined(self):
        """Test that histogram buckets are defined correctly."""
        main_path = INFERENCE_SERVER_PATH / "main.py"
        content = main_path.read_text()
        
        # Check for bucket values
        expected_buckets = [10, 50, 100, 200, 500, 1000, 2000, 5000]
        for bucket in expected_buckets:
            assert str(bucket) in content


@pytest.mark.metrics
@pytest.mark.unit
class TestServiceMonitorTemplate:
    """Tests for ServiceMonitor Helm template."""

    def test_servicemonitor_template_exists(self):
        """Test that ServiceMonitor template file exists."""
        template_path = Path(__file__).parent.parent / "charts" / "model-serving" / "templates" / "servicemonitor.yaml"
        assert template_path.exists()

    def test_servicemonitor_template_structure(self):
        """Test that ServiceMonitor template has correct structure."""
        template_path = Path(__file__).parent.parent / "charts" / "model-serving" / "templates" / "servicemonitor.yaml"
        content = template_path.read_text()
        
        # Check for required Kubernetes resource fields
        assert "apiVersion: monitoring.coreos.com/v1" in content
        assert "kind: ServiceMonitor" in content
        assert "metadata:" in content
        assert "spec:" in content

    def test_servicemonitor_conditional_rendering(self):
        """Test that ServiceMonitor is conditionally rendered."""
        template_path = Path(__file__).parent.parent / "charts" / "model-serving" / "templates" / "servicemonitor.yaml"
        content = template_path.read_text()
        
        # Should be conditional on monitoring.serviceMonitor.enabled
        assert "{{- if .Values.monitoring.serviceMonitor.enabled }}" in content
        assert "{{- end }}" in content

    def test_servicemonitor_selector(self):
        """Test that ServiceMonitor has correct selector."""
        template_path = Path(__file__).parent.parent / "charts" / "model-serving" / "templates" / "servicemonitor.yaml"
        content = template_path.read_text()
        
        # Check for selector configuration
        assert "selector:" in content
        assert "matchLabels:" in content
        assert "app.kubernetes.io/component: inference-server" in content

    def test_servicemonitor_endpoints(self):
        """Test that ServiceMonitor has correct endpoint configuration."""
        template_path = Path(__file__).parent.parent / "charts" / "model-serving" / "templates" / "servicemonitor.yaml"
        content = template_path.read_text()
        
        # Check for endpoint configuration
        assert "endpoints:" in content
        assert "port: http" in content
        assert "path: /metrics" in content
        assert "interval:" in content
        assert "scrapeTimeout:" in content

    def test_servicemonitor_uses_helpers(self):
        """Test that ServiceMonitor uses Helm helper functions."""
        template_path = Path(__file__).parent.parent / "charts" / "model-serving" / "templates" / "servicemonitor.yaml"
        content = template_path.read_text()
        
        # Should use helper functions for naming and labels
        assert "model-serving.fullname" in content
        assert "model-serving.labels" in content
        assert "model-serving.selectorLabels" in content

    def test_servicemonitor_namespace_configuration(self):
        """Test that ServiceMonitor uses namespace from values."""
        template_path = Path(__file__).parent.parent / "charts" / "model-serving" / "templates" / "servicemonitor.yaml"
        content = template_path.read_text()
        
        # Should use namespace from values or release namespace
        assert ".Values.namespace" in content or ".Release.Namespace" in content


@pytest.mark.metrics
@pytest.mark.unit
class TestMonitoringConfiguration:
    """Tests for monitoring configuration in Helm values."""

    def test_monitoring_values_exist(self):
        """Test that monitoring configuration exists in values.yaml."""
        values_path = Path(__file__).parent.parent / "charts" / "model-serving" / "values.yaml"
        assert values_path.exists()
        
        content = values_path.read_text()
        assert "monitoring:" in content

    def test_servicemonitor_values_structure(self):
        """Test that ServiceMonitor values have correct structure."""
        values_path = Path(__file__).parent.parent / "charts" / "model-serving" / "values.yaml"
        content = values_path.read_text()
        
        # Check for ServiceMonitor configuration
        assert "serviceMonitor:" in content
        assert "enabled:" in content
        assert "interval:" in content
        assert "scrapeTimeout:" in content

    def test_servicemonitor_default_enabled(self):
        """Test that ServiceMonitor is enabled by default."""
        values_path = Path(__file__).parent.parent / "charts" / "model-serving" / "values.yaml"
        content = values_path.read_text()
        
        # Find the enabled value
        lines = content.split('\n')
        enabled_line = None
        in_monitoring = False
        in_servicemonitor = False
        
        for line in lines:
            if "monitoring:" in line:
                in_monitoring = True
            elif in_monitoring and "serviceMonitor:" in line:
                in_servicemonitor = True
            elif in_servicemonitor and "enabled:" in line:
                enabled_line = line
                break
        
        # Should be enabled by default (true)
        assert enabled_line is not None
        assert "true" in enabled_line.lower()

