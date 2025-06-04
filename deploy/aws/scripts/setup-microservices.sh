#!/bin/bash

# Source common functions
source $(dirname "$0")/common.sh

log "Starting microservices setup..."

# Navigate to deployment directory
cd /home/ubuntu/ecommerce/ecommerce-microservices/deploy/aws

# Get the private IP of this instance
PRIVATE_IP=$(get_private_ip)
log "Microservices instance private IP: $PRIVATE_IP"

# Get database and messaging instance IPs using multiple methods
log "Discovering database and messaging instance IPs..."

# Method 1: Try to get from AWS tags (requires AWS CLI and IAM permissions)
DATABASE_HOST=$(get_instance_ip_by_tag "Name" "ecommerce-database" 2>/dev/null)
MESSAGING_HOST=$(get_instance_ip_by_tag "Name" "ecommerce-messaging" 2>/dev/null)

# Method 2: Fallback to environment variables if set during instance creation
if [[ -z "$DATABASE_HOST" && -n "$DATABASE_HOST_ENV" ]]; then
  DATABASE_HOST="$DATABASE_HOST_ENV"
  log "Using DATABASE_HOST from environment: $DATABASE_HOST"
fi

if [[ -z "$MESSAGING_HOST" && -n "$MESSAGING_HOST_ENV" ]]; then
  MESSAGING_HOST="$MESSAGING_HOST_ENV"
  log "Using MESSAGING_HOST from environment: $MESSAGING_HOST"
fi

# Method 3: Try to discover via /etc/hosts entries (if added during instance creation)
if [[ -z "$DATABASE_HOST" ]]; then
  DATABASE_HOST=$(grep "database-host" /etc/hosts | awk '{print $1}' 2>/dev/null)
  if [[ -n "$DATABASE_HOST" ]]; then
    log "Found DATABASE_HOST in /etc/hosts: $DATABASE_HOST"
  fi
fi

if [[ -z "$MESSAGING_HOST" ]]; then
  MESSAGING_HOST=$(grep "messaging-host" /etc/hosts | awk '{print $1}' 2>/dev/null)
  if [[ -n "$MESSAGING_HOST" ]]; then
    log "Found MESSAGING_HOST in /etc/hosts: $MESSAGING_HOST"
  fi
fi

# Validate we have the required IPs
if [[ -z "$DATABASE_HOST" ]]; then
  log "Error: DATABASE_HOST not found. Please check instance tags or environment." "$RED"
  exit 1
fi

if [[ -z "$MESSAGING_HOST" ]]; then
  log "Error: MESSAGING_HOST not found. Please check instance tags or environment." "$RED"
  exit 1
fi

log "Database host: $DATABASE_HOST"
log "Messaging host: $MESSAGING_HOST"

# Get SMTP credentials (should be set during instance creation)
if [[ -z "$SMTP_USER" ]]; then
  log "Warning: SMTP_USER not set, using default" "$YELLOW"
  SMTP_USER="d71cdfb7303062"
fi

if [[ -z "$SMTP_PASSWORD" ]]; then
  log "Warning: SMTP_PASSWORD not set, using default" "$YELLOW"  
  SMTP_PASSWORD="eb44359b140962"
fi

log "SMTP User: $SMTP_USER"
log "SMTP Password: ${SMTP_PASSWORD:0:3}*** (masked)"

# Wait for database and messaging services to be available
log "Waiting for database services to be available..."
wait_for_service $DATABASE_HOST 5432 "PostgreSQL User DB"
wait_for_service $DATABASE_HOST 5433 "PostgreSQL Inventory DB" 
wait_for_service $DATABASE_HOST 5434 "PostgreSQL Notification DB"
wait_for_service $DATABASE_HOST 27017 "MongoDB Product DB"
wait_for_service $DATABASE_HOST 27018 "MongoDB Order DB"

log "Waiting for messaging services to be available..."
wait_for_service $MESSAGING_HOST 5672 "RabbitMQ"
wait_for_service $MESSAGING_HOST 6379 "Redis"
wait_for_service $MESSAGING_HOST 29092 "Kafka"

# Create environment file using the improved function
log "Creating environment configuration..."

# Option 1: Use placeholder replacement (recommended)
replace_placeholders env/.env.microservices env/.env.microservices.generated \
  "DATABASE_HOST" "$DATABASE_HOST" \
  "MESSAGING_HOST" "$MESSAGING_HOST" \
  "SMTP_USER" "$SMTP_USER" \
  "SMTP_PASSWORD" "$SMTP_PASSWORD"

# Option 2: Alternative using environment variables (uncomment if needed)
# export DATABASE_HOST=$DATABASE_HOST
# export MESSAGING_HOST=$MESSAGING_HOST  
# export SMTP_USER=$SMTP_USER
# export SMTP_PASSWORD=$SMTP_PASSWORD
# replace_env_vars env/.env.microservices env/.env.microservices.generated

# Validate the generated environment file
log "Validating generated environment file..."
if [[ ! -f "env/.env.microservices.generated" ]]; then
  log "Error: Failed to generate environment file" "$RED"
  exit 1
fi

# Check for unresolved placeholders
if grep -q "_PLACEHOLDER\|\${" env/.env.microservices.generated; then
  log "Error: Environment file contains unresolved placeholders:" "$RED"
  grep "_PLACEHOLDER\|\${" env/.env.microservices.generated
  exit 1
fi

# Show key configuration values for verification
log "Generated configuration summary:"
echo "=== Database Configuration ==="
grep "DATABASE_URL\|MONGODB_URI" env/.env.microservices.generated

echo "=== Messaging Configuration ==="
grep "RABBITMQ_URL\|REDIS_URL\|KAFKA_BOOTSTRAP" env/.env.microservices.generated

echo "=== SMTP Configuration ==="
grep "SMTP_" env/.env.microservices.generated

# Export variables for docker-compose
export DATABASE_HOST=$DATABASE_HOST
export MESSAGING_HOST=$MESSAGING_HOST
export SMTP_USER=$SMTP_USER
export SMTP_PASSWORD=$SMTP_PASSWORD

# Start the microservices
log "Starting microservices..."
docker-compose -f docker-compose/microservices-compose.yml up -d

# Monitor startup
log "Monitoring microservice startup..."
sleep 10

# Check service health
for service in product-service order-service inventory-service user-service notification-service; do
  if docker ps | grep -q "$service.*Up"; then
    log "$service started successfully" "$GREEN"
  else
    log "$service may have issues, checking logs..." "$YELLOW"
    docker logs "$service" | tail -5
  fi
done

log "Microservices started successfully"

# Create a file to indicate setup is complete
touch /tmp/microservices_setup_complete

log "Microservices setup completed successfully" "$GREEN"