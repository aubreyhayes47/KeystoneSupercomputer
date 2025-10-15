# Helm Charts Quick Start Guide

This guide provides quick commands for deploying Keystone Supercomputer using Helm charts.

## Prerequisites

- Kubernetes cluster running (e.g., k3d)
- Helm 3.x installed
- kubectl configured

## Quick Deploy

```bash
# Install complete simulation stack
helm install keystone-sim k8s/helm/keystone-simulation \
  -n keystone \
  --create-namespace

# Check deployment
kubectl get all -n keystone
```

## Environment-Specific Deployments

### Development

```bash
helm install keystone-sim k8s/helm/keystone-simulation \
  -n keystone \
  --create-namespace \
  -f k8s/helm/values-dev.yaml
```

### Production

```bash
helm install keystone-sim k8s/helm/keystone-simulation \
  -n keystone \
  --create-namespace \
  -f k8s/helm/values-production.yaml
```

### Minimal (Testing)

```bash
helm install keystone-sim k8s/helm/keystone-simulation \
  -n keystone \
  --create-namespace \
  -f k8s/helm/values-minimal.yaml
```

### High-Performance Computing

```bash
helm install keystone-sim k8s/helm/keystone-simulation \
  -n keystone \
  --create-namespace \
  -f k8s/helm/values-hpc.yaml
```

## Common Operations

### Check Status

```bash
# Helm releases
helm list -n keystone

# Resources
kubectl get all -n keystone

# Specific pods
kubectl get pods -n keystone
```

### Upgrade Deployment

```bash
# Scale workers
helm upgrade keystone-sim k8s/helm/keystone-simulation \
  -n keystone \
  --set celeryWorker.replicaCount=5

# Or with values file
helm upgrade keystone-sim k8s/helm/keystone-simulation \
  -n keystone \
  -f custom-values.yaml
```

### Run Simulations

```bash
# FEniCSx
kubectl create job -n keystone fenicsx-run-1 \
  --from=job/fenicsx-simulation
kubectl logs -n keystone job/fenicsx-run-1 -f

# LAMMPS
kubectl create job -n keystone lammps-run-1 \
  --from=job/lammps-simulation
kubectl logs -n keystone job/lammps-run-1 -f

# OpenFOAM
kubectl create job -n keystone openfoam-run-1 \
  --from=job/openfoam-simulation
kubectl logs -n keystone job/openfoam-run-1 -f
```

### Uninstall

```bash
helm uninstall keystone-sim -n keystone
```

## Customization Examples

### Scale Celery Workers

```bash
helm upgrade keystone-sim k8s/helm/keystone-simulation \
  -n keystone \
  --set celeryWorker.replicaCount=10
```

### Adjust Resources

```bash
helm upgrade keystone-sim k8s/helm/keystone-simulation \
  -n keystone \
  --set fenicsx.resources.limits.memory=8Gi \
  --set fenicsx.resources.limits.cpu=4000m
```

### Enable/Disable Components

```bash
# Disable FEniCSx
helm upgrade keystone-sim k8s/helm/keystone-simulation \
  -n keystone \
  --set fenicsx.enabled=false
```

## Troubleshooting

### View Chart Values

```bash
# Current values
helm get values keystone-sim -n keystone

# All values (including defaults)
helm get values keystone-sim -n keystone --all
```

### Debug Rendering

```bash
# Preview rendered templates
helm template keystone-sim k8s/helm/keystone-simulation -n keystone

# With custom values
helm template keystone-sim k8s/helm/keystone-simulation \
  -n keystone \
  -f k8s/helm/values-dev.yaml
```

### Check Logs

```bash
# Pod logs
kubectl logs -n keystone <pod-name>

# All worker logs
kubectl logs -n keystone -l app=celery-worker -f
```

## Documentation

For comprehensive documentation, see:

- [k8s/helm/README.md](k8s/helm/README.md) - Complete Helm chart documentation
- [K3D.md](K3D.md) - k3d cluster setup and management
- [k8s/README.md](k8s/README.md) - Kubernetes deployment overview
