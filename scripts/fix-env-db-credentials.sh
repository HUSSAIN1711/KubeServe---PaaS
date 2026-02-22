#!/bin/bash
#
# Fix database credentials in .env file to match docker-compose.yml
#

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$PROJECT_ROOT"

if [ ! -f .env ]; then
    echo "❌ .env file not found"
    exit 1
fi

echo "Fixing database credentials in .env file..."

# Backup original
cp .env .env.backup
echo "✅ Created backup: .env.backup"

# Update DATABASE_URL to use correct credentials
# macOS uses different sed syntax
if [[ "$OSTYPE" == "darwin"* ]]; then
    sed -i '' 's|postgresql+asyncpg://postgres:postgres@|postgresql+asyncpg://kubeserve:kubeserve_dev@|' .env
    sed -i '' 's|postgresql://postgres:postgres@|postgresql://kubeserve:kubeserve_dev@|' .env
else
    sed -i 's|postgresql+asyncpg://postgres:postgres@|postgresql+asyncpg://kubeserve:kubeserve_dev@|' .env
    sed -i 's|postgresql://postgres:postgres@|postgresql://kubeserve:kubeserve_dev@|' .env
fi

echo "✅ Updated DATABASE_URL in .env"
echo ""
echo "New DATABASE_URL:"
grep "^DATABASE_URL=" .env
echo ""
echo "You can now run migrations:"
echo "  source venv/bin/activate"
echo "  alembic upgrade head"


