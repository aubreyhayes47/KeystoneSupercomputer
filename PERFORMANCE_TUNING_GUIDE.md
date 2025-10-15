# Performance Tuning Guide for Keystone Supercomputer

## Overview

This comprehensive guide provides end users with best practices and optimization techniques to maximize simulation performance in Keystone Supercomputer. Whether you're running on a laptop, workstation, or cluster, these recommendations will help you get the most out of your hardware and software configuration.

**Who is this guide for?**
- Researchers optimizing simulation workflows
- Engineers benchmarking hardware configurations
- DevOps teams deploying Keystone Supercomputer
- Anyone looking to improve simulation throughput and efficiency

---

## Table of Contents

- [Quick Wins - Start Here](#quick-wins---start-here)
- [Hardware Optimization](#hardware-optimization)
- [Software Configuration](#software-configuration)
- [Simulation-Specific Tuning](#simulation-specific-tuning)
- [Workflow Optimization](#workflow-optimization)
- [Container Optimization](#container-optimization)
- [Monitoring and Profiling](#monitoring-and-profiling)
- [Troubleshooting Performance Issues](#troubleshooting-performance-issues)
- [Performance Checklist](#performance-checklist)

---

## Quick Wins - Start Here

These are the highest-impact optimizations you can make with minimal effort:

### 1. Enable GPU Acceleration (if available)
**Impact:** 2-50x speedup for compatible simulations

```bash
# Test GPU access
docker run --rm --gpus all nvidia/cuda:12.0.0-base-ubuntu22.04 nvidia-smi

# Use GPU-enabled compose file
docker compose -f docker-compose.gpu.yml up -d
```

**See:** [GPU_ACCELERATION.md](GPU_ACCELERATION.md) for complete setup

### 2. Use Parallel Workflow Submission
**Impact:** Near-linear speedup for independent tasks

```python
from task_pipeline import TaskPipeline

pipeline = TaskPipeline()

# Submit tasks in parallel instead of sequential
tasks = [
    {"tool": "fenicsx", "script": "poisson.py", "params": {"mesh_size": 32}},
    {"tool": "fenicsx", "script": "poisson.py", "params": {"mesh_size": 64}},
    {"tool": "fenicsx", "script": "poisson.py", "params": {"mesh_size": 128}},
]

# Parallel submission (non-blocking)
task_ids = pipeline.submit_workflow(tasks, sequential=False)
results = pipeline.wait_for_workflow(task_ids)
```

**See:** [PARALLEL_ORCHESTRATION.md](PARALLEL_ORCHESTRATION.md) for details

### 3. Optimize Container Images
**Impact:** 30-50% smaller images, faster startup

```bash
# Rebuild with optimized Dockerfiles
export DOCKER_BUILDKIT=1
docker compose build --parallel
```

**See:** [CONTAINER_OPTIMIZATION.md](CONTAINER_OPTIMIZATION.md) for techniques

### 4. Scale Celery Workers
**Impact:** Better task throughput and resource utilization

```bash
# Docker Compose
docker compose up -d --scale celery-worker=4

# Kubernetes/Helm
helm upgrade keystone-sim k8s/helm/keystone-simulation \
  --set celeryWorker.replicaCount=8
```

### 5. Enable BuildKit Caching
**Impact:** 50-90% faster rebuilds

```bash
# Add to shell profile
export DOCKER_BUILDKIT=1

# Or in docker-compose.yml
DOCKER_BUILDKIT=1 docker compose build
```

---

## Hardware Optimization

### CPU Configuration

#### Core Allocation

**Single Simulation:**
- Allocate all available cores for maximum performance
- Set `OMP_NUM_THREADS` to match physical cores (not hyperthreads)

```bash
# Check available cores
nproc --all

# Set OpenMP threads
export OMP_NUM_THREADS=8  # Use physical core count

# Run simulation
docker compose run --rm fenicsx python3 poisson.py
```

**Multiple Concurrent Simulations:**
- Divide cores among simulations
- Leave 1-2 cores for system overhead

```bash
# For 8 cores running 4 simulations
export OMP_NUM_THREADS=2

# Scale workers to match
docker compose up -d --scale celery-worker=4
```

#### CPU Pinning and Affinity

Prevent thread migration and improve cache locality:

```bash
# Set CPU affinity for Docker containers
docker run --cpuset-cpus="0-3" --rm fenicsx python3 poisson.py

# In docker-compose.yml
services:
  celery-worker:
    cpuset: "0-7"
```

**OpenMP Thread Affinity:**

```bash
# Bind threads to cores
export OMP_PROC_BIND=spread
export OMP_PLACES=threads

# Or for compact binding (better for cache)
export OMP_PROC_BIND=close
export OMP_PLACES=cores
```

#### CPU Governor

Ensure CPU is running at maximum frequency:

```bash
# Check current governor
cat /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor

# Set to performance mode
echo performance | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor

# Or install cpupower
sudo apt-get install linux-tools-common
sudo cpupower frequency-set -g performance
```

### Memory Optimization

#### Memory Allocation

**Avoid swapping at all costs** - it can slow simulations by 100-1000x:

```bash
# Check swap usage
free -h

# Disable swap for maximum performance (if you have enough RAM)
sudo swapoff -a

# Make permanent (edit /etc/fstab and comment out swap line)
```

**Docker Memory Limits:**

Set appropriate limits to prevent OOM kills:

```yaml
# docker-compose.yml
services:
  fenicsx:
    deploy:
      resources:
        limits:
          memory: 8G
        reservations:
          memory: 4G
```

**Huge Pages for Large Simulations:**

Improve TLB efficiency for memory-intensive workloads:

```bash
# Check current huge pages
cat /proc/meminfo | grep Huge

# Allocate 2GB of 2MB huge pages
echo 1024 | sudo tee /sys/kernel/mm/hugepages/hugepages-2048kB/nr_hugepages

# Make permanent in /etc/sysctl.conf
vm.nr_hugepages = 1024
```

Mount huge pages in containers:

```yaml
services:
  fenicsx:
    volumes:
      - /dev/hugepages:/dev/hugepages
    cap_add:
      - IPC_LOCK
```

#### Memory Speed and Channels

- Use dual-channel or quad-channel memory configuration
- Match memory speed to CPU specifications (e.g., DDR4-3200 for modern CPUs)
- Enable XMP/DOCP in BIOS for rated speeds

### GPU/NPU Acceleration

#### NVIDIA GPU Optimization

**1. GPU Selection:**

```bash
# List available GPUs
nvidia-smi -L

# Pin to specific GPU
export CUDA_VISIBLE_DEVICES=0  # Use first GPU only

# Use multiple GPUs
export CUDA_VISIBLE_DEVICES=0,1
```

**2. GPU Clock Settings:**

```bash
# Lock GPU to maximum clocks for consistent performance
sudo nvidia-smi -pm 1  # Enable persistence mode
sudo nvidia-smi -lgc 1800  # Lock GPU clock (adjust for your GPU)
```

**3. Memory Optimization:**

```bash
# Pre-allocate GPU memory to avoid fragmentation
export TF_FORCE_GPU_ALLOW_GROWTH=false  # TensorFlow
export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512  # PyTorch
```

**4. Docker Configuration:**

```yaml
services:
  fenicsx-gpu:
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu, compute, utility]
    environment:
      - NVIDIA_VISIBLE_DEVICES=0
      - CUDA_VISIBLE_DEVICES=0
```

#### Intel GPU/NPU Optimization

**1. Device Selection:**

```bash
# List Intel compute devices
clinfo

# Set GPU affinity
export ZE_AFFINITY_MASK=0  # First GPU
export ZE_ENABLE_PCI_ID_DEVICE_ORDER=1
```

**2. oneAPI Configuration:**

```bash
# Source oneAPI environment
source /opt/intel/oneapi/setvars.sh

# Enable Level Zero debugging (if needed)
export ZE_ENABLE_VALIDATION_LAYER=1
```

**3. Docker Configuration:**

```yaml
services:
  fenicsx-intel:
    devices:
      - /dev/dri:/dev/dri
    group_add:
      - video
      - render
    environment:
      - ZE_AFFINITY_MASK=0
      - ONEAPI_DEVICE_SELECTOR=level_zero:0
```

#### AMD GPU Optimization

**1. GPU Configuration:**

```bash
# Check GPU status
rocm-smi

# Set performance mode
rocm-smi --setperflevel high

# Monitor GPU utilization
watch -n 1 rocm-smi
```

**2. Environment Variables:**

```bash
# Override GFX version if needed
export HSA_OVERRIDE_GFX_VERSION=10.3.0

# Enable GPU debug
export HIP_VISIBLE_DEVICES=0
export GPU_DEVICE_ORDINAL=0
```

### Storage Optimization

#### Disk Selection

**Best to Worst:**
1. **NVMe SSD** - Best for I/O intensive simulations (10-50x faster than HDD)
2. **SATA SSD** - Good for most workloads (5-10x faster than HDD)
3. **HDD** - Avoid for performance-critical work

**Recommended Configuration:**
- OS and containers on NVMe/SSD
- Input data on NVMe/SSD
- Output/results can be on HDD for archival

#### Docker Storage Driver

Use overlay2 for best performance:

```bash
# Check current driver
docker info | grep "Storage Driver"

# Configure overlay2 in /etc/docker/daemon.json
{
  "storage-driver": "overlay2"
}

# Restart Docker
sudo systemctl restart docker
```

#### Volume Optimization

```yaml
# Use named volumes instead of bind mounts for better performance
services:
  fenicsx:
    volumes:
      - simulation-data:/data  # Named volume (faster)
      # - ./data:/data  # Bind mount (slower)

volumes:
  simulation-data:
    driver: local
```

**tmpfs for Temporary Data:**

Use RAM-backed storage for temporary files:

```yaml
services:
  fenicsx:
    tmpfs:
      - /tmp:size=2G,mode=1777
      - /workspace/scratch:size=4G
```

### Network Optimization (for Kubernetes/Distributed)

#### Network Selection

- Use dedicated network interface for cluster traffic
- Enable jumbo frames (MTU 9000) for high-throughput workloads
- Consider 10GbE or faster for multi-node setups

```bash
# Set MTU for better throughput
ip link set eth0 mtu 9000

# Verify
ip link show eth0
```

#### Kubernetes Network Policies

Optimize pod-to-pod communication:

```yaml
# Use host network for performance-critical pods
apiVersion: v1
kind: Pod
metadata:
  name: simulation-job
spec:
  hostNetwork: true  # Direct host networking
  containers:
  - name: fenicsx
    image: fenicsx-toolbox:latest
```

---

## Software Configuration

### Docker Configuration

#### Daemon Settings

Optimize Docker daemon for performance:

```json
{
  "storage-driver": "overlay2",
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  },
  "default-ulimits": {
    "nofile": {
      "Name": "nofile",
      "Hard": 64000,
      "Soft": 64000
    }
  },
  "max-concurrent-downloads": 10,
  "max-concurrent-uploads": 10
}
```

Save to `/etc/docker/daemon.json` and restart:

```bash
sudo systemctl restart docker
```

#### Resource Limits

Configure appropriate defaults:

```yaml
# docker-compose.yml
services:
  celery-worker:
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 8G
        reservations:
          cpus: '2'
          memory: 4G
```

### Kubernetes Configuration

#### Scheduler Optimization

**Node Affinity for GPU Workloads:**

```yaml
affinity:
  nodeAffinity:
    requiredDuringSchedulingIgnoredDuringExecution:
      nodeSelectorTerms:
      - matchExpressions:
        - key: accelerator
          operator: In
          values:
          - nvidia-gpu
          - intel-gpu
```

**Pod Anti-Affinity for Distribution:**

```yaml
affinity:
  podAntiAffinity:
    preferredDuringSchedulingIgnoredDuringExecution:
    - weight: 100
      podAffinityTerm:
        labelSelector:
          matchExpressions:
          - key: app
            operator: In
            values:
            - simulation-worker
        topologyKey: kubernetes.io/hostname
```

#### Resource Quotas

Set per-namespace limits:

```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: simulation-quota
  namespace: keystone
spec:
  hard:
    requests.cpu: "64"
    requests.memory: 128Gi
    limits.cpu: "128"
    limits.memory: 256Gi
    nvidia.com/gpu: "4"
```

#### Quality of Service (QoS)

Configure for guaranteed resources:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: critical-simulation
spec:
  containers:
  - name: fenicsx
    image: fenicsx-toolbox:latest
    resources:
      limits:
        cpu: "8"
        memory: 16Gi
      requests:
        cpu: "8"  # Must match limits for Guaranteed QoS
        memory: 16Gi
```

### Celery Worker Configuration

#### Concurrency Settings

```bash
# In docker-compose.yml or Dockerfile
CMD ["celery", "-A", "celery_app", "worker", \
     "--loglevel=info", \
     "--concurrency=4", \
     "--max-tasks-per-child=1000", \
     "--prefetch-multiplier=1"]
```

**Parameters Explained:**
- `--concurrency=4`: Number of worker processes (match to CPU cores)
- `--max-tasks-per-child=1000`: Recycle workers to prevent memory leaks
- `--prefetch-multiplier=1`: Fetch one task at a time (better for long tasks)

#### Task Routing

Separate queues for different workload types:

```python
# celery_app.py
app.conf.task_routes = {
    'tasks.simulation.quick': {'queue': 'quick'},
    'tasks.simulation.long': {'queue': 'long'},
    'tasks.simulation.gpu': {'queue': 'gpu'},
}
```

Start specialized workers:

```bash
# CPU-only worker
celery -A celery_app worker -Q quick,long -n cpu-worker@%h

# GPU worker
celery -A celery_app worker -Q gpu -n gpu-worker@%h
```

### Redis Configuration

Optimize for task queue performance:

```conf
# redis.conf
maxmemory 2gb
maxmemory-policy allkeys-lru
save ""  # Disable persistence for better performance
appendonly no
```

Or via Docker Compose:

```yaml
services:
  redis:
    image: redis:7-alpine
    command: redis-server --maxmemory 2gb --maxmemory-policy allkeys-lru --save "" --appendonly no
```

### Environment Variables

#### Critical Performance Variables

**OpenMP:**
```bash
export OMP_NUM_THREADS=8
export OMP_PROC_BIND=spread
export OMP_PLACES=threads
export OMP_WAIT_POLICY=active  # Spin wait (lower latency)
# export OMP_WAIT_POLICY=passive  # Yield (lower CPU for mixed workloads)
```

**Python:**
```bash
export PYTHONUNBUFFERED=1  # Immediate output
export PYTHONDONTWRITEBYTECODE=1  # No .pyc files
export PYTHONHASHSEED=0  # Reproducible results
```

**CUDA/GPU:**
```bash
export CUDA_VISIBLE_DEVICES=0
export CUDA_DEVICE_ORDER=PCI_BUS_ID
```

**System:**
```bash
export MALLOC_ARENA_MAX=2  # Reduce memory fragmentation
export MALLOC_TRIM_THRESHOLD_=128000
```

---

## Simulation-Specific Tuning

### FEniCSx (Finite Element Method)

#### Mesh Optimization

```python
# Use appropriate mesh refinement
mesh_size = 64  # Start here, then increase

# For parallel execution
from mpi4py import MPI
comm = MPI.COMM_WORLD
rank = comm.Get_rank()

# Distribute mesh across processes
mesh = create_mesh(MPI.COMM_WORLD, cells, points, domain)
```

#### Solver Configuration

```python
# Use efficient solvers
from dolfinx.fem.petsc import LinearProblem

problem = LinearProblem(
    a, L, bcs=bcs,
    petsc_options={
        "ksp_type": "cg",
        "pc_type": "hypre",
        "pc_hypre_type": "boomeramg",
        "ksp_rtol": 1e-8,
        "ksp_atol": 1e-10
    }
)
```

#### GPU Acceleration

```python
# Use CUDA-enabled PETSc build
import os
os.environ["PETSC_OPTIONS"] = "-use_gpu_aware_mpi 1 -vec_type cuda -mat_type aijcusparse"
```

### LAMMPS (Molecular Dynamics)

#### Package Selection

Enable appropriate acceleration packages:

```bash
# Check available packages
lmp -h

# Use GPU package for NVIDIA
lmp -sf gpu -pk gpu 1

# Use KOKKOS for multi-threading
lmp -sf kk -k on t 8 -pk kokkos newton on

# Use OpenMP
lmp -sf omp -pk omp 8
```

#### Input Script Optimization

```lammps
# Reduce output frequency
thermo 1000  # Instead of every step

# Use efficient neighbor lists
neighbor 2.0 bin
neigh_modify delay 10 every 1 check yes

# Optimize communication
comm_modify mode single cutoff 2.5 vel yes
```

#### Run Configuration

```bash
# CPU-only with OpenMP
docker compose run --rm -e OMP_NUM_THREADS=8 lammps \
  lmp -sf omp -pk omp 8 -in input.lammps

# GPU acceleration
docker compose run --rm --gpus all lammps \
  lmp -sf gpu -pk gpu 1 -in input.lammps
```

### OpenFOAM (Computational Fluid Dynamics)

#### Mesh Decomposition

```bash
# Decompose for parallel execution
# system/decomposeParDict
numberOfSubdomains 8;

method simple;
simpleCoeffs
{
    n (2 2 2);  # 2x2x2 = 8 domains
}

# Run decomposition
decomposePar
```

#### Solver Selection

Use efficient solvers in system/fvSolution:

```cpp
solvers
{
    p
    {
        solver          PCG;
        preconditioner  DIC;
        tolerance       1e-6;
        relTol          0.01;
    }

    U
    {
        solver          smoothSolver;
        smoother        symGaussSeidel;
        tolerance       1e-6;
        relTol          0.1;
    }
}
```

#### Parallel Execution

```bash
# Run in parallel
mpirun -np 8 simpleFoam -parallel

# Or via Docker
docker compose run --rm -e OMP_NUM_THREADS=8 openfoam \
  bash -c "decomposePar && mpirun -np 8 simpleFoam -parallel"
```

---

## Workflow Optimization

### Parallel Task Execution

#### Batch Submission

Submit multiple tasks efficiently:

```python
from task_pipeline import TaskPipeline

pipeline = TaskPipeline()

# Create batch of tasks
tasks = []
for mesh_size in [16, 32, 64, 128, 256]:
    tasks.append({
        "tool": "fenicsx",
        "script": "poisson.py",
        "params": {"mesh_size": mesh_size}
    })

# Submit all at once (parallel)
task_ids = pipeline.submit_workflow(tasks, sequential=False)

# Wait for completion with progress callback
def show_progress(status):
    print(f"Completed {status['completed']}/{status['total']} tasks")

results = pipeline.wait_for_workflow(task_ids, callback=show_progress)
```

#### Parameter Sweeps

Automatically explore parameter space:

```python
# Define parameter grid
param_grid = {
    'mesh_size': [32, 64, 128],
    'time_steps': [100, 200, 500],
    'tolerance': [1e-6, 1e-8, 1e-10]
}

# Submit all combinations (3 × 3 × 3 = 27 tasks)
task_ids = pipeline.parameter_sweep(
    tool='fenicsx',
    script='poisson.py',
    param_grid=param_grid
)

# Analyze performance
stats = pipeline.get_parallel_execution_stats(task_ids)
print(f"Speedup: {stats['speedup']:.2f}x")
print(f"Efficiency: {stats['efficiency']:.1%}")
```

### Worker Scaling

#### Dynamic Scaling

**Docker Compose:**
```bash
# Scale workers based on workload
docker compose up -d --scale celery-worker=8

# Scale down when idle
docker compose up -d --scale celery-worker=2
```

**Kubernetes Horizontal Pod Autoscaler:**
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: celery-worker-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: celery-worker
  minReplicas: 2
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 80
```

### Task Prioritization

Prioritize critical simulations:

```python
# Submit high-priority task
task_id = pipeline.submit_task(
    tool="fenicsx",
    script="critical_simulation.py",
    priority=9  # Higher number = higher priority (default: 5)
)
```

Configure priority queues in Celery:

```python
# celery_app.py
from kombu import Exchange, Queue

app.conf.task_queues = (
    Queue('high', Exchange('high'), routing_key='high', priority=9),
    Queue('default', Exchange('default'), routing_key='default', priority=5),
    Queue('low', Exchange('low'), routing_key='low', priority=1),
)
```

### Workflow Patterns

#### Pipeline Pattern

Sequential processing with data dependencies:

```python
# Step 1: Generate mesh
mesh_task_id = pipeline.submit_task("fenicsx", "generate_mesh.py")
mesh_result = pipeline.wait_for_task(mesh_task_id)

# Step 2: Run simulation with generated mesh
sim_task_id = pipeline.submit_task(
    "fenicsx",
    "run_simulation.py",
    params={"mesh_file": mesh_result['artifacts'][0]}
)
sim_result = pipeline.wait_for_task(sim_task_id)

# Step 3: Post-process results
post_task_id = pipeline.submit_task(
    "fenicsx",
    "post_process.py",
    params={"result_file": sim_result['artifacts'][0]}
)
```

#### Map-Reduce Pattern

Parallel computation with aggregation:

```python
# Map: Run simulations in parallel
map_tasks = []
for i in range(100):
    task_id = pipeline.submit_task(
        "fenicsx",
        "monte_carlo_sample.py",
        params={"seed": i}
    )
    map_tasks.append(task_id)

# Wait for all map tasks
map_results = pipeline.wait_for_workflow(map_tasks)

# Reduce: Aggregate results
reduce_task_id = pipeline.submit_task(
    "fenicsx",
    "aggregate_results.py",
    params={"input_files": [r['artifacts'][0] for r in map_results]}
)
```

---

## Container Optimization

### Image Size Reduction

Smaller images deploy faster and use less storage.

#### Multi-Stage Builds

```dockerfile
# Build stage
FROM python:3.11-slim AS builder
WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Runtime stage
FROM python:3.11-slim
COPY --from=builder /root/.local /root/.local
COPY src/ /app/
WORKDIR /app
CMD ["python", "main.py"]
```

**Savings:** 30-50% reduction in image size

#### Minimal Base Images

```dockerfile
# Use slim variants
FROM python:3.11-slim  # Instead of python:3.11

# Or Alpine for minimal size
FROM python:3.11-alpine  # ~5MB vs ~75MB for slim
```

#### Cleanup in Same Layer

```dockerfile
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*
```

### Build Performance

#### BuildKit

Enable for parallel builds and better caching:

```bash
export DOCKER_BUILDKIT=1
docker compose build --parallel
```

#### .dockerignore

Exclude unnecessary files:

```
.git
*.md
__pycache__
*.pyc
.pytest_cache
data/
output/
.vscode
.idea
```

**Savings:** 50-90% faster context transfer

### Runtime Optimization

#### Environment Variables

```dockerfile
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    OMP_NUM_THREADS=1 \
    OMP_PROC_BIND=spread \
    OMP_PLACES=threads
```

#### Resource Limits

```yaml
services:
  simulation:
    deploy:
      resources:
        limits:
          cpus: '8'
          memory: 16G
```

**See:** [CONTAINER_OPTIMIZATION.md](CONTAINER_OPTIMIZATION.md) for complete details

---

## Monitoring and Profiling

### Resource Profiling

Enable automatic profiling for all simulations:

```bash
# Submit with automatic profiling
cd src/agent
python3 cli.py submit fenicsx poisson.py --wait

# View detailed profile
python3 cli.py job-details <task-id>
```

**Metrics Collected:**
- CPU usage (user/system time, percentage)
- Memory consumption (RSS, VMS, peak)
- GPU utilization and memory (if available)
- Disk I/O (read/write operations and bytes)
- Network I/O
- Container-specific metrics

### Performance Analysis

```bash
# View job history with resource metrics
python3 cli.py job-history --limit 20

# Show aggregate statistics
python3 cli.py job-stats

# Filter by tool or status
python3 cli.py job-history --tool fenicsx --status success
```

**See:** [RESOURCE_PROFILING.md](RESOURCE_PROFILING.md) for comprehensive guide

### Benchmarking

Compare performance across configurations:

```bash
cd src

# Benchmark CPU
python3 benchmark.py --tool fenicsx --device cpu --runs 3

# Benchmark GPU
python3 benchmark.py --tool fenicsx --device gpu --runs 3

# Compare results
python3 benchmark.py --compare <cpu-id> <gpu-id>

# Generate report
python3 benchmark.py --report
```

**See:** [BENCHMARK_GUIDE.md](BENCHMARK_GUIDE.md) for detailed documentation

### Real-Time Monitoring

#### Docker Stats

```bash
# Monitor container resources
docker stats

# Specific containers
docker stats celery-worker fenicsx
```

#### GPU Monitoring

```bash
# NVIDIA
watch -n 1 nvidia-smi

# Intel
intel_gpu_top

# AMD
watch -n 1 rocm-smi
```

#### Celery Monitoring

```bash
# Worker status
celery -A celery_app inspect active
celery -A celery_app inspect stats

# Queue status
celery -A celery_app inspect active_queues
```

---

## Troubleshooting Performance Issues

### Symptom: Slow Simulation Execution

**Check CPU throttling:**
```bash
# Check CPU frequency
watch -n 1 "cat /proc/cpuinfo | grep MHz"

# Disable throttling
echo performance | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor
```

**Check memory swapping:**
```bash
# High swap usage kills performance
free -h
vmstat 1

# Solution: Add RAM or disable swap
sudo swapoff -a
```

**Check I/O bottleneck:**
```bash
# Monitor disk activity
iostat -x 1

# Use faster storage (NVMe SSD)
# Use tmpfs for temporary files
```

### Symptom: GPU Underutilization

**Verify GPU access:**
```bash
# NVIDIA
docker run --rm --gpus all nvidia/cuda:12.0.0-base-ubuntu22.04 nvidia-smi

# Intel
docker run --rm --device /dev/dri:/dev/dri intel/oneapi-basekit clinfo
```

**Check GPU memory:**
```bash
# GPU memory too small for problem size?
nvidia-smi --query-gpu=memory.total,memory.used,memory.free --format=csv
```

**Solution:**
- Reduce problem size
- Use model parallelism
- Enable memory swapping (with performance penalty)

### Symptom: Poor Parallel Scaling

**Check worker utilization:**
```bash
# Are all workers busy?
celery -A celery_app inspect active
docker compose ps
```

**Common causes:**
1. **Too few tasks:** Not enough work to saturate workers
   - Solution: Increase problem size or batch size

2. **Task dependencies:** Sequential bottleneck
   - Solution: Restructure workflow for more parallelism

3. **Resource contention:** Workers competing for resources
   - Solution: Reduce concurrency or add hardware

4. **I/O bottleneck:** Shared storage saturated
   - Solution: Use local storage or faster disks

### Symptom: Out of Memory Errors

**Check memory limits:**
```bash
# Container limits
docker inspect container_name | grep -i memory

# System memory
free -h
```

**Solutions:**

1. **Increase container limits:**
```yaml
services:
  simulation:
    deploy:
      resources:
        limits:
          memory: 32G
```

2. **Reduce problem size:**
```python
# Smaller mesh, fewer time steps, etc.
mesh_size = 32  # Instead of 256
```

3. **Enable out-of-core algorithms:**
```python
# Use disk-backed arrays for large data
import numpy as np
large_array = np.memmap('temp.dat', dtype='float64', mode='w+', shape=(1000000, 1000))
```

4. **Add swap (with performance penalty):**
```bash
sudo swapon /swapfile
```

### Symptom: High Build Times

**Enable BuildKit:**
```bash
export DOCKER_BUILDKIT=1
```

**Use .dockerignore:**
```
.git
data/
output/
```

**Cache dependencies:**
```dockerfile
# Install deps before copying code
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .  # This layer rebuilds less often
```

**See:** [CONTAINER_OPTIMIZATION.md](CONTAINER_OPTIMIZATION.md)

### Symptom: Network Bottleneck (Kubernetes)

**Check network latency:**
```bash
# Test pod-to-pod latency
kubectl run test-pod --rm -it --image=nicolaka/netshoot -- iperf3 -c service-name
```

**Solutions:**

1. **Enable host networking:**
```yaml
spec:
  hostNetwork: true
```

2. **Use CNI with better performance:**
- Calico (default in k3d)
- Cilium (eBPF-based)
- Flannel (simple)

3. **Increase MTU:**
```bash
ip link set eth0 mtu 9000
```

---

## Performance Checklist

Use this checklist to ensure optimal configuration:

### Hardware
- [ ] CPU governor set to "performance"
- [ ] Memory running at rated speed (XMP/DOCP enabled)
- [ ] Sufficient RAM to avoid swapping (check with `free -h`)
- [ ] Fast storage (NVMe SSD preferred)
- [ ] GPU drivers installed and verified (if applicable)

### Software
- [ ] Docker BuildKit enabled (`export DOCKER_BUILDKIT=1`)
- [ ] Docker storage driver set to overlay2
- [ ] Container images optimized (multi-stage builds, cleanup)
- [ ] .dockerignore files in place
- [ ] Appropriate resource limits set

### Configuration
- [ ] `OMP_NUM_THREADS` set correctly
- [ ] `OMP_PROC_BIND` and `OMP_PLACES` configured
- [ ] Python buffering disabled (`PYTHONUNBUFFERED=1`)
- [ ] GPU environment variables set (if applicable)
- [ ] Celery worker concurrency optimized

### Workflows
- [ ] Using parallel task submission when possible
- [ ] Worker count matches workload
- [ ] Task priorities configured
- [ ] Monitoring and profiling enabled

### Monitoring
- [ ] Resource profiling active
- [ ] Benchmarks run for baseline comparison
- [ ] Regular checks for bottlenecks
- [ ] Job history tracked for performance trends

---

## Performance Targets by Workload

### Interactive Development
- **Container startup:** < 2 seconds
- **Task submission:** < 100ms
- **Status query:** < 50ms
- **Build time (cached):** < 10 seconds

### Small Simulations (< 1 minute)
- **Task overhead:** < 5% of execution time
- **Parallel efficiency:** > 80%
- **Memory overhead:** < 500MB per task

### Medium Simulations (1-10 minutes)
- **Task overhead:** < 2% of execution time
- **Parallel efficiency:** > 85%
- **Resource utilization:** > 90%

### Large Simulations (> 10 minutes)
- **Task overhead:** < 1% of execution time
- **Parallel efficiency:** > 90%
- **Resource utilization:** > 95%

### GPU Acceleration
- **Expected speedup:** 2-50x vs CPU (problem dependent)
- **GPU utilization:** > 80% for compute-bound tasks
- **Memory transfer overhead:** < 10% of execution time

---

## Best Practices Summary

### DO:
✅ Profile before optimizing - measure to find real bottlenecks  
✅ Use GPU acceleration for compatible workloads  
✅ Submit tasks in parallel when independent  
✅ Scale workers to match workload  
✅ Use fast storage (NVMe SSD) for I/O intensive work  
✅ Monitor resource utilization regularly  
✅ Set appropriate CPU affinity and OpenMP settings  
✅ Optimize container images (multi-stage builds, cleanup)  
✅ Use benchmarking to compare configurations  
✅ Keep containers updated for performance improvements  

### DON'T:
❌ Run on swap - it kills performance  
❌ Oversubscribe CPU cores  
❌ Ignore resource limits - leads to OOM kills  
❌ Use slow storage (HDD) for active workloads  
❌ Run sequential workflows when parallelism is possible  
❌ Skip monitoring - you can't improve what you don't measure  
❌ Copy large unnecessary files into build context  
❌ Use debug builds for production workloads  
❌ Ignore thermal throttling on laptops  
❌ Assume defaults are optimal - tune for your workload  

---

## Additional Resources

### Documentation
- **[GPU_ACCELERATION.md](GPU_ACCELERATION.md)** - GPU/NPU setup and configuration
- **[CONTAINER_OPTIMIZATION.md](CONTAINER_OPTIMIZATION.md)** - Container image optimization
- **[BENCHMARK_GUIDE.md](BENCHMARK_GUIDE.md)** - Performance benchmarking system
- **[RESOURCE_PROFILING.md](RESOURCE_PROFILING.md)** - Resource monitoring and profiling
- **[PARALLEL_ORCHESTRATION.md](PARALLEL_ORCHESTRATION.md)** - Parallel workflow patterns
- **[PARALLEL_SIMULATIONS.md](PARALLEL_SIMULATIONS.md)** - OpenMP and MPI configuration
- **[ORCHESTRATION_GUIDE.md](ORCHESTRATION_GUIDE.md)** - Workflow orchestration guide

### Tools
- **Docker BuildKit:** https://docs.docker.com/build/buildkit/
- **NVIDIA Container Toolkit:** https://github.com/NVIDIA/nvidia-container-toolkit
- **Intel oneAPI:** https://www.intel.com/content/www/us/en/developer/tools/oneapi/overview.html
- **AMD ROCm:** https://rocm.docs.amd.com/
- **Celery:** https://docs.celeryq.dev/

### Community
- **Issues:** https://github.com/aubreyhayes47/KeystoneSupercomputer/issues
- **Discussions:** https://github.com/aubreyhayes47/KeystoneSupercomputer/discussions

---

## Feedback and Contributions

Found a performance optimization we missed? Have a use case that needs specific tuning?

- Open an issue: https://github.com/aubreyhayes47/KeystoneSupercomputer/issues
- Submit a PR with your optimization techniques
- Share your benchmarks and results

**Together we can make Keystone Supercomputer faster for everyone!**
