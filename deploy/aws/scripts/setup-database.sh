#!/bin/bash

# Source common functions
source $(dirname "$0")/common.sh

log "Starting database setup..."

# Create directories for data persistence
mkdir -p /data/mongodb/product
mkdir -p /data/mongodb/order
mkdir -p /data/postgresql/user
mkdir -p /data/postgresql/inventory
mkdir -p /data/postgresql/notification

# Set correct permissions
chown -R 1000:1000 /data/mongodb
chown -R 999:999 /data/postgresql

# Navigate to deployment directory
cd /home/ubuntu/ecommerce/ecommerce-microservices/deploy/aws

# Get the private IP
PRIVATE_IP=$(get_private_ip)
log "Database instance private IP: $PRIVATE_IP"

# Create environment file
replace_placeholders env/.env.database env/.env.database.generated \
  "DATABASE_HOST" "$PRIVATE_IP"

# Start the database containers
log "Starting database containers..."
docker-compose -f docker-compose/database-compose.yml up -d

log "Database services started successfully"

# Create a file to indicate setup is complete
touch /tmp/database_setup_complete

log "Database setup completed successfully" "$GREEN"