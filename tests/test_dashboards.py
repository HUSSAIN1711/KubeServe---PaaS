"""
Unit tests for Phase 5.2: Visualization - Grafana Dashboards.

Tests cover:
- Dashboard JSON validation
- Dashboard structure and required panels
- Dashboard configuration
"""

import pytest
import json
from pathlib import Path


@pytest.mark.metrics
@pytest.mark.unit
class TestMasterDashboard:
    """Tests for the master dashboard."""

    def test_master_dashboard_exists(self):
        """Test that master dashboard JSON file exists."""
        dashboard_path = Path(__file__).parent.parent / "grafana" / "dashboards" / "kubeserve-master.json"
        assert dashboard_path.exists()

    def test_master_dashboard_valid_json(self):
        """Test that master dashboard is valid JSON."""
        dashboard_path = Path(__file__).parent.parent / "grafana" / "dashboards" / "kubeserve-master.json"
        
        with open(dashboard_path) as f:
            dashboard_data = json.load(f)
        
        assert dashboard_data is not None
        assert isinstance(dashboard_data, dict)

    def test_master_dashboard_structure(self):
        """Test that master dashboard has correct structure."""
        dashboard_path = Path(__file__).parent.parent / "grafana" / "dashboards" / "kubeserve-master.json"
        
        with open(dashboard_path) as f:
            dashboard_data = json.load(f)
        
        # Check for required top-level fields
        assert "dashboard" in dashboard_data
        dashboard = dashboard_data["dashboard"]
        
        assert "title" in dashboard
        assert "panels" in dashboard
        assert isinstance(dashboard["panels"], list)

    def test_master_dashboard_title(self):
        """Test that master dashboard has correct title."""
        dashboard_path = Path(__file__).parent.parent / "grafana" / "dashboards" / "kubeserve-master.json"
        
        with open(dashboard_path) as f:
            dashboard_data = json.load(f)
        
        dashboard = dashboard_data["dashboard"]
        assert "KubeServe Master Dashboard" in dashboard["title"]

    def test_master_dashboard_required_panels(self):
        """Test that master dashboard has required panels."""
        dashboard_path = Path(__file__).parent.parent / "grafana" / "dashboards" / "kubeserve-master.json"
        
        with open(dashboard_path) as f:
            dashboard_data = json.load(f)
        
        dashboard = dashboard_data["dashboard"]
        panels = dashboard["panels"]
        
        # Check for key panels
        panel_titles = [panel.get("title", "") for panel in panels]
        
        assert any("Request Rate" in title for title in panel_titles)
        assert any("Error Rate" in title for title in panel_titles)
        assert any("CPU Usage" in title for title in panel_titles)
        assert any("Memory Usage" in title for title in panel_titles)
        assert any("Latency" in title for title in panel_titles)
        assert any("Success Rate" in title for title in panel_titles)

    def test_master_dashboard_prometheus_queries(self):
        """Test that master dashboard uses Prometheus queries."""
        dashboard_path = Path(__file__).parent.parent / "grafana" / "dashboards" / "kubeserve-master.json"
        
        with open(dashboard_path) as f:
            dashboard_data = json.load(f)
        
        dashboard = dashboard_data["dashboard"]
        panels = dashboard["panels"]
        
        # Check that panels have Prometheus queries
        has_prometheus_query = False
        for panel in panels:
            if "targets" in panel:
                for target in panel["targets"]:
                    if "expr" in target:
                        has_prometheus_query = True
                        break
                if has_prometheus_query:
                    break
        
        assert has_prometheus_query, "Dashboard should contain Prometheus queries"

    def test_master_dashboard_tags(self):
        """Test that master dashboard has appropriate tags."""
        dashboard_path = Path(__file__).parent.parent / "grafana" / "dashboards" / "kubeserve-master.json"
        
        with open(dashboard_path) as f:
            dashboard_data = json.load(f)
        
        dashboard = dashboard_data["dashboard"]
        
        if "tags" in dashboard:
            assert "kubeserve" in dashboard["tags"]
            assert "master" in dashboard["tags"]


@pytest.mark.metrics
@pytest.mark.unit
class TestDeploymentDashboard:
    """Tests for the deployment dashboard."""

    def test_deployment_dashboard_exists(self):
        """Test that deployment dashboard JSON file exists."""
        dashboard_path = Path(__file__).parent.parent / "grafana" / "dashboards" / "kubeserve-deployment.json"
        assert dashboard_path.exists()

    def test_deployment_dashboard_valid_json(self):
        """Test that deployment dashboard is valid JSON."""
        dashboard_path = Path(__file__).parent.parent / "grafana" / "dashboards" / "kubeserve-deployment.json"
        
        with open(dashboard_path) as f:
            dashboard_data = json.load(f)
        
        assert dashboard_data is not None
        assert isinstance(dashboard_data, dict)

    def test_deployment_dashboard_structure(self):
        """Test that deployment dashboard has correct structure."""
        dashboard_path = Path(__file__).parent.parent / "grafana" / "dashboards" / "kubeserve-deployment.json"
        
        with open(dashboard_path) as f:
            dashboard_data = json.load(f)
        
        assert "dashboard" in dashboard_data
        dashboard = dashboard_data["dashboard"]
        
        assert "title" in dashboard
        assert "panels" in dashboard
        assert "templating" in dashboard  # Should have variables

    def test_deployment_dashboard_variables(self):
        """Test that deployment dashboard has template variables."""
        dashboard_path = Path(__file__).parent.parent / "grafana" / "dashboards" / "kubeserve-deployment.json"
        
        with open(dashboard_path) as f:
            dashboard_data = json.load(f)
        
        dashboard = dashboard_data["dashboard"]
        
        assert "templating" in dashboard
        assert "list" in dashboard["templating"]
        
        variables = dashboard["templating"]["list"]
        assert len(variables) > 0
        
        # Check for namespace and deployment variables
        variable_names = [var.get("name", "") for var in variables]
        assert "namespace" in variable_names
        assert "deployment" in variable_names

    def test_deployment_dashboard_required_panels(self):
        """Test that deployment dashboard has required panels."""
        dashboard_path = Path(__file__).parent.parent / "grafana" / "dashboards" / "kubeserve-deployment.json"
        
        with open(dashboard_path) as f:
            dashboard_data = json.load(f)
        
        dashboard = dashboard_data["dashboard"]
        panels = dashboard["panels"]
        
        panel_titles = [panel.get("title", "") for panel in panels]
        
        assert any("Request Rate" in title for title in panel_titles)
        assert any("Latency" in title for title in panel_titles)
        assert any("CPU Usage" in title for title in panel_titles)
        assert any("Memory Usage" in title for title in panel_titles)
        assert any("Replicas" in title for title in panel_titles)

    def test_deployment_dashboard_uses_variables(self):
        """Test that deployment dashboard panels use template variables."""
        dashboard_path = Path(__file__).parent.parent / "grafana" / "dashboards" / "kubeserve-deployment.json"
        
        with open(dashboard_path) as f:
            dashboard_data = json.load(f)
        
        dashboard = dashboard_data["dashboard"]
        panels = dashboard["panels"]
        
        # Check that at least one panel uses variables
        uses_variables = False
        for panel in panels:
            if "targets" in panel:
                for target in panel["targets"]:
                    if "expr" in target:
                        expr = target["expr"]
                        if "$namespace" in expr or "$deployment" in expr:
                            uses_variables = True
                            break
                if uses_variables:
                    break
        
        assert uses_variables, "Dashboard should use template variables in queries"

    def test_deployment_dashboard_tags(self):
        """Test that deployment dashboard has appropriate tags."""
        dashboard_path = Path(__file__).parent.parent / "grafana" / "dashboards" / "kubeserve-deployment.json"
        
        with open(dashboard_path) as f:
            dashboard_data = json.load(f)
        
        dashboard = dashboard_data["dashboard"]
        
        if "tags" in dashboard:
            assert "kubeserve" in dashboard["tags"]
            assert "deployment" in dashboard["tags"]


@pytest.mark.metrics
@pytest.mark.unit
class TestDashboardConfiguration:
    """Tests for dashboard configuration and structure."""

    def test_dashboard_directory_exists(self):
        """Test that dashboard directory exists."""
        dashboard_dir = Path(__file__).parent.parent / "grafana" / "dashboards"
        assert dashboard_dir.exists()
        assert dashboard_dir.is_dir()

    def test_dashboard_files_count(self):
        """Test that we have the expected number of dashboard files."""
        dashboard_dir = Path(__file__).parent.parent / "grafana" / "dashboards"
        json_files = list(dashboard_dir.glob("*.json"))
        
        # Should have at least master and deployment dashboards
        assert len(json_files) >= 2

    def test_dashboard_schema_version(self):
        """Test that dashboards have valid schema versions."""
        dashboard_dir = Path(__file__).parent.parent / "grafana" / "dashboards"
        
        for json_file in dashboard_dir.glob("*.json"):
            with open(json_file) as f:
                dashboard_data = json.load(f)
            
            dashboard = dashboard_data.get("dashboard", {})
            if "schemaVersion" in dashboard:
                # Schema version should be a positive integer
                assert isinstance(dashboard["schemaVersion"], int)
                assert dashboard["schemaVersion"] > 0

    def test_dashboard_refresh_intervals(self):
        """Test that dashboards have refresh intervals configured."""
        dashboard_dir = Path(__file__).parent.parent / "grafana" / "dashboards"
        
        for json_file in dashboard_dir.glob("*.json"):
            with open(json_file) as f:
                dashboard_data = json.load(f)
            
            dashboard = dashboard_data.get("dashboard", {})
            
            # Check for refresh configuration
            if "refresh" in dashboard:
                assert dashboard["refresh"] is not None
            
            # Check for timepicker refresh intervals
            if "timepicker" in dashboard:
                if "refresh_intervals" in dashboard["timepicker"]:
                    intervals = dashboard["timepicker"]["refresh_intervals"]
                    assert isinstance(intervals, list)
                    assert len(intervals) > 0

