# KubeServe PaaS - Project Context

## Current Goals
- **Phase 0**: ✅ Complete - Local development infrastructure set up
- **Phase 1.1**: ✅ Complete - Project Scaffolding (FastAPI setup with Service-Repository pattern)
- **Phase 1.2**: ✅ Complete - Authentication (JWT implementation)
- **Phase 1.3**: ✅ Complete - Model Registry (Database Schema)
- **Phase 1.4**: ✅ Complete - Artifact Storage (Minio/S3 integration)
- **Next**: Phase 2 - The Optimized Inference Engine

## Architectural Decisions
- **Backend**: FastAPI with async SQLAlchemy
- **Database**: PostgreSQL (production), SQLite (dev option)
- **Migrations**: Alembic
- **Architecture Pattern**: Service-Repository pattern (strict separation of concerns)
- **Authentication**: JWT with python-jose
- **Storage**: Minio (S3-compatible) for model artifacts
- **Orchestration**: Kubernetes with Helm charts
- **Frontend**: Next.js + Tailwind CSS (Phase 7)

## Recent Changes
- Project initialized
- ROADMAP.md created
- context.md created for stateful memory
- Phase 0 setup files created:
  - `docker-compose.yml` for Minio and PostgreSQL (with restart policies, custom network, improved healthchecks)
  - `phase0-setup.md` with installation instructions (updated with automated script reference)
  - `scripts/verify-phase0.sh` verification script (updated with network check)
  - `scripts/setup-kind-cluster.sh` automated Kind cluster setup script (uses port 5001 for registry to avoid AirPlay Receiver conflict)
  - `scripts/teardown-phase0.sh` teardown script to stop/cleanup all Phase 0 services
  - `.gitignore` for Python project
  - `.env` and `.env.example` files created
- Phase 1.1 completed:
  - FastAPI project structure initialized
  - pydantic-settings configured for environment management
  - SQLAlchemy (Async) set up with database connection
  - Alembic configured for database migrations
  - Service-Repository pattern structure created
  - README.md and ARCHITECTURE.md documentation created
- Phase 1.2 completed:
  - User model created (id, email, password_hash, role)
  - User schemas created (UserCreate, UserResponse, UserLogin, Token)
  - UserRepository implemented for database operations
  - UserService implemented with business logic (password hashing, validation)
  - Security utilities created (password hashing with passlib, JWT with python-jose)
  - Auth routes created (POST /api/v1/auth/register, POST /api/v1/auth/login)
  - Authentication dependency created (get_current_user, get_current_active_user)
  - Protected route example created (GET /api/v1/me)
  - Alembic migration created for users table
- Phase 1.3 completed:
  - Model, ModelVersion, and Deployment database models created
  - Model schemas created (ModelCreate, ModelResponse, ModelVersionCreate, etc.)
  - Model repositories created (ModelRepository, ModelVersionRepository, DeploymentRepository)
  - Model services created with business logic (ownership verification, status validation)
  - Model API routes created (CRUD operations for models, versions, deployments)
  - Alembic migration created for model registry tables
- Testing infrastructure completed:
  - pytest configuration and fixtures set up
  - Unit tests for authentication (happy and sad paths) - 13 tests
  - Unit tests for model registry (happy and sad paths) - 20 tests
  - Test fixtures for database, test client, users, models, versions, deployments
  - Test documentation created
- Phase 1.4 completed:
  - Minio client wrapper created (`app/core/storage.py`) for S3 operations
  - Storage service created (`app/services/storage_service.py`) with business logic for file validation
  - File upload endpoint created (POST `/api/v1/versions/{version_id}/upload`)
  - Upload logic implemented: stores files in `s3://models/{user_id}/{model_name}/{version_tag}/`
  - File validation: model files (.joblib, .pkl, .pickle) max 500MB, requirements.txt max 1MB
  - Model version s3_path updated after successful upload
  - Service method added to update version S3 path (`update_version_s3_path`)

