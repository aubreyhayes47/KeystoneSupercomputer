# k3d Local Kubernetes Cluster for Keystone Supercomputer

## Overview

This document describes the local multi-node Kubernetes cluster setup using k3d for the Keystone Supercomputer project. The cluster provides advanced orchestration and scaling capabilities for running scientific simulations in a cloud-native environment.

### What is k3d?

k3d is a lightweight wrapper to run k3s (Rancher Lab's minimal Kubernetes distribution) in Docker. It allows you to create multi-node Kubernetes clusters on your local machine quickly and easily, making it perfect for:

- Local development and testing
- CI/CD pipelines
- Learning Kubernetes
- Running containerized workloads with orchestration

### Architecture

The Keystone k3d cluster consists of:

- **2 Server Nodes (Control Plane)**: High availability for the Kubernetes control plane
- **3 Agent Nodes (Workers)**: Run your application workloads
- **Local Registry**: For storing custom container images
- **Load Balancer**: Automatic load balancing for exposed services

```
┌─────────────────────────────────────────────────────────────┐
│                    Keystone k3d Cluster                      │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │             Control Plane (2 servers)                 │  │
│  │  • API Server  • Scheduler  • Controller Manager     │  │
│  └──────────────────────────────────────────────────────┘  │
│                            │                                 │
│  ┌─────────────────────────┴────────────────────────────┐  │
│  │            Worker Nodes (3 agents)                    │  │
│  │                                                        │  │
│  │  Agent-1          Agent-2          Agent-3           │  │
│  │  ┌─────────┐      ┌─────────┐      ┌─────────┐      │  │
│  │  │ Redis   │      │ Celery  │      │ Celery  │      │  │
│  │  │         │      │ Worker  │      │ Worker  │      │  │
│  │  └─────────┘      └─────────┘      └─────────┘      │  │
│  │                                                        │  │
│  │  [Simulation Jobs run as Kubernetes Jobs/Pods]       │  │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  ┌────────────────┐         ┌──────────────────────────┐   │
│  │ Load Balancer  │◄────────┤  Local Registry (5000)   │   │
│  │ (Port mapping) │         └──────────────────────────┘   │
│  └────────────────┘                                          │
└─────────────────────────────────────────────────────────────┘
```

---

## Prerequisites

Before setting up the cluster, ensure you have:

- **Docker**: Container runtime (v20.10+)
- **kubectl**: Kubernetes command-line tool (v1.27+)
- **k3d**: k3d cluster manager (v5.8+, auto-installed by setup script)
- **helm** (optional): Kubernetes package manager for advanced deployments

### Installing Prerequisites

```bash
# Docker (if not installed)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
chmod +x kubectl
sudo mv kubectl /usr/local/bin/

# helm (optional)
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
```

---

## Quick Start

### 1. Create the Cluster

Run the setup script to create and configure the k3d cluster:

```bash
./k3d-setup.sh
```

This script will:
- Install k3d if not present
- Create a multi-node cluster with the configuration from `k8s/configs/k3d-cluster-config.yaml`
- Build and import Docker images
- Deploy Redis, Celery workers, and simulation service templates
- Configure networking and storage

**Expected output:**
```
======================================================================
Keystone Supercomputer - k3d Cluster Setup
======================================================================

━━━ Checking Prerequisites ━━━
✓ kubectl is installed
✓ Docker is installed
✓ helm is installed

━━━ Creating k3d Cluster ━━━
→ Creating multi-node cluster with config: ./k8s/configs/k3d-cluster-config.yaml
✓ Cluster created successfully

━━━ Waiting for Cluster to be Ready ━━━
→ Waiting for nodes to be ready...
✓ All nodes are ready

... (deployment output) ...

✓ Setup Complete!
```

### 2. Verify the Cluster

Check that all nodes are ready:

```bash
kubectl get nodes
```

Check deployed services:

```bash
kubectl get all -n keystone
```

### 3. Access Services

Set up port forwarding to access Redis from your host:

```bash
kubectl port-forward -n keystone svc/redis 6379:6379
```

---

## Cluster Configuration

The cluster configuration is defined in `k8s/configs/k3d-cluster-config.yaml`:

```yaml
apiVersion: k3d.io/v1alpha5
kind: Simple
metadata:
  name: keystone-cluster
servers: 2    # Control plane nodes
agents: 3     # Worker nodes
```

### Key Configuration Options

- **Server nodes**: 2 control plane nodes for high availability
- **Agent nodes**: 3 worker nodes for distributing workloads
- **Port mappings**: 
  - 8080:80 (HTTP ingress)
  - 8443:443 (HTTPS ingress)
  - 6379:6379 (Redis)
- **Volume mounts**: Host `./data` directory mounted to `/data` in all nodes
- **Local registry**: Runs on port 5000 for custom images

### Modifying Configuration

To change the cluster configuration:

1. Edit `k8s/configs/k3d-cluster-config.yaml`
2. Delete and recreate the cluster:
   ```bash
   k3d cluster delete keystone-cluster
   ./k3d-setup.sh
   ```

---

## Kubernetes Manifests

All Kubernetes manifests are located in `k8s/manifests/`:

### Service Deployments

1. **00-namespace.yaml**: Creates the `keystone` namespace
2. **10-redis.yaml**: Redis deployment with persistent storage
3. **20-celery-worker.yaml**: Celery worker deployment (2 replicas)
4. **30-fenicsx.yaml**: FEniCSx simulation job template
5. **31-lammps.yaml**: LAMMPS simulation job template
6. **32-openfoam.yaml**: OpenFOAM simulation job template

### Key Resources

#### Redis (Message Broker)
- **Type**: Deployment
- **Replicas**: 1
- **Storage**: PersistentVolumeClaim (1Gi)
- **Service**: ClusterIP on port 6379

#### Celery Worker (Job Queue)
- **Type**: Deployment
- **Replicas**: 2 (scalable)
- **Resource limits**: 1GB RAM, 1 CPU per worker
- **Connects to**: Redis for task queue

#### Simulation Services
- **Type**: Job templates (suspended by default)
- **Usage**: Create jobs on-demand for simulations
- **Storage**: HostPath volumes for data persistence

---

## Cluster Management

Use the `k3d-manage.sh` script for common cluster operations:

### Basic Commands

```bash
# Show cluster status
./k3d-manage.sh status

# List all pods
./k3d-manage.sh pods

# View service logs
./k3d-manage.sh logs redis
./k3d-manage.sh logs celery-worker

# Open shell in a pod
./k3d-manage.sh shell <pod-name>

# Stop the cluster
./k3d-manage.sh stop

# Start the cluster
./k3d-manage.sh start

# Delete the cluster
./k3d-manage.sh delete
```

### Running Simulations

```bash
# Run a FEniCSx simulation
./k3d-manage.sh run-simulation fenicsx poisson.py

# Run a LAMMPS simulation
./k3d-manage.sh run-simulation lammps example.lammps

# Run an OpenFOAM simulation
./k3d-manage.sh run-simulation openfoam cavity
```

### Scaling Services

```bash
# Scale Celery workers to 5 replicas
./k3d-manage.sh scale celery-worker 5

# Scale back to 2 replicas
./k3d-manage.sh scale celery-worker 2
```

### Restarting Services

```bash
# Restart Redis
./k3d-manage.sh restart redis

# Restart Celery workers
./k3d-manage.sh restart celery-worker
```

---

## Using kubectl Directly

### Namespace Operations

```bash
# Set default namespace
kubectl config set-context --current --namespace=keystone

# View all resources in namespace
kubectl get all -n keystone
```

### Pod Management

```bash
# List pods with details
kubectl get pods -n keystone -o wide

# Describe a pod
kubectl describe pod -n keystone <pod-name>

# View pod logs
kubectl logs -n keystone <pod-name> -f

# Execute command in pod
kubectl exec -n keystone -it <pod-name> -- bash
```

### Deployment Management

```bash
# View deployments
kubectl get deployments -n keystone

# Scale a deployment
kubectl scale deployment -n keystone celery-worker --replicas=3

# Update deployment
kubectl set image deployment/celery-worker -n keystone \
  celery-worker=keystone-celery-worker:latest

# Rollout status
kubectl rollout status deployment/celery-worker -n keystone

# Rollout history
kubectl rollout history deployment/celery-worker -n keystone

# Rollback deployment
kubectl rollout undo deployment/celery-worker -n keystone
```

### Service Management

```bash
# List services
kubectl get services -n keystone

# Describe a service
kubectl describe service -n keystone redis

# Port forward
kubectl port-forward -n keystone svc/redis 6379:6379
```

### Job Management

```bash
# List jobs
kubectl get jobs -n keystone

# View job logs
kubectl logs -n keystone job/<job-name>

# Delete completed jobs
kubectl delete job -n keystone <job-name>

# Delete all completed jobs
kubectl delete jobs -n keystone --field-selector status.successful=1
```

---

## Storage and Volumes

### Data Persistence

The cluster uses two types of storage:

1. **PersistentVolumeClaims (PVC)**: For Redis data
   ```bash
   kubectl get pvc -n keystone
   ```

2. **HostPath Volumes**: For simulation data
   - Mounted from host `./data` directory
   - Shared across all nodes via k3d configuration

### Accessing Data

Data is stored on your host machine:

```
./data/
├── fenicsx/     # FEniCSx simulation data
├── lammps/      # LAMMPS simulation data
└── openfoam/    # OpenFOAM simulation data
```

---

## Networking

### Service Discovery

Services can communicate using DNS:

```bash
# Redis service DNS name
redis.keystone.svc.cluster.local

# Full service DNS format
<service-name>.<namespace>.svc.cluster.local
```

### Port Forwarding

Access services from your host machine:

```bash
# Redis
kubectl port-forward -n keystone svc/redis 6379:6379

# Access via localhost:6379
redis-cli -h localhost -p 6379 ping
```

### Load Balancer

The cluster includes a load balancer for external access:

- Port 8080 → HTTP (port 80)
- Port 8443 → HTTPS (port 443)
- Port 6379 → Redis

---

## Resource Management

### View Resource Usage

```bash
# Node resource usage
kubectl top nodes

# Pod resource usage
kubectl top pods -n keystone

# Describe node to see resource allocation
kubectl describe node <node-name>
```

### Resource Limits

Services have defined resource limits in their manifests:

**Redis:**
- Requests: 128Mi memory, 100m CPU
- Limits: 512Mi memory, 500m CPU

**Celery Worker:**
- Requests: 256Mi memory, 200m CPU
- Limits: 1Gi memory, 1 CPU

**Simulation Jobs:**
- Requests: 512Mi memory, 500m CPU
- Limits: 4Gi memory, 2 CPUs

### Modifying Resources

Edit the deployment:

```bash
kubectl edit deployment -n keystone celery-worker
```

Or update via manifest:

```bash
kubectl apply -f k8s/manifests/20-celery-worker.yaml
```

---

## Monitoring and Debugging

### View Logs

```bash
# View logs for all pods with a label
kubectl logs -n keystone -l app=celery-worker -f

# View logs for a specific pod
kubectl logs -n keystone <pod-name> -f

# View logs for previous pod instance
kubectl logs -n keystone <pod-name> --previous

# View logs with timestamps
kubectl logs -n keystone <pod-name> --timestamps
```

### Events

```bash
# View events in namespace
kubectl get events -n keystone --sort-by='.lastTimestamp'

# Watch events in real-time
kubectl get events -n keystone --watch
```

### Debugging Pods

```bash
# Describe pod for detailed info
kubectl describe pod -n keystone <pod-name>

# Interactive shell
kubectl exec -n keystone -it <pod-name> -- /bin/bash

# Run debug container
kubectl debug -n keystone <pod-name> -it --image=busybox
```

### Cluster Diagnostics

```bash
# Check cluster info
kubectl cluster-info

# Check component status
kubectl get componentstatuses

# View node conditions
kubectl get nodes -o json | jq '.items[].status.conditions'
```

---

## Image Management

### Building and Importing Images

```bash
# Build images with Docker Compose
docker compose build fenicsx lammps openfoam celery-worker

# Import images to k3d cluster
k3d image import -c keystone-cluster \
  fenicsx-toolbox:latest \
  keystone/lammps:latest \
  openfoam-toolbox:latest \
  keystone-celery-worker:latest

# Or use the management script
./k3d-manage.sh import-images
```

### Using Local Registry

The cluster includes a local registry at `localhost:5000`:

```bash
# Tag image for local registry
docker tag fenicsx-toolbox:latest localhost:5000/fenicsx-toolbox:latest

# Push to local registry
docker push localhost:5000/fenicsx-toolbox:latest

# Use in Kubernetes manifest
image: localhost:5000/fenicsx-toolbox:latest
```

---

## Integration with Docker Compose

The k3d setup complements the existing Docker Compose setup:

### When to Use Each

**Docker Compose:**
- Local development
- Quick single-node testing
- Simple multi-container applications

**k3d Kubernetes:**
- Multi-node orchestration
- Production-like environment
- Advanced scaling and load balancing
- Learning Kubernetes
- CI/CD testing

### Migration Path

Services can run in both environments:

```bash
# Docker Compose
docker compose up redis celery-worker

# Kubernetes
./k3d-setup.sh
kubectl get pods -n keystone
```

---

## Advanced Usage

### Using Helm Charts

Install Helm charts in the cluster:

```bash
# Add Helm repository
helm repo add bitnami https://charts.bitnami.com/bitnami

# Install PostgreSQL
helm install postgres bitnami/postgresql \
  --namespace keystone \
  --set auth.postgresPassword=mysecretpassword

# List releases
helm list -n keystone
```

### Custom Resource Definitions (CRDs)

Install custom operators:

```bash
# Example: Install monitoring stack
kubectl apply -f https://raw.githubusercontent.com/prometheus-operator/prometheus-operator/main/bundle.yaml
```

### Network Policies

Add network security:

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-redis
  namespace: keystone
spec:
  podSelector:
    matchLabels:
      app: redis
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: celery-worker
    ports:
    - protocol: TCP
      port: 6379
```

### Ingress Controller

Expose services via ingress:

```bash
# Install NGINX ingress controller
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.1/deploy/static/provider/cloud/deploy.yaml
```

---

## Troubleshooting

### Cluster Won't Start

```bash
# Check Docker is running
docker ps

# Check k3d cluster list
k3d cluster list

# View k3d logs
docker logs k3d-keystone-cluster-server-0
```

### Pods Not Starting

```bash
# Check pod status
kubectl get pods -n keystone

# Describe pod for events
kubectl describe pod -n keystone <pod-name>

# Check pod logs
kubectl logs -n keystone <pod-name>

# Check node resources
kubectl top nodes
```

### Image Pull Errors

```bash
# Import images again
./k3d-manage.sh import-images

# Or import specific image
k3d image import -c keystone-cluster fenicsx-toolbox:latest

# Check if image exists
docker images | grep fenicsx
```

### Port Conflicts

If ports are already in use:

1. Edit `k8s/configs/k3d-cluster-config.yaml`
2. Change port mappings
3. Recreate cluster

### Storage Issues

```bash
# Check PVCs
kubectl get pvc -n keystone

# Describe PVC
kubectl describe pvc -n keystone redis-data

# Check if data directory exists
ls -la ./data/
```

### Networking Issues

```bash
# Test service connectivity
kubectl run -n keystone test-pod --image=busybox -it --rm -- sh
# Inside pod:
# wget -O- redis:6379

# Check service endpoints
kubectl get endpoints -n keystone redis
```

---

## Performance Tips

1. **Adjust resource limits**: Match your hardware capabilities
2. **Scale workers**: Add more Celery workers for parallel processing
3. **Use SSD storage**: Better I/O performance for simulations
4. **Allocate CPU cores**: Give Docker adequate CPU resources
5. **Monitor resources**: Use `kubectl top` regularly

---

## Cleanup

### Temporary Cleanup

```bash
# Stop cluster (preserves data)
./k3d-manage.sh stop

# Delete completed jobs
kubectl delete jobs -n keystone --field-selector status.successful=1
```

### Full Cleanup

```bash
# Delete cluster (removes everything)
./k3d-manage.sh delete

# Or directly
k3d cluster delete keystone-cluster
```

---

## Comparison: k3d vs Docker Compose

| Feature | Docker Compose | k3d Kubernetes |
|---------|---------------|----------------|
| Setup complexity | Simple | Moderate |
| Multi-node support | No | Yes (2+3 nodes) |
| Scaling | Manual | Automatic |
| Load balancing | No | Yes |
| Self-healing | No | Yes |
| Production-like | No | Yes |
| Learning curve | Easy | Steeper |
| Resource usage | Lower | Higher |

---

## Next Steps

1. **Explore Kubernetes Features**:
   - Try scaling services
   - Experiment with rolling updates
   - Set up monitoring with Prometheus

2. **Integrate with CI/CD**:
   - Use k3d in GitHub Actions
   - Automate testing in Kubernetes

3. **Deploy Additional Services**:
   - PostgreSQL database
   - Monitoring stack (Prometheus/Grafana)
   - Web dashboard

4. **Learn More**:
   - [Kubernetes Documentation](https://kubernetes.io/docs/)
   - [k3d Documentation](https://k3d.io/)
   - [k3s Documentation](https://docs.k3s.io/)

---

## References

- [k3d GitHub Repository](https://github.com/k3d-io/k3d)
- [k3s Documentation](https://docs.k3s.io/)
- [Kubernetes Documentation](https://kubernetes.io/docs/home/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [kubectl Cheat Sheet](https://kubernetes.io/docs/reference/kubectl/cheatsheet/)

---

## Support

For issues or questions:
1. Check this documentation
2. Review cluster logs: `kubectl logs -n keystone <pod-name>`
3. Check cluster events: `kubectl get events -n keystone`
4. Open an issue in the repository

---

**Maintainer**: Keystone Supercomputer Project  
**Last Updated**: 2025-10-14
