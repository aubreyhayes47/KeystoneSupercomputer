# sim-toolbox Benchmark Registry

This directory contains the benchmark registry for all supported simulators in sim-toolbox.

## Contents

- **benchmark_schema.json**: JSON schema defining the structure of benchmark definitions
- **benchmark_registry.py**: Python module for managing and validating benchmarks
- **fenicsx/**: FEniCSx (Finite Element Method) benchmarks
- **lammps/**: LAMMPS (Molecular Dynamics) benchmarks
- **openfoam/**: OpenFOAM (Computational Fluid Dynamics) benchmarks

## Quick Start

```bash
# List all benchmarks
python3 benchmark_registry.py list

# View benchmark details
python3 benchmark_registry.py info --benchmark-id fenicsx-poisson-2d-basic

# Validate all benchmarks
python3 benchmark_registry.py validate-all

# Generate report
python3 benchmark_registry.py report --output BENCHMARK_REPORT.md

# Get statistics
python3 benchmark_registry.py stats
```

## Documentation

For comprehensive documentation, see:
- **[BENCHMARK_REGISTRY.md](../../../BENCHMARK_REGISTRY.md)**: Complete guide to the benchmark registry
- **[BENCHMARK_GUIDE.md](../../../BENCHMARK_GUIDE.md)**: Performance benchmarking system
- **[CONTRIBUTING_BENCHMARKS.md](CONTRIBUTING_BENCHMARKS.md)**: Guidelines for contributing benchmarks

## Available Benchmarks

### FEniCSx
- `fenicsx-poisson-2d-basic`: 2D Poisson equation solver (beginner)

### LAMMPS
- `lammps-lennard-jones-fluid`: Lennard-Jones fluid simulation (beginner)

### OpenFOAM
- `openfoam-cavity-flow`: Lid-driven cavity flow (beginner)

## Python API

```python
from benchmark_registry import BenchmarkRegistry

registry = BenchmarkRegistry()

# List benchmarks
benchmarks = registry.list_benchmarks(simulator="fenicsx")

# Load benchmark
benchmark = registry.load_benchmark("fenicsx-poisson-2d-basic")

# Validate benchmark
result = registry.validate_benchmark("fenicsx-poisson-2d-basic")
```

## Adding New Benchmarks

1. Create benchmark JSON file following the schema
2. Place in appropriate simulator directory
3. Validate with `python3 benchmark_registry.py validate --benchmark-id {id}`
4. Test execution to verify correctness
5. Submit pull request

See [CONTRIBUTING_BENCHMARKS.md](CONTRIBUTING_BENCHMARKS.md) for detailed guidelines.

## Schema Overview

Each benchmark must include:
- **Identification**: id, name, simulator, version
- **Description**: category, difficulty, tags, detailed description
- **Input Files**: List of required files with checksums
- **Expected Results**: Output files, metrics, performance data
- **Validation**: Criteria for validating results
- **Metadata**: Author, dates, license, references
- **Execution**: Command, parameters, timeout, parallelization

## License

Benchmarks are provided under various open-source licenses (specified in each benchmark's metadata).
