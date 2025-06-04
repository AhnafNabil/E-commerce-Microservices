#!/bin/bash

# Colors for terminal output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Print colored message
log() {
  local msg="$1"
  local color="${2:-$GREEN}"
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

# FIXED: Wait for a service to be ready with proper parameter handling
wait_for_service() {
  local host="$1"
  local port="$2"
  local service_name="$3"
  local max_retries="${4:-30}"
  local retry_count=0
  
  # Debug: Log received parameters
  log "DEBUG: host='$host' port='$port' service='$service_name' max_retries='$max_retries'" "$YELLOW"
  
  # Validate parameters
  if [[ -z "$host" ]]; then
    log "Error: Host parameter is empty" "$RED"
    return 1
  fi
  
  if [[ -z "$port" || ! "$port" =~ ^[0-9]+$ ]]; then
    log "Error: Port parameter is invalid: '$port'" "$RED"
    return 1
  fi
  
  if [[ ! "$max_retries" =~ ^[0-9]+$ ]]; then
    log "Warning: max_retries is not a number: '$max_retries', using default 30" "$YELLOW"
    max_retries=30
  fi
  
  log "Waiting for $service_name at $host:$port..." "$YELLOW"
  
  while ! nc -z "$host" "$port" 2>/dev/null; do
    retry_count=$((retry_count + 1))
    if [ "$retry_count" -ge "$max_retries" ]; then
      log "Failed to connect to $service_name after $max_retries attempts" "$RED"
      return 1
    fi
    log "Waiting for $service_name to be available... ($retry_count/$max_retries)" "$YELLOW"
    sleep 5
  done
  
  log "$service_name is available at $host:$port" "$GREEN"
  return 0
}

# FIXED: Enhanced replace_placeholders function
replace_placeholders() {
  local input_file="$1"
  local output_file="$2"
  shift 2
  
  log "Processing template: $input_file -> $output_file" "$YELLOW"
  
  # Validate input file exists
  if [[ ! -f "$input_file" ]]; then
    log "Error: Input file $input_file does not exist" "$RED"
    return 1
  fi
  
  # Create a copy of the input file
  cp "$input_file" "$output_file"
  
  # Process each key-value pair
  while [[ $# -gt 1 ]]; do
    local placeholder="$1"
    local value="$2"
    shift 2
    
    log "Replacing ${placeholder}_PLACEHOLDER with: $value" "$YELLOW"
    
    # Replace placeholder with value using more robust sed
    if [[ -n "$value" ]]; then
      sed -i "s|${placeholder}_PLACEHOLDER|${value}|g" "$output_file"
    else
      log "Warning: Empty value for placeholder $placeholder" "$YELLOW"
    fi
  done
  
  # Handle odd number of arguments
  if [[ $# -eq 1 ]]; then
    log "Warning: Odd number of arguments, ignoring: $1" "$YELLOW"
  fi
  
  # Verify replacements were successful
  if grep -q "_PLACEHOLDER" "$output_file"; then
    log "Warning: Some placeholders were not replaced in $output_file:" "$YELLOW"
    grep "_PLACEHOLDER" "$output_file"
  else
    log "All placeholders successfully replaced in $output_file" "$GREEN"
  fi
}

# ALTERNATIVE: Direct environment variable replacement function
replace_env_vars() {
  local input_file="$1"
  local output_file="$2"
  
  log "Processing environment template: $input_file -> $output_file" "$YELLOW"
  
  # Use envsubst to replace environment variables
  if command_exists envsubst; then
    envsubst < "$input_file" > "$output_file"
    log "Environment variables replaced using envsubst" "$GREEN"
  else
    # Fallback to manual replacement
    cp "$input_file" "$output_file"
    
    # Replace common patterns
    if [[ -n "$DATABASE_HOST" ]]; then
      sed -i "s|\${DATABASE_HOST}|${DATABASE_HOST}|g" "$output_file"
    fi
    if [[ -n "$MESSAGING_HOST" ]]; then
      sed -i "s|\${MESSAGING_HOST}|${MESSAGING_HOST}|g" "$output_file"
    fi
    if [[ -n "$SMTP_USER" ]]; then
      sed -i "s|\${SMTP_USER}|${SMTP_USER}|g" "$output_file"
    fi
    if [[ -n "$SMTP_PASSWORD" ]]; then
      sed -i "s|\${SMTP_PASSWORD}|${SMTP_PASSWORD}|g" "$output_file"
    fi
    
    log "Environment variables replaced manually" "$GREEN"
  fi
  
  # Verify no unresolved variables remain
  if grep -q '\${' "$output_file"; then
    log "Warning: Unresolved environment variables found:" "$YELLOW"
    grep '\${' "$output_file"
  fi
}

# FIXED: Get instance IP by tag with better error handling
get_instance_ip_by_tag() {
  local tag_key="$1"
  local tag_value="$2"
  
  log "Looking up instance with ${tag_key}=${tag_value}" "$YELLOW"
  
  # Check if AWS CLI is available
  if ! command_exists aws; then
    log "AWS CLI not found. Installing..." "$YELLOW"
    apt-get update && apt-get install -y awscli
  fi
  
  # Get the region
  local region=$(curl -s http://169.254.169.254/latest/meta-data/placement/region 2>/dev/null)
  if [[ -z "$region" ]]; then
    log "Warning: Could not determine AWS region" "$YELLOW"
    region="ap-southeast-1"  # fallback
  fi
  
  # Get the instance private IP using AWS CLI
  local instance_ip=$(aws ec2 describe-instances \
    --filters "Name=tag:${tag_key},Values=${tag_value}" "Name=instance-state-name,Values=running" \
    --query "Reservations[0].Instances[0].PrivateIpAddress" \
    --output text --region "$region" 2>/dev/null)
  
  if [[ "$instance_ip" == "None" || -z "$instance_ip" ]]; then
    log "Could not find instance with ${tag_key}: ${tag_value}" "$RED"
    return 1
  fi
  
  log "Found instance IP: $instance_ip" "$GREEN"
  echo "$instance_ip"
}

# FIXED: Simple connectivity test function
test_connectivity() {
  local host="$1"
  local port="$2"
  local service_name="${3:-Service}"
  
  if nc -z -w 5 "$host" "$port" 2>/dev/null; then
    log "✅ $service_name ($host:$port) - Connected" "$GREEN"
    return 0
  else
    log "❌ $service_name ($host:$port) - Connection Failed" "$RED"
    return 1
  fi
}