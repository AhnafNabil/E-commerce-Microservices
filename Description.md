# E-commerce Microservices Architecture

## **System Overview**

This e-commerce platform consists of **5 core microservices** orchestrated through **multiple messaging patterns** (RabbitMQ, Kafka, Redis) and unified by an **API Gateway**. Each service has its own database following the database-per-service pattern.

## **🏗️ Core Services Architecture**

### **1. Product Service (Port 8000)**
- **Database**: MongoDB
- **Purpose**: Manages the product catalog
- **Key Features**:
  - CRUD operations for products
  - Category filtering and search
  - Price range filtering
  - **Kafka Integration**: Publishes product lifecycle events

**Main Endpoints**:
```
POST /api/v1/products/     - Create product
GET  /api/v1/products/     - List/search products  
GET  /api/v1/products/{id} - Get specific product
PUT  /api/v1/products/{id} - Update product
DELETE /api/v1/products/{id} - Delete product
```

**Event Publishing**: When products are created/updated, events are sent to Kafka's `product.events` topic.

### **2. Inventory Service (Port 8002)**
- **Database**: PostgreSQL
- **Purpose**: Manages stock levels and inventory operations
- **Integration Points**: 
  - **Kafka Consumer**: Listens to product events to auto-create inventory
  - **RabbitMQ Consumer**: Processes order-related inventory operations
  - **Redis Publisher**: Sends low-stock notifications

**Key Features**:
- Automatic inventory creation when products are added
- Stock reservation/release for orders
- Low stock threshold monitoring
- Inventory history tracking

**Main Endpoints**:
```
POST /api/v1/inventory/           - Create inventory item
GET  /api/v1/inventory/           - List inventory items
GET  /api/v1/inventory/{id}       - Get specific inventory
PUT  /api/v1/inventory/{id}       - Update inventory
POST /api/v1/inventory/reserve    - Reserve stock
POST /api/v1/inventory/release    - Release reserved stock
GET  /api/v1/inventory/check      - Check availability
```

### **3. Order Service (Port 8001)**
- **Database**: MongoDB
- **Purpose**: Handles customer orders and order lifecycle
- **Integration**: 
  - **RabbitMQ Publisher**: Publishes order events for inventory processing
  - **HTTP Clients**: Validates users and products

**Key Features**:
- Order creation with automatic inventory validation
- Order status management with allowed transitions
- Asynchronous inventory reservation via RabbitMQ
- Order cancellation with inventory release

**Main Endpoints**:
```
POST /api/v1/orders/              - Create order
GET  /api/v1/orders/              - List orders (with filters)
GET  /api/v1/orders/{id}          - Get specific order
PUT  /api/v1/orders/{id}/status   - Update order status
DELETE /api/v1/orders/{id}        - Cancel order
GET  /api/v1/orders/user/{id}     - Get user's orders
```

### **4. User Service (Port 8003)**
- **Database**: PostgreSQL
- **Purpose**: User management and authentication
- **Security**: JWT-based authentication with access/refresh tokens

**Key Features**:
- User registration with password strength validation
- JWT authentication (access + refresh tokens)
- User profile management
- Multiple shipping addresses per user
- Password change functionality

**Main Endpoints**:
```
POST /api/v1/auth/register        - Register user
POST /api/v1/auth/login           - Login user
POST /api/v1/auth/refresh         - Refresh token
GET  /api/v1/users/me             - Get current user
PUT  /api/v1/users/me             - Update profile
POST /api/v1/users/me/addresses   - Add address
GET  /api/v1/users/{id}/verify    - Verify user exists
```

### **5. Notification Service (Port 8004)**
- **Database**: PostgreSQL
- **Purpose**: Handles all system notifications
- **Integration**:
  - **Redis Subscriber**: Listens for low-stock alerts
  - **SMTP**: Email delivery via configurable providers

**Key Features**:
- Real-time low stock email notifications
- Notification history and status tracking
- Multiple delivery channels (currently email)
- Mailtrap integration for testing

**Main Endpoints**:
```
GET  /api/v1/notifications/       - List notifications
GET  /api/v1/notifications/{id}   - Get specific notification
POST /api/v1/notifications/test   - Send test email
```

## **🔄 Messaging Architecture**

### **1. RabbitMQ (Port 5672/15672)**
**Purpose**: Handles order processing workflow
**Message Flow**:
1. **Order Created** → `order_created` queue
2. **Inventory Reserved** → `inventory_reserved` queue  
3. **Inventory Failed** → `inventory_failed` queue
4. **Inventory Release** → `inventory_release` queue

**Benefits**:
- Reliable message delivery
- Order processing resilience during service outages
- Automatic retry mechanisms

### **2. Kafka (Port 9092)**
**Purpose**: Event streaming for product lifecycle
**Topics**:
- `product.events` - Product creation/update events
- `inventory.events` - Inventory lifecycle events

**Consumer Groups**:
- `inventory-consumer-group` - Processes product events

**Benefits**:
- Service decoupling
- Event replay capability
- Scalable event processing

### **3. Redis (Port 6379)**
**Purpose**: Real-time notifications
**Channels**:
- `inventory:low-stock` - Low stock alert channel
- `inventory:low-stock:stream` - Persistent notification stream

**Benefits**:
- Real-time pub/sub messaging
- Low latency notifications

## **🌐 API Gateway (Nginx - Port 80)**

**Purpose**: Single entry point for all services
**Features**:
- Request routing to appropriate services
- Load balancing capabilities
- CORS handling
- Health check aggregation

**Routing Rules**:
```
/api/v1/products/*      → product-service:8000
/api/v1/orders/*        → order-service:8001  
/api/v1/inventory/*     → inventory-service:8002
/api/v1/auth/*          → user-service:8003
/api/v1/users/*         → user-service:8003
/api/v1/notifications/* → notification-service:8004
```

## **📊 Data Flow Examples**

### **Complete Order Flow**:
1. **User Login** → User Service validates and returns JWT
2. **Product Browse** → Product Service returns catalog
3. **Order Creation** → Order Service creates order, publishes to RabbitMQ
4. **Inventory Check** → Inventory Service processes order via RabbitMQ
5. **Stock Reservation** → Inventory updated, low-stock check performed
6. **Notification** → If low stock, Redis message sent to Notification Service
7. **Email Alert** → Admin receives low stock email

### **Product Creation Flow**:
1. **Admin Creates Product** → Product Service stores in MongoDB
2. **Kafka Event** → Product created event published to `product.events`
3. **Inventory Auto-Creation** → Inventory Service consumes event, creates inventory record
4. **Threshold Setup** → Smart reorder thresholds calculated (10% of stock, minimum 5)

## **Deployment Architecture**

All services are containerized with Docker Compose providing:
- **Service Discovery**: Internal DNS resolution
- **Network Isolation**: Dedicated microservice network
- **Volume Persistence**: Data persistence across restarts
- **Environment Configuration**: Service-specific environment files
- **Startup Orchestration**: Proper service dependency management

This architecture demonstrates modern microservices best practices including event sourcing, CQRS patterns, eventual consistency, and resilient distributed systems design.