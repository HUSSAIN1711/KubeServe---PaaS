#!/bin/bash
#
# KubeServe Backend Shutdown Script
# Stops all infrastructure and services
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     KubeServe Backend Shutdown Script                     ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

cd "$PROJECT_ROOT"

# Stop Docker services
echo -e "${YELLOW}Stopping Docker services...${NC}"
docker-compose down
echo -e "${GREEN}✅ Docker services stopped${NC}"
echo ""

# Optionally remove Kind cluster
read -p "Do you want to remove the Kind cluster? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Removing Kind cluster...${NC}"
    kind delete cluster --name kubeserve 2>/dev/null || echo "Cluster already removed"
    echo -e "${GREEN}✅ Kind cluster removed${NC}"
else
    echo "Kind cluster kept running"
fi

echo ""
echo -e "${GREEN}✅ Shutdown complete!${NC}"
echo ""
echo "To start everything again, run:"
echo "  ./scripts/start-backend.sh"

