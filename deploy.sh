#!/bin/bash
# Quick deployment script for AI Story World

set -e

echo "🚀 Starting AI Story World deployment..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found"
    echo "   Please create .env from env.example and add your API keys"
    exit 1
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Error: Docker is not running"
    echo "   Please start Docker Desktop"
    exit 1
fi

# Pull latest images
echo "📦 Pulling latest images..."
docker-compose pull

# Build application
echo "🔨 Building application..."
docker-compose build

# Start services
echo "🎬 Starting services..."
docker-compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 10

# Check health
echo "🏥 Checking API health..."
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ API is healthy!"
else
    echo "⚠️  API health check failed. Check logs with: docker-compose logs api"
fi

echo ""
echo "✨ Deployment complete!"
echo ""
echo "📊 Services:"
echo "   - API:    http://localhost:8000"
echo "   - Neo4j:  http://localhost:7474 (neo4j/password)"
echo "   - Redis:  localhost:6379"
echo ""
echo "📝 Commands:"
echo "   View logs:    docker-compose logs -f"
echo "   Stop:         docker-compose down"
echo "   Restart:      docker-compose restart"
echo ""
