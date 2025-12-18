#!/bin/bash
#
# Run Locust load tests for KubeServe
# Tests baseline (single pod) and scalability (HPA enabled) scenarios
#

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Configuration
DEPLOYMENT_URL="${DEPLOYMENT_URL:-http://localhost:30080/api/v1/predict/1}"
LOCUST_HOST="${LOCUST_HOST:-$DEPLOYMENT_URL}"
LOCUST_USERS="${LOCUST_USERS:-10}"
LOCUST_SPAWN_RATE="${LOCUST_SPAWN_RATE:-2}"
LOCUST_RUN_TIME="${LOCUST_RUN_TIME:-5m}"

echo "🧪 KubeServe Load Testing with Locust"
echo "======================================"
echo "Target URL: $LOCUST_HOST"
echo "Users: $LOCUST_USERS"
echo "Spawn Rate: $LOCUST_SPAWN_RATE users/second"
echo "Run Time: $LOCUST_RUN_TIME"
echo ""

# Check if locust is installed
if ! command -v locust &> /dev/null; then
    echo "❌ Locust is not installed. Installing..."
    pip install locust
fi

# Check if deployment is accessible
echo "🔍 Checking deployment health..."
HEALTH_URL=$(echo "$LOCUST_HOST" | sed 's|/predict.*|/health|')
if curl -s -f "$HEALTH_URL" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Deployment is accessible${NC}"
else
    echo -e "${YELLOW}⚠️  Warning: Deployment might not be accessible at $HEALTH_URL${NC}"
    echo "   Continuing anyway..."
fi

echo ""
echo "🚀 Starting Locust..."
echo "   Open http://localhost:8089 in your browser to view the web UI"
echo "   Or use --headless mode for automated testing"
echo ""

# Run Locust
locust \
    --host="$LOCUST_HOST" \
    --users="$LOCUST_USERS" \
    --spawn-rate="$LOCUST_SPAWN_RATE" \
    --run-time="$LOCUST_RUN_TIME" \
    --headless \
    --html=load_test_report.html \
    --csv=load_test_results \
    -f locustfile.py

echo ""
echo -e "${GREEN}✅ Load test completed!${NC}"
echo "   Report saved to: load_test_report.html"
echo "   CSV results saved to: load_test_results_*.csv"
echo ""
echo "📊 To verify HPA scaling:"
echo "   kubectl get hpa -n user-1"
echo "   kubectl get pods -n user-1 -w"
echo ""

