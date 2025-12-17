#!/bin/bash

# Phase 0 Teardown Script for KubeServe
# Stops all services and optionally cleans up resources

set -e

CLUSTER_NAME="kubeserve"
REGISTRY_NAME="kind-registry"

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

# Show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --stop-only      Stop services but keep containers/data (default)"
    echo "  --full-cleanup   Stop services and remove all containers, volumes, and cluster"
    echo "  --cluster-only    Stop/remove only the Kind cluster"
    echo "  --registry-only   Stop/remove only the Docker registry"
    echo "  --help           Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                    # Stop all services (can restart with docker-compose up)"
    echo "  $0 --full-cleanup      # Remove everything (fresh start needed)"
    echo "  $0 --cluster-only      # Remove only the Kind cluster"
}

# Stop Docker Compose services
stop_docker_compose() {
    echo_info "Stopping Docker Compose services..."
    if [ -f docker-compose.yml ]; then
        docker-compose down
        echo_success "Docker Compose services stopped"
    else
        echo_warn "docker-compose.yml not found, skipping..."
    fi
}

# Stop Docker Compose services and remove volumes
stop_docker_compose_with_volumes() {
    echo_info "Stopping Docker Compose services and removing volumes..."
    if [ -f docker-compose.yml ]; then
        docker-compose down -v
        echo_success "Docker Compose services stopped and volumes removed"
    else
        echo_warn "docker-compose.yml not found, skipping..."
    fi
}

# Stop Kind cluster
stop_kind_cluster() {
    echo_info "Checking for Kind cluster..."
    if kind get clusters | grep -q "^${CLUSTER_NAME}$"; then
        echo_warn "Kind cluster '${CLUSTER_NAME}' exists"
        read -p "Do you want to delete it? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo_info "Deleting Kind cluster..."
            kind delete cluster --name "${CLUSTER_NAME}"
            echo_success "Kind cluster deleted"
        else
            echo_info "Keeping Kind cluster"
        fi
    else
        echo_info "No Kind cluster found"
    fi
}

# Stop Kind cluster without prompt
stop_kind_cluster_force() {
    echo_info "Checking for Kind cluster..."
    if kind get clusters | grep -q "^${CLUSTER_NAME}$"; then
        echo_info "Deleting Kind cluster..."
        kind delete cluster --name "${CLUSTER_NAME}"
        echo_success "Kind cluster deleted"
    else
        echo_info "No Kind cluster found"
    fi
}

# Stop Docker registry
stop_registry() {
    echo_info "Checking for Docker registry..."
    if docker ps -a --format '{{.Names}}' | grep -q "^${REGISTRY_NAME}$"; then
        if docker ps --format '{{.Names}}' | grep -q "^${REGISTRY_NAME}$"; then
            echo_info "Stopping registry container..."
            docker stop "${REGISTRY_NAME}"
            echo_success "Registry container stopped"
        else
            echo_info "Registry container already stopped"
        fi
    else
        echo_info "No registry container found"
    fi
}

# Remove Docker registry
remove_registry() {
    echo_info "Checking for Docker registry..."
    if docker ps -a --format '{{.Names}}' | grep -q "^${REGISTRY_NAME}$"; then
        echo_info "Removing registry container..."
        docker stop "${REGISTRY_NAME}" 2>/dev/null || true
        docker rm "${REGISTRY_NAME}"
        echo_success "Registry container removed"
    else
        echo_info "No registry container found"
    fi
}

# Main execution
main() {
    local STOP_ONLY=false
    local FULL_CLEANUP=false
    local CLUSTER_ONLY=false
    local REGISTRY_ONLY=false

    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --stop-only)
                STOP_ONLY=true
                shift
                ;;
            --full-cleanup)
                FULL_CLEANUP=true
                shift
                ;;
            --cluster-only)
                CLUSTER_ONLY=true
                shift
                ;;
            --registry-only)
                REGISTRY_ONLY=true
                shift
                ;;
            --help)
                show_usage
                exit 0
                ;;
            *)
                echo_error "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done

    echo_info "Starting Phase 0 teardown..."
    echo ""

    # Handle specific operations
    if [ "$CLUSTER_ONLY" = true ]; then
        stop_kind_cluster
        exit 0
    fi

    if [ "$REGISTRY_ONLY" = true ]; then
        remove_registry
        exit 0
    fi

    # Handle full cleanup
    if [ "$FULL_CLEANUP" = true ]; then
        echo_warn "This will remove ALL containers, volumes, and the Kind cluster!"
        read -p "Are you sure you want to continue? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo_info "Cancelled. Exiting."
            exit 0
        fi

        echo_info "Performing full cleanup..."
        stop_docker_compose_with_volumes
        stop_kind_cluster_force
        remove_registry
        echo ""
        echo_success "Full cleanup complete! All resources have been removed."
        echo_info "To start fresh, run: ./scripts/setup-kind-cluster.sh && docker-compose up -d"
        exit 0
    fi

    # Default: stop-only mode
    echo_info "Stopping services (containers and data will be preserved)..."
    stop_docker_compose
    stop_registry
    echo ""
    echo_success "Services stopped. Data is preserved."
    echo_info "To restart, run: docker-compose up -d"
    echo_info "To remove everything, run: $0 --full-cleanup"
}

# Run main function
main "$@"

