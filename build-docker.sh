#!/bin/bash

# Docker Build Script for Real Estate Platform
# ============================================
# This script builds all Docker images for the platform

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# Configuration
BUILD_TYPE=${1:-all}
ENVIRONMENT=${2:-development}
PUSH_IMAGES=${3:-false}

# Help function
show_help() {
    echo "Docker Build Script for Real Estate Platform"
    echo "============================================"
    echo ""
    echo "Usage: $0 [BUILD_TYPE] [ENVIRONMENT] [PUSH_IMAGES]"
    echo ""
    echo "Arguments:"
    echo "  BUILD_TYPE    - What to build (all|backend|frontend|services) [default: all]"
    echo "  ENVIRONMENT   - Target environment (development|production) [default: development]"
    echo "  PUSH_IMAGES   - Push images to registry (true|false) [default: false]"
    echo ""
    echo "Examples:"
    echo "  $0 all development              # Build all images for development"
    echo "  $0 backend production           # Build only backend for production"
    echo "  $0 all production true          # Build all and push to registry"
    echo ""
}

# Validate build type
validate_build_type() {
    case $BUILD_TYPE in
        all|backend|frontend|services)
            log_info "Building: $BUILD_TYPE"
            ;;
        *)
            log_error "Invalid build type: $BUILD_TYPE"
            log_error "Valid build types: all, backend, frontend, services"
            show_help
            exit 1
            ;;
    esac
}

# Validate environment
validate_environment() {
    case $ENVIRONMENT in
        development|production)
            log_info "Environment: $ENVIRONMENT"
            ;;
        *)
            log_error "Invalid environment: $ENVIRONMENT"
            log_error "Valid environments: development, production"
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
    
    # Check if Docker is running
    if ! docker info &> /dev/null; then
        log_error "Docker is not running. Please start Docker first."
        exit 1
    fi
    
    log_success "Prerequisites check completed"
}

# Clean up old images
cleanup_old_images() {
    log_info "Cleaning up old images..."
    
    # Remove dangling images
    docker image prune -f
    
    # Remove old versions of our images
    docker images | grep "real-estate-" | awk '{print $3}' | xargs -r docker rmi -f || true
    
    log_success "Cleanup completed"
}

# Build backend image
build_backend() {
    log_info "Building backend image..."
    
    local dockerfile="Dockerfile"
    local tag_suffix=""
    
    if [ "$ENVIRONMENT" = "development" ]; then
        dockerfile="Dockerfile.dev"
        tag_suffix="-dev"
    fi
    
    cd backend
    
    # Build the image
    docker build \
        -f "$dockerfile" \
        -t "real-estate-backend${tag_suffix}:latest" \
        -t "real-estate-backend${tag_suffix}:$(date +%Y%m%d-%H%M%S)" \
        .
    
    cd ..
    
    log_success "Backend image built successfully"
}

# Build frontend image
build_frontend() {
    log_info "Building frontend image..."
    
    local dockerfile="Dockerfile"
    local tag_suffix=""
    
    if [ "$ENVIRONMENT" = "development" ]; then
        dockerfile="Dockerfile.dev"
        tag_suffix="-dev"
    fi
    
    cd frontend
    
    # Build the image
    docker build \
        -f "$dockerfile" \
        -t "real-estate-frontend${tag_suffix}:latest" \
        -t "real-estate-frontend${tag_suffix}:$(date +%Y%m%d-%H%M%S)" \
        .
    
    cd ..
    
    log_success "Frontend image built successfully"
}

# Build service images
build_services() {
    log_info "Building service images..."
    
    # Build nginx image if needed
    if [ -f "docker/Dockerfile.nginx" ]; then
        log_info "Building nginx image..."
        docker build \
            -f docker/Dockerfile.nginx \
            -t "real-estate-nginx:latest" \
            docker/
        log_success "Nginx image built successfully"
    fi
    
    log_success "Service images built successfully"
}

# Push images to registry
push_images() {
    if [ "$PUSH_IMAGES" = "true" ]; then
        log_info "Pushing images to registry..."
        
        # This would push to a Docker registry like Docker Hub or AWS ECR
        # For now, we'll just log what would be pushed
        log_warning "Image pushing not implemented yet"
        log_warning "Images are built locally and ready for use"
    fi
}

# Show build summary
show_summary() {
    log_success "Build Summary"
    echo "=============="
    echo "Build Type: $BUILD_TYPE"
    echo "Environment: $ENVIRONMENT"
    echo "Timestamp: $(date)"
    echo ""
    echo "Built Images:"
    
    # List built images
    docker images | grep "real-estate-" | head -10
    
    echo ""
    echo "Next Steps:"
    echo "  Development: docker-compose -f docker-compose.dev.yml up -d"
    echo "  Production:  docker-compose up -d"
    echo "  View logs:   docker-compose logs -f"
    echo "  Stop:        docker-compose down"
}

# Main build function
main() {
    log_info "Starting Docker Build Process"
    log_info "Build Type: $BUILD_TYPE"
    log_info "Environment: $ENVIRONMENT"
    log_info "Push Images: $PUSH_IMAGES"
    echo ""
    
    # Show help if requested
    if [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
        show_help
        exit 0
    fi
    
    # Validate inputs
    validate_build_type
    validate_environment
    
    # Check prerequisites
    check_prerequisites
    
    # Clean up old images
    cleanup_old_images
    
    # Build based on type
    case $BUILD_TYPE in
        all)
            build_backend
            build_frontend
            build_services
            ;;
        backend)
            build_backend
            ;;
        frontend)
            build_frontend
            ;;
        services)
            build_services
            ;;
    esac
    
    # Push images if requested
    push_images
    
    # Show summary
    show_summary
    
    log_success "Docker build completed successfully! 🎉"
}

# Run main function with all arguments
main "$@"
