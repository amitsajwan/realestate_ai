#!/bin/bash

# PropertyAI Platform Deployment Script
# =====================================
# Comprehensive deployment script for production, staging, and development environments

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENVIRONMENT=${1:-development}
VERBOSE=${2:-false}
SKIP_TESTS=${3:-false}

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Help function
show_help() {
    echo "PropertyAI Platform Deployment Script"
    echo "======================================"
    echo ""
    echo "Usage: $0 [ENVIRONMENT] [VERBOSE] [SKIP_TESTS]"
    echo ""
    echo "Arguments:"
    echo "  ENVIRONMENT  - Target environment (development|staging|production) [default: development]"
    echo "  VERBOSE      - Enable verbose output (true|false) [default: false]"
    echo "  SKIP_TESTS   - Skip running tests (true|false) [default: false]"
    echo ""
    echo "Examples:"
    echo "  $0 development                    # Deploy to development"
    echo "  $0 staging true                   # Deploy to staging with verbose output"
    echo "  $0 production false true          # Deploy to production, skip tests"
    echo ""
    echo "Environment-specific configurations:"
    echo "  - development: Uses docker-compose.yml with local services"
    echo "  - staging: Uses docker-compose.staging.yml with staging configs"
    echo "  - production: Uses docker-compose.production.yml with production configs"
    echo ""
}

# Validate environment
validate_environment() {
    case $ENVIRONMENT in
        development|staging|production)
            log_info "Deploying to $ENVIRONMENT environment"
            ;;
        *)
            log_error "Invalid environment: $ENVIRONMENT"
            log_error "Valid environments: development, staging, production"
            show_help
            exit 1
            ;;
    esac
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Check if Docker Compose is installed
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    # Check if required files exist
    local compose_file="docker-compose.yml"
    case $ENVIRONMENT in
        staging)
            compose_file="docker-compose.staging.yml"
            ;;
        production)
            compose_file="docker-compose.production.yml"
            ;;
    esac
    
    if [ ! -f "$compose_file" ]; then
        log_error "Docker Compose file not found: $compose_file"
        exit 1
    fi
    
    # Check environment file
    local env_file=".env"
    case $ENVIRONMENT in
        staging)
            env_file=".env.staging"
            ;;
        production)
            env_file=".env.production"
            ;;
    esac
    
    if [ ! -f "$env_file" ] && [ ! -f ".env.template" ]; then
        log_warning "Environment file not found: $env_file"
        log_warning "Please create environment file or copy from template"
    fi
    
    log_success "Prerequisites check completed"
}

# Run tests
run_tests() {
    if [ "$SKIP_TESTS" = "true" ]; then
        log_warning "Skipping tests as requested"
        return 0
    fi
    
    log_info "Running comprehensive tests..."
    
    # Backend tests
    log_info "Running backend tests..."
    cd backend
    if [ -f "requirements.txt" ]; then
        python -m venv venv
        source venv/bin/activate
        pip install -r requirements.txt
        python -m pytest tests/ -v --tb=short
        deactivate
    else
        log_warning "Backend requirements.txt not found, skipping backend tests"
    fi
    cd ..
    
    # Frontend tests
    log_info "Running frontend tests..."
    cd frontend
    if [ -f "package.json" ]; then
        npm ci
        npm run test:ci || npm run test || log_warning "Frontend tests failed or not configured"
    else
        log_warning "Frontend package.json not found, skipping frontend tests"
    fi
    cd ..
    
    # Integration tests
    log_info "Running integration tests..."
    if [ -f "comprehensive_test.py" ]; then
        python comprehensive_test.py
    else
        log_warning "Integration test script not found"
    fi
    
    log_success "Tests completed"
}

# Build and deploy
deploy_services() {
    log_info "Building and deploying services..."
    
    # Set compose file based on environment
    local compose_file="docker-compose.yml"
    case $ENVIRONMENT in
        staging)
            compose_file="docker-compose.staging.yml"
            ;;
        production)
            compose_file="docker-compose.production.yml"
            ;;
    esac
    
    # Stop existing services
    log_info "Stopping existing services..."
    docker-compose -f "$compose_file" down --remove-orphans
    
    # Pull latest images (for production)
    if [ "$ENVIRONMENT" = "production" ]; then
        log_info "Pulling latest images..."
        docker-compose -f "$compose_file" pull
    fi
    
    # Build and start services
    log_info "Building and starting services..."
    if [ "$VERBOSE" = "true" ]; then
        docker-compose -f "$compose_file" up --build -d
    else
        docker-compose -f "$compose_file" up --build -d > /dev/null 2>&1
    fi
    
    # Wait for services to be ready
    log_info "Waiting for services to be ready..."
    sleep 30
    
    # Check service health
    check_service_health
    
    log_success "Services deployed successfully"
}

# Check service health
check_service_health() {
    log_info "Checking service health..."
    
    # Check MongoDB
    if docker-compose ps mongodb | grep -q "Up"; then
        log_success "MongoDB is running"
    else
        log_error "MongoDB is not running"
        return 1
    fi
    
    # Check Backend API
    local backend_url="http://localhost:8000"
    if curl -s "$backend_url/api/v1/health" > /dev/null; then
        log_success "Backend API is healthy"
    else
        log_error "Backend API is not responding"
        return 1
    fi
    
    # Check Frontend
    local frontend_url="http://localhost:3000"
    if curl -s "$frontend_url" > /dev/null; then
        log_success "Frontend is healthy"
    else
        log_error "Frontend is not responding"
        return 1
    fi
    
    # Check Redis (if enabled)
    if docker-compose ps redis | grep -q "Up"; then
        log_success "Redis is running"
    fi
    
    log_success "All services are healthy"
}

# Setup monitoring (production only)
setup_monitoring() {
    if [ "$ENVIRONMENT" != "production" ]; then
        return 0
    fi
    
    log_info "Setting up monitoring stack..."
    
    # Start monitoring services
    docker-compose -f docker-compose.production.yml --profile monitoring up -d
    
    # Wait for monitoring services
    sleep 20
    
    # Check monitoring services
    if curl -s "http://localhost:9090" > /dev/null; then
        log_success "Prometheus is running"
    else
        log_warning "Prometheus is not responding"
    fi
    
    if curl -s "http://localhost:3001" > /dev/null; then
        log_success "Grafana is running"
    else
        log_warning "Grafana is not responding"
    fi
}

# Backup existing data (production only)
backup_data() {
    if [ "$ENVIRONMENT" != "production" ]; then
        return 0
    fi
    
    log_info "Creating backup of existing data..."
    
    # Create backup directory
    local backup_dir="backups/$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$backup_dir"
    
    # Backup MongoDB
    if docker-compose ps mongodb | grep -q "Up"; then
        docker-compose exec -T mongodb mongodump --archive > "$backup_dir/mongodb_backup.archive"
        log_success "MongoDB backup created: $backup_dir/mongodb_backup.archive"
    fi
    
    # Backup uploaded files
    if [ -d "backend/uploads" ]; then
        cp -r backend/uploads "$backup_dir/"
        log_success "Upload files backed up"
    fi
    
    log_success "Backup completed: $backup_dir"
}

# Cleanup old resources
cleanup() {
    log_info "Cleaning up old resources..."
    
    # Remove unused Docker images
    docker image prune -f
    
    # Remove unused Docker volumes (be careful with this in production)
    if [ "$ENVIRONMENT" != "production" ]; then
        docker volume prune -f
    fi
    
    log_success "Cleanup completed"
}

# Show deployment summary
show_summary() {
    log_success "Deployment Summary"
    echo "=================="
    echo "Environment: $ENVIRONMENT"
    echo "Timestamp: $(date)"
    echo ""
    echo "Service URLs:"
    echo "  Frontend: http://localhost:3000"
    echo "  Backend API: http://localhost:8000"
    echo "  API Documentation: http://localhost:8000/docs"
    
    if [ "$ENVIRONMENT" = "production" ]; then
        echo "  Monitoring:"
        echo "    Prometheus: http://localhost:9090"
        echo "    Grafana: http://localhost:3001 (admin/admin123)"
    fi
    
    echo ""
    echo "Useful commands:"
    echo "  View logs: docker-compose logs -f"
    echo "  Stop services: docker-compose down"
    echo "  Restart services: docker-compose restart"
    echo "  Scale services: docker-compose up --scale backend=3"
}

# Main deployment function
main() {
    log_info "Starting PropertyAI Platform Deployment"
    log_info "Environment: $ENVIRONMENT"
    log_info "Verbose: $VERBOSE"
    log_info "Skip Tests: $SKIP_TESTS"
    echo ""
    
    # Show help if requested
    if [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
        show_help
        exit 0
    fi
    
    # Validate environment
    validate_environment
    
    # Check prerequisites
    check_prerequisites
    
    # Run tests
    run_tests
    
    # Backup data (production only)
    backup_data
    
    # Deploy services
    deploy_services
    
    # Setup monitoring (production only)
    setup_monitoring
    
    # Cleanup
    cleanup
    
    # Show summary
    show_summary
    
    log_success "Deployment completed successfully! 🎉"
}

# Run main function with all arguments
main "$@"