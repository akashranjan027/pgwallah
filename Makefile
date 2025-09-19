.PHONY: help up down logs restart status clean
.PHONY: init-db reset-db seed migrate
.PHONY: test test-auth test-booking test-payment test-invoicing test-mess test-orders test-notification
.PHONY: integration e2e performance
.PHONY: dev-auth dev-booking dev-payment dev-invoicing dev-mess dev-orders dev-notification dev-frontend
.PHONY: build push deploy-staging deploy-production
.PHONY: lint format security-scan

# Default target
help:
	@echo "PGwallah Development Commands"
	@echo "============================"
	@echo ""
	@echo "Container Management:"
	@echo "  up              Start all services with docker-compose"
	@echo "  down            Stop all services"
	@echo "  logs            View logs from all services"
	@echo "  restart         Restart all services"
	@echo "  status          Show status of all containers"
	@echo "  clean           Remove containers, volumes, and networks"
	@echo ""
	@echo "Database Operations:"
	@echo "  init-db         Initialize databases and run migrations"
	@echo "  reset-db        Reset all databases (destructive)"
	@echo "  seed            Seed development data"
	@echo "  migrate         Run pending migrations for all services"
	@echo ""
	@echo "Testing:"
	@echo "  test            Run all unit tests"
	@echo "  test-SERVICE    Run tests for specific service"
	@echo "  integration     Run integration tests"
	@echo "  e2e             Run end-to-end tests"
	@echo "  performance     Run performance tests"
	@echo ""
	@echo "Development:"
	@echo "  dev-SERVICE     Start service in development mode"
	@echo "  dev-frontend    Start Next.js development server"
	@echo ""
	@echo "Code Quality:"
	@echo "  lint            Run linters on all services"
	@echo "  format          Format code in all services"
	@echo "  security-scan   Run security scans"
	@echo ""
	@echo "Deployment:"
	@echo "  build           Build all Docker images"
	@echo "  push            Push images to ECR"
	@echo "  deploy-staging  Deploy to staging environment"
	@echo "  deploy-production Deploy to production environment"

# Container Management
up:
	@echo "🚀 Starting PGwallah stack..."
	docker-compose up -d
	@echo "✅ Stack started. Services available at:"
	@echo "   - API Gateway: http://localhost:8000"
	@echo "   - Frontend: http://localhost:3000"
	@echo "   - Kong Admin: http://localhost:8001"
	@echo "   - Grafana: http://localhost:3001 (admin/admin)"
	@echo "   - RabbitMQ: http://localhost:15672 (guest/guest)"
	@echo "   - MinIO Console: http://localhost:9001 (minioadmin/minioadmin)"

down:
	@echo "🛑 Stopping PGwallah stack..."
	docker-compose down

logs:
	docker-compose logs -f

restart:
	@echo "🔄 Restarting PGwallah stack..."
	docker-compose restart

status:
	@echo "📊 Container Status:"
	docker-compose ps

clean:
	@echo "🧹 Cleaning up containers, volumes, and networks..."
	docker-compose down -v --remove-orphans
	docker system prune -f

# Database Operations
init-db:
	@echo "🗄️  Initializing databases..."
	@echo "Running migrations for Auth service..."
	docker-compose exec auth alembic upgrade head || echo "Auth migrations failed"
	@echo "Running migrations for Booking service..."
	docker-compose exec booking alembic upgrade head || echo "Booking migrations failed"
	@echo "Running migrations for Payment service..."
	docker-compose exec payment alembic upgrade head || echo "Payment migrations failed"
	@echo "Running migrations for Invoicing service..."
	docker-compose exec invoicing alembic upgrade head || echo "Invoicing migrations failed"
	@echo "Running migrations for Mess service..."
	docker-compose exec mess alembic upgrade head || echo "Mess migrations failed"
	@echo "Running migrations for Orders service..."
	docker-compose exec orders alembic upgrade head || echo "Orders migrations failed"
	@echo "Running migrations for Notification service..."
	docker-compose exec notification alembic upgrade head || echo "Notification migrations failed"
	@echo "✅ Database initialization complete"

reset-db:
	@echo "⚠️  Resetting all databases (destructive operation)..."
	@read -p "Are you sure? Type 'yes' to continue: " confirm && [ "$$confirm" = "yes" ] || exit 1
	docker-compose down
	docker volume rm pgwallah_postgres-auth-data pgwallah_postgres-booking-data pgwallah_postgres-payment-data pgwallah_postgres-invoicing-data pgwallah_postgres-mess-data pgwallah_postgres-orders-data pgwallah_postgres-notification-data 2>/dev/null || true
	docker-compose up -d postgres-auth postgres-booking postgres-payment postgres-invoicing postgres-mess postgres-orders postgres-notification
	@echo "Waiting for databases to be ready..."
	sleep 10
	$(MAKE) init-db

seed:
	@echo "🌱 Seeding development data..."
	docker-compose exec auth python scripts/seed_dev.py
	docker-compose exec booking python scripts/seed_dev.py
	docker-compose exec mess python scripts/seed_dev.py
	@echo "✅ Development data seeded"

migrate:
	@echo "🔄 Running pending migrations..."
	$(MAKE) init-db

# Testing
test:
	@echo "🧪 Running all unit tests..."
	docker-compose exec auth pytest tests/ -v
	docker-compose exec booking pytest tests/ -v
	docker-compose exec payment pytest tests/ -v
	docker-compose exec invoicing pytest tests/ -v
	docker-compose exec mess pytest tests/ -v
	docker-compose exec orders pytest tests/ -v
	docker-compose exec notification pytest tests/ -v

test-auth:
	docker-compose exec auth pytest tests/ -v

test-booking:
	docker-compose exec booking pytest tests/ -v

test-payment:
	docker-compose exec payment pytest tests/ -v

test-invoicing:
	docker-compose exec invoicing pytest tests/ -v

test-mess:
	docker-compose exec mess pytest tests/ -v

test-orders:
	docker-compose exec orders pytest tests/ -v

test-notification:
	docker-compose exec notification pytest tests/ -v

integration:
	@echo "🔗 Running integration tests..."
	docker-compose -f docker-compose.yml -f docker-compose.test.yml run --rm integration-tests

e2e:
	@echo "🎭 Running end-to-end tests..."
	cd tests/e2e && npm test

performance:
	@echo "⚡ Running performance tests..."
	cd tests/performance && k6 run smoke-test.js

# Development
dev-auth:
	@echo "🚀 Starting Auth service in development mode..."
	cd services/auth && uvicorn app.main:app --reload --host 0.0.0.0 --port 8010

dev-booking:
	@echo "🚀 Starting Booking service in development mode..."
	cd services/booking && uvicorn app.main:app --reload --host 0.0.0.0 --port 8020

dev-payment:
	@echo "🚀 Starting Payment service in development mode..."
	cd services/payment && uvicorn app.main:app --reload --host 0.0.0.0 --port 8030

dev-invoicing:
	@echo "🚀 Starting Invoicing service in development mode..."
	cd services/invoicing && uvicorn app.main:app --reload --host 0.0.0.0 --port 8040

dev-mess:
	@echo "🚀 Starting Mess service in development mode..."
	cd services/mess && uvicorn app.main:app --reload --host 0.0.0.0 --port 8050

dev-orders:
	@echo "🚀 Starting Orders service in development mode..."
	cd services/orders && uvicorn app.main:app --reload --host 0.0.0.0 --port 8060

dev-notification:
	@echo "🚀 Starting Notification service in development mode..."
	cd services/notification && uvicorn app.main:app --reload --host 0.0.0.0 --port 8070

dev-frontend:
	@echo "🚀 Starting Next.js development server..."
	cd frontend && npm run dev

# Code Quality
lint:
	@echo "🔍 Running linters..."
	docker-compose exec auth flake8 app/ tests/
	docker-compose exec booking flake8 app/ tests/
	docker-compose exec payment flake8 app/ tests/
	docker-compose exec invoicing flake8 app/ tests/
	docker-compose exec mess flake8 app/ tests/
	docker-compose exec orders flake8 app/ tests/
	docker-compose exec notification flake8 app/ tests/
	cd frontend && npm run lint

format:
	@echo "💄 Formatting code..."
	docker-compose exec auth black app/ tests/
	docker-compose exec booking black app/ tests/
	docker-compose exec payment black app/ tests/
	docker-compose exec invoicing black app/ tests/
	docker-compose exec mess black app/ tests/
	docker-compose exec orders black app/ tests/
	docker-compose exec notification black app/ tests/
	cd frontend && npm run format

security-scan:
	@echo "🔒 Running security scans..."
	docker-compose exec auth safety check
	docker-compose exec booking safety check
	docker-compose exec payment safety check
	docker-compose exec invoicing safety check
	docker-compose exec mess safety check
	docker-compose exec orders safety check
	docker-compose exec notification safety check
	cd frontend && npm audit

# Deployment
build:
	@echo "🏗️  Building Docker images..."
	docker-compose build

push:
	@echo "📤 Pushing images to ECR..."
	./scripts/push-to-ecr.sh

deploy-staging:
	@echo "🚢 Deploying to staging environment..."
	./scripts/deploy-staging.sh

deploy-production:
	@echo "🚀 Deploying to production environment..."
	./scripts/deploy-production.sh