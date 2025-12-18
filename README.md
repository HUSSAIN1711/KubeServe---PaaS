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

## 🚀 Quick Start

### One-Command Backend Startup

Start all backend infrastructure (Phases 0-5) with a single command:

```bash
# Make scripts executable (first time only)
chmod +x scripts/start-backend.sh scripts/stop-backend.sh

# Start everything
./scripts/start-backend.sh
```

**Note**: If you get a "permission denied" error, run `chmod +x scripts/start-backend.sh` first.

This automatically:
- ✅ Starts Docker services (Minio, PostgreSQL)
- ✅ Sets up Kubernetes cluster (Kind)
- ✅ Builds and pushes inference server image
- ✅ Installs Ingress Controller
- ✅ Installs Prometheus & Grafana
- ✅ Runs database migrations
- ✅ Starts the FastAPI API server

**API will be available at**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Minio Console**: http://localhost:9001 (minioadmin/minioadmin)
- **Prometheus**: http://localhost:30090
- **Grafana**: http://localhost:30091 (admin/admin)

See [QUICKSTART.md](QUICKSTART.md) for detailed instructions and troubleshooting.

### Prerequisites

- Python 3.10+
- Docker & Docker Compose (daemon running)
- kubectl
- helm
- kind

### Manual Setup (Alternative)

If you prefer step-by-step setup, see [phase0-setup.md](phase0-setup.md) for detailed instructions.

### Stopping Everything

```bash
./scripts/stop-backend.sh
```

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

