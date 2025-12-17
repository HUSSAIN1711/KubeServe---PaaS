#!/bin/bash

# Phase 1.1 Verification Script
# Checks if the project is ready for Phase 1.2 development

echo "🔍 Verifying Phase 1.1 Setup..."
echo ""

ERRORS=0
WARNINGS=0

# Check Python version
echo -n "Checking Python version... "
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    echo "✅ Python $PYTHON_VERSION installed"
    
    # Check if version is 3.10 or higher
    MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
    MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)
    if [ "$MAJOR" -lt 3 ] || ([ "$MAJOR" -eq 3 ] && [ "$MINOR" -lt 10 ]); then
        echo "⚠️  Python 3.10+ required, found $PYTHON_VERSION"
        WARNINGS=$((WARNINGS + 1))
    fi
else
    echo "❌ Python 3 not found"
    ERRORS=$((ERRORS + 1))
fi
echo ""

# Check virtual environment
echo -n "Checking virtual environment... "
if [ -d "venv" ] || [ -d ".venv" ]; then
    echo "✅ Virtual environment found"
else
    echo "⚠️  Virtual environment not found (recommended but not required)"
    WARNINGS=$((WARNINGS + 1))
fi
echo ""

# Check if dependencies are installed
echo -n "Checking Python dependencies... "
if python3 -c "import fastapi" &> /dev/null 2>&1; then
    echo "✅ Dependencies appear to be installed"
else
    echo "❌ Dependencies not installed"
    echo "   Run: pip install -r requirements.txt"
    ERRORS=$((ERRORS + 1))
fi
echo ""

# Check .env file
echo -n "Checking .env file... "
if [ -f ".env" ]; then
    echo "✅ .env file exists"
    
    # Check if required variables are set
    if grep -q "DATABASE_URL=" .env && grep -q "MINIO_ENDPOINT=" .env && grep -q "JWT_SECRET_KEY=" .env; then
        echo "✅ Required environment variables appear to be set"
    else
        echo "⚠️  Some required environment variables may be missing"
        WARNINGS=$((WARNINGS + 1))
    fi
else
    echo "❌ .env file not found"
    echo "   Copy .env.example to .env and configure it"
    ERRORS=$((ERRORS + 1))
fi
echo ""

# Check Docker services
echo -n "Checking Docker services... "
if docker ps | grep -q kubeserve-postgres && docker ps | grep -q kubeserve-minio; then
    echo "✅ PostgreSQL and Minio containers are running"
else
    echo "⚠️  Docker services not running"
    echo "   Run: docker-compose up -d"
    WARNINGS=$((WARNINGS + 1))
fi
echo ""

# Check database connectivity (if services are running)
if docker ps | grep -q kubeserve-postgres; then
    echo -n "Checking database connectivity... "
    if docker exec kubeserve-postgres pg_isready -U kubeserve &> /dev/null; then
        echo "✅ Database is accessible"
    else
        echo "⚠️  Database container exists but not ready"
        WARNINGS=$((WARNINGS + 1))
    fi
    echo ""
fi

# Check project structure
echo -n "Checking project structure... "
if [ -d "app" ] && [ -d "alembic" ] && [ -f "app/main.py" ] && [ -f "app/config.py" ] && [ -f "app/database.py" ]; then
    echo "✅ Project structure is correct"
else
    echo "❌ Project structure incomplete"
    ERRORS=$((ERRORS + 1))
fi
echo ""

# Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo "✅ Phase 1.1 Setup Complete! Ready for Phase 1.2."
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo "⚠️  Phase 1.1 Setup Mostly Complete. $WARNINGS warning(s) found."
    echo "You can proceed, but consider addressing the warnings above."
    exit 0
else
    echo "❌ Phase 1.1 Setup Incomplete. $ERRORS error(s) and $WARNINGS warning(s) found."
    echo "Please fix the errors above before proceeding to Phase 1.2."
    exit 1
fi

