#!/bin/bash
#
# Test database connection using the .env file
#

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# Load .env file
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
else
    echo "❌ .env file not found"
    exit 1
fi

if [ -z "$DATABASE_URL" ]; then
    echo "❌ DATABASE_URL not set in .env file"
    exit 1
fi

echo "Testing database connection..."
echo "DATABASE_URL: $DATABASE_URL"
echo ""

# Check if PostgreSQL container is running
if ! docker ps | grep -q kubeserve-postgres; then
    echo "❌ PostgreSQL container is not running"
    echo "   Start it with: docker-compose up -d postgres"
    exit 1
fi

# Check if venv exists
VENV_PYTHON="$PROJECT_ROOT/venv/bin/python"
if [ ! -f "$VENV_PYTHON" ]; then
    echo "❌ Virtual environment not found"
    echo "   Create it with: python3 -m venv venv"
    exit 1
fi

# Test connection using Python
"$VENV_PYTHON" -c "
import asyncio
import asyncpg
import os
from urllib.parse import urlparse

# Parse DATABASE_URL
db_url = os.getenv('DATABASE_URL', '')
parsed = urlparse(db_url.replace('postgresql+asyncpg://', 'postgresql://'))
user = parsed.username
password = parsed.password
host = parsed.hostname
port = parsed.port or 5433
database = parsed.path.lstrip('/')

print(f'Connecting to: {user}@{host}:{port}/{database}')

async def test_connection():
    try:
        conn = await asyncpg.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database
        )
        result = await conn.fetchval('SELECT version()')
        print(f'✅ Connection successful!')
        print(f'   PostgreSQL version: {result.split()[0]} {result.split()[1]}')
        
        # Check if user exists
        user_exists = await conn.fetchval(
            \"SELECT 1 FROM pg_roles WHERE rolname=\$1\",
            user
        )
        if user_exists:
            print(f'✅ User \"{user}\" exists')
        else:
            print(f'❌ User \"{user}\" does not exist')
        
        # Check if database exists
        db_exists = await conn.fetchval(
            \"SELECT 1 FROM pg_database WHERE datname=\$1\",
            database
        )
        if db_exists:
            print(f'✅ Database \"{database}\" exists')
        else:
            print(f'❌ Database \"{database}\" does not exist')
        
        await conn.close()
        return True
    except asyncpg.exceptions.InvalidAuthorizationSpecificationError as e:
        print(f'❌ Authentication failed: {e}')
        print(f'   User: {user}, Database: {database}')
        print('')
        print('   Possible fixes:')
        print('   1. Run: ./scripts/reset-postgres.sh')
        print('   2. Check docker-compose.yml has correct POSTGRES_USER and POSTGRES_PASSWORD')
        return False
    except asyncpg.exceptions.InvalidCatalogNameError as e:
        print(f'❌ Database does not exist: {e}')
        print(f'   Database: {database}')
        print('')
        print('   Possible fixes:')
        print('   1. Run: ./scripts/reset-postgres.sh')
        print('   2. Check docker-compose.yml has POSTGRES_DB set')
        return False
    except Exception as e:
        print(f'❌ Connection failed: {type(e).__name__}: {e}')
        return False

result = asyncio.run(test_connection())
exit(0 if result else 1)
"

