# Phase 5.1: Observability - Metrics

## Overview

Phase 5.1 implements comprehensive metrics collection for the KubeServe platform. This includes installing Prometheus, configuring ServiceMonitors for automatic metric discovery, and adding custom prediction latency metrics to the inference server.

## Components

### 5.1.1 Prometheus Installation

The Prometheus monitoring stack is installed via Helm using the `kube-prometheus-stack` chart, which includes:
- **Prometheus**: Metrics collection and storage
- **Grafana**: Visualization and dashboards
- **ServiceMonitor CRD**: Automatic service discovery

**Installation Script**: `scripts/install-prometheus.sh`

**Features**:
- Installs kube-prometheus-stack using Helm
- Configures NodePort services (30090 for Prometheus, 30091 for Grafana)
- Sets retention to 30 days
- Default Grafana admin password: `admin`
- Waits for components to be ready

**Usage**:
```bash
./scripts/install-prometheus.sh
```

**Access**:
- Prometheus UI: http://localhost:30090
- Grafana UI: http://localhost:30091 (admin/admin)

**For Kind Clusters**:
```bash
kubectl port-forward -n monitoring svc/kube-prometheus-stack-prometheus 30090:9090
kubectl port-forward -n monitoring svc/kube-prometheus-stack-grafana 30091:80
```

### 5.1.2 ServiceMonitor Template

The Helm chart now includes a ServiceMonitor template that automatically creates ServiceMonitor resources for deployed models.

**Template**: `charts/model-serving/templates/servicemonitor.yaml`

**Configuration** (in `values.yaml`):
```yaml
monitoring:
  serviceMonitor:
    enabled: true
    interval: "30s"
    scrapeTimeout: "10s"
    labels: {}
```

**Features**:
- Conditional creation (only if `monitoring.serviceMonitor.enabled: true`)
- Automatically discovers services with matching labels
- Scrapes `/metrics` endpoint every 30 seconds
- Configurable scrape interval and timeout

**How It Works**:
1. ServiceMonitor selects services with labels matching the deployment
2. Prometheus Operator discovers the ServiceMonitor
3. Prometheus automatically scrapes the `/metrics` endpoint
4. Metrics are stored and available for querying

### 5.1.3 Custom Prediction Latency Metrics

The inference server now exposes custom Prometheus metrics for prediction performance:

**Metrics Added**:
- `prediction_latency_ms` (Histogram): Prediction latency in milliseconds
  - Buckets: [10, 50, 100, 200, 500, 1000, 2000, 5000] ms
  - Tracks distribution of prediction times
- `predictions_total` (Counter): Total number of predictions
  - Labels: `status` (success/error)
  - Tracks prediction success/failure rates

**Implementation**:
- Uses `prometheus_client` library for custom metrics
- Metrics are exposed alongside standard FastAPI metrics
- Latency is measured from request start to response completion
- Both successful and failed predictions are tracked

**Example Queries**:
```promql
# Average prediction latency
rate(prediction_latency_ms_sum[5m]) / rate(prediction_latency_ms_count[5m])

# 95th percentile latency
histogram_quantile(0.95, rate(prediction_latency_ms_bucket[5m]))

# Prediction success rate
rate(predictions_total{status="success"}[5m]) / rate(predictions_total[5m])
```

### 5.1.4 Integration

ServiceMonitor creation is automatically enabled when deploying models:
- Helm chart includes ServiceMonitor template
- Enabled by default in deployment service
- No additional configuration needed

## Metrics Available

### Standard Metrics (from prometheus-fastapi-instrumentator)
- `http_requests_total`: Total HTTP requests
- `http_request_duration_seconds`: Request duration
- `http_request_size_bytes`: Request size
- `http_response_size_bytes`: Response size

### Custom Metrics
- `prediction_latency_ms`: Prediction latency histogram
- `predictions_total`: Prediction counter with status label

### Kubernetes Metrics (from kube-prometheus-stack)
- `container_cpu_usage_seconds_total`: CPU usage per container
- `container_memory_usage_bytes`: Memory usage per container
- `kube_pod_status_phase`: Pod status
- `kube_deployment_status_replicas`: Deployment replica counts

## Testing

To test the metrics setup:

1. **Install Prometheus**:
   ```bash
   ./scripts/install-prometheus.sh
   ```

2. **Deploy a model** (via API or Helm):
   ```bash
   # Via API
   POST /api/v1/versions/1/deployments
   
   # Or via Helm directly
   helm install test-deployment charts/model-serving \
     --set monitoring.serviceMonitor.enabled=true \
     --namespace user-1
   ```

3. **Verify ServiceMonitor**:
   ```bash
   kubectl get servicemonitor -n user-1
   ```

4. **Check Prometheus targets**:
   - Open Prometheus UI: http://localhost:30090
   - Navigate to Status → Targets
   - Verify your service appears as a target

5. **Query metrics**:
   - In Prometheus UI, try: `prediction_latency_ms`
   - Or: `predictions_total{status="success"}`

6. **Make predictions and verify metrics**:
   ```bash
   curl -X POST http://localhost:30080/api/v1/predict/1/predict \
     -H "Content-Type: application/json" \
     -d '{"data": [[1.0, 2.0, 3.0, 4.0]]}'
   ```
   
   Then check Prometheus for updated metrics.

## Phase 5.2: Visualization

### Overview

Phase 5.2 implements Grafana dashboards for visualizing KubeServe metrics. Grafana is already installed as part of kube-prometheus-stack, so we focus on creating and importing dashboard configurations.

### Components

#### 5.2.1 Master Dashboard

**File**: `grafana/dashboards/kubeserve-master.json`

The master dashboard provides platform-wide visibility:

**Key Panels:**
- **Total Request Rate**: Aggregate requests/sec across all deployments
- **Error Rate**: HTTP errors and prediction failures
- **CPU Usage per User Namespace**: Resource consumption by tenant
- **Memory Usage per User Namespace**: Memory consumption by tenant
- **Average Prediction Latency**: P50, P95, P99 percentiles
- **Prediction Success Rate**: Overall success percentage
- **Active Deployments**: Count of running deployments
- **Total Pods**: Aggregate pod count
- **Total Predictions**: Predictions in the last hour
- **Error Rate Percentage**: Error rate with color thresholds

**Use Cases:**
- Platform health monitoring
- Multi-tenant resource tracking
- Capacity planning
- Performance bottleneck identification

#### 5.2.2 Deployment Dashboard

**File**: `grafana/dashboards/kubeserve-deployment.json`

The deployment dashboard provides detailed metrics for individual deployments:

**Variables:**
- `$namespace`: User namespace selector (e.g., `user-1`)
- `$deployment`: Deployment selector within namespace

**Key Panels:**
- **Request Rate**: Requests/sec for selected deployment
- **Prediction Latency**: Average, P50, P95, P99 latencies
- **CPU Usage**: Per-pod CPU consumption
- **Memory Usage**: Per-pod memory consumption
- **Pod Replicas**: Desired, ready, available counts
- **Prediction Success/Error Rate**: Success vs error rates
- **Current Requests/sec**: Real-time request rate
- **Average Latency**: Current latency with thresholds
- **Success Rate**: Current success percentage
- **Active Pods**: Ready pod count

**Use Cases:**
- Debugging deployment issues
- Performance optimization
- Individual model monitoring
- SLA compliance tracking

#### 5.2.3 Dashboard Import Script

**File**: `scripts/import-grafana-dashboards.sh`

Automated script to import dashboards into Grafana:

**Features:**
- Sets up port forwarding to Grafana
- Imports all dashboards from `grafana/dashboards/`
- Provides dashboard URLs after import
- Handles authentication automatically

**Usage:**
```bash
./scripts/import-grafana-dashboards.sh
```

### Installation Methods

1. **Automated Import** (Recommended):
   ```bash
   ./scripts/import-grafana-dashboards.sh
   ```

2. **Manual Import via UI**:
   - Access Grafana: http://localhost:30091
   - Login: `admin` / `admin`
   - Navigate to Dashboards → Import
   - Upload JSON files

3. **Grafana Provisioning** (Production):
   - Create ConfigMap with dashboard JSONs
   - Mount to Grafana pod
   - Configure provisioning YAML

### Prometheus Metrics Used

**Application Metrics:**
- `http_requests_total`: HTTP request counter
- `prediction_latency_ms`: Latency histogram
- `predictions_total`: Prediction counter with status label

**Kubernetes Metrics:**
- `container_cpu_usage_seconds_total`: CPU usage
- `container_memory_usage_bytes`: Memory usage
- `kube_deployment_status_replicas*`: Replica status

### Accessing Dashboards

After import:
- Master Dashboard: Platform-wide overview
- Deployment Dashboard: Per-deployment details (use variables to select)

Access via: http://localhost:30091 (or port-forward if needed)

## Next Steps

- Phase 6: Reliability & Testing
  - Integration tests (upload → deploy → predict → delete)
  - Load testing with Locust
  - HPA verification

