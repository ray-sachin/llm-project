.PHONY: help setup install-backend install-frontend run-backend run-frontend run-all stop clean build-docker push-docker deploy-docker

# Default target
help:
	@echo "LLM Deployment Platform - Development Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make setup              - Complete setup for development"
	@echo "  make install-backend    - Install Python dependencies"
	@echo "  make install-frontend   - Install Node dependencies"
	@echo ""
	@echo "Development:"
	@echo "  make run-backend        - Start backend server"
	@echo "  make run-frontend       - Start frontend dev server"
	@echo "  make run-all            - Start backend + frontend"
	@echo ""
	@echo "Docker:"
	@echo "  make build-docker       - Build Docker image"
	@echo "  make run-docker         - Run with Docker Compose"
	@echo "  make stop-docker        - Stop Docker containers"
	@echo "  make push-docker        - Push image to registry"
	@echo "  make deploy-docker      - Deploy container"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean              - Remove node_modules, venv, cache"
	@echo "  make stop               - Stop all running services"

# Setup
setup: install-backend install-frontend
	@echo "✅ Setup complete! Run 'make run-all' to start development"

install-backend:
	@echo "📦 Installing Python dependencies..."
	python -m venv venv
	. venv/bin/activate && pip install --upgrade pip && pip install -r requirements.txt
	@echo "✅ Backend dependencies installed"

install-frontend:
	@echo "📦 Installing Node dependencies..."
	cd frontend && npm install
	@echo "✅ Frontend dependencies installed"

# Development
run-backend:
	@echo "🚀 Starting backend server..."
	. venv/bin/activate && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

run-frontend:
	@echo "🚀 Starting frontend dev server..."
	cd frontend && npm run dev

run-all:
	@echo "🚀 Starting all services..."
	@echo "Backend will run on http://localhost:8000"
	@echo "Frontend will run on http://localhost:5173"
	@echo "Press Ctrl+C to stop"
	@sh -c 'trap "echo 'Stopping services...'; exit" INT; \
		(. venv/bin/activate && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000) & \
		(cd frontend && npm run dev) & \
		wait'

# Docker
build-docker:
	@echo "🐳 Building Docker image..."
	docker build -t llm-platform:latest .
	@echo "✅ Docker image built"

run-docker:
	@echo "🐳 Starting Docker containers..."
	docker-compose up

run-docker-detached:
	@echo "🐳 Starting Docker containers (detached)..."
	docker-compose up -d
	@echo "✅ Containers running in background"

stop-docker:
	@echo "🛑 Stopping Docker containers..."
	docker-compose down

logs-docker:
	@echo "📋 Showing Docker logs..."
	docker-compose logs -f

push-docker:
	@echo "📤 Pushing Docker image..."
	docker push llm-platform:latest
	@echo "✅ Image pushed"

# Cleanup
stop:
	@echo "🛑 Stopping all services..."
	pkill -f "uvicorn" || true
	pkill -f "vite" || true
	@echo "✅ Services stopped"

clean:
	@echo "🧹 Cleaning up..."
	rm -rf venv/
	rm -rf frontend/node_modules/
	rm -rf frontend/dist/
	rm -rf app/__pycache__/
	rm -rf .pytest_cache/
	rm -rf *.pyc
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@echo "✅ Cleanup complete"

clean-all: clean
	rm -rf .env
	@echo "✅ Full cleanup including .env"

# Development helpers
lint-backend:
	@echo "🔍 Linting Python code..."
	. venv/bin/activate && pip install flake8 && flake8 app/
	@echo "✅ Linting complete"

lint-frontend:
	@echo "🔍 Linting TypeScript..."
	cd frontend && npm run lint
	@echo "✅ Linting complete"

type-check:
	@echo "✅ Type checking..."
	cd frontend && npm run type-check
	@echo "✅ Type check complete"

test-backend:
	@echo "🧪 Running backend tests..."
	. venv/bin/activate && pytest app/ -v
	@echo "✅ Tests complete"

# Diagnostics
status:
	@echo "📊 Checking service status..."
	@curl -s http://localhost:8000/health && echo "✅ Backend running" || echo "❌ Backend not responding"
	@curl -s http://localhost:5173 && echo "✅ Frontend running" || echo "❌ Frontend not responding"

env-check:
	@echo "🔍 Checking environment..."
	@test -f .env && echo "✅ .env file exists" || echo "❌ .env file missing"
	@python --version && echo "✅ Python installed" || echo "❌ Python not found"
	@node --version && echo "✅ Node installed" || echo "❌ Node not found"
	@docker --version && echo "✅ Docker installed" || echo "❌ Docker not found"

# Documentation
docs:
	@echo "📚 Opening documentation..."
	@which open >/dev/null && open http://localhost:8000/docs || echo "📖 API docs at http://localhost:8000/docs"

version:
	@grep -oP '"version":\s*"\K[^"]+' frontend/package.json
