# 🚀 CSRD RAG System - Quick Start Guide

Get the CSRD RAG System running in under 5 minutes!

## Prerequisites

- **Git** installed on your system
- **Docker & Docker Compose** installed
- **Basic terminal/command line knowledge**

## Step 1: Clone the Repository

```bash
git clone https://github.com/yourusername/csrd-rag-system.git
cd csrd-rag-system
```

## Step 2: Configure Environment

```bash
# Copy the example environment file
cp .env.example .env

# Edit the .env file with your settings
# At minimum, you need to set:
# - OPENAI_API_KEY (for AI functionality)
# - POSTGRES_PASSWORD (database password)
# - SECRET_KEY (for security)
```

### Required Environment Variables

Open `.env` and set these essential variables:

```bash
# Required: OpenAI API key for AI functionality
OPENAI_API_KEY=your_openai_api_key_here

# Required: Database password
POSTGRES_PASSWORD=your_secure_password_here

# Required: Secret key for security
SECRET_KEY=your_secret_key_here

# Optional: Anthropic API key for Claude model
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

## Step 3: Start the System

```bash
# Start in development mode (recommended for first run)
docker-compose -f docker-compose.dev.yml up -d

# Wait for all services to start (about 30-60 seconds)
# Check status with:
docker-compose -f docker-compose.dev.yml ps
```

## Step 4: Access the Application

Once all containers are running:

- **🌐 Frontend Application**: http://localhost:3000
- **🔧 Backend API**: http://localhost:8000
- **📚 API Documentation**: http://localhost:8000/docs
- **📊 Monitoring Dashboard**: http://localhost:3001 (Grafana)

## Step 5: Test the System

### Upload a Document
1. Go to http://localhost:3000
2. Navigate to "Documents" page
3. Upload a PDF or text file about sustainability
4. Wait for processing to complete

### Try Search
1. Go to "Search" page
2. Enter a query like "carbon emissions"
3. View search results with relevance scores

### Ask Questions (RAG)
1. Go to "RAG" page
2. Select "GPT-4" model
3. Ask: "What are the main requirements for carbon reporting?"
4. Get AI-generated answers with source citations

## 🔧 Troubleshooting

### Common Issues

**Services not starting?**
```bash
# Check logs
docker-compose -f docker-compose.dev.yml logs

# Restart services
docker-compose -f docker-compose.dev.yml restart
```

**Database connection errors?**
```bash
# Check if PostgreSQL is running
docker-compose -f docker-compose.dev.yml ps postgres

# Reset database
docker-compose -f docker-compose.dev.yml down -v
docker-compose -f docker-compose.dev.yml up -d
```

**Frontend not loading?**
```bash
# Check frontend logs
docker-compose -f docker-compose.dev.yml logs frontend

# Rebuild frontend
docker-compose -f docker-compose.dev.yml build frontend
docker-compose -f docker-compose.dev.yml up -d frontend
```

### Health Check

Visit http://localhost:8000/health to check system status.

### System Validation

```bash
# Run system validation
docker-compose -f docker-compose.dev.yml exec backend python validate_setup.py

# Run demo tests
docker-compose -f docker-compose.dev.yml exec backend python backend/demo_integration_tests.py
```

## 🛑 Stopping the System

```bash
# Stop all services
docker-compose -f docker-compose.dev.yml down

# Stop and remove all data (careful!)
docker-compose -f docker-compose.dev.yml down -v
```

## 📈 Next Steps

1. **Upload Documents**: Add your sustainability documents
2. **Configure AI Models**: Set up additional AI model API keys
3. **Customize Schemas**: Add custom reporting schemas
4. **Set up Monitoring**: Configure Grafana dashboards
5. **Production Deployment**: Use `docker-compose.prod.yml` for production

## 🆘 Need Help?

- **Documentation**: Check the `docs/` folder
- **API Reference**: Visit http://localhost:8000/docs
- **Issues**: Create a GitHub issue
- **Logs**: Use `docker-compose logs [service-name]`

## 🎯 What You Can Do Now

✅ **Upload sustainability documents**  
✅ **Search through document content**  
✅ **Ask AI questions about regulations**  
✅ **Generate compliance reports**  
✅ **Monitor system performance**  
✅ **Access comprehensive APIs**  

---

**🎉 Congratulations! Your CSRD RAG System is now running!**