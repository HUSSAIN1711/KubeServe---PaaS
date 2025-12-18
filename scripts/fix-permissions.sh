#!/bin/bash
#
# Fix script permissions for KubeServe scripts
#

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Making all scripts executable..."

chmod +x "$SCRIPT_DIR"/*.sh

echo "✅ All scripts are now executable"
echo ""
echo "You can now run:"
echo "  ./scripts/start-backend.sh"
echo "  ./scripts/stop-backend.sh"

