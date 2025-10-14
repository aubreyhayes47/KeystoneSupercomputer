# Kubernetes Manifests for Keystone Supercomputer

This directory contains Kubernetes manifests and configuration for deploying Keystone Supercomputer services on a k3d cluster.

## Directory Structure

```
k8s/
├── configs/
│   └── k3d-cluster-config.yaml    # k3d cluster configuration
└── manifests/
    ├── 00-namespace.yaml           # Keystone namespace
    ├── 10-redis.yaml               # Redis deployment and service
    ├── 20-celery-worker.yaml       # Celery worker deployment
    ├── 30-fenicsx.yaml             # FEniCSx job template
    ├── 31-lammps.yaml              # LAMMPS job template
    └── 32-openfoam.yaml            # OpenFOAM job template
```

## Manifests Overview

### 00-namespace.yaml
Creates the `keystone` namespace where all services will be deployed.

### 10-redis.yaml
Deploys Redis as the message broker for Celery tasks:
- Single replica deployment
- PersistentVolumeClaim for data persistence
- ClusterIP service on port 6379
- Liveness and readiness probes

### 20-celery-worker.yaml
Deploys Celery workers for background job processing:
- 2 replicas by default (scalable)
- ConfigMap for environment variables
- Mounts data directory and celery_app.py
- Resource limits: 1GB RAM, 1 CPU per worker

### 30-fenicsx.yaml, 31-lammps.yaml, 32-openfoam.yaml
Job templates for simulation services:
- Created as suspended jobs (don't run automatically)
- Use `kubectl create job` to create instances
- HostPath volumes for simulation data
- Resource limits: 4GB RAM, 2 CPUs per job

## Usage

### Apply All Manifests

```bash
kubectl apply -f k8s/manifests/
```

### Apply Specific Manifest

```bash
kubectl apply -f k8s/manifests/10-redis.yaml
```

### View Resources

```bash
kubectl get all -n keystone
kubectl get pods -n keystone
kubectl get services -n keystone
```

### Run a Simulation Job

```bash
# Create a job from the template
kubectl create job -n keystone fenicsx-test \
  --from=job/fenicsx-simulation

# View job status
kubectl get jobs -n keystone

# View job logs
kubectl logs -n keystone job/fenicsx-test
```

## Configuration

The k3d cluster configuration is in `configs/k3d-cluster-config.yaml`:

- **Cluster name**: keystone-cluster
- **Servers**: 2 (control plane)
- **Agents**: 3 (worker nodes)
- **Port mappings**: 8080:80, 8443:443, 6379:6379
- **Volume mounts**: Host data directory to /data
- **Local registry**: Port 5000

## Customization

### Scaling Services

Edit the manifest and change `replicas`:

```yaml
spec:
  replicas: 5  # Scale to 5 replicas
```

Then apply:

```bash
kubectl apply -f k8s/manifests/20-celery-worker.yaml
```

Or use kubectl scale:

```bash
kubectl scale deployment -n keystone celery-worker --replicas=5
```

### Resource Limits

Edit the `resources` section in manifests:

```yaml
resources:
  requests:
    memory: "512Mi"
    cpu: "500m"
  limits:
    memory: "2Gi"
    cpu: "2000m"
```

### Adding New Services

1. Create a new manifest file (e.g., `40-myservice.yaml`)
2. Define the Deployment, Service, ConfigMap, etc.
3. Apply the manifest: `kubectl apply -f k8s/manifests/40-myservice.yaml`

## Troubleshooting

### Pods Not Starting

```bash
# Describe the pod for events
kubectl describe pod -n keystone <pod-name>

# View pod logs
kubectl logs -n keystone <pod-name>
```

### Service Not Accessible

```bash
# Check service endpoints
kubectl get endpoints -n keystone

# Test service connectivity
kubectl run -n keystone test --image=busybox -it --rm -- wget -O- redis:6379
```

### Storage Issues

```bash
# Check PVC status
kubectl get pvc -n keystone

# Describe PVC
kubectl describe pvc -n keystone redis-data
```

## See Also

- [K3D.md](../K3D.md) - Comprehensive k3d documentation
- [k3d-setup.sh](../k3d-setup.sh) - Cluster setup script
- [k3d-manage.sh](../k3d-manage.sh) - Cluster management script
- [Kubernetes Documentation](https://kubernetes.io/docs/)
