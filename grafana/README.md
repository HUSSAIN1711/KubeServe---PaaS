# KubeServe Grafana Dashboards

This directory contains Grafana dashboard configurations for monitoring KubeServe deployments.

## Dashboards

### Master Dashboard (`kubeserve-master.json`)

The master dashboard provides an overview of all deployments across the platform:

**Panels:**
- **Total Request Rate**: Aggregate request rate across all model-serving deployments
- **Error Rate**: HTTP error rates and prediction errors
- **CPU Usage per User Namespace**: CPU consumption broken down by user namespace
- **Memory Usage per User Namespace**: Memory consumption broken down by user namespace
- **Average Prediction Latency**: Average, P95, and P99 latency percentiles
- **Prediction Success Rate**: Percentage of successful predictions
- **Active Deployments**: Count of active deployments
- **Total Pods**: Total number of running pods
- **Total Predictions**: Total predictions in the last hour
- **Error Rate Percentage**: Overall error rate percentage with color thresholds

**Use Cases:**
- Platform-wide monitoring
- Resource usage tracking per tenant
- Identifying performance bottlenecks
- Capacity planning

### Deployment Dashboard (`kubeserve-deployment.json`)

The deployment dashboard provides detailed metrics for a specific model deployment:

**Variables:**
- **Namespace**: Select user namespace (e.g., `user-1`)
- **Deployment**: Select specific deployment within the namespace

**Panels:**
- **Request Rate**: Requests per second for the selected deployment
- **Prediction Latency**: Average, P50, P95, P99 latency percentiles
- **CPU Usage**: CPU usage per pod
- **Memory Usage**: Memory usage per pod
- **Pod Replicas**: Desired, ready, and available replica counts
- **Prediction Success/Error Rate**: Success vs error prediction rates
- **Current Requests/sec**: Real-time request rate
- **Average Latency**: Current average latency with color thresholds
- **Success Rate**: Current success rate percentage
- **Active Pods**: Number of ready pods

**Use Cases:**
- Debugging specific deployment issues
- Performance optimization
- Capacity planning for individual models
- SLA monitoring

## Installation

### Method 1: Using the Import Script (Recommended)

```bash
./scripts/import-grafana-dashboards.sh
```

This script:
1. Sets up port forwarding to Grafana
2. Imports all dashboards from `grafana/dashboards/`
3. Provides URLs to access the dashboards

### Method 2: Manual Import via Grafana UI

1. Access Grafana: http://localhost:30091 (or port-forward if needed)
2. Login: `admin` / `admin` (or check secret: `kubectl get secret -n monitoring kube-prometheus-stack-grafana -o jsonpath="{.data.admin-password}" | base64 -d`)
3. Navigate to **Dashboards** → **Import**
4. Upload the JSON file or paste the contents
5. Select **Prometheus** as the data source
6. Click **Import**

### Method 3: Grafana Provisioning (Advanced)

For production deployments, you can configure Grafana to automatically load dashboards using provisioning:

1. Create a ConfigMap with the dashboard JSON files
2. Mount it to `/etc/grafana/provisioning/dashboards/` in the Grafana pod
3. Configure `dashboards.yaml` to point to the directory

## Prerequisites

- Prometheus and Grafana installed (via `scripts/install-prometheus.sh`)
- ServiceMonitors configured for model deployments (automatic via Helm chart)
- Prometheus data source configured in Grafana (automatic with kube-prometheus-stack)

## Prometheus Queries Used

The dashboards use the following Prometheus metrics:

### Application Metrics (from inference server)
- `http_requests_total`: Total HTTP requests
- `prediction_latency_ms`: Prediction latency histogram
- `predictions_total`: Prediction counter with status label

### Kubernetes Metrics (from kube-prometheus-stack)
- `container_cpu_usage_seconds_total`: CPU usage per container
- `container_memory_usage_bytes`: Memory usage per container
- `kube_deployment_status_replicas`: Deployment replica counts
- `kube_deployment_status_replicas_ready`: Ready replica counts
- `kube_deployment_status_replicas_available`: Available replica counts

## Troubleshooting

### Dashboards show "No Data"

1. **Check Prometheus targets**: Navigate to Prometheus UI → Status → Targets
   - Verify ServiceMonitors are discovered
   - Verify targets are up and scraping successfully

2. **Verify metric labels**: Ensure deployments have correct labels:
   ```bash
   kubectl get servicemonitor -n user-1
   kubectl get svc -n user-1 --show-labels
   ```

3. **Check metric names**: Query Prometheus directly:
   ```promql
   http_requests_total
   prediction_latency_ms
   predictions_total
   ```

### Variables not populating

- Ensure Prometheus is scraping metrics from your deployments
- Check that the metric queries in the variable definitions return results
- Verify namespace and deployment names match your actual resources

### Port forwarding issues

If the import script fails:
```bash
# Manual port forward
kubectl port-forward -n monitoring svc/kube-prometheus-stack-grafana 30091:80

# In another terminal, import manually via curl or Grafana UI
```

## Customization

Dashboards can be customized by:
1. Editing the JSON files directly
2. Using Grafana UI to modify panels and save changes
3. Exporting updated dashboards and replacing the JSON files

## Dashboard URLs

After import, dashboards are accessible at:
- Master Dashboard: `http://localhost:30091/d/kubeserve-master/kubeserve-master-dashboard`
- Deployment Dashboard: `http://localhost:30091/d/kubeserve-deployment/kubeserve-deployment-dashboard`

(URLs may vary based on Grafana's URL generation)

