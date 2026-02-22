#!/bin/bash
#
# Verify and fix .env file database credentials
#

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "Checking .env file..."

if [ ! -f .env ]; then
    echo "❌ .env file not found"
    echo "Creating .env file with correct credentials..."
    cat > .env << 'EOF'
# Database
# Note: User/password match docker-compose.yml postgres service
DATABASE_URL=postgresql+asyncpg://kubeserve:kubeserve_dev@localhost:5433/kubeserve

# Minio/S3
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET_NAME=kubeserve-models
MINIO_USE_SSL=false

# JWT
JWT_SECRET_KEY=your-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# Kubernetes
KUBECONFIG=
INGRESS_HOST=localhost
INGRESS_BASE_PATH=/api/v1/predict

# CORS
CORS_ORIGINS=["http://localhost:3000","http://localhost:3001"]
EOF
    echo "✅ Created .env file"
    exit 0
fi

# Check if DATABASE_URL exists
if ! grep -q "^DATABASE_URL=" .env; then
    echo "⚠️  DATABASE_URL not found in .env"
    echo "Adding DATABASE_URL..."
    # Add it at the top after any comments
    if grep -q "^# Database" .env; then
        sed -i.bak '/^# Database/a\
DATABASE_URL=postgresql+asyncpg://kubeserve:kubeserve_dev@localhost:5433/kubeserve
' .env 2>/dev/null || \
        sed -i '' '/^# Database/a\
DATABASE_URL=postgresql+asyncpg://kubeserve:kubeserve_dev@localhost:5433/kubeserve
' .env
        rm -f .env.bak
    else
        # Add at the beginning
        echo "DATABASE_URL=postgresql+asyncpg://kubeserve:kubeserve_dev@localhost:5433/kubeserve" > .env.tmp
        echo "" >> .env.tmp
        cat .env >> .env.tmp
        mv .env.tmp .env
    fi
    echo "✅ Added DATABASE_URL"
fi

# Check current DATABASE_URL
CURRENT_DB_URL=$(grep "^DATABASE_URL=" .env | head -1 | cut -d'=' -f2-)

echo "Current DATABASE_URL: $CURRENT_DB_URL"

# Check if it has correct credentials
CORRECT_URL="postgresql+asyncpg://kubeserve:kubeserve_dev@localhost:5432/kubeserve"

if [[ "$CURRENT_DB_URL" != "$CORRECT_URL" ]]; then
    echo "⚠️  DATABASE_URL has incorrect credentials"
    echo "Updating to correct credentials..."
    
    # Backup
    cp .env .env.backup
    echo "✅ Created backup: .env.backup"
    
    # Update DATABASE_URL
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i '' "s|^DATABASE_URL=.*|DATABASE_URL=$CORRECT_URL|" .env
    else
        sed -i "s|^DATABASE_URL=.*|DATABASE_URL=$CORRECT_URL|" .env
    fi
    
    echo "✅ Updated DATABASE_URL"
    echo ""
    echo "New DATABASE_URL:"
    grep "^DATABASE_URL=" .env
else
    echo "✅ DATABASE_URL is correct"
fi

echo ""
echo "Verifying PostgreSQL connection..."
# Try to connect (this will fail if user doesn't exist, but that's okay - we just want to see the error)
if command -v psql &> /dev/null; then
    PGPASSWORD=kubeserve_dev psql -h localhost -U kubeserve -d kubeserve -c "SELECT 1;" &>/dev/null
    if [ $? -eq 0 ]; then
        echo "✅ Can connect to PostgreSQL with these credentials"
    else
        echo "⚠️  Cannot connect to PostgreSQL"
        echo "   Make sure PostgreSQL is running and the user 'kubeserve' exists"
        echo "   Run: ./scripts/reset-postgres.sh"
    fi
else
    echo "ℹ️  psql not found, skipping connection test"
fi

