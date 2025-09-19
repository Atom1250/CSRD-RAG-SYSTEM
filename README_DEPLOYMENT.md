# CSRD RAG System - Deployment Documentation

## Quick Start

### Development Environment

```bash
# Clone repository
git clone <repository-url>
cd csrd-rag-system

# Copy environment configuration
cp .env.example .env
# Edit .env with your settings

# Deploy development environment
./scripts/deploy-dev.sh
```

**Access Points:**
- Application: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

### Production Environment

```bash
# Ensure SSL certificates are in place
mkdir -p nginx/ssl
cp your-cert.pem nginx/ssl/cert.pem
cp your-key.pem nginx/ssl/key.pem

# Configure production environment
cp .env.example .env
# Update .env with production settings

# Deploy production environment
./scripts/deploy-prod.sh
```

## Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Nginx Proxy   │    │  Load Balancer  │    │   Monitoring    │
│   (SSL/HTTPS)   │    │   (Optional)    │    │   (Optional)    │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 │
                    ┌─────────────┴─────────────┐
                    │    CSRD RAG Application   │
                    │      (FastAPI)            │
                    └─────────────┬─────────────┘
                                  │
          ┌───────────────────────┼───────────────────────┐
          │                       │                       │
    ┌─────▼─────┐         ┌─────▼─────┐         ┌─────▼─────┐
    │PostgreSQL │         │   Redis   │         │  Chroma   │
    │ Database  │         │   Cache   │         │Vector DB  │
    └───────────┘         └───────────┘         └───────────┘
          │                       │                       │
          └───────────────────────┼───────────────────────┘
                                  │
                         ┌─────▼─────┐
                         │  Celery   │
                         │ Workers   │
                         └───────────┘
```

## Service Components

### Core Services

1. **Application (FastAPI)**
   - Main web application and API
   - Document processing and RAG functionality
   - Health checks and monitoring endpoints

2. **PostgreSQL Database**
   - Document metadata and user data
   - Configuration and schema information
   - Persistent storage for application state

3. **Redis Cache**
   - Session management and caching
   - Celery message broker
   - Performance optimization

4. **Chroma Vector Database**
   - Document embeddings storage
   - Semantic search functionality
   - Vector similarity operations

5. **Celery Workers**
   - Asynchronous document processing
   - Background task execution
   - Queue management

### Optional Services

6. **Nginx Reverse Proxy**
   - SSL termination and HTTPS
   - Load balancing and rate limiting
   - Static file serving

7. **Monitoring Stack** (Optional)
   - Prometheus for metrics collection
   - Grafana for visualization
   - AlertManager for notifications

## Environment Configurations

### Development
- Hot reload enabled
- Debug mode active
- All ports exposed for debugging
- Simplified security settings

### Staging
- Production-like configuration
- Performance testing ready
- Backup and recovery testing
- Integration testing environment

### Production
- SSL/HTTPS enforced
- Resource limits and scaling
- Comprehensive monitoring
- Security hardening

## Health Monitoring

### Health Check Endpoints

| Endpoint | Purpose | Response Time |
|----------|---------|---------------|
| `/health` | Comprehensive system health | < 2s |
| `/api/v1/metrics/health` | Detailed service status | < 1s |
| `/api/v1/metrics/summary` | Key metrics summary | < 500ms |

### Health Check Script

```bash
# Simple health check
./scripts/health-check.sh --simple

# Detailed diagnostics
./scripts/health-check.sh --detailed

# Process-only check
./scripts/health-check.sh --process
```

### Monitoring Metrics

**System Metrics:**
- CPU usage and load average
- Memory consumption and availability
- Disk usage and I/O operations
- Network traffic and connections

**Application Metrics:**
- Request response times
- Error rates and status codes
- Document processing statistics
- RAG query performance

**Service Health:**
- Database connectivity and performance
- Cache hit rates and memory usage
- Vector database operations
- Celery worker status and queue length

## Deployment Scripts

### Development Deployment
```bash
./scripts/deploy-dev.sh
```
- Builds and starts all services
- Runs database migrations
- Loads initial schemas
- Provides development-friendly configuration

### Staging Deployment
```bash
./scripts/deploy-staging.sh
```
- Production-like deployment
- Comprehensive health checks
- Backup creation before deployment
- Performance validation

### Production Deployment
```bash
./scripts/deploy-prod.sh
```
- Full production deployment
- SSL certificate validation
- Resource optimization
- Comprehensive monitoring setup
- Rollback capabilities

## Configuration Management

### Environment Variables

**Required Variables:**
```bash
# Database
POSTGRES_DB=csrd_rag
POSTGRES_USER=csrd_user
POSTGRES_PASSWORD=secure_password

# Redis
REDIS_PASSWORD=redis_password

# AI Models
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key

# Application
SECRET_KEY=your_secret_key
ENVIRONMENT=production
```

**Optional Variables:**
```bash
# Monitoring
GRAFANA_PASSWORD=admin_password
PROMETHEUS_RETENTION=200h

# Performance
MAX_WORKERS=4
CACHE_TTL=3600

# Security
ALLOWED_HOSTS=yourdomain.com
CORS_ORIGINS=https://yourdomain.com
```

### SSL Configuration

For production deployments with HTTPS:

```bash
# Create SSL directory
mkdir -p nginx/ssl

# Copy certificates
cp your-certificate.pem nginx/ssl/cert.pem
cp your-private-key.pem nginx/ssl/key.pem

# Set proper permissions
chmod 600 nginx/ssl/key.pem
chmod 644 nginx/ssl/cert.pem
```

## Backup and Recovery

### Automated Backups

```bash
# Database backup
./scripts/backup-db.sh

# Document storage backup
./scripts/backup-documents.sh

# Full system backup
./scripts/backup-full.sh
```

### Recovery Procedures

```bash
# Restore database
./scripts/restore-db.sh backup/database.sql

# Restore documents
./scripts/restore-documents.sh backup/documents.tar.gz

# Full system restore
./scripts/restore-full.sh backup/full-backup.tar.gz
```

## Scaling and Performance

### Horizontal Scaling

```yaml
# docker-compose.prod.yml
services:
  app:
    deploy:
      replicas: 3  # Scale application instances
      
  celery-worker:
    deploy:
      replicas: 2  # Scale worker instances
```

### Resource Optimization

**CPU Optimization:**
- Adjust worker processes based on CPU cores
- Enable CPU affinity for better performance
- Monitor CPU usage and scale accordingly

**Memory Optimization:**
- Configure appropriate memory limits
- Optimize database connection pooling
- Use Redis for caching frequently accessed data

**Storage Optimization:**
- Use SSD storage for better I/O performance
- Implement data retention policies
- Regular cleanup of temporary files

## Security Considerations

### Network Security
- All services communicate via internal Docker network
- Only necessary ports exposed to host
- Firewall rules for production deployment

### Data Security
- SSL/TLS encryption for all external communication
- Database encryption at rest (if supported)
- Secure API key storage and rotation

### Application Security
- Input validation and sanitization
- Rate limiting on API endpoints
- Security headers and CORS configuration
- Regular security updates

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
# Test connectivity
docker-compose exec app python -c "
from app.models.database_config import get_db
db = next(get_db())
db.execute('SELECT 1')
print('Database connection successful')
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

### Log Analysis

**Application Logs:**
```bash
# View real-time logs
docker-compose logs -f app

# Search for errors
docker-compose logs app | grep ERROR

# Export logs for analysis
docker-compose logs app > app.log
```

**System Logs:**
```bash
# View system metrics
curl http://localhost:8000/api/v1/metrics/system

# Check health status
curl http://localhost:8000/health

# View alerts
curl http://localhost:8000/api/v1/metrics/alerts
```

## Maintenance

### Regular Maintenance Tasks

**Daily:**
- Monitor system health and alerts
- Check disk space and resource usage
- Review error logs for issues
- Verify backup completion

**Weekly:**
- Update system packages
- Review performance metrics
- Clean up old logs and temporary files
- Test backup recovery procedures

**Monthly:**
- Security updates and patches
- Performance optimization review
- Capacity planning assessment
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
# Update Docker
curl -fsSL https://get.docker.com | sh

# Update system packages
sudo apt update && sudo apt upgrade

# Restart services if needed
docker-compose restart
```

## Support and Documentation

### Additional Resources
- [API Documentation](docs/API_DOCUMENTATION.md)
- [User Guide](docs/USER_GUIDE.md)
- [Deployment Guide](docs/DEPLOYMENT_GUIDE.md)

### Getting Help
1. Check service health endpoints
2. Review application and system logs
3. Consult troubleshooting documentation
4. Contact system administrator or support team

### Contributing
For deployment improvements:
1. Test changes in development environment
2. Document configuration changes
3. Update deployment scripts
4. Submit pull requests with clear descriptions