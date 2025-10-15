# Parallel Simulations Guide

## Overview

Keystone Supercomputer supports parallel simulations using **OpenMP** (multi-core shared memory) and **MPI** (distributed multi-process) for all supported simulation tools. This guide covers configuration, usage, and best practices for parallel computing.

---

## Table of Contents

- [Quick Start](#quick-start)
- [Understanding Parallel Computing Models](#understanding-parallel-computing-models)
- [Simulation Tools](#simulation-tools)
  - [LAMMPS Parallel Execution](#lammps-parallel-execution)
  - [FEniCSx Parallel Execution](#fenicsx-parallel-execution)
  - [OpenFOAM Parallel Execution](#openfoam-parallel-execution)
- [Docker Compose Configuration](#docker-compose-configuration)
- [Kubernetes Configuration](#kubernetes-configuration)
- [Performance Tuning](#performance-tuning)
- [Testing Parallel Support](#testing-parallel-support)
- [Troubleshooting](#troubleshooting)

---

## Quick Start

All simulation containers include OpenMP and MPI support out of the box. To run a parallel simulation:

```bash
# Docker Compose: Run with MPI (4 processes)
docker compose run --rm lammps mpirun -np 4 --allow-run-as-root lmp -in input.lammps

# Docker Compose: Run with OpenMP (4 threads)
docker compose run --rm -e OMP_NUM_THREADS=4 lammps lmp -in input.lammps

# Docker Compose: Hybrid MPI + OpenMP
docker compose run --rm -e OMP_NUM_THREADS=2 lammps \
  mpirun -np 4 --allow-run-as-root lmp -in input.lammps
```

**Quick Test**: Verify parallel support is working:

```bash
# Test LAMMPS
docker compose run --rm lammps bash /app/test_parallel.sh

# Test FEniCSx
docker compose run --rm --entrypoint="" fenicsx mpirun -np 4 python3 /app/test_parallel.py

# Test OpenFOAM
docker compose run --rm openfoam bash /workspace/test_parallel.sh
```

---

## Understanding Parallel Computing Models

### OpenMP (Shared Memory Parallelism)

- **Use case**: Multi-core parallelism on a single node
- **Best for**: Small to medium problems that fit in memory
- **Configuration**: Set `OMP_NUM_THREADS` environment variable
- **Overhead**: Low, but limited to single node

### MPI (Distributed Parallelism)

- **Use case**: Multi-process parallelism across nodes
- **Best for**: Large problems requiring distributed computing
- **Configuration**: Use `mpirun -np <N>` to launch
- **Overhead**: Higher communication overhead, scales to multiple nodes

### Hybrid OpenMP + MPI

- **Use case**: Best performance on multi-node clusters
- **Configuration**: Combine both methods
- **Example**: 4 MPI processes × 2 OpenMP threads = 8 total cores

---

## Simulation Tools

### LAMMPS Parallel Execution

LAMMPS supports both OpenMP and MPI parallelism.

#### OpenMP Only

```bash
# Set number of threads
export OMP_NUM_THREADS=4

# Run with OpenMP
docker compose run --rm -e OMP_NUM_THREADS=4 lammps \
  lmp -sf omp -in input.lammps
```

#### MPI Only

```bash
# Run with 4 MPI processes
docker compose run --rm lammps \
  mpirun -np 4 --allow-run-as-root lmp -in input.lammps
```

#### Hybrid OpenMP + MPI

```bash
# 4 MPI processes, each using 2 OpenMP threads = 8 cores total
docker compose run --rm -e OMP_NUM_THREADS=2 lammps \
  mpirun -np 4 --allow-run-as-root lmp -sf omp -in input.lammps
```

#### Performance Tips

- Use `-sf omp` suffix style for OpenMP acceleration
- For small systems, OpenMP may be faster due to lower overhead
- For large systems, MPI typically scales better
- Hybrid approach works best on multi-socket systems

#### Example LAMMPS Script

```bash
# Save your input as input.lammps
cat > /tmp/input.lammps << 'EOF'
units lj
atom_style atomic
lattice fcc 0.8442
region box block 0 10 0 10 0 10
create_box 1 box
create_atoms 1 box
mass 1 1.0
velocity all create 1.44 87287
pair_style lj/cut 2.5
pair_coeff 1 1 1.0 1.0 2.5
neighbor 0.3 bin
neigh_modify every 20 delay 0 check no
fix 1 all nve
timestep 0.005
thermo 100
run 1000
EOF

# Run with MPI
docker compose run --rm -v /tmp:/data lammps \
  mpirun -np 4 --allow-run-as-root lmp -in /data/input.lammps
```

### Testing LAMMPS Parallel Support

```bash
# Test OpenMP and MPI
docker compose run --rm lammps bash /app/test_parallel.sh
```

---

### FEniCSx Parallel Execution

FEniCSx primarily uses MPI for parallelism through PETSc.

#### MPI Execution

```bash
# Run with 4 MPI processes
docker compose run --rm fenicsx \
  mpirun -np 4 python3 poisson.py
```

#### Python Script with MPI

```python
from mpi4py import MPI
from dolfinx import mesh, fem, io
import numpy as np

# Get MPI communicator
comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()

# Create mesh (distributed across processes)
msh = mesh.create_unit_square(comm, 64, 64)

if rank == 0:
    print(f"Running on {size} processes")

# Your FEniCSx code here...
```

#### Performance Tips

- FEniCSx automatically distributes mesh across MPI processes
- Larger meshes benefit more from parallelization
- Use PETSc command-line options for fine-tuning: `-ksp_monitor -ksp_view`

#### Example Parallel Poisson

```bash
# Edit poisson.py to use MPI
docker compose run --rm fenicsx \
  mpirun -np 4 python3 poisson.py

# Monitor from another terminal
docker compose exec fenicsx ps aux
```

### Testing FEniCSx Parallel Support

```bash
# Test MPI
docker compose run --rm fenicsx python3 test_parallel.py
docker compose run --rm fenicsx mpirun -np 4 python3 test_parallel.py
```

---

### OpenFOAM Parallel Execution

OpenFOAM uses domain decomposition for parallel execution with MPI.

#### Workflow

1. **Decompose** domain into subdomains
2. **Run** solver in parallel
3. **Reconstruct** results

#### Step-by-Step Example

```bash
# 1. Create your case in /data/openfoam
cd /data/openfoam/cavity

# 2. Generate mesh
docker compose run --rm openfoam blockMesh

# 3. Create decomposition dictionary
cat > system/decomposeParDict << 'EOF'
FoamFile
{
    version     2.0;
    format      ascii;
    class       dictionary;
    object      decomposeParDict;
}
numberOfSubdomains 4;
method          scotch;
EOF

# 4. Decompose domain
docker compose run --rm openfoam decomposePar

# 5. Run in parallel (4 processes)
docker compose run --rm openfoam \
  mpirun -np 4 --allow-run-as-root simpleFoam -parallel

# 6. Reconstruct solution
docker compose run --rm openfoam reconstructPar
```

#### Decomposition Methods

- **scotch**: Automatic, good load balance (recommended)
- **simple**: Simple geometric decomposition
- **hierarchical**: Hierarchical decomposition
- **metis**: METIS-based (requires installation)

#### Performance Tips

- Use `scotch` method for best load balancing
- Number of subdomains should match MPI processes
- Larger cases benefit more from parallelization
- OpenMP: Set `OMP_NUM_THREADS` for additional thread parallelism

#### Example Complete Workflow

```bash
#!/bin/bash
# Complete parallel OpenFOAM workflow

# Source environment
docker compose run --rm openfoam bash << 'EOF'
source /opt/openfoam11/etc/bashrc

cd /data/openfoam/cavity

# Mesh
blockMesh

# Decompose for 4 processes
decomposePar

# Run parallel
mpirun -np 4 --allow-run-as-root icoFoam -parallel

# Reconstruct
reconstructPar

# Check results
ls -la
EOF
```

### Testing OpenFOAM Parallel Support

```bash
# Test MPI and parallel workflow
docker compose run --rm openfoam bash /workspace/test_parallel.sh
```

---

## Docker Compose Configuration

### Resource Limits

Control CPU and memory allocation in `docker-compose.yml`:

```yaml
services:
  lammps:
    deploy:
      resources:
        limits:
          cpus: '4.0'
          memory: 8G
        reservations:
          cpus: '2.0'
          memory: 4G
```

### Environment Variables

Set parallelism defaults:

```yaml
services:
  lammps:
    environment:
      - OMP_NUM_THREADS=4
      - OMP_PROC_BIND=spread
      - OMP_PLACES=threads
```

---

## Kubernetes Configuration

### MPI Job Example

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: lammps-mpi-job
spec:
  template:
    spec:
      containers:
      - name: lammps
        image: keystone/lammps:latest
        command: ["mpirun", "-np", "4", "lmp", "-in", "/data/input.lammps"]
        resources:
          limits:
            cpu: "4"
            memory: "8Gi"
        volumeMounts:
        - name: data
          mountPath: /data
      volumes:
      - name: data
        persistentVolumeClaim:
          claimName: simulation-data
      restartPolicy: Never
```

### Helm Configuration

Update `values.yaml` for parallel jobs:

```yaml
lammps:
  resources:
    requests:
      cpu: "4"
      memory: "4Gi"
    limits:
      cpu: "8"
      memory: "16Gi"
  env:
    - name: OMP_NUM_THREADS
      value: "4"
```

---

## Performance Tuning

### General Guidelines

1. **Start small**: Test with 1, 2, 4 processes to find scaling
2. **Monitor**: Use `htop`, `top`, or `docker stats` to check utilization
3. **Memory**: Ensure sufficient RAM per process (system RAM / processes)
4. **Storage**: Use local SSD for best I/O performance

### OpenMP Tuning

```bash
# Set number of threads
export OMP_NUM_THREADS=4

# Control thread affinity
export OMP_PROC_BIND=spread  # or: close, master
export OMP_PLACES=threads    # or: cores, sockets

# Enable nested parallelism (advanced)
export OMP_NESTED=true
export OMP_MAX_ACTIVE_LEVELS=2
```

### MPI Tuning

```bash
# Bind to cores
mpirun -np 4 --bind-to core --allow-run-as-root <command>

# Control mapping
mpirun -np 4 --map-by socket:PE=2 --allow-run-as-root <command>

# Tune buffer sizes
mpirun -np 4 --mca btl_tcp_eager_limit 32768 --allow-run-as-root <command>
```

### Container-Specific

```bash
# Allocate more CPUs to container
docker compose run --rm --cpus=8 lammps <command>

# Set CPU affinity
docker compose run --rm --cpuset-cpus=0-7 lammps <command>
```

---

## Testing Parallel Support

### Quick Tests

```bash
# Test LAMMPS
docker compose run --rm lammps bash /app/test_parallel.sh

# Test FEniCSx
docker compose run --rm fenicsx python3 test_parallel.py
docker compose run --rm fenicsx mpirun -np 4 python3 test_parallel.py

# Test OpenFOAM
docker compose run --rm openfoam bash /workspace/test_parallel.sh
```

### Verify Installation

```bash
# Check OpenMP
docker compose run --rm lammps bash -c \
  "echo 'int main(){return 0;}' | gcc -x c - -fopenmp && echo 'OpenMP OK'"

# Check MPI
docker compose run --rm lammps mpirun --version

# Check LAMMPS features
docker compose run --rm lammps lmp -h | grep -i "openmp\|mpi"
```

---

## Troubleshooting

### Common Issues

#### 1. MPI "run as root" Error

**Problem**: `mpirun` refuses to run as root

**Solution**: Add `--allow-run-as-root` flag

```bash
mpirun -np 4 --allow-run-as-root lmp -in input.lammps
```

#### 2. OpenMP Not Using Multiple Threads

**Problem**: Simulation runs on single core despite `OMP_NUM_THREADS`

**Solutions**:
- Verify `OMP_NUM_THREADS` is set: `echo $OMP_NUM_THREADS`
- Use correct suffix style for LAMMPS: `-sf omp`
- Check if application is compiled with OpenMP

#### 3. Poor Scaling

**Problem**: Performance doesn't improve with more cores

**Causes**:
- Problem size too small
- Poor load balancing
- I/O bottleneck
- Memory bandwidth limitation

**Solutions**:
- Increase problem size
- Use better decomposition (OpenFOAM: try `scotch`)
- Profile to identify bottlenecks

#### 4. Out of Memory

**Problem**: Container killed due to memory

**Solutions**:
```bash
# Increase memory limit
docker compose run --rm --memory=16g lammps <command>

# Reduce processes
mpirun -np 2 <command>  # instead of -np 4

# Check memory per process
# Total RAM / Number of processes should be > problem size
```

#### 5. Networking Issues (MPI)

**Problem**: MPI processes can't communicate

**Solutions**:
- Ensure containers are on same network
- Check firewall settings
- Use `--network host` for testing
- Verify OpenMPI version compatibility

---

## Best Practices

### 1. Choose the Right Parallelism

- **Small problems** (< 1M elements): OpenMP
- **Medium problems** (1M-10M elements): MPI or hybrid
- **Large problems** (> 10M elements): MPI multi-node

### 2. Resource Planning

```
Total cores needed = MPI processes × OpenMP threads
Memory needed = Problem size × Safety factor (1.5-2x)
```

### 3. Testing Strategy

1. Run serial first to establish baseline
2. Test with 2 processes to verify parallel works
3. Scale up: 4, 8, 16 processes
4. Measure speedup = Serial time / Parallel time
5. Stop scaling when speedup < 1.5× for doubling processes

### 4. Production Deployment

- Use Kubernetes for multi-node clusters
- Set resource requests and limits
- Monitor with Prometheus/Grafana
- Use persistent volumes for large datasets

---

## Examples Repository

Complete working examples are available in:
- `src/sim-toolbox/lammps/test_parallel.sh`
- `src/sim-toolbox/fenicsx/test_parallel.py`
- `src/sim-toolbox/openfoam/test_parallel.sh`

---

## Additional Resources

### Documentation
- [OpenMPI Documentation](https://www.open-mpi.org/doc/)
- [LAMMPS Parallel Guide](https://docs.lammps.org/Speed.html)
- [FEniCSx MPI Usage](https://docs.fenicsproject.org/)
- [OpenFOAM Parallel Guide](https://www.openfoam.com/documentation/user-guide/a-reference/a.2-running-applications-in-parallel)

### Performance Analysis
- Use `time` to measure execution time
- Use `htop` or `top` to monitor CPU usage
- Use `docker stats` to monitor container resources
- Profile with tool-specific profilers (e.g., `gprof`, `valgrind`)

---

## Summary

All Keystone Supercomputer simulation containers include:
- ✅ **OpenMP** support for multi-core parallelism
- ✅ **MPI** support for distributed parallelism  
- ✅ **Hybrid** OpenMP+MPI for maximum performance
- ✅ **Test scripts** to validate parallel functionality
- ✅ **Documentation** for all supported tools

For questions or issues, please open a GitHub issue.
