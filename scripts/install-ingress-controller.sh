#!/bin/bash
#
# Install NGINX Ingress Controller for KubeServe
# This script installs the NGINX Ingress Controller using Helm
#

set -e

echo "🚀 Installing NGINX Ingress Controller for KubeServe..."

# Check if helm is installed
if ! command -v helm &> /dev/null; then
    echo "❌ Error: helm is not installed. Please install it first:"
    echo "   brew install helm  # macOS"
    echo "   or visit: https://helm.sh/docs/intro/install/"
    exit 1
fi

# Check if kubectl is installed
if ! command -v kubectl &> /dev/null; then
    echo "❌ Error: kubectl is not installed. Please install it first."
    exit 1
fi

# Check if we can connect to the cluster
if ! kubectl cluster-info &> /dev/null; then
    echo "❌ Error: Cannot connect to Kubernetes cluster."
    echo "   Make sure your cluster is running and kubeconfig is configured."
    exit 1
fi

# Add the ingress-nginx Helm repository
echo "📦 Adding ingress-nginx Helm repository..."
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo update

# Check if ingress-nginx is already installed
if helm list -n ingress-nginx | grep -q ingress-nginx; then
    echo "⚠️  ingress-nginx is already installed. Upgrading..."
    helm upgrade ingress-nginx ingress-nginx/ingress-nginx \
        --namespace ingress-nginx \
        --create-namespace \
        --set controller.service.type=NodePort \
        --set controller.service.nodePorts.http=30080 \
        --set controller.service.nodePorts.https=30443
else
    echo "📥 Installing ingress-nginx..."
    helm install ingress-nginx ingress-nginx/ingress-nginx \
        --namespace ingress-nginx \
        --create-namespace \
        --set controller.service.type=NodePort \
        --set controller.service.nodePorts.http=30080 \
        --set controller.service.nodePorts.https=30443
fi

# Wait for ingress controller to be ready
echo "⏳ Waiting for ingress controller to be ready..."
kubectl wait --namespace ingress-nginx \
    --for=condition=ready pod \
    --selector=app.kubernetes.io/component=controller \
    --timeout=300s

# Get the ingress controller service details
echo ""
echo "✅ NGINX Ingress Controller installed successfully!"
echo ""
echo "📋 Ingress Controller Details:"
kubectl get svc -n ingress-nginx ingress-nginx-controller

echo ""
echo "🌐 Access your services via:"
echo "   - HTTP:  http://localhost:30080"
echo "   - HTTPS: https://localhost:30443"
echo ""
echo "💡 For local development with Kind, you may need to:"
echo "   kubectl port-forward -n ingress-nginx svc/ingress-nginx-controller 30080:80 30443:443"
echo ""

