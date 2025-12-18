#!/bin/bash
#
# Import Grafana dashboards for KubeServe
# This script imports dashboard JSON files into Grafana
#

set -e

echo "📊 Importing KubeServe Grafana dashboards..."

# Check if kubectl is installed
if ! command -v kubectl &> /dev/null; then
    echo "❌ Error: kubectl is not installed. Please install it first."
    exit 1
fi

# Check if jq is installed
if ! command -v jq &> /dev/null; then
    echo "❌ Error: jq is not installed. Please install it first:"
    echo "   brew install jq  # macOS"
    echo "   or visit: https://stedolan.github.io/jq/download/"
    exit 1
fi

# Check if curl is installed
if ! command -v curl &> /dev/null; then
    echo "❌ Error: curl is not installed. Please install it first."
    exit 1
fi

# Check if we can connect to the cluster
if ! kubectl cluster-info &> /dev/null; then
    echo "❌ Error: Cannot connect to Kubernetes cluster."
    echo "   Make sure your cluster is running and kubeconfig is configured."
    exit 1
fi

# Check if Grafana is running
if ! kubectl get pods -n monitoring -l app.kubernetes.io/name=grafana &> /dev/null; then
    echo "❌ Error: Grafana is not running in the monitoring namespace."
    echo "   Please install Prometheus/Grafana first: ./scripts/install-prometheus.sh"
    exit 1
fi

# Get Grafana admin password
GRAFANA_PASSWORD=$(kubectl get secret -n monitoring kube-prometheus-stack-grafana -o jsonpath="{.data.admin-password}" | base64 -d)

# Port forward Grafana
echo "🔌 Setting up port forwarding to Grafana..."
kubectl port-forward -n monitoring svc/kube-prometheus-stack-grafana 30091:80 &
PORT_FORWARD_PID=$!

# Wait for port forward to be ready
sleep 3

# Function to import dashboard
import_dashboard() {
    local dashboard_file=$1
    local dashboard_name=$(basename "$dashboard_file" .json)
    
    echo "📥 Importing $dashboard_name..."
    
    # Extract dashboard JSON (Grafana API expects the dashboard object, not the wrapper)
    DASHBOARD_JSON=$(cat "$dashboard_file" | jq '.dashboard')
    
    # Import dashboard via Grafana API
    RESPONSE=$(curl -s -X POST \
        -H "Content-Type: application/json" \
        -H "Accept: application/json" \
        -u "admin:${GRAFANA_PASSWORD}" \
        -d "{\"dashboard\": ${DASHBOARD_JSON}, \"overwrite\": true}" \
        http://localhost:30091/api/dashboards/db)
    
    # Check if import was successful
    if echo "$RESPONSE" | jq -e '.status == "success"' > /dev/null 2>&1; then
        echo "✅ Successfully imported $dashboard_name"
        DASHBOARD_URL=$(echo "$RESPONSE" | jq -r '.url')
        echo "   URL: http://localhost:30091${DASHBOARD_URL}"
    else
        echo "⚠️  Warning: Failed to import $dashboard_name"
        echo "   Response: $RESPONSE"
    fi
}

# Import all dashboards
DASHBOARD_DIR="grafana/dashboards"
if [ ! -d "$DASHBOARD_DIR" ]; then
    echo "❌ Error: Dashboard directory not found: $DASHBOARD_DIR"
    kill $PORT_FORWARD_PID 2>/dev/null || true
    exit 1
fi

for dashboard_file in "$DASHBOARD_DIR"/*.json; do
    if [ -f "$dashboard_file" ]; then
        import_dashboard "$dashboard_file"
    fi
done

# Cleanup
echo ""
echo "🧹 Cleaning up..."
kill $PORT_FORWARD_PID 2>/dev/null || true

echo ""
echo "✅ Dashboard import complete!"
echo ""
echo "🌐 Access Grafana at: http://localhost:30091"
echo "   Login: admin / ${GRAFANA_PASSWORD}"
echo ""
echo "💡 To keep port forwarding active, run:"
echo "   kubectl port-forward -n monitoring svc/kube-prometheus-stack-grafana 30091:80"
echo ""

