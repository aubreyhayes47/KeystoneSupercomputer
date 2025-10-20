# Benchmark Registry for sim-toolbox

## Overview

The Benchmark Registry provides a comprehensive system for managing, validating, and executing reference benchmark cases for all supported simulators in sim-toolbox: **FEniCSx**, **LAMMPS**, and **OpenFOAM**.

The registry serves multiple purposes:
- **Quality Assurance**: Validate simulation tools are working correctly
- **Reproducibility**: Provide standardized test cases with expected results
- **Education**: Offer learning resources for new users
- **Performance Testing**: Compare hardware and software configurations
- **Regression Testing**: Detect when changes break existing functionality

## Directory Structure

```
src/sim-toolbox/benchmarks/
├── benchmark_schema.json          # JSON schema for benchmark definitions
├── benchmark_registry.py          # Registry manager Python module
├── fenicsx/                       # FEniCSx benchmarks
│   ├── poisson-2d-basic.json
│   ├── elasticity-3d.json
│   └── heat-transfer.json
├── lammps/                        # LAMMPS benchmarks
│   ├── lennard-jones-fluid.json
│   └── polymer-melt.json
└── openfoam/                      # OpenFOAM benchmarks
    ├── cavity-flow.json
    └── backward-step.json
```

## Quick Start

### List Available Benchmarks

```bash
cd src/sim-toolbox/benchmarks

# List all benchmarks
python3 benchmark_registry.py list

# Filter by simulator
python3 benchmark_registry.py list --simulator fenicsx

# Filter by difficulty
python3 benchmark_registry.py list --difficulty beginner

# Filter by category
python3 benchmark_registry.py list --category finite-element
```

### View Benchmark Details

```bash
# Get complete benchmark information
python3 benchmark_registry.py info --benchmark-id fenicsx-poisson-2d-basic
```

### Validate Benchmarks

```bash
# Validate a specific benchmark
python3 benchmark_registry.py validate --benchmark-id fenicsx-poisson-2d-basic

# Validate all benchmarks
python3 benchmark_registry.py validate-all
```

### Generate Report

```bash
# Print report to console
python3 benchmark_registry.py report

# Save report to file
python3 benchmark_registry.py report --output BENCHMARK_REPORT.md
```

### Get Statistics

```bash
python3 benchmark_registry.py stats
```

## Python API

### Basic Usage

```python
from benchmark_registry import BenchmarkRegistry

# Initialize registry
registry = BenchmarkRegistry()

# List benchmarks
benchmarks = registry.list_benchmarks(simulator="fenicsx")
for bench in benchmarks:
    print(f"{bench['id']}: {bench['name']}")

# Load benchmark details
benchmark = registry.load_benchmark("fenicsx-poisson-2d-basic")
print(f"Description: {benchmark['description']}")
print(f"Input files: {benchmark['input_files']}")
print(f"Expected results: {benchmark['expected_results']}")

# Validate benchmark
result = registry.validate_benchmark("fenicsx-poisson-2d-basic")
if result['valid']:
    print("✓ Benchmark is valid")
else:
    print("✗ Validation errors:", result['errors'])
```

### Filter Benchmarks

```python
# Filter by multiple criteria
benchmarks = registry.list_benchmarks(
    simulator="lammps",
    category="molecular-dynamics",
    difficulty="beginner"
)

# Filter by tags
benchmarks = registry.list_benchmarks(tags=["poisson", "2d"])
```

### Generate Reports

```python
# Generate statistics
stats = registry.get_statistics()
print(f"Total benchmarks: {stats['total_benchmarks']}")
print(f"By simulator: {stats['by_simulator']}")

# Generate markdown report
report = registry.generate_report(output_file="BENCHMARK_REPORT.md")
print(report)
```

## Benchmark Schema

Each benchmark is defined by a JSON file conforming to the [benchmark_schema.json](src/sim-toolbox/benchmarks/benchmark_schema.json) schema. The schema defines:

### Required Fields

- **id**: Unique identifier (e.g., `fenicsx-poisson-2d-basic`)
- **name**: Human-readable name
- **simulator**: One of `fenicsx`, `lammps`, or `openfoam`
- **version**: Semantic version (e.g., `1.0.0`)
- **description**: Detailed problem description
- **category**: Classification (finite-element, molecular-dynamics, etc.)
- **difficulty**: Complexity level (beginner, intermediate, advanced, expert)
- **input_files**: List of required input files with checksums
- **expected_results**: Output files, metrics, and performance data
- **validation_criteria**: How to validate results
- **metadata**: Author, dates, license, references
- **execution**: Command, parameters, timeout, parallelization

### Example Benchmark Definition

```json
{
  "id": "fenicsx-poisson-2d-basic",
  "name": "2D Poisson Equation - Basic",
  "simulator": "fenicsx",
  "version": "1.0.0",
  "description": "Solves the 2D Poisson equation...",
  "category": "finite-element",
  "difficulty": "beginner",
  "tags": ["poisson", "elliptic-pde", "2d"],
  "input_files": [
    {
      "filename": "poisson.py",
      "description": "FEniCSx Python script",
      "path": "../../fenicsx/poisson.py",
      "checksum": "abc123..."
    }
  ],
  "expected_results": {
    "output_files": [...],
    "metrics": {
      "solution_max": {
        "value": 0.975,
        "tolerance": 0.01,
        "unit": "dimensionless"
      }
    },
    "performance": {
      "typical_runtime_seconds": 5,
      "memory_mb": 256
    }
  },
  "validation_criteria": {
    "method": "tolerance_based",
    "tolerance": 0.01,
    "checks": [...]
  },
  "metadata": {
    "author": "Keystone Supercomputer Team",
    "created_date": "2025-10-20",
    "license": "MIT"
  },
  "execution": {
    "command": "python3 poisson.py",
    "timeout_seconds": 60
  }
}
```

## Available Benchmarks

### FEniCSx (Finite Element Method)

| ID | Name | Category | Difficulty | Description |
|---|---|---|---|
| `fenicsx-poisson-2d-basic` | 2D Poisson Equation | finite-element | beginner | Basic elliptic PDE with Dirichlet BC |

### LAMMPS (Molecular Dynamics)

| ID | Name | Category | Difficulty | Description |
|---|---|---|---|
| `lammps-lennard-jones-fluid` | Lennard-Jones Fluid | molecular-dynamics | beginner | Classical MD with periodic boundaries |

### OpenFOAM (Computational Fluid Dynamics)

| ID | Name | Category | Difficulty | Description |
|---|---|---|---|
| `openfoam-cavity-flow` | Lid-Driven Cavity | computational-fluid-dynamics | beginner | Classic CFD validation case |

## Submitting New Benchmarks

### Process

1. **Prepare Benchmark**: Create test case with input files and expected results
2. **Create Definition**: Write JSON definition following the schema
3. **Validate**: Use `benchmark_registry.py validate` to check compliance
4. **Test Execution**: Run the benchmark to verify it works
5. **Submit**: Create pull request with benchmark files

### Acceptance Criteria

For a benchmark to be accepted into the registry, it must meet these criteria:

#### Technical Requirements
- ✅ Valid JSON conforming to `benchmark_schema.json`
- ✅ Unique benchmark ID following naming convention: `{simulator}-{name}-{variant}`
- ✅ Complete metadata (author, date, license, references)
- ✅ All input files present with correct checksums
- ✅ Expected results documented with tolerances
- ✅ Execution completes successfully within timeout
- ✅ Validation criteria clearly defined and testable

#### Quality Requirements
- ✅ Clear, detailed description of the problem
- ✅ Scientific or engineering relevance
- ✅ Reproducible results
- ✅ Appropriate difficulty classification
- ✅ Reasonable execution time (typically < 5 minutes for beginner benchmarks)
- ✅ Documentation of any assumptions or limitations

#### Documentation Requirements
- ✅ References to literature or standards (if applicable)
- ✅ Description of expected output
- ✅ Explanation of validation criteria
- ✅ Hardware requirements (CPU/GPU, memory)

### Creating a Benchmark Definition

```python
from benchmark_registry import BenchmarkRegistry

registry = BenchmarkRegistry()

# Create benchmark definition
benchmark_def = {
    "id": "fenicsx-elasticity-3d",
    "name": "3D Linear Elasticity",
    "simulator": "fenicsx",
    "version": "1.0.0",
    "description": "3D linear elasticity problem...",
    "category": "structural-analysis",
    "difficulty": "intermediate",
    "tags": ["elasticity", "3d", "structural"],
    "input_files": [...],
    "expected_results": {...},
    "validation_criteria": {...},
    "metadata": {...},
    "execution": {...}
}

# Add to registry (validates automatically)
result = registry.add_benchmark(benchmark_def)
if result['success']:
    print(f"✓ Benchmark added: {result['file_path']}")
else:
    print(f"✗ Errors: {result['errors']}")
```

### Naming Conventions

Benchmark IDs should follow this pattern:
```
{simulator}-{problem-type}-{variant}
```

Examples:
- `fenicsx-poisson-2d-basic`
- `fenicsx-poisson-3d-neumann`
- `lammps-lennard-jones-fluid`
- `lammps-polymer-melt-equilibrium`
- `openfoam-cavity-flow`
- `openfoam-backward-step-turbulent`

## Validation Methods

The registry supports multiple validation methods:

### 1. Exact Match
Files or values must match exactly (rarely used due to floating-point precision).

### 2. Tolerance-Based
Numerical values must be within specified tolerance:
```json
{
  "method": "tolerance_based",
  "tolerance": 0.01,
  "checks": [
    {
      "name": "solution_maximum",
      "type": "metric_value",
      "parameters": {
        "metric": "solution_max",
        "expected": 0.975,
        "tolerance": 0.01
      }
    }
  ]
}
```

### 3. Convergence Check
Validates that iterative solvers converged:
```json
{
  "method": "convergence_check",
  "checks": [
    {
      "name": "solver_converged",
      "type": "convergence",
      "parameters": {
        "log_file": "solver.log",
        "check_pattern": "converged"
      }
    }
  ]
}
```

### 4. Custom Script
User-provided validation script:
```json
{
  "method": "custom_script",
  "validation_script": "validate_results.py",
  "checks": [...]
}
```

## Integration with Existing Systems

The benchmark registry integrates with existing Keystone Supercomputer components:

### With Performance Benchmarking (`benchmark.py`)

```python
from benchmark import BenchmarkRunner
from benchmark_registry import BenchmarkRegistry

# Get reference case from registry
registry = BenchmarkRegistry()
benchmark = registry.load_benchmark("fenicsx-poisson-2d-basic")

# Use with performance benchmarking
runner = BenchmarkRunner()
result = runner.run_benchmark(
    tool=benchmark['simulator'],
    device="cpu",
    runs=3
)
```

### With Job Monitoring

```python
from job_monitor import JobMonitor
from benchmark_registry import BenchmarkRegistry

registry = BenchmarkRegistry()
monitor = JobMonitor()

benchmark = registry.load_benchmark("fenicsx-poisson-2d-basic")

# Run and monitor benchmark execution
# ... execute benchmark ...
# Compare results against expected values
```

### With Provenance Logging

```python
from provenance_logger import get_provenance_logger
from benchmark_registry import BenchmarkRegistry

registry = BenchmarkRegistry()
logger = get_provenance_logger()

benchmark = registry.load_benchmark("fenicsx-poisson-2d-basic")

# Log benchmark execution with full provenance
# ... execute benchmark ...
# Includes benchmark metadata in provenance record
```

## Best Practices

### For Benchmark Authors

1. **Start Simple**: Begin with basic cases before creating complex benchmarks
2. **Document Everything**: Provide clear descriptions and references
3. **Test Thoroughly**: Verify benchmark works on multiple systems
4. **Set Realistic Tolerances**: Account for numerical precision and hardware variations
5. **Include Metadata**: Add author, references, and creation date
6. **Version Control**: Update version when making significant changes

### For Benchmark Users

1. **Check Difficulty**: Start with beginner benchmarks to verify setup
2. **Review Tolerances**: Understand acceptable result variations
3. **Note Hardware**: Compare performance against reference hardware
4. **Validate Results**: Always check validation criteria after execution
5. **Report Issues**: Submit bug reports for failing benchmarks

## Troubleshooting

### Benchmark Fails Validation

```bash
# Check validation details
python3 benchmark_registry.py validate --benchmark-id {benchmark-id}

# Common issues:
# - Missing input files
# - Incorrect file paths
# - Invalid JSON syntax
# - Schema violations
```

### Benchmark Not Found

```bash
# List all available benchmarks
python3 benchmark_registry.py list

# Check if file exists
ls -la src/sim-toolbox/benchmarks/{simulator}/
```

### Results Don't Match Expected Values

1. Check if tolerances are appropriate
2. Verify hardware matches reference specs
3. Ensure simulator versions match
4. Review numerical precision settings
5. Check for non-deterministic behavior (random seeds, etc.)

## Contributing

We welcome contributions of new benchmarks! Please follow these steps:

1. **Discuss**: Open an issue describing the proposed benchmark
2. **Develop**: Create benchmark files following the schema
3. **Test**: Validate locally using `benchmark_registry.py`
4. **Document**: Include clear description and references
5. **Submit**: Create pull request with benchmark files

### Pull Request Checklist

- [ ] Benchmark JSON validates against schema
- [ ] All input files included with checksums
- [ ] Expected results documented
- [ ] Validation criteria defined
- [ ] Metadata complete (author, date, license)
- [ ] Benchmark tested and works correctly
- [ ] Appropriate difficulty level assigned
- [ ] References provided (if applicable)

## License

All benchmarks in this registry are provided under open-source licenses (specified in each benchmark's metadata). Most use MIT or Apache 2.0 licenses.

## References

- **FEniCSx**: https://fenicsproject.org/
- **LAMMPS**: https://www.lammps.org/
- **OpenFOAM**: https://www.openfoam.com/
- **JSON Schema**: https://json-schema.org/
- **Benchmark Standards**: ISO/IEC 14756:1999

## Support

For questions or issues with the benchmark registry:

1. Check this documentation
2. Review existing benchmarks as examples
3. Open an issue on GitHub
4. Contact the Keystone Supercomputer team

---

**Last Updated**: 2025-10-20  
**Version**: 1.0.0
