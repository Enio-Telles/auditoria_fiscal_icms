# Microservices Architecture - Auditoria Fiscal ICMS

## Overview

This directory contains the microservices architecture implementation for the Auditoria Fiscal ICMS system. The system has been decomposed into specialized services for better scalability, maintainability, and deployment flexibility.

## Architecture

### Services

1. **API Gateway** (Port 8000)
   - Central entry point for all client requests
   - Handles routing, authentication, and load balancing
   - Forwards requests to appropriate microservices

2. **Authentication Service** (Port 8001)
   - User authentication and JWT token management
   - User registration and login
   - Token validation

3. **Tenant Service** (Port 8002)
   - Multi-tenant configuration and isolation
   - Tenant settings management
   - Schema creation and management

4. **Product Service** (Port 8003)
   - Product CRUD operations
   - Product classification management
   - Tenant-specific product isolation

5. **Classification Service** (Port 8004)
   - AI-powered product classification
   - Integration with multiple LLM providers
   - Classification strategy management

6. **Import Service** (Port 8005)
   - Data import and processing
   - Excel/CSV file handling
   - Bulk operations

7. **AI Service** (Port 8006)
   - LLM integration (Ollama, OpenAI, Anthropic)
   - AI model management
   - RAG (Retrieval-Augmented Generation) operations

### Shared Components

- **Database Configuration**: Multi-tenant PostgreSQL setup
- **Authentication**: JWT-based authentication with role-based access
- **Logging**: Centralized logging configuration
- **Models**: Common data models and schemas

## Setup and Installation

### Option 1: Conda Environment (Recommended for Development)

1. **Setup Environment**:
   ```bash
   setup_microservices_conda.bat
   ```

2. **Start Services in Development Mode**:
   ```bash
   start_microservices_dev.bat
   ```

### Option 2: Docker Compose (Recommended for Production)

1. **Start All Services**:
   ```bash
   start_microservices.bat
   ```

   Or manually:
   ```bash
   cd microservices
   docker-compose up --build
   ```

## Environment Variables

Each service can be configured with the following environment variables:

### Database
- `DATABASE_URL`: PostgreSQL connection string
- Default: `postgresql://postgres:admin@localhost:5432/auditoria_fiscal_icms`

### Authentication
- `SECRET_KEY`: JWT secret key
- `ACCESS_TOKEN_EXPIRE_MINUTES`: Token expiration time (default: 30)

### Service URLs (for API Gateway)
- `AUTH_SERVICE_URL`: Authentication service URL
- `TENANT_SERVICE_URL`: Tenant service URL
- `PRODUCT_SERVICE_URL`: Product service URL
- `CLASSIFICATION_SERVICE_URL`: Classification service URL
- `IMPORT_SERVICE_URL`: Import service URL
- `AI_SERVICE_URL`: AI service URL

## API Endpoints

### API Gateway (http://localhost:8000)

#### Health Check
- `GET /health` - Check status of all services

#### Authentication (Proxied)
- `POST /auth/login` - User login
- `POST /auth/register` - User registration

#### Protected Routes (Require JWT Token)
- `GET|POST|PUT|DELETE /tenant/{path}` - Tenant operations
- `GET|POST|PUT|DELETE /product/{path}` - Product operations
- `GET|POST|PUT|DELETE /classification/{path}` - Classification operations
- `GET|POST|PUT|DELETE /import/{path}` - Import operations
- `GET|POST|PUT|DELETE /ai/{path}` - AI operations

### Authentication Service (http://localhost:8001)

- `POST /register` - Register new user
- `POST /login` - Authenticate user
- `GET /me` - Get current user info
- `POST /validate-token` - Validate JWT token

### Tenant Service (http://localhost:8002)

- `POST /tenants` - Create new tenant
- `GET /tenants` - List all tenants
- `GET /tenants/{tenant_id}` - Get tenant info
- `PUT /tenants/{tenant_id}` - Update tenant
- `GET /tenants/{tenant_id}/settings` - Get tenant settings

## Authentication Flow

1. **User Registration/Login**:
   ```http
   POST /auth/login
   {
     "username": "user@example.com",
     "password": "password"
   }
   ```

2. **Get JWT Token**:
   ```json
   {
     "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
     "token_type": "bearer"
   }
   ```

3. **Use Token in Requests**:
   ```http
   Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
   ```

## Multi-Tenant Architecture

- Each tenant has isolated data using PostgreSQL schemas
- Tenant ID is embedded in JWT tokens
- Services automatically route to correct tenant schema
- Database schemas are created automatically: `tenant_{tenant_id}`

## Development

### Adding New Services

1. Create service directory: `microservices/{service-name}/`
2. Implement `main.py` with FastAPI application
3. Add to `docker-compose.yml`
4. Update API Gateway routing
5. Add service URL to environment variables

### Database Migrations

Services create their own tables on startup using SQLAlchemy. For production, consider implementing proper migration scripts.

### Logging

All services use structured logging with the following format:
```
timestamp - service_name - level - function:line - message
```

## Production Considerations

### Security
- Change default SECRET_KEY
- Use environment variables for sensitive data
- Implement rate limiting
- Add HTTPS/TLS termination

### Scalability
- Use container orchestration (Kubernetes)
- Implement service discovery
- Add load balancers
- Consider message queues for async operations

### Monitoring
- Add health checks for each service
- Implement distributed tracing
- Set up monitoring and alerting
- Add metrics collection

### Database
- Use connection pooling
- Implement read replicas
- Consider database per service pattern
- Add backup and recovery procedures

## Troubleshooting

### Common Issues

1. **Service Connection Errors**:
   - Check if PostgreSQL is running
   - Verify database connection strings
   - Ensure all services are started

2. **Authentication Errors**:
   - Verify JWT token format
   - Check token expiration
   - Ensure SECRET_KEY consistency

3. **Port Conflicts**:
   - Check if ports 8000-8006 are available
   - Modify port assignments in configuration

### Logs
- Check individual service logs in terminal windows
- For Docker: `docker-compose logs -f {service-name}`

## Migration from Monolithic Architecture

The microservices maintain compatibility with the existing frontend and database structure while providing:

- Better separation of concerns
- Independent service scaling
- Easier testing and deployment
- Improved fault isolation
- Technology diversity support

Services can be gradually migrated and deployed independently without affecting the overall system functionality.
