# 🚀 Complete Deployment Instructions

This guide covers everything you need to deploy the CSRD RAG System from GitHub to a running application.

## 📋 Prerequisites

Before you begin, ensure you have:

- **Git** installed
- **Docker** and **Docker Compose** installed
- **OpenAI API key** (required for AI functionality)
- **Basic command line knowledge**

### System Requirements

**Minimum:**
- 2 CPU cores
- 4GB RAM  
- 10GB storage
- Internet connection

**Recommended:**
- 4+ CPU cores
- 8GB+ RAM
- 50GB+ SSD storage
- High-speed internet

## 🔧 Step-by-Step Deployment

### 1. Clone the Repository

```bash
# Clone from GitHub
git clone https://github.com/YOUR_USERNAME/csrd-rag-system.git
cd csrd-rag-system

# Verify you have all the files
ls -la
```

You should see:
```
├── README.md
├── docker-compose.yml
├── docker-compose.dev.yml
├── docker-compose.prod.yml
├── .env.example
├── backend/
├── frontend-simple/
├── docs/
└── scripts/
```

### 2. Environment Configuration

```bash
# Copy the environment template
cp .env.example .env

# Edit the environment file
nano .env  # or use your preferred editor
```

**Required Environment Variables:**

```bash
# Database Configuration
POSTGRES_USER=csrd_user
POSTGRES_PASSWORD=your_secure_password_here
POSTGRES_DB=csrd_rag
DATABASE_URL=postgresql://csrd_user:your_secure_password_here@postgres:5432/csrd_rag

# Redis Configuration
REDIS_URL=redis://redis:6379/0

# AI Model APIs (at least OpenAI is required)
OPENAI_API_KEY=sk-your-openai-api-key-here
ANTHROPIC_API_KEY=your-anthropic-api-key-here  # Optional

# Security
SECRET_KEY=your-very-secure-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1,your-domain.com

# File Storage
UPLOAD_DIR=/app/data/uploads
MAX_FILE_SIZE=100MB

# Vector Database
CHROMA_PERSIST_DIRECTORY=/app/data/chroma
CHROMA_HOST=chroma
CHROMA_PORT=8000

# Monitoring
PROMETHEUS_PORT=9090
GRAFANA_PORT=3001
```

**Generate Secure Keys:**

```bash
# Generate a secure secret key
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Generate a secure database password
openssl rand -base64 32
```

### 3. Choose Your Deployment Mode

#### Option A: Development Mode (Recommended for Testing)

```bash
# Start all services in development mode
docker-compose -f docker-compose.dev.yml up -d

# Check that all services are running
docker-compose -f docker-compose.dev.yml ps

# View logs if needed
docker-compose -f docker-compose.dev.yml logs -f
```

#### Option B: Production Mode

```bash
# Start all services in production mode
docker-compose -f docker-compose.prod.yml up -d

# Check status
docker-compose -f docker-compose.prod.yml ps
```

### 4. Wait for Services to Start

The system needs time to initialize:

```bash
# Monitor the startup process
docker-compose -f docker-compose.dev.yml logs -f

# Wait for these messages:
# - "PostgreSQL init process complete"
# - "FastAPI server started"
# - "Frontend server started"
# - "Chroma server started"
```

This typically takes 1-3 minutes on first startup.

### 5. Verify Deployment

#### Check Service Health

```bash
# Check all containers are running
docker-compose -f docker-compose.dev.yml ps

# Should show all services as "Up"
```

#### Test API Endpoints

```bash
# Test backend health
curl http://localhost:8000/health

# Should return: {"status": "healthy"}

# Test API documentation
curl http://localhost:8000/docs
```

#### Access the Application

Open your web browser and visit:

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Monitoring**: http://localhost:3001

### 6. Initial System Setup

#### Run Database Migrations

```bash
# Execute database setup
docker-compose -f docker-compose.dev.yml exec backend python -m alembic upgrade head

# Load initial schema data
docker-compose -f docker-compose.dev.yml exec backend python -c "
from app.services.schema_service import SchemaService
schema_service = SchemaService()
schema_service.load_schemas()
print('Schemas loaded successfully')
"
```

#### Validate System Setup

```bash
# Run system validation
docker-compose -f docker-compose.dev.yml exec backend python validate_setup.py

# Run integration tests
docker-compose -f docker-compose.dev.yml exec backend python backend/demo_integration_tests.py
```

## 🧪 Testing Your Deployment

### 1. Upload a Test Document

1. Go to http://localhost:3000
2. Navigate to "Documents" page
3. Upload a text file or PDF
4. Wait for processing to complete

### 2. Test Search Functionality

1. Go to "Search" page
2. Enter a search query
3. Verify results are returned

### 3. Test AI Question Answering

1. Go to "RAG" page
2. Select "GPT-4" model
3. Ask a question about your uploaded document
4. Verify AI response is generated

## 🔧 Troubleshooting

### Common Issues and Solutions

#### Services Won't Start

```bash
# Check Docker is running
docker --version
docker-compose --version

# Check for port conflicts
netstat -tulpn | grep :3000
netstat -tulpn | grep :8000

# Restart Docker
sudo systemctl restart docker  # Linux
# or restart Docker Desktop on Mac/Windows
```

#### Database Connection Errors

```bash
# Check PostgreSQL logs
docker-compose -f docker-compose.dev.yml logs postgres

# Reset database
docker-compose -f docker-compose.dev.yml down -v
docker-compose -f docker-compose.dev.yml up -d
```

#### Frontend Not Loading

```bash
# Check frontend logs
docker-compose -f docker-compose.dev.yml logs frontend

# Rebuild frontend
docker-compose -f docker-compose.dev.yml build frontend
docker-compose -f docker-compose.dev.yml up -d frontend
```

#### AI Models Not Working

```bash
# Verify API keys are set
docker-compose -f docker-compose.dev.yml exec backend env | grep API_KEY

# Test API key
docker-compose -f docker-compose.dev.yml exec backend python -c "
import openai
import os
openai.api_key = os.getenv('OPENAI_API_KEY')
print('OpenAI API key is valid' if openai.api_key else 'OpenAI API key not found')
"
```

#### Out of Memory Errors

```bash
# Check system resources
docker stats

# Increase Docker memory limit (Docker Desktop)
# Settings → Resources → Memory → Increase to 6GB+

# Or reduce services
docker-compose -f docker-compose.dev.yml stop grafana prometheus
```

### Log Analysis

```bash
# View all logs
docker-compose -f docker-compose.dev.yml logs

# View specific service logs
docker-compose -f docker-compose.dev.yml logs backend
docker-compose -f docker-compose.dev.yml logs frontend
docker-compose -f docker-compose.dev.yml logs postgres

# Follow logs in real-time
docker-compose -f docker-compose.dev.yml logs -f backend
```

## 🔄 Updating the System

### Pull Latest Changes

```bash
# Pull latest code
git pull origin main

# Rebuild and restart services
docker-compose -f docker-compose.dev.yml down
docker-compose -f docker-compose.dev.yml build
docker-compose -f docker-compose.dev.yml up -d
```

### Update Dependencies

```bash
# Rebuild with no cache
docker-compose -f docker-compose.dev.yml build --no-cache

# Update Python packages
docker-compose -f docker-compose.dev.yml exec backend pip install -r requirements.txt --upgrade
```

## 🛑 Stopping the System

```bash
# Stop all services
docker-compose -f docker-compose.dev.yml down

# Stop and remove all data (careful!)
docker-compose -f docker-compose.dev.yml down -v

# Remove all images (to free space)
docker-compose -f docker-compose.dev.yml down --rmi all
```

## 🌐 Production Deployment

### Domain Setup

1. **Point your domain** to your server's IP address
2. **Update .env file**:
   ```bash
   ALLOWED_HOSTS=localhost,127.0.0.1,yourdomain.com
   ```

### SSL Certificate

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d yourdomain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

### Production Configuration

```bash
# Use production compose file
docker-compose -f docker-compose.prod.yml up -d

# Enable monitoring
docker-compose -f docker-compose.monitoring.yml up -d
```

## 📊 Monitoring

### Grafana Dashboard

1. Go to http://localhost:3001
2. Login: admin / admin
3. Import dashboards from `monitoring/grafana/`

### Prometheus Metrics

- Visit http://localhost:9090
- Check system metrics and alerts

### Health Monitoring

```bash
# Automated health check
./scripts/health-check.sh

# Manual health check
curl http://localhost:8000/health
```

## 🔐 Security Checklist

- [ ] Changed default passwords
- [ ] Set strong SECRET_KEY
- [ ] Configured ALLOWED_HOSTS
- [ ] Set up SSL certificates (production)
- [ ] Enabled firewall rules
- [ ] Regular security updates
- [ ] Monitor access logs

## 📈 Performance Optimization

### Resource Monitoring

```bash
# Monitor resource usage
docker stats

# Check disk usage
df -h
docker system df
```

### Optimization Tips

1. **Increase memory** for better performance
2. **Use SSD storage** for database
3. **Configure Redis** for caching
4. **Enable compression** in nginx
5. **Monitor and tune** database queries

## ✅ Deployment Checklist

- [ ] Repository cloned successfully
- [ ] Environment variables configured
- [ ] All services started without errors
- [ ] Database migrations completed
- [ ] Frontend accessible at http://localhost:3000
- [ ] Backend API accessible at http://localhost:8000
- [ ] Document upload works
- [ ] Search functionality works
- [ ] AI question answering works
- [ ] Monitoring dashboards accessible
- [ ] System validation tests pass

---

**🎉 Congratulations! Your CSRD RAG System is now deployed and running!**

For ongoing support, check the documentation in the `docs/` folder or create an issue on GitHub.