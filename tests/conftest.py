"""
Pytest configuration and shared fixtures.
"""

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db
from app.models.user import User
from app.models.model import Model, ModelVersion, Deployment
from app.core.security import get_password_hash


# Test database URL (in-memory SQLite for testing)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="function")
async def test_engine():
    """Create a test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture(scope="function")
async def test_session(test_engine):
    """Create a test database session."""
    async_session_maker = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session_maker() as session:
        yield session
        await session.rollback()


@pytest.fixture(scope="function")
async def test_client(test_session):
    """Create a test FastAPI client with database override."""
    async def override_get_db():
        yield test_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        yield client
    
    app.dependency_overrides.clear()


@pytest.fixture
async def test_user(test_session: AsyncSession):
    """Create a test user."""
    from app.models.user import UserRole
    
    user = User(
        email="test@example.com",
        password_hash=get_password_hash("testpassword123"),
        role=UserRole.USER,
    )
    test_session.add(user)
    await test_session.commit()
    await test_session.refresh(user)
    return user


@pytest.fixture
async def test_user_2(test_session: AsyncSession):
    """Create a second test user."""
    from app.models.user import UserRole
    
    user = User(
        email="test2@example.com",
        password_hash=get_password_hash("testpassword123"),
        role=UserRole.USER,
    )
    test_session.add(user)
    await test_session.commit()
    await test_session.refresh(user)
    return user


@pytest.fixture
async def auth_headers(test_client: AsyncClient, test_user: User):
    """Get authentication headers for test user."""
    response = await test_client.post(
        "/api/v1/auth/login",
        json={"email": test_user.email, "password": "testpassword123"},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def test_model(test_session: AsyncSession, test_user: User):
    """Create a test model."""
    from app.models.model import ModelType
    
    model = Model(
        name="Test Model",
        type=ModelType.SKLEARN,
        user_id=test_user.id,
    )
    test_session.add(model)
    await test_session.commit()
    await test_session.refresh(model)
    return model


@pytest.fixture
async def test_model_version(test_session: AsyncSession, test_model: Model):
    """Create a test model version."""
    from app.models.model import ModelVersionStatus
    
    version = ModelVersion(
        model_id=test_model.id,
        version_tag="v1",
        s3_path="s3://models/test/model/v1/model.joblib",
        status=ModelVersionStatus.READY,
    )
    test_session.add(version)
    await test_session.commit()
    await test_session.refresh(version)
    return version


@pytest.fixture
async def test_deployment(test_session: AsyncSession, test_model_version: ModelVersion):
    """Create a test deployment."""
    deployment = Deployment(
        version_id=test_model_version.id,
        k8s_service_name="model-1-1-1234567890",
        replicas=1,
    )
    test_session.add(deployment)
    await test_session.commit()
    await test_session.refresh(deployment)
    return deployment

