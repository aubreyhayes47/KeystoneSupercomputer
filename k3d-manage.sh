#!/usr/bin/env bash
# k3d Cluster Management Script for Keystone Supercomputer
# Provides convenient commands for managing the k3d cluster and running simulations

set -e

CLUSTER_NAME="keystone-cluster"
NAMESPACE="keystone"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_success() { echo -e "${GREEN}✓ $1${NC}"; }
print_error() { echo -e "${RED}✗ $1${NC}"; }
print_info() { echo -e "${YELLOW}→ $1${NC}"; }
print_header() { echo -e "${BLUE}━━━ $1 ━━━${NC}"; }

# Function to display usage
usage() {
    cat << EOF
Keystone Supercomputer - k3d Cluster Management

Usage: $0 <command> [options]

Commands:
  start                 Start the k3d cluster
  stop                  Stop the k3d cluster
  delete                Delete the k3d cluster
  status                Show cluster status
  nodes                 List cluster nodes
  pods                  List all pods in keystone namespace
  logs <service>        Show logs for a service (redis, celery-worker)
  shell <pod-name>      Open a shell in a pod
  port-forward          Setup port forwarding for Redis
  run-simulation <tool> <script>  Run a simulation job
  scale <service> <replicas>      Scale a deployment
  restart <service>     Restart a service
  describe <resource>   Describe a Kubernetes resource
  import-images         Import Docker images to cluster
  apply-manifests       Apply/update Kubernetes manifests
  help                  Show this help message

Examples:
  $0 status
  $0 pods
  $0 logs redis
  $0 logs celery-worker
  $0 shell keystone-redis-xxx
  $0 run-simulation fenicsx poisson.py
  $0 scale celery-worker 3
  $0 restart redis

EOF
    exit 1
}

# Check if cluster exists
check_cluster() {
    if ! k3d cluster list | grep -q "$CLUSTER_NAME"; then
        print_error "Cluster '$CLUSTER_NAME' does not exist"
        echo "Run './k3d-setup.sh' to create the cluster first"
        exit 1
    fi
}

# Start cluster
start_cluster() {
    print_header "Starting Cluster"
    k3d cluster start "$CLUSTER_NAME"
    print_success "Cluster started"
}

# Stop cluster
stop_cluster() {
    check_cluster
    print_header "Stopping Cluster"
    k3d cluster stop "$CLUSTER_NAME"
    print_success "Cluster stopped"
}

# Delete cluster
delete_cluster() {
    check_cluster
    print_header "Deleting Cluster"
    read -p "Are you sure you want to delete the cluster? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        k3d cluster delete "$CLUSTER_NAME"
        print_success "Cluster deleted"
    else
        print_info "Cancelled"
    fi
}

# Show cluster status
show_status() {
    check_cluster
    print_header "Cluster Status"
    echo ""
    echo "Cluster: $CLUSTER_NAME"
    echo ""
    k3d cluster list | grep "$CLUSTER_NAME"
    echo ""
    print_header "Nodes"
    kubectl get nodes -o wide
    echo ""
    print_header "Services in $NAMESPACE namespace"
    kubectl get all -n "$NAMESPACE"
}

# List nodes
list_nodes() {
    check_cluster
    kubectl get nodes -o wide
}

# List pods
list_pods() {
    check_cluster
    kubectl get pods -n "$NAMESPACE" -o wide
}

# Show logs
show_logs() {
    check_cluster
    if [ -z "$1" ]; then
        print_error "Service name required"
        echo "Usage: $0 logs <service>"
        echo "Available services: redis, celery-worker"
        exit 1
    fi
    
    print_header "Logs for $1"
    kubectl logs -n "$NAMESPACE" -l app="$1" --tail=100 -f
}

# Open shell
open_shell() {
    check_cluster
    if [ -z "$1" ]; then
        print_error "Pod name required"
        echo "Usage: $0 shell <pod-name>"
        echo "Use '$0 pods' to list available pods"
        exit 1
    fi
    
    print_info "Opening shell in $1..."
    kubectl exec -n "$NAMESPACE" -it "$1" -- /bin/sh
}

# Port forward
port_forward() {
    check_cluster
    print_header "Setting up Port Forwarding"
    print_info "Forwarding Redis: localhost:6379 -> redis:6379"
    echo "Press Ctrl+C to stop port forwarding"
    kubectl port-forward -n "$NAMESPACE" svc/redis 6379:6379
}

# Run simulation
run_simulation() {
    check_cluster
    if [ -z "$1" ] || [ -z "$2" ]; then
        print_error "Tool and script required"
        echo "Usage: $0 run-simulation <tool> <script>"
        echo "Available tools: fenicsx, lammps, openfoam"
        exit 1
    fi
    
    TOOL="$1"
    SCRIPT="$2"
    JOB_NAME="${TOOL}-simulation-$(date +%s)"
    
    print_header "Running $TOOL Simulation"
    print_info "Tool: $TOOL"
    print_info "Script: $SCRIPT"
    print_info "Job name: $JOB_NAME"
    
    # Create a job from the template
    kubectl create job -n "$NAMESPACE" "$JOB_NAME" \
        --from=job/"${TOOL}-simulation" \
        --dry-run=client -o yaml | \
        sed "s/suspend: true/suspend: false/" | \
        kubectl apply -f -
    
    print_success "Job created: $JOB_NAME"
    print_info "Monitor with: kubectl logs -n $NAMESPACE job/$JOB_NAME -f"
    
    # Wait for job to complete
    print_info "Waiting for job to complete..."
    kubectl wait --for=condition=complete --timeout=300s -n "$NAMESPACE" job/"$JOB_NAME" || true
    
    # Show logs
    print_header "Job Logs"
    kubectl logs -n "$NAMESPACE" job/"$JOB_NAME"
    
    # Show job status
    kubectl get job -n "$NAMESPACE" "$JOB_NAME"
}

# Scale deployment
scale_deployment() {
    check_cluster
    if [ -z "$1" ] || [ -z "$2" ]; then
        print_error "Service and replica count required"
        echo "Usage: $0 scale <service> <replicas>"
        exit 1
    fi
    
    print_header "Scaling $1"
    kubectl scale deployment -n "$NAMESPACE" "$1" --replicas="$2"
    print_success "Scaled $1 to $2 replicas"
    kubectl get deployment -n "$NAMESPACE" "$1"
}

# Restart service
restart_service() {
    check_cluster
    if [ -z "$1" ]; then
        print_error "Service name required"
        echo "Usage: $0 restart <service>"
        exit 1
    fi
    
    print_header "Restarting $1"
    kubectl rollout restart deployment -n "$NAMESPACE" "$1"
    print_success "Restarted $1"
    kubectl rollout status deployment -n "$NAMESPACE" "$1"
}

# Describe resource
describe_resource() {
    check_cluster
    if [ -z "$1" ]; then
        print_error "Resource required"
        echo "Usage: $0 describe <resource>"
        echo "Example: $0 describe pod/redis-xxx"
        exit 1
    fi
    
    kubectl describe -n "$NAMESPACE" "$1"
}

# Import images
import_images() {
    check_cluster
    print_header "Importing Docker Images"
    
    print_info "Building images..."
    docker compose build fenicsx lammps openfoam celery-worker
    
    print_info "Importing to cluster..."
    k3d image import -c "$CLUSTER_NAME" \
        fenicsx-toolbox:latest \
        keystone/lammps:latest \
        openfoam-toolbox:latest \
        keystone-celery-worker:latest
    
    print_success "Images imported"
}

# Apply manifests
apply_manifests() {
    check_cluster
    print_header "Applying Kubernetes Manifests"
    
    kubectl apply -f k8s/manifests/
    print_success "Manifests applied"
    
    print_info "Current state:"
    kubectl get all -n "$NAMESPACE"
}

# Main command router
case "${1:-help}" in
    start)
        start_cluster
        ;;
    stop)
        stop_cluster
        ;;
    delete)
        delete_cluster
        ;;
    status)
        show_status
        ;;
    nodes)
        list_nodes
        ;;
    pods)
        list_pods
        ;;
    logs)
        show_logs "$2"
        ;;
    shell)
        open_shell "$2"
        ;;
    port-forward)
        port_forward
        ;;
    run-simulation)
        run_simulation "$2" "$3"
        ;;
    scale)
        scale_deployment "$2" "$3"
        ;;
    restart)
        restart_service "$2"
        ;;
    describe)
        describe_resource "$2"
        ;;
    import-images)
        import_images
        ;;
    apply-manifests)
        apply_manifests
        ;;
    help|*)
        usage
        ;;
esac
