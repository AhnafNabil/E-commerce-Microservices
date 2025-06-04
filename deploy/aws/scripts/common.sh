#!/bin/bash

# Colors for terminal output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Print colored message
log() {
  local msg=$1
  local color=${2:-$GREEN}
  echo -e "${color}[$(date '+%Y-%m-%d %H:%M:%S')] $msg${NC}"
}

# Check if a command exists
command_exists() {
  command -v "$1" >/dev/null 2>&1
}

# Get the private IP of this instance
get_private_ip() {
  curl -s http://169.254.169.254/latest/meta-data/local-ipv4
}

# Wait for a service to be ready
wait_for_service() {
  local host=$1
  local port=$2
  local service_name=$3
  local max_retries=${4:-30}
  local retry_count=0
  
  log "Waiting for $service_name at $host:$port..." "$YELLOW"
  
  while ! nc -z $host $port; do
    retry_count=$((retry_count + 1))
    if [ $retry_count -ge $max_retries ]; then
      log "Failed to connect to $service_name after $max_retries attempts" "$RED"
      return 1
    fi
    log "Waiting for $service_name to be available... ($retry_count/$max_retries)" "$YELLOW"
    sleep 5
  done
  
  log "$service_name is available at $host:$port" "$GREEN"
  return 0
}

# Replace placeholders in a file
replace_placeholders() {
  local file=$1
  local output=$2
  shift 2
  
  # Create a copy of the input file
  cp $file $output
  
  # Process each key-value pair
  while [[ $# -gt 0 ]]; do
    local key=$1
    local value=$2
    shift 2
    
    # Replace placeholder with value
    sed -i "s|\${$key}|$value|g" $output
  done
}

# Get private IP of another instance by Name tag
get_instance_ip_by_name() {
  local instance_name=$1
  
  # Check if AWS CLI is available
  if ! command_exists aws; then
    log "AWS CLI not found. Installing..." "$YELLOW"
    apt-get update && apt-get install -y awscli
  fi
  
  # Get the instance private IP using AWS CLI
  local instance_ip=$(aws ec2 describe-instances \
    --filters "Name=tag:Name,Values=$instance_name" "Name=instance-state-name,Values=running" \
    --query "Reservations[0].Instances[0].PrivateIpAddress" \
    --output text --region $(curl -s http://169.254.169.254/latest/meta-data/placement/region))
  
  if [[ "$instance_ip" == "None" || -z "$instance_ip" ]]; then
    log "Could not find instance with name: $instance_name" "$RED"
    return 1
  fi
  
  echo "$instance_ip"
}