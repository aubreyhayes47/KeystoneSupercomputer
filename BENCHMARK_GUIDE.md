# Benchmark System Documentation

## Overview

The Keystone Supercomputer benchmark system provides standardized performance testing for simulation tools across different hardware configurations (CPU, GPU, NPU). It enables reproducible performance comparisons and helps users understand the benefits of hardware acceleration.

## Features

- **Standardized Benchmarks**: Pre-configured benchmarks for FEniCSx, LAMMPS, and OpenFOAM
- **Multi-Device Support**: Test on CPU, NVIDIA GPU, and Intel GPU/NPU
- **Performance Metrics**: Track execution time, CPU usage, memory consumption
- **Result Comparison**: Compare performance across different hardware configurations
- **Reproducibility**: Store detailed system information and benchmark parameters
- **Reporting**: Generate markdown reports of benchmark results

## Quick Start

### Running a Single Benchmark

```bash
cd src
python3 benchmark.py --tool fenicsx --device cpu --runs 3
```

### Running Multiple Benchmarks

```bash
# Test all tools on CPU
python3 benchmark.py --tool all --device cpu --runs 3

# Test FEniCSx on all devices
python3 benchmark.py --tool fenicsx --device all --runs 5
```

### Comparing Results

```bash
# Run benchmarks and get their IDs
python3 benchmark.py --tool fenicsx --device cpu --runs 3
# Note the benchmark ID (e.g., fenicsx-cpu-20241015-120000)

python3 benchmark.py --tool fenicsx --device gpu --runs 3
# Note the benchmark ID (e.g., fenicsx-gpu-20241015-120500)

# Compare results
python3 benchmark.py --compare fenicsx-cpu-20241015-120000 fenicsx-gpu-20241015-120500
```

### Generating a Report

```bash
python3 benchmark.py --report
```

## Python API

### Basic Usage

```python
from benchmark import BenchmarkRunner

# Create runner
runner = BenchmarkRunner()

# Run CPU benchmark
cpu_result = runner.run_benchmark("fenicsx", device="cpu", runs=3)
print(f"Average duration: {cpu_result['metrics']['avg_duration_seconds']}s")

# Run GPU benchmark
gpu_result = runner.run_benchmark("fenicsx", device="gpu", runs=3)

# Compare results
comparison = runner.compare_results(cpu_result['id'], gpu_result['id'])
print(f"Speedup: {comparison['speedup']}x")

# Save results
runner.save_results()

# Generate report
report = runner.generate_report(output_file="BENCHMARK_REPORT.md")
```

### Custom Parameters

```python
# Run with custom parameters
result = runner.run_benchmark(
    tool="fenicsx",
    device="cpu",
    custom_params={"mesh_size": 128},  # Override default mesh size
    runs=5
)
```

## Benchmark Configuration

### Available Tools

1. **FEniCSx** - Finite Element Method simulations
   - Script: `poisson.py`
   - Default params: `mesh_size: 64`
   - Description: Poisson equation solver

2. **LAMMPS** - Molecular Dynamics simulations
   - Script: `example.lammps`
   - Default params: None
   - Description: Molecular dynamics simulation

3. **OpenFOAM** - Computational Fluid Dynamics
   - Script: `example_cavity.py`
   - Default params: None
   - Description: Cavity flow CFD simulation

### Device Types

1. **cpu** - CPU-only execution
   - No special hardware requirements
   - Baseline for comparisons

2. **gpu** - NVIDIA GPU acceleration
   - Requires: NVIDIA GPU, drivers, Container Toolkit
   - Uses: `--gpus all` Docker flag

3. **intel-gpu** - Intel GPU/NPU acceleration
   - Requires: Intel GPU/NPU, drivers, device plugin
   - Uses: `/dev/dri` device mounting

## Performance Metrics

Each benchmark records the following metrics:

### Execution Metrics
- **Average Duration**: Mean execution time across all runs
- **Min/Max Duration**: Fastest and slowest run times
- **Standard Deviation**: Variability in execution times

### Resource Metrics
- **CPU Time**: User + system CPU time consumed
- **Memory Usage**: Average and peak memory consumption
- **Success Rate**: Percentage of successful runs

### System Information
- Hostname and OS version
- CPU model and core count
- Total memory
- GPU information (if applicable)

## Result Storage

Benchmarks are stored in `/tmp/keystone_benchmarks/` by default:

```
/tmp/keystone_benchmarks/
├── benchmark_results.jsonl          # Line-delimited JSON log
├── benchmark_results_summary.json   # Summary of all results
├── BENCHMARK_REPORT.md             # Generated markdown report
└── job_logs/                       # Detailed job monitoring logs
    └── jobs_history.jsonl
```

### Result Format

Each benchmark result includes:

```json
{
  "id": "fenicsx-cpu-20241015-120000",
  "timestamp": "2024-10-15T12:00:00",
  "tool": "fenicsx",
  "device": "cpu",
  "script": "poisson.py",
  "description": "Poisson equation solver with 64x64 mesh",
  "params": {"mesh_size": 64},
  "runs": 3,
  "metrics": {
    "successful_runs": 3,
    "failed_runs": 0,
    "success_rate": 100.0,
    "avg_duration_seconds": 10.5,
    "min_duration_seconds": 10.2,
    "max_duration_seconds": 10.8,
    "std_duration_seconds": 0.3,
    "avg_cpu_seconds": 9.2,
    "avg_memory_mb": 512.0,
    "max_memory_mb": 520.0
  },
  "system_info": {
    "hostname": "myhost",
    "os": "Linux 5.15.0",
    "cpu_model": "Intel Core i7",
    "cpu_count": 4,
    "cpu_count_logical": 8,
    "memory_total_gb": 16.0,
    "device": "cpu"
  },
  "run_results": [...]
}
```

## Example Workflow

### Complete CPU vs GPU Comparison

```python
from benchmark import BenchmarkRunner

# Initialize runner
runner = BenchmarkRunner()

# Define tools to test
tools = ['fenicsx', 'lammps', 'openfoam']

# Run benchmarks
results = {}
for tool in tools:
    # CPU baseline
    cpu_result = runner.run_benchmark(tool, device='cpu', runs=5)
    results[f"{tool}_cpu"] = cpu_result
    
    # GPU comparison
    try:
        gpu_result = runner.run_benchmark(tool, device='gpu', runs=5)
        results[f"{tool}_gpu"] = gpu_result
        
        # Compare
        comparison = runner.compare_results(cpu_result['id'], gpu_result['id'])
        print(f"\n{tool.upper()}: {comparison['speedup']}x speedup with GPU")
    except Exception as e:
        print(f"GPU benchmark failed for {tool}: {e}")

# Generate comprehensive report
runner.save_results()
runner.generate_report(output_file="PERFORMANCE_COMPARISON.md")
```

## Reproducibility

### Recording System Configuration

Every benchmark automatically records:
- Exact tool and script versions
- Hardware specifications
- Docker configuration
- Simulation parameters

### Sharing Results

Share benchmark results by copying:
1. The generated report: `BENCHMARK_REPORT.md`
2. Raw data: `benchmark_results_summary.json`
3. Job logs: `job_logs/jobs_history.jsonl`

### Reproducing Benchmarks

To reproduce a benchmark:

```python
# Load previous results
runner = BenchmarkRunner()
results = runner.load_results()

# Find the benchmark
target = [r for r in results if r['id'] == 'fenicsx-cpu-20241015-120000'][0]

# Re-run with same parameters
new_result = runner.run_benchmark(
    tool=target['tool'],
    device=target['device'],
    custom_params=target['params'],
    runs=target['runs']
)

# Compare
comparison = runner.compare_results(target['id'], new_result['id'])
```

## Best Practices

### Number of Runs

- **Quick tests**: 3 runs (default)
- **Standard benchmarks**: 5 runs
- **Publication-quality**: 10+ runs

### Benchmark Timing

- Run benchmarks when system is idle
- Close unnecessary applications
- Disable power-saving modes
- Use consistent system load

### GPU Benchmarks

- Warm up GPU with a test run first
- Monitor GPU temperature
- Ensure adequate cooling
- Check GPU is not throttling

### Interpreting Results

- Look at standard deviation - high variance indicates inconsistent performance
- Compare peak memory usage to available memory
- CPU time vs wall time ratio indicates parallelization efficiency
- Success rate below 100% indicates stability issues

## Troubleshooting

### Benchmark Fails

1. Check Docker is running: `docker ps`
2. Verify images are built: `docker images`
3. Check system resources: `free -h`, `df -h`
4. Review error logs in job monitoring files

### GPU Not Detected

1. Verify GPU drivers: `nvidia-smi` or `clinfo`
2. Check Docker GPU support: `docker run --rm --gpus all nvidia/cuda:12.0.0-base-ubuntu22.04 nvidia-smi`
3. Review GPU_ACCELERATION.md for setup

### Inconsistent Results

1. Increase number of runs
2. Check for background processes
3. Monitor thermal throttling
4. Ensure consistent power profile

## Advanced Usage

### Custom Benchmarks

```python
# Add custom benchmark configuration
from benchmark import BenchmarkConfig

BenchmarkConfig.BENCHMARKS['custom_tool'] = {
    'script': 'my_script.py',
    'params': {'param1': 'value1'},
    'description': 'My custom benchmark',
}

# Run custom benchmark
runner = BenchmarkRunner()
result = runner.run_benchmark('custom_tool', device='cpu')
```

### Statistical Analysis

```python
import statistics

# Load results
runner = BenchmarkRunner()
results = runner.load_results()

# Analyze duration across runs
for result in results:
    durations = [r['duration_seconds'] for r in result['run_results'] 
                 if r['status'] == 'success']
    
    print(f"\n{result['id']}:")
    print(f"  Mean: {statistics.mean(durations):.3f}s")
    print(f"  Median: {statistics.median(durations):.3f}s")
    print(f"  Stdev: {statistics.stdev(durations):.3f}s")
```

## Integration with CI/CD

### GitHub Actions Example

```yaml
name: Benchmark Tests

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  benchmark:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run benchmarks
        run: |
          cd src
          python3 benchmark.py --tool all --device cpu --runs 3
      - name: Generate report
        run: python3 benchmark.py --report
      - name: Upload results
        uses: actions/upload-artifact@v2
        with:
          name: benchmark-results
          path: /tmp/keystone_benchmarks/
```

## References

- [Job Monitoring Documentation](JOB_MONITORING.md)
- [GPU Acceleration Guide](GPU_ACCELERATION.md)
- [Task Pipeline Documentation](TASK_PIPELINE.md)
- [Orchestration Guide](ORCHESTRATION_GUIDE.md)

## Contributing

To add new benchmarks or improve the system:

1. Add benchmark configuration to `BenchmarkConfig.BENCHMARKS`
2. Ensure simulation tool has standardized interface
3. Add tests for new benchmarks
4. Update documentation
5. Submit pull request

---

Last updated: 2024-10-15
