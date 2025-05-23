# Product Service - Breakdown

The Product Service is a FastAPI-based microservice responsible for managing product information in the e-commerce system, using MongoDB as the database and automatically creating inventory records when products are created.

![alt text](../images/Product-service.svg)

## **Project Structure**

```
product-service/
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
    │       └── products.py     # Product management endpoints
    ├── core/                   # Core functionality
    │   ├── __init__.py
    │   └── config.py           # Application settings
    ├── db/                     # Database layer
    │   ├── __init__.py
    │   └── mongodb.py          # MongoDB connection & setup
    ├── models/                 # Data models
    │   ├── __init__.py
    │   └── product.py          # Product models
    └── services/               # External service clients
        └── inventory_service.py # Inventory service integration
```

## **1. Configuration (.env & config.py)**

### **Environment Variables (.env)**

```bash
# MongoDB Configuration
MONGODB_URI=mongodb://mongodb-product:27017
MONGODB_DB=product_db

# API Configuration
API_PREFIX=/api/v1
DEBUG=False

# Authentication (for testing purposes)
SECRET_KEY=your-secret-key-here

# Service URLs
INVENTORY_SERVICE_URL=http://inventory-service:8002/api/v1
```

### **Settings Class (core/config.py)**

```python
class Settings(BaseSettings):
    # API settings
    API_PREFIX: str = "/api/v1"
    DEBUG: bool = False
    PROJECT_NAME: str = "Product Service"
    
    # MongoDB settings
    MONGODB_URI: str = "mongodb://localhost:27017"
    MONGODB_DB: str = "product_db"
    
    # Service URLs
    INVENTORY_SERVICE_URL: Optional[AnyHttpUrl] = None
    
    # JWT Auth settings (for testing/development)
    SECRET_KEY: str = "development-secret-key"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
```

## **2. Database Layer (db/mongodb.py)**

### **Database Setup**
- **Engine**: Motor async MongoDB client
- **Connection**: Async MongoDB connection with proper lifecycle management
- **Indexing**: Automatic index creation on product name and category fields

### **Key Functions**
```python
async def connect_to_mongo():
    """Create database connection."""
    # Establishes MongoDB connection
    # Creates indexes for optimized queries

async def close_mongo_connection():
    """Close database connection."""
    # Properly closes MongoDB connections

def get_database():
    """Return database instance."""
    # Provides database instance for API endpoints
```

## **3. Data Models (models/product.py)**

### **MongoDB Document Structure**

#### **Product Document**

```python
# MongoDB stores products as documents with these fields:
{
    "_id": ObjectId,           # MongoDB unique identifier
    "name": str,              # Product name
    "description": str,       # Product description
    "category": str,          # Product category
    "price": float,           # Product price
    "quantity": int           # Available quantity
}
```

### **Pydantic API Models**

#### **Product Models**
- **ProductBase**: Base model with common fields (name, description, category, price, quantity)
- **ProductCreate**: Model for creating new products
- **ProductResponse**: Complete product data with MongoDB ObjectId
- **ProductUpdate**: Optional fields for partial product updates
- **PyObjectId**: Custom ObjectId handler for Pydantic models

#### **Model Features**
```python
class ProductBase(BaseModel):
    name: str
    description: str
    category: str
    price: float
    quantity: int
    
    class Config:
        schema_extra = {
            "example": {
                "name": "Smartphone X",
                "description": "Latest model with high-end camera",
                "category": "Electronics",
                "price": 699.99,
                "quantity": 50
            }
        }
```

## **4. External Service Integration (services/inventory_service.py)**

### **Inventory Service Client**
- **Purpose**: Automatically creates inventory records when products are created
- **Retry Logic**: Implements retry mechanism with exponential backoff
- **Error Handling**: Graceful handling of inventory service failures

### **Key Functions**
```python
async def create_inventory(product_id: str, initial_quantity: int = 0, reorder_threshold: int = 5) -> bool:
    # Creates inventory record in Inventory Service
    # Sets initial quantity and reorder threshold
    # Returns success/failure status
```

## **5. Authentication Dependencies (api/dependencies.py)**

### **Key Functions**
```python
async def get_current_user(token: str = Depends(oauth2_scheme)):
    # Stub authentication for development/testing
    # In production, would validate JWT tokens
    # Currently returns test user with admin privileges

async def get_db():
    # Dependency for database access
    # Returns MongoDB database instance
```

## **6. API Routes (api/routes/products.py)**

### **Product Management Routes**

#### **POST /api/v1/products/**
- **Purpose**: Create new product with automatic inventory creation
- **Authentication**: Required (currently stub)
- **Process**:
  1. Validate product data
  2. Insert product into MongoDB
  3. Automatically create inventory record
  4. Return created product with ObjectId
- **Integration**: Calls Inventory Service to create inventory record

#### **GET /api/v1/products/**
- **Purpose**: Retrieve products with filtering and pagination
- **Authentication**: Not required
- **Filters**:
  - `category`: Filter by product category
  - `name`: Case-insensitive name search
  - `min_price`/`max_price`: Price range filtering
  - `skip`/`limit`: Pagination parameters
- **Process**: Builds MongoDB query with filters and pagination

#### **GET /api/v1/products/{product_id}**
- **Purpose**: Get single product by ID
- **Authentication**: Not required
- **Validation**: Validates ObjectId format
- **Returns**: Complete product information or 404 error

#### **PUT /api/v1/products/{product_id}**
- **Purpose**: Update existing product
- **Authentication**: Required
- **Features**: 
  - Partial updates (only provided fields)
  - ObjectId validation
  - Returns updated product data
- **Process**: Uses MongoDB's `find_one_and_update` with `AFTER` return

#### **DELETE /api/v1/products/{product_id}**
- **Purpose**: Delete product by ID
- **Authentication**: Required
- **Validation**: Validates ObjectId format
- **Returns**: 204 No Content on success, 404 if not found

#### **GET /api/v1/products/category/list**
- **Purpose**: Get all unique product categories
- **Authentication**: Not required
- **Process**: Uses MongoDB's `distinct()` operation
- **Returns**: Array of category names

## **7. Application Entry Point (main.py)**

### **FastAPI Application Setup**
```python
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Product Service API",
    version="1.0.0",
    openapi_url=f"{settings.API_PREFIX}/openapi.json",
    docs_url=f"{settings.API_PREFIX}/docs",
    redoc_url=f"{settings.API_PREFIX}/redoc",
)

# CORS middleware for cross-origin requests
app.add_middleware(CORSMiddleware, ...)

# Route registration
app.include_router(products.router, prefix=settings.API_PREFIX)

# Lifecycle events
app.add_event_handler("startup", connect_to_mongo)
app.add_event_handler("shutdown", close_mongo_connection)

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "product-service"}
```

## **8. Containerization**

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
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

- **Base**: Python 3.10-slim for lightweight container
- **Dependencies**: Minimal system packages for Python compilation
- **App**: Standard Python app containerization pattern
- **Runtime**: Uvicorn ASGI server on port 8000