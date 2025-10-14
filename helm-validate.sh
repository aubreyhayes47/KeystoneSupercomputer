#!/usr/bin/env bash
# Helm Chart Validation Test
# This script validates the Helm charts without requiring a Kubernetes cluster

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_success() { echo -e "${GREEN}✓ $1${NC}"; }
print_error() { echo -e "${RED}✗ $1${NC}"; }
print_info() { echo -e "${YELLOW}→ $1${NC}"; }

echo "========================================================================"
echo "Helm Chart Validation Test"
echo "========================================================================"
echo ""

# Check prerequisites
print_info "Checking prerequisites..."

if ! command -v helm &> /dev/null; then
    print_error "helm not installed"
    exit 1
fi
print_success "helm is installed: $(helm version --short)"

# Check chart directory exists
print_info "Checking chart structure..."

if [ ! -d "k8s/helm/keystone-simulation" ]; then
    print_error "Chart directory not found"
    exit 1
fi
print_success "Chart directory exists"

# Lint the chart
print_info "Linting Helm chart..."
if helm lint k8s/helm/keystone-simulation; then
    print_success "Chart linting passed"
else
    print_error "Chart linting failed"
    exit 1
fi

# Test default values
print_info "Testing default values template rendering..."
if helm template keystone-sim k8s/helm/keystone-simulation -n keystone > /dev/null; then
    print_success "Default values template rendering passed"
else
    print_error "Default values template rendering failed"
    exit 1
fi

# Test dev values
print_info "Testing development values..."
if helm template keystone-sim k8s/helm/keystone-simulation -n keystone -f k8s/helm/values-dev.yaml > /dev/null; then
    print_success "Development values template rendering passed"
else
    print_error "Development values template rendering failed"
    exit 1
fi

# Test production values
print_info "Testing production values..."
if helm template keystone-sim k8s/helm/keystone-simulation -n keystone -f k8s/helm/values-production.yaml > /dev/null; then
    print_success "Production values template rendering passed"
else
    print_error "Production values template rendering failed"
    exit 1
fi

# Test minimal values
print_info "Testing minimal values..."
if helm template keystone-sim k8s/helm/keystone-simulation -n keystone -f k8s/helm/values-minimal.yaml > /dev/null; then
    print_success "Minimal values template rendering passed"
else
    print_error "Minimal values template rendering failed"
    exit 1
fi

# Test HPC values
print_info "Testing HPC values..."
if helm template keystone-sim k8s/helm/keystone-simulation -n keystone -f k8s/helm/values-hpc.yaml > /dev/null; then
    print_success "HPC values template rendering passed"
else
    print_error "HPC values template rendering failed"
    exit 1
fi

# Test chart packaging
print_info "Testing chart packaging..."
if helm package k8s/helm/keystone-simulation -d /tmp > /dev/null; then
    print_success "Chart packaging passed"
    rm -f /tmp/keystone-simulation-*.tgz
else
    print_error "Chart packaging failed"
    exit 1
fi

# Check documentation files exist
print_info "Checking documentation..."

DOCS=(
    "k8s/helm/README.md"
    "HELM_QUICKSTART.md"
    "K3D.md"
    "k8s/README.md"
)

for doc in "${DOCS[@]}"; do
    if [ ! -f "$doc" ]; then
        print_error "Missing documentation: $doc"
        exit 1
    fi
done
print_success "All documentation files exist"

# Verify Chart.yaml metadata
print_info "Verifying chart metadata..."
if grep -q "version: 1.0.0" k8s/helm/keystone-simulation/Chart.yaml; then
    print_success "Chart version is correct"
else
    print_error "Chart version is incorrect"
    exit 1
fi

# Summary
echo ""
echo "========================================================================"
print_success "Helm Chart Validation Complete!"
echo "========================================================================"
echo ""
echo "All tests passed! The Helm charts are ready for deployment."
echo ""
echo "Quick start:"
echo "  helm install keystone-sim k8s/helm/keystone-simulation -n keystone --create-namespace"
echo ""
echo "For more information, see:"
echo "  - HELM_QUICKSTART.md"
echo "  - k8s/helm/README.md"
echo ""
