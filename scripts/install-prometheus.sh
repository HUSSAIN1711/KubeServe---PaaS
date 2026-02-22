#!/bin/bash
#
# Install Prometheus and Grafana for KubeServe
# This script installs the kube-prometheus-stack using Helm
#

set -e

echo "🚀 Installing Prometheus and Grafana for KubeServe..."

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

# Add the prometheus-community Helm repository
echo "📦 Adding prometheus-community Helm repository..."
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

# Check if kube-prometheus-stack is already installed
if helm list -n monitoring | grep -q kube-prometheus-stack; then
    echo "⚠️  kube-prometheus-stack is already installed. Upgrading..."
    helm upgrade kube-prometheus-stack prometheus-community/kube-prometheus-stack \
        --namespace monitoring \
        --create-namespace \
        --set prometheus.prometheusSpec.retention=30d \
        --set grafana.adminPassword=admin \
        --set prometheus.service.type=NodePort \
        --set prometheus.service.nodePort=30090 \
        --set grafana.service.type=NodePort \
        --set grafana.service.nodePort=30091
else
    echo "📥 Installing kube-prometheus-stack..."
    helm install kube-prometheus-stack prometheus-community/kube-prometheus-stack \
        --namespace monitoring \
        --create-namespace \
        --set prometheus.prometheusSpec.retention=30d \
        --set grafana.adminPassword=admin \
        --set prometheus.service.type=NodePort \
        --set prometheus.service.nodePort=30090 \
        --set grafana.service.type=NodePort \
        --set grafana.service.nodePort=30091
fi

# Wait for Prometheus to be ready
echo "⏳ Waiting for Prometheus to be ready..."
kubectl wait --namespace monitoring \
    --for=condition=ready pod \
    --selector=app.kubernetes.io/name=prometheus \
    --timeout=300s || echo "⚠️  Prometheus pods may still be starting..."

# Wait for Grafana to be ready
echo "⏳ Waiting for Grafana to be ready..."
kubectl wait --namespace monitoring \
    --for=condition=ready pod \
    --selector=app.kubernetes.io/name=grafana \
    --timeout=300s || echo "⚠️  Grafana pods may still be starting..."

# Get service details
echo ""
echo "✅ Prometheus and Grafana installed successfully!"
echo ""
echo "📋 Service Details:"
kubectl get svc -n monitoring

echo ""
echo "🌐 Access your services:"
echo "   - Prometheus UI:  http://localhost:30090"
echo "   - Grafana UI:     http://localhost:30091"
echo "   - Grafana Login:  admin / admin"
echo ""
echo "💡 For local development with Kind, you may need to:"
echo "   kubectl port-forward -n monitoring svc/kube-prometheus-stack-prometheus 30090:9090"
echo "   kubectl port-forward -n monitoring svc/kube-prometheus-stack-grafana 30091:80"
echo ""
echo "📊 ServiceMonitors will automatically discover services with the correct labels."
echo ""


