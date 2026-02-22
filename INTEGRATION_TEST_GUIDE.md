# Integration Test Guide

This guide explains how to run the integration test script that validates the complete KubeServe workflow.

## Prerequisites

Before running the integration test, ensure you have:

1. **All Phase 0 infrastructure running**:
   - Kubernetes cluster (Kind or Minikube)
   - Minio (S3 storage)
   - PostgreSQL database
   - Docker registry (for pushing images)

2. **KubeServe API server running**

3. **Required tools installed**:
   - `curl` (for API calls)
   - `python3` (for creating test model)
   - `scikit-learn` and `joblib` (for test model)
   - `kubectl` (configured to access your cluster)
   - `helm` (for deployments)

## Step-by-Step Setup

### 1. Start Infrastructure (Phase 0)

```bash
# Start Minio and PostgreSQL
docker-compose up -d

# Verify services are running
docker-compose ps

# If using Kind, ensure cluster is running
kind get clusters

# If cluster doesn't exist, create it
./scripts/setup-kind-cluster.sh

# Kind: choose one so model pods can reach MinIO:
#   A) MinIO on host (docker-compose): kubectl apply -f scripts/kind-minio-host.yaml
#   B) MinIO in cluster (recommended): kubectl apply -f scripts/minio-in-cluster.yaml
#      Then: kubectl port-forward svc/minio 9000:9000 -n default &
#      In .env set: MINIO_ENDPOINT=localhost:9000 and MINIO_DEPLOY_ENDPOINT=minio.default.svc.cluster.local:9000
```

### 2. Build and Push Inference Server Image

The integration test deploys models, so you need the inference server image:

```bash
# Build the base inference image
cd inference-server
docker build -t kubeserve-base:latest .

# Tag for local registry (if using Kind)
docker tag kubeserve-base:latest localhost:5001/kubeserve-base:latest

# Push to local registry
docker push localhost:5001/kubeserve-base:latest

# Or if using Minikube
eval $(minikube docker-env)
docker build -t kubeserve-base:latest .
```

### 3. Start the KubeServe API Server

```bash
# Make sure you're in the project root
cd /path/to/KubeServe

# Activate virtual environment (if using one)
source venv/bin/activate  # or: . venv/bin/activate

# Install dependencies (if not already installed)
pip install -r requirements.txt

# Set up environment variables
# Make sure .env file exists and is configured
cp .env.example .env
# Edit .env with your settings

# Run database migrations
alembic upgrade head

# Start the API server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API should now be running at `http://localhost:8000`

**Verify API is running**:
```bash
curl http://localhost:8000/health
# Should return: {"status":"healthy"}
```

### 4. Install Python Dependencies for Test Model

The integration test creates a test model using scikit-learn:

```bash
pip install scikit-learn joblib
```

### 5. Run the Integration Test

```bash
# Make sure the script is executable
chmod +x scripts/integration_test.sh

# Run with default settings
./scripts/integration_test.sh
```

**With custom configuration**:
```bash
API_BASE_URL=http://localhost:8000 \
TEST_USER_EMAIL=my-test@example.com \
TEST_USER_PASSWORD=mypassword \
MODEL_NAME=my-test-model \
VERSION_TAG=v1.0.0 \
./scripts/integration_test.sh
```

## What the Test Does

The integration test performs these steps in order:

1. **User Registration** → Creates a test user account
2. **Login** → Authenticates and gets JWT token
3. **Create Model** → Creates a model in the registry
4. **Create Version** → Creates a model version
5. **Upload Model File** → Uploads a scikit-learn model to S3
6. **Update Status** → Sets version status to "Ready"
7. **Deploy Model** → Deploys model to Kubernetes via Helm
8. **Wait for Ready** → Waits up to 5 minutes for deployment to be healthy
9. **Make Predictions** → Sends test prediction requests
10. **Cleanup** → Deletes deployment and model

## Expected Output

You should see output like:

```
🧪 Starting KubeServe Integration Test
========================================
API Base URL: http://localhost:8000
Test User: integration-test@example.com

📝 Step 1: Registering test user...
✅ User registered successfully

🔐 Step 2: Logging in...
✅ Login successful

📦 Step 3: Creating model...
✅ Model created with ID: 1

🏷️  Step 4: Creating model version...
✅ Model version created with ID: 1

📤 Step 5: Uploading model file...
✅ Model file uploaded successfully

✅ Step 6: Updating version status to Ready...
✅ Version status updated to Ready

🚀 Step 7: Deploying model...
✅ Model deployed with ID: 1
   Deployment URL: http://localhost:30080/api/v1/predict/1

⏳ Waiting for deployment to be ready (max 5 minutes)...
✅ Deployment is ready!

🔮 Step 8: Making predictions...
✅ Predictions successful!
   Response: {"predictions":[...],"model_loaded":true}

🗑️  Step 9: Deleting deployment...
✅ Deployment deleted successfully

🧹 Step 10: Cleaning up model...
✅ Model deleted successfully

========================================
✅ Integration test completed successfully!
```

## Troubleshooting

### API Server Not Running

**Error**: `Failed to connect to localhost:8000`

**Solution**:
```bash
# Check if server is running
curl http://localhost:8000/health

# If not, start it
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Database Connection Issues

**Error**: Database connection errors

**Solution**:
```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Check .env file has correct DATABASE_URL
cat .env | grep DATABASE_URL

# Run migrations
alembic upgrade head
```

### Minio/S3 Upload Failures

**Error**: Upload fails or S3 errors

**Solution**:
```bash
# Check Minio is running
docker-compose ps minio

# Check Minio credentials in .env
cat .env | grep MINIO

# Test Minio connectivity
curl http://localhost:9000/minio/health/live
```

### Kubernetes Deployment Failures

**Error**: Helm deployment fails or pods don't start

**Solution**:
```bash
# Check cluster is accessible
kubectl cluster-info

# Check if namespace exists
kubectl get namespaces | grep user-

# Check pod logs
kubectl get pods -n user-1
kubectl logs -n user-1 <pod-name>

# Check Helm release
helm list -n user-1
```

### Model File Creation Fails

**Error**: `Failed to create test model`

**Solution**:
```bash
# Install required Python packages
pip install scikit-learn joblib

# Test model creation manually
python3 -c "import joblib; from sklearn.linear_model import LogisticRegression; import numpy as np; X = np.array([[1,2],[2,3]]); y = np.array([0,1]); m = LogisticRegression(); m.fit(X,y); joblib.dump(m, '/tmp/test.joblib'); print('OK')"
```

### Deployment Timeout

**Error**: Deployment doesn't become ready within 90 seconds (health never returns 200)

**Solution**:
```bash
# Kind: use in-cluster MinIO (recommended) so pods can reach S3:
#   kubectl apply -f scripts/minio-in-cluster.yaml
#   kubectl port-forward svc/minio 9000:9000 -n default &
#   In .env: MINIO_ENDPOINT=localhost:9000 and MINIO_DEPLOY_ENDPOINT=minio.default.svc.cluster.local:9000
#   Restart the backend, then run the test again.

# Or if using MinIO on host: kubectl apply -f scripts/kind-minio-host.yaml

# Check pod status (replace user-1 with your user namespace, e.g. user-2)
kubectl get pods -n user-1

# If pod is in Init or CrashLoop, check the model-download init container
kubectl logs -n user-1 <pod-name> -c download-model

# Check pod events
kubectl describe pod -n user-1 <pod-name>

# Check if image pull is failing
kubectl get events -n user-1 --sort-by='.lastTimestamp'

# Verify image exists in registry
docker images | grep kubeserve-base
```

### Prediction Failures

**Error**: Predictions return errors

**Solution**:
```bash
# Check deployment URL is correct
curl http://localhost:30080/api/v1/predict/1/health

# Check pod logs for errors
kubectl logs -n user-1 <pod-name>

# Verify model loaded correctly
kubectl logs -n user-1 <pod-name> | grep "Model loaded"
```

## Running in Different Environments

### Custom API URL

```bash
API_BASE_URL=http://192.168.1.100:8000 ./scripts/integration_test.sh
```

### Different Kubernetes Context

```bash
# Switch kubectl context first
kubectl config use-context my-cluster

# Then run test
./scripts/integration_test.sh
```

### Skip Cleanup (for debugging)

To keep resources after test for inspection, you can modify the script or comment out the cleanup steps.

## Next Steps

After the integration test passes:

1. **Verify resources were created**:
   ```bash
   kubectl get all -n user-1
   helm list -n user-1
   ```

2. **Check Minio for uploaded files**:
   ```bash
   # Access Minio UI at http://localhost:9001
   # Login with MINIO_ACCESS_KEY / MINIO_SECRET_KEY
   ```

3. **Run load tests**:
   ```bash
   ./scripts/run-load-test.sh
   ```

## Common Issues Summary

| Issue | Check | Fix |
|-------|-------|-----|
| API not accessible | `curl http://localhost:8000/health` | Start API server |
| Database error | `docker-compose ps postgres` | Start PostgreSQL |
| S3 upload fails | `docker-compose ps minio` | Start Minio |
| Deployment fails | `kubectl get pods -n user-1` | Check pod logs |
| Image pull error | `docker images \| grep kubeserve` | Build/push image |
| Model creation fails | `pip list \| grep scikit` | Install scikit-learn |

## Getting Help

If the test fails:

1. Check the error message in the output
2. Review the troubleshooting section above
3. Check logs:
   - API server logs (terminal where uvicorn is running)
   - Pod logs: `kubectl logs -n user-1 <pod-name>`
   - Docker logs: `docker-compose logs`
4. Verify all prerequisites are met


