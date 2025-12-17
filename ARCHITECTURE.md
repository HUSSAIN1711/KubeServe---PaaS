# KubeServe Architecture Documentation

## Service-Repository Pattern Implementation

This document explains how we implement the Service-Repository pattern in KubeServe.

## Pattern Overview

The Service-Repository pattern provides clear separation between:
- **HTTP concerns** (routes)
- **Business logic** (services)
- **Data access** (repositories)

## Directory Structure

```
app/
├── api/
│   └── v1/
│       └── users.py          # HTTP routes only
├── services/
│   └── user_service.py       # Business logic
├── repositories/
│   └── user_repository.py    # Database operations
├── models/
│   └── user.py               # SQLAlchemy models
└── schemas/
    └── user.py                # Pydantic schemas
```

## Layer Details

### 1. API Routes Layer (`app/api/`)

**Purpose**: Handle HTTP requests and responses

**Responsibilities**:
- Parse and validate HTTP requests
- Convert HTTP to service calls
- Convert service responses to HTTP
- Handle HTTP status codes
- Handle exceptions and return appropriate HTTP errors

**Rules**:
- ✅ Call services, never repositories
- ✅ Use Pydantic schemas for validation
- ✅ Return appropriate HTTP status codes
- ❌ No business logic
- ❌ No database queries

**Example**:
```python
from fastapi import APIRouter, Depends, HTTPException
from app.schemas.user import UserCreate, UserResponse
from app.services.user_service import UserService
from app.database import get_db

router = APIRouter()

@router.post("/users", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new user."""
    service = UserService(db)
    try:
        user = await service.create_user(user_data)
        return user
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

### 2. Service Layer (`app/services/`)

**Purpose**: Contain all business logic

**Responsibilities**:
- Implement business rules
- Orchestrate multiple repositories
- Handle transactions
- Validate business constraints
- Transform data between layers

**Rules**:
- ✅ Call repositories for data access
- ✅ Contain all business logic
- ✅ Handle transactions
- ❌ No direct database access
- ❌ No HTTP concerns

**Example**:
```python
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate
from sqlalchemy.ext.asyncio import AsyncSession

class UserService:
    def __init__(self, db: AsyncSession):
        self.repository = UserRepository(db)
    
    async def create_user(self, user_data: UserCreate):
        """Create a user with business logic."""
        # Business rule: Check if email exists
        existing = await self.repository.get_by_email(user_data.email)
        if existing:
            raise ValueError("Email already registered")
        
        # Business rule: Validate password strength
        if len(user_data.password) < 8:
            raise ValueError("Password must be at least 8 characters")
        
        # Create user via repository
        return await self.repository.create(user_data)
```

### 3. Repository Layer (`app/repositories/`)

**Purpose**: Abstract database operations

**Responsibilities**:
- Execute database queries
- Map database results to models
- Handle SQLAlchemy operations
- Provide data access methods

**Rules**:
- ✅ Handle all database operations
- ✅ Return domain models
- ✅ Abstract SQLAlchemy complexity
- ❌ No business logic
- ❌ No HTTP concerns

**Example**:
```python
from app.models.user import User
from app.schemas.user import UserCreate
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_by_email(self, email: str) -> User | None:
        """Get user by email."""
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()
    
    async def create(self, user_data: UserCreate) -> User:
        """Create a new user."""
        user = User(**user_data.dict())
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user
```

### 4. Models Layer (`app/models/`)

**Purpose**: Define database schema

**Responsibilities**:
- Define SQLAlchemy ORM models
- Define table structure
- Define relationships
- Define constraints

**Example**:
```python
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from app.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False)
    
    # Relationships
    models = relationship("Model", back_populates="user")
```

### 5. Schemas Layer (`app/schemas/`)

**Purpose**: Define API contracts

**Responsibilities**:
- Validate request data
- Define response structure
- Serialize/deserialize data
- Document API

**Example**:
```python
from pydantic import BaseModel, EmailStr
from datetime import datetime

class UserCreate(BaseModel):
    """Schema for creating a user."""
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    """Schema for user response."""
    id: int
    email: str
    created_at: datetime
    
    class Config:
        from_attributes = True
```

## Data Flow Example

### Creating a User

```
1. HTTP POST /api/v1/users
   ↓
2. API Route (app/api/v1/users.py)
   - Validates request with UserCreate schema
   - Calls UserService.create_user()
   ↓
3. Service (app/services/user_service.py)
   - Checks business rules (email unique, password strength)
   - Calls UserRepository.create()
   ↓
4. Repository (app/repositories/user_repository.py)
   - Executes SQL INSERT
   - Returns User model
   ↓
5. Service
   - Returns User model
   ↓
6. API Route
   - Converts User to UserResponse schema
   - Returns HTTP 201 with JSON
```

## Benefits

1. **Testability**: Each layer can be tested independently
2. **Maintainability**: Changes in one layer don't affect others
3. **Reusability**: Services can be reused across different API endpoints
4. **Clarity**: Clear separation of concerns makes code easier to understand
5. **Flexibility**: Easy to swap implementations (e.g., different database)

## Testing Strategy

- **API Tests**: Test HTTP layer with mocked services
- **Service Tests**: Test business logic with mocked repositories
- **Repository Tests**: Test database operations with test database
- **Integration Tests**: Test full flow with real database

## Common Patterns

### Dependency Injection

Services receive database session via dependency injection:

```python
# In route
@router.post("/users")
async def create_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    service = UserService(db)
    return await service.create_user(user_data)
```

### Transaction Management

Services handle transactions:

```python
async def create_user_with_model(self, user_data, model_data):
    async with self.db.begin():
        user = await self.user_repo.create(user_data)
        model = await self.model_repo.create(model_data, user_id=user.id)
        return user, model
```

## Next Steps

As we build features, we'll follow this pattern consistently:
- Phase 1.2: Authentication (User model, service, repository)
- Phase 1.3: Model Registry (Model, ModelVersion models)
- Phase 1.4: Artifact Storage (Minio service)

