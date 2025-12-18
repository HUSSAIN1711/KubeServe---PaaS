#!/bin/bash
# Build script for KubeServe base inference image

set -e

IMAGE_NAME="kubeserve-base"
IMAGE_TAG="${1:-latest}"
REGISTRY="${2:-localhost:5001}"

echo "=== Building KubeServe Base Inference Image ==="
echo "Image: ${IMAGE_NAME}:${IMAGE_TAG}"
echo "Registry: ${REGISTRY}"

# Build the image
docker build -t "${IMAGE_NAME}:${IMAGE_TAG}" .

# Tag for local registry
FULL_IMAGE_NAME="${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"
docker tag "${IMAGE_NAME}:${IMAGE_TAG}" "${FULL_IMAGE_NAME}"

echo ""
echo "=== Build Complete ==="
echo "Image built: ${IMAGE_NAME}:${IMAGE_TAG}"
echo "Tagged for registry: ${FULL_IMAGE_NAME}"
echo ""
echo "To push to registry:"
echo "  docker push ${FULL_IMAGE_NAME}"
echo ""
echo "To test locally:"
echo "  docker run -p 8080:80 ${IMAGE_NAME}:${IMAGE_TAG}"

