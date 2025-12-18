# KubeServe Quick Start Guide

## One-Command Backend Startup

Start all backend infrastructure (Phases 0-5) with a single command:

```bash
# Make scripts executable (first time only)
chmod +x scripts/start-backend.sh scripts/stop-backend.sh

# Start everything
./scripts/start-backend.sh
```

**Note**: If you get a "permission denied" error, run `chmod +x scripts/start-backend.sh` first.

This script automatically:
1. ✅ Checks prerequisites (Docker, kubectl, helm, kind)
2. ✅ Starts Docker services (Minio, PostgreSQL)
3. ✅ Creates Kind Kubernetes cluster (if needed)
4. ✅ Builds and pushes inference server image
5. ✅ Installs NGINX Ingress Controller (if needed)
6. ✅ Installs Prometheus and Grafana (if needed)
7. ✅ Runs database migrations
8. ✅ Starts the FastAPI API server

The API will be available at:
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Minio Console**: http://localhost:9001 (minioadmin/minioadmin)
- **Prometheus**: http://localhost:30090
- **Grafana**: http://localhost:30091 (admin/admin)

## What Gets Started

### Docker Services
- **Minio** (S3-compatible storage) - Port 9000
- **PostgreSQL** (Database) - Port 5432
- **Docker Registry** (Local) - Port 5001

### Kubernetes (Kind)
- **Cluster**: `kubeserve`
- **Namespace**: `user-*` (created per user)
- **Ingress Controller**: NGINX (NodePort 30080/30443)
- **Prometheus Stack**: Monitoring (NodePort 30090/30091)

### FastAPI Server
- **Port**: 8000
- **Auto-reload**: Enabled
- **Database**: Connected to PostgreSQL
- **Migrations**: Applied automatically

## Prerequisites

The script checks for and requires:
- **Docker** (with daemon running)
- **kubectl** (Kubernetes CLI)
- **helm** (Helm package manager)
- **kind** (Kubernetes in Docker)
- **Python 3.10+** (for API server)
- **curl** (for health checks)

## First-Time Setup

On first run, the script will:
1. Create a Python virtual environment (`venv/`)
2. Install all Python dependencies
3. Create `.env` file from `.env.example` (if missing)
4. Set up the Kind cluster
5. Install all Helm charts

**Note**: You may need to edit `.env` if defaults don't work for your setup.

## Stopping Everything

To stop all services:

```bash
./scripts/stop-backend.sh
```

This will:
- Stop Docker services (Minio, PostgreSQL)
- Optionally remove the Kind cluster (prompts for confirmation)
- Keep your data intact (unless you remove the cluster)

## Manual Steps (Optional)

If you prefer manual control:

### Start Infrastructure Only
```bash
# Start Docker services
docker-compose up -d

# Setup Kind cluster
./scripts/setup-kind-cluster.sh

# Install Ingress
./scripts/install-ingress-controller.sh

# Install Prometheus
./scripts/install-prometheus.sh
```

### Start API Server Only
```bash
source venv/bin/activate
alembic upgrade head
uvicorn app.main:app --reload
```

## Troubleshooting

### Docker Registry Push Fails (HTTPS/Insecure Registry Error)

**Error**: `failed to do request: Head "https://localhost:5001/...": dial tcp [::1]:5001: i/o timeout`

**Solution**: Configure Docker Desktop to allow insecure registries:

1. Open Docker Desktop
2. Go to **Settings** > **Docker Engine**
3. Add this to the JSON configuration:
   ```json
   {
     "insecure-registries": ["localhost:5001"]
   }
   ```
4. Click **Apply & Restart**
5. Wait for Docker to restart
6. Run the startup script again

**Alternative** (Linux): Edit `/etc/docker/daemon.json`:
```json
{
  "insecure-registries": ["localhost:5001"]
}
```
Then restart Docker: `sudo systemctl restart docker`

### Script Fails at Prerequisites Check

**Error**: Command not found

**Solution**: Install missing tools:
```bash
# macOS
brew install docker kubectl helm kind

# Start Docker Desktop
```

### Docker Daemon Not Running

**Error**: Cannot connect to Docker daemon

**Solution**: Start Docker Desktop or Docker daemon

### Port Already in Use

**Error**: Port conflict

**Solution**: 
- Check what's using the port: `lsof -i :8000`
- Stop conflicting service or change port in `.env`

### Kind Cluster Creation Fails

**Error**: Cluster creation timeout

**Solution**:
- Ensure Docker has enough resources (4GB+ RAM)
- Check Docker is running: `docker info`
- Try removing existing cluster: `kind delete cluster --name kubeserve`

### Database Connection Fails

**Error**: `role "kubeserve" does not exist` or `Cannot connect to PostgreSQL`

**Solution**:
- Check PostgreSQL is running: `docker-compose ps`
- Verify `.env` has correct `DATABASE_URL` matching docker-compose.yml:
  ```env
  DATABASE_URL=postgresql+asyncpg://kubeserve:kubeserve_dev@localhost:5432/kubeserve
  ```
  (User: `kubeserve`, Password: `kubeserve_dev`, Database: `kubeserve`)
- Check logs: `docker-compose logs postgres`
- Wait a few seconds after starting PostgreSQL before running migrations

### Image Push Fails

**Error**: Cannot push to registry

**Solution**:
- Verify registry is running: `docker ps | grep registry`
- Check registry port (default: 5001)
- Ensure Kind cluster can access registry

## Environment Variables

The script uses `.env` file. Key variables:

```env
# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/kubeserve

# Minio/S3
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET_NAME=kubeserve-models

# Kubernetes
KUBECONFIG=  # Uses default ~/.kube/config
INGRESS_HOST=localhost
INGRESS_BASE_PATH=/api/v1/predict

# JWT
JWT_SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
```

## What's Running

After startup, you can verify everything:

```bash
# Docker services
docker-compose ps

# Kubernetes cluster
kubectl cluster-info
kubectl get nodes

# Helm releases
helm list -A

# API health
curl http://localhost:8000/health
```

## Next Steps

Once the backend is running:

1. **Test the API**: Visit http://localhost:8000/docs
2. **Run Integration Test**: `./scripts/integration_test.sh`
3. **Start Frontend**: `cd frontend && npm install && npm run dev`
4. **View Metrics**: http://localhost:30091 (Grafana)

## Notes

- The script is idempotent - safe to run multiple times
- Existing resources are reused (won't recreate if already exists)
- First run may take 5-10 minutes (downloads images, builds)
- Subsequent runs are faster (1-2 minutes)
- All data persists between restarts (unless cluster is deleted)

