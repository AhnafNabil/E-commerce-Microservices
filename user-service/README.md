# User Service - Breakdown

The User Service is a FastAPI-based microservice responsible for user management, authentication, and authorization using JWT tokens and PostgreSQL as the database.

![alt text](../images/user-service.svg)

## **Project Structure**

```
user-service/
├── .env                          # Environment variables
├── Dockerfile                    # Container configuration
├── docker-compose.yml           # Local development setup
├── requirements.txt             # Python dependencies
├── README.md                   # Service documentation
└── app/
    ├── __init__.py
    ├── main.py                 # FastAPI application entry point
    ├── api/                    # API layer
    │   ├── __init__.py
    │   ├── dependencies.py     # Authentication & database dependencies
    │   └── routes/
    │       ├── __init__.py
    │       ├── auth.py         # Authentication endpoints
    │       └── users.py        # User management endpoints
    ├── core/                   # Core functionality
    │   ├── __init__.py
    │   ├── config.py           # Application settings
    │   └── security.py         # JWT & password utilities
    ├── db/                     # Database layer
    │   ├── __init__.py
    │   └── postgresql.py       # Database connection & setup
    └── models/                 # Data models
        ├── __init__.py
        └── user.py             # User & Address models
```

## **1. Configuration (.env & config.py)**

### **Environment Variables (.env)**

```bash
# Database
DATABASE_URL=postgresql://postgres:postgres@postgres-user:5432/user_db

# API Settings
API_PREFIX=/api/v1
DEBUG=False
PORT=8003

# JWT Security
JWT_SECRET_KEY=your-super-secret-key-here-change-it-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Password Security
SECURITY_PASSWORD_SALT=your-password-salt-change-it
SECURITY_PASSWORD_HASH=bcrypt
```

### **Settings Class (core/config.py)**

```python
class Settings(BaseSettings):
    # API settings
    API_PREFIX: str = "/api/v1"
    DEBUG: bool = False
    PROJECT_NAME: str = "User Service"
    PORT: int = 8003
    
    # Database settings
    DATABASE_URL: PostgresDsn
    
    # JWT settings
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Security
    SECURITY_PASSWORD_SALT: str
    SECURITY_PASSWORD_HASH: str = "bcrypt"
```

## **2. Database Layer (db/postgresql.py)**

### **Database Setup**
- **Engine**: SQLAlchemy async engine with asyncpg driver
- **Sessions**: Async session factory for database operations
- **Connection**: Converts sync PostgreSQL URL to async format

### **Key Functions**
```python
async def initialize_db():
    """Initialize database with required tables."""
    # Creates all tables if they don't exist

async def close_db_connection():
    """Close database connection."""
    # Properly dispose of database connections

async def get_db():
    """Dependency for getting an async database session."""
    # Yields database session for API endpoints
```

## **3. Data Models (models/user.py)**

### **SQLAlchemy Database Models**

#### **User Table**

```python
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationship with addresses
    addresses = relationship("Address", back_populates="user", cascade="all, delete-orphan")
```

#### **Address Table**

```python
class Address(Base):
    __tablename__ = "addresses"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Address fields
    line1 = Column(String, nullable=False)
    line2 = Column(String, nullable=True)
    city = Column(String, nullable=False)
    state = Column(String, nullable=False)
    postal_code = Column(String, nullable=False)
    country = Column(String, nullable=False)
    is_default = Column(Boolean, nullable=False, default=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationship with user
    user = relationship("User", back_populates="addresses")
```

### **Pydantic API Models**

#### **User Models**
- **UserCreate**: Registration data with password validation
- **UserUpdate**: Optional fields for profile updates
- **UserResponse**: Complete user data for API responses
- **UserLogin**: Login credentials
- **UserChangePassword**: Current + new password for changes

#### **Address Models**
- **AddressCreate**: New address data
- **AddressUpdate**: Optional fields for address updates
- **AddressResponse**: Complete address data for API responses

#### **Authentication Models**
- **Token**: JWT token response (access + refresh tokens)
- **TokenData**: Parsed token data
- **TokenPayload**: JWT payload structure

## **4. Security Layer (core/security.py)**

### **Password Security**
```python
# Password hashing with salt
def get_password_hash(password: str) -> str:
    return pwd_context.hash(password + settings.SECURITY_PASSWORD_SALT)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password + settings.SECURITY_PASSWORD_SALT, hashed_password)
```

### **JWT Token Management**
```python
def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    # Creates JWT access token with 30-minute expiry
    to_encode.update({"exp": expire, "type": "access"})

def create_refresh_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    # Creates JWT refresh token with 7-day expiry
    to_encode.update({"exp": expire, "type": "refresh"})

def verify_token(token: str, token_type: str) -> Optional[Dict[str, Any]]:
    # Verifies token signature and checks token type
```

## **5. Authentication Dependencies (api/dependencies.py)**

### **Key Functions**
```python
async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    # Database query to find user by email

async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
    # Database query to find user by ID

async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)) -> User:
    # Extracts user from JWT token
    # Validates token and checks user exists and is active
    # Returns User object for authenticated endpoints
```

## **6. API Routes**

### **Authentication Routes (api/routes/auth.py)**

#### **POST /api/v1/auth/register**
- **Purpose**: Register new user
- **Validation**: 
  - Email uniqueness check
  - Password strength validation (uppercase, lowercase, digit)
- **Process**:
  1. Check if email already exists
  2. Hash password with salt
  3. Create user record
  4. Return user data (without password)

#### **POST /api/v1/auth/login**
- **Purpose**: User login with OAuth2 compatible flow
- **Input**: Username (email) + password
- **Process**:
  1. Verify user exists and is active
  2. Verify password
  3. Create access token (30 min) + refresh token (7 days)
  4. Return both tokens

#### **POST /api/v1/auth/refresh**
- **Purpose**: Refresh expired access token
- **Input**: Refresh token
- **Process**:
  1. Verify refresh token validity
  2. Check user still exists and is active
  3. Generate new access + refresh tokens
  4. Return new tokens

### **User Management Routes (api/routes/users.py)**

#### **GET /api/v1/users/me**
- **Purpose**: Get current user profile
- **Authentication**: Required (JWT token)
- **Returns**: User data + all addresses

#### **PUT /api/v1/users/me**
- **Purpose**: Update current user profile
- **Authentication**: Required
- **Updatable**: first_name, last_name, phone
- **Process**: Updates only provided fields

#### **PUT /api/v1/users/me/password**
- **Purpose**: Change user password
- **Authentication**: Required
- **Validation**: 
  - Verify current password
  - Validate new password strength
- **Process**: Hash and update new password

#### **Address Management Endpoints**

**GET /api/v1/users/me/addresses**
- Returns all addresses for current user

**POST /api/v1/users/me/addresses**
- Create new address
- Auto-sets as default if it's the first address
- Handles default address switching

**GET /api/v1/users/me/addresses/{address_id}**
- Get specific address (ownership verified)

#### **GET /api/v1/users/{user_id}/verify**
- **Purpose**: Verify user exists (for other services)
- **Authentication**: Not required (inter-service)
- **Returns**: User validity status

## **7. Application Entry Point (main.py)**

### **FastAPI Application Setup**
```python
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="User Service API",
    version="1.0.0",
    openapi_url=f"{settings.API_PREFIX}/openapi.json",
    docs_url=f"{settings.API_PREFIX}/docs",
    redoc_url=f"{settings.API_PREFIX}/redoc",
)

# CORS middleware for cross-origin requests
app.add_middleware(CORSMiddleware, ...)

# Route registration
app.include_router(auth.router, prefix=settings.API_PREFIX)
app.include_router(users.router, prefix=settings.API_PREFIX)

# Lifecycle events
app.add_event_handler("startup", initialize_db)
app.add_event_handler("shutdown", close_db_connection)

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "user-service"}
```

## **8. Containerization**

### **Dockerfile**

```Dockerfile
FROM python:3.10-slim

WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ app/

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8003"]
```

- **Base**: Python 3.10-slim
- **Dependencies**: Installs system packages (build-essential, libpq-dev)
- **App**: Copies requirements → installs → copies app code
- **Runtime**: Uvicorn server on port 8003