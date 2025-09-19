#!/bin/bash

# Production deployment script for CSRD RAG System

set -e

echo "🚀 Starting CSRD RAG System - Production Environment"

# Configuration
BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
HEALTH_CHECK_TIMEOUT=600
ROLLBACK_ENABLED=true

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
if ! command -v docker &> /dev/null; then
    log_error "Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    log_error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Validate environment file
if [ ! -f .env ]; then
    log_error ".env file not found. Please create it from .env.example"
    exit 1
fi

# Source environment variables
source .env

# Validate required environment variables
required_vars=("POSTGRES_PASSWORD" "REDIS_PASSWORD" "OPENAI_API_KEY")
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        log_error "Required environment variable $var is not set"
        exit 1
    fi
done

# Pre-deployment checks
log_info "Running pre-deployment checks..."

# Check SSL certificates
if [ ! -f "nginx/ssl/cert.pem" ] || [ ! -f "nginx/ssl/key.pem" ]; then
    log_warn "SSL certificates not found. HTTPS will not be available."
    log_warn "Please place cert.pem and key.pem in nginx/ssl/ directory"
fi

# Check disk space (require at least 5GB free)
available_space=$(df . | tail -1 | awk '{print $4}')
required_space=5242880  # 5GB in KB
if [ "$available_space" -lt "$required_space" ]; then
    log_error "Insufficient disk space. Required: 5GB, Available: $(($available_space/1024/1024))GB"
    exit 1
fi

# Create comprehensive backup
log_info "Creating comprehensive backup..."
mkdir -p "$BACKUP_DIR"

# Backup data
if [ -d "data" ]; then
    cp -r data "$BACKUP_DIR/"
fi

# Backup database
if docker-compose ps postgres | grep -q "Up"; then
    log_info "Backing up database..."
    docker-compose exec -T postgres pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" > "$BACKUP_DIR/database_backup.sql"
fi

# Backup current docker-compose state
docker-compose config > "$BACKUP_DIR/docker-compose-backup.yml"

log_info "Backup created at $BACKUP_DIR"

# Create necessary directories
log_info "Creating necessary directories..."
mkdir -p data/documents data/chroma_db data/schemas logs/nginx nginx/ssl

# Pull latest images
log_info "Pulling latest images..."
docker-compose -f docker-compose.yml -f docker-compose.prod.yml pull

# Build application image
log_info "Building application image..."
docker-compose -f docker-compose.yml -f docker-compose.prod.yml build --no-cache

# Graceful shutdown of existing services
log_info "Gracefully stopping existing services..."
if docker-compose ps | grep -q "Up"; then
    # Give services time to finish current requests
    docker-compose -f docker-compose.yml -f docker-compose.prod.yml exec -T app curl -X POST http://localhost:8000/admin/maintenance-mode || true
    sleep 10
    docker-compose -f docker-compose.yml -f docker-compose.prod.yml down --timeout 60
fi

# Start services with production configuration
log_info "Starting production services..."
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Wait for services to be healthy
log_info "Waiting for services to be ready..."
timeout=$HEALTH_CHECK_TIMEOUT
healthy=false

while [ $timeout -gt 0 ]; do
    if docker-compose -f docker-compose.yml -f docker-compose.prod.yml exec -T app curl -f http://localhost:8000/health > /dev/null 2>&1; then
        log_info "Application is healthy"
        healthy=true
        break
    fi
    echo "⏳ Waiting for application... ($timeout seconds remaining)"
    sleep 10
    timeout=$((timeout - 10))
done

if [ "$healthy" = false ]; then
    log_error "Application failed to start within $HEALTH_CHECK_TIMEOUT seconds"
    
    if [ "$ROLLBACK_ENABLED" = true ]; then
        log_warn "Rolling back to previous version..."
        docker-compose -f docker-compose.yml -f docker-compose.prod.yml down
        
        # Restore from backup if available
        if [ -f "$BACKUP_DIR/docker-compose-backup.yml" ]; then
            log_info "Restoring previous configuration..."
            # This would require more sophisticated rollback logic
            log_warn "Manual rollback required. Backup available at $BACKUP_DIR"
        fi
    fi
    
    log_error "Deployment failed. Check logs:"
    docker-compose -f docker-compose.yml -f docker-compose.prod.yml logs
    exit 1
fi

# Run database migrations
log_info "Running database migrations..."
docker-compose -f docker-compose.yml -f docker-compose.prod.yml exec -T app python -m alembic upgrade head

# Load schemas
log_info "Loading schemas..."
docker-compose -f docker-compose.yml -f docker-compose.prod.yml exec -T app python -c "
from backend.app.services.schema_service import SchemaService
schema_service = SchemaService()
schema_service.load_initial_schemas()
print('✅ Schemas loaded successfully')
"

# Post-deployment verification
log_info "Running post-deployment verification..."

# Check all services are running
services_status=$(docker-compose -f docker-compose.yml -f docker-compose.prod.yml ps --services --filter "status=running")
expected_services=("postgres" "redis" "chroma" "app" "celery-worker" "nginx")

for service in "${expected_services[@]}"; do
    if echo "$services_status" | grep -q "$service"; then
        log_info "✅ $service is running"
    else
        log_error "❌ $service is not running"
        exit 1
    fi
done

# Test API endpoints
log_info "Testing API endpoints..."
if curl -f -s http://localhost/health > /dev/null; then
    log_info "✅ Health endpoint accessible"
else
    log_error "❌ Health endpoint not accessible"
    exit 1
fi

if curl -f -s http://localhost/docs > /dev/null; then
    log_info "✅ API documentation accessible"
else
    log_warn "⚠️  API documentation not accessible"
fi

# Performance check
log_info "Running performance check..."
response_time=$(curl -o /dev/null -s -w '%{time_total}' http://localhost/health)
if (( $(echo "$response_time < 2.0" | bc -l) )); then
    log_info "✅ Response time acceptable: ${response_time}s"
else
    log_warn "⚠️  Response time high: ${response_time}s"
fi

log_info "✅ Production deployment successful!"

echo ""
echo "📋 Deployment Summary:"
echo "  - Environment: Production"
echo "  - Backup location: $BACKUP_DIR"
echo "  - Application URL: https://your-domain.com (or http://localhost)"
echo "  - API Docs: https://your-domain.com/docs"
echo "  - Services: $(echo "$services_status" | wc -l) running"
echo ""
echo "🔍 Monitoring commands:"
echo "  - View logs: docker-compose -f docker-compose.yml -f docker-compose.prod.yml logs -f"
echo "  - Check status: docker-compose -f docker-compose.yml -f docker-compose.prod.yml ps"
echo "  - Stop services: docker-compose -f docker-compose.yml -f docker-compose.prod.yml down"
echo ""
echo "⚠️  Remember to:"
echo "  - Monitor application logs for the first few hours"
echo "  - Update DNS records if needed"
echo "  - Configure SSL certificates for HTTPS"
echo "  - Set up monitoring and alerting"