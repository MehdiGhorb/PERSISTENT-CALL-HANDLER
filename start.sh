#!/bin/bash
# Quick start script for Persistent Call Handler

set -e

echo "🚀 Starting Persistent Call Handler..."

# Check if .env.local exists
if [ ! -f .env.local ]; then
    echo "❌ .env.local not found"
    echo "📝 Please copy .env.example to .env.local and configure it"
    echo ""
    echo "   cp .env.example .env.local"
    echo ""
    exit 1
fi

# Build and start with Docker Compose
echo "🐳 Building and starting Docker container..."
docker compose up --build -d

echo ""
echo "⏳ Waiting for service to be ready..."
sleep 10

# Check health
echo "🏥 Checking health..."
curl -s http://localhost:8001/health | python -m json.tool || echo "Health check pending..."

echo ""
echo "✅ Service started!"
echo ""
echo "📊 Check status: curl http://localhost:8001/status"
echo "📝 View logs:    docker compose logs -f"
echo "🛑 Stop:         docker compose down"
echo ""
