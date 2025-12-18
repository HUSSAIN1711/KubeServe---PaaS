# Phase 3.3: The Deploy Endpoint

## Overview

Phase 3.3 implements the complete deployment workflow that bridges the database records with actual Kubernetes deployments. When a user creates a deployment, the system now:

1. Validates the model version is ready
2. Creates a deployment record in the database
3. Deploys the model to Kubernetes using Helm
4. Creates an Ingress resource for public access
5. Updates the deployment with the public URL

## Components

### 3.3.1 Helm Deployment Service

**File**: `app/services/deployment_service.py`

A new service that handles all Helm operations:

- **`HelmDeploymentService`**: Manages Helm install/uninstall operations
- **`deploy_model()`**: Deploys a model using `helm install` with all required values
- **`undeploy_model()`**: Removes a deployment using `helm uninstall`
- **`get_deployment_status()`**: Gets the status of a Helm release

**Features**:
- Automatic S3 path parsing and injection
- Configurable ingress paths
- Error handling with proper cleanup
- Timeout protection (300s default)

### 3.3.2 Enhanced Deployment Service

**File**: `app/services/model_service.py` (DeploymentService class)

The `DeploymentService` has been extended to:

- **Create Deployments**: Now triggers actual Kubernetes deployments via Helm
- **Delete Deployments**: Removes Helm releases on deletion
- **URL Management**: Automatically generates and stores public URLs

**Deployment Flow**:
1. Validate model version is READY and has S3 path
2. Create deployment record in database (to get deployment.id)
3. Parse S3 path (bucket/key) from model version
4. Deploy to Kubernetes using Helm with:
   - S3 configuration (path, endpoint, credentials)
   - Replica count
   - Ingress configuration with deployment-specific path
5. Update deployment record with public URL
6. Handle errors: cleanup database record if Helm fails

**Deletion Flow**:
1. Verify ownership
2. Uninstall Helm release
3. Delete database record
4. Graceful error handling (continues even if Helm uninstall fails)

### 3.3.3 API Endpoint

**Endpoint**: `POST /api/v1/versions/{version_id}/deployments`

The existing endpoint now triggers full Kubernetes deployment:

**Request**:
```json
{
  "replicas": 1
}
```

**Response**:
```json
{
  "id": 1,
  "version_id": 1,
  "k8s_service_name": "model-1-1234567890",
  "url": "http://localhost:30080/api/v1/predict/1",
  "replicas": 1,
  "created_at": "2024-01-01T00:00:00",
  "updated_at": "2024-01-01T00:00:00"
}
```

### 3.3.4 S3 Path Handling

The service automatically:
- Parses S3 paths (handles both `s3://bucket/key` and `bucket/key` formats)
- Extracts bucket and key components
- Injects S3 configuration into Helm values
- Uses internal cluster endpoint (`minio:9000`) for Kubernetes pods

### 3.3.5 Ingress Integration

Each deployment gets:
- **Unique Path**: `/api/v1/predict/{deployment_id}`
- **Public URL**: `http://localhost:30080/api/v1/predict/{deployment_id}`
- **Automatic Creation**: Ingress is created via Helm template

## Configuration

The deployment service uses these settings from `app/config.py`:
- `MINIO_ENDPOINT`: S3 endpoint
- `MINIO_ACCESS_KEY`: S3 access key
- `MINIO_SECRET_KEY`: S3 secret key
- `MINIO_BUCKET_NAME`: Default bucket name
- `MINIO_USE_SSL`: SSL configuration
- `INGRESS_HOST`: Ingress hostname (default: "localhost")
- `INGRESS_BASE_PATH`: Base path for predictions (default: "/api/v1/predict")

## Error Handling

**Deployment Failures**:
- If Helm install fails, the database record is automatically deleted
- Error details are logged and returned to the user
- Prevents orphaned deployment records

**Deletion Failures**:
- If Helm uninstall fails, the database record is still deleted
- Warning is logged but operation continues
- Allows cleanup even if Kubernetes is unavailable

## Usage Example

```python
# Create a deployment (via API)
POST /api/v1/versions/1/deployments
{
  "replicas": 2
}

# This triggers:
# 1. Database record creation
# 2. Helm install with model S3 path
# 3. Ingress creation
# 4. URL generation

# Response includes the public URL:
{
  "url": "http://localhost:30080/api/v1/predict/1"
}

# Delete deployment
DELETE /api/v1/deployments/1

# This triggers:
# 1. Helm uninstall
# 2. Database record deletion
```

## Integration with Other Phases

- **Phase 3.1**: Uses user namespaces (`user-{id}`)
- **Phase 3.2**: Uses the Helm chart from `charts/model-serving`
- **Phase 4.1**: Creates Ingress resources automatically
- **Phase 1.4**: Requires model version to have S3 path (from upload)

## Testing

To test the deployment:

1. **Upload a model**:
   ```bash
   POST /api/v1/versions/1/upload
   # Upload model.joblib and requirements.txt
   ```

2. **Create deployment**:
   ```bash
   POST /api/v1/versions/1/deployments
   {
     "replicas": 1
   }
   ```

3. **Check deployment status**:
   ```bash
   GET /api/v1/deployments/1
   # Returns URL and status
   ```

4. **Test prediction endpoint**:
   ```bash
   curl http://localhost:30080/api/v1/predict/1/predict
   # Make predictions
   ```

5. **Delete deployment**:
   ```bash
   DELETE /api/v1/deployments/1
   # Removes Helm release and database record
   ```

## Next Steps

- Phase 5: Add observability (Prometheus, Grafana) to monitor deployments
- Phase 6: Integration tests for the full deployment workflow
- Phase 7: Frontend dashboard to manage deployments

