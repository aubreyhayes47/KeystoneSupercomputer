#!/usr/bin/env python3
"""
Example Usage of Benchmark Registry
====================================

This script demonstrates how to use the Benchmark Registry to:
- List available benchmarks
- Load benchmark definitions
- Filter benchmarks by criteria
- Validate benchmarks
- Generate reports

Run this script to see the benchmark registry in action.
"""

from benchmark_registry import BenchmarkRegistry


def main():
    print("="*70)
    print("Benchmark Registry - Example Usage")
    print("="*70)
    print()
    
    # Initialize the registry
    registry = BenchmarkRegistry()
    
    # Example 1: List all benchmarks
    print("Example 1: List All Benchmarks")
    print("-" * 70)
    all_benchmarks = registry.list_benchmarks()
    print(f"Found {len(all_benchmarks)} benchmark(s):\n")
    for bench in all_benchmarks:
        print(f"  • {bench['id']}")
        print(f"    Name: {bench['name']}")
        print(f"    Simulator: {bench['simulator']} | Difficulty: {bench['difficulty']}")
        print()
    
    # Example 2: Filter benchmarks by simulator
    print("\nExample 2: Filter by Simulator (FEniCSx)")
    print("-" * 70)
    fenicsx_benchmarks = registry.list_benchmarks(simulator='fenicsx')
    for bench in fenicsx_benchmarks:
        print(f"  • {bench['id']}: {bench['name']}")
    
    # Example 3: Filter by difficulty
    print("\nExample 3: Filter by Difficulty (Beginner)")
    print("-" * 70)
    beginner_benchmarks = registry.list_benchmarks(difficulty='beginner')
    print(f"Found {len(beginner_benchmarks)} beginner benchmark(s)")
    
    # Example 4: Load detailed benchmark information
    print("\nExample 4: Load Detailed Benchmark Information")
    print("-" * 70)
    benchmark = registry.load_benchmark('fenicsx-poisson-2d-basic')
    print(f"ID: {benchmark['id']}")
    print(f"Name: {benchmark['name']}")
    print(f"Description: {benchmark['description'][:100]}...")
    print(f"Input Files: {len(benchmark['input_files'])}")
    print(f"Expected Metrics:")
    for metric_name, metric_data in benchmark['expected_results']['metrics'].items():
        print(f"  - {metric_name}: {metric_data['value']} ± {metric_data['tolerance']} {metric_data['unit']}")
    
    # Example 5: Validate a benchmark
    print("\nExample 5: Validate a Benchmark")
    print("-" * 70)
    validation = registry.validate_benchmark('fenicsx-poisson-2d-basic')
    print(f"Benchmark: {validation['benchmark_id']}")
    print(f"Valid: {'✓' if validation['valid'] else '✗'}")
    if validation['errors']:
        print("Errors:")
        for error in validation['errors']:
            print(f"  - {error}")
    if validation['warnings']:
        print("Warnings:")
        for warning in validation['warnings']:
            print(f"  - {warning}")
    
    # Example 6: Validate all benchmarks
    print("\nExample 6: Validate All Benchmarks")
    print("-" * 70)
    all_validation = registry.validate_all_benchmarks()
    print(f"Total: {all_validation['total']}")
    print(f"Valid: {all_validation['valid']} ✓")
    print(f"Invalid: {all_validation['invalid']}")
    
    # Example 7: Get statistics
    print("\nExample 7: Registry Statistics")
    print("-" * 70)
    stats = registry.get_statistics()
    print(f"Total Benchmarks: {stats['total_benchmarks']}")
    print("\nBy Simulator:")
    for sim, count in sorted(stats['by_simulator'].items()):
        print(f"  {sim}: {count}")
    print("\nBy Category:")
    for cat, count in sorted(stats['by_category'].items()):
        print(f"  {cat}: {count}")
    print("\nBy Difficulty:")
    for diff, count in sorted(stats['by_difficulty'].items()):
        print(f"  {diff}: {count}")
    
    # Example 8: Generate markdown report
    print("\nExample 8: Generate Markdown Report")
    print("-" * 70)
    report = registry.generate_report()
    print(f"Report generated ({len(report)} characters)")
    print("\nFirst 300 characters of report:")
    print(report[:300] + "...")
    
    # Example 9: Search by category
    print("\nExample 9: Filter by Category")
    print("-" * 70)
    fem_benchmarks = registry.list_benchmarks(category='finite-element')
    md_benchmarks = registry.list_benchmarks(category='molecular-dynamics')
    cfd_benchmarks = registry.list_benchmarks(category='computational-fluid-dynamics')
    
    print(f"Finite Element: {len(fem_benchmarks)}")
    print(f"Molecular Dynamics: {len(md_benchmarks)}")
    print(f"Computational Fluid Dynamics: {len(cfd_benchmarks)}")
    
    # Example 10: Filter by multiple criteria
    print("\nExample 10: Filter by Multiple Criteria")
    print("-" * 70)
    filtered = registry.list_benchmarks(
        simulator='fenicsx',
        difficulty='beginner'
    )
    print(f"FEniCSx beginner benchmarks: {len(filtered)}")
    for bench in filtered:
        print(f"  • {bench['id']}")
    
    print("\n" + "="*70)
    print("Examples Complete!")
    print("="*70)
    print("\nFor more information:")
    print("  - Run: python3 benchmark_registry.py --help")
    print("  - Read: ../../../BENCHMARK_REGISTRY.md")
    print("  - See: CONTRIBUTING_BENCHMARKS.md for adding new benchmarks")
    print()


if __name__ == "__main__":
    main()
