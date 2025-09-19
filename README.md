# PGwallah - Microservices PG Management Platform

A scalable, microservices-based PG (Paying Guest) management platform built for the Indian market with FastAPI, Next.js, Kong Gateway, and AWS deployment.

## Features

- **Multi-tenant PG Management**: Room booking, rent collection, mess management
- **UPI-first Payments**: Razorpay integration with UPI intents and subscriptions
- **Mess Management**: Attendance tracking, meal-wise coupons, on-demand food orders
- **GST-ready Invoicing**: Monthly invoices with Indian tax compliance
- **Real-time Notifications**: SMS via Gupshup DLT, Email via AWS SES
- **Admin Dashboards**: Property management, tenant oversight, financial tracking

## Architecture

Microservices architecture with:
- **API Gateway**: Kong with rate limiting, CORS, request transformation
- **Services**: Auth, Booking, Payment, Invoicing, Mess, Orders, Notification
- **Databases**: PostgreSQL per service with Redis caching
- **Messaging**: RabbitMQ for event-driven communication
- **Storage**: S3/MinIO for files and receipts
- **Observability**: Prometheus, Grafana, Loki for metrics and logs

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Make
- Node.js 18+ (for frontend development)
- Python 3.11+ (for service development)

### Local Development

```bash
# Clone the repository
git clone https://github.com/your-org/pgwallah.git
cd pgwallah

# Start the complete stack
make up

# Initialize databases and seed data
make init-db
make seed

# View services
open http://localhost:8000/api/auth/health   # Auth API via Kong
open http://localhost:3000                   # Next.js Frontend
open http://localhost:8001                   # Kong Admin
open http://localhost:3001                   # Grafana (admin/admin)
open http://localhost:9001                   # MinIO Console (minioadmin/minioadmin)
```

### Available Services

| Service | Port | API Path | Description |
|---------|------|----------|-------------|
| Auth Service | 8010 | `/api/auth` | JWT authentication, user management |
| Booking Service | 8020 | `/api/booking` | Room availability, reservations |
| Payment Service | 8030 | `/api/payments` | Razorpay integration, billing |
| Invoicing Service | 8040 | `/api/invoices` | Monthly invoices, PDF generation |
| Mess Service | 8050 | `/api/mess` | Attendance, coupons, menu |
| Orders Service | 8060 | `/api/orders` | Food ordering, kitchen console |
| Notification Service | 8070 | `/api/notify` | SMS, Email notifications |

### Development Commands

```bash
# Container management
make up            # Start all services
make down          # Stop all services
make logs          # View all logs
make restart       # Restart services

# Database operations
make init-db       # Run migrations for all services
make reset-db      # Reset all databases
make seed          # Seed development data

# Testing
make test          # Run all tests
make test-auth     # Test specific service
make integration   # Integration tests
make e2e          # End-to-end tests

# Development
make dev-auth      # Develop auth service with hot reload
make dev-frontend  # Start Next.js dev server
```

## Project Structure

```
pgwallah/
├── services/                 # Microservices
│   ├── auth/                # Authentication service
│   ├── booking/             # Room booking service
│   ├── payment/             # Payment & billing service
│   ├── invoicing/           # Invoice generation service
│   ├── mess/                # Mess attendance & coupons
│   ├── orders/              # Food ordering service
│   └── notification/        # Notification service
├── frontend/                # Next.js web application
├── gateway/                 # Kong API Gateway config
├── docs/                    # API documentation
│   ├── api/                 # OpenAPI specifications
│   └── events/              # Event schemas
├── infra/                   # Infrastructure as Code
│   ├── terraform/           # AWS resources
│   └── k8s/                 # Kubernetes manifests
├── observability/           # Monitoring configs
├── tests/                   # Test suites
│   ├── integration/         # Integration tests
│   ├── e2e/                 # End-to-end tests
│   └── performance/         # Load tests
└── docker-compose.yml       # Local development stack
```

## Technology Stack

### Backend
- **Framework**: FastAPI with async/await
- **Database**: PostgreSQL per service
- **Caching**: Redis
- **Message Queue**: RabbitMQ
- **Object Storage**: MinIO (local), S3 (production)
- **Authentication**: JWT with RSA256

### Frontend
- **Framework**: Next.js 14 with React
- **Styling**: Tailwind CSS
- **State Management**: React Query + Zustand
- **Forms**: React Hook Form + Zod validation

### Infrastructure
- **API Gateway**: Kong
- **Container Runtime**: Docker + Docker Compose (local), EKS (production)
- **Monitoring**: Prometheus + Grafana + Loki
- **CI/CD**: GitHub Actions
- **Cloud**: AWS (ap-south-1 Mumbai)

### Integrations
- **Payments**: Razorpay (UPI, Cards, Net Banking)
- **SMS**: Gupshup with DLT compliance
- **Email**: AWS SES
- **Storage**: AWS S3
- **CDN**: CloudFront

## Environment Configuration

Copy environment files and configure:

```bash
# Service configurations
cp services/auth/.env.example services/auth/.env
cp services/payment/.env.example services/payment/.env
# ... configure each service

# Frontend configuration  
cp frontend/.env.example frontend/.env.local
```

## API Documentation

- OpenAPI specs: `docs/api/`
- Interactive docs: http://localhost:8000/docs (via Kong)
- Postman collection: `tests/postman/`

## Deployment

### Staging/Production on AWS EKS

```bash
# Configure AWS CLI and kubectl
aws configure
aws eks update-kubeconfig --region ap-south-1 --name pgwallah-cluster

# Deploy infrastructure
cd infra/terraform
terraform init && terraform apply

# Deploy services
cd ../../
make deploy-staging
make test-staging
make deploy-production
```

## Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/your-feature`
3. Run tests: `make test`
4. Submit pull request

## License

MIT License - see [LICENSE](LICENSE) file for details.