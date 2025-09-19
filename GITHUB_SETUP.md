# 📋 GitHub Setup Instructions

Follow these steps to set up the CSRD RAG System on GitHub and clone it to run locally.

## 🔧 Setting Up on GitHub

### Step 1: Create a New GitHub Repository

1. **Go to GitHub**: Visit https://github.com
2. **Create Repository**: Click the "+" icon → "New repository"
3. **Repository Settings**:
   - **Name**: `csrd-rag-system` (or your preferred name)
   - **Description**: "AI-powered CSRD sustainability reporting system with RAG capabilities"
   - **Visibility**: Choose Public or Private
   - **Initialize**: ✅ Add a README file
   - **Add .gitignore**: Choose "Python" template
   - **License**: Choose "MIT License"

### Step 2: Clone Your New Repository

```bash
# Clone your empty repository
git clone https://github.com/YOUR_USERNAME/csrd-rag-system.git
cd csrd-rag-system
```

### Step 3: Add the CSRD RAG System Files

You have two options:

#### Option A: Copy Files from Current Directory

If you have the files locally:

```bash
# Copy all files from your current CSRD RAG directory
cp -r /path/to/current/csrd-rag-system/* .
cp -r /path/to/current/csrd-rag-system/.* . 2>/dev/null || true

# Add all files to git
git add .
git commit -m "Initial commit: Complete CSRD RAG System implementation"
git push origin main
```

#### Option B: Download and Set Up Fresh

If you want to start fresh:

```bash
# Remove the default README
rm README.md

# Create the project structure
mkdir -p backend/{app/{api,core,models,services,tasks,middleware,utils},tests,data/schemas}
mkdir -p frontend-simple/{src/{services,styles},public}
mkdir -p frontend/{src/{components,contexts,pages,services,utils},public}
mkdir -p docs
mkdir -p scripts
mkdir -p monitoring/{prometheus,grafana/provisioning/datasources}
mkdir -p nginx

# You'll need to recreate all the files from your implementation
# This is more work, so Option A is recommended if you have the files
```

### Step 4: Set Up Repository Settings

1. **Go to your repository on GitHub**
2. **Settings → General**:
   - Set default branch to `main`
   - Enable "Allow merge commits"
   - Enable "Allow squash merging"

3. **Settings → Security**:
   - Enable "Dependency graph"
   - Enable "Dependabot alerts"
   - Enable "Dependabot security updates"

### Step 5: Add Repository Secrets (for CI/CD)

If you plan to use GitHub Actions:

1. **Go to Settings → Secrets and variables → Actions**
2. **Add these secrets**:
   - `OPENAI_API_KEY`: Your OpenAI API key
   - `ANTHROPIC_API_KEY`: Your Anthropic API key
   - `POSTGRES_PASSWORD`: Database password
   - `SECRET_KEY`: Application secret key

## 🚀 Cloning and Running

### For New Users (Cloning from GitHub)

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/csrd-rag-system.git
cd csrd-rag-system

# Follow the Quick Start guide
cp .env.example .env
# Edit .env with your API keys and settings

# Start with Docker
docker-compose -f docker-compose.dev.yml up -d

# Access the application
open http://localhost:3000
```

### For Contributors

```bash
# Fork the repository on GitHub first, then:
git clone https://github.com/YOUR_USERNAME/csrd-rag-system.git
cd csrd-rag-system

# Add upstream remote
git remote add upstream https://github.com/ORIGINAL_OWNER/csrd-rag-system.git

# Create a feature branch
git checkout -b feature/your-feature-name

# Make changes, commit, and push
git add .
git commit -m "Add your feature"
git push origin feature/your-feature-name

# Create a Pull Request on GitHub
```

## 📁 Repository Structure

Your GitHub repository should have this structure:

```
csrd-rag-system/
├── README.md                 # Main documentation
├── QUICK_START.md           # Quick start guide
├── LICENSE                  # MIT license
├── .gitignore              # Git ignore rules
├── .env.example            # Environment template
├── docker-compose.yml      # Docker configuration
├── docker-compose.dev.yml  # Development environment
├── docker-compose.prod.yml # Production environment
├── Dockerfile              # Docker build instructions
├── backend/                # Python FastAPI backend
├── frontend-simple/        # Vanilla TypeScript frontend
├── frontend/              # React frontend (alternative)
├── docs/                  # Documentation
├── scripts/               # Deployment scripts
├── monitoring/            # Prometheus & Grafana
├── nginx/                 # Nginx configuration
└── .kiro/                 # Kiro IDE specs (optional)
```

## 🔒 Security Best Practices

### Environment Variables

Never commit sensitive data to GitHub:

```bash
# ❌ Never commit these files:
.env
.env.local
.env.production

# ✅ Always commit these:
.env.example
.env.template
```

### API Keys

Store API keys securely:

1. **Local Development**: Use `.env` file (gitignored)
2. **GitHub Actions**: Use repository secrets
3. **Production**: Use environment variables or secret management

### Database Passwords

Use strong, unique passwords:

```bash
# Generate a secure password
openssl rand -base64 32
```

## 🔄 GitHub Actions (Optional)

Create `.github/workflows/ci.yml` for automated testing:

```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:14
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        cd backend
        pip install -r requirements.txt
    
    - name: Run tests
      run: |
        cd backend
        pytest
      env:
        DATABASE_URL: postgresql://postgres:postgres@localhost:5432/test_db
        OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
```

## 📊 Repository Analytics

Enable GitHub's built-in analytics:

1. **Insights → Traffic**: Monitor clones and views
2. **Insights → Contributors**: Track contributions
3. **Insights → Community**: Check community health
4. **Security → Advisories**: Monitor security issues

## 🏷️ Releases and Tags

Create releases for major versions:

```bash
# Create and push a tag
git tag -a v1.0.0 -m "Initial release"
git push origin v1.0.0

# GitHub will automatically create a release
```

## 📝 Documentation

Keep these files updated:

- `README.md`: Main project documentation
- `QUICK_START.md`: Getting started guide
- `CHANGELOG.md`: Version history
- `CONTRIBUTING.md`: Contribution guidelines
- `docs/`: Detailed documentation

## 🤝 Collaboration

Set up collaboration features:

1. **Issues**: Enable issue templates
2. **Pull Requests**: Set up PR templates
3. **Discussions**: Enable for community questions
4. **Wiki**: For detailed documentation
5. **Projects**: For project management

## ✅ Verification Checklist

Before sharing your repository:

- [ ] All sensitive data removed from git history
- [ ] `.env.example` file created with all required variables
- [ ] README.md is comprehensive and up-to-date
- [ ] .gitignore includes all necessary patterns
- [ ] License file is present
- [ ] Repository description and topics are set
- [ ] All tests pass in CI/CD
- [ ] Documentation is complete

---

**🎉 Your CSRD RAG System is now ready on GitHub!**

Share the repository URL with others, and they can follow the Quick Start guide to get it running locally.