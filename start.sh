#!/bin/bash
# Quick start script for BOOM Wizard Engine

echo "🚀 Starting BOOM Wizard Engine..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "📝 Creating .env from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env with your API keys before continuing!"
    echo "   Required: OPENAI_API_KEY (or other LLM provider key)"
    exit 1
fi

# Check if Docker is available
if command -v docker-compose &> /dev/null; then
    echo "🐳 Starting with Docker Compose..."
    docker-compose up -d
    echo "✅ Services started!"
    echo "   - API: http://localhost:8000"
    echo "   - Docs: http://localhost:8000/docs"
    echo "   - Redis: localhost:6379"
    echo ""
    echo "📊 View logs: docker-compose logs -f wizard_engine"
    echo "🛑 Stop: docker-compose down"
else
    echo "🐍 Starting with Python..."
    
    # Check if venv exists
    if [ ! -d "venv" ]; then
        echo "Creating virtual environment..."
        python -m venv venv
    fi
    
    # Activate venv
    source venv/bin/activate
    
    # Install dependencies
    echo "Installing dependencies..."
    pip install -r requirements.txt
    
    # Check Redis
    if ! command -v redis-cli &> /dev/null; then
        echo "⚠️  Redis not found. Please install and start Redis:"
        echo "   - macOS: brew install redis && brew services start redis"
        echo "   - Linux: sudo apt-get install redis-server"
        exit 1
    fi
    
    if ! redis-cli ping &> /dev/null; then
        echo "⚠️  Redis is not running. Starting Redis..."
        redis-server --daemonize yes
    fi
    
    # Start the application
    echo "🚀 Starting API server..."
    python -m app.main
fi
