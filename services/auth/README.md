# PGwallah Auth Service

Authentication and user management service for the PGwallah platform.

## Features

- JWT-based authentication with RS256 signing
- User registration and login
- Role-based access control (tenant, admin, staff)
- Password complexity validation
- Account lockout protection
- Token refresh mechanism
- User profile management
- Prometheus metrics and structured logging
- Health check endpoints

## Quick Start

### Development Setup

1. **Install dependencies:**
   ```bash
   cd services/auth
   poetry install
   ```

2. **Set up environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Run database migrations:**
   ```bash
   poetry run alembic upgrade head
   ```

4. **Start the service:**
   ```bash
   poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8010
   ```

### Docker Development

```bash
# From project root
docker-compose up auth postgres-auth redis
```

## API Endpoints

### Authentication
- `POST /register` - Register new user
- `POST /login` - User login
- `POST /refresh` - Refresh access token
- `GET /.well-known/jwks.json` - JSON Web Key Set

### Profile Management
- `GET /me` - Get current user profile
- `PUT /me` - Update user profile
- `POST /change-password` - Change password

### Health
- `GET /health` - Health check
- `GET /health/liveness` - Kubernetes liveness probe
- `GET /health/readiness` - Kubernetes readiness probe

## Database Schema

### Users Table
- `id` (UUID, PK) - User unique identifier
- `email` (string, unique) - User email address
- `hashed_password` (string) - Bcrypt hashed password
- `full_name` (string) - User's full name
- `phone` (string, optional) - Phone number in +91XXXXXXXXXX format
- `role` (enum) - User role: tenant, admin, staff
- `is_active` (boolean) - Account activation status
- `is_verified` (boolean) - Email verification status
- `login_attempts` (integer) - Failed login attempts counter
- `locked_until` (datetime, optional) - Account lock expiration
- `created_at`, `updated_at` (datetime) - Timestamps

### Tenant Profiles Table
- `id` (UUID, PK) - Profile unique identifier
- `user_id` (UUID, FK) - Reference to users table
- `emergency_contact_name` (string, optional) - Emergency contact name
- `emergency_contact_phone` (string, optional) - Emergency contact phone
- `occupation` (string, optional) - Tenant occupation
- `company` (string, optional) - Employer company
- `id_proof_type` (enum, optional) - aadhaar, pan, passport, driving_license
- `id_proof_number` (string, optional) - ID proof number
- Address fields: `address_line1`, `address_line2`, `city`, `state`, `pincode`
- `created_at`, `updated_at` (datetime) - Timestamps

### Refresh Tokens Table
- `id` (UUID, PK) - Token unique identifier
- `jti` (string, unique) - JWT ID from token payload
- `user_id` (UUID, FK) - Reference to users table
- `is_revoked` (boolean) - Token revocation status
- `expires_at` (datetime) - Token expiration time
- `created_at` (datetime) - Token creation time

## Security Features

### Password Requirements
- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one digit
- At least one special character

### Account Protection
- Maximum 5 failed login attempts
- 15-minute lockout after exceeding attempts
- Automatic unlock after timeout period

### JWT Token Security
- RS256 algorithm with public/private key pairs
- Access tokens expire in 1 hour
- Refresh tokens expire in 30 days
- Token revocation on password change
- JWKS endpoint for public key distribution

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | - |
| `REDIS_URL` | Redis connection string | - |
| `JWT_SECRET_KEY` | JWT signing key | - |
| `JWT_ALGORITHM` | JWT algorithm | RS256 |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | Access token TTL | 60 |
| `JWT_REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token TTL | 30 |
| `MAX_LOGIN_ATTEMPTS` | Max failed logins | 5 |
| `LOGIN_ATTEMPT_TIMEOUT_MINUTES` | Lockout duration | 15 |

## Development

### Database Migrations

```bash
# Create new migration
poetry run alembic revision --autogenerate -m "Description"

# Apply migrations
poetry run alembic upgrade head

# Rollback migration
poetry run alembic downgrade -1
```

### Testing

```bash
# Run unit tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=app --cov-report=html

# Run integration tests
poetry run pytest tests/integration/
```

### Code Quality

```bash
# Format code
poetry run black app/ tests/

# Sort imports
poetry run isort app/ tests/

# Lint code
poetry run flake8 app/ tests/

# Type checking
poetry run mypy app/

# Security scan
poetry run safety check
```

## Monitoring

### Metrics
- HTTP request metrics (count, duration, status codes)
- Database connection health
- Authentication success/failure rates
- Token generation and validation metrics

### Logging
- Structured JSON logging with correlation IDs
- Request/response logging with timing
- Authentication events (login, logout, failures)
- Error tracking with stack traces

### Health Checks
- Database connectivity
- Redis connectivity (if configured)
- Service readiness status

## Production Deployment

### Docker Build
```bash
docker build -t pgwallah/auth:latest .
```

### Kubernetes Deployment
```bash
helm install auth ./k8s/helm/auth-service
```

### Environment Setup
- Use secure JWT signing keys
- Enable TLS in production
- Configure proper CORS origins
- Set up monitoring and alerting
- Use secrets management for sensitive data

## API Documentation

When running in development mode, interactive API documentation is available at:
- Swagger UI: http://localhost:8010/docs
- ReDoc: http://localhost:8010/redoc

## License

MIT License - see [LICENSE](../../LICENSE) file for details.