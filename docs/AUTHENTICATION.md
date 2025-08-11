# Docugent - Complete Setup & Authentication Guide

This comprehensive guide covers the complete setup of the Docugent application with JWT authentication, role-based authorization, Docker deployment, and cloud database integration.

## Table of Contents

1. [Project Overview](#project-overview)
2. [Prerequisites](#prerequisites)
3. [Quick Start](#quick-start)
4. [Authentication System](#authentication-system)
5. [Docker Deployment](#docker-deployment)
6. [Cloud Database Setup](#cloud-database-setup)
7. [API Documentation](#api-documentation)
8. [Security Configuration](#security-configuration)
9. [Development Guide](#development-guide)
10. [Troubleshooting](#troubleshooting)

## Project Overview

Docugent is an AI-powered agent system designed for API Conference management, featuring:

- **JWT Authentication**: Secure access/refresh token system
- **Role-based Authorization**: Admin, Moderator, User roles
- **FastAPI Backend**: High-performance Python web framework
- **React Frontend**: Modern TypeScript-based UI
- **Docker Deployment**: Container-based deployment
- **Cloud Database**: PostgreSQL cloud database support
- **Poetry Management**: Modern Python dependency management

### Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   React UI      │────▶│   FastAPI       │────▶│  PostgreSQL     │
│   (TypeScript)  │     │   Backend       │     │  Database       │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                 │
                                 ▼
                        ┌─────────────────┐
                        │   AI Agents     │
                        │   & Tools       │
                        └─────────────────┘
```

## Prerequisites

### System Requirements

- **Python**: 3.10+
- **Node.js**: 18+ (for frontend)
- **Docker**: 20.10+ and Docker Compose
- **Git**: For version control

### Cloud Database Account

Choose one of these cloud PostgreSQL providers:

- [Supabase](https://supabase.com) (Recommended - Free tier available)
- [Railway](https://railway.app)
- [Neon](https://neon.tech)
- AWS RDS
- DigitalOcean Managed Database
- Heroku Postgres

## Quick Start

### 1. Clone and Setup

```bash
# Clone repository
git clone <repository-url>
cd docugent

# Install Poetry (if not installed)
curl -sSL https://install.python-poetry.org | python3 -

# Create clean virtual environment
poetry env use python3
poetry install
```

### 2. Environment Configuration

```bash
# Copy environment template
cp env.example .env

# Edit .env file with your configuration
nano .env
```

**Required Environment Variables:**

```env
# Database (Required)
DATABASE_URL=postgresql://user:password@host:port/database

# JWT Security (Required)
SECRET_KEY=your-super-secret-key-here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Google Services (Required for AI features)
GOOGLE_API_KEY=your-google-api-key

# Optional Settings
DEBUG=false
LOG_LEVEL=INFO
```

### 3. Quick Development Start

```bash
# Run database migrations
poetry run alembic upgrade head

# Initialize database with default data
poetry run python scripts/init_db.py

# Start development server
poetry run python main.py
```

### 4. Quick Docker Start

```bash
# Start all services with Docker
docker-compose up --build
```

**Default Admin Credentials:**

- Email: `admin@apiconf.com`
- Password: `admin123!@#`

⚠️ **Important**: Change default password immediately after first login!

## Authentication System

### Architecture Overview

The authentication system implements JWT-based authentication with role-based authorization:

#### Database Schema

```sql
-- Role definitions
CREATE TABLE roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    permissions JSONB,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Public user information
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    phone_number VARCHAR(20),
    is_active BOOLEAN DEFAULT true,
    is_verified BOOLEAN DEFAULT false,
    role_id INTEGER REFERENCES roles(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Private authentication data (one-to-one with users)
CREATE TABLE auth (
    id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    hashed_password VARCHAR(255) NOT NULL,
    salt VARCHAR(255) NOT NULL,
    refresh_token TEXT,
    refresh_token_expires_at TIMESTAMP,
    failed_login_attempts INTEGER DEFAULT 0,
    last_login_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Token blacklist for logout/revocation
CREATE TABLE token_blacklist (
    id SERIAL PRIMARY KEY,
    token_jti VARCHAR(255) UNIQUE NOT NULL,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    blacklisted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL
);
```

#### Relationships

- **User ↔ Role**: Many-to-One (many users can have the same role)
- **User ↔ Auth**: One-to-One (each user has one auth record)
- **Auth data is never exposed** in API responses

### Security Features

#### Password Security

- **bcrypt hashing** with unique salt per user
- **Strong password validation**
- **Failed login attempt tracking**

#### JWT Tokens

- **Access tokens**: Short-lived (30 minutes default)
- **Refresh tokens**: Long-lived (7 days default)
- **Token blacklisting**: Secure logout implementation
- **JTI (JWT ID)**: Unique identifier for each token

#### Role-based Access Control

- **Admin**: Full system access, user management, role management
- **Moderator**: Limited admin access, user viewing and updating
- **User**: Basic access, own profile management

### API Authentication Endpoints

All authentication endpoints are under `/api/v1/auth`:

#### Registration

```bash
POST /api/v1/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePass123!",
  "first_name": "John",
  "last_name": "Doe",
  "role_id": 3
}
```

#### Login

```bash
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePass123!"
}

# Response:
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 1800,
  "user": {
    "id": 1,
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "role": "user"
  }
}
```

#### Refresh Token

```bash
POST /api/v1/auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

#### Logout

```bash
POST /api/v1/auth/logout
Authorization: Bearer <access_token>
```

#### Protected Endpoint Access

```bash
GET /api/v1/auth/me
Authorization: Bearer <access_token>
```

## Docker Deployment

### Docker Architecture

The application uses a multi-service Docker setup:

```yaml
services:
  backend: # FastAPI application
  frontend: # React application
  csv-updater: # Scheduled data updates
```

### Docker Configuration

The `docker-compose.yml` is configured for cloud database deployment:

```yaml
version: "3.8"

services:
  backend:
    build:
      context: .
      dockerfile: docker/Dockerfile
      target: backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - SECRET_KEY=${SECRET_KEY}
      - GOOGLE_API_KEY=${GOOGLE_API_KEY}
    env_file:
      - .env

  frontend:
    build:
      context: ./frontend
      dockerfile: ../docker/nginx/Dockerfile
    ports:
      - "3000:80"
    depends_on:
      - backend

  csv-updater:
    build:
      context: .
      dockerfile: docker/Dockerfile
      target: csv-updater
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - GOOGLE_API_KEY=${GOOGLE_API_KEY}
    env_file:
      - .env
```

### Deployment Steps

1. **Configure Environment:**

   ```bash
   cp env.example .env
   # Edit .env with your cloud database URL and secrets
   ```

2. **Build and Start:**

   ```bash
   docker-compose up --build
   ```

3. **Verify Deployment:**
   ```bash
   curl http://localhost:8000/api/v1/agents/health
   ```

### Docker Environment Variables

The application automatically loads environment variables from:

- `.env` file
- Docker environment variables
- System environment variables

### Database Initialization

The Docker setup includes automatic database initialization:

1. **Migration**: Runs Alembic migrations
2. **Seed Data**: Creates default roles and admin user
3. **Health Check**: Verifies database connectivity

## Cloud Database Setup

### Supported Providers

#### 🚀 Supabase (Recommended)

```bash
# Get from Supabase Dashboard > Settings > Database
DATABASE_URL=postgresql://postgres:[password]@[host]:5432/postgres?sslmode=require
```

**Setup Steps:**

1. Create account at [supabase.com](https://supabase.com)
2. Create new project
3. Go to Settings > Database
4. Copy connection string
5. Add to `.env` file

#### ⚡ Neon

```bash
DATABASE_URL=postgresql://[user]:[password]@[host]/[dbname]?sslmode=require
```

#### 🚄 Railway

```bash
DATABASE_URL=postgresql://postgres:[password]@[host]:5432/railway
```

#### ☁️ AWS RDS

```bash
DATABASE_URL=postgresql://[username]:[password]@[rds-endpoint]:5432/[dbname]
```

### Security Configuration

#### SSL Requirements

Most cloud providers require SSL connections:

```bash
DATABASE_URL=postgresql://user:pass@host:port/db?sslmode=require
```

#### Connection Pooling

For production environments:

```bash
DATABASE_URL=postgresql://user:pass@host:port/db?max_connections=20&min_connections=5
```

#### IP Whitelisting

- Add your server's IP to database firewall rules
- For Docker deployment, ensure container network can reach external hosts

## API Documentation

### Complete API Reference

#### Authentication Endpoints (`/api/v1/auth`)

| Method | Endpoint           | Description           | Auth Required | Role Required |
| ------ | ------------------ | --------------------- | ------------- | ------------- |
| POST   | `/register`        | Register new user     | No            | None          |
| POST   | `/login`           | User login            | No            | None          |
| POST   | `/refresh`         | Refresh access token  | No            | None          |
| POST   | `/logout`          | Logout user           | Yes           | Any           |
| GET    | `/me`              | Get current user info | Yes           | Any           |
| POST   | `/change-password` | Change password       | Yes           | Any           |

#### Role Management (`/api/v1/roles`)

| Method | Endpoint     | Description     | Auth Required | Role Required |
| ------ | ------------ | --------------- | ------------- | ------------- |
| POST   | `/`          | Create role     | Yes           | Admin         |
| GET    | `/`          | Get all roles   | Yes           | User+         |
| GET    | `/{role_id}` | Get single role | Yes           | User+         |
| PUT    | `/{role_id}` | Update role     | Yes           | Admin         |
| DELETE | `/{role_id}` | Delete role     | Yes           | Admin         |

#### User Management (`/api/v1/users`)

| Method | Endpoint                | Description      | Auth Required | Role Required   |
| ------ | ----------------------- | ---------------- | ------------- | --------------- |
| GET    | `/`                     | Get all users    | Yes           | Moderator+      |
| GET    | `/{user_id}`            | Get user         | Yes           | Self/Moderator+ |
| PUT    | `/{user_id}`            | Update user      | Yes           | Self/Moderator+ |
| PATCH  | `/{user_id}/activate`   | Activate user    | Yes           | Admin           |
| PATCH  | `/{user_id}/deactivate` | Deactivate user  | Yes           | Admin           |
| PATCH  | `/{user_id}/role`       | Change user role | Yes           | Admin           |

#### Agent Endpoints (`/api/v1/agents`)

| Method | Endpoint         | Description       | Auth Required | Role Required |
| ------ | ---------------- | ----------------- | ------------- | ------------- |
| GET    | `/health`        | Health check      | No            | None          |
| POST   | `/chat`          | Send chat message | Yes           | User+         |
| GET    | `/sessions`      | Get user sessions | Yes           | User+         |
| DELETE | `/sessions/{id}` | Delete session    | Yes           | User+         |

### Response Formats

#### Success Response

```json
{
  "success": true,
  "data": { ... },
  "message": "Operation completed successfully"
}
```

#### Error Response

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "details": { ... }
  }
}
```

#### Authentication Response

```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 1800,
  "user": {
    "id": 1,
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "role": "user",
    "is_active": true,
    "is_verified": false
  }
}
```

## Security Configuration

### JWT Configuration

#### Secret Key Generation

```bash
# Generate a secure secret key
openssl rand -hex 32
```

#### Token Configuration

```env
# JWT settings
SECRET_KEY=your-256-bit-secret-key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30    # Short-lived
REFRESH_TOKEN_EXPIRE_DAYS=7       # Long-lived
```

### Password Security

#### Password Requirements

- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one number
- At least one special character

#### Implementation

```python
# Password validation regex
PASSWORD_REGEX = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$'
```

### Rate Limiting

#### Implementation Recommendations

```python
# Add to FastAPI app
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Apply to login endpoint
@limiter.limit("5/minute")
async def login(request: Request, ...):
    # Login logic
```

### HTTPS Configuration

#### Production Setup

```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;

    ssl_certificate /path/to/certificate.crt;
    ssl_certificate_key /path/to/private.key;

    location / {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Development Guide

### Project Structure

```
docugent/
├── app/                    # FastAPI application
│   ├── agents/             # AI agents and tools
│   ├── api/                # API routes
│   ├── config/             # Configuration
│   ├── schemas/            # Pydantic models
│   └── services/           # Business logic
├── frontend/               # React application
├── docker/                 # Docker configuration
├── data/                   # Data files
├── scripts/                # Utility scripts
├── tests/                  # Test files
├── alembic/                # Database migrations
├── docs/                   # Documentation
├── pyproject.toml          # Poetry configuration
├── docker-compose.yml      # Docker services
└── .env                    # Environment variables
```

### Development Workflow

#### 1. Local Development Setup

```bash
# Install dependencies
poetry install

# Activate virtual environment
poetry shell

# Run database migrations
poetry run alembic upgrade head

# Initialize database
poetry run python scripts/init_db.py

# Start development server
poetry run python main.py
```

#### 2. Database Management

##### Create Migration

```bash
poetry run alembic revision --autogenerate -m "Add new table"
```

##### Run Migrations

```bash
poetry run alembic upgrade head
```

##### Rollback Migration

```bash
poetry run alembic downgrade -1
```

#### 3. Testing

##### Run Tests

```bash
# Run all tests
poetry run pytest

# Run specific test file
poetry run pytest tests/test_auth.py

# Run with coverage
poetry run pytest --cov=app
```

##### Test Database

Tests use a separate test database configured in `tests/conftest.py`.

#### 4. Code Quality

##### Format Code

```bash
poetry run black .
poetry run isort .
```

##### Lint Code

```bash
poetry run flake8
poetry run mypy app/
```

### Adding New Features

#### 1. Create Database Models

```python
# app/models/new_model.py
from sqlalchemy import Column, Integer, String
from app.database import Base

class NewModel(Base):
    __tablename__ = "new_models"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
```

#### 2. Create Pydantic Schemas

```python
# app/schemas/new_model.py
from pydantic import BaseModel

class NewModelCreate(BaseModel):
    name: str

class NewModelResponse(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True
```

#### 3. Implement Service Layer

```python
# app/services/new_service.py
from app.models.new_model import NewModel
from app.schemas.new_model import NewModelCreate

class NewService:
    async def create(self, data: NewModelCreate) -> NewModel:
        # Implementation
        pass
```

#### 4. Create API Routes

```python
# app/api/v1/new_routes.py
from fastapi import APIRouter, Depends
from app.services.new_service import NewService

router = APIRouter(prefix="/new", tags=["new"])

@router.post("/")
async def create_new(data: NewModelCreate):
    service = NewService()
    return await service.create(data)
```

## Troubleshooting

### Common Issues

#### 1. Database Connection Issues

**Error**: `connection refused`

```bash
# Check database URL
echo $DATABASE_URL

# Test connection
poetry run python -c "import asyncpg; print('Testing connection...')"
```

**Solutions**:

- Verify DATABASE_URL format
- Check firewall settings
- Ensure IP is whitelisted
- Verify SSL requirements

#### 2. Authentication Issues

**Error**: `Invalid credentials`

```bash
# Check user exists
poetry run python scripts/check_user.py admin@apiconf.com

# Reset admin password
poetry run python scripts/reset_admin_password.py
```

**Error**: `Token expired`

```bash
# Check token settings
grep TOKEN .env

# Use refresh token endpoint
curl -X POST /api/v1/auth/refresh -d '{"refresh_token": "..."}'
```

#### 3. Docker Issues

**Error**: `Container exits immediately`

```bash
# Check logs
docker-compose logs backend

# Debug container
docker-compose run backend bash
```

**Error**: `Port already in use`

```bash
# Check processes using port
sudo lsof -i :8000

# Kill process
sudo kill -9 <PID>
```

#### 4. Environment Variable Issues

**Error**: `Environment variable not found`

```bash
# Check .env file
cat .env

# Verify Docker loads .env
docker-compose config
```

#### 5. Poetry Issues

**Error**: `Poetry not found`

```bash
# Install Poetry
curl -sSL https://install.python-poetry.org | python3 -

# Add to PATH
export PATH="$HOME/.local/bin:$PATH"
```

**Error**: `Dependency conflicts`

```bash
# Clear cache
poetry cache clear pypi --all

# Reinstall dependencies
poetry install --no-cache
```

### Debugging Tools

#### 1. Health Check Endpoint

```bash
curl http://localhost:8000/api/v1/agents/health
```

#### 2. Database Console

```bash
# Connect to database
poetry run python scripts/db_console.py
```

#### 3. Log Analysis

```bash
# View application logs
docker-compose logs -f backend

# Check specific service
docker-compose logs csv-updater
```

#### 4. Token Debugging

```bash
# Decode JWT token (without verification)
poetry run python scripts/decode_token.py <token>
```

### Performance Optimization

#### 1. Database Optimization

- Enable connection pooling
- Add database indexes
- Use read replicas for heavy queries

#### 2. Caching

- Implement Redis for session storage
- Cache frequently accessed data
- Use CDN for static assets

#### 3. Monitoring

- Set up application monitoring
- Monitor database performance
- Track API response times

### Support and Resources

#### Documentation

- FastAPI: https://fastapi.tiangolo.com/
- SQLAlchemy: https://docs.sqlalchemy.org/
- Alembic: https://alembic.sqlalchemy.org/
- Poetry: https://python-poetry.org/docs/

#### Community

- FastAPI Discord
- Python Discord
- Stack Overflow

---

## Conclusion

This comprehensive guide covers all aspects of setting up and deploying the Docugent application. The authentication system provides enterprise-grade security with JWT tokens and role-based access control, while the Docker deployment ensures scalability and consistency across environments.

For additional support or questions, please refer to the troubleshooting section or reach out to the development team.

**Security Reminder**: Always use HTTPS in production, change default passwords, and regularly rotate secret keys.
