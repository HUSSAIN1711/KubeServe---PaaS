# KubeServe Scripts

This directory contains automation scripts for managing the KubeServe platform.

## Quick Start Scripts

### `start-backend.sh` - One-Command Startup

**The easiest way to start everything!**

Starts all backend infrastructure (Phases 0-5) with a single command:

```bash
./scripts/start-backend.sh
```

**What it does**:
1. ✅ Checks prerequisites (Docker, kubectl, helm, kind, python3)
2. ✅ Starts Docker services (Minio, PostgreSQL)
3. ✅ Creates Kind Kubernetes cluster (if needed)
4. ✅ Builds and pushes inference server image
5. ✅ Installs NGINX Ingress Controller (if needed)
6. ✅ Installs Prometheus and Grafana (if needed)
7. ✅ Sets up Python virtual environment
8. ✅ Installs Python dependencies
9. ✅ Runs database migrations
10. ✅ Starts FastAPI API server

**First run**: Takes 5-10 minutes (downloads images, builds)
**Subsequent runs**: Takes 1-2 minutes (reuses existing resources)

### `stop-backend.sh` - Shutdown Script

Stops all services:

```bash
./scripts/stop-backend.sh
```

Prompts to optionally remove the Kind cluster.

## Infrastructure Scripts

### `setup-kind-cluster.sh`

Creates a Kind Kubernetes cluster with local Docker registry.

```bash
./scripts/setup-kind-cluster.sh
```

**Features**:
- Creates Kind cluster named `kubeserve`
- Sets up local Docker registry on port 5001
- Configures cluster to use local registry
- Handles port conflicts

### `verify-phase0.sh`

Verifies Phase 0 infrastructure is running correctly.

```bash
./scripts/verify-phase0.sh
```

**Checks**:
- Docker services (Minio, PostgreSQL)
- Kubernetes cluster connectivity
- Helm installation
- Network configuration

### `teardown-phase0.sh`

Stops Phase 0 services.

```bash
# Stop services (preserve data)
./scripts/teardown-phase0.sh

# Full cleanup (remove everything)
./scripts/teardown-phase0.sh --full-cleanup
```

## Installation Scripts

### `install-ingress-controller.sh`

Installs NGINX Ingress Controller via Helm.

```bash
./scripts/install-ingress-controller.sh
```

**Features**:
- Installs via Helm
- Configures NodePort (30080/30443)
- Waits for readiness

### `install-prometheus.sh`

Installs Prometheus and Grafana via Helm (kube-prometheus-stack).

```bash
./scripts/install-prometheus.sh
```

**Features**:
- Installs Prometheus + Grafana
- Configures NodePort (30090/30091)
- Sets retention to 30 days
- Default Grafana password: `admin`

### `import-grafana-dashboards.sh`

Imports Grafana dashboards for KubeServe.

```bash
./scripts/import-grafana-dashboards.sh
```

**Requirements**:
- Prometheus/Grafana installed
- `jq` installed
- `curl` installed

## Testing Scripts

### `integration_test.sh`

End-to-end integration test (upload → deploy → predict → delete).

```bash
./scripts/integration_test.sh
```

See [INTEGRATION_TEST_GUIDE.md](../INTEGRATION_TEST_GUIDE.md) for details.

### `run-load-test.sh`

Runs Locust load tests against deployed models.

```bash
DEPLOYMENT_URL=http://localhost:30080/api/v1/predict/1 \
LOCUST_USERS=20 \
./scripts/run-load-test.sh
```

## Usage Examples

### Complete Fresh Start

```bash
# Start everything
./scripts/start-backend.sh

# In another terminal, test it
curl http://localhost:8000/health
```

### Restart After Stop

```bash
# Stop everything
./scripts/stop-backend.sh

# Start again (faster, reuses resources)
./scripts/start-backend.sh
```

### Clean Slate

```bash
# Remove everything
./scripts/teardown-phase0.sh --full-cleanup

# Start fresh
./scripts/start-backend.sh
```

## Script Dependencies

Most scripts require:
- `bash` (version 4+)
- `curl` (for health checks)
- `jq` (for JSON parsing in some scripts)

Install on macOS:
```bash
brew install jq
```

## Troubleshooting

### Script Permission Denied

```bash
chmod +x scripts/start-backend.sh
```

### Script Fails Silently

Run with verbose output:
```bash
bash -x scripts/start-backend.sh
```

### Port Conflicts

Check what's using the port:
```bash
lsof -i :8000  # API server
lsof -i :9000  # Minio
lsof -i :5432  # PostgreSQL
```

### Script Hangs

Check if services are actually starting:
```bash
docker-compose ps
kubectl get pods -A
```

## Script Architecture

All scripts follow these principles:
- **Idempotent**: Safe to run multiple times
- **Error handling**: Clear error messages
- **Color output**: Easy to read status
- **Progress indicators**: Shows what's happening
- **Graceful degradation**: Continues if optional steps fail

