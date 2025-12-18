# KubeServe Test Suite

This directory contains unit tests for the KubeServe platform.

## Test Structure

```
tests/
├── conftest.py              # Shared pytest fixtures
├── test_auth.py             # Authentication tests (Phase 1.2)
├── test_models.py           # Model registry tests (Phase 1.3)
├── test_storage.py          # Storage/upload tests (Phase 1.4)
├── test_kubernetes.py       # Kubernetes operations tests (Phase 3.1)
├── test_helm_chart.py       # Helm chart validation tests (Phase 3.2)
├── test_deployment_service.py  # Deployment service tests (Phase 3.3)
├── test_ingress.py          # Ingress tests (Phase 4.1)
├── test_metrics.py          # Metrics tests (Phase 5.1)
└── test_dashboards.py       # Dashboard tests (Phase 5.2)
```

## Running Tests

### Install Test Dependencies

```bash
pip install -r requirements.txt
# or install dev dependencies
pip install pytest pytest-asyncio httpx aiosqlite
```

### Run All Tests

```bash
pytest
```

### Run Specific Test Files

```bash
# Authentication tests only
pytest tests/test_auth.py

# Model registry tests only
pytest tests/test_models.py
```

### Run with Markers

```bash
# Run only happy path tests
pytest -m "not sad"

# Run only authentication tests
pytest -m auth

# Run only model registry tests
pytest -m models

# Run only storage tests
pytest -m storage

# Run only Kubernetes tests
pytest -m kubernetes

# Run only Helm chart tests
pytest -m helm

# Run only deployment service tests
pytest -m deployment

# Run only ingress tests
pytest -m ingress

# Run only metrics/observability tests
pytest -m metrics
```

### Run with Verbose Output

```bash
pytest -v
```

### Run with Coverage

```bash
pytest --cov=app --cov-report=html
```

## Test Coverage

### Authentication Tests (Phase 1.2)

**Happy Path:**
- ✅ User registration success
- ✅ User registration with default role
- ✅ User login success
- ✅ Get current user information
- ✅ Access protected routes with valid token

**Sad Path:**
- ✅ Duplicate email registration
- ✅ Invalid email format
- ✅ Password too short
- ✅ Wrong password login
- ✅ Non-existent user login
- ✅ Access protected route without token
- ✅ Access protected route with invalid token
- ✅ Access protected route with expired/malformed token

### Model Registry Tests (Phase 1.3)

**Happy Path:**
- ✅ Create model success
- ✅ Get all models
- ✅ Get model by ID
- ✅ Delete model
- ✅ Create model version success
- ✅ Get model versions
- ✅ Update version status
- ✅ Create deployment success
- ✅ Get deployments
- ✅ Delete deployment

**Sad Path:**
- ✅ Create model without authentication
- ✅ Get non-existent model
- ✅ Get model owned by another user
- ✅ Delete non-existent model
- ✅ Create version with duplicate tag
- ✅ Create version for non-existent model
- ✅ Create deployment for non-ready version
- ✅ Create deployment for non-existent version
- ✅ Get/delete non-existent deployment
- ✅ Invalid model type
- ✅ Invalid replica count

### Storage Tests (Phase 1.4)

**StorageClient Tests:**
- ✅ Client initialization
- ✅ Bucket creation if missing
- ✅ Successful file upload
- ✅ Upload failure handling
- ✅ File existence check
- ✅ File non-existence check

**StorageService Tests:**
- ✅ S3 path generation
- ✅ Path sanitization (special characters)
- ✅ File validation (valid model files)
- ✅ File validation (invalid extensions)
- ✅ File validation (missing filename)
- ✅ Successful artifact upload
- ✅ File size validation (too large)
- ✅ S3 error handling

**Upload Endpoint Tests:**
- ✅ Successful upload
- ✅ Unauthorized access
- ✅ Invalid version ID
- ✅ Other user's version (ownership check)
- ✅ Invalid file type

### Kubernetes Tests (Phase 3.1)

**KubernetesClient Tests:**
- ✅ Client initialization
- ✅ Client initialization with custom kubeconfig
- ✅ Namespace existence check
- ✅ Namespace creation
- ✅ Namespace creation when already exists
- ✅ ResourceQuota creation
- ✅ ResourceQuota creation when already exists
- ✅ NetworkPolicy creation
- ✅ Complete user namespace setup
- ✅ Namespace deletion
- ✅ Namespace deletion when not found

**User Service Integration Tests:**
- ✅ User registration creates namespace
- ✅ User creation handles K8s failure gracefully

### Helm Chart Tests (Phase 3.2)

**Chart Structure Tests:**
- ✅ Chart.yaml exists and is valid
- ✅ values.yaml exists and is valid
- ✅ Required templates exist
- ✅ Deployment template structure
- ✅ Service template structure
- ✅ HPA template structure
- ✅ Helpers template exists

**Values Validation Tests:**
- ✅ Default values are valid
- ✅ Default resource limits
- ✅ Default health probes

**Template Validation Tests:**
- ✅ Deployment template uses values
- ✅ Service template uses values
- ✅ HPA template uses values
- ✅ Init container handles SSL
- ✅ Helpers used in templates

### Deployment Service Tests (Phase 3.3)

**HelmDeploymentService Tests:**
- ✅ Service initialization
- ✅ Successful model deployment via Helm
- ✅ Helm deployment failure handling
- ✅ Successful model undeployment via Helm
- ✅ Undeployment when release doesn't exist
- ✅ Get deployment status
- ✅ Get status for non-existent deployment
- ✅ Deployment with custom ingress path

**DeploymentService Integration Tests:**
- ✅ Create deployment triggers Helm deploy
- ✅ Helm deployment failure cleans up database record
- ✅ Deployment requires S3 path
- ✅ Delete deployment triggers Helm undeploy
- ✅ Helm undeployment failure doesn't prevent database cleanup
- ✅ S3 path parsing and injection

### Ingress Tests (Phase 4.1)

**KubernetesClient Ingress Tests:**
- ✅ Successful Ingress creation
- ✅ Ingress creation when already exists
- ✅ Ingress creation with custom path
- ✅ Ingress creation with annotations
- ✅ Successful Ingress deletion
- ✅ Ingress deletion when doesn't exist
- ✅ Ingress creation with custom ingress class

### Metrics Tests (Phase 5.1)

**Inference Server Metrics Tests:**
- ✅ Metrics defined in code (prediction_latency_histogram, prediction_counter)
- ✅ Histogram configuration (buckets, name, description)
- ✅ Counter configuration (labels, name, description)
- ✅ Metrics used in predict endpoint
- ✅ Metrics endpoint exposed via Instrumentator

**ServiceMonitor Template Tests:**
- ✅ ServiceMonitor template exists and has correct structure
- ✅ Conditional rendering based on monitoring.serviceMonitor.enabled
- ✅ Correct selector configuration
- ✅ Endpoint configuration (/metrics, port, interval)
- ✅ Uses Helm helper functions
- ✅ Monitoring configuration in values.yaml

### Dashboard Tests (Phase 5.2)

**Master Dashboard Tests:**
- ✅ Dashboard JSON file exists and is valid
- ✅ Dashboard structure (title, panels, schema)
- ✅ Required panels (Request Rate, Error Rate, CPU/Memory Usage, Latency, Success Rate)
- ✅ Prometheus queries configured
- ✅ Appropriate tags

**Deployment Dashboard Tests:**
- ✅ Dashboard JSON file exists and is valid
- ✅ Dashboard structure with templating variables
- ✅ Template variables (namespace, deployment)
- ✅ Required panels (Request Rate, Latency, CPU/Memory, Replicas)
- ✅ Variables used in queries
- ✅ Appropriate tags

**Dashboard Configuration Tests:**
- ✅ Dashboard directory exists
- ✅ Expected number of dashboard files
- ✅ Valid schema versions
- ✅ Refresh intervals configured

## Test Fixtures

The `conftest.py` file provides the following fixtures:

- `test_engine`: In-memory SQLite database engine
- `test_session`: Database session for tests
- `test_client`: FastAPI test client with database override
- `test_user`: Test user fixture
- `test_user_2`: Second test user fixture
- `auth_headers`: Authentication headers for test user
- `test_model`: Test model fixture
- `test_model_version`: Test model version fixture
- `test_deployment`: Test deployment fixture

## Test Database

Tests use an in-memory SQLite database (`sqlite+aiosqlite:///:memory:`) for fast execution and isolation. Each test gets a fresh database instance.

## Writing New Tests

When adding new tests:

1. Follow the existing pattern (happy path and sad path classes)
2. Use appropriate pytest markers (`@pytest.mark.auth`, `@pytest.mark.models`, etc.)
3. Use fixtures from `conftest.py` when possible
4. Ensure tests are isolated (don't depend on test execution order)
5. Use descriptive test names that explain what is being tested

## Example Test

```python
@pytest.mark.asyncio
@pytest.mark.auth
@pytest.mark.unit
class TestMyFeature:
    async def test_my_feature_success(self, test_client: AsyncClient, auth_headers: dict):
        """Test successful feature operation."""
        response = await test_client.post(
            "/api/v1/my-endpoint",
            headers=auth_headers,
            json={"data": "value"},
        )
        
        assert response.status_code == 200
        assert response.json()["status"] == "success"
```

