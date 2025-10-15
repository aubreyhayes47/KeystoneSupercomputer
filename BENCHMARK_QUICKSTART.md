# Quick Start: Performance Benchmarking

This guide helps you quickly run benchmarks to compare CPU vs GPU/NPU performance.

## Prerequisites

1. **Docker Services Running**
   ```bash
   # Start Redis and Celery worker
   cd /path/to/KeystoneSupercomputer
   docker compose up -d redis celery-worker
   ```

2. **Python Dependencies Installed**
   ```bash
   pip install -r requirements.txt
   ```

3. **Simulation Images Built**
   ```bash
   docker compose build fenicsx lammps openfoam
   ```

## Quick Benchmark Run

### Option 1: Using Python API

```python
from benchmark import BenchmarkRunner

# Create runner
runner = BenchmarkRunner()

# Run CPU benchmark
print("Running CPU benchmark...")
cpu_result = runner.run_benchmark("fenicsx", device="cpu", runs=3)
print(f"CPU: {cpu_result['metrics']['avg_duration_seconds']}s")

# Run GPU benchmark (if available)
print("\nRunning GPU benchmark...")
try:
    gpu_result = runner.run_benchmark("fenicsx", device="gpu", runs=3)
    print(f"GPU: {gpu_result['metrics']['avg_duration_seconds']}s")
    
    # Compare
    comparison = runner.compare_results(cpu_result['id'], gpu_result['id'])
    print(f"\nSpeedup: {comparison['speedup']}x")
except Exception as e:
    print(f"GPU benchmark failed: {e}")

# Save results
runner.save_results()
```

### Option 2: Using CLI

```bash
cd src/agent

# Run CPU benchmark
python3 cli.py benchmark run --tool fenicsx --device cpu --runs 3

# Note the benchmark ID from output

# Run GPU benchmark
python3 cli.py benchmark run --tool fenicsx --device gpu --runs 3

# Compare results (replace IDs with actual IDs from output)
python3 cli.py benchmark compare fenicsx-cpu-XXXXXX fenicsx-gpu-XXXXXX

# Generate report
python3 cli.py benchmark report
```

### Option 3: Using Standalone Script

```bash
cd src

# Run all tools on CPU
python3 benchmark.py --tool all --device cpu --runs 3

# Generate report
python3 benchmark.py --report
```

## Expected Results

With GPU acceleration, you should see:
- **FEniCSx**: 3-4x speedup
- **LAMMPS**: 4-5x speedup  
- **OpenFOAM**: 3-4x speedup

Results will be saved to `/tmp/keystone_benchmarks/` including:
- `benchmark_results.jsonl` - Line-delimited JSON log
- `benchmark_results_summary.json` - Summary file
- `BENCHMARK_REPORT.md` - Markdown report

## Troubleshooting

### Docker Services Not Running

```bash
# Check services
docker compose ps

# Start services if needed
docker compose up -d redis celery-worker
```

### GPU Not Available

If GPU benchmarks fail:
1. Check GPU is detected: `nvidia-smi` or `clinfo`
2. Verify Docker GPU support (see `GPU_ACCELERATION.md`)
3. Run CPU-only benchmarks: `--device cpu`

### Benchmark Times Out

Increase timeout in code:
```python
# In benchmark.py, _run_single_benchmark method
timeout=1200  # 20 minutes instead of 10
```

## Next Steps

1. **View Results**: Check `/tmp/keystone_benchmarks/BENCHMARK_REPORT.md`
2. **Run More Tools**: Try LAMMPS and OpenFOAM benchmarks
3. **Custom Parameters**: Test with different simulation parameters
4. **Share Results**: Results are reproducible - share JSON files

## Full Documentation

- [BENCHMARK_GUIDE.md](BENCHMARK_GUIDE.md) - Complete documentation
- [CLI_REFERENCE.md](CLI_REFERENCE.md) - CLI command reference
- [GPU_ACCELERATION.md](GPU_ACCELERATION.md) - GPU setup guide

---

**Ready to benchmark!** Start with CPU-only tests, then add GPU once confirmed working.
