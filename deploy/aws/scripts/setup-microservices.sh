#!/bin/bash

# Source common functions
source $(dirname "$0")/common.sh

log "Starting microservices setup..."

# FIXED: Navigate to correct deployment directory
cd /home/ubuntu/ecommerce/deploy/aws

# Get the private IP of this instance
PRIVATE_IP=$(get_private_ip)
log "Microservices instance private IP: $PRIVATE_IP"

# FIXED: Get database and messaging IPs using multiple methods
log "Discovering database and messaging instance IPs..."

# Method 1: Try environment variables set during instance creation (most reliable)
DATABASE_HOST="$DATABASE_HOST_ENV"
MESSAGING_HOST="$MESSAGING_HOST_ENV"

# Method 2: Try /etc/hosts entries if environment variables aren't set
if [[ -z "$DATABASE_HOST" ]]; then
  DATABASE_HOST=$(grep "database-host" /etc/hosts 2>/dev/null | awk '{print $1}')
  if [[ -n "$DATABASE_HOST" ]]; then
    log "Found DATABASE_HOST in /etc/hosts: $DATABASE_HOST"
  fi
fi

if [[ -z "$MESSAGING_HOST" ]]; then
  MESSAGING_HOST=$(grep "messaging-host" /etc/hosts 2>/dev/null | awk '{print $1}')
  if [[ -n "$MESSAGING_HOST" ]]; then
    log "Found MESSAGING_HOST in /etc/hosts: $MESSAGING_HOST"
  fi
fi

# Method 3: Try AWS CLI as last resort (requires IAM permissions)
if [[ -z "$DATABASE_HOST" ]] && command_exists aws; then
  log "Attempting AWS CLI lookup for database instance..."
  DATABASE_HOST=$(get_instance_ip_by_tag "Name" "ecommerce-database" 2>/dev/null)
fi

if [[ -z "$MESSAGING_HOST" ]] && command_exists aws; then
  log "Attempting AWS CLI lookup for messaging instance..."
  MESSAGING_HOST=$(get_instance_ip_by_tag "Name" "ecommerce-messaging" 2>/dev/null)
fi

# FIXED: Validate we have the required IPs
if [[ -z "$DATABASE_HOST" ]]; then
  log "Error: DATABASE_HOST not found. Available methods:" "$RED"
  log "1. Environment variable DATABASE_HOST_ENV not set" "$RED"
  log "2. No entry in /etc/hosts for database-host" "$RED"
  log "3. AWS CLI lookup failed" "$RED"
  log "Current environment variables:" "$YELLOW"
  env | grep -E "(DATABASE|HOST)" || log "No DATABASE/HOST env vars found"
  exit 1
fi

if [[ -z "$MESSAGING_HOST" ]]; then
  log "Error: MESSAGING_HOST not found. Available methods:" "$RED"
  log "1. Environment variable MESSAGING_HOST_ENV not set" "$RED"
  log "2. No entry in /etc/hosts for messaging-host" "$RED"
  log "3. AWS CLI lookup failed" "$RED"
  exit 1
fi

log "Database host: $DATABASE_HOST"
log "Messaging host: $MESSAGING_HOST"

# Get SMTP credentials (should be set during instance creation)
if [[ -z "$SMTP_USER" ]]; then
  log "Warning: SMTP_USER not set, using default" "$YELLOW"
  SMTP_USER="8f17fc1a376da4"
fi

if [[ -z "$SMTP_PASSWORD" ]]; then
  log "Warning: SMTP_PASSWORD not set, using default" "$YELLOW"  
  SMTP_PASSWORD="afb5060d93cdaf"
fi

log "SMTP User: $SMTP_USER"
log "SMTP Password: ${SMTP_PASSWORD:0:3}*** (masked)"

# Wait for database and messaging services to be available
log "Waiting for database services to be available..."
wait_for_service "$DATABASE_HOST" 5432 "PostgreSQL User DB" 10
wait_for_service "$DATABASE_HOST" 5433 "PostgreSQL Inventory DB" 10
wait_for_service "$DATABASE_HOST" 5434 "PostgreSQL Notification DB" 10
wait_for_service "$DATABASE_HOST" 27017 "MongoDB Product DB" 10
wait_for_service "$DATABASE_HOST" 27018 "MongoDB Order DB" 10

log "Waiting for messaging services to be available..."
wait_for_service "$MESSAGING_HOST" 5672 "RabbitMQ" 10
wait_for_service "$MESSAGING_HOST" 6379 "Redis" 10
wait_for_service "$MESSAGING_HOST" 29092 "Kafka" 10

# FIXED: Create environment file using simple replacement
log "Creating environment configuration..."

# Check if template file exists
if [[ ! -f "env/.env.microservices" ]]; then
  log "Error: Template file env/.env.microservices not found" "$RED"
  log "Available files in env/:" "$YELLOW"
  ls -la env/ || log "env/ directory not found"
  exit 1
fi

# Use placeholder replacement
replace_placeholders env/.env.microservices env/.env.microservices.generated \
  "DATABASE_HOST" "$DATABASE_HOST" \
  "MESSAGING_HOST" "$MESSAGING_HOST" \
  "SMTP_USER" "$SMTP_USER" \
  "SMTP_PASSWORD" "$SMTP_PASSWORD"

# FIXED: Validate the generated environment file
log "Validating generated environment file..."
if [[ ! -f "env/.env.microservices.generated" ]]; then
  log "Error: Failed to generate environment file" "$RED"
  exit 1
fi

# Check for unresolved placeholders
if grep -q "_PLACEHOLDER\|\${" env/.env.microservices.generated; then
  log "Error: Environment file contains unresolved placeholders:" "$RED"
  grep "_PLACEHOLDER\|\${" env/.env.microservices.generated
  log "Debug: Template file contents:" "$YELLOW"
  cat env/.env.microservices
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
export DATABASE_HOST="$DATABASE_HOST"
export MESSAGING_HOST="$MESSAGING_HOST"
export SMTP_USER="$SMTP_USER"
export SMTP_PASSWORD="$SMTP_PASSWORD"

# Check if docker-compose file exists
if [[ ! -f "docker-compose/microservices-compose.yml" ]]; then
  log "Error: Docker compose file not found" "$RED"
  log "Available files:" "$YELLOW"
  find . -name "*.yml" -o -name "*.yaml" 2>/dev/null || log "No compose files found"
  exit 1
fi

# Start the microservices
log "Starting microservices..."
docker-compose -f docker-compose/microservices-compose.yml up -d

# Monitor startup
log "Monitoring microservice startup..."
sleep 15

# Check service health
for service in product-service order-service inventory-service user-service notification-service; do
  if docker ps | grep -q "$service.*Up"; then
    log "$service started successfully" "$GREEN"
  else
    log "$service may have issues, checking logs..." "$YELLOW"
    docker logs "${service}" 2>/dev/null | tail -5 || log "Could not get logs for $service"
  fi
done

log "Microservices setup completed"

# Create a file to indicate setup is complete
touch /tmp/microservices_setup_complete

log "Microservices setup completed successfully" "$GREEN"