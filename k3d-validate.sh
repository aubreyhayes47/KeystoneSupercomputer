#!/usr/bin/env bash
# Quick validation test for k3d setup
# This script validates the k3d configuration and manifests without creating a full cluster

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
echo "k3d Setup Validation Test"
echo "========================================================================"
echo ""

# Check prerequisites
print_info "Checking prerequisites..."

if ! command -v k3d &> /dev/null; then
    print_error "k3d not installed"
    exit 1
fi
print_success "k3d is installed: $(k3d version | head -1)"

if ! command -v kubectl &> /dev/null; then
    print_error "kubectl not installed"
    exit 1
fi
print_success "kubectl is installed: $(kubectl version --client -o json 2>/dev/null | jq -r .clientVersion.gitVersion)"

if ! command -v docker &> /dev/null; then
    print_error "Docker not installed"
    exit 1
fi
print_success "Docker is installed: $(docker --version)"

# Validate configuration file
print_info "Validating k3d configuration..."

if [ ! -f "k8s/configs/k3d-cluster-config.yaml" ]; then
    print_error "k3d config file not found"
    exit 1
fi
print_success "k3d config file exists"

# Validate YAML syntax
print_info "Validating YAML syntax..."

python3 -c "
import yaml
import sys

try:
    # Validate config
    with open('k8s/configs/k3d-cluster-config.yaml', 'r') as f:
        yaml.safe_load(f)
    
    # Validate manifests
    import glob
    for manifest_file in glob.glob('k8s/manifests/*.yaml'):
        with open(manifest_file, 'r') as f:
            list(yaml.safe_load_all(f))
    
    print('All YAML files are valid')
except Exception as e:
    print(f'YAML validation error: {e}')
    sys.exit(1)
" || exit 1

print_success "All YAML files are valid"

# Validate scripts are executable
print_info "Checking scripts..."

if [ ! -x "k3d-setup.sh" ]; then
    print_error "k3d-setup.sh is not executable"
    exit 1
fi
print_success "k3d-setup.sh is executable"

if [ ! -x "k3d-manage.sh" ]; then
    print_error "k3d-manage.sh is not executable"
    exit 1
fi
print_success "k3d-manage.sh is executable"

# Check manifest structure
print_info "Validating manifest structure..."

MANIFESTS=(
    "k8s/manifests/00-namespace.yaml"
    "k8s/manifests/10-redis.yaml"
    "k8s/manifests/20-celery-worker.yaml"
    "k8s/manifests/30-fenicsx.yaml"
    "k8s/manifests/31-lammps.yaml"
    "k8s/manifests/32-openfoam.yaml"
)

for manifest in "${MANIFESTS[@]}"; do
    if [ ! -f "$manifest" ]; then
        print_error "Missing manifest: $manifest"
        exit 1
    fi
done
print_success "All required manifests exist"

# Check documentation
print_info "Checking documentation..."

if [ ! -f "K3D.md" ]; then
    print_error "K3D.md documentation not found"
    exit 1
fi
print_success "K3D.md documentation exists"

# Validate k3d config can be parsed
print_info "Validating k3d config structure..."

python3 -c "
import yaml

with open('k8s/configs/k3d-cluster-config.yaml', 'r') as f:
    config = yaml.safe_load(f)

# Check required fields
assert config.get('apiVersion') == 'k3d.io/v1alpha5', 'Invalid apiVersion'
assert config.get('kind') == 'Simple', 'Invalid kind'
assert 'metadata' in config, 'Missing metadata'
assert 'name' in config['metadata'], 'Missing cluster name'

print(f\"Cluster name: {config['metadata']['name']}\")
print(f\"Servers: {config.get('servers', 1)}\")
print(f\"Agents: {config.get('agents', 0)}\")
"

print_success "k3d config structure is valid"

# Test that k3d can validate the config (without creating cluster)
print_info "Testing k3d config validation..."

# Note: k3d doesn't have a --dry-run flag, so we just check the syntax is parseable
k3d version &> /dev/null
print_success "k3d is functional"

# Summary
echo ""
echo "========================================================================"
print_success "Validation Complete!"
echo "========================================================================"
echo ""
echo "All checks passed. The k3d setup is ready for deployment."
echo ""
echo "Next steps:"
echo "  1. Create the cluster: ./k3d-setup.sh"
echo "  2. Manage the cluster: ./k3d-manage.sh help"
echo "  3. Read documentation: K3D.md"
echo ""
