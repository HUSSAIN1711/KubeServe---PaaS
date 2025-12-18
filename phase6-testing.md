# Phase 6: Reliability & Testing

## Overview

Phase 6 focuses on ensuring the KubeServe platform handles real-world scenarios and load. This includes integration tests for the full workflow and load testing to verify autoscaling behavior.

## Components

### 6.1 Integration Tests

**Script**: `scripts/integration_test.sh`

A comprehensive integration test that validates the complete workflow:

1. **User Registration**: Creates a test user
2. **Authentication**: Logs in and obtains JWT token
3. **Model Creation**: Creates a new model in the registry
4. **Version Creation**: Creates a model version
5. **File Upload**: Uploads a test model file (scikit-learn LogisticRegression)
6. **Status Update**: Updates version status to Ready
7. **Deployment**: Deploys the model to Kubernetes
8. **Health Check**: Waits for deployment to be ready
9. **Prediction**: Makes test predictions against the deployed model
10. **Cleanup**: Deletes deployment and model

**Usage**:
```bash
# Basic usage (uses defaults)
./scripts/integration_test.sh

# Custom configuration
API_BASE_URL=http://localhost:8000 \
TEST_USER_EMAIL=test@example.com \
TEST_USER_PASSWORD=mypassword \
MODEL_NAME=my-test-model \
./scripts/integration_test.sh
```

**Prerequisites**:
- KubeServe API running
- Kubernetes cluster accessible
- Minio/S3 storage available
- Helm installed
- kubectl configured

**What It Tests**:
- ✅ End-to-end workflow functionality
- ✅ API endpoint correctness
- ✅ Authentication flow
- ✅ File upload and storage
- ✅ Kubernetes deployment
- ✅ Model inference
- ✅ Cleanup operations

### 6.2 Load Testing with Locust

**Locustfile**: `locustfile.py`

Load testing script that simulates multiple users making prediction requests.

**Features**:
- **Single Predictions**: Most common operation (weight: 3)
- **Batch Predictions**: Less common batch requests (weight: 1)
- **Health Checks**: Periodic health monitoring (weight: 1)
- **Custom Wait Times**: 1-3 seconds between requests
- **Response Validation**: Validates JSON structure and status codes
- **Statistics**: Tracks response times, success/failure rates

**Usage**:
```bash
# Interactive mode (web UI)
locust --host=http://localhost:30080/api/v1/predict/1 -f locustfile.py

# Headless mode (automated)
locust --host=http://localhost:30080/api/v1/predict/1 \
       --users=10 \
       --spawn-rate=2 \
       --run-time=5m \
       --headless \
       -f locustfile.py
```

**Helper Script**: `scripts/run-load-test.sh`

Automated script for running load tests:

```bash
# Basic usage
DEPLOYMENT_URL=http://localhost:30080/api/v1/predict/1 \
LOCUST_USERS=10 \
LOCUST_RUN_TIME=5m \
./scripts/run-load-test.sh

# High load scenario
DEPLOYMENT_URL=http://localhost:30080/api/v1/predict/1 \
LOCUST_USERS=50 \
LOCUST_SPAWN_RATE=5 \
LOCUST_RUN_TIME=10m \
./scripts/run-load-test.sh
```

### 6.3 Test Scenarios

#### Baseline Test (Single Pod)

**Configuration**:
- Replicas: 1
- HPA: Disabled (or min=max=1)
- Load: 1-2 concurrent users
- Duration: 5 minutes

**What to Measure**:
- Average latency
- Max RPS (Requests Per Second)
- CPU/Memory usage
- Error rate

**Expected Results**:
- Stable latency (should not degrade significantly)
- Predictable resource usage
- Low error rate (<1%)

**Run**:
```bash
# Deploy with 1 replica
kubectl scale deployment <deployment-name> --replicas=1 -n user-1

# Run baseline test
LOCUST_USERS=2 \
LOCUST_RUN_TIME=5m \
./scripts/run-load-test.sh
```

#### Scalability Test (HPA Enabled)

**Configuration**:
- HPA: Enabled (Min: 1, Max: 5, Target CPU: 50%, Target Memory: 80%)
- Load: Ramp up users (5 → 10 → 20)
- Duration: 10-15 minutes

**What to Measure**:
- Pod count over time (should scale up)
- Latency stability (should remain consistent)
- RPS capacity (should increase with pods)
- HPA response time

**Expected Results**:
- Pods scale from 1 → 2 → 3+ as load increases
- Latency remains stable despite increased load
- RPS increases proportionally with pod count
- HPA responds within 1-2 minutes

**Run**:
```bash
# Ensure HPA is enabled
kubectl get hpa -n user-1

# Run scalability test with ramping load
LOCUST_USERS=20 \
LOCUST_SPAWN_RATE=2 \
LOCUST_RUN_TIME=10m \
./scripts/run-load-test.sh

# Monitor pods in another terminal
kubectl get pods -n user-1 -w
```

### 6.4 Verifying HPA Behavior

**Monitor HPA Status**:
```bash
# Watch HPA metrics
kubectl get hpa -n user-1 -w

# Check current metrics
kubectl describe hpa <deployment-name> -n user-1
```

**Monitor Pod Scaling**:
```bash
# Watch pods
kubectl get pods -n user-1 -w

# Check pod resource usage
kubectl top pods -n user-1
```

**Check Prometheus Metrics**:
- Navigate to Prometheus UI: http://localhost:30090
- Query: `kube_horizontalpodautoscaler_status_current_replicas{namespace="user-1"}`
- Query: `container_cpu_usage_seconds_total{namespace="user-1"}`
- Query: `rate(http_requests_total{namespace="user-1"}[5m])`

**Expected HPA Behavior**:
1. **Initial State**: 1 pod running
2. **Load Increase**: CPU/Memory usage increases
3. **HPA Detection**: HPA detects metrics exceed threshold (within 30-60s)
4. **Scaling Decision**: HPA calculates desired replicas
5. **Pod Creation**: New pods are created (1-2 minutes)
6. **Load Distribution**: Load balancer distributes traffic
7. **Stabilization**: System stabilizes at new replica count

### 6.5 Load Test Results Analysis

**Metrics to Review**:
- **Response Time**: Should remain stable or improve with scaling
- **RPS**: Should increase with number of pods
- **Error Rate**: Should remain low (<1%)
- **P95/P99 Latency**: Should not degrade significantly

**Locust Reports**:
- HTML report: `load_test_report.html`
- CSV files: `load_test_results_*.csv`

**Grafana Dashboards**:
- Use the deployment dashboard to visualize:
  - Request rate over time
  - Pod replica count
  - CPU/Memory usage per pod
  - Prediction latency percentiles

## Troubleshooting

### Integration Test Failures

**Deployment Timeout**:
- Check Kubernetes cluster status
- Verify Helm chart is valid
- Check pod logs: `kubectl logs -n user-1 <pod-name>`

**Upload Failures**:
- Verify Minio is accessible
- Check S3 credentials
- Verify bucket exists

**Prediction Failures**:
- Check model file format
- Verify model loaded correctly: `kubectl logs -n user-1 <pod-name>`
- Check deployment URL is correct

### Load Test Issues

**High Error Rate**:
- Check pod resources (might be throttled)
- Verify HPA is scaling correctly
- Check for rate limiting

**HPA Not Scaling**:
- Verify HPA is configured: `kubectl get hpa -n user-1`
- Check metrics are available: `kubectl top pods -n user-1`
- Verify HPA targets are set correctly
- Check Prometheus metrics are being scraped

**High Latency**:
- Check pod resource limits
- Verify network policies allow traffic
- Check if pods are being throttled
- Monitor CPU/Memory usage

## Next Steps

- Phase 7: Frontend Dashboard
  - Next.js application
  - User authentication UI
  - Model management interface
  - Deployment monitoring
  - Grafana dashboard embedding

