#!/bin/bash

# Source common functions
source $(dirname "$0")/common.sh

log "Starting Nginx setup..."

# Navigate to deployment directory
cd /home/ubuntu/ecommerce/ecommerce-microservices/deploy/aws

# Get microservices instance IP
MICROSERVICES_HOST=$(get_instance_ip_by_tag "Name" "ecommerce-microservices")
log "Microservices host: $MICROSERVICES_HOST"

# Wait for microservices to be available
wait_for_service $MICROSERVICES_HOST 8000 "Product Service"
wait_for_service $MICROSERVICES_HOST 8001 "Order Service"
wait_for_service $MICROSERVICES_HOST 8002 "Inventory Service"
wait_for_service $MICROSERVICES_HOST 8003 "User Service"
wait_for_service $MICROSERVICES_HOST 8004 "Notification Service"

# Create Nginx configuration
replace_placeholders config/nginx/default.conf config/nginx/default.conf.generated \
  "MICROSERVICES_HOST" "$MICROSERVICES_HOST"

# Create environment file
replace_placeholders env/.env.nginx env/.env.nginx.generated \
  "MICROSERVICES_HOST" "$MICROSERVICES_HOST"

# Export variable for docker-compose
export MICROSERVICES_HOST=$MICROSERVICES_HOST

# Start Nginx
log "Starting Nginx..."
docker-compose -f docker-compose/nginx-compose.yml up -d

log "Nginx started successfully"

# Create a file to indicate setup is complete
touch /tmp/nginx_setup_complete

log "Nginx setup completed successfully" "$GREEN"