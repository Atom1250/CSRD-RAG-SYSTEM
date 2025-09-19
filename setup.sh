#!/bin/bash

# CSRD RAG System Setup Script
echo "Setting up CSRD RAG System..."

# Create Python virtual environment
echo "Creating Python virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install backend dependencies
echo "Installing backend dependencies..."
cd backend
pip install -r requirements.txt
cd ..

# Create necessary directories
echo "Creating data directories..."
mkdir -p data/documents
mkdir -p data/schemas
mkdir -p data/chroma_db

# Copy environment configuration
if [ ! -f .env ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "Please update .env file with your actual configuration values"
fi

echo "Setup complete!"
echo ""
echo "To start the development server:"
echo "1. Activate the virtual environment: source venv/bin/activate"
echo "2. Start the backend server: cd backend && python main.py"
echo ""
echo "Make sure to:"
echo "- Update .env file with your database and API keys"
echo "- Install and configure PostgreSQL and Redis"
echo "- Set up your vector database (Chroma is configured by default)"