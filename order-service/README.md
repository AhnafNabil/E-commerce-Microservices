# Order Service - Breakdown

The Order Service is a FastAPI-based microservice responsible for managing the complete order lifecycle in the e-commerce system, using MongoDB as the database and integrating with User, Product, and Inventory services for comprehensive order processing.

![alt text](../images/Order-service.svg)

## **Project Structure**

```
order-service/
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
    │       └── orders.py       # Order management endpoints
    ├── core/                   # Core functionality
    │   ├── __init__.py
    │   ├── config.py           # Application settings
    │   └── logging.py          # Logging configuration
    ├── db/                     # Database layer
    │   ├── __init__.py
    │   └── mongodb.py          # MongoDB connection & setup
    ├── models/                 # Data models
    │   ├── __init__.py
    │   └── order.py            # Order models
    └── services/               # External service clients
        ├── __init__.py
        ├── inventory.py        # Inventory service integration
        ├── product.py          # Product service integration
        └── user.py             # User service integration
```

## **1. Configuration (.env & config.py)**

### **Environment Variables (.env)**

```bash
# MongoDB Configuration
MONGODB_URI=mongodb://mongodb-order:27017
MONGODB_DB=order_db

# API Configuration
API_PREFIX=/api/v1
DEBUG=False
PORT=8001

# Service URLs
USER_SERVICE_URL=http://user-service:8003/api/v1
PRODUCT_SERVICE_URL=http://product-service:8000/api/v1
INVENTORY_SERVICE_URL=http://inventory-service:8002/api/v1

# Authentication (for testing purposes)
SECRET_KEY=your-secret-key-here

# Retry Configuration
MAX_RETRIES=3
RETRY_DELAY=1  # seconds
```

### **Settings Class (core/config.py)**

```python
class Settings(BaseSettings):
    # API settings
    API_PREFIX: str = "/api/v1"
    DEBUG: bool = False
    PROJECT_NAME: str = "Order Service"
    PORT: int = 8001
    
    # MongoDB settings
    MONGODB_URI: str = "mongodb://localhost:27017"
    MONGODB_DB: str = "order_db"
    
    # Service URLs
    USER_SERVICE_URL: AnyHttpUrl
    PRODUCT_SERVICE_URL: AnyHttpUrl
    INVENTORY_SERVICE_URL: AnyHttpUrl
    
    # Order status codes
    ORDER_STATUS: Dict[str, str] = {
        "PENDING": "pending",
        "PAID": "paid",
        "PROCESSING": "processing",
        "SHIPPED": "shipped",
        "DELIVERED": "delivered",
        "CANCELLED": "cancelled",
        "REFUNDED": "refunded"
    }
    
    # Status transitions allowed
    ALLOWED_STATUS_TRANSITIONS: Dict[str, List[str]] = {
        "pending": ["paid", "cancelled"],
        "paid": ["processing", "cancelled", "refunded"],
        "processing": ["shipped", "cancelled", "refunded"],
        "shipped": ["delivered", "refunded"],
        "delivered": ["refunded"],
        "cancelled": [],
        "refunded": []
    }
```

## **2. Database Layer (db/mongodb.py)**

### **Database Setup**
- **Engine**: Motor async MongoDB client for high-performance operations
- **Connection**: Async MongoDB connection with proper lifecycle management
- **Indexing**: Automatic index creation on user_id, status, and created_at fields for optimized queries

### **Key Functions**
```python
async def connect_to_mongo():
    """Create database connection."""
    # Establishes MongoDB connection
    # Creates indexes for optimized order queries

async def close_mongo_connection():
    """Close database connection."""
    # Properly closes MongoDB connections

def get_database():
    """Return database instance."""
    # Provides database instance for API endpoints
```

## **3. Data Models (models/order.py)**

### **MongoDB Document Structure**

#### **Order Document**

```javascript
{
    "_id": ObjectId,              // MongoDB unique identifier
    "user_id": string,           // Reference to user who placed order
    "items": [                   // Array of order items
        {
            "product_id": string,     // Reference to product
            "quantity": integer,      // Quantity ordered
            "price": decimal         // Price at time of order
        }
    ],
    "total_price": decimal,      // Calculated total price
    "status": string,           // Order status (pending, paid, etc.)
    "shipping_address": {        // Complete shipping address
        "line1": string,
        "line2": string,
        "city": string,
        "state": string,
        "postal_code": string,
        "country": string
    },
    "created_at": datetime,     // Order creation timestamp
    "updated_at": datetime      // Last modification timestamp
}
```

### **Pydantic API Models**

#### **Order Models**
- **OrderItem**: Individual item within an order (product_id, quantity, price)
- **OrderAddress**: Shipping address information
- **OrderCreate**: Model for creating new orders with validation
- **OrderUpdate**: Optional fields for order updates
- **OrderResponse**: Complete order data with MongoDB ObjectId
- **OrderStatusUpdate**: Model for updating order status

#### **Model Features**
```python
class OrderItem(BaseModel):
    product_id: str
    quantity: int = Field(..., gt=0)
    price: condecimal(max_digits=10, decimal_places=2) = Field(...)
    
    @validator('price')
    def validate_price(cls, v):
        if v <= 0:
            raise ValueError("Price must be greater than 0")
        return v

class OrderCreate(BaseModel):
    user_id: str
    items: List[OrderItem] = Field(..., min_items=1)
    shipping_address: OrderAddress
    
    @validator('items')
    def validate_items(cls, v):
        if not v:
            raise ValueError("Order must have at least one item")
        return v
```

#### **Custom ObjectId Handler**
```python
class PyObjectId(ObjectId):
    """Custom ObjectId type for Pydantic models."""
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)
```

## **4. External Service Integration**

### **User Service Client (services/user.py)**
- **Purpose**: Validates user existence and retrieves user information
- **Retry Logic**: Implements tenacity retry mechanism for resilient communication
- **Graceful Fallback**: Returns success for testing when service unavailable

```python
async def verify_user(user_id: str) -> bool:
    # Verifies user exists and is active
    # Handles different user ID formats for compatibility
    # Returns True/False for user validity
```

### **Product Service Client (services/product.py)**
- **Purpose**: Validates products exist and prices are correct
- **Price Verification**: Ensures order prices match current product prices
- **Bulk Validation**: Efficiently validates multiple products in single order

```python
async def verify_products(items: List) -> bool:
    # Validates all products in order exist
    # Checks price accuracy against current product prices
    # Returns overall validation result
```

### **Inventory Service Client (services/inventory.py)**
- **Purpose**: Manages inventory reservations and releases
- **Stock Checking**: Verifies sufficient inventory before order creation
- **Reservation Management**: Reserves/releases inventory based on order lifecycle

```python
async def check_inventory(product_id: str, quantity: int) -> bool:
    # Checks if sufficient inventory is available
    
async def reserve_inventory(product_id: str, quantity: int) -> bool:
    # Reserves inventory for order processing
    
async def release_inventory(product_id: str, quantity: int) -> bool:
    # Releases inventory from cancelled orders
```

## **5. Authentication Dependencies (api/dependencies.py)**

### **Key Functions**
```python
async def get_current_user(token: str = Depends(oauth2_scheme)):
    # Stub authentication for development/testing
    # In production, would validate JWT tokens from API gateway
    # Returns authenticated user information

async def get_db():
    # Dependency for database access
    # Returns MongoDB database instance

def is_admin(current_user=Depends(get_current_user)):
    # Checks if current user has admin privileges
    # Required for certain administrative operations
```

## **6. API Routes (api/routes/orders.py)**

### **Order Management Routes**

#### **POST /api/v1/orders/**
- **Purpose**: Create new order with comprehensive validation
- **Authentication**: Required
- **Multi-Service Integration Process**:
  1. **User Validation**: Verify user exists via User Service
  2. **Product Validation**: Verify all products exist and prices are correct
  3. **Inventory Check**: Verify sufficient inventory for all items
  4. **Inventory Reservation**: Reserve inventory for all order items
  5. **Order Creation**: Create order in pending status
  6. **Price Calculation**: Calculate total price with decimal precision
- **Error Handling**: Rollback operations if any step fails
- **Returns**: Complete order information with generated ObjectId

#### **GET /api/v1/orders/**
- **Purpose**: List orders with advanced filtering and pagination
- **Authentication**: Required
- **Advanced Filtering**:
  - `status`: Filter by order status
  - `user_id`: Filter by specific user
  - `start_date`/`end_date`: Date range filtering
  - `skip`/`limit`: Pagination parameters
- **Sorting**: Orders sorted by creation date (newest first)
- **Returns**: Paginated list of orders matching criteria

#### **GET /api/v1/orders/{order_id}**
- **Purpose**: Get single order by ID
- **Authentication**: Required
- **Validation**: Validates MongoDB ObjectId format
- **Returns**: Complete order information or 404 error

#### **GET /api/v1/orders/user/{user_id}**
- **Purpose**: Get all orders for specific user
- **Authentication**: Required
- **Features**:
  - User-specific order filtering
  - Status filtering within user orders
  - Pagination support
  - Chronological ordering
- **Returns**: User's order history

#### **PUT /api/v1/orders/{order_id}/status**
- **Purpose**: Update order status with business logic validation
- **Authentication**: Required
- **Status Transition Validation**:
  - Validates allowed status transitions (pending → paid → processing → shipped → delivered)
  - Prevents invalid status changes
  - Handles inventory implications of status changes
- **Inventory Management**:
  - Releases inventory when order cancelled from pending state
  - Maintains inventory reservations during valid transitions
- **Process**: Updates status and timestamp atomically

#### **DELETE /api/v1/orders/{order_id}**
- **Purpose**: Cancel order (sets status to cancelled)
- **Authentication**: Required
- **Business Rules**:
  - Cannot cancel shipped, delivered, or already cancelled orders
  - Can cancel pending, paid, or processing orders
- **Inventory Management**:
  - Automatically releases reserved inventory
  - Updates inventory availability
- **Process**: Sets status to cancelled and releases inventory

## **7. Advanced Features**

### **Order Status Management**
```python
# Comprehensive status workflow
ORDER_STATUS = {
    "PENDING": "pending",        # Order created, payment pending
    "PAID": "paid",             # Payment received
    "PROCESSING": "processing",  # Order being prepared
    "SHIPPED": "shipped",       # Order dispatched
    "DELIVERED": "delivered",   # Order received by customer
    "CANCELLED": "cancelled",   # Order cancelled
    "REFUNDED": "refunded"      # Order refunded
}

# Business logic for valid transitions
ALLOWED_STATUS_TRANSITIONS = {
    "pending": ["paid", "cancelled"],
    "paid": ["processing", "cancelled", "refunded"],
    "processing": ["shipped", "cancelled", "refunded"],
    "shipped": ["delivered", "refunded"],
    "delivered": ["refunded"],
    "cancelled": [],
    "refunded": []
}
```

### **Multi-Service Orchestration**
- **Transaction-like Behavior**: Coordinates operations across multiple services
- **Rollback Logic**: Undoes operations if any step in order creation fails
- **Service Resilience**: Continues operation even if some services are temporarily unavailable
- **Data Consistency**: Ensures order data remains consistent across all services

### **Price and Inventory Management**
- **Price Freezing**: Orders store prices at time of creation to prevent price changes
- **Decimal Precision**: Uses proper decimal handling for financial calculations
- **Inventory Coordination**: Seamlessly manages inventory reservations throughout order lifecycle
- **Stock Validation**: Prevents overselling by checking inventory before order creation

## **8. Application Entry Point (main.py)**

### **FastAPI Application Setup**
```python
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Order Service API",
    version="1.0.0",
    openapi_url=f"{settings.API_PREFIX}/openapi.json",
    docs_url=f"{settings.API_PREFIX}/docs",
    redoc_url=f"{settings.API_PREFIX}/redoc",
)

# CORS middleware for cross-origin requests
app.add_middleware(CORSMiddleware, ...)

# Route registration
app.include_router(orders.router, prefix=settings.API_PREFIX)

# Lifecycle events
app.add_event_handler("startup", connect_to_mongo)
app.add_event_handler("shutdown", close_mongo_connection)

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "order-service"}
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
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ app/

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
```

- **Base**: Python 3.10-slim for lightweight container
- **Dependencies**: Minimal system packages for Python compilation
- **Runtime**: Uvicorn ASGI server on port 8001