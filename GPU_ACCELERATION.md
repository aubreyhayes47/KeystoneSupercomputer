# GPU/NPU Acceleration Guide

This guide explains how to enable GPU and NPU hardware acceleration for simulation containers in Keystone Supercomputer. Hardware acceleration can significantly improve performance for computationally intensive simulations.

## Table of Contents

- [Overview](#overview)
- [NVIDIA GPU Setup](#nvidia-gpu-setup)
- [Intel GPU/NPU Setup](#intel-gpunpu-setup)
- [AMD GPU Setup](#amd-gpu-setup)
- [Docker Configuration](#docker-configuration)
- [Kubernetes Configuration](#kubernetes-configuration)
- [Verification](#verification)
- [Troubleshooting](#troubleshooting)

---

## Overview

Keystone Supercomputer supports hardware acceleration via:

- **NVIDIA GPUs**: Using NVIDIA Container Toolkit and CUDA
- **Intel GPUs/NPUs**: Using Intel oneAPI and Level Zero drivers
- **AMD GPUs**: Using ROCm runtime

### Prerequisites

Before enabling GPU/NPU acceleration:

1. Verify GPU/NPU hardware is installed and recognized by the host OS
2. Install appropriate drivers on the host system
3. Install container runtime support (NVIDIA Container Toolkit, Intel GPU drivers, etc.)
4. Ensure Docker or Kubernetes has access to GPU devices

---

## NVIDIA GPU Setup

### Host System Requirements

1. **Install NVIDIA Drivers**:
   ```bash
   # Ubuntu/Debian
   sudo apt-get update
   sudo apt-get install -y nvidia-driver-535
   
   # Verify installation
   nvidia-smi
   ```

2. **Install NVIDIA Container Toolkit**:
   ```bash
   # Add NVIDIA package repositories
   distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
   curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
   curl -s -L https://nvidia.github.io/libnvidia-container/$distribution/libnvidia-container.list | \
     sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
     sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
   
   # Install the toolkit
   sudo apt-get update
   sudo apt-get install -y nvidia-container-toolkit
   
   # Configure Docker to use NVIDIA runtime
   sudo nvidia-ctk runtime configure --runtime=docker
   sudo systemctl restart docker
   ```

3. **Verify NVIDIA Runtime**:
   ```bash
   docker run --rm --gpus all nvidia/cuda:12.0.0-base-ubuntu22.04 nvidia-smi
   ```

### Docker Compose Configuration

Add GPU support to simulation services in `docker-compose.yml`:

```yaml
services:
  fenicsx:
    # ... existing configuration ...
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1  # or 'all' for all GPUs
              capabilities: [gpu, compute, utility]
```

Example complete service configuration:

```yaml
fenicsx-gpu:
  build:
    context: ./src/sim-toolbox/fenicsx
    dockerfile: Dockerfile
  image: fenicsx-toolbox:latest
  volumes:
    - ./data/fenicsx:/data
  environment:
    - PYTHONUNBUFFERED=1
    - CUDA_VISIBLE_DEVICES=0
  deploy:
    resources:
      reservations:
        devices:
          - driver: nvidia
            count: 1
            capabilities: [gpu, compute, utility]
```

### Kubernetes Configuration

1. **Install NVIDIA Device Plugin**:
   ```bash
   kubectl create -f https://raw.githubusercontent.com/NVIDIA/k8s-device-plugin/v0.14.0/nvidia-device-plugin.yml
   ```

2. **Verify Device Plugin**:
   ```bash
   kubectl get pods -n kube-system | grep nvidia
   kubectl describe nodes | grep nvidia.com/gpu
   ```

3. **Configure Pod to Use GPU**:
   ```yaml
   apiVersion: v1
   kind: Pod
   metadata:
     name: gpu-simulation
   spec:
     containers:
     - name: fenicsx
       image: fenicsx-toolbox:latest
       resources:
         limits:
           nvidia.com/gpu: 1  # Request 1 GPU
   ```

For Helm chart deployments, see [values-gpu.yaml](k8s/helm/values-gpu.yaml).

---

## Intel GPU/NPU Setup

### Host System Requirements

1. **Install Intel GPU Drivers**:
   ```bash
   # Ubuntu 22.04 LTS
   sudo apt-get update
   sudo apt-get install -y gpg-agent wget
   
   # Add Intel graphics repository
   wget -qO - https://repositories.intel.com/graphics/intel-graphics.key | \
     sudo gpg --dearmor --output /usr/share/keyrings/intel-graphics.gpg
   echo 'deb [arch=amd64,i386 signed-by=/usr/share/keyrings/intel-graphics.gpg] https://repositories.intel.com/graphics/ubuntu jammy arc' | \
     sudo tee /etc/apt/sources.list.d/intel.gpu.jammy.list
   
   # Install drivers
   sudo apt-get update
   sudo apt-get install -y \
     intel-opencl-icd \
     intel-level-zero-gpu \
     level-zero \
     intel-media-va-driver-non-free
   
   # Verify installation
   clinfo
   ls -la /dev/dri
   ```

2. **Install Intel oneAPI Base Toolkit** (for NPU and advanced features):
   ```bash
   # Download and install oneAPI
   wget https://registrationcenter-download.intel.com/akdlm/IRC_NAS/992857b9-624c-45de-9701-f6445d845359/l_BaseKit_p_2024.0.0.49564.sh
   
   sudo sh ./l_BaseKit_p_2024.0.0.49564.sh
   ```

### Docker Configuration

Add Intel GPU device access to containers:

```yaml
services:
  fenicsx-intel:
    # ... existing configuration ...
    devices:
      - /dev/dri:/dev/dri  # Intel GPU devices
    volumes:
      - /opt/intel/oneapi:/opt/intel/oneapi:ro  # Optional: for oneAPI
    environment:
      - ZE_AFFINITY_MASK=0  # Target specific GPU
```

Complete example:

```yaml
fenicsx-intel:
  build:
    context: ./src/sim-toolbox/fenicsx
    dockerfile: Dockerfile.intel
  image: fenicsx-toolbox:intel
  devices:
    - /dev/dri:/dev/dri
  group_add:
    - video
    - render
  volumes:
    - ./data/fenicsx:/data
  environment:
    - PYTHONUNBUFFERED=1
    - ONEAPI_ROOT=/opt/intel/oneapi
```

### Kubernetes Configuration

1. **Install Intel GPU Device Plugin**:
   ```bash
   kubectl apply -k 'https://github.com/intel/intel-device-plugins-for-kubernetes/deployments/nfd?ref=v0.29.0'
   kubectl apply -k 'https://github.com/intel/intel-device-plugins-for-kubernetes/deployments/nfd/overlays/node-feature-rules?ref=v0.29.0'
   kubectl apply -k 'https://github.com/intel/intel-device-plugins-for-kubernetes/deployments/gpu_plugin/overlays/nfd_labeled_nodes?ref=v0.29.0'
   ```

2. **Configure Pod to Use Intel GPU**:
   ```yaml
   apiVersion: v1
   kind: Pod
   metadata:
     name: intel-gpu-simulation
   spec:
     containers:
     - name: fenicsx
       image: fenicsx-toolbox:intel
       resources:
         limits:
           gpu.intel.com/i915: 1  # Request 1 Intel GPU
       securityContext:
         capabilities:
           add:
             - SYS_ADMIN
       volumeMounts:
       - name: dri
         mountPath: /dev/dri
     volumes:
     - name: dri
       hostPath:
         path: /dev/dri
   ```

### Intel NPU Configuration

For Intel NPU (Neural Processing Unit) support:

```yaml
resources:
  limits:
    npu.intel.com/npu: 1  # Request NPU access
```

---

## AMD GPU Setup

### Host System Requirements

1. **Install AMD ROCm Drivers**:
   ```bash
   # Ubuntu 22.04
   wget https://repo.radeon.com/amdgpu-install/22.40.5/ubuntu/jammy/amdgpu-install_5.4.50405-1_all.deb
   sudo apt-get update
   sudo apt-get install -y ./amdgpu-install_5.4.50405-1_all.deb
   
   # Install ROCm
   sudo amdgpu-install --usecase=rocm
   
   # Add user to render and video groups
   sudo usermod -a -G render,video $USER
   
   # Verify installation
   rocm-smi
   ```

### Docker Configuration

Add AMD GPU device access:

```yaml
services:
  fenicsx-amd:
    # ... existing configuration ...
    devices:
      - /dev/kfd:/dev/kfd
      - /dev/dri:/dev/dri
    group_add:
      - video
      - render
    environment:
      - HSA_OVERRIDE_GFX_VERSION=10.3.0  # Adjust for your GPU
```

Complete example:

```yaml
fenicsx-amd:
  build:
    context: ./src/sim-toolbox/fenicsx
    dockerfile: Dockerfile.rocm
  image: fenicsx-toolbox:rocm
  devices:
    - /dev/kfd:/dev/kfd
    - /dev/dri:/dev/dri
  group_add:
    - video
    - render
  volumes:
    - ./data/fenicsx:/data
  environment:
    - PYTHONUNBUFFERED=1
    - ROCM_PATH=/opt/rocm
```

### Kubernetes Configuration

1. **Install AMD Device Plugin**:
   ```bash
   kubectl create -f https://raw.githubusercontent.com/RadeonOpenCompute/k8s-device-plugin/master/k8s-ds-amdgpu-dp.yaml
   ```

2. **Configure Pod to Use AMD GPU**:
   ```yaml
   apiVersion: v1
   kind: Pod
   metadata:
     name: amd-gpu-simulation
   spec:
     containers:
     - name: fenicsx
       image: fenicsx-toolbox:rocm
       resources:
         limits:
           amd.com/gpu: 1  # Request 1 AMD GPU
       securityContext:
         capabilities:
           add:
             - SYS_PTRACE
   ```

---

## Docker Configuration

### Docker Compose GPU Examples

See [docker-compose.gpu.yml](docker-compose.gpu.yml) for complete examples.

#### Multi-GPU Configuration

```yaml
services:
  fenicsx-multigpu:
    # ... existing configuration ...
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 2  # Request 2 GPUs
              capabilities: [gpu, compute, utility]
    environment:
      - CUDA_VISIBLE_DEVICES=0,1  # Make both GPUs visible
```

#### GPU Selection

To target specific GPUs:

```yaml
environment:
  - CUDA_VISIBLE_DEVICES=0  # Use only GPU 0
  - CUDA_VISIBLE_DEVICES=1,2  # Use GPUs 1 and 2
```

---

## Kubernetes Configuration

### Helm Chart GPU Configuration

See [k8s/helm/values-gpu.yaml](k8s/helm/values-gpu.yaml) for a complete GPU-enabled configuration.

#### Node Selection for GPU Workloads

Target nodes with GPU hardware:

```yaml
nodeSelector:
  accelerator: nvidia-gpu
  # or
  accelerator: intel-gpu
  # or
  accelerator: amd-gpu
```

#### Resource Requests and Limits

```yaml
fenicsx:
  resources:
    limits:
      nvidia.com/gpu: 1
      # or
      gpu.intel.com/i915: 1
      # or
      amd.com/gpu: 1
    requests:
      memory: "8Gi"
      cpu: "4000m"
```

### Taints and Tolerations

For dedicated GPU nodes:

```yaml
tolerations:
- key: nvidia.com/gpu
  operator: Exists
  effect: NoSchedule
```

---

## Verification

### Test NVIDIA GPU Access

```bash
# Docker
docker run --rm --gpus all nvidia/cuda:12.0.0-base-ubuntu22.04 nvidia-smi

# Kubernetes
kubectl run gpu-test --rm -i --tty --restart=Never \
  --image=nvidia/cuda:12.0.0-base-ubuntu22.04 \
  --limits=nvidia.com/gpu=1 \
  -- nvidia-smi
```

### Test Intel GPU Access

```bash
# Docker
docker run --rm --device /dev/dri:/dev/dri \
  intel/oneapi-basekit:latest \
  bash -c "clinfo | head -n 20"

# Kubernetes
kubectl run intel-gpu-test --rm -i --tty --restart=Never \
  --image=intel/oneapi-basekit:latest \
  --limits=gpu.intel.com/i915=1 \
  -- clinfo
```

### Test AMD GPU Access

```bash
# Docker
docker run --rm \
  --device=/dev/kfd --device=/dev/dri \
  --group-add video --group-add render \
  rocm/pytorch:latest \
  rocm-smi

# Kubernetes
kubectl run amd-gpu-test --rm -i --tty --restart=Never \
  --image=rocm/pytorch:latest \
  --limits=amd.com/gpu=1 \
  -- rocm-smi
```

### Verify GPU Utilization

Monitor GPU usage during simulations:

```bash
# NVIDIA
watch -n 1 nvidia-smi

# Intel
intel_gpu_top

# AMD
watch -n 1 rocm-smi
```

---

## Troubleshooting

### Common Issues

#### NVIDIA: "could not select device driver"

**Solution**: Ensure NVIDIA Container Toolkit is installed and Docker is configured:
```bash
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
```

#### NVIDIA: "no CUDA-capable device is detected"

**Solution**: Check GPU visibility and driver installation:
```bash
nvidia-smi  # Should show GPU info
docker run --rm --gpus all nvidia/cuda:12.0.0-base-ubuntu22.04 nvidia-smi
```

#### Intel: "No GPU devices found"

**Solution**: Verify Intel GPU drivers and device permissions:
```bash
ls -la /dev/dri  # Should show render and card devices
clinfo  # Should list Intel GPU
sudo usermod -aG video,render $USER  # Add user to groups
```

#### Intel: "Permission denied" on /dev/dri

**Solution**: Ensure container has access to device groups:
```yaml
group_add:
  - video
  - render
```

#### AMD: "HSA Error: Device not found"

**Solution**: Check ROCm installation and device access:
```bash
rocm-smi  # Should show GPU info
ls -la /dev/kfd /dev/dri  # Verify device nodes exist
```

#### Kubernetes: Pods not scheduled on GPU nodes

**Solution**: Verify device plugin is running and nodes are labeled:
```bash
# NVIDIA
kubectl get pods -n kube-system | grep nvidia-device-plugin

# Intel
kubectl get pods -n kube-system | grep intel-gpu-plugin

# AMD
kubectl get pods -n kube-system | grep amdgpu-device-plugin

# Check node labels
kubectl describe nodes | grep -A 5 "Allocatable"
```

### Performance Tips

1. **Pin GPU Affinity**: Use `CUDA_VISIBLE_DEVICES` or `ZE_AFFINITY_MASK` to pin workloads to specific GPUs
2. **Resource Limits**: Set appropriate CPU and memory limits to avoid resource contention
3. **Persistent Storage**: Use fast storage (NVMe) for data I/O to avoid GPU idle time
4. **Batch Jobs**: Run multiple simulations in parallel when multiple GPUs are available

### Getting Help

For additional support:
- Check simulation tool documentation for GPU-specific configuration
- Review Docker/Kubernetes logs: `docker logs <container>` or `kubectl logs <pod>`
- Consult hardware-specific forums (NVIDIA, Intel, AMD)

---

## Next Steps

- Review [docker-compose.gpu.yml](docker-compose.gpu.yml) for Docker examples
- See [k8s/helm/values-gpu.yaml](k8s/helm/values-gpu.yaml) for Kubernetes examples
- Update simulation Dockerfiles to use GPU-enabled base images
- Benchmark your simulations with and without GPU acceleration
- Explore [ORCHESTRATION_GUIDE.md](ORCHESTRATION_GUIDE.md) for workflow optimization

---

## References

- [NVIDIA Container Toolkit Documentation](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/index.html)
- [NVIDIA GPU Operator for Kubernetes](https://docs.nvidia.com/datacenter/cloud-native/gpu-operator/latest/index.html)
- [Intel GPU Device Plugin](https://github.com/intel/intel-device-plugins-for-kubernetes)
- [Intel oneAPI Documentation](https://www.intel.com/content/www/us/en/developer/tools/oneapi/overview.html)
- [AMD ROCm Documentation](https://rocm.docs.amd.com/)
- [AMD GPU Device Plugin](https://github.com/RadeonOpenCompute/k8s-device-plugin)
