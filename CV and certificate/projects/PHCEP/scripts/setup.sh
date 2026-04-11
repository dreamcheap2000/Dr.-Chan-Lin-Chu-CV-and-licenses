#!/usr/bin/env bash
# PHCEP Setup Script
# Checks prerequisites and starts the local Docker Compose stack.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PHCEP_DIR="$(dirname "$SCRIPT_DIR")"
DOCKER_DIR="$PHCEP_DIR/docker"

echo "=== PHCEP Setup ==="

# Check prerequisites
for cmd in docker java mvn node python3; do
    if ! command -v "$cmd" &> /dev/null; then
        echo "ERROR: '$cmd' is required but not installed."
        exit 1
    fi
done

echo "✓ Prerequisites satisfied"

# Create .env if missing
if [ ! -f "$DOCKER_DIR/../.env" ]; then
    echo "Creating .env from template..."
    cat > "$DOCKER_DIR/../.env" << 'EOF'
JWT_SECRET=REPLACE_WITH_256_BIT_BASE64_SECRET
LINE_CHANNEL_ACCESS_TOKEN=YOUR_LINE_CHANNEL_ACCESS_TOKEN
LINE_CHANNEL_SECRET=YOUR_LINE_CHANNEL_SECRET
DATE_SHIFT_SEED=REPLACE_WITH_RANDOM_SECRET
EOF
    echo "⚠  Edit .env with your secrets before starting services."
fi

# Start Docker Compose stack
echo "Starting PHCEP stack..."
cd "$DOCKER_DIR"
docker compose up --build -d

echo ""
echo "=== PHCEP is running ==="
echo "  Frontend  → http://localhost:3000"
echo "  Backend   → http://localhost:8080"
echo "  ML API    → http://localhost:8081"
echo "  PostgreSQL→ localhost:5432"
echo ""
echo "Stop with: docker compose -f $DOCKER_DIR/docker-compose.yml down"
