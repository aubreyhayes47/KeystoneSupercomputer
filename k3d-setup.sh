#!/usr/bin/env bash
# k3d Cluster Setup Script for Keystone Supercomputer
# This script creates and configures a local multi-node Kubernetes cluster using k3d

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Cluster configuration
CLUSTER_NAME="keystone-cluster"
CONFIG_FILE="./k8s/configs/k3d-cluster-config.yaml"

# Function to print colored messages
print_success() { echo -e "${GREEN}✓ $1${NC}"; }
print_error() { echo -e "${RED}✗ $1${NC}"; }
print_info() { echo -e "${YELLOW}→ $1${NC}"; }
print_header() { echo -e "${BLUE}━━━ $1 ━━━${NC}"; }

echo ""
echo "========================================================================"
echo "Keystone Supercomputer - k3d Cluster Setup"
echo "========================================================================"
echo ""

# Check prerequisites
print_header "Checking Prerequisites"

if ! command -v k3d &> /dev/null; then
    print_error "k3d is not installed. Installing now..."
    curl -s https://raw.githubusercontent.com/k3d-io/k3d/main/install.sh | bash
    print_success "k3d installed"
fi

if ! command -v kubectl &> /dev/null; then
    print_error "kubectl is not installed. Please install kubectl first."
    exit 1
fi
print_success "kubectl is installed"

if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi
print_success "Docker is installed"

if ! command -v helm &> /dev/null; then
    print_info "helm is not installed (optional, but recommended)"
else
    print_success "helm is installed"
fi

# Check if cluster already exists
print_header "Checking Existing Cluster"

if k3d cluster list | grep -q "$CLUSTER_NAME"; then
    print_info "Cluster '$CLUSTER_NAME' already exists"
    read -p "Do you want to delete and recreate it? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_info "Deleting existing cluster..."
        k3d cluster delete "$CLUSTER_NAME"
        print_success "Cluster deleted"
    else
        print_info "Using existing cluster"
        k3d kubeconfig merge "$CLUSTER_NAME" --kubeconfig-switch-context
        kubectl config use-context "k3d-$CLUSTER_NAME"
        print_success "Switched to cluster context"
        exit 0
    fi
fi

# Create data directories
print_header "Creating Data Directories"

mkdir -p data/{fenicsx,lammps,openfoam}
print_success "Data directories created"

# Create the cluster
print_header "Creating k3d Cluster"

print_info "Creating multi-node cluster with config: $CONFIG_FILE"
k3d cluster create --config "$CONFIG_FILE"
print_success "Cluster created successfully"

# Wait for cluster to be ready
print_header "Waiting for Cluster to be Ready"

print_info "Waiting for nodes to be ready..."
kubectl wait --for=condition=Ready nodes --all --timeout=300s
print_success "All nodes are ready"

# Display cluster info
print_header "Cluster Information"

echo ""
echo "Cluster: $CLUSTER_NAME"
echo ""
echo "Nodes:"
kubectl get nodes -o wide
echo ""

# Build Docker images for k3d
print_header "Preparing Docker Images for k3d"

print_info "Building simulation images..."
docker compose build fenicsx lammps openfoam 2>&1 | grep -E "(Building|built|tagged|ERROR)" || true
print_info "Building Celery worker image..."
docker compose build celery-worker 2>&1 | grep -E "(Building|built|tagged|ERROR)" || true
print_success "Images built"

print_info "Importing images to k3d cluster..."
k3d image import -c "$CLUSTER_NAME" \
    fenicsx-toolbox:latest \
    keystone/lammps:latest \
    openfoam-toolbox:latest \
    keystone-celery-worker:latest 2>&1 || print_info "Some images may not have been imported (will be built later)"
print_success "Images imported to cluster"

# Apply Kubernetes manifests
print_header "Deploying Keystone Services"

print_info "Applying Kubernetes manifests..."
kubectl apply -f k8s/manifests/00-namespace.yaml
print_success "Namespace created"

kubectl apply -f k8s/manifests/10-redis.yaml
print_success "Redis deployed"

print_info "Waiting for Redis to be ready..."
kubectl wait --for=condition=Ready pod -l app=redis -n keystone --timeout=120s
print_success "Redis is ready"

kubectl apply -f k8s/manifests/20-celery-worker.yaml
print_success "Celery worker deployed"

kubectl apply -f k8s/manifests/30-fenicsx.yaml
kubectl apply -f k8s/manifests/31-lammps.yaml
kubectl apply -f k8s/manifests/32-openfoam.yaml
print_success "Simulation service templates deployed"

# Display service status
print_header "Service Status"

echo ""
kubectl get all -n keystone
echo ""

# Setup port forwarding information
print_header "Access Information"

echo ""
echo "To access services from your host machine, use port forwarding:"
echo ""
echo "  Redis:"
echo "    kubectl port-forward -n keystone svc/redis 6379:6379"
echo ""
echo "  View logs:"
echo "    kubectl logs -n keystone -l app=redis"
echo "    kubectl logs -n keystone -l app=celery-worker -f"
echo ""
echo "  Shell into containers:"
echo "    kubectl exec -n keystone -it <pod-name> -- bash"
echo ""

# Create kubeconfig info
print_header "Kubeconfig Information"

echo ""
echo "Cluster context: k3d-$CLUSTER_NAME"
echo "Kubeconfig: $(kubectl config view --minify -o jsonpath='{.clusters[0].cluster.server}')"
echo ""
echo "Current context:"
kubectl config current-context
echo ""

print_success "Setup Complete!"

echo ""
echo "========================================================================"
echo "Next Steps:"
echo "========================================================================"
echo ""
echo "1. Check cluster status:"
echo "   kubectl get nodes"
echo "   kubectl get pods -n keystone"
echo ""
echo "2. View service logs:"
echo "   kubectl logs -n keystone -l app=redis"
echo "   kubectl logs -n keystone -l app=celery-worker -f"
echo ""
echo "3. Run a test simulation:"
echo "   ./k3d-manage.sh run-simulation fenicsx poisson.py"
echo ""
echo "4. Use kubectl to manage the cluster:"
echo "   kubectl get all -n keystone"
echo ""
echo "5. Delete the cluster when done:"
echo "   k3d cluster delete $CLUSTER_NAME"
echo ""
echo "See K3D.md for comprehensive documentation."
echo ""
