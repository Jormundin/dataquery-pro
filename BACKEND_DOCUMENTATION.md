# Backend Documentation - Corporate Database Interface API

## Overview
A FastAPI-based backend service that provides secure API endpoints for corporate database access. Designed to bridge the gap between Oracle databases and frontend applications, offering authentication, query building, and data management capabilities.

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- Oracle Database (11g or higher)
- Oracle Instant Client
- Administrative access to target databases

### Installation
```bash
cd database-backend
pip install -r requirements.txt
python main.py
```

The API will be available at `http://localhost:8000`

## 📁 Project Structure

```
database-backend/
├── main.py                    # FastAPI application entry point
├── database.py               # Database connection and session management
├── models.py                 # Pydantic models for request/response
├── auth.py                   # Authentication and authorization
├── query_builder.py          # SQL query generation and validation
├── requirements.txt          # Python dependencies
├── test_connection.py        # Database connection testing utility
├── test_table_access.py      # Table access testing utility
├── start_server.bat          # Windows startup script
├── start_corporate.bat       # Corporate deployment script
├── QUICK_START.md           # Quick start guide
└── README.md                # Detailed documentation
```

## 🎯 Core Features

### 1. Database Management
- **Multi-Database Support**: Connect to multiple Oracle instances
- **Connection Pooling**: Efficient connection management
- **Health Monitoring**: Real-time database status checking
- **Schema Discovery**: Automatic table and column detection
- **Transaction Management**: Proper commit/rollback handling

### 2. Authentication & Security
- **JWT Token Authentication**: Secure API access
- **Role-Based Access Control**: User permissions management
- **Database User Mapping**: Map API users to database accounts
- **Audit Logging**: Track all database operations
- **Rate Limiting**: Prevent API abuse

### 3. Query Builder
- **Visual Query Generation**: Convert frontend filters to SQL
- **SQL Validation**: Prevent injection and syntax errors
- **Query Optimization**: Automatic query performance tuning
- **Result Pagination**: Handle large datasets efficiently
- **Export Capabilities**: CSV, JSON, Excel formats

### 4. Data Operations
- **CRUD Operations**: Create, Read, Update, Delete
- **Bulk Operations**: Handle multiple records efficiently
- **Data Validation**: Ensure data integrity
- **Type Conversion**: Automatic data type handling
- **Error Handling**: Comprehensive error reporting

## 🛠 Technical Architecture

### Framework Stack
- **FastAPI**: Modern, fast web framework
- **cx_Oracle**: Oracle database connectivity
- **SQLAlchemy**: Database ORM and connection pooling
- **Pydantic**: Data validation and serialization
- **JWT**: Authentication token management

### Database Integration
```python
# Oracle connection configuration
DATABASE_CONFIG = {
    "host": "localhost",
    "port": 1521,
    "service_name": "ORCLPDB1",
    "username": "hr",
    "password": "password"
}
```

### API Architecture
- **RESTful Design**: Standard HTTP methods and status codes
- **Async Support**: Non-blocking request handling
- **Auto-Documentation**: Swagger/OpenAPI integration
- **CORS Configuration**: Cross-origin request support
- **Error Standardization**: Consistent error response format

## 🔐 Security Implementation

### Authentication Flow
1. **User Login**: POST `/auth/login` with credentials
2. **Token Generation**: JWT token with expiration
3. **Token Validation**: Middleware validates all requests
4. **Database Access**: Map authenticated user to DB user

### Security Measures
```python
# JWT Configuration
JWT_SECRET_KEY = "your-secret-key"
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

# Password hashing
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
```

### Database Security
- **Connection Encryption**: SSL/TLS for database connections
- **Credential Management**: Secure storage of database credentials
- **Query Sanitization**: Prevent SQL injection attacks
- **Access Control**: Table-level and column-level permissions

## 📊 API Endpoints

### Authentication Endpoints
```
POST   /auth/login           # User authentication
POST   /auth/refresh         # Token refresh
POST   /auth/logout          # User logout
GET    /auth/me             # Current user info
```

### Database Management
```
GET    /databases           # List available databases
POST   /databases           # Add new database connection
GET    /databases/{db_id}   # Get database details
PUT    /databases/{db_id}   # Update database connection
DELETE /databases/{db_id}   # Remove database connection
GET    /databases/{db_id}/status  # Check database status
```

### Schema Discovery
```
GET    /databases/{db_id}/tables     # List tables
GET    /databases/{db_id}/tables/{table}/columns  # Table columns
GET    /databases/{db_id}/tables/{table}/info     # Table metadata
```

### Query Operations
```
POST   /query/build         # Build SQL from visual filters
POST   /query/execute       # Execute SQL query
GET    /query/history       # Query execution history
POST   /query/validate      # Validate SQL syntax
POST   /query/explain       # Get query execution plan
```

### Data Operations
```
GET    /data/{table}        # Get table data with pagination
POST   /data/{table}        # Insert new records
PUT    /data/{table}/{id}   # Update specific record
DELETE /data/{table}/{id}   # Delete specific record
POST   /data/{table}/bulk   # Bulk operations
GET    /data/{table}/export # Export data (CSV, JSON)
```

### Analytics & Monitoring
```
GET    /stats/overview      # Database statistics
GET    /stats/performance   # Performance metrics
GET    /stats/usage         # Usage statistics
GET    /health              # System health check
```

## 🔧 Configuration

### Environment Variables
Create `.env` file:
```bash
# Database Configuration
DB_HOST=localhost
DB_PORT=1521
DB_SERVICE_NAME=ORCLPDB1
DB_USERNAME=hr
DB_PASSWORD=password

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_ENVIRONMENT=development

# Security
JWT_SECRET_KEY=your-super-secret-jwt-key
JWT_EXPIRATION_HOURS=24

# Oracle Client
ORACLE_CLIENT_PATH=C:\oracle\instantclient_21_8
```

### Database Setup
```sql
-- Create API user
CREATE USER api_user IDENTIFIED BY secure_password;
GRANT CONNECT, RESOURCE TO api_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON hr.employees TO api_user;

-- Create audit table
CREATE TABLE audit_log (
    id NUMBER PRIMARY KEY,
    user_id VARCHAR2(50),
    action VARCHAR2(20),
    table_name VARCHAR2(50),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 🚀 Deployment

### Development Environment
```bash
# Install dependencies
pip install -r requirements.txt

# Run with auto-reload
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Or use the provided script
start_server.bat
```

### Production Deployment

#### Docker Deployment
```dockerfile
FROM python:3.9-slim

# Install Oracle Instant Client
RUN apt-get update && apt-get install -y \
    libaio1 \
    unzip \
    wget

# Copy Oracle Instant Client
COPY instantclient_21_8 /opt/oracle/instantclient_21_8

# Set environment variables
ENV LD_LIBRARY_PATH=/opt/oracle/instantclient_21_8
ENV ORACLE_HOME=/opt/oracle/instantclient_21_8

# Install Python dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy application
COPY . /app
WORKDIR /app

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### Gunicorn Production Server
```bash
# Install gunicorn
pip install gunicorn

# Run with multiple workers
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

#### Systemd Service
```ini
[Unit]
Description=Database Interface API
After=network.target

[Service]
Type=notify
User=api
Group=api
WorkingDirectory=/opt/database-backend
ExecStart=/opt/database-backend/venv/bin/gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

## 🐛 Troubleshooting

### Common Issues

#### Oracle Client Issues
**Issue**: `DPI-1047: Cannot locate a 64-bit Oracle Client library`
**Solution**: 
```bash
# Download Oracle Instant Client
# Set environment variables
set ORACLE_CLIENT_PATH=C:\oracle\instantclient_21_8
set PATH=%PATH%;%ORACLE_CLIENT_PATH%
```

#### Connection Issues
**Issue**: `ORA-12514: TNS:listener does not currently know of service`
**Solution**: 
```python
# Use IP address instead of hostname
# Check service name in tnsnames.ora
# Verify listener is running
```

#### Performance Issues
**Issue**: Slow query execution
**Solution**:
```python
# Enable connection pooling
engine = create_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=30,
    pool_recycle=3600
)
```

#### Memory Issues
**Issue**: High memory usage with large datasets
**Solution**:
```python
# Implement streaming for large results
async def stream_results(query):
    async with engine.begin() as conn:
        result = await conn.stream(text(query))
        async for row in result:
            yield row
```

### Debugging Tools

#### Connection Testing
```bash
python test_connection.py
```

#### Table Access Testing
```bash
python test_table_access.py
```

#### API Testing
```bash
# Test health endpoint
curl http://localhost:8000/health

# Test with authentication
curl -H "Authorization: Bearer your-jwt-token" \
     http://localhost:8000/databases
```

## 📊 Monitoring and Logging

### Logging Configuration
```python
import logging
from logging.handlers import RotatingFileHandler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler('api.log', maxBytes=10485760, backupCount=5),
        logging.StreamHandler()
    ]
)
```

### Performance Monitoring
```python
# Add middleware for request timing
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    logger.info(f"Path: {request.url.path} - Time: {process_time:.4f}s")
    return response
```

### Health Checks
```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "database": await check_database_connection(),
        "timestamp": datetime.utcnow().isoformat()
    }
```

## 🔄 Development Workflow

### Code Standards
- **PEP 8**: Python style guide compliance
- **Type Hints**: Use type annotations for better code clarity
- **Docstrings**: Document all functions and classes
- **Error Handling**: Comprehensive exception handling

### Testing
```bash
# Install testing dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html
```

### Database Migrations
```python
# Using Alembic for database migrations
from alembic import command
from alembic.config import Config

def run_migrations():
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")
```

## 📈 Performance Optimization

### Query Optimization
- **Indexing Strategy**: Proper database indexing
- **Query Caching**: Cache frequently used queries
- **Connection Pooling**: Reuse database connections
- **Async Operations**: Non-blocking database operations

### Scaling Considerations
- **Horizontal Scaling**: Multiple API instances
- **Load Balancing**: Distribute requests across instances
- **Database Clustering**: Oracle RAC for high availability
- **Caching Layer**: Redis for session and query caching

## 🔒 Security Best Practices

### API Security
- **Input Validation**: Validate all input parameters
- **SQL Injection Prevention**: Use parameterized queries
- **Rate Limiting**: Prevent API abuse
- **HTTPS Only**: Enforce SSL/TLS in production

### Database Security
- **Least Privilege**: Grant minimum required permissions
- **Audit Logging**: Track all database operations
- **Encryption**: Encrypt sensitive data at rest
- **Regular Updates**: Keep Oracle patches current

## 📞 Support and Maintenance

### Regular Maintenance
- **Log Analysis**: Monitor application logs
- **Performance Monitoring**: Track API response times
- **Database Maintenance**: Regular Oracle maintenance tasks
- **Security Updates**: Apply security patches promptly

### Backup Strategy
- **Database Backups**: Regular Oracle RMAN backups
- **Configuration Backups**: Backup environment files
- **Code Repository**: Regular Git commits and tags

---

**Version**: 1.0.0  
**Last Updated**: December 2024  
**Maintainer**: Development Team  
**Oracle Compatibility**: 11g, 12c, 19c, 21c 