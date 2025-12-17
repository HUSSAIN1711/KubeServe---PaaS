# Phase 0: Local Development Infrastructure Setup

This guide will help you set up the local "Data Center" for KubeServe development.

---

## Automated Setup (Recommended)

This is the fastest and easiest way to set up your local development environment. All steps are automated using provided scripts.

### Prerequisites

Before starting, ensure you have the following installed:
- Docker Desktop (or Docker Engine)
- kubectl
- helm
- kind

Check what's installed:
```bash
which kubectl helm docker kind
```

### Step 1: Start Docker Daemon

**macOS:**
- Start Docker Desktop application
- Wait for Docker to fully start (whale icon in menu bar should be steady)

**Linux:**
```bash
sudo systemctl start docker
# Or if using Docker Desktop:
systemctl --user start docker-desktop
```

**Verify Docker is running:**
```bash
docker ps
```

If you see an error like "Cannot connect to the Docker daemon", Docker is not running. Start it before continuing.

### Step 2: Set Up Kubernetes Cluster (Kind)

Run the automated setup script:
```bash
./scripts/setup-kind-cluster.sh
```

This script will:
- Check all prerequisites
- Create a Kind cluster named `kubeserve`
- Set up a local Docker registry on port 5001
- Configure the cluster to use the local registry
- Verify the cluster is working

### Step 3: Start Minio and PostgreSQL

Start the required services using Docker Compose:
```bash
docker-compose up -d
```

This will start:
- **Minio** (S3-compatible storage) on ports 9000 (API) and 9001 (Console)
- **PostgreSQL** (Database) on port 5432

### Step 4: Verify Everything is Working

Run the verification script:
```bash
./scripts/verify-phase0.sh
```

This will check:
- ✅ kubectl connectivity
- ✅ helm installation
- ✅ docker daemon
- ✅ Minio service
- ✅ PostgreSQL service
- ✅ Docker network

### Step 5: Create Environment Variables File

Create a `.env` file in the project root:
```env
# Database
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
KUBECONFIG=~/.kube/config
```

### Quick Access

Once everything is running:
- **Minio Console:** http://localhost:9001 (minioadmin / minioadmin)
- **Minio API:** http://localhost:9000
- **PostgreSQL:** localhost:5432 (kubeserve / kubeserve_dev)
- **Docker Registry:** localhost:5001

---

## Manual Setup

If you prefer manual control, need to use Minikube instead of Kind, or want to understand each step in detail, follow these instructions.

### Prerequisites

Install the following tools if missing:

**Helm:**
```bash
# macOS
brew install helm

# Linux
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
```

**Kubernetes Cluster (choose one):**

**Option A: Kind (Kubernetes in Docker) - Recommended**
```bash
# macOS
brew install kind

# Linux
curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.20.0/kind-linux-amd64
chmod +x ./kind
sudo mv ./kind /usr/local/bin/kind
```

**Option B: Minikube**
```bash
# macOS
brew install minikube

# Linux
curl -Lo minikube https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
chmod +x minikube
sudo mv minikube /usr/local/bin/
```

### Step 1: Start Docker Daemon

**macOS:**
- Start Docker Desktop application
- Wait for Docker to fully start

**Linux:**
```bash
sudo systemctl start docker
# Or if using Docker Desktop:
systemctl --user start docker-desktop
```

**Verify:**
```bash
docker ps
```

### Step 2: Create Kubernetes Cluster

**If using Kind:**
```bash
kind create cluster --name kubeserve
kubectl cluster-info --context kind-kubeserve
```

**If using Minikube:**
```bash
minikube start
kubectl cluster-info
```

### Step 3: Set Up Local Docker Registry (Optional but Recommended)

**If using Kind:**
```bash
# Create registry container (using port 5001 to avoid conflict with AirPlay Receiver on macOS)
docker run -d --name kind-registry -p 5001:5000 registry:2

# Connect registry to kind network
docker network connect kind kind-registry || true

# Configure kind to use local registry
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: ConfigMap
metadata:
  name: local-registry-hosting
  namespace: kube-public
data:
  localRegistryHosting.v1: |
    host: "localhost:5001"
    help: "https://kind.sigs.k8s.io/docs/user/local-registry/"
EOF
```

**If using Minikube:**
```bash
minikube addons enable registry
```

### Step 4: Start Minio and PostgreSQL

```bash
docker-compose up -d
```

Verify services are running:
```bash
docker-compose ps
```

### Step 5: Manual Verification

**Check Kubernetes:**
```bash
kubectl get nodes
kubectl get pods --all-namespaces
```

**Check Minio:**
- Console: http://localhost:9001
- API: http://localhost:9000
- Credentials: minioadmin / minioadmin

**Check PostgreSQL:**
```bash
docker exec -it kubeserve-postgres psql -U kubeserve -d kubeserve -c "SELECT version();"
```

**Check Helm:**
```bash
helm version
```

**Check Docker Registry (if set up):**
```bash
curl http://localhost:5001/v2/_catalog
```

### Step 6: Create Environment Variables File

Create a `.env` file in the project root (same as automated setup):
```env
# Database
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
KUBECONFIG=~/.kube/config
```

---

## Troubleshooting

### Kind Cluster Issues
```bash
kind delete cluster --name kubeserve
kind create cluster --name kubeserve
```

### Minikube Issues
```bash
minikube delete
minikube start
```

### Docker Compose Issues
```bash
docker-compose down -v
docker-compose up -d
```

### Docker Daemon Not Running
- **macOS:** Start Docker Desktop from Applications
- **Linux:** `sudo systemctl start docker` or `systemctl --user start docker-desktop`

---

## Stopping Services

When you're done working, you can stop all services using the teardown script:

**Stop services (preserves data):**
```bash
./scripts/teardown-phase0.sh
```
This stops all containers but keeps your data. You can restart with `docker-compose up -d`.

**Full cleanup (removes everything):**
```bash
./scripts/teardown-phase0.sh --full-cleanup
```
This removes all containers, volumes, and the Kind cluster. Use when you want a fresh start.

**Other options:**
```bash
./scripts/teardown-phase0.sh --help          # Show all options
./scripts/teardown-phase0.sh --cluster-only   # Remove only Kind cluster
./scripts/teardown-phase0.sh --registry-only # Remove only Docker registry
```

---

## Next Steps

Once all checks pass, proceed to **Phase 1.1: Project Scaffolding**.
