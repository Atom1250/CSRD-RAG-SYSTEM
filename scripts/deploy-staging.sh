#!/bin/bash

# Staging deployment script for CSRD RAG System

set -e

echo "🚀 Starting CSRD RAG System - Staging Environment"

# Configuration
BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
HEALTH_CHECK_TIMEOUT=300

# Check prerequisites
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Validate environment file
if [ ! -f .env ]; then
    echo "❌ .env file not found. Please create it from .env.example"
    exit 1
fi

# Source environment variables
source .env

# Create backup of existing data
if [ -d "data" ]; then
    echo "💾 Creating backup of existing data..."
    mkdir -p "$BACKUP_DIR"
    cp -r data "$BACKUP_DIR/"
    echo "✅ Backup created at $BACKUP_DIR"
fi

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p data/documents data/chroma_db data/schemas logs/nginx

# Pull latest images
echo "📥 Pulling latest images..."
docker-compose pull

# Build application image
echo "🔨 Building application image..."
docker-compose build

# Stop existing services gracefully
echo "🛑 Stopping existing services..."
docker-compose down --timeout 30

# Start services
echo "🏃 Starting services..."
docker-compose up -d

# Wait for services to be healthy
echo "⏳ Waiting for services to be ready..."
timeout=$HEALTH_CHECK_TIMEOUT
while [ $timeout -gt 0 ]; do
    if docker-compose exec -T app curl -f http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ Application is healthy"
        break
    fi
    echo "⏳ Waiting for application... ($timeout seconds remaining)"
    sleep 5
    timeout=$((timeout - 5))
done

if [ $timeout -le 0 ]; then
    echo "❌ Application failed to start within $HEALTH_CHECK_TIMEOUT seconds"
    echo "📋 Service status:"
    docker-compose ps
    echo "📋 Application logs:"
    docker-compose logs app
    exit 1
fi

# Run database migrations
echo "🗄️  Running database migrations..."
docker-compose exec -T app python -m alembic upgrade head

# Load schemas if needed
echo "📊 Loading schemas..."
docker-compose exec -T app python -c "
from backend.app.services.schema_service import SchemaService
schema_service = SchemaService()
schema_service.load_initial_schemas()
print('✅ Schemas loaded successfully')
"

# Verify deployment
echo "🔍 Verifying deployment..."
docker-compose ps

# Health check
if docker-compose exec -T app curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Staging deployment successful!"
    echo "🌐 Application is available at: http://localhost:8000"
    echo "📚 API documentation: http://localhost:8000/docs"
else
    echo "❌ Health check failed"
    exit 1
fi

echo "📋 Deployment Summary:"
echo "  - Environment: Staging"
echo "  - Backup location: $BACKUP_DIR"
echo "  - Application URL: http://localhost:8000"
echo "  - API Docs: http://localhost:8000/docs"
echo ""
echo "🔍 To monitor: docker-compose logs -f"
echo "🛑 To stop: docker-compose down"