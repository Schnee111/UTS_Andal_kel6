#!/bin/bash

echo "🚀 Installing Web Crawler Project..."

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    exit 1
fi

# Check Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is required but not installed."
    exit 1
fi

# Install root dependencies
echo "📦 Installing root dependencies..."
npm install

# Install backend dependencies
echo "🐍 Installing backend dependencies..."
cd backend
pip install -r requirements.txt
cd ..

# Install frontend dependencies
echo "⚛️ Installing frontend dependencies..."
cd frontend
npm install
cd ..

# Create directories
echo "📁 Creating directories..."
mkdir -p backend/logs
mkdir -p backend/database
mkdir -p backend/config

# Setup environment
echo "⚙️ Setting up environment..."
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > frontend/.env.local

echo "✅ Installation completed!"
echo ""
echo "🎯 To start the application:"
echo "   npm run dev"
echo ""
echo "🌐 URLs:"
echo "   Frontend: http://localhost:3000"
echo "   Backend API: http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
