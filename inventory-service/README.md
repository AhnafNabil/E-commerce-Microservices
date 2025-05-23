# Inventory Service - Breakdown

The Inventory Service is a FastAPI-based microservice responsible for managing product stock levels, inventory reservations, and stock tracking in the e-commerce system, using PostgreSQL as the database with comprehensive inventory history tracking.

![alt text](../images/Inventory-service.svg)

## **Project Structure**

```
inventory-service/
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
    │       └── inventory.py    # Inventory management endpoints
    ├── core/                   # Core functionality
    │   ├── __init__.py
    │   ├── config.py           # Application settings
    │   └── logging.py          # Logging configuration
    ├── db/                     # Database layer
    │   ├── __init__.py
    │   └── postgresql.py       # PostgreSQL connection & setup
    ├── models/                 # Data models
    │   ├── __init__.py
    │   └── inventory.py        # Inventory & history models
    └── services/               # External service clients
        └── product.py          # Product service integration
```

## **1. Configuration (.env & config.py)**

### **Environment Variables (.env)**

```bash
# PostgreSQL Configuration
DATABASE_URL=postgresql://postgres:postgres@postgres-inventory:5432/inventory_db

# API Configuration
API_PREFIX=/api/v1
DEBUG=False
PORT=8002

# Service URLs
PRODUCT_SERVICE_URL=http://product-service:8000/api/v1

# Authentication (for testing purposes)
SECRET_KEY=your-secret-key-here

# Retry Configuration
MAX_RETRIES=3
RETRY_DELAY=1  # seconds

# Inventory Configuration
LOW_STOCK_THRESHOLD=5
ENABLE_NOTIFICATIONS=true
NOTIFICATION_URL=http://notification-service:8003/api/v1/notifications
```

### **Settings Class (core/config.py)**

```python
class Settings(BaseSettings):
    # API settings
    API_PREFIX: str = "/api/v1"
    DEBUG: bool = False
    PROJECT_NAME: str = "Inventory Service"
    PORT: int = 8002
    
    # Database settings
    DATABASE_URL: PostgresDsn
    
    # Service URLs
    PRODUCT_SERVICE_URL: AnyHttpUrl
    
    # Retry Configuration
    MAX_RETRIES: int = 3
    RETRY_DELAY: int = 1  # seconds
    
    # Inventory settings
    LOW_STOCK_THRESHOLD: int = 5
    ENABLE_NOTIFICATIONS: bool = True
    NOTIFICATION_URL: Optional[AnyHttpUrl] = None
```

## **2. Database Layer (db/postgresql.py)**

### **Database Setup**
- **Engine**: SQLAlchemy async engine with asyncpg driver
- **Sessions**: Async session factory for transactional operations
- **Connection**: Converts sync PostgreSQL URL to async format
- **Lifecycle**: Proper initialization and cleanup of database connections

### **Key Functions**
```python
async def initialize_db():
    """Initialize database with required tables."""
    # Creates all tables automatically using SQLAlchemy metadata
    # Sets up proper indexes for query optimization

async def close_db_connection():
    """Close database connection."""
    # Properly disposes of connection pools

async def get_db():
    """Dependency for getting an async database session."""
    # Provides database session with automatic cleanup
```

## **3. Data Models (models/inventory.py)**

### **SQLAlchemy Database Models**

#### **Inventory Items Table**

```python
class InventoryItem(Base):
    __tablename__ = "inventory_items"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(String, unique=True, index=True, nullable=False)
    available_quantity = Column(Integer, nullable=False, default=0)
    reserved_quantity = Column(Integer, nullable=False, default=0)
    reorder_threshold = Column(Integer, nullable=False, default=5)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Constraints to ensure quantities are never negative
    __table_args__ = (
        CheckConstraint('available_quantity >= 0'),
        CheckConstraint('reserved_quantity >= 0'),
    )
```

#### **Inventory History Table**

```python
class InventoryHistory(Base):
    __tablename__ = "inventory_history"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(String, index=True, nullable=False)
    quantity_change = Column(Integer, nullable=False)
    previous_quantity = Column(Integer, nullable=False)
    new_quantity = Column(Integer, nullable=False)
    change_type = Column(String, nullable=False)  # "add", "remove", "reserve", "release"
    reference_id = Column(String, nullable=True)  # Order ID or other reference
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
```

### **Pydantic API Models**

#### **Inventory Models**
- **InventoryItemBase**: Base model with core inventory fields
- **InventoryItemCreate**: Model for creating new inventory records
- **InventoryItemUpdate**: Optional fields for inventory updates
- **InventoryItemResponse**: Complete inventory data for API responses

#### **Operation Models**
- **InventoryCheck**: Model for checking product availability
- **InventoryReserve**: Model for reserving inventory for orders
- **InventoryRelease**: Model for releasing reserved inventory
- **InventoryAdjust**: Model for manual inventory adjustments

#### **Model Features**
```python
class InventoryItemBase(BaseModel):
    product_id: str
    available_quantity: int = Field(..., ge=0)
    reserved_quantity: int = Field(..., ge=0)
    reorder_threshold: int = Field(..., ge=0)

class InventoryReserve(BaseModel):
    product_id: str
    quantity: int = Field(..., gt=0)
    order_id: Optional[str] = None
    
    @validator('quantity')
    def validate_quantity(cls, v):
        if v <= 0:
            raise ValueError("Quantity must be greater than 0")
        return v
```

## **4. External Service Integration (services/product.py)**

### **Product Service Client**
- **Purpose**: Validates product existence before inventory operations
- **Retry Logic**: Implements tenacity retry mechanism for resilient communication
- **Error Handling**: Graceful handling of product service unavailability

### **Key Functions**
```python
async def get_product(product_id: str) -> Optional[Dict]:
    # Retrieves product details from Product Service
    # Validates product exists before inventory operations
    # Returns product data or None if not found
```

## **5. Authentication Dependencies (api/dependencies.py)**

### **Key Functions**
```python
async def get_current_user(token: str = Depends(oauth2_scheme)):
    # Stub authentication for development/testing
    # In production, would validate JWT tokens from API gateway
    # Returns user with admin privileges for testing

def is_admin(current_user=Depends(get_current_user)):
    # Checks if current user has admin privileges
    # Required for inventory creation and adjustment operations
    # Raises 403 error for insufficient permissions
```

## **6. API Routes (api/routes/inventory.py)**

### **Inventory Management Routes**

#### **POST /api/v1/inventory/**
- **Purpose**: Create new inventory record for a product
- **Authentication**: Admin required
- **Process**:
  1. Verify product exists in Product Service
  2. Create inventory record with constraints
  3. Add history entry for audit trail
  4. Handle duplicate product ID errors
- **Features**: Automatic history tracking, product validation

#### **GET /api/v1/inventory/**
- **Purpose**: List inventory items with filtering and pagination
- **Authentication**: Required
- **Filters**:
  - `low_stock_only`: Show only items below reorder threshold
  - `skip`/`limit`: Pagination parameters
- **Returns**: List of inventory items with current stock levels

#### **GET /api/v1/inventory/check**
- **Purpose**: Check if sufficient inventory is available for a quantity
- **Authentication**: Not required (used by other services)
- **Parameters**: 
  - `product_id`: Product to check
  - `quantity`: Required quantity
- **Returns**: Availability status and current stock information

#### **GET /api/v1/inventory/{product_id}**
- **Purpose**: Get inventory details for specific product
- **Authentication**: Required
- **Returns**: Complete inventory information including quantities and thresholds

#### **PUT /api/v1/inventory/{product_id}**
- **Purpose**: Update inventory levels and settings
- **Authentication**: Admin required
- **Features**:
  - Partial updates (only provided fields)
  - Automatic history tracking
  - Low stock notification checking
- **Process**: Updates inventory and creates history record

#### **POST /api/v1/inventory/reserve**
- **Purpose**: Reserve inventory for order processing
- **Authentication**: Required
- **Process**:
  1. Check sufficient available inventory
  2. Move quantity from available to reserved
  3. Create history record with order reference
  4. Check for low stock notifications
- **Used By**: Order Service when creating orders

#### **POST /api/v1/inventory/release**
- **Purpose**: Release previously reserved inventory
- **Authentication**: Required
- **Process**:
  1. Validate reserved quantity exists
  2. Move quantity from reserved back to available
  3. Create history record with order reference
  4. Handle over-release scenarios gracefully
- **Used By**: Order Service when canceling orders

#### **POST /api/v1/inventory/adjust**
- **Purpose**: Manual inventory adjustments (add/remove stock)
- **Authentication**: Admin required
- **Features**:
  - Positive or negative quantity changes
  - Reason tracking for audit purposes
  - Prevents negative inventory levels
- **Process**: Adjusts inventory and creates detailed history record

#### **GET /api/v1/inventory/low-stock**
- **Purpose**: Get products with inventory below reorder threshold
- **Authentication**: Required
- **Returns**: List of products requiring restocking
- **Used For**: Inventory management and procurement planning

#### **GET /api/v1/inventory/history/{product_id}**
- **Purpose**: Get inventory change history for a product
- **Authentication**: Required
- **Features**:
  - Chronological order (newest first)
  - Configurable limit
  - Complete audit trail
- **Returns**: List of all inventory changes with timestamps and reasons

## **7. Advanced Features**

### **Low Stock Notifications**
```python
async def check_and_notify_low_stock(inventory_item: InventoryItem):
    # Checks if inventory is below reorder threshold
    # Sends notification to external notification service
    # Includes product details and current stock levels
    # Handles notification service failures gracefully
```

### **Inventory History Tracking**
- **Complete Audit Trail**: Every inventory change is recorded
- **Change Types**: add, remove, reserve, release, update
- **Reference Tracking**: Links changes to orders or other operations
- **Timestamp Precision**: Full datetime tracking for all changes

### **Data Integrity**
- **Database Constraints**: Prevents negative quantities at database level
- **Transaction Safety**: Uses database transactions for atomic operations
- **Concurrent Access**: Handles multiple simultaneous inventory updates
- **Error Recovery**: Graceful handling of constraint violations

## **8. Application Entry Point (main.py)**

### **FastAPI Application Setup**
```python
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Inventory Service API",
    version="1.0.0",
    openapi_url=f"{settings.API_PREFIX}/openapi.json",
    docs_url=f"{settings.API_PREFIX}/docs",
    redoc_url=f"{settings.API_PREFIX}/redoc",
)

# CORS middleware for cross-origin requests
app.add_middleware(CORSMiddleware, ...)

# Route registration
app.include_router(inventory.router, prefix=settings.API_PREFIX)

# Lifecycle events
app.add_event_handler("startup", initialize_db)
app.add_event_handler("shutdown", close_db_connection)

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "inventory-service"}
```

## **9. Containerization**

### **Dockerfile**

```dockerfile
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
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8002"]
```

- **Base**: Python 3.10-slim for lightweight container
- **Dependencies**: PostgreSQL development libraries for asyncpg
- **Runtime**: Uvicorn ASGI server on port 8002