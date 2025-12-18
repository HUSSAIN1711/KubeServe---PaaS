#!/bin/bash
#
# KubeServe Backend Startup Script
# Starts all infrastructure and services needed for Phases 0-5
# This script abstracts away all the manual setup steps
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     KubeServe Backend Startup Script                     ║${NC}"
echo -e "${BLUE}║     Starting Phases 0-5 Infrastructure                   ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check prerequisites
echo -e "${YELLOW}📋 Checking prerequisites...${NC}"

check_command() {
    if ! command -v "$1" &> /dev/null; then
        echo -e "${RED}❌ $1 is not installed${NC}"
        echo "   Please install it first:"
        case "$1" in
            docker)
                echo "   macOS: Install Docker Desktop"
                echo "   Linux: sudo apt-get install docker.io"
                ;;
            kubectl)
                echo "   brew install kubectl"
                echo "   or visit: https://kubernetes.io/docs/tasks/tools/"
                ;;
            helm)
                echo "   brew install helm"
                echo "   or visit: https://helm.sh/docs/intro/install/"
                ;;
            kind)
                echo "   brew install kind"
                echo "   or visit: https://kind.sigs.k8s.io/docs/user/quick-start/"
                ;;
        esac
        exit 1
    else
        echo -e "${GREEN}✅ $1 is installed${NC}"
    fi
}

check_command docker
check_command kubectl
check_command helm
check_command kind

# Check if Docker daemon is running
if ! docker info &> /dev/null; then
    echo -e "${RED}❌ Docker daemon is not running${NC}"
    echo "   Please start Docker Desktop or the Docker daemon"
    exit 1
fi
echo -e "${GREEN}✅ Docker daemon is running${NC}"
echo ""

# Phase 0.1: Start Docker services (Minio, PostgreSQL)
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}Phase 0.1: Starting Docker Services${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

cd "$PROJECT_ROOT"

# If network was created manually before, remove it to avoid warnings
# docker-compose will recreate it with proper labels
if docker network ls | grep -q kubeserve-network; then
    # Check if any containers are using it
    if ! docker ps -a --filter network=kubeserve-network --format '{{.Names}}' | grep -q .; then
        echo "Removing existing network to recreate with docker-compose..."
        docker network rm kubeserve-network 2>/dev/null || true
    fi
fi

echo "Starting Minio and PostgreSQL..."
# docker-compose will create the network automatically with proper labels
docker-compose up -d

echo "Waiting for services to be ready..."
sleep 5

# Check Minio health
echo "Checking Minio health..."
MAX_RETRIES=30
RETRY=0
while [ $RETRY -lt $MAX_RETRIES ]; do
    if curl -s -f http://localhost:9000/minio/health/live > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Minio is ready${NC}"
        break
    fi
    RETRY=$((RETRY + 1))
    sleep 2
done

if [ $RETRY -eq $MAX_RETRIES ]; then
    echo -e "${YELLOW}⚠️  Minio health check timed out, but continuing...${NC}"
fi

# Check PostgreSQL health
echo "Checking PostgreSQL health..."
RETRY=0
while [ $RETRY -lt $MAX_RETRIES ]; do
    if docker exec kubeserve-postgres pg_isready -U postgres > /dev/null 2>&1; then
        echo -e "${GREEN}✅ PostgreSQL is ready${NC}"
        break
    fi
    RETRY=$((RETRY + 1))
    sleep 2
done

if [ $RETRY -eq $MAX_RETRIES ]; then
    echo -e "${YELLOW}⚠️  PostgreSQL health check timed out, but continuing...${NC}"
fi

echo ""

# Phase 0.2: Setup Kind cluster
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}Phase 0.2: Setting up Kubernetes Cluster${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

if kind get clusters | grep -q kubeserve; then
    echo "Kind cluster 'kubeserve' already exists"
    if ! kubectl cluster-info &> /dev/null; then
        echo "Configuring kubectl context..."
        kind get kubeconfig --name kubeserve > /tmp/kubeserve-kubeconfig.yaml
        export KUBECONFIG=/tmp/kubeserve-kubeconfig.yaml
    fi
    echo -e "${GREEN}✅ Using existing Kind cluster${NC}"
else
    echo "Creating Kind cluster with local registry..."
    "$SCRIPT_DIR/setup-kind-cluster.sh"
    echo -e "${GREEN}✅ Kind cluster created${NC}"
fi

# Verify cluster is accessible
if ! kubectl cluster-info &> /dev/null; then
    echo -e "${RED}❌ Cannot connect to Kubernetes cluster${NC}"
    exit 1
fi

echo ""

# Phase 2: Build and push inference server image
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}Phase 2: Building Inference Server Image${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Ensure registry is running
REGISTRY_NAME="kind-registry"
REGISTRY_PORT="5001"

echo "Checking Docker registry..."
if ! docker ps --format '{{.Names}}' | grep -q "^${REGISTRY_NAME}$"; then
    echo "Starting Docker registry..."
    if docker ps -a --format '{{.Names}}' | grep -q "^${REGISTRY_NAME}$"; then
        docker start "${REGISTRY_NAME}"
    else
        docker run -d \
            --name "${REGISTRY_NAME}" \
            --restart=unless-stopped \
            -p "${REGISTRY_PORT}:5000" \
            registry:2
    fi
    echo "Waiting for registry to be ready..."
    sleep 3
fi

# Verify registry is accessible
if ! curl -s "http://localhost:${REGISTRY_PORT}/v2/" > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Registry might not be fully ready, but continuing...${NC}"
fi

# Configure Docker to use insecure registry (if not already configured)
if [ -f /etc/docker/daemon.json ]; then
    if ! grep -q "localhost:${REGISTRY_PORT}" /etc/docker/daemon.json 2>/dev/null; then
        echo -e "${YELLOW}⚠️  Docker daemon.json exists but doesn't include localhost:${REGISTRY_PORT}${NC}"
        echo -e "${YELLOW}   You may need to add it manually for insecure registry support${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Note: For insecure registry support, add to Docker Desktop settings:${NC}"
    echo -e "${YELLOW}   Settings > Docker Engine > Add: \"insecure-registries\": [\"localhost:5001\"]${NC}"
fi

cd "$PROJECT_ROOT/inference-server"

echo "Building kubeserve-base image..."
docker build -t kubeserve-base:latest .

echo "Tagging for local registry..."
docker tag kubeserve-base:latest localhost:${REGISTRY_PORT}/kubeserve-base:latest

echo "Pushing to local registry..."
PUSH_OUTPUT=$(docker push localhost:${REGISTRY_PORT}/kubeserve-base:latest 2>&1)
PUSH_EXIT_CODE=$?

if [ $PUSH_EXIT_CODE -ne 0 ]; then
    # Check for common error patterns
    if echo "$PUSH_OUTPUT" | grep -qi "insecure\|https\|tls\|certificate\|x509"; then
        echo -e "${RED}❌ Docker registry push failed - insecure registry not configured${NC}"
        echo ""
        echo -e "${YELLOW}Please configure Docker Desktop to allow insecure registries:${NC}"
        echo ""
        echo "1. Open Docker Desktop"
        echo "2. Go to Settings (gear icon) > Docker Engine"
        echo "3. Add this to the JSON configuration:"
        echo ""
        echo "   \"insecure-registries\": [\"localhost:5001\"]"
        echo ""
        echo "4. Click 'Apply & Restart'"
        echo "5. Wait for Docker to restart"
        echo "6. Run this script again: ./scripts/start-backend.sh"
        echo ""
        echo -e "${YELLOW}Full error output:${NC}"
        echo "$PUSH_OUTPUT"
        exit 1
    else
        echo -e "${RED}❌ Failed to push image to registry${NC}"
        echo ""
        echo "Checking registry status..."
        echo "Registry container:"
        docker ps | grep "${REGISTRY_NAME}" || echo "  ❌ Registry container not running"
        echo ""
        echo "Registry accessibility:"
        curl -s "http://localhost:${REGISTRY_PORT}/v2/" && echo "  ✅ Registry is accessible" || echo "  ❌ Registry not accessible"
        echo ""
        echo -e "${YELLOW}Full error output:${NC}"
        echo "$PUSH_OUTPUT"
        exit 1
    fi
fi

echo -e "${GREEN}✅ Inference server image built and pushed${NC}"
echo ""

# Phase 4.1: Install Ingress Controller
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}Phase 4.1: Installing NGINX Ingress Controller${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

if helm list -n ingress-nginx 2>/dev/null | grep -q ingress-nginx; then
    echo "NGINX Ingress Controller already installed"
    echo -e "${GREEN}✅ Using existing Ingress Controller${NC}"
else
    echo "Installing NGINX Ingress Controller..."
    "$SCRIPT_DIR/install-ingress-controller.sh"
    echo -e "${GREEN}✅ Ingress Controller installed${NC}"
fi

echo ""

# Phase 5.1: Install Prometheus and Grafana
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}Phase 5.1: Installing Prometheus and Grafana${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

if helm list -n monitoring 2>/dev/null | grep -q kube-prometheus-stack; then
    echo "Prometheus stack already installed"
    echo -e "${GREEN}✅ Using existing Prometheus/Grafana${NC}"
else
    echo "Installing Prometheus and Grafana..."
    if [ -f "$SCRIPT_DIR/install-prometheus.sh" ]; then
        "$SCRIPT_DIR/install-prometheus.sh"
        echo -e "${GREEN}✅ Prometheus and Grafana installed${NC}"
    else
        echo -e "${YELLOW}⚠️  install-prometheus.sh not found, skipping...${NC}"
        echo -e "${YELLOW}   You can install manually later if needed${NC}"
    fi
fi

echo ""

# Phase 1: Database migrations
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}Phase 1: Setting up Database${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

cd "$PROJECT_ROOT"

# Check if .env exists
if [ ! -f .env ]; then
    echo "Creating .env file..."
    if [ -f .env.example ]; then
        cp .env.example .env
        echo -e "${GREEN}✅ Created .env from .env.example${NC}"
    else
        # Create minimal .env with defaults
        cat > .env << EOF
# Database
# Note: User/password match docker-compose.yml postgres service
DATABASE_URL=postgresql+asyncpg://kubeserve:kubeserve_dev@localhost:5432/kubeserve

# Minio/S3
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET_NAME=kubeserve-models
MINIO_USE_SSL=false

# JWT
JWT_SECRET_KEY=your-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# Kubernetes
KUBECONFIG=
INGRESS_HOST=localhost
INGRESS_BASE_PATH=/api/v1/predict

# CORS
CORS_ORIGINS=["http://localhost:3000","http://localhost:3001"]
EOF
        echo -e "${GREEN}✅ Created .env with default values${NC}"
    fi
    echo -e "${YELLOW}⚠️  Using default .env values. Edit .env if needed.${NC}"
fi

# Check if virtual environment exists
VENV_PYTHON="$PROJECT_ROOT/venv/bin/python"
if [ ! -f "$VENV_PYTHON" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

echo "Installing Python dependencies..."
"$VENV_PYTHON" -m pip install -q --upgrade pip
"$VENV_PYTHON" -m pip install -q -r requirements.txt

echo "Running database migrations..."
"$VENV_PYTHON" -m alembic upgrade head

echo -e "${GREEN}✅ Database migrations completed${NC}"
echo ""

# Summary
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ All infrastructure is ready!${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${GREEN}📊 Service Status:${NC}"
echo ""
echo "Docker Services:"
docker-compose ps
echo ""
echo "Kubernetes Cluster:"
kubectl cluster-info --context kind-kubeserve 2>/dev/null || kubectl cluster-info
echo ""
echo "Helm Releases:"
helm list -A 2>/dev/null || echo "No Helm releases found"
echo ""
echo -e "${GREEN}🚀 Starting FastAPI Server...${NC}"
echo ""
echo "The API server will start on http://localhost:8000"
echo "API docs available at http://localhost:8000/docs"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop the server${NC}"
echo ""

# Start the FastAPI server
cd "$PROJECT_ROOT"
echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}🎉 Starting FastAPI Server...${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
exec "$VENV_PYTHON" -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

