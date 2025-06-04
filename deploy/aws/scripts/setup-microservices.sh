#!/bin/bash

# Source common functions
source $(dirname "$0")/common.sh

log "Starting microservices setup..."

# Navigate to deployment directory
cd /home/ubuntu/ecommerce/ecommerce-microservices/deploy/aws

# Get the private IP of this instance
PRIVATE_IP=$(get_private_ip)
log "Microservices instance private IP: $PRIVATE_IP"

# Get database and messaging instance IPs
# In production, you would get these from EC2 metadata or tags
DATABASE_HOST=$(get_instance_ip_by_tag "Name" "ecommerce-database")
MESSAGING_HOST=$(get_instance_ip_by_tag "Name" "ecommerce-messaging")

log "Database host: $DATABASE_HOST"
log "Messaging host: $MESSAGING_HOST"

# Log the Mailtrap credentials (securely)
if [ -n "$SMTP_USER" ] && [ -n "$SMTP_PASSWORD" ]; then
  log "Using provided Mailtrap credentials"
  # Only show first few characters of password for security
  log "SMTP User: $SMTP_USER"
  log "SMTP Password: ${SMTP_PASSWORD:0:3}*** (masked for security)"
else
  log "Using default Mailtrap credentials" "$YELLOW"
  # Set defaults if not provided
  SMTP_USER="d71cdfb7303062"
  SMTP_PASSWORD="eb44359b140962"
fi

# Wait for database and messaging services to be available
wait_for_service $DATABASE_HOST 5432 "PostgreSQL"
wait_for_service $DATABASE_HOST 27017 "MongoDB"
wait_for_service $MESSAGING_HOST 5672 "RabbitMQ"
wait_for_service $MESSAGING_HOST 6379 "Redis"
wait_for_service $MESSAGING_HOST 29092 "Kafka"

# Create environment file
replace_placeholders env/.env.microservices env/.env.microservices.generated \
  "DATABASE_HOST" "$DATABASE_HOST" \
  "MESSAGING_HOST" "$MESSAGING_HOST" \
  "SMTP_USER" "$SMTP_USER" \
  "SMTP_PASSWORD" "$SMTP_PASSWORD"

# Export variables for docker-compose
export DATABASE_HOST=$DATABASE_HOST
export MESSAGING_HOST=$MESSAGING_HOST
export SMTP_USER=$SMTP_USER
export SMTP_PASSWORD=$SMTP_PASSWORD

# Start the microservices
log "Starting microservices..."
docker-compose -f docker-compose/microservices-compose.yml up -d

log "Microservices started successfully"

# Create a file to indicate setup is complete
touch /tmp/microservices_setup_complete

log "Microservices setup completed successfully" "$GREEN"