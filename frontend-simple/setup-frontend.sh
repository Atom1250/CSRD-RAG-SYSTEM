#!/bin/bash

# Frontend Setup Script for CSRD RAG System

echo "🚀 Setting up CSRD RAG System Frontend..."

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed."
    echo "Please install Node.js from https://nodejs.org/ and run this script again."
    exit 1
fi

echo "✅ Node.js version: $(node --version)"
echo "✅ npm version: $(npm --version)"

# Install dependencies
echo "📦 Installing dependencies..."
npm install

# Check if backend is running
echo "🔍 Checking backend connection..."
BACKEND_URL="http://localhost:60145"

if curl -s "$BACKEND_URL/health" > /dev/null; then
    echo "✅ Backend is running on port 60145"
else
    echo "⚠️  Backend is not responding on port 60145"
    echo "Please make sure the backend is running:"
    echo "  cd backend && python3 simple_main.py"
fi

echo "🎉 Frontend setup complete!"
echo ""
echo "To start the frontend development server:"
echo "  npm run dev"
echo ""
echo "The frontend will be available at: http://localhost:3000"