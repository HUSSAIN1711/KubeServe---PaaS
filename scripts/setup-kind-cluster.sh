#!/bin/bash

# Kind Cluster Setup Script for KubeServe
# This script creates a Kind cluster with local registry support

set -e

CLUSTER_NAME="kubeserve"
REGISTRY_NAME="kind-registry"
REGISTRY_PORT="5001"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo_info() {
    echo -e "${GREEN}ℹ️  $1${NC}"
}

echo_warn() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

echo_error() {
    echo -e "${RED}❌ $1${NC}"
}

echo_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

# Check prerequisites
check_prerequisites() {
    echo_info "Checking prerequisites..."
    
    if ! command -v kind &> /dev/null; then
        echo_error "kind is not installed. Please install it first:"
        echo "  brew install kind"
        exit 1
    fi
    
    if ! command -v kubectl &> /dev/null; then
        echo_error "kubectl is not installed. Please install it first."
        exit 1
    fi
    
    if ! command -v docker &> /dev/null; then
        echo_error "docker is not installed. Please install it first."
        exit 1
    fi
    
    if ! docker ps &> /dev/null; then
        echo_error "Docker daemon is not running. Please start Docker first."
        exit 1
    fi
    
    echo_success "All prerequisites met"
}

# Delete existing cluster if it exists
cleanup_existing_cluster() {
    if kind get clusters | grep -q "^${CLUSTER_NAME}$"; then
        echo_warn "Cluster '${CLUSTER_NAME}' already exists"
        read -p "Do you want to delete and recreate it? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo_info "Deleting existing cluster..."
            kind delete cluster --name "${CLUSTER_NAME}"
            echo_success "Cluster deleted"
        else
            echo_info "Keeping existing cluster. Exiting."
            exit 0
        fi
    fi
}

# Check if port is available
check_port_available() {
    local port=$1
    if lsof -i :${port} &> /dev/null || nc -z localhost ${port} &> /dev/null; then
        return 1  # Port is in use
    fi
    return 0  # Port is available
}

# Create local Docker registry
setup_registry() {
    echo_info "Setting up local Docker registry..."
    
    # Check if registry container already exists
    if docker ps -a --format '{{.Names}}' | grep -q "^${REGISTRY_NAME}$"; then
        if docker ps --format '{{.Names}}' | grep -q "^${REGISTRY_NAME}$"; then
            echo_info "Registry container '${REGISTRY_NAME}' is already running"
        else
            # Check if port is available before starting
            if ! check_port_available "${REGISTRY_PORT}"; then
                echo_error "Port ${REGISTRY_PORT} is already in use. Cannot start registry."
                echo_warn "On macOS, this is often AirPlay Receiver. You can disable it:"
                echo "  System Settings > General > AirDrop & Handoff > AirPlay Receiver: Off"
                echo ""
                echo_warn "Alternatively, you can manually remove the existing registry container:"
                echo "  docker rm ${REGISTRY_NAME}"
                exit 1
            fi
            echo_info "Starting existing registry container..."
            docker start "${REGISTRY_NAME}"
        fi
    else
        # Check if port is available before creating
        if ! check_port_available "${REGISTRY_PORT}"; then
            echo_error "Port ${REGISTRY_PORT} is already in use. Cannot create registry."
            echo_warn "On macOS, this is often AirPlay Receiver. You can disable it:"
            echo "  System Settings > General > AirDrop & Handoff > AirPlay Receiver: Off"
            echo ""
            echo_warn "Or check what's using the port:"
            echo "  lsof -i :${REGISTRY_PORT}"
            exit 1
        fi
        
        echo_info "Creating new registry container..."
        docker run -d \
            --name "${REGISTRY_NAME}" \
            --restart=unless-stopped \
            -p "${REGISTRY_PORT}:5000" \
            registry:2
        echo_success "Registry container created"
    fi
    
    # Wait for registry to be ready
    echo_info "Waiting for registry to be ready..."
    sleep 2
    if curl -s "http://localhost:${REGISTRY_PORT}/v2/" > /dev/null 2>&1; then
        echo_success "Registry is ready at localhost:${REGISTRY_PORT}"
    else
        echo_warn "Registry might not be fully ready yet, but continuing..."
    fi
}

# Create Kind cluster configuration with registry
create_cluster_config() {
    echo_info "Creating Kind cluster configuration..."
    
    cat <<EOF > /tmp/kind-config.yaml
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
name: ${CLUSTER_NAME}
containerdConfigPatches:
- |-
  [plugins."io.containerd.grpc.v1.cri".registry.mirrors."localhost:${REGISTRY_PORT}"]
    endpoint = ["http://${REGISTRY_NAME}:5000"]
nodes:
- role: control-plane
  extraPortMappings:
  - containerPort: 30080
    hostPort: 30080
    protocol: TCP
  - containerPort: 30443
    hostPort: 30443
    protocol: TCP
EOF
    
    echo_success "Cluster configuration created"
}

# Create the Kind cluster
create_cluster() {
    echo_info "Creating Kind cluster '${CLUSTER_NAME}'..."
    kind create cluster --name "${CLUSTER_NAME}" --config /tmp/kind-config.yaml
    echo_success "Cluster created"
    
    # Connect registry to kind network
    echo_info "Connecting registry to Kind network..."
    docker network connect kind "${REGISTRY_NAME}" 2>/dev/null || \
        echo_warn "Registry might already be connected to kind network"
    
    # Configure Kubernetes to use local registry
    echo_info "Configuring Kubernetes to use local registry..."
    kubectl apply -f - <<EOF
apiVersion: v1
kind: ConfigMap
metadata:
  name: local-registry-hosting
  namespace: kube-public
data:
  localRegistryHosting.v1: |
    host: "localhost:${REGISTRY_PORT}"
    help: "https://kind.sigs.k8s.io/docs/user/local-registry/"
EOF
    
    echo_success "Registry configuration applied"
}

# Verify cluster setup
verify_cluster() {
    echo_info "Verifying cluster setup..."
    
    # Check cluster is running
    if kubectl cluster-info --context "kind-${CLUSTER_NAME}" &> /dev/null; then
        echo_success "Cluster is running and accessible"
    else
        echo_error "Cluster is not accessible"
        exit 1
    fi
    
    # Check nodes
    echo_info "Cluster nodes:"
    kubectl get nodes --context "kind-${CLUSTER_NAME}"
    
    # Check registry connectivity
    if docker network inspect kind | grep -q "${REGISTRY_NAME}"; then
        echo_success "Registry is connected to Kind network"
    else
        echo_warn "Registry might not be connected to Kind network"
    fi
    
    echo ""
    echo_success "Cluster setup complete!"
    echo_info "Cluster name: ${CLUSTER_NAME}"
    echo_info "Registry: localhost:${REGISTRY_PORT}"
    echo_info "To use this cluster: kubectl cluster-info --context kind-${CLUSTER_NAME}"
}

# Cleanup function
cleanup() {
    echo_info "Cleaning up temporary files..."
    rm -f /tmp/kind-config.yaml
}

# Main execution
main() {
    echo_info "Starting Kind cluster setup for KubeServe..."
    echo ""
    
    check_prerequisites
    cleanup_existing_cluster
    setup_registry
    create_cluster_config
    create_cluster
    verify_cluster
    cleanup
    
    echo ""
    echo_success "Setup complete! Your Kind cluster is ready."
    echo_info "Next steps:"
    echo "  1. Run: docker-compose up -d (to start Minio and PostgreSQL)"
    echo "  2. Run: ./scripts/verify-phase0.sh (to verify everything)"
}

# Trap to cleanup on exit
trap cleanup EXIT

# Run main function
main

