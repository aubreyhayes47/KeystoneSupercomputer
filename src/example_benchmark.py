#!/usr/bin/env python3
"""
Example: Running Benchmarks for CPU vs GPU Performance Comparison

This script demonstrates how to use the benchmark module to compare
simulation performance across different hardware configurations.
"""

import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent))

from benchmark import BenchmarkRunner


def run_simple_benchmark():
    """Run a simple benchmark example."""
    print("\n" + "="*70)
    print("Example 1: Simple CPU Benchmark")
    print("="*70)
    
    # Create benchmark runner
    runner = BenchmarkRunner()
    
    # Run a CPU benchmark for FEniCSx
    result = runner.run_benchmark(
        tool="fenicsx",
        device="cpu",
        runs=3
    )
    
    # Print key metrics
    print(f"\nKey Results:")
    print(f"  Benchmark ID: {result['id']}")
    print(f"  Average Duration: {result['metrics']['avg_duration_seconds']}s")
    print(f"  Success Rate: {result['metrics']['success_rate']}%")
    
    return result


def compare_cpu_vs_gpu():
    """Compare CPU and GPU performance."""
    print("\n" + "="*70)
    print("Example 2: CPU vs GPU Comparison")
    print("="*70)
    
    runner = BenchmarkRunner()
    
    # Run CPU benchmark
    print("\nRunning CPU benchmark...")
    cpu_result = runner.run_benchmark(
        tool="fenicsx",
        device="cpu",
        runs=3
    )
    
    # Run GPU benchmark (if available)
    print("\nRunning GPU benchmark...")
    try:
        gpu_result = runner.run_benchmark(
            tool="fenicsx",
            device="gpu",
            runs=3
        )
        
        # Compare results
        comparison = runner.compare_results(cpu_result['id'], gpu_result['id'])
        
        print(f"\n{'='*70}")
        print("Performance Comparison Summary")
        print(f"{'='*70}")
        print(f"CPU Duration: {cpu_result['metrics']['avg_duration_seconds']}s")
        print(f"GPU Duration: {gpu_result['metrics']['avg_duration_seconds']}s")
        print(f"Speedup: {comparison['speedup']}x")
        print(f"Time Saved: {comparison['time_saved_seconds']}s")
        print(f"{'='*70}")
        
    except Exception as e:
        print(f"\nGPU benchmark failed: {e}")
        print("This is expected if GPU is not available.")
        print("See GPU_ACCELERATION.md for setup instructions.")


def benchmark_all_tools():
    """Benchmark all simulation tools."""
    print("\n" + "="*70)
    print("Example 3: Benchmark All Tools")
    print("="*70)
    
    runner = BenchmarkRunner()
    tools = ['fenicsx', 'lammps', 'openfoam']
    
    results = {}
    for tool in tools:
        print(f"\nBenchmarking {tool}...")
        try:
            result = runner.run_benchmark(
                tool=tool,
                device="cpu",
                runs=3
            )
            results[tool] = result
            print(f"✓ {tool}: {result['metrics']['avg_duration_seconds']}s")
        except Exception as e:
            print(f"✗ {tool} failed: {e}")
    
    # Print summary
    print(f"\n{'='*70}")
    print("Summary of All Benchmarks")
    print(f"{'='*70}")
    for tool, result in results.items():
        metrics = result['metrics']
        print(f"\n{tool.upper()}:")
        print(f"  Duration: {metrics['avg_duration_seconds']}s")
        print(f"  CPU Time: {metrics['avg_cpu_seconds']}s")
        print(f"  Memory: {metrics['avg_memory_mb']} MB")
        print(f"  Success Rate: {metrics['success_rate']}%")
    print(f"{'='*70}")


def custom_parameters():
    """Run benchmark with custom parameters."""
    print("\n" + "="*70)
    print("Example 4: Custom Parameters")
    print("="*70)
    
    runner = BenchmarkRunner()
    
    # Run with different mesh sizes
    mesh_sizes = [32, 64, 128]
    results = []
    
    for size in mesh_sizes:
        print(f"\nBenchmarking with mesh_size={size}...")
        result = runner.run_benchmark(
            tool="fenicsx",
            device="cpu",
            custom_params={"mesh_size": size},
            runs=3
        )
        results.append((size, result['metrics']['avg_duration_seconds']))
    
    # Show scaling
    print(f"\n{'='*70}")
    print("Mesh Size Scaling")
    print(f"{'='*70}")
    for size, duration in results:
        print(f"  mesh_size={size:3d}: {duration:6.3f}s")
    print(f"{'='*70}")


def generate_report_example():
    """Generate a comprehensive report."""
    print("\n" + "="*70)
    print("Example 5: Generate Report")
    print("="*70)
    
    runner = BenchmarkRunner()
    
    # Load existing results
    results = runner.load_results()
    
    if not results:
        print("\nNo benchmark results found.")
        print("Run some benchmarks first, then generate a report.")
        return
    
    # Generate markdown report
    report_file = runner.results_dir / "EXAMPLE_REPORT.md"
    report = runner.generate_report(output_file=str(report_file))
    
    print(f"\n✓ Report generated: {report_file}")
    print("\nReport preview:")
    print("-" * 70)
    print("\n".join(report.split("\n")[:20]))
    print("...")
    print("-" * 70)


def load_and_analyze():
    """Load and analyze previous benchmark results."""
    print("\n" + "="*70)
    print("Example 6: Load and Analyze Results")
    print("="*70)
    
    runner = BenchmarkRunner()
    
    # Load all results
    results = runner.load_results()
    
    if not results:
        print("\nNo benchmark results found.")
        return
    
    print(f"\nLoaded {len(results)} benchmark results")
    
    # Group by tool
    by_tool = {}
    for result in results:
        tool = result['tool']
        if tool not in by_tool:
            by_tool[tool] = []
        by_tool[tool].append(result)
    
    # Analyze each tool
    print(f"\n{'='*70}")
    print("Analysis by Tool")
    print(f"{'='*70}")
    
    for tool, tool_results in by_tool.items():
        print(f"\n{tool.upper()}:")
        print(f"  Total benchmarks: {len(tool_results)}")
        
        # Calculate average metrics
        avg_duration = sum(r['metrics']['avg_duration_seconds'] 
                          for r in tool_results) / len(tool_results)
        avg_memory = sum(r['metrics']['avg_memory_mb'] 
                        for r in tool_results) / len(tool_results)
        
        print(f"  Average duration: {avg_duration:.3f}s")
        print(f"  Average memory: {avg_memory:.2f} MB")
        
        # Show devices tested
        devices = set(r['device'] for r in tool_results)
        print(f"  Devices tested: {', '.join(devices)}")


def main():
    """Run all examples."""
    print("\n" + "="*70)
    print("Keystone Supercomputer - Benchmark Examples")
    print("="*70)
    print("\nThese examples demonstrate the benchmark system capabilities.")
    print("Note: Some examples may fail if Docker services are not running.")
    print("="*70)
    
    examples = [
        ("Simple Benchmark", run_simple_benchmark),
        ("CPU vs GPU Comparison", compare_cpu_vs_gpu),
        ("Benchmark All Tools", benchmark_all_tools),
        ("Custom Parameters", custom_parameters),
        ("Generate Report", generate_report_example),
        ("Load and Analyze", load_and_analyze),
    ]
    
    for name, func in examples:
        try:
            func()
        except KeyboardInterrupt:
            print("\n\nExamples interrupted by user.")
            break
        except Exception as e:
            print(f"\n✗ Example failed: {e}")
            print("This may be expected if Docker services are not running.")
        
        input("\nPress Enter to continue to next example...")
    
    print("\n" + "="*70)
    print("Examples Complete!")
    print("="*70)
    print("\nFor more information:")
    print("  - See BENCHMARK_GUIDE.md for detailed documentation")
    print("  - Run: python3 benchmark.py --help")
    print("  - View results in: /tmp/keystone_benchmarks/")
    print("="*70 + "\n")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nExamples interrupted by user.")
        sys.exit(0)
