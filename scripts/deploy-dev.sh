#!/bin/bash

# Development deployment script for CSRD RAG System

set -e

echo "🚀 Starting CSRD RAG System - Development Environment"

# Check if Docker and Docker Compose are installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p data/documents data/chroma_db data/schemas logs/nginx

# Copy environment file if it doesn't exist
if [ ! -f .env ]; then
    echo "📋 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please update .env file with your configuration before proceeding."
    read -p "Press enter to continue after updating .env file..."
fi

# Build and start services
echo "🔨 Building Docker images..."
docker-compose -f docker-compose.yml -f docker-compose.dev.yml build

echo "🏃 Starting services..."
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# Wait for services to be healthy
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check service health
echo "🔍 Checking service health..."
docker-compose -f docker-compose.yml -f docker-compose.dev.yml ps

# Run database migrations
echo "🗄️  Running database migrations..."
docker-compose -f docker-compose.yml -f docker-compose.dev.yml exec app python -m alembic upgrade head

# Load initial schemas
echo "📊 Loading initial schemas..."
docker-compose -f docker-compose.yml -f docker-compose.dev.yml exec app python -c "
from backend.app.services.schema_service import SchemaService
schema_service = SchemaService()
schema_service.load_initial_schemas()
print('✅ Schemas loaded successfully')
"

echo "✅ Development environment is ready!"
echo "🌐 Application is available at: http://localhost:8000"
echo "📚 API documentation: http://localhost:8000/docs"
echo "🔍 To view logs: docker-compose -f docker-compose.yml -f docker-compose.dev.yml logs -f"
echo "🛑 To stop: docker-compose -f docker-compose.yml -f docker-compose.dev.yml down"