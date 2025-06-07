#!/bin/bash

echo "🚀 Starting Web Crawler Application..."

# Check if dependencies are installed
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    ./install.sh
fi

# Create environment file if missing
if [ ! -f "frontend/.env.local" ]; then
    echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > frontend/.env.local
fi

echo "🎯 Starting services..."
echo "   Frontend: http://localhost:3000"
echo "   Backend: http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop"

npm run dev
