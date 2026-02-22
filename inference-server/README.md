# KubeServe Inference Server

A generic, optimized FastAPI inference server that can run any scikit-learn model with minimal cold start time.

## Architecture

### The "Heavy" Base Image Strategy

Instead of installing all dependencies at runtime (which takes ~45 seconds), we pre-install the most common ML packages in the base Docker image. This reduces cold start time to ~3 seconds for 90% of models.

**Pre-installed packages:**
- `fastapi`, `uvicorn` (web framework)
- `pandas`, `numpy` (data manipulation)
- `scikit-learn`, `joblib` (ML libraries)
- `prometheus-fastapi-instrumentator` (metrics)
- `minio`, `boto3` (S3 client)

### Smart Dependency Installation

The `start.sh` script:
1. Checks if `requirements.txt` exists in `/model/`
2. Compares required packages against installed packages
3. Only installs missing packages (saves ~40 seconds for most models)
4. Starts the Uvicorn server

## Building the Base Image

```bash
cd inference-server
docker build -t kubeserve-base:latest .
```

Or use the build script (from `inference-server/`):
```bash
./build.sh [tag] [registry]
# Examples:
./build.sh                    # builds kubeserve-base:latest, tags for localhost:5001
./build.sh v1.2.3             # builds kubeserve-base:v1.2.3
./build.sh latest myreg.io   # tags for myreg.io/kubeserve-base:latest
```

Then push to your registry (script prints the exact command):
```bash
docker push localhost:5001/kubeserve-base:latest   # local registry
# or
docker push <your-registry>/kubeserve-base:latest  # remote registry
```

---

## Rebuild and redeploy (use new image in Kubernetes)

After you rebuild the inference image, do the following so running deployments use it.

### 1. Build and push the image

From the **repo root**:

```bash
# Build (option A: direct docker)
docker build -t <your-registry>/kubeserve-base:latest inference-server/

# Build (option B: use script from inference-server dir)
cd inference-server && ./build.sh latest <your-registry> && cd ..

# Push to the registry your chart uses
docker push <your-registry>/kubeserve-base:latest
```

Use the same registry and tag as in your Helm values (default in chart: `localhost:5001/kubeserve-base:latest` for a local registry).

### 2. Restart deployments so pods use the new image

**Option A – Restart a specific deployment (by Helm release name)**

If your release is in namespace `user-1` and the release name is e.g. `model-42-1739123456`:

```bash
# Restart the deployment (new pods will be created)
kubectl rollout restart deployment/model-42-1739123456-model-serving -n user-1
```

To find release names: list Helm releases, or use the name shown in the KubeServe UI (e.g. "Service name" / `k8s_service_name`). The deployment name is `{release-name}-model-serving`.

**Option B – Scale to 0 then back up**

```bash
kubectl scale deployment/<release-name>-model-serving -n <namespace> --replicas=0
kubectl scale deployment/<release-name>-model-serving -n <namespace> --replicas=1
```

**Option C – Helm upgrade with same chart (e.g. after changing image tag)**

If you use a **new image tag** (recommended so Kubernetes pulls the new image):

```bash
# Upgrade with new image tag (replace release name, namespace, and tag)
helm upgrade <release-name> charts/model-serving -n <namespace> \
  --set deployment.image.repository=<your-registry>/kubeserve-base \
  --set deployment.image.tag=v1.2.3 \
  --reuse-values
```

**Using tag `latest`:** If you keep using `latest`, set pull policy to Always so each new pod pulls the updated image:

```bash
helm upgrade <release-name> charts/model-serving -n <namespace> \
  --set deployment.image.pullPolicy=Always \
  --reuse-values
```

Then delete the pods so they are recreated and pull the new image:

```bash
kubectl delete pods -l app.kubernetes.io/instance=<release-name> -n <namespace>
```

**Restart all model-serving deployments in a namespace:**

```bash
kubectl rollout restart deployment -l app.kubernetes.io/component=inference-server -n <namespace>
```

## How It Works

1. **Model Loading**: The server loads `model.joblib` from `/model/model.joblib` at startup
2. **Dynamic Requirements**: If `requirements.txt` exists, only missing packages are installed
3. **Prediction Endpoint**: `POST /predict` accepts JSON with `data` field containing input arrays
4. **Health Check**: `GET /health` returns server and model status

## API Endpoints

- `GET /` - API information
- `GET /health` - Health check
- `POST /predict` - Make predictions
- `GET /docs` - Swagger documentation
- `GET /metrics` - Prometheus metrics (via prometheus-fastapi-instrumentator)

## Example Usage

### Request
```bash
curl -X POST http://localhost:80/predict \
  -H "Content-Type: application/json" \
  -d '{
    "data": [[1.0, 2.0, 3.0, 4.0]]
  }'
```

### Response
```json
{
  "predictions": [1],
  "model_loaded": true
}
```

## Security

- Container runs as non-root user (`appuser`)
- Model files are mounted read-only from init container
- No write access to filesystem except `/tmp`

## Directory Structure

```
/model/              # Mounted from init container (read-only)
  model.joblib      # The ML model file
  requirements.txt  # Optional: additional dependencies

/app/               # Application code
  main.py          # FastAPI application
  start.sh         # Entrypoint script
```

## Development

To test locally:

```bash
# Build image
docker build -t kubeserve-base:latest .

# Run with model mounted
docker run -p 8080:80 \
  -v /path/to/model:/model:ro \
  kubeserve-base:latest
```

## Next Steps

This inference server will be deployed to Kubernetes in Phase 3, where:
- Init containers download models from S3
- Deployments use this base image
- Services expose the inference endpoints
- HPA scales based on load


