# CSRD RAG System Deployment Guide

## Overview

This guide provides comprehensive instructions for deploying the CSRD RAG System in development, staging, and production environments using Docker containers.

## Prerequisites

### System Requirements

**Minimum Requirements:**
- 4 CPU cores
- 8 GB RAM
- 50 GB available disk space
- Docker 20.10+ and Docker Compose 2.0+

**Recommended Requirements:**
- 8 CPU cores
- 16 GB RAM
- 100 GB available disk space (SSD preferred)
- Load balancer for production deployments

### Software Dependencies

**Required:**
- Docker Engine 20.10+
- Docker Compose 2.0+
- Git (for source code)

**Optional:**
- Nginx (for reverse proxy)
- SSL certificates (for HTTPS)
- Monitoring tools (Prometheus, Grafana)

## Environment Setup

### 1. Clone Repository

```bash
git clone <repository-url>
cd csrd-rag-system
```

### 2. Environment Configuration

Copy the example environment file and customize:

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

```bash
# Database Configuration
POSTGRES_DB=csrd_rag
POSTGRES_USER=csrd_user
POSTGRES_PASSWORD=your_secure_password

# Redis Configuration
REDIS_PASSWORD=your_redis_password

# AI Model Configuration
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key

# Application Configuration
ENVIRONMENT=development  # development, staging, production
DEBUG=true
LOG_LEVEL=INFO

# Security
SECRET_KEY=your_secret_key_here
ALLOWED_HOSTS=localhost,127.0.0.1

# External Services
CHROMA_HOST=chroma
CHROMA_PORT=8001
```

### 3. SSL Certificates (Production Only)

For production deployments with HTTPS:

```bash
mkdir -p nginx/ssl
# Copy your SSL certificates
cp your-cert.pem nginx/ssl/cert.pem
cp your-key.pem nginx/ssl/key.pem
```

## Development Deployment

### Quick Start

Use the automated deployment script:

```bash
chmod +x scripts/deploy-dev.sh
./scripts/deploy-dev.sh
```

### Manual Development Setup

1. **Build and start services:**
```bash
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d --build
```

2. **Check service status:**
```bash
docker-compose -f docker-compose.yml -f docker-compose.dev.yml ps
```

3. **Run database migrations:**
```bash
docker-compose -f docker-compose.yml -f docker-compose.dev.yml exec app python -m alembic upgrade head
```

4. **Load initial schemas:**
```bash
docker-compose -f docker-compose.yml -f docker-compose.dev.yml exec app python -c "
from backend.app.services.schema_service import SchemaService
schema_service = SchemaService()
schema_service.load_initial_schemas()
"
```

### Development Features

- **Hot Reload**: Code changes automatically reload the application
- **Debug Mode**: Detailed error messages and stack traces
- **Exposed Ports**: Direct access to all services for debugging
- **Volume Mounts**: Local code changes reflected immediately

### Accessing Development Environment

- **Application**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Database**: localhost:5432
- **Redis**: localhost:6379
- **Chroma Vector DB**: localhost:8001

## Staging Deployment

### Automated Staging Deployment

```bash
chmod +x scripts/deploy-staging.sh
./scripts/deploy-staging.sh
```

### Manual Staging Setup

1. **Set environment to staging:**
```bash
export ENVIRONMENT=staging
```

2. **Deploy services:**
```bash
docker-compose up -d --build
```

3. **Run health checks:**
```bash
# Wait for services to be ready
sleep 30

# Check application health
curl -f http://localhost:8000/health

# Check service status
docker-compose ps
```

4. **Run migrations and setup:**
```bash
docker-compose exec app python -m alembic upgrade head
docker-compose exec app python -c "
from backend.app.services.schema_service import SchemaService
schema_service = SchemaService()
schema_service.load_initial_schemas()
"
```

### Staging Environment Features

- **Production-like Configuration**: Mirrors production setup
- **Performance Testing**: Suitable for load testing
- **Integration Testing**: Full end-to-end testing
- **Backup Testing**: Test backup and recovery procedures

## Production Deployment

### Pre-Production Checklist

- [ ] SSL certificates configured
- [ ] Environment variables set correctly
- [ ] Database backup strategy in place
- [ ] Monitoring and alerting configured
- [ ] Load balancer configured (if applicable)
- [ ] DNS records updated
- [ ] Security review completed

### Automated Production Deployment

```bash
chmod +x scripts/deploy-prod.sh
./scripts/deploy-prod.sh
```

### Manual Production Setup

1. **Set production environment:**
```bash
export ENVIRONMENT=production
```

2. **Deploy with production configuration:**
```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

3. **Verify deployment:**
```bash
# Check all services are running
docker-compose -f docker-compose.yml -f docker-compose.prod.yml ps

# Test application health
curl -f https://your-domain.com/health

# Check SSL certificate
curl -I https://your-domain.com
```

### Production Configuration

**Resource Limits:**
- Application: 1 CPU, 1GB RAM per replica
- Database: 0.5 CPU, 512MB RAM
- Redis: 0.25 CPU, 256MB RAM
- Vector DB: 0.5 CPU, 512MB RAM

**Scaling:**
- Application: 2 replicas (can be increased)
- Celery Workers: 2 replicas
- Database: Single instance with backup
- Load balancer: Nginx with SSL termination

## Service Configuration

### PostgreSQL Database

**Configuration:**
- Version: PostgreSQL 15
- Storage: Persistent volume
- Backup: Automated daily backups
- Connection pooling: Enabled

**Optimization:**
```sql
-- Add to postgresql.conf
shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 64MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
```

### Redis Cache

**Configuration:**
- Version: Redis 7
- Persistence: AOF enabled
- Memory policy: allkeys-lru
- Password protection: Enabled

### Chroma Vector Database

**Configuration:**
- Version: Latest stable
- Storage: Persistent volume
- Collections: Separate per schema type
- Backup: Regular collection exports

### Nginx Reverse Proxy

**Features:**
- SSL termination
- Rate limiting
- Gzip compression
- Security headers
- Load balancing

**Configuration highlights:**
```nginx
# Rate limiting
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
limit_req_zone $binary_remote_addr zone=upload:10m rate=2r/s;

# Security headers
add_header X-Frame-Options DENY;
add_header X-Content-Type-Options nosniff;
add_header Strict-Transport-Security "max-age=63072000";

# File upload size
client_max_body_size 100M;
```

## Monitoring and Health Checks

### Health Check Endpoints

**Application Health:**
```bash
curl http://localhost:8000/health
```

**Service-Specific Checks:**
```bash
# Database
docker-compose exec postgres pg_isready

# Redis
docker-compose exec redis redis-cli ping

# Chroma
curl http://localhost:8001/api/v1/heartbeat
```

### Monitoring Metrics

**System Metrics:**
- CPU usage per service
- Memory consumption
- Disk usage and I/O
- Network traffic

**Application Metrics:**
- Request response times
- Error rates
- Document processing times
- Queue lengths

### Log Management

**Log Locations:**
- Application logs: `logs/app.log`
- Nginx logs: `logs/nginx/`
- Database logs: Docker container logs
- Celery logs: Docker container logs

**Log Rotation:**
```bash
# Add to crontab for log rotation
0 2 * * * docker-compose exec app python -c "
import logging.handlers
# Rotate application logs
"
```

## Backup and Recovery

### Database Backup

**Automated Backup Script:**
```bash
#!/bin/bash
# backup-db.sh
BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

docker-compose exec -T postgres pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" > "$BACKUP_DIR/database.sql"
docker-compose exec -T postgres pg_dump -U "$POSTGRES_USER" -Fc "$POSTGRES_DB" > "$BACKUP_DIR/database.dump"

echo "Database backup completed: $BACKUP_DIR"
```

**Schedule with cron:**
```bash
# Daily backup at 2 AM
0 2 * * * /path/to/backup-db.sh
```

### Document Storage Backup

```bash
#!/bin/bash
# backup-documents.sh
BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Backup document files
tar -czf "$BACKUP_DIR/documents.tar.gz" data/documents/

# Backup vector database
docker-compose exec -T chroma python -c "
import chromadb
client = chromadb.Client()
# Export collections
"

echo "Document backup completed: $BACKUP_DIR"
```

### Recovery Procedures

**Database Recovery:**
```bash
# Stop application
docker-compose down

# Restore database
docker-compose up -d postgres
docker-compose exec -T postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" < backup/database.sql

# Start all services
docker-compose up -d
```

**Document Recovery:**
```bash
# Extract documents
tar -xzf backup/documents.tar.gz -C data/

# Restart services to reindex
docker-compose restart app celery-worker
```

## Security Considerations

### Network Security

**Firewall Rules:**
```bash
# Allow only necessary ports
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw allow 22/tcp    # SSH (admin only)
ufw deny 5432/tcp   # PostgreSQL (internal only)
ufw deny 6379/tcp   # Redis (internal only)
```

**Docker Network:**
- Services communicate via internal Docker network
- Only web ports exposed to host
- Database and cache not directly accessible

### Data Security

**Encryption:**
- SSL/TLS for all external communication
- Database encryption at rest (if supported)
- Encrypted backups
- Secure API key storage

**Access Control:**
- Strong passwords for all services
- Regular password rotation
- Principle of least privilege
- Audit logging enabled

### Application Security

**Security Headers:**
```nginx
add_header X-Frame-Options DENY;
add_header X-Content-Type-Options nosniff;
add_header X-XSS-Protection "1; mode=block";
add_header Strict-Transport-Security "max-age=63072000";
add_header Content-Security-Policy "default-src 'self'";
```

**Rate Limiting:**
- API endpoints: 100 requests/minute
- Upload endpoints: 10 requests/minute
- Authentication attempts: 5 attempts/minute

## Troubleshooting

### Common Issues

**Service Won't Start:**
```bash
# Check logs
docker-compose logs service-name

# Check resource usage
docker stats

# Verify configuration
docker-compose config
```

**Database Connection Issues:**
```bash
# Test database connectivity
docker-compose exec app python -c "
from backend.app.models.database import engine
try:
    engine.connect()
    print('Database connection successful')
except Exception as e:
    print(f'Database connection failed: {e}')
"
```

**Performance Issues:**
```bash
# Check system resources
htop
df -h
iostat

# Check Docker resources
docker system df
docker system prune
```

### Performance Tuning

**Database Optimization:**
- Increase shared_buffers for more RAM
- Tune checkpoint settings
- Add appropriate indexes
- Regular VACUUM and ANALYZE

**Application Optimization:**
- Increase worker processes
- Tune connection pools
- Enable caching
- Optimize query patterns

**System Optimization:**
- Use SSD storage
- Increase available RAM
- Optimize Docker settings
- Use appropriate CPU allocation

## Maintenance

### Regular Maintenance Tasks

**Daily:**
- Check service health
- Monitor disk space
- Review error logs
- Verify backups

**Weekly:**
- Update system packages
- Review performance metrics
- Clean up old logs
- Test backup recovery

**Monthly:**
- Security updates
- Performance review
- Capacity planning
- Documentation updates

### Update Procedures

**Application Updates:**
```bash
# Pull latest code
git pull origin main

# Rebuild and deploy
docker-compose build --no-cache
docker-compose up -d

# Run migrations
docker-compose exec app python -m alembic upgrade head
```

**System Updates:**
```bash
# Update system packages
apt update && apt upgrade

# Update Docker
curl -fsSL https://get.docker.com | sh

# Restart services if needed
docker-compose restart
```

## Support and Documentation

### Additional Resources

- **API Documentation**: `/docs` endpoint
- **Health Monitoring**: `/health` endpoint
- **System Metrics**: `/api/metrics` endpoint
- **User Guide**: `docs/USER_GUIDE.md`

### Getting Help

**Self-Diagnosis:**
1. Check service health endpoints
2. Review application logs
3. Verify configuration settings
4. Test individual components

**Support Channels:**
- System administrator
- Technical documentation
- Community forums
- Professional support (if available)

### Contributing

For deployment improvements:
1. Test changes in development environment
2. Document configuration changes
3. Update deployment scripts
4. Submit pull requests with clear descriptions