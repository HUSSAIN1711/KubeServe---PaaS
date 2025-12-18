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

Or tag for local registry:
```bash
docker build -t localhost:5001/kubeserve-base:latest .
docker push localhost:5001/kubeserve-base:latest
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

