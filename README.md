# E-commerce Microservices Deployment Guide

This documentation provides comprehensive instructions for deploying the e-commerce microservices application on AWS infrastructure using Pulumi, followed by verification steps to ensure everything is working correctly.

## Part 1: Deployment Process

### Prerequisites

1. **Local Environment Setup**
   - Install Pulumi CLI
   - Install AWS CLI and configure with appropriate credentials
   - Install Python 3.8+
   - Generate or use an existing EC2 key pair named "EcommerceKeyPair"

2. **Repository Preparation**
   - Clone your e-commerce microservices repository
   - Create the deployment directory structure as outlined below

### Step 1: Create Deployment Files in Repository

Create the following directory structure in your repository:

```
deploy/
└── aws/
    ├── docker-compose/
    │   ├── database-compose.yml
    │   ├── messaging-compose.yml
    │   ├── microservices-compose.yml
    │   └── nginx-compose.yml
    ├── env/
    │   ├── .env.database
    │   ├── .env.messaging
    │   ├── .env.microservices
    │   └── .env.nginx
    ├── config/
    │   └── nginx/
    │       └── default.conf
    ├── scripts/
    │   ├── common.sh
    │   ├── setup-database.sh
    │   ├── setup-messaging.sh
    │   ├── setup-microservices.sh
    │   └── setup-nginx.sh
    └── deploy.sh
```

Populate these files with the content provided in the previous responses. The key files are:

- Docker Compose files for each instance type
- Environment templates with placeholders
- Configuration templates (e.g., Nginx)
- Deployment scripts

### Step 2: Create Pulumi Project

1. Create a new directory for your Pulumi project:
   ```bash
   mkdir ecommerce-infra && cd ecommerce-infra
   ```

2. Initialize a new Pulumi project:
   ```bash
   pulumi new aws-python
   ```

3. Replace the `__main__.py` content with the Pulumi code provided in the previous response.

4. Update Mailtrap credentials in the Pulumi code:
   ```python
   # Update these values with your Mailtrap credentials
   smtp_user = "your_mailtrap_username"
   smtp_password = "your_mailtrap_password"
   ```

5. Ensure you have the EC2 key pair named "EcommerceKeyPair" in your AWS account:
   - If not, create one through the AWS Console or CLI
   - Download and securely store the private key (.pem file)

### Step 3: Deploy the Infrastructure

1. Preview the deployment:
   ```bash
   pulumi preview
   ```

2. Deploy the infrastructure:
   ```bash
   pulumi up
   ```

3. Note the outputs from the deployment, especially:
   - `nginx_instance_public_ip`
   - `microservices_instance_public_ip`
   - Private IPs for database and messaging instances



```bash
# Step 1: From your LOCAL machine, copy the key to microservices instance
scp -i EcommerceKeyPair.pem EcommerceKeyPair.pem ubuntu@<microservices_public_ip>:/home/ubuntu/

# Step 2: SSH into microservices instance  
ssh -i EcommerceKeyPair.pem ubuntu@<microservices_public_ip>

# Step 3: Set correct permissions on the copied key
chmod 400 /home/ubuntu/EcommerceKeyPair.pem

# Step 4: Now you can SSH to database instance
ssh -i /home/ubuntu/EcommerceKeyPair.pem ubuntu@10.0.3.222
```

### Step 4: Wait for Deployment Completion

The user data scripts will automatically:
1. Install Docker and Docker Compose
2. Clone your repository
3. Run the appropriate deployment scripts for each instance
4. Configure and start the services

This process takes approximately 10-15 minutes to complete. You can monitor progress by SSH-ing into the instances.

## Part 2: Verification Process

Follow these steps to verify your deployment is working correctly.

### Step 1: Verify SSH Access to Instances

1. Connect to the Nginx instance:
   ```bash
   ssh -i EcommerceKeyPair.pem ubuntu@<nginx_instance_public_ip>
   ```

2. Connect to the Microservices instance:
   ```bash
   ssh -i EcommerceKeyPair.pem ubuntu@<microservices_instance_public_ip>
   ```

3. Connect to private instances through the Microservices instance:
   ```bash
   # From the microservices instance
   ssh ubuntu@<database_instance_private_ip>
   ssh ubuntu@<messaging_instance_private_ip>
   ```

4. SSH into the instance and check logs: 

    ```bash
    cat /var/log/cloud-init-output.log
    ```

### Step 2: Verify Docker Services on Each Instance

#### Database Instance
```bash
ssh -i EcommerceKeyPair.pem ubuntu@<database_instance_private_ip>
docker ps

# Expected output:
# Containers for MongoDB and PostgreSQL should be running
```

#### Messaging Instance
```bash
ssh -i EcommerceKeyPair.pem ubuntu@<messaging_instance_private_ip>
docker ps

# Expected output:
# Containers for RabbitMQ, Redis, Kafka, and Zookeeper should be running
```

#### Microservices Instance
```bash
ssh -i EcommerceKeyPair.pem ubuntu@<microservices_instance_public_ip>
docker ps

# Expected output:
# Containers for all five microservices should be running
```

#### Nginx Instance
```bash
ssh -i EcommerceKeyPair.pem ubuntu@<nginx_instance_public_ip>
docker ps

# Expected output:
# Nginx container should be running
```

### Step 3: Check Container Logs

Check logs for any errors or issues:

```bash
# Example for checking product service logs on microservices instance
docker logs product-service

# Example for checking database logs
docker logs mongodb-product
```

### Step 4: Verify API Endpoints

Test the API endpoints through the Nginx gateway:

1. Register a user:
   ```bash
   curl -X POST "http://<nginx_instance_public_ip>/api/v1/auth/register" \
     -H "Content-Type: application/json" \
     -d '{
       "email": "test@example.com",
       "password": "Password123",
       "first_name": "Test",
       "last_name": "User",
       "phone": "555-123-4567"
     }'
   ```

2. Login to get an access token:
   ```bash
   curl -X POST "http://<nginx_instance_public_ip>/api/v1/auth/login" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "username=test@example.com&password=Password123"
   ```

3. Create a product using the token:
   ```bash
   curl -X POST "http://<nginx_instance_public_ip>/api/v1/products/" \
     -H "Authorization: Bearer <access_token>" \
     -H "Content-Type: application/json" \
     -d '{
       "name": "Test Product",
       "description": "This is a test product",
       "category": "Test",
       "price": 99.99,
       "quantity": 10
     }'
   ```

4. Retrieve products:
   ```bash
   curl "http://<nginx_instance_public_ip>/api/v1/products/"
   ```

### Step 5: Verify Messaging Integration

1. Check RabbitMQ Management Interface:
   - Access http://<microservices_instance_public_ip>:15672
   - Login with guest/guest
   - Verify queues are created

2. Check Kafka UI:
   - Access http://<microservices_instance_public_ip>:8082
   - Verify topics are created

3. Test order creation and inventory interaction:
   ```bash
   # Create an order
   curl -X POST "http://<nginx_instance_public_ip>/api/v1/orders/" \
     -H "Authorization: Bearer <access_token>" \
     -H "Content-Type: application/json" \
     -d '{
       "user_id": "<user_id>",
       "items": [
         {
           "product_id": "<product_id>",
           "quantity": 1,
           "price": 99.99
         }
       ],
       "shipping_address": {
         "line1": "123 Test St",
         "city": "Test City",
         "state": "TS",
         "postal_code": "12345",
         "country": "Testland"
       }
     }'
   ```

4. Verify the order was created and inventory was updated:
   ```bash
   # Check order status
   curl "http://<nginx_instance_public_ip>/api/v1/orders/<order_id>" \
     -H "Authorization: Bearer <access_token>"
     
   # Check inventory status
   curl "http://<nginx_instance_public_ip>/api/v1/inventory/<product_id>" \
     -H "Authorization: Bearer <access_token>"
   ```

### Step 6: Verify Notification Service

1. Create a low-stock condition:
   ```bash
   # Update inventory to trigger low stock
   curl -X PUT "http://<nginx_instance_public_ip>/api/v1/inventory/<product_id>" \
     -H "Authorization: Bearer <access_token>" \
     -H "Content-Type: application/json" \
     -d '{
       "available_quantity": 3,
       "reorder_threshold": 5
     }'
   ```

2. Check email notifications:
   - Login to your Mailtrap account
   - Verify a low stock notification was received

3. Test the notification service directly:
   ```bash
   curl -X POST "http://<nginx_instance_public_ip>/api/v1/notifications/test"
   ```

### Step 7: Check System Health

Verify the health endpoints for all services:

```bash
# Nginx health
curl "http://<nginx_instance_public_ip>/health"

# Service health checks
curl "http://<nginx_instance_public_ip>/api/v1/products/health"
curl "http://<nginx_instance_public_ip>/api/v1/orders/health"
curl "http://<nginx_instance_public_ip>/api/v1/inventory/health"
curl "http://<nginx_instance_public_ip>/api/v1/users/health"
curl "http://<nginx_instance_public_ip>/api/v1/notifications/health"
```

## Troubleshooting Common Issues

### Services Not Starting

1. Check if Docker is running:
   ```bash
   systemctl status docker
   ```

2. Check deployment logs:
   ```bash
   cat /var/log/cloud-init-output.log
   ```

3. Check Docker Compose logs:
   ```bash
   cd /home/ubuntu/ecommerce/deploy/aws
   docker-compose -f docker-compose/microservices-compose.yml logs
   ```

### Connectivity Issues

1. Verify security group rules are correctly set up:
   ```bash
   # Check connectivity from microservices to database
   telnet <database_instance_private_ip> 5432
   telnet <database_instance_private_ip> 27017
   
   # Check connectivity from microservices to messaging
   telnet <messaging_instance_private_ip> 5672
   telnet <messaging_instance_private_ip> 6379
   telnet <messaging_instance_private_ip> 29092
   ```

2. Check route tables and NAT gateway:
   - Ensure private instances can access the internet for package installation

### Microservices Communication Issues

1. Check environment variables:
   ```bash
   docker exec product-service env | grep SERVICE_URL
   ```

2. Verify service discovery is working:
   ```bash
   # On microservices instance
   cat /home/ubuntu/ecommerce/deploy/aws/env/.env.microservices.generated
   ```

## Clean Up

To remove all AWS resources when done testing:

```bash
pulumi destroy
```

This will terminate all instances and remove the associated networking resources.