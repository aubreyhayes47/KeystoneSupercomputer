# Keystone Simulation Helm Charts

This directory contains Helm charts for deploying the Keystone Supercomputer simulation stack to Kubernetes.

## Overview

The `keystone-simulation` chart deploys a complete scientific computing simulation stack including:

- **Redis**: Message broker for task queuing
- **Celery Workers**: Background job processing workers
- **FEniCSx**: Finite element simulation tool job template
- **LAMMPS**: Molecular dynamics simulation tool job template
- **OpenFOAM**: Computational fluid dynamics simulation tool job template

## Prerequisites

- Kubernetes cluster (v1.27+)
- Helm 3.x installed
- kubectl configured to access your cluster
- Docker images built locally (or available in a registry)

## Installation

### Quick Install

Install the chart with default values:

```bash
helm install keystone-sim ./keystone-simulation -n keystone --create-namespace
```

### Install with Custom Values

Create a custom values file:

```bash
# custom-values.yaml
celeryWorker:
  replicaCount: 5

redis:
  persistence:
    size: 5Gi

fenicsx:
  resources:
    limits:
      memory: "8Gi"
      cpu: "4000m"
```

Install with custom values:

```bash
helm install keystone-sim ./keystone-simulation \
  -n keystone \
  --create-namespace \
  -f custom-values.yaml
```

### Dry Run

Test the chart without installing:

```bash
helm install keystone-sim ./keystone-simulation \
  -n keystone \
  --create-namespace \
  --dry-run --debug
```

## Chart Configuration

### Redis Configuration

| Parameter | Description | Default |
|-----------|-------------|---------|
| `redis.enabled` | Enable Redis deployment | `true` |
| `redis.image.repository` | Redis image repository | `redis` |
| `redis.image.tag` | Redis image tag | `7-alpine` |
| `redis.service.port` | Redis service port | `6379` |
| `redis.persistence.enabled` | Enable persistent storage | `true` |
| `redis.persistence.size` | PVC storage size | `1Gi` |
| `redis.resources.limits.memory` | Memory limit | `512Mi` |
| `redis.resources.limits.cpu` | CPU limit | `500m` |

### Celery Worker Configuration

| Parameter | Description | Default |
|-----------|-------------|---------|
| `celeryWorker.enabled` | Enable Celery workers | `true` |
| `celeryWorker.replicaCount` | Number of worker replicas | `2` |
| `celeryWorker.image.repository` | Worker image repository | `keystone-celery-worker` |
| `celeryWorker.image.tag` | Worker image tag | `latest` |
| `celeryWorker.config.brokerUrl` | Redis broker URL | `redis://redis:6379/0` |
| `celeryWorker.resources.limits.memory` | Memory limit | `1Gi` |
| `celeryWorker.resources.limits.cpu` | CPU limit | `1000m` |

### Simulation Tools Configuration

Each simulation tool (FEniCSx, LAMMPS, OpenFOAM) has similar configuration:

| Parameter | Description | Default |
|-----------|-------------|---------|
| `<tool>.enabled` | Enable this simulation tool | `true` |
| `<tool>.image.repository` | Tool image repository | Tool-specific |
| `<tool>.image.tag` | Tool image tag | `latest` |
| `<tool>.jobTemplate.suspend` | Create suspended job template | `true` |
| `<tool>.resources.limits.memory` | Memory limit | `4Gi` |
| `<tool>.resources.limits.cpu` | CPU limit | `2000m` |

Replace `<tool>` with `fenicsx`, `lammps`, or `openfoam`.

## Usage

### Check Deployment Status

```bash
# List all releases
helm list -n keystone

# Get deployment status
kubectl get all -n keystone

# Check pods
kubectl get pods -n keystone
```

### Running Simulations

The simulation tools are deployed as suspended Job templates. To run a simulation:

```bash
# FEniCSx simulation
kubectl create job -n keystone fenicsx-run-1 --from=job/fenicsx-simulation

# LAMMPS simulation
kubectl create job -n keystone lammps-run-1 --from=job/lammps-simulation

# OpenFOAM simulation
kubectl create job -n keystone openfoam-run-1 --from=job/openfoam-simulation
```

### View Job Logs

```bash
kubectl logs -n keystone job/fenicsx-run-1 -f
```

### Scaling Workers

```bash
# Scale Celery workers
kubectl scale deployment -n keystone celery-worker --replicas=5

# Or upgrade the release
helm upgrade keystone-sim ./keystone-simulation \
  -n keystone \
  --set celeryWorker.replicaCount=5
```

### Port Forwarding

Access Redis directly for debugging:

```bash
kubectl port-forward -n keystone svc/redis 6379:6379
```

## Upgrading

Update the chart with new values:

```bash
helm upgrade keystone-sim ./keystone-simulation \
  -n keystone \
  -f custom-values.yaml
```

## Uninstalling

Remove the chart deployment:

```bash
helm uninstall keystone-sim -n keystone
```

Note: This will delete all resources including PVCs. Back up data before uninstalling.

## Chart Development

### Lint the Chart

```bash
helm lint ./keystone-simulation
```

### Template Rendering

Preview rendered templates:

```bash
helm template keystone-sim ./keystone-simulation -n keystone
```

### Package the Chart

Create a chart archive:

```bash
helm package ./keystone-simulation
```

### Validate Chart Values

```bash
helm install keystone-sim ./keystone-simulation \
  --dry-run --debug \
  -f values.yaml
```

## Directory Structure

```
k8s/helm/
├── README.md                    # This documentation
├── values-dev.yaml              # Development environment values
├── values-production.yaml       # Production environment values
├── values-minimal.yaml          # Minimal deployment values
├── values-hpc.yaml              # High-performance computing values
├── values-gpu.yaml              # GPU-enabled configuration
└── keystone-simulation/
    ├── Chart.yaml               # Chart metadata
    ├── values.yaml              # Default configuration values
    ├── templates/
    │   ├── _helpers.tpl         # Template helpers
    │   ├── NOTES.txt            # Post-install notes
    │   ├── namespace.yaml       # Namespace definition
    │   ├── redis.yaml           # Redis deployment
    │   ├── celery-worker.yaml   # Celery worker deployment
    │   ├── fenicsx.yaml         # FEniCSx job template
    │   ├── lammps.yaml          # LAMMPS job template
    │   └── openfoam.yaml        # OpenFOAM job template
    └── .helmignore              # Files to ignore when packaging
```

## GPU/NPU Acceleration

Keystone Simulation supports GPU and NPU hardware acceleration. See [GPU_ACCELERATION.md](../../GPU_ACCELERATION.md) for comprehensive setup instructions.

### Quick Start with GPU

```bash
# Install with NVIDIA GPU support
helm install keystone-sim ./keystone-simulation \
  -n keystone --create-namespace \
  -f values-gpu.yaml

# Custom GPU configuration
helm install keystone-sim ./keystone-simulation \
  -n keystone --create-namespace \
  -f values-gpu.yaml \
  --set fenicsx.resources.limits.nvidia\.com/gpu=2
```

### Prerequisites

Before deploying with GPU support:

1. **NVIDIA GPU**: Install [NVIDIA GPU Operator](https://docs.nvidia.com/datacenter/cloud-native/gpu-operator/latest/index.html)
2. **Intel GPU**: Install [Intel Device Plugin](https://github.com/intel/intel-device-plugins-for-kubernetes)
3. **AMD GPU**: Install [AMD Device Plugin](https://github.com/RadeonOpenCompute/k8s-device-plugin)

### Available GPU Configurations

The `values-gpu.yaml` file includes configurations for:
- NVIDIA GPU resource limits
- Intel GPU/NPU resource limits (commented examples)
- AMD GPU resource limits (commented examples)
- GPU node selection and tolerations
- Multi-GPU configurations

See [values-gpu.yaml](values-gpu.yaml) for full details.

## Troubleshooting

### Pods Not Starting

```bash
# Describe the pod
kubectl describe pod -n keystone <pod-name>

# Check logs
kubectl logs -n keystone <pod-name>
```

### Image Pull Errors

Ensure Docker images are built and available:

```bash
# For local k3d clusters, import images
docker compose build
k3d image import -c keystone-cluster \
  fenicsx-toolbox:latest \
  keystone/lammps:latest \
  openfoam-toolbox:latest \
  keystone-celery-worker:latest
```

### Storage Issues

Check PVC status:

```bash
kubectl get pvc -n keystone
kubectl describe pvc -n keystone redis-data
```

## Advanced Configuration

### Using External Redis

Disable the built-in Redis and connect to an external instance:

```yaml
# custom-values.yaml
redis:
  enabled: false

celeryWorker:
  config:
    brokerUrl: "redis://external-redis.example.com:6379/0"
    resultBackend: "redis://external-redis.example.com:6379/0"
```

### Custom Resource Limits

Adjust resources for specific workloads:

```yaml
# High-memory FEniCSx configuration
fenicsx:
  resources:
    requests:
      memory: "2Gi"
      cpu: "1000m"
    limits:
      memory: "16Gi"
      cpu: "8000m"
```

### Node Selection

Target specific nodes for deployments:

```yaml
nodeSelector:
  workload-type: simulation

# Or use node affinity
affinity:
  nodeAffinity:
    requiredDuringSchedulingIgnoredDuringExecution:
      nodeSelectorTerms:
      - matchExpressions:
        - key: node-role.kubernetes.io/worker
          operator: In
          values:
          - "true"
```

## Examples

### Development Setup

```bash
# Install with reduced resources for local development
helm install keystone-sim ./keystone-simulation \
  -n keystone \
  --create-namespace \
  -f values-dev.yaml
```

### Production Setup

```bash
# Install with production-ready configuration
helm install keystone-sim ./keystone-simulation \
  -n keystone \
  --create-namespace \
  -f values-production.yaml
```

### Minimal Setup

For testing or CI/CD environments:

```bash
# Install only Redis and Celery workers
helm install keystone-sim ./keystone-simulation \
  -n keystone \
  --create-namespace \
  -f values-minimal.yaml
```

### High-Performance Computing

For large-scale simulations:

```bash
# Install with HPC-optimized resources
helm install keystone-sim ./keystone-simulation \
  -n keystone \
  --create-namespace \
  -f values-hpc.yaml
```

### Example Values Files

The chart includes several pre-configured values files:

- **`values-dev.yaml`**: Development environment with minimal resources
- **`values-production.yaml`**: Production setup with high availability and resources
- **`values-minimal.yaml`**: Minimal deployment (Redis + Celery only)
- **`values-hpc.yaml`**: High-performance computing configuration with OpenMP/MPI support

### Parallel Computing Support

All simulation containers include OpenMP and MPI support for multi-core and distributed parallel computing.

**Configure OpenMP**:
```yaml
lammps:
  config:
    ompNumThreads: "4"    # Number of OpenMP threads
    ompProcBind: "spread" # Thread affinity
    ompPlaces: "threads"  # Placement strategy
```

**Run MPI jobs**:
```bash
# Create a job that runs with MPI
kubectl create job -n keystone lammps-mpi --from=job/lammps-simulation \
  -- mpirun -np 4 --allow-run-as-root lmp -in /data/input.lammps
```

See [PARALLEL_SIMULATIONS.md](../../PARALLEL_SIMULATIONS.md) for comprehensive parallel computing documentation.

## See Also

- [K3D Setup Guide](../../K3D.md)
- [Kubernetes Manifests](../manifests/)
- [Parallel Simulations Guide](../../PARALLEL_SIMULATIONS.md)
- [Keystone Documentation](../../README.md)
