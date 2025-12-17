#!/bin/bash

# Phase 0 Verification Script
# Checks if all required infrastructure components are running

echo "🔍 Verifying Phase 0 Setup..."
echo ""

ERRORS=0

# Check kubectl
echo -n "Checking kubectl... "
if command -v kubectl &> /dev/null; then
    if kubectl cluster-info &> /dev/null; then
        echo "✅ kubectl is installed and connected to cluster"
        kubectl get nodes
    else
        echo "❌ kubectl is installed but not connected to a cluster"
        ERRORS=$((ERRORS + 1))
    fi
else
    echo "❌ kubectl is not installed"
    ERRORS=$((ERRORS + 1))
fi
echo ""

# Check helm
echo -n "Checking helm... "
if command -v helm &> /dev/null; then
    echo "✅ helm is installed"
    helm version --short
else
    echo "❌ helm is not installed"
    ERRORS=$((ERRORS + 1))
fi
echo ""

# Check docker
echo -n "Checking docker... "
if command -v docker &> /dev/null; then
    if docker ps &> /dev/null; then
        echo "✅ docker is installed and running"
    else
        echo "❌ docker is installed but not running"
        ERRORS=$((ERRORS + 1))
    fi
else
    echo "❌ docker is not installed"
    ERRORS=$((ERRORS + 1))
fi
echo ""

# Check Minio
echo -n "Checking Minio... "
if docker ps | grep -q kubeserve-minio; then
    # Check MinIO health endpoint from host (Minio container doesn't have Python)
    if curl -s -f http://localhost:9000/minio/health/live &> /dev/null; then
        echo "✅ Minio is running on port 9000"
    else
        echo "⚠️  Minio container exists but health check failed"
        ERRORS=$((ERRORS + 1))
    fi
else
    echo "❌ Minio container is not running"
    ERRORS=$((ERRORS + 1))
fi
echo ""

# Check Docker network
echo -n "Checking Docker network... "
if docker network ls | grep -q kubeserve-network; then
    echo "✅ kubeserve-network exists"
else
    echo "⚠️  kubeserve-network not found (containers might not be on custom network)"
fi
echo ""

# Check PostgreSQL
echo -n "Checking PostgreSQL... "
if docker ps | grep -q kubeserve-postgres; then
    if docker exec kubeserve-postgres pg_isready -U kubeserve &> /dev/null; then
        echo "✅ PostgreSQL is running on port 5432"
    else
        echo "⚠️  PostgreSQL container exists but not ready"
        ERRORS=$((ERRORS + 1))
    fi
else
    echo "❌ PostgreSQL container is not running"
    ERRORS=$((ERRORS + 1))
fi
echo ""

# Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ $ERRORS -eq 0 ]; then
    echo "✅ Phase 0 Setup Complete! All checks passed."
    exit 0
else
    echo "❌ Phase 0 Setup Incomplete. $ERRORS issue(s) found."
    echo "Please review phase0-setup.md for installation instructions."
    exit 1
fi

