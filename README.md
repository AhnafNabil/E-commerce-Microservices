# E-commerce Microservices Testing Documentation

This documentation provides a comprehensive guide for testing the complete workflow of the integrated E-commerce Microservices system. With our product-inventory integration, creating products now automatically creates inventory records, simplifying the testing process.

## Overview of Testing Flow

1. User Registration and Authentication
2. Adding User Address
3. Creating Products (Inventory is automatically created)
4. Browsing Products and Checking Inventory
5. Placing Orders
6. Viewing Order Details

Let's begin testing each component of the system.

## 1. User Registration and Authentication

First, we'll register a new user and obtain an authentication token.

### Step 1.1: Register a New User

```bash
curl -X POST "http://localhost/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "customer@example.com",
    "password": "Password123",
    "first_name": "Example",
    "last_name": "Customer",
    "phone": "555-123-4567"
  }'
```

Expected response:
```json
{
  "id": 1,
  "email": "customer@example.com",
  "first_name": "Example",
  "last_name": "Customer",
  "phone": "555-123-4567",
  "is_active": true,
  "created_at": "2025-05-15T11:30:00.123456+00:00",
  "addresses": []
}
```

### Step 1.2: Login to Get Authentication Token

```bash
curl -X POST "http://localhost/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=customer@example.com&password=Password123"
```

Expected response:
```json
{
  "access_token": "eyJhbGciOiJS...",
  "refresh_token": "eyJhbGciOiJS...",
  "token_type": "bearer"
}
```

Save the access_token for subsequent requests:

```bash
TOKEN="eyJhbGciOiJS..."  # Replace with the actual token from the response
```

### Step 1.3: Verify User Authentication

```bash
curl -X GET "http://localhost/api/v1/users/me" \
  -H "Authorization: Bearer $TOKEN"
```

Expected response:
```json
{
  "id": 1,
  "email": "customer@example.com",
  "first_name": "Example",
  "last_name": "Customer",
  "phone": "555-123-4567",
  "is_active": true,
  "created_at": "2025-05-15T11:30:00.123456+00:00",
  "addresses": []
}
```

## 2. Adding User Address

Next, we'll add a shipping address for the user.

```bash
curl -X POST "http://localhost/api/v1/users/me/addresses" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "line1": "123 Example Street",
    "line2": "Apt 4B",
    "city": "Example City",
    "state": "EX",
    "postal_code": "12345",
    "country": "Example Country",
    "is_default": true
  }'
```

Expected response:
```json
{
  "id": 1,
  "line1": "123 Example Street",
  "line2": "Apt 4B",
  "city": "Example City",
  "state": "EX",
  "postal_code": "12345",
  "country": "Example Country",
  "is_default": true
}
```

## 3. Creating Products with Automatic Inventory

Now, we'll create three different products. Because of our integration, inventory records will be automatically created for each product.

### Step 3.1: Create Product 1 - Smartphone

```bash
curl -X POST "http://localhost/api/v1/products/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Premium Smartphone",
    "description": "Latest model with high-end camera and long battery life",
    "category": "Electronics",
    "price": 899.99,
    "quantity": 50
  }'
```

Expected response (save the `_id` for later use):
```json
{
  "name": "Premium Smartphone",
  "description": "Latest model with high-end camera and long battery life",
  "category": "Electronics",
  "price": 899.99,
  "quantity": 50,
  "_id": "product_id_1"
}
```

```bash
PRODUCT_ID_1="product_id_1"  # Replace with the actual ID from the response
```

### Step 3.2: Create Product 2 - Wireless Headphones

```bash
curl -X POST "http://localhost/api/v1/products/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Wireless Noise-Cancelling Headphones",
    "description": "Premium headphones with active noise cancellation",
    "category": "Audio",
    "price": 249.99,
    "quantity": 100
  }'
```

Expected response:
```json
{
  "name": "Wireless Noise-Cancelling Headphones",
  "description": "Premium headphones with active noise cancellation",
  "category": "Audio",
  "price": 249.99,
  "quantity": 100,
  "_id": "product_id_2"
}
```

```bash
PRODUCT_ID_2="product_id_2"  # Replace with the actual ID from the response
```

### Step 3.3: Create Product 3 - Smart Watch

```bash
curl -X POST "http://localhost/api/v1/products/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Smart Fitness Watch",
    "description": "Waterproof fitness tracker with heart rate monitoring",
    "category": "Wearables",
    "price": 179.99,
    "quantity": 75
  }'
```

Expected response:
```json
{
  "name": "Smart Fitness Watch",
  "description": "Waterproof fitness tracker with heart rate monitoring",
  "category": "Wearables",
  "price": 179.99,
  "quantity": 75,
  "_id": "product_id_3"
}
```

```bash
PRODUCT_ID_3="product_id_3"  # Replace with the actual ID from the response
```

## 4. Browsing Products and Checking Inventory

Now, let's browse products and verify that inventory was automatically created.

### Step 4.1: Get All Products

```bash
curl -X GET "http://localhost/api/v1/products/" \
  -H "Authorization: Bearer $TOKEN"
```

Expected response:
```json
[
  {
    "name": "Premium Smartphone",
    "description": "Latest model with high-end camera and long battery life",
    "category": "Electronics",
    "price": 899.99,
    "quantity": 50,
    "_id": "product_id_1"
  },
  {
    "name": "Wireless Noise-Cancelling Headphones",
    "description": "Premium headphones with active noise cancellation",
    "category": "Audio",
    "price": 249.99,
    "quantity": 100,
    "_id": "product_id_2"
  },
  {
    "name": "Smart Fitness Watch",
    "description": "Waterproof fitness tracker with heart rate monitoring",
    "category": "Wearables",
    "price": 179.99,
    "quantity": 75,
    "_id": "product_id_3"
  }
]
```

### Step 4.2: Verify Inventory Was Created For Products

Check inventory for Product 1:

```bash
curl -X GET "http://localhost/api/v1/inventory/$PRODUCT_ID_1" \
  -H "Authorization: Bearer $TOKEN"
```

Expected response:
```json
{
  "product_id": "product_id_1",
  "available_quantity": 50,
  "reserved_quantity": 0,
  "reorder_threshold": 5,
  "id": 1,
  "created_at": "2025-05-15T11:40:00.123456+00:00",
  "updated_at": "2025-05-15T11:40:00.123456+00:00"
}
```

Check inventory for Product 2:

```bash
curl -X GET "http://localhost/api/v1/inventory/$PRODUCT_ID_2" \
  -H "Authorization: Bearer $TOKEN"
```

Expected response:
```json
{
  "product_id": "product_id_2",
  "available_quantity": 100,
  "reserved_quantity": 0,
  "reorder_threshold": 10,
  "id": 2,
  "created_at": "2025-05-15T11:41:00.123456+00:00",
  "updated_at": "2025-05-15T11:41:00.123456+00:00"
}
```

### Step 4.3: Filter Products by Category

```bash
curl -X GET "http://localhost/api/v1/products/?category=Electronics" \
  -H "Authorization: Bearer $TOKEN"
```

Expected response:
```json
[
  {
    "name": "Premium Smartphone",
    "description": "Latest model with high-end camera and long battery life",
    "category": "Electronics",
    "price": 899.99,
    "quantity": 50,
    "_id": "product_id_1"
  }
]
```

### Step 4.4: Filter Products by Price Range

```bash
curl -X GET "http://localhost/api/v1/products/?min_price=100&max_price=300" \
  -H "Authorization: Bearer $TOKEN"
```

Expected response:
```json
[
  {
    "name": "Wireless Noise-Cancelling Headphones",
    "description": "Premium headphones with active noise cancellation",
    "category": "Audio",
    "price": 249.99,
    "quantity": 100,
    "_id": "product_id_2"
  },
  {
    "name": "Smart Fitness Watch",
    "description": "Waterproof fitness tracker with heart rate monitoring",
    "category": "Wearables",
    "price": 179.99,
    "quantity": 75,
    "_id": "product_id_3"
  }
]
```

## 5. Placing Orders

Now, let's place orders.

### Step 5.1: Get User ID

First, we need to get the user's ID:

```bash
curl -X GET "http://localhost/api/v1/users/me" \
  -H "Authorization: Bearer $TOKEN"
```

From the response, save the user ID:

```bash
USER_ID="1"  # Replace with the actual ID from the response
```

### Step 5.2: Place an Order for a Single Product

```bash
curl -X POST "http://localhost/api/v1/orders/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "'$USER_ID'",
    "items": [
      {
        "product_id": "'$PRODUCT_ID_1'",
        "quantity": 1,
        "price": 899.99
      }
    ],
    "shipping_address": {
      "line1": "123 Example Street",
      "line2": "Apt 4B",
      "city": "Example City",
      "state": "EX",
      "postal_code": "12345",
      "country": "Example Country"
    }
  }'
```

Expected response (save the `_id` for later use):
```json
{
  "_id": "order_id_1",
  "user_id": "1",
  "items": [
    {
      "product_id": "product_id_1",
      "quantity": 1,
      "price": 899.99
    }
  ],
  "total_price": 899.99,
  "status": "pending",
  "shipping_address": {
    "line1": "123 Example Street",
    "line2": "Apt 4B",
    "city": "Example City",
    "state": "EX",
    "postal_code": "12345",
    "country": "Example Country"
  },
  "created_at": "2025-05-15T11:50:00.123456+00:00",
  "updated_at": "2025-05-15T11:50:00.123456+00:00"
}
```

```bash
ORDER_ID_1="order_id_1"  # Replace with the actual ID from the response
```

### Step 5.3: Place an Order for Multiple Products

```bash
curl -X POST "http://localhost/api/v1/orders/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "'$USER_ID'",
    "items": [
      {
        "product_id": "'$PRODUCT_ID_2'",
        "quantity": 1,
        "price": 249.99
      },
      {
        "product_id": "'$PRODUCT_ID_3'",
        "quantity": 2,
        "price": 179.99
      }
    ],
    "shipping_address": {
      "line1": "123 Example Street",
      "line2": "Apt 4B",
      "city": "Example City",
      "state": "EX",
      "postal_code": "12345",
      "country": "Example Country"
    }
  }'
```

Expected response:
```json
{
  "_id": "order_id_2",
  "user_id": "1",
  "items": [
    {
      "product_id": "product_id_2",
      "quantity": 1,
      "price": 249.99
    },
    {
      "product_id": "product_id_3",
      "quantity": 2,
      "price": 179.99
    }
  ],
  "total_price": 609.97,
  "status": "pending",
  "shipping_address": {
    "line1": "123 Example Street",
    "line2": "Apt 4B",
    "city": "Example City",
    "state": "EX",
    "postal_code": "12345",
    "country": "Example Country"
  },
  "created_at": "2025-05-15T11:55:00.123456+00:00",
  "updated_at": "2025-05-15T11:55:00.123456+00:00"
}
```

```bash
ORDER_ID_2="order_id_2"  # Replace with the actual ID from the response
```

## 6. Viewing and Managing Orders

Now, let's view and manage the orders.

### Step 6.1: Get Order Details

```bash
curl -X GET "http://localhost/api/v1/orders/$ORDER_ID_1" \
  -H "Authorization: Bearer $TOKEN"
```

Expected response:
```json
{
  "_id": "order_id_1",
  "user_id": "1",
  "items": [
    {
      "product_id": "product_id_1",
      "quantity": 1,
      "price": 899.99
    }
  ],
  "total_price": 899.99,
  "status": "pending",
  "shipping_address": {
    "line1": "123 Example Street",
    "line2": "Apt 4B",
    "city": "Example City",
    "state": "EX",
    "postal_code": "12345",
    "country": "Example Country"
  },
  "created_at": "2025-05-15T11:50:00.123456+00:00",
  "updated_at": "2025-05-15T11:50:00.123456+00:00"
}
```

### Step 6.2: List All Orders of the User

```bash
curl -X GET "http://localhost/api/v1/orders/" \
  -H "Authorization: Bearer $TOKEN"
```

Expected response:
```json
[
  {
    "_id": "order_id_2",
    "user_id": "1",
    "items": [
      {
        "product_id": "product_id_2",
        "quantity": 1,
        "price": 249.99
      },
      {
        "product_id": "product_id_3",
        "quantity": 2,
        "price": 179.99
      }
    ],
    "total_price": 609.97,
    "status": "pending",
    "shipping_address": {
      "line1": "123 Example Street",
      "line2": "Apt 4B",
      "city": "Example City",
      "state": "EX",
      "postal_code": "12345",
      "country": "Example Country"
    },
    "created_at": "2025-05-15T11:55:00.123456+00:00",
    "updated_at": "2025-05-15T11:55:00.123456+00:00"
  },
  {
    "_id": "order_id_1",
    "user_id": "1",
    "items": [
      {
        "product_id": "product_id_1",
        "quantity": 1,
        "price": 899.99
      }
    ],
    "total_price": 899.99,
    "status": "pending",
    "shipping_address": {
      "line1": "123 Example Street",
      "line2": "Apt 4B",
      "city": "Example City",
      "state": "EX",
      "postal_code": "12345",
      "country": "Example Country"
    },
    "created_at": "2025-05-15T11:50:00.123456+00:00",
    "updated_at": "2025-05-15T11:50:00.123456+00:00"
  }
]
```

### Step 6.3: Update Order Status

```bash
curl -X PUT "http://localhost/api/v1/orders/$ORDER_ID_1/status" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "paid"
  }'
```

Expected response:
```json
{
  "_id": "order_id_1",
  "user_id": "1",
  "items": [
    {
      "product_id": "product_id_1",
      "quantity": 1,
      "price": 899.99
    }
  ],
  "total_price": 899.99,
  "status": "paid",
  "shipping_address": {
    "line1": "123 Example Street",
    "line2": "Apt 4B",
    "city": "Example City",
    "state": "EX",
    "postal_code": "12345",
    "country": "Example Country"
  },
  "created_at": "2025-05-15T11:50:00.123456+00:00",
  "updated_at": "2025-05-15T12:00:00.123456+00:00"
}
```

### Step 6.4: Cancel an Order

```bash
curl -X DELETE "http://localhost/api/v1/orders/$ORDER_ID_2" \
  -H "Authorization: Bearer $TOKEN"
```

This should return a 204 No Content status with no response body. Now let's verify the order was cancelled:

```bash
curl -X GET "http://localhost/api/v1/orders/$ORDER_ID_2" \
  -H "Authorization: Bearer $TOKEN"
```

Expected response:
```json
{
  "_id": "order_id_2",
  "user_id": "1",
  "items": [
    {
      "product_id": "product_id_2",
      "quantity": 1,
      "price": 249.99
    },
    {
      "product_id": "product_id_3",
      "quantity": 2,
      "price": 179.99
    }
  ],
  "total_price": 609.97,
  "status": "cancelled",
  "shipping_address": {
    "line1": "123 Example Street",
    "line2": "Apt 4B",
    "city": "Example City",
    "state": "EX",
    "postal_code": "12345",
    "country": "Example Country"
  },
  "created_at": "2025-05-15T11:55:00.123456+00:00",
  "updated_at": "2025-05-15T12:05:00.123456+00:00"
}
```

### Step 6.5: Check Inventory After Order Operations

Let's check the inventory for Product 1 after placing an order:

```bash
curl -X GET "http://localhost/api/v1/inventory/$PRODUCT_ID_1" \
  -H "Authorization: Bearer $TOKEN"
```

Expected response:
```json
{
  "product_id": "product_id_1",
  "available_quantity": 49,
  "reserved_quantity": 1,
  "reorder_threshold": 5,
  "id": 1,
  "created_at": "2025-05-15T11:40:00.123456+00:00",
  "updated_at": "2025-05-15T11:50:00.123456+00:00"
}
```

And check inventory for Product 2 after cancelling an order:

```bash
curl -X GET "http://localhost/api/v1/inventory/$PRODUCT_ID_2" \
  -H "Authorization: Bearer $TOKEN"
```

Expected response:
```json
{
  "product_id": "product_id_2",
  "available_quantity": 100,
  "reserved_quantity": 0,
  "reorder_threshold": 10,
  "id": 2,
  "created_at": "2025-05-15T11:41:00.123456+00:00",
  "updated_at": "2025-05-15T12:05:00.123456+00:00"
}
```

## 7. Verifying the Complete Workflow

To verify that the complete e-commerce flow works end-to-end with our integrated product-inventory system, we've successfully:

1. ✅ Registered a user account and authenticated
2. ✅ Added a shipping address
3. ✅ Created three different products with automatic inventory creation
4. ✅ Verified that inventory was created for each product
5. ✅ Browsed and filtered products
6. ✅ Placed orders for products
7. ✅ Viewed order details
8. ✅ Updated order status
9. ✅ Cancelled an order
10. ✅ Verified inventory changes after order operations

This confirms that all microservices are working together correctly and the data flows as expected through the system.