#!/bin/bash
# KubeServe Inference Server Entrypoint
# Smart dependency installation: only installs packages not in base image

set -e  # Exit on error

MODEL_DIR="/model"
REQUIREMENTS_FILE="${MODEL_DIR}/requirements.txt"
BASE_PACKAGES_FILE="/tmp/base-packages.txt"

echo "=== KubeServe Inference Server Starting ==="

# Function to get installed packages
get_installed_packages() {
    pip list --format=freeze | cut -d'=' -f1 | tr '[:upper:]' '[:lower:]' | sort
}

# Function to get required packages from requirements.txt
get_required_packages() {
    if [ ! -f "$REQUIREMENTS_FILE" ]; then
        echo ""
        return
    fi
    grep -v "^#" "$REQUIREMENTS_FILE" | grep -v "^$" | cut -d'=' -f1 | cut -d'>' -f1 | cut -d'<' -f1 | cut -d'[' -f1 | tr '[:upper:]' '[:lower:]' | sed 's/^[[:space:]]*//;s/[[:space:]]*$//' | sort
}

# Check if requirements.txt exists
if [ -f "$REQUIREMENTS_FILE" ]; then
    echo "Found requirements.txt, checking for missing packages..."
    
    # Get lists of installed and required packages
    INSTALLED=$(get_installed_packages)
    REQUIRED=$(get_required_packages)
    
    # Save installed packages to file for comparison
    echo "$INSTALLED" > "$BASE_PACKAGES_FILE"
    
    # Find missing packages
    MISSING=$(comm -23 <(echo "$REQUIRED") <(echo "$INSTALLED") || true)
    
    if [ -n "$MISSING" ]; then
        echo "Installing missing packages:"
        echo "$MISSING" | while read -r package; do
            if [ -n "$package" ]; then
                echo "  - $package"
            fi
        done
        
        # Install missing packages
        pip install --no-cache-dir -r "$REQUIREMENTS_FILE" || {
            echo "WARNING: Some packages failed to install. Continuing anyway..."
        }
    else
        echo "All required packages are already installed in base image!"
        echo "Skipping pip install (saves ~40 seconds)"
    fi
else
    echo "No requirements.txt found. Using base image packages only."
fi

# Verify model file exists
if [ ! -f "${MODEL_DIR}/model.joblib" ]; then
    echo "WARNING: model.joblib not found in ${MODEL_DIR}"
    echo "The model should be downloaded by an init container before this container starts."
fi

echo "=== Starting Uvicorn Server ==="

# Start the FastAPI application
exec uvicorn main:app --host 0.0.0.0 --port 80

