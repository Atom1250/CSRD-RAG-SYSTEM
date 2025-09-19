#!/bin/bash

# CSRD RAG System Frontend Setup Script

echo "🚀 Setting up CSRD RAG System Frontend..."

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 16+ first."
    exit 1
fi

# Check Node.js version
NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 16 ]; then
    echo "❌ Node.js version 16+ is required. Current version: $(node -v)"
    exit 1
fi

echo "✅ Node.js version: $(node -v)"

# Install dependencies
echo "📦 Installing dependencies..."
npm install

if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies"
    exit 1
fi

# Install additional testing dependencies
echo "🧪 Installing testing dependencies..."
npm install --save-dev jest-axe

if [ $? -ne 0 ]; then
    echo "⚠️  Warning: Failed to install jest-axe. Accessibility tests may not work."
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "⚙️  Creating environment configuration..."
    cp .env.example .env
    echo "✅ Created .env file. Please update it with your API endpoint."
else
    echo "✅ Environment configuration already exists."
fi

# Run tests to verify setup
echo "🧪 Running tests to verify setup..."
npm test -- --run --passWithNoTests

if [ $? -eq 0 ]; then
    echo "✅ Setup completed successfully!"
    echo ""
    echo "🎉 Next steps:"
    echo "   1. Update .env with your API endpoint"
    echo "   2. Start development server: npm start"
    echo "   3. Open http://localhost:3000 in your browser"
else
    echo "⚠️  Setup completed with test warnings. Check the output above."
fi