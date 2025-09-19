#!/bin/bash

# Health check script for Docker containers
# This script is used by Docker's HEALTHCHECK instruction

set -e

# Configuration
HEALTH_ENDPOINT="http://localhost:8000/health"
TIMEOUT=10
MAX_RETRIES=3

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to log messages
log() {
    echo -e "${GREEN}[HEALTH]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check HTTP endpoint
check_http_endpoint() {
    local url=$1
    local timeout=${2:-10}
    
    if command -v curl >/dev/null 2>&1; then
        curl -f -s --max-time "$timeout" "$url" >/dev/null
    elif command -v wget >/dev/null 2>&1; then
        wget -q --timeout="$timeout" --tries=1 -O /dev/null "$url"
    else
        log_error "Neither curl nor wget is available"
        return 1
    fi
}

# Function to check application health
check_application_health() {
    local retries=0
    
    while [ $retries -lt $MAX_RETRIES ]; do
        if check_http_endpoint "$HEALTH_ENDPOINT" "$TIMEOUT"; then
            log "Application health check passed"
            return 0
        else
            retries=$((retries + 1))
            if [ $retries -lt $MAX_RETRIES ]; then
                log_warn "Health check failed, retrying ($retries/$MAX_RETRIES)..."
                sleep 2
            fi
        fi
    done
    
    log_error "Application health check failed after $MAX_RETRIES attempts"
    return 1
}

# Function to check detailed health status
check_detailed_health() {
    if command -v curl >/dev/null 2>&1; then
        local response
        response=$(curl -f -s --max-time "$TIMEOUT" "$HEALTH_ENDPOINT" 2>/dev/null)
        
        if [ $? -eq 0 ]; then
            # Parse JSON response to check overall status
            local status
            status=$(echo "$response" | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
            
            case "$status" in
                "healthy")
                    log "System status: HEALTHY"
                    return 0
                    ;;
                "degraded")
                    log_warn "System status: DEGRADED"
                    return 1
                    ;;
                "unhealthy")
                    log_error "System status: UNHEALTHY"
                    return 2
                    ;;
                *)
                    log_warn "System status: UNKNOWN ($status)"
                    return 1
                    ;;
            esac
        else
            log_error "Failed to get health status"
            return 1
        fi
    else
        # Fallback to simple HTTP check
        check_application_health
    fi
}

# Function to check process health
check_process_health() {
    # Check if the main application process is running
    if pgrep -f "python.*main.py\|uvicorn.*main:app" >/dev/null; then
        log "Application process is running"
        return 0
    else
        log_error "Application process not found"
        return 1
    fi
}

# Function to check system resources
check_system_resources() {
    # Check available disk space (require at least 100MB free)
    local available_space
    available_space=$(df /tmp | tail -1 | awk '{print $4}')
    local required_space=102400  # 100MB in KB
    
    if [ "$available_space" -lt "$required_space" ]; then
        log_error "Insufficient disk space: ${available_space}KB available, ${required_space}KB required"
        return 1
    fi
    
    # Check memory usage (warn if over 90%)
    if command -v free >/dev/null 2>&1; then
        local memory_usage
        memory_usage=$(free | grep Mem | awk '{printf "%.0f", $3/$2 * 100.0}')
        
        if [ "$memory_usage" -gt 95 ]; then
            log_error "Critical memory usage: ${memory_usage}%"
            return 1
        elif [ "$memory_usage" -gt 90 ]; then
            log_warn "High memory usage: ${memory_usage}%"
        fi
    fi
    
    log "System resources check passed"
    return 0
}

# Main health check function
main() {
    local exit_code=0
    
    log "Starting health check..."
    
    # Check 1: Process health
    if ! check_process_health; then
        exit_code=1
    fi
    
    # Check 2: System resources
    if ! check_system_resources; then
        exit_code=1
    fi
    
    # Check 3: Application health endpoint
    if ! check_detailed_health; then
        exit_code=1
    fi
    
    # Final status
    if [ $exit_code -eq 0 ]; then
        log "All health checks passed"
    else
        log_error "One or more health checks failed"
    fi
    
    return $exit_code
}

# Handle script arguments
case "${1:-}" in
    --simple)
        # Simple check for basic Docker health check
        check_http_endpoint "$HEALTH_ENDPOINT" 5
        ;;
    --detailed)
        # Detailed check with full diagnostics
        main
        ;;
    --process)
        # Check only process health
        check_process_health
        ;;
    --resources)
        # Check only system resources
        check_system_resources
        ;;
    *)
        # Default: run main health check
        main
        ;;
esac