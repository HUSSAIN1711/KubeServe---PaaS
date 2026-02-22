#!/bin/bash
#
# Integration Test Script for KubeServe
# Tests the full workflow: upload -> deploy -> predict -> delete
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
API_BASE_URL="${API_BASE_URL:-http://localhost:8000}"
TEST_USER_EMAIL="${TEST_USER_EMAIL:-integration-test@example.com}"
TEST_USER_PASSWORD="${TEST_USER_PASSWORD:-testpass123}"
MODEL_NAME="${MODEL_NAME:-integration-test-model}"
VERSION_TAG="${VERSION_TAG:-v1.0.0}"

echo "🧪 Starting KubeServe Integration Test"
echo "========================================"
echo "API Base URL: $API_BASE_URL"
echo "Test User: $TEST_USER_EMAIL"
echo ""

# Pre-flight: MinIO must be reachable at localhost:9000 for uploads. If you use in-cluster MinIO,
# run: kubectl port-forward svc/minio 9000:9000 -n default &
# so uploads and deploy use the same MinIO.
if ! curl -sf --connect-timeout 2 "http://localhost:9000/minio/health/live" >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  MinIO not reachable at localhost:9000. Uploads will fail.${NC}"
    echo "   If using in-cluster MinIO: kubectl port-forward svc/minio 9000:9000 -n default &"
    echo ""
fi

# Step 1: Register user
echo "📝 Step 1: Registering test user..."
REGISTER_RESPONSE=$(curl -s -X POST "$API_BASE_URL/api/v1/auth/register" \
    -H "Content-Type: application/json" \
    -d "{
        \"email\": \"$TEST_USER_EMAIL\",
        \"password\": \"$TEST_USER_PASSWORD\"
    }")

if echo "$REGISTER_RESPONSE" | grep -q "email"; then
    echo -e "${GREEN}✅ User registered successfully${NC}"
else
    # User might already exist, try to login
    echo -e "${YELLOW}⚠️  User might already exist, attempting login...${NC}"
fi

# Step 2: Login and get token
echo ""
echo "🔐 Step 2: Logging in..."
LOGIN_RESPONSE=$(curl -s -X POST "$API_BASE_URL/api/v1/auth/login" \
    -H "Content-Type: application/json" \
    -d "{
        \"email\": \"$TEST_USER_EMAIL\",
        \"password\": \"$TEST_USER_PASSWORD\"
    }")

TOKEN=$(echo "$LOGIN_RESPONSE" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
    echo -e "${RED}❌ Failed to get access token${NC}"
    echo "Response: $LOGIN_RESPONSE"
    exit 1
fi

echo -e "${GREEN}✅ Login successful${NC}"
AUTH_HEADER="Authorization: Bearer $TOKEN"

# Step 3: Create model
echo ""
echo "📦 Step 3: Creating model..."
MODEL_RESPONSE=$(curl -s -X POST "$API_BASE_URL/api/v1/models" \
    -H "Content-Type: application/json" \
    -H "$AUTH_HEADER" \
    -d "{
        \"name\": \"$MODEL_NAME\",
        \"type\": \"sklearn\"
    }")

MODEL_ID=$(echo "$MODEL_RESPONSE" | grep -o '"id":[0-9]*' | head -1 | cut -d':' -f2)

if [ -z "$MODEL_ID" ]; then
    echo -e "${RED}❌ Failed to create model${NC}"
    echo "Response: $MODEL_RESPONSE"
    exit 1
fi

echo -e "${GREEN}✅ Model created with ID: $MODEL_ID${NC}"

# Step 4: Create model version
echo ""
echo "🏷️  Step 4: Creating model version..."
VERSION_RESPONSE=$(curl -s -X POST "$API_BASE_URL/api/v1/models/$MODEL_ID/versions" \
    -H "Content-Type: application/json" \
    -H "$AUTH_HEADER" \
    -d "{
        \"version_tag\": \"$VERSION_TAG\",
        \"s3_path\": \"s3://kubeserve-models/user-1/$MODEL_NAME/$VERSION_TAG/model.joblib\"
    }")

VERSION_ID=$(echo "$VERSION_RESPONSE" | grep -o '"id":[0-9]*' | head -1 | cut -d':' -f2)

if [ -z "$VERSION_ID" ]; then
    echo -e "${RED}❌ Failed to create model version${NC}"
    echo "Response: $VERSION_RESPONSE"
    exit 1
fi

echo -e "${GREEN}✅ Model version created with ID: $VERSION_ID${NC}"

# Step 5: Upload model file
echo ""
echo "📤 Step 5: Uploading model file..."

# Create a simple test model file (scikit-learn)
TEMP_MODEL_FILE=$(mktemp)
python3 << 'EOF'
import joblib
from sklearn.linear_model import LogisticRegression
import numpy as np

# Create a simple model
X = np.array([[1, 2], [2, 3], [3, 4], [4, 5]])
y = np.array([0, 0, 1, 1])
model = LogisticRegression()
model.fit(X, y)

# Save model
joblib.dump(model, '/tmp/test_model.joblib')
print("Model created successfully")
EOF

if [ ! -f /tmp/test_model.joblib ]; then
    echo -e "${RED}❌ Failed to create test model${NC}"
    exit 1
fi

# Minimal requirements for the test model (joblib + scikit-learn)
cat > /tmp/test_requirements.txt << 'REQEOF'
joblib>=1.3.0
scikit-learn>=1.3.0
REQEOF

UPLOAD_RESPONSE=$(curl -s -X POST "$API_BASE_URL/api/v1/versions/$VERSION_ID/upload" \
    -H "$AUTH_HEADER" \
    -F "model_file=@/tmp/test_model.joblib" \
    -F "requirements_file=@/tmp/test_requirements.txt")

if echo "$UPLOAD_RESPONSE" | grep -q "s3_path"; then
    echo -e "${GREEN}✅ Model file uploaded successfully${NC}"
else
    echo -e "${RED}❌ Failed to upload model file${NC}"
    echo "Response: $UPLOAD_RESPONSE"
    exit 1
fi

# Step 6: Update version status to Ready
echo ""
echo "✅ Step 6: Updating version status to Ready..."
STATUS_RESPONSE=$(curl -s -X PATCH "$API_BASE_URL/api/v1/versions/$VERSION_ID/status?status=Ready" \
    -H "$AUTH_HEADER")

if echo "$STATUS_RESPONSE" | grep -q "Ready"; then
    echo -e "${GREEN}✅ Version status updated to Ready${NC}"
else
    echo -e "${YELLOW}⚠️  Status update response: $STATUS_RESPONSE${NC}"
fi

# Step 7: Deploy model
echo ""
echo "🚀 Step 7: Deploying model..."
DEPLOY_RESPONSE=$(curl -s -X POST "$API_BASE_URL/api/v1/versions/$VERSION_ID/deployments" \
    -H "Content-Type: application/json" \
    -H "$AUTH_HEADER" \
    -d "{
        \"replicas\": 1
    }")

DEPLOYMENT_ID=$(echo "$DEPLOY_RESPONSE" | grep -o '"id":[0-9]*' | head -1 | cut -d':' -f2)
DEPLOYMENT_URL=$(echo "$DEPLOY_RESPONSE" | grep -o '"url":"[^"]*' | cut -d'"' -f4)

if [ -z "$DEPLOYMENT_ID" ]; then
    echo -e "${RED}❌ Failed to deploy model${NC}"
    echo "Response: $DEPLOY_RESPONSE"
    exit 1
fi

echo -e "${GREEN}✅ Model deployed with ID: $DEPLOYMENT_ID${NC}"
echo "   Deployment URL: $DEPLOYMENT_URL"

# Wait for deployment to be ready
echo ""
echo "⏳ Waiting for deployment to be ready (up to 90 seconds)..."
MAX_WAIT=90
WAITED=0
while [ $WAITED -lt $MAX_WAIT ]; do
    sleep 5
    WAITED=$((WAITED + 5))
    
    # Check deployment health
    if [ -n "$DEPLOYMENT_URL" ]; then
        HEALTH_CHECK=$(curl -s -o /dev/null -w "%{http_code}" "$DEPLOYMENT_URL/health" || echo "000")
        if [ "$HEALTH_CHECK" = "200" ]; then
            echo -e "${GREEN}✅ Deployment is ready!${NC}"
            break
        fi
    fi
    
    echo "   Still waiting... (${WAITED}s/${MAX_WAIT}s)"
done

if [ $WAITED -ge $MAX_WAIT ]; then
    echo -e "${YELLOW}⚠️  Deployment might not be ready yet, continuing anyway...${NC}"
fi

# Step 8: Make predictions (retry a few times in case pod just became ready)
echo ""
echo "🔮 Step 8: Making predictions..."
if [ -n "$DEPLOYMENT_URL" ]; then
    PREDICT_OK=false
    for attempt in 1 2 3; do
        PREDICT_RESPONSE=$(curl -s -X POST "$DEPLOYMENT_URL/predict" \
            -H "Content-Type: application/json" \
            -d '{
                "data": [[1.0, 2.0], [2.0, 3.0]]
            }')
        if echo "$PREDICT_RESPONSE" | grep -q "predictions"; then
            echo -e "${GREEN}✅ Predictions successful!${NC}"
            echo "   Response: $PREDICT_RESPONSE"
            PREDICT_OK=true
            break
        fi
        if [ $attempt -lt 3 ]; then
            echo "   Attempt $attempt failed, retrying in 15s..."
            sleep 15
        fi
    done
    if [ "$PREDICT_OK" = false ]; then
        echo -e "${RED}❌ Failed to make predictions${NC}"
        echo "   Response: $PREDICT_RESPONSE"
        if echo "$PREDICT_RESPONSE" | grep -q "503\|Service Temporarily Unavailable"; then
            echo ""
            echo -e "${YELLOW}💡 503 = no ready inference pod. Run these (during the test or right after Step 7):${NC}"
            echo "   kubectl get namespaces | grep user-"
            echo "   kubectl get pods -A"
            echo "   kubectl logs <pod> -n user-X -c download-model   # why model download failed"
            echo "   If using in-cluster MinIO: kubectl port-forward svc/minio 9000:9000 -n default &"
            echo "   Restart backend; port-forward Ingress: 30080:80"
        fi
        exit 1
    fi
else
    echo -e "${YELLOW}⚠️  Skipping predictions (no deployment URL)${NC}"
fi

# Step 9: Delete deployment
echo ""
echo "🗑️  Step 9: Deleting deployment..."
DELETE_DEPLOYMENT_RESPONSE=$(curl -s -X DELETE "$API_BASE_URL/api/v1/deployments/$DEPLOYMENT_ID" \
    -H "$AUTH_HEADER" \
    -w "\n%{http_code}")

HTTP_CODE=$(echo "$DELETE_DEPLOYMENT_RESPONSE" | tail -1)

if [ "$HTTP_CODE" = "204" ] || [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✅ Deployment deleted successfully${NC}"
else
    echo -e "${YELLOW}⚠️  Unexpected HTTP code: $HTTP_CODE${NC}"
fi

# Step 10: Cleanup - Delete model
echo ""
echo "🧹 Step 10: Cleaning up model..."
DELETE_MODEL_RESPONSE=$(curl -s -X DELETE "$API_BASE_URL/api/v1/models/$MODEL_ID" \
    -H "$AUTH_HEADER" \
    -w "\n%{http_code}")

HTTP_CODE=$(echo "$DELETE_MODEL_RESPONSE" | tail -1)

if [ "$HTTP_CODE" = "204" ] || [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✅ Model deleted successfully${NC}"
else
    echo -e "${YELLOW}⚠️  Unexpected HTTP code: $HTTP_CODE${NC}"
fi

# Cleanup temp file
rm -f /tmp/test_model.joblib /tmp/test_requirements.txt

echo ""
echo "========================================"
echo -e "${GREEN}✅ Integration test completed successfully!${NC}"
echo ""


