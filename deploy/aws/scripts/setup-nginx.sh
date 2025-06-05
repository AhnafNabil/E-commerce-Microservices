#!/bin/bash
set -e  # Exit on any error

# Source common functions
source $(dirname "$0")/common.sh

log "Starting Nginx setup..."

# Navigate to deployment directory
cd /home/ubuntu/ecommerce/deploy/aws

# Check if environment variable is already set (from Pulumi)
if [ -n "$MICROSERVICES_HOST" ]; then
  log "Using MICROSERVICES_HOST from environment: $MICROSERVICES_HOST"
else
  log "MICROSERVICES_HOST not set, trying to discover..." "$YELLOW"
  
  # Install AWS CLI if not present
  if ! command_exists aws; then
    log "Installing AWS CLI..." "$YELLOW"
    apt-get update && apt-get install -y awscli
  fi
  
  # Get microservices instance IP using AWS CLI
  MICROSERVICES_HOST=$(get_instance_ip_by_name "ecommerce-microservices")
  
  if [ -z "$MICROSERVICES_HOST" ]; then
    log "Failed to discover microservices IP. Exiting..." "$RED"
    exit 1
  fi
fi

log "Final Microservices host: $MICROSERVICES_HOST"

# Wait for microservices to be available
log "Waiting for microservices to be ready..."
wait_for_service $MICROSERVICES_HOST 8000 "Product Service"
wait_for_service $MICROSERVICES_HOST 8001 "Order Service"
wait_for_service $MICROSERVICES_HOST 8002 "Inventory Service"
wait_for_service $MICROSERVICES_HOST 8003 "User Service"
wait_for_service $MICROSERVICES_HOST 8004 "Notification Service"

# Create Nginx configuration with proper IP replacement
log "Creating Nginx configuration..."
replace_placeholders config/nginx/default.conf config/nginx/default.conf.tmp \
  "MICROSERVICES_HOST" "$MICROSERVICES_HOST"

# Verify the generated config has real IPs, not placeholders
if grep -q '${MICROSERVICES_HOST}' config/nginx/default.conf.tmp; then
  log "ERROR: Placeholder not replaced in nginx config" "$RED"
  exit 1
fi

# Verify the generated config has the correct IP
if ! grep -q "$MICROSERVICES_HOST:8000" config/nginx/default.conf.tmp; then
  log "ERROR: Microservices IP not found in nginx config" "$RED"
  exit 1
fi

# Overwrite the original config file with the processed one
mv config/nginx/default.conf.tmp config/nginx/default.conf

log "Final Nginx configuration:"
head -20 config/nginx/default.conf

# Export variable for docker-compose
export MICROSERVICES_HOST=$MICROSERVICES_HOST

# Verify Docker is running
if ! systemctl is-active --quiet docker; then
  log "Starting Docker service..." "$YELLOW"
  sudo systemctl start docker
  sleep 5
fi

# Start Nginx
log "Starting Nginx..."
docker-compose -f docker-compose/nginx-compose.yml down 2>/dev/null || true
docker-compose -f docker-compose/nginx-compose.yml up -d

# Wait for nginx to start
log "Waiting for Nginx to initialize..."
sleep 10

# Check container status
log "Nginx container status:"
docker-compose -f docker-compose/nginx-compose.yml ps

# Verify nginx is working
log "Testing Nginx configuration..."
for i in {1..30}; do
  if curl -s http://localhost/health > /dev/null; then
    log "Nginx is responding to health checks" "$GREEN"
    break
  fi
  log "Waiting for Nginx to respond... ($i/30)" "$YELLOW"
  sleep 5
done

# Create a file to indicate setup is complete
touch /tmp/nginx_setup_complete

log "Nginx setup completed successfully" "$GREEN"