# Parallel Simulation Examples

This directory contains practical examples demonstrating OpenMP and MPI usage across all simulation tools.

## Quick Test

Verify all parallel support is working:

```bash
# Run all tests
./run_all_parallel_tests.sh
```

## LAMMPS Examples

### Serial Execution
```bash
docker compose run --rm lammps lmp -in /data/input.lammps
```

### MPI Parallel (4 processes)
```bash
docker compose run --rm lammps \
  mpirun -np 4 --allow-run-as-root lmp -in /data/input.lammps
```

### OpenMP Multi-threading (4 threads)
```bash
docker compose run --rm -e OMP_NUM_THREADS=4 lammps \
  lmp -in /data/input.lammps
```

### Hybrid MPI + OpenMP (2 processes × 2 threads = 4 cores)
```bash
docker compose run --rm -e OMP_NUM_THREADS=2 lammps \
  mpirun -np 2 --allow-run-as-root lmp -in /data/input.lammps
```

## FEniCSx Examples

### Serial Execution
```bash
docker compose run --rm fenicsx poisson.py
```

### MPI Parallel (4 processes)
```bash
docker compose run --rm --entrypoint="" fenicsx \
  mpirun -np 4 python3 poisson.py
```

## OpenFOAM Examples

### Serial Execution
```bash
# Run simulation in serial mode
docker compose run --rm openfoam simpleFoam
```

### MPI Parallel Workflow
```bash
# 1. Decompose domain for parallel execution
docker compose run --rm openfoam decomposePar

# 2. Run solver in parallel (4 processes)
docker compose run --rm openfoam \
  mpirun -np 4 --allow-run-as-root simpleFoam -parallel

# 3. Reconstruct solution
docker compose run --rm openfoam reconstructPar
```

## Performance Comparison

Run benchmarks to compare serial vs parallel performance:

```bash
# Serial baseline
time docker compose run --rm lammps lmp -in benchmark.lammps

# 2 processes
time docker compose run --rm lammps \
  mpirun -np 2 --allow-run-as-root lmp -in benchmark.lammps

# 4 processes
time docker compose run --rm lammps \
  mpirun -np 4 --allow-run-as-root lmp -in benchmark.lammps
```

## Kubernetes Examples

### Deploy with MPI support
```bash
# Install with HPC configuration
helm install keystone k8s/helm/keystone-simulation \
  -n keystone \
  -f k8s/helm/values-hpc.yaml

# Run MPI job
kubectl create job -n keystone lammps-parallel \
  --from=job/lammps-simulation \
  -- mpirun -np 4 --allow-run-as-root lmp -in /data/input.lammps
```

### Configure OpenMP threads
```bash
# Create custom values
cat > custom-parallel.yaml << EOF
lammps:
  config:
    ompNumThreads: "4"
    ompProcBind: "spread"
    ompPlaces: "threads"
EOF

# Deploy with custom configuration
helm upgrade keystone k8s/helm/keystone-simulation \
  -n keystone \
  -f custom-parallel.yaml
```

## Troubleshooting

### Check if MPI is working
```bash
docker compose run --rm lammps mpirun --version
docker compose run --rm fenicsx mpirun --version
docker compose run --rm openfoam mpirun --version
```

### Check OpenMP threads
```bash
docker compose run --rm -e OMP_NUM_THREADS=4 lammps \
  bash -c 'echo "OMP_NUM_THREADS=$OMP_NUM_THREADS"'
```

### Run test suites
```bash
# LAMMPS
docker compose run --rm lammps bash /app/test_parallel.sh

# FEniCSx
docker compose run --rm --entrypoint="" fenicsx python3 /app/test_parallel.py
docker compose run --rm --entrypoint="" fenicsx mpirun -np 4 python3 /app/test_parallel.py

# OpenFOAM
docker compose run --rm openfoam bash /workspace/test_parallel.sh
```

## Best Practices

1. **Start small**: Test with 2 processes first
2. **Monitor resources**: Use `docker stats` to check utilization
3. **Profile**: Measure speedup before scaling up
4. **Memory**: Ensure enough RAM per process (Total RAM / Number of processes)
5. **I/O**: Use fast storage for large datasets

## See Also

- [PARALLEL_SIMULATIONS.md](../PARALLEL_SIMULATIONS.md) - Complete parallel computing guide
- [ORCHESTRATION_GUIDE.md](../ORCHESTRATION_GUIDE.md) - Workflow orchestration
- [K3D.md](../K3D.md) - Kubernetes cluster setup
