# KubeServe Test Suite

This directory contains unit tests for the KubeServe platform.

## Test Structure

```
tests/
├── conftest.py          # Shared pytest fixtures
├── test_auth.py         # Authentication tests (Phase 1.2)
└── test_models.py       # Model registry tests (Phase 1.3)
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

