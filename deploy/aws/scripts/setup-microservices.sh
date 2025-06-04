#!/bin/bash

# Source common functions
source $(dirname "$0")/common.sh

log "Starting microservices setup..."

# Navigate to deployment directory
cd /home/ubuntu/ecommerce/deploy/aws

# Get the private IP of this instance
PRIVATE_IP=$(get_private_ip)
log "Microservices instance private IP: $PRIVATE_IP"

# Check if environment variables are already set (from Pulumi)
if [ -n "$DATABASE_HOST" ] && [ -n "$MESSAGING_HOST" ]; then
  log "Using environment variables from Pulumi"
  log "Database host: $DATABASE_HOST"
  log "Messaging host: $MESSAGING_HOST"
else
  log "Environment variables not set, trying to load from file..." "$YELLOW"
  
  # Try to load from the file created by Pulumi
  if [ -f "/home/ubuntu/service_ips.env" ]; then
    source /home/ubuntu/service_ips.env
    log "Loaded IPs from service_ips.env"
    log "Database host: $DATABASE_HOST"
    log "Messaging host: $MESSAGING_HOST"
  else
    log "No service IPs file found, deployment may fail" "$RED"
    exit 1
  fi
fi

# Set SMTP credentials
if [ -n "$SMTP_USER" ] && [ -n "$SMTP_PASSWORD" ]; then
  log "Using provided Mailtrap credentials"
  log "SMTP User: $SMTP_USER"
  log "SMTP Password: ${SMTP_PASSWORD:0:3}*** (masked)"
else
  log "Setting default SMTP credentials" "$YELLOW"
  SMTP_USER="d71cdfb7303062"
  SMTP_PASSWORD="eb44359b140962"
fi

# Wait for database and messaging services to be available
log "Waiting for dependent services..."
wait_for_service $DATABASE_HOST 5432 "PostgreSQL"
wait_for_service $DATABASE_HOST 27017 "MongoDB"
wait_for_service $MESSAGING_HOST 5672 "RabbitMQ"
wait_for_service $MESSAGING_HOST 6379 "Redis"
wait_for_service $MESSAGING_HOST 29092 "Kafka"

# Create environment file
log "Creating environment configuration..."
replace_placeholders env/.env.microservices env/.env.microservices.generated \
  "DATABASE_HOST" "$DATABASE_HOST" \
  "MESSAGING_HOST" "$MESSAGING_HOST" \
  "SMTP_USER" "$SMTP_USER" \
  "SMTP_PASSWORD" "$SMTP_PASSWORD"

# Verify the generated file exists and has content
if [ ! -f "env/.env.microservices.generated" ]; then
  log "Failed to create environment file" "$RED"
  exit 1
fi

log "Generated environment file:"
head -10 env/.env.microservices.generated

# Export variables for docker-compose
export DATABASE_HOST=$DATABASE_HOST
export MESSAGING_HOST=$MESSAGING_HOST
export SMTP_USER=$SMTP_USER
export SMTP_PASSWORD=$SMTP_PASSWORD

# Build and start the microservices
log "Building and starting microservices..."
docker-compose -f docker-compose/microservices-compose.yml build --no-cache
docker-compose -f docker-compose/microservices-compose.yml up -d

# Wait for services to start
log "Waiting for services to initialize..."
sleep 30

# Check container status
log "Container status:"
docker-compose -f docker-compose/microservices-compose.yml ps

# Check if all services are healthy
log "Checking service health..."
for service in user-service product-service order-service inventory-service notification-service; do
  container_id=$(docker-compose -f docker-compose/microservices-compose.yml ps -q $service)
  if [ -n "$container_id" ]; then
    status=$(docker inspect --format='{{.State.Status}}' $container_id)
    log "$service status: $status"
    if [ "$status" != "running" ]; then
      log "$service is not running. Checking logs..." "$YELLOW"
      docker-compose -f docker-compose/microservices-compose.yml logs --tail=20 $service
    fi
  else
    log "$service container not found" "$RED"
  fi
done

# Create completion marker
touch /tmp/microservices_setup_complete

log "Microservices setup completed!" "$GREEN"