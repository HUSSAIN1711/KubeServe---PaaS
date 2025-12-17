# KubeServe PaaS - Project Context

## Current Goals
- **Phase 0**: Setting up local development infrastructure (Kubernetes cluster, Minio, PostgreSQL, Docker registry)
- **Next**: Phase 1.1 - Project Scaffolding (FastAPI setup with Service-Repository pattern)

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

