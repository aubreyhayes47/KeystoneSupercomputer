# k3d Quick Start Examples

This document provides quick examples for common k3d cluster operations.

## Initial Setup

```bash
# 1. Create the cluster (one-time setup)
./k3d-setup.sh

# Expected: Cluster created with 2 servers + 3 agents, all services deployed
```

## Basic Operations

### Check Cluster Status

```bash
# View cluster info
./k3d-manage.sh status

# List nodes
kubectl get nodes

# List all resources in keystone namespace
kubectl get all -n keystone
```

### View Service Logs

```bash
# View Redis logs
./k3d-manage.sh logs redis

# View Celery worker logs (follows)
./k3d-manage.sh logs celery-worker

# Or use kubectl directly
kubectl logs -n keystone -l app=celery-worker -f
```

### Access Services

```bash
# Port forward Redis to localhost
./k3d-manage.sh port-forward
# Now you can access Redis at localhost:6379

# In another terminal, test connection
redis-cli -h localhost -p 6379 ping
# Should return: PONG
```

## Running Simulations

### FEniCSx Simulation

```bash
# Run a FEniCSx simulation
./k3d-manage.sh run-simulation fenicsx poisson.py

# Monitor the job
kubectl get jobs -n keystone
kubectl logs -n keystone job/fenicsx-simulation-<timestamp> -f
```

### LAMMPS Simulation

```bash
# Run a LAMMPS simulation
./k3d-manage.sh run-simulation lammps example.lammps

# Check job status
kubectl get jobs -n keystone -l app=lammps
```

### OpenFOAM Simulation

```bash
# Run an OpenFOAM simulation
./k3d-manage.sh run-simulation openfoam cavity

# View logs
kubectl logs -n keystone job/openfoam-simulation-<timestamp>
```

## Scaling

### Scale Celery Workers

```bash
# Scale up to 5 workers
./k3d-manage.sh scale celery-worker 5

# Verify scaling
kubectl get pods -n keystone -l app=celery-worker

# Scale back down to 2
./k3d-manage.sh scale celery-worker 2
```

## Debugging

### Shell into a Pod

```bash
# List pods
./k3d-manage.sh pods

# Open shell in Redis pod
kubectl exec -n keystone -it <redis-pod-name> -- sh

# Inside the pod, test Redis
redis-cli ping
```

### Describe Resources

```bash
# Describe a pod
kubectl describe pod -n keystone <pod-name>

# Describe a service
kubectl describe service -n keystone redis

# View events
kubectl get events -n keystone --sort-by='.lastTimestamp'
```

## Managing Jobs

### Clean Up Completed Jobs

```bash
# List all jobs
kubectl get jobs -n keystone

# Delete a specific job
kubectl delete job -n keystone fenicsx-simulation-1234567890

# Delete all completed jobs
kubectl delete jobs -n keystone --field-selector status.successful=1
```

## Image Management

### Build and Import Custom Images

```bash
# Build images
docker compose build fenicsx lammps openfoam celery-worker

# Import to k3d cluster
./k3d-manage.sh import-images

# Or import specific images
k3d image import -c keystone-cluster fenicsx-toolbox:latest
```

## Advanced Usage

### Update Deployments

```bash
# Edit a deployment
kubectl edit deployment -n keystone celery-worker

# Or apply updated manifests
./k3d-manage.sh apply-manifests
```

### Restart Services

```bash
# Restart Celery workers (rolling restart)
./k3d-manage.sh restart celery-worker

# Restart Redis
./k3d-manage.sh restart redis
```

### Resource Monitoring

```bash
# View node resource usage
kubectl top nodes

# View pod resource usage
kubectl top pods -n keystone

# Detailed node info
kubectl describe node <node-name>
```

## Cluster Lifecycle

### Stop the Cluster

```bash
# Stop cluster (preserves data)
./k3d-manage.sh stop

# Or use k3d directly
k3d cluster stop keystone-cluster
```

### Restart the Cluster

```bash
# Start stopped cluster
./k3d-manage.sh start

# Or use k3d directly
k3d cluster start keystone-cluster
```

### Delete the Cluster

```bash
# Delete cluster (removes everything)
./k3d-manage.sh delete

# Or use k3d directly
k3d cluster delete keystone-cluster
```

## Integration with Celery Task Pipeline

```python
# Python script using Task Pipeline with k3d cluster
from task_pipeline import TaskPipeline

# Ensure Redis is accessible (port-forward if needed)
pipeline = TaskPipeline(broker_url="redis://localhost:6379/0")

# Submit simulation task
task_id = pipeline.submit_task(
    tool="fenicsx",
    script="poisson.py",
    params={"mesh_size": 64}
)

# Monitor task
result = pipeline.wait_for_task(task_id, timeout=300)
print(f"Task completed: {result['status']}")
```

## Troubleshooting

### Pods Not Starting

```bash
# Check pod status
kubectl get pods -n keystone

# Describe pod for events
kubectl describe pod -n keystone <pod-name>

# Check logs
kubectl logs -n keystone <pod-name>

# Check if images are available
docker images | grep -E "fenicsx|lammps|openfoam|celery"
```

### Port Already in Use

If you get port conflicts:

1. Edit `k8s/configs/k3d-cluster-config.yaml`
2. Change port mappings to available ports
3. Delete and recreate cluster

### Storage Issues

```bash
# Check PVC status
kubectl get pvc -n keystone

# Ensure data directory exists
ls -la ./data/
mkdir -p ./data/{fenicsx,lammps,openfoam}
```

## Best Practices

1. **Always validate before deploying**: Run `./k3d-validate.sh` first
2. **Monitor resources**: Use `kubectl top` to watch resource usage
3. **Clean up jobs**: Regularly delete completed jobs to save resources
4. **Use namespaces**: Keep all resources in `keystone` namespace
5. **Version your images**: Tag images with versions for reproducibility
6. **Back up data**: The `./data/` directory contains all simulation data

## See Also

- [K3D.md](K3D.md) - Comprehensive documentation
- [k8s/README.md](k8s/README.md) - Kubernetes manifests documentation
- [DOCKER_COMPOSE.md](DOCKER_COMPOSE.md) - Docker Compose alternative
