.PHONY: help install dev docker-up docker-down docker-logs test clean

help:
	@echo "BOOM Wizard Engine - Available commands:"
	@echo ""
	@echo "  make install       Install dependencies"
	@echo "  make dev           Run development server"
	@echo "  make docker-up     Start all services with Docker"
	@echo "  make docker-down   Stop all Docker services"
	@echo "  make docker-logs   View Docker logs"
	@echo "  make test          Run tests"
	@echo "  make clean         Clean up temporary files"
	@echo ""

install:
	@echo "Installing dependencies..."
	pip install -r requirements.txt

dev:
	@echo "Starting development server..."
	python -m app.main

docker-up:
	@echo "Starting services with Docker Compose..."
	docker-compose up -d
	@echo "✅ Services started!"
	@echo "   - API: http://localhost:8000"
	@echo "   - Docs: http://localhost:8000/docs"

docker-down:
	@echo "Stopping Docker services..."
	docker-compose down

docker-logs:
	docker-compose logs -f wizard_engine

test:
	@echo "Running tests..."
	pytest -v

test-coverage:
	@echo "Running tests with coverage..."
	pytest --cov=app --cov-report=html tests/
	@echo "Coverage report: htmlcov/index.html"

clean:
	@echo "Cleaning up..."
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache htmlcov .coverage
	@echo "✅ Cleanup complete"

format:
	@echo "Formatting code..."
	black app/ tests/
	isort app/ tests/

lint:
	@echo "Linting code..."
	flake8 app/ tests/ --max-line-length=120
	mypy app/

redis-cli:
	redis-cli

redis-flush:
	@echo "⚠️  Flushing Redis database..."
	redis-cli FLUSHALL
	@echo "✅ Redis flushed"
