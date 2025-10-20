# Benchmark Registry Integration Examples

This document shows how to integrate the Benchmark Registry with other Keystone Supercomputer components.

## Integration with Performance Benchmarking

The Benchmark Registry provides reference test cases that can be used with the performance benchmarking system (`src/benchmark.py`).

### Example: Run Performance Tests on Registry Benchmarks

```python
#!/usr/bin/env python3
"""
Example: Using Benchmark Registry with Performance Benchmarking
"""

import sys
from pathlib import Path

# Add paths for imports
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from benchmark_registry import BenchmarkRegistry
from benchmark import BenchmarkRunner

def run_performance_benchmarks():
    """Run performance benchmarks on all registry test cases."""
    
    # Initialize both systems
    registry = BenchmarkRegistry()
    runner = BenchmarkRunner()
    
    # Get all beginner benchmarks
    benchmarks = registry.list_benchmarks(difficulty='beginner')
    
    print(f"Running performance benchmarks on {len(benchmarks)} test cases...\n")
    
    results = []
    for bench in benchmarks:
        print(f"Testing: {bench['name']}")
        
        # Load full benchmark definition
        benchmark_def = registry.load_benchmark(bench['id'])
        
        # Extract execution parameters
        simulator = benchmark_def['simulator']
        
        # Run performance benchmark
        try:
            result = runner.run_benchmark(
                tool=simulator,
                device='cpu',
                runs=3
            )
            
            results.append({
                'benchmark_id': bench['id'],
                'name': bench['name'],
                'simulator': simulator,
                'performance': result['metrics']
            })
            
            print(f"  ✓ Completed in {result['metrics']['avg_duration_seconds']:.2f}s\n")
        except Exception as e:
            print(f"  ✗ Error: {e}\n")
    
    # Summary
    print("\nPerformance Summary:")
    print("=" * 70)
    for r in results:
        print(f"{r['name']} ({r['simulator']})")
        print(f"  Average Time: {r['performance']['avg_duration_seconds']:.2f}s")
        print(f"  Memory: {r['performance']['avg_memory_peak_mb']:.1f} MB")
        print()

if __name__ == "__main__":
    run_performance_benchmarks()
```

## Integration with Provenance Logging

Benchmark executions can be tracked with full provenance for reproducibility.

### Example: Run Benchmark with Provenance Tracking

```python
#!/usr/bin/env python3
"""
Example: Benchmark Registry with Provenance Logging
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from benchmark_registry import BenchmarkRegistry
from provenance_logger import get_provenance_logger

def run_benchmark_with_provenance(benchmark_id):
    """Run a benchmark and log complete provenance."""
    
    # Initialize systems
    registry = BenchmarkRegistry()
    logger = get_provenance_logger()
    
    # Start provenance logging
    workflow_id = logger.start_workflow(
        user_prompt=f"Execute benchmark: {benchmark_id}"
    )
    
    # Load benchmark
    benchmark = registry.load_benchmark(benchmark_id)
    
    # Log benchmark metadata
    logger.log_event(
        workflow_id=workflow_id,
        event_type="benchmark_loaded",
        details={
            'benchmark_id': benchmark['id'],
            'benchmark_name': benchmark['name'],
            'simulator': benchmark['simulator'],
            'version': benchmark['version'],
            'input_files': benchmark['input_files'],
            'expected_results': benchmark['expected_results']
        }
    )
    
    # Execute benchmark (pseudo-code - actual execution depends on setup)
    # result = execute_benchmark(benchmark)
    
    # Log completion
    logger.end_workflow(workflow_id, status="completed")
    
    # Retrieve provenance
    provenance = logger.get_provenance(workflow_id)
    
    print(f"Benchmark executed with full provenance tracking")
    print(f"Provenance file: {provenance['_provenance_file']}")
    
    return provenance

if __name__ == "__main__":
    run_benchmark_with_provenance("fenicsx-poisson-2d-basic")
```

## Integration with Job Monitoring

Track benchmark execution metrics using the job monitoring system.

### Example: Monitor Benchmark Execution

```python
#!/usr/bin/env python3
"""
Example: Benchmark Registry with Job Monitoring
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from benchmark_registry import BenchmarkRegistry
from job_monitor import JobMonitor

def validate_benchmark_results(benchmark_id):
    """
    Validate actual results against expected results from registry.
    """
    
    # Initialize systems
    registry = BenchmarkRegistry()
    monitor = JobMonitor()
    
    # Load benchmark definition
    benchmark = registry.load_benchmark(benchmark_id)
    
    # Get expected results
    expected_metrics = benchmark['expected_results']['metrics']
    expected_performance = benchmark['expected_results']['performance']
    
    print(f"Validating: {benchmark['name']}")
    print("=" * 70)
    
    # Get job history for this benchmark
    # (In practice, you'd filter by task ID or other identifier)
    jobs = monitor.get_job_history(limit=10)
    
    # Example validation
    print("\nExpected Metrics:")
    for metric_name, metric_data in expected_metrics.items():
        print(f"  {metric_name}: {metric_data['value']} ± {metric_data['tolerance']} {metric_data['unit']}")
    
    print("\nExpected Performance:")
    print(f"  Runtime: ~{expected_performance['typical_runtime_seconds']}s")
    print(f"  Memory: ~{expected_performance['memory_mb']} MB")
    print(f"  Hardware: {expected_performance['reference_hardware']}")
    
    return True

if __name__ == "__main__":
    validate_benchmark_results("fenicsx-poisson-2d-basic")
```

## Integration with Task Pipeline

Use benchmarks as validation tests in automated workflows.

### Example: Automated Benchmark Validation

```python
#!/usr/bin/env python3
"""
Example: Run All Registry Benchmarks via Task Pipeline
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / 'agent'))

from benchmark_registry import BenchmarkRegistry
# from task_pipeline import TaskPipeline  # Commented as it requires Docker

def run_all_benchmarks():
    """
    Submit all registry benchmarks to the task pipeline for execution.
    """
    
    registry = BenchmarkRegistry()
    # pipeline = TaskPipeline()
    
    # Get all benchmarks
    benchmarks = registry.list_benchmarks()
    
    print(f"Submitting {len(benchmarks)} benchmarks for execution...\n")
    
    task_ids = []
    for bench in benchmarks:
        benchmark_def = registry.load_benchmark(bench['id'])
        
        # Extract execution parameters
        simulator = benchmark_def['simulator']
        command = benchmark_def['execution']['command']
        
        print(f"Submitting: {bench['name']}")
        print(f"  Simulator: {simulator}")
        print(f"  Command: {command}")
        
        # Submit to task pipeline (pseudo-code)
        # task_id = pipeline.submit_task(
        #     tool=simulator,
        #     script=command.split()[-1],  # Extract script name
        #     params=benchmark_def['execution'].get('parameters', {})
        # )
        # task_ids.append(task_id)
        
        print(f"  ✓ Submitted\n")
    
    print(f"Total benchmarks submitted: {len(task_ids)}")
    
    return task_ids

if __name__ == "__main__":
    run_all_benchmarks()
```

## Validation Workflow

Complete workflow for validating simulation results against benchmark expectations.

### Example: Complete Validation Pipeline

```python
#!/usr/bin/env python3
"""
Example: Complete Benchmark Validation Pipeline
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from benchmark_registry import BenchmarkRegistry

def validate_simulation_results(benchmark_id, actual_results):
    """
    Validate actual simulation results against benchmark expectations.
    
    Args:
        benchmark_id: ID of the benchmark to validate against
        actual_results: Dictionary with actual simulation results
        
    Returns:
        Dictionary with validation results
    """
    
    registry = BenchmarkRegistry()
    benchmark = registry.load_benchmark(benchmark_id)
    
    validation_result = {
        'benchmark_id': benchmark_id,
        'passed': True,
        'checks': []
    }
    
    # Get validation criteria
    criteria = benchmark['validation_criteria']
    expected_metrics = benchmark['expected_results']['metrics']
    
    print(f"Validating: {benchmark['name']}")
    print("=" * 70)
    
    # Perform validation checks
    for check in criteria['checks']:
        check_result = {
            'name': check['name'],
            'type': check['type'],
            'passed': False,
            'details': {}
        }
        
        if check['type'] == 'metric_value':
            # Validate metric values
            metric_name = check['parameters']['metric']
            expected_value = check['parameters']['expected']
            tolerance = check['parameters']['tolerance']
            
            if metric_name in actual_results:
                actual_value = actual_results[metric_name]
                diff = abs(actual_value - expected_value)
                
                check_result['passed'] = diff <= tolerance
                check_result['details'] = {
                    'expected': expected_value,
                    'actual': actual_value,
                    'difference': diff,
                    'tolerance': tolerance
                }
                
                status = "✓" if check_result['passed'] else "✗"
                print(f"{status} {check['name']}: {actual_value} "
                      f"(expected {expected_value} ± {tolerance})")
            else:
                print(f"✗ {check['name']}: metric not found in results")
        
        elif check['type'] == 'file_exists':
            # Check if output file exists
            filename = check['parameters']['filename']
            file_exists = Path(filename).exists()
            
            check_result['passed'] = file_exists
            check_result['details'] = {'filename': filename, 'exists': file_exists}
            
            status = "✓" if file_exists else "✗"
            print(f"{status} {check['name']}: {filename}")
        
        validation_result['checks'].append(check_result)
        
        if not check_result['passed']:
            validation_result['passed'] = False
    
    print("\n" + "=" * 70)
    if validation_result['passed']:
        print("✓ All validation checks passed!")
    else:
        print("✗ Some validation checks failed")
    
    return validation_result

if __name__ == "__main__":
    # Example usage
    actual_results = {
        'solution_max': 0.973,
        'solution_min': 0.001,
        'solution_mean': 0.043
    }
    
    result = validate_simulation_results(
        'fenicsx-poisson-2d-basic',
        actual_results
    )
    
    print(f"\nFinal result: {'PASS' if result['passed'] else 'FAIL'}")
```

## CI/CD Integration

Use benchmark validation in continuous integration pipelines.

### Example: GitHub Actions Workflow

```yaml
# .github/workflows/benchmark-validation.yml
name: Benchmark Validation

on: [push, pull_request]

jobs:
  validate-benchmarks:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.10'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
    
    - name: Validate benchmark definitions
      run: |
        cd src/sim-toolbox/benchmarks
        python3 benchmark_registry.py validate-all
    
    - name: Run benchmark tests
      run: |
        cd src/sim-toolbox/benchmarks
        python3 test_benchmark_registry.py
    
    - name: Generate benchmark report
      run: |
        cd src/sim-toolbox/benchmarks
        python3 benchmark_registry.py report --output $GITHUB_WORKSPACE/BENCHMARK_REPORT.md
    
    - name: Upload report
      uses: actions/upload-artifact@v2
      with:
        name: benchmark-report
        path: BENCHMARK_REPORT.md
```

## Summary

The Benchmark Registry integrates seamlessly with:

1. **Performance Benchmarking**: Use registry cases for performance testing
2. **Provenance Logging**: Track benchmark execution with full provenance
3. **Job Monitoring**: Monitor and validate benchmark results
4. **Task Pipeline**: Automate benchmark execution in workflows
5. **CI/CD**: Validate benchmarks in continuous integration

These integrations enable:
- Automated quality assurance
- Reproducible performance testing
- Continuous validation
- Complete audit trails
- Standardized testing across environments
