#!/bin/bash

# Source common functions
source $(dirname "$0")/common.sh

log "Starting messaging setup..."

# Create directories for data persistence
mkdir -p /data/rabbitmq
mkdir -p /data/redis
mkdir -p /data/kafka
mkdir -p /data/zookeeper

# Set correct permissions
chown -R 1000:1000 /data/rabbitmq
chown -R 1000:1000 /data/redis
chown -R 1000:1000 /data/kafka
chown -R 1000:1000 /data/zookeeper

# Navigate to deployment directory
cd /home/ubuntu/ecommerce/ecommerce-microservices/deploy/aws

# Get the private IP
PRIVATE_IP=$(get_private_ip)
log "Messaging instance private IP: $PRIVATE_IP"

# Create environment file
replace_placeholders env/.env.messaging env/.env.messaging.generated \
  "MESSAGING_HOST" "$PRIVATE_IP"

# Export the variable for docker-compose
export MESSAGING_HOST=$PRIVATE_IP

# Start the messaging containers
log "Starting messaging containers..."
docker-compose -f docker-compose/messaging-compose.yml up -d

log "Messaging services started successfully"

# Create a file to indicate setup is complete
touch /tmp/messaging_setup_complete

log "Messaging setup completed successfully" "$GREEN"