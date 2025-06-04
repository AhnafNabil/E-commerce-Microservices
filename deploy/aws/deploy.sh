#!/bin/bash

# Get the type of instance from command line argument
INSTANCE_TYPE=$1

# If no instance type provided, try to determine from EC2 tags
if [ -z "$INSTANCE_TYPE" ]; then
  # Check if we're on EC2
  if curl -s http://169.254.169.254/latest/meta-data/ > /dev/null; then
    # Try to get the instance type from tags
    # In a real scenario, you'd need to set up IAM permissions for this
    INSTANCE_TYPE=$(aws ec2 describe-tags --filters "Name=resource-id,Values=$(curl -s http://169.254.169.254/latest/meta-data/instance-id)" "Name=key,Values=Type" --query "Tags[0].Value" --output text)
  fi
fi

# Source common functions
source $(dirname "$0")/scripts/common.sh

log "Starting deployment for instance type: $INSTANCE_TYPE" "$YELLOW"

# Run the appropriate setup script based on instance type
case $INSTANCE_TYPE in
  database|db)
    log "Running database setup..."
    bash $(dirname "$0")/scripts/setup-database.sh
    ;;
  messaging|mq)
    log "Running messaging setup..."
    bash $(dirname "$0")/scripts/setup-messaging.sh
    ;;
  microservices|ms)
    log "Running microservices setup..."
    bash $(dirname "$0")/scripts/setup-microservices.sh
    ;;
  nginx|gateway|gw)
    log "Running Nginx setup..."
    bash $(dirname "$0")/scripts/setup-nginx.sh
    ;;
  *)
    log "Unknown instance type: $INSTANCE_TYPE" "$RED"
    log "Valid types: database, messaging, microservices, nginx" "$RED"
    exit 1
    ;;
esac

log "Deployment completed for $INSTANCE_TYPE instance" "$GREEN"