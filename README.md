# CSRD RAG System

A comprehensive AI-powered system for managing Corporate Sustainability Reporting Directive (CSRD) documents with intelligent search, question-answering, and automated report generation capabilities.

## 🚀 Features

- **Document Repository**: Upload and manage PDF, DOCX, and TXT sustainability documents
- **Intelligent Search**: Semantic search through document content using vector embeddings
- **RAG Question Answering**: AI-powered responses with multiple model support (GPT-4, Claude, Llama)
- **Schema Support**: EU ESRS/CSRD and UK SRD reporting standards compliance
- **Report Generation**: Automated sustainability report creation with PDF export
- **Remote Directory Sync**: Automatic document synchronization from remote sources
- **Performance Optimized**: Caching, async processing, and comprehensive monitoring

## 🏗️ Architecture

- **Backend**: FastAPI with Python 3.9+
- **Frontend**: Vanilla TypeScript with Vite (lightweight alternative to React)
- **Database**: PostgreSQL with vector extensions
- **Vector Store**: Chroma for embeddings storage
- **Task Queue**: Celery with Redis
- **Monitoring**: Prometheus + Grafana
- **Deployment**: Docker with multi-environment support

## 📋 Prerequisites

- **Docker & Docker Compose** (recommended)
- **Python 3.9+** (for local development)
- **Node.js 18+** (for frontend development)
- **PostgreSQL 14+** (if running without Docker)
- **Redis** (for task queue)

## 🚀 Quick Start

### Option 1: Docker Compose (Recommended)

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/csrd-rag-system.git
   cd csrd-rag-system
   ```

2. **Set up environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and configuration
   ```

3. **Start the system**:
   ```bash
   # Development environment
   docker-compose -f docker-compose.dev.yml up -d
   
   # Production environment
   docker-compose -f docker-compose.prod.yml up -d
   ```

4. **Access the application**:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs
   - Monitoring: http://localhost:3001 (Grafana)

### Option 2: Local Development

1. **Clone and setup backend**:
   ```bash
   git clone https://github.com/yourusername/csrd-rag-system.git
   cd csrd-rag-system/backend
   
   # Create virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   
   # Install dependencies
   pip install -r requirements.txt
   
   # Set up environment
   cp .env.example .env
   # Edit .env with your configuration
   
   # Run database migrations
   python -m alembic upgrade head
   
   # Start the backend
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

2. **Setup frontend** (in a new terminal):
   ```bash
   cd frontend-simple
   
   # Install dependencies
   npm install
   
   # Start development server
   npm run dev
   ```

3. **Start supporting services**:
   ```bash
   # Redis (for task queue)
   docker run -d -p 6379:6379 redis:alpine
   
   # PostgreSQL (if not using Docker)
   # Install and configure PostgreSQL with vector extensions
   ```

## 🔧 Configuration

### Environment Variables

Key environment variables in `.env`:

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/csrd_rag
POSTGRES_USER=csrd_user
POSTGRES_PASSWORD=your_secure_password
POSTGRES_DB=csrd_rag

# Redis
REDIS_URL=redis://localhost:6379/0

# AI Models
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key

# Vector Database
CHROMA_PERSIST_DIRECTORY=./data/chroma
CHROMA_HOST=localhost
CHROMA_PORT=8001

# File Storage
UPLOAD_DIR=./data/uploads
MAX_FILE_SIZE=100MB

# Security
SECRET_KEY=your_secret_key_here
ALLOWED_HOSTS=localhost,127.0.0.1

# Monitoring
PROMETHEUS_PORT=9090
GRAFANA_PORT=3001
```

### AI Model Configuration

The system supports multiple AI models:

- **OpenAI GPT-4**: Requires `OPENAI_API_KEY`
- **Anthropic Claude**: Requires `ANTHROPIC_API_KEY`
- **Local Models**: Configure Ollama or similar local model servers

## 📚 Usage

### 1. Document Upload

- Navigate to the Documents page
- Drag and drop files or click to upload
- Supported formats: PDF, DOCX, TXT
- Documents are automatically processed and indexed

### 2. Search Documents

- Use the Search page for semantic search
- Enter natural language queries
- Results show relevance scores and source documents
- Filter by schema type (EU ESRS/CSRD, UK SRD)

### 3. Ask Questions (RAG)

- Go to the RAG page
- Select your preferred AI model
- Ask questions about sustainability reporting
- Get AI-generated answers with source citations

### 4. Generate Reports

- Upload client requirements on the Reports page
- Select a report template
- Generate comprehensive sustainability reports
- Download as professional PDF documents

## 🧪 Testing

### Run Backend Tests

```bash
cd backend

# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run integration tests
python run_integration_tests.py

# Run performance benchmarks
pytest tests/test_performance_benchmarks.py -v
```

### Run Frontend Tests

```bash
cd frontend-simple

# Run tests
npm test

# Run with coverage
npm run test:coverage
```

### Validate System Setup

```bash
# Validate backend setup
python validate_setup.py

# Validate integration test framework
python backend/validate_integration_tests.py

# Run demo integration tests
python backend/demo_integration_tests.py
```

## 📊 Monitoring

The system includes comprehensive monitoring:

- **Prometheus**: Metrics collection (http://localhost:9090)
- **Grafana**: Dashboards and visualization (http://localhost:3001)
- **Health Checks**: Automated system health monitoring
- **Performance Metrics**: Response times, throughput, error rates

### Default Grafana Credentials
- Username: `admin`
- Password: `admin` (change on first login)

## 🚀 Deployment

### Development Environment

```bash
docker-compose -f docker-compose.dev.yml up -d
```

### Staging Environment

```bash
docker-compose -f docker-compose.yml up -d
```

### Production Environment

```bash
docker-compose -f docker-compose.prod.yml up -d
```

### Deployment Scripts

```bash
# Deploy to development
./scripts/deploy-dev.sh

# Deploy to staging
./scripts/deploy-staging.sh

# Deploy to production
./scripts/deploy-prod.sh
```

## 📖 Documentation

- **API Documentation**: Available at `/docs` when running the backend
- **User Guide**: See `docs/USER_GUIDE.md`
- **Deployment Guide**: See `docs/DEPLOYMENT_GUIDE.md`
- **API Reference**: See `docs/API_DOCUMENTATION.md`

## 🔒 Security

- Environment-based configuration
- API key management
- Input validation and sanitization
- Rate limiting
- CORS configuration
- Secure file upload handling

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Issues**: Report bugs and request features via GitHub Issues
- **Documentation**: Check the `docs/` directory for detailed guides
- **Health Check**: Use `/health` endpoint to verify system status

## 🏆 Performance

- **Bundle Size**: 50KB (frontend)
- **Cold Start**: <100ms
- **Search Response**: <2s
- **RAG Response**: <5s
- **Document Processing**: <30s (medium documents)

## 🔄 System Requirements

### Minimum Requirements
- **CPU**: 2 cores
- **RAM**: 4GB
- **Storage**: 10GB
- **Network**: Broadband internet for AI model APIs

### Recommended Requirements
- **CPU**: 4+ cores
- **RAM**: 8GB+
- **Storage**: 50GB+ SSD
- **Network**: High-speed internet for optimal AI model performance

---

**Built with ❤️ for sustainability reporting professionals**# CSRD-RAG-SYSTEM
# CSRD-RAG-SYSTEM
