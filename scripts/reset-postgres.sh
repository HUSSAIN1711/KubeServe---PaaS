#!/bin/bash
#
# Reset PostgreSQL container and volume to fix user/credential issues
#

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$PROJECT_ROOT"

echo "⚠️  This will DELETE all PostgreSQL data!"
read -p "Are you sure you want to continue? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 0
fi

echo "Stopping PostgreSQL container..."
docker-compose stop postgres

echo "Removing PostgreSQL container..."
docker-compose rm -f postgres

echo "Removing PostgreSQL volume..."
docker volume rm kubeserve_postgres_data 2>/dev/null || echo "Volume already removed or doesn't exist"

echo "Starting PostgreSQL with fresh volume..."
docker-compose up -d postgres

echo "Waiting for PostgreSQL to initialize..."
echo "This may take 15-30 seconds on first run..."

# Wait for PostgreSQL to be ready
MAX_WAIT=30
WAITED=0
while [ $WAITED -lt $MAX_WAIT ]; do
    if docker exec kubeserve-postgres pg_isready -U kubeserve > /dev/null 2>&1; then
        echo "✅ PostgreSQL is ready"
        break
    fi
    echo "  Waiting... ($WAITED/$MAX_WAIT seconds)"
    sleep 2
    WAITED=$((WAITED + 2))
done

if [ $WAITED -ge $MAX_WAIT ]; then
    echo "⚠️  PostgreSQL took longer than expected to start"
    echo "Checking container logs..."
    docker logs kubeserve-postgres --tail 20
fi

# Give it a bit more time for user creation
sleep 5

echo "Verifying PostgreSQL user 'kubeserve' exists..."
# When POSTGRES_USER is set, that user becomes the superuser (not 'postgres')
# Try connecting as kubeserve user first (if it works, user exists)
if docker exec kubeserve-postgres psql -U kubeserve -d kubeserve -c "SELECT 1" > /dev/null 2>&1; then
    echo "✅ PostgreSQL user 'kubeserve' exists and can connect to database 'kubeserve'"
else
    # Try connecting to postgres database (default database) as kubeserve
    if docker exec kubeserve-postgres psql -U kubeserve -d postgres -c "SELECT 1" > /dev/null 2>&1; then
        echo "✅ PostgreSQL user 'kubeserve' exists"
        # Check if kubeserve database exists
        DB_EXISTS=$(docker exec kubeserve-postgres psql -U kubeserve -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='kubeserve'" 2>/dev/null | tr -d '[:space:]')
        if [ "$DB_EXISTS" = "1" ]; then
            echo "✅ PostgreSQL database 'kubeserve' exists"
        else
            echo "⚠️  Database 'kubeserve' does not exist, creating it..."
            docker exec kubeserve-postgres psql -U kubeserve -d postgres -c "CREATE DATABASE kubeserve;" 2>/dev/null || true
            echo "✅ Database 'kubeserve' created"
        fi
    else
        echo "❌ PostgreSQL user 'kubeserve' does not exist or cannot connect"
        echo "Checking PostgreSQL logs..."
        docker logs kubeserve-postgres --tail 30
        echo ""
        echo "The user should be created automatically by docker-compose."
        echo "If this persists, check docker-compose.yml has:"
        echo "  POSTGRES_USER: kubeserve"
        echo "  POSTGRES_PASSWORD: kubeserve_dev"
        echo "  POSTGRES_DB: kubeserve"
        echo ""
        echo "You can try connecting manually:"
        echo "  docker exec -it kubeserve-postgres psql -U kubeserve -d postgres"
        exit 1
    fi
fi

echo ""
echo "✅ PostgreSQL reset complete!"
echo "You can now run migrations:"
echo "  source venv/bin/activate"
echo "  alembic upgrade head"

