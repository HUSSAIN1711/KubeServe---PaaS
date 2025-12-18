# Phase 4: Networking & Ingress

## Overview

Phase 4 implements networking and ingress to expose internal Kubernetes services to the public internet securely. This allows users to access their deployed models via HTTP endpoints.

## Components

### 4.1 Ingress Controller Installation

The NGINX Ingress Controller is installed via Helm to provide ingress capabilities to the cluster.

**Installation Script**: `scripts/install-ingress-controller.sh`

**Features**:
- Installs NGINX Ingress Controller using Helm
- Configures NodePort service (ports 30080 for HTTP, 30443 for HTTPS)
- Waits for controller to be ready
- Provides access information

**Usage**:
```bash
./scripts/install-ingress-controller.sh
```

**For Kind Clusters**:
Since Kind doesn't support LoadBalancer services, the ingress controller uses NodePort. You may need to set up port forwarding:
```bash
kubectl port-forward -n ingress-nginx svc/ingress-nginx-controller 30080:80 30443:443
```

### 4.2 Helm Chart Ingress Template

The Helm chart now includes an Ingress template that automatically creates ingress resources for deployed models.

**Template**: `charts/model-serving/templates/ingress.yaml`

**Configuration** (in `values.yaml`):
```yaml
ingress:
  enabled: true
  className: "nginx"
  hosts:
    - host: localhost
      paths:
        - path: /api/v1/predict
          pathType: Prefix
```

**Features**:
- Conditional creation (only if `ingress.enabled: true`)
- Configurable host and paths
- Support for TLS/SSL
- Custom annotations support

### 4.3 Kubernetes Client Ingress Support

The `KubernetesClient` has been extended with methods to create and manage Ingress resources programmatically.

**New Methods**:
- `create_ingress()`: Creates an Ingress resource for a service
- `delete_ingress()`: Deletes an Ingress resource

**Usage Example**:
```python
from app.core.kubernetes_client import KubernetesClient

k8s_client = KubernetesClient()
url = k8s_client.create_ingress(
    namespace="user-1",
    name="model-deployment-1",
    service_name="model-serving-1",
    service_port=80,
    ingress_host="localhost",
    ingress_path="/api/v1/predict/1"
)
```

### 4.4 Configuration

New configuration options in `app/config.py`:
- `INGRESS_HOST`: Ingress hostname (default: "localhost")
- `INGRESS_BASE_PATH`: Base path for prediction endpoints (default: "/api/v1/predict")

## Routing

The ingress routes requests as follows:
- **Path**: `/api/v1/predict/{deployment_id}`
- **Routes to**: Service `model-{deployment_id}` on port 80
- **Example**: `http://localhost/api/v1/predict/1` → `model-serving-1:80`

## Integration with Phase 3.3

When Phase 3.3 (The Deploy Endpoint) is implemented, the deployment service will:
1. Deploy the model using Helm
2. Create an Ingress resource (or use Helm template)
3. Update the deployment's `url` field with the public endpoint

## Testing

To test the ingress setup:

1. **Install the ingress controller**:
   ```bash
   ./scripts/install-ingress-controller.sh
   ```

2. **Deploy a test service** (manually or via Helm):
   ```bash
   helm install test-deployment charts/model-serving \
     --set ingress.enabled=true \
     --set ingress.hosts[0].host=localhost \
     --namespace user-1
   ```

3. **Test the endpoint**:
   ```bash
   curl http://localhost:30080/api/v1/predict/1/health
   ```

## Next Steps

- Phase 3.3: Implement the deploy endpoint that integrates Helm installs with Ingress creation
- Phase 5: Add observability (Prometheus, Grafana) to monitor ingress traffic

