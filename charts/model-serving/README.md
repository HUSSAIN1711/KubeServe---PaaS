# Model Serving Helm Chart

A Helm chart for deploying KubeServe ML model inference servers to Kubernetes.

## Overview

This chart deploys a complete inference server setup including:
- **Deployment**: Inference server pods with init container for model download
- **Service**: ClusterIP service to expose the inference endpoint
- **HorizontalPodAutoscaler**: Auto-scaling based on CPU and memory usage

## Prerequisites

- Kubernetes 1.19+
- Helm 3.0+
- Minio/S3 access for model artifacts
- KubeServe base image (`kubeserve-base:latest`) available in cluster

## Installation

### Basic Installation

```bash
helm install my-model ./charts/model-serving \
  --namespace user-1 \
  --set model.s3Path="s3://kubeserve-models/user-1/my-model/v1/model.joblib" \
  --set model.s3Endpoint="minio:9000"
```

### With Custom Values

```bash
helm install my-model ./charts/model-serving \
  --namespace user-1 \
  -f custom-values.yaml
```

## Configuration

### Model Configuration

| Parameter | Description | Default |
|-----------|-------------|---------|
| `model.s3Path` | S3 path to model file | `""` (required) |
| `model.s3Endpoint` | Minio/S3 endpoint | `"localhost:9000"` |
| `model.s3AccessKey` | S3 access key | `"minioadmin"` |
| `model.s3SecretKey` | S3 secret key | `"minioadmin"` |
| `model.s3Bucket` | S3 bucket name | `"kubeserve-models"` |
| `model.s3UseSSL` | Use SSL for S3 | `false` |

### Deployment Configuration

| Parameter | Description | Default |
|-----------|-------------|---------|
| `deployment.replicas` | Number of replicas | `1` |
| `deployment.image.repository` | Image repository | `"localhost:5001/kubeserve-base"` |
| `deployment.image.tag` | Image tag | `"latest"` |
| `deployment.resources.requests.cpu` | CPU request | `"100m"` |
| `deployment.resources.requests.memory` | Memory request | `"256Mi"` |
| `deployment.resources.limits.cpu` | CPU limit | `"1"` |
| `deployment.resources.limits.memory` | Memory limit | `"1Gi"` |

### Autoscaling Configuration

| Parameter | Description | Default |
|-----------|-------------|---------|
| `autoscaling.enabled` | Enable HPA | `true` |
| `autoscaling.minReplicas` | Minimum replicas | `1` |
| `autoscaling.maxReplicas` | Maximum replicas | `5` |
| `autoscaling.targetCPUUtilizationPercentage` | Target CPU usage | `50` |
| `autoscaling.targetMemoryUtilizationPercentage` | Target memory usage | `80` |

## Architecture

### Init Container

The init container (`minio/mc`) downloads the model from S3 before the main container starts:
1. Configures Minio client with credentials
2. Downloads `model.joblib` to `/model/model.joblib`
3. Downloads `requirements.txt` if it exists
4. Shares the `/model` directory with the main container via `emptyDir` volume

### Main Container

The inference server container:
- Loads the model from `/model/model.joblib` at startup
- Serves predictions via `POST /predict`
- Exposes health check at `GET /health`
- Exposes Prometheus metrics at `GET /metrics`

### Health Probes

- **Liveness Probe**: Checks `/health` every 10s, restarts pod if unhealthy
- **Readiness Probe**: Checks `/health` every 5s, removes from service if not ready

## Example Values File

```yaml
model:
  s3Path: "s3://kubeserve-models/user-1/fraud-detector/v1/model.joblib"
  s3Endpoint: "minio:9000"
  s3AccessKey: "minioadmin"
  s3SecretKey: "minioadmin"

deployment:
  replicas: 2
  resources:
    requests:
      cpu: "200m"
      memory: "512Mi"
    limits:
      cpu: "2"
      memory: "2Gi"

autoscaling:
  enabled: true
  minReplicas: 1
  maxReplicas: 10
  targetCPUUtilizationPercentage: 70
```

## Usage

After deployment, the inference server is available at:
- Service name: `{release-name}-model-serving`
- Port: `80`
- Health: `http://{service-name}/health`
- Predict: `http://{service-name}/predict`

### Example Prediction Request

```bash
curl -X POST http://model-serving-service/predict \
  -H "Content-Type: application/json" \
  -d '{
    "data": [[1.0, 2.0, 3.0, 4.0]]
  }'
```

## Troubleshooting

### Model Not Loading

Check init container logs:
```bash
kubectl logs deployment/{release-name}-model-serving -c download-model
```

### Pod Not Ready

Check main container logs:
```bash
kubectl logs deployment/{release-name}-model-serving -c inference-server
```

### Health Check Failing

Verify the health endpoint:
```bash
kubectl exec -it deployment/{release-name}-model-serving -c inference-server -- curl http://localhost:80/health
```

## Uninstallation

```bash
helm uninstall my-model --namespace user-1
```

