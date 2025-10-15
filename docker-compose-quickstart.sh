#!/usr/bin/env bash
# Quick Start Script for Keystone Supercomputer Docker Compose
# This script helps set up and validate the Docker Compose environment

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "======================================================================"
echo "Keystone Supercomputer - Docker Compose Quick Start"
echo "======================================================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored messages
print_success() { echo -e "${GREEN}✓ $1${NC}"; }
print_error() { echo -e "${RED}✗ $1${NC}"; }
print_info() { echo -e "${YELLOW}→ $1${NC}"; }

# Check prerequisites
print_info "Checking prerequisites..."

if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi
print_success "Docker is installed"

if ! docker compose version &> /dev/null; then
    print_error "Docker Compose is not available. Please install Docker Compose V2."
    exit 1
fi
print_success "Docker Compose is available"

# Validate docker-compose.yml
print_info "Validating docker-compose.yml..."
if docker compose config --quiet; then
    print_success "docker-compose.yml is valid"
else
    print_error "docker-compose.yml validation failed"
    exit 1
fi

# Create data directories
print_info "Creating data directories..."
mkdir -p data/{fenicsx,lammps,openfoam}
print_success "Data directories created"

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    print_info "Creating .env file from .env.example..."
    cp .env.example .env
    print_success ".env file created (please review and customize)"
else
    print_success ".env file already exists"
fi

# Start Redis service
print_info "Starting Redis service..."
if docker compose up -d redis; then
    print_success "Redis service started"
    
    # Wait for Redis to be healthy
    print_info "Waiting for Redis to be healthy..."
    for i in {1..30}; do
        if docker compose exec redis redis-cli ping &> /dev/null; then
            print_success "Redis is healthy and responding"
            break
        fi
        sleep 1
    done
else
    print_error "Failed to start Redis service"
    exit 1
fi

# Show status
echo ""
print_info "Current service status:"
docker compose ps

echo ""
echo "======================================================================"
echo "Setup Complete!"
echo "======================================================================"
echo ""
echo "Next Steps:"
echo ""
echo "1. Build simulation images (with BuildKit for faster builds):"
echo "   export DOCKER_BUILDKIT=1"
echo "   docker compose build"
echo ""
echo "2. Run a test simulation:"
echo "   docker compose run --rm fenicsx poisson.py"
echo ""
echo "3. Run integration tests:"
echo "   cd src/sim-toolbox"
echo "   python3 integration_test.py --build"
echo ""
echo "4. View documentation:"
echo "   less DOCKER_COMPOSE.md"
echo "   less CONTAINER_OPTIMIZATION.md  # Learn about container optimizations"
echo ""
echo "5. Stop services:"
echo "   docker compose down"
echo ""
echo "======================================================================"
