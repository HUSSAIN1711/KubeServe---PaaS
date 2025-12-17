# KubeServe PaaS

A secure, scalable "Heroku for Machine Learning" platform that bridges the gap between Data Science (Models) and DevOps (Kubernetes).

## 🎯 Project Goal

Build a multi-tenant ML Inference Platform where users upload their own models (scikit-learn) and receive a scalable, monitored API endpoint on Kubernetes.

## 🏗️ Architecture

### High-Level Overview

```
┌─────────────────┐
│   React Frontend │ (Phase 7)
└────────┬────────┘
         │
┌────────▼────────┐
│  FastAPI Backend │ (Control Plane)
│  - Auth          │
│  - Model Registry│
│  - Deployments   │
└────────┬────────┘
         │
    ┌────┴────┬──────────────┬─────────────┐
    │         │              │             │
┌───▼───┐ ┌──▼───┐    ┌─────▼─────┐  ┌────▼────┐
│Postgres│ │Minio │    │ Kubernetes│  │Prometheus│
│  DB    │ │  S3  │    │  Cluster  │  │  Metrics │
└────────┘ └──────┘    └───────────┘  └─────────┘
```

### Technology Stack

- **Backend**: FastAPI (Python) with async SQLAlchemy
- **Database**: PostgreSQL
- **Storage**: Minio (S3-compatible)
- **Orchestration**: Kubernetes (Kind for local dev)
- **Package Management**: Helm
- **Observability**: Prometheus + Grafana
- **Frontend**: Next.js + Tailwind CSS (Phase 7)

## 📁 Project Structure

```
KubeServe/
├── app/
│   ├── api/              # API routes (HTTP layer only)
│   │   └── v1/           # API versioning
│   ├── models/           # SQLAlchemy database models
│   ├── repositories/     # Data access layer
│   ├── services/         # Business logic layer
│   ├── schemas/          # Pydantic schemas (request/response)
│   ├── config.py         # Application settings (pydantic-settings)
│   ├── database.py       # Database connection & session management
│   └── main.py           # FastAPI application entry point
├── alembic/              # Database migrations
├── charts/               # Helm charts (Phase 4)
├── scripts/              # Setup and utility scripts
├── docker-compose.yml    # Local development services
├── requirements.txt       # Python dependencies
└── .env                  # Environment variables (not in git)
```

## 🏛️ Architecture Pattern: Service-Repository

We follow a strict **Service-Repository pattern** to ensure clean separation of concerns:

### Layer Responsibilities

1. **API Routes** (`app/api/`)
   - Handle HTTP requests/responses
   - Validate input using Pydantic schemas
   - Call services (never repositories directly)
   - Return HTTP responses

2. **Services** (`app/services/`)
   - Contain all business logic
   - Orchestrate multiple repositories
   - Handle transactions
   - Never directly access database

3. **Repositories** (`app/repositories/`)
   - Handle all database operations
   - Abstract SQLAlchemy queries
   - No business logic
   - Return domain models

4. **Models** (`app/models/`)
   - SQLAlchemy ORM models
   - Database schema definition
   - Relationships between entities

5. **Schemas** (`app/schemas/`)
   - Pydantic models for request/response validation
   - API contract definition

### Example Flow

```
HTTP Request
    ↓
API Route (app/api/v1/users.py)
    ↓
Service (app/services/user_service.py)
    ↓
Repository (app/repositories/user_repository.py)
    ↓
Database (PostgreSQL)
```

### Rules

- ❌ **Never** put business logic in routes
- ❌ **Never** call repositories directly from routes
- ❌ **Never** put business logic in repositories
- ✅ Routes → Services → Repositories → Database

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- Docker & Docker Compose
- kubectl
- helm
- kind (or minikube)

### Phase 0: Infrastructure Setup

See [phase0-setup.md](phase0-setup.md) for detailed instructions.

Quick start:
```bash
# 1. Set up Kind cluster
./scripts/setup-kind-cluster.sh

# 2. Start services (Minio, PostgreSQL)
docker-compose up -d

# 3. Verify setup
./scripts/verify-phase0.sh
```

### Phase 1: Control Plane Setup

```bash
# 1. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# 4. Run database migrations
alembic upgrade head

# 5. Start the application
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`
- API docs: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/health`

## 📚 Development Guidelines

### Code Style

- Follow PEP 8
- Use type hints
- Maximum line length: 100 characters
- Use `black` for formatting
- Use `ruff` for linting
- Use `mypy` for type checking

### Running Tests

```bash
pytest
```

### Database Migrations

```bash
# Create a new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## 📖 Roadmap

See [ROADMAP.md](ROADMAP.md) for the complete development roadmap.

**Current Phase**: Phase 1.1 - Project Scaffolding ✅

## 🤝 Contributing

This is a learning project. Contributions and suggestions are welcome!

## 📄 License

[Add license information]

