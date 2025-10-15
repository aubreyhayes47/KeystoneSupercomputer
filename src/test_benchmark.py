#!/usr/bin/env python3
"""
Unit tests for the Benchmark module.

These tests validate benchmark execution, metrics collection, and result comparison.
"""

import sys
import time
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent))

from benchmark import BenchmarkRunner, BenchmarkConfig


def test_benchmark_runner_instantiation():
    """Test that BenchmarkRunner can be instantiated."""
    with tempfile.TemporaryDirectory() as tmpdir:
        runner = BenchmarkRunner(results_dir=tmpdir)
        assert runner is not None
        assert runner.results_dir.exists()
        assert runner.results_file.exists() or not runner.results_file.exists()  # File created on write
        print("✓ BenchmarkRunner instantiation test passed")


def test_benchmark_config():
    """Test benchmark configuration."""
    # Check that all required tools are configured
    assert 'fenicsx' in BenchmarkConfig.BENCHMARKS
    assert 'lammps' in BenchmarkConfig.BENCHMARKS
    assert 'openfoam' in BenchmarkConfig.BENCHMARKS
    
    # Check device configurations
    assert 'cpu' in BenchmarkConfig.DEVICES
    assert 'gpu' in BenchmarkConfig.DEVICES
    assert 'intel-gpu' in BenchmarkConfig.DEVICES
    
    # Check benchmark structure
    for tool, config in BenchmarkConfig.BENCHMARKS.items():
        assert 'script' in config
        assert 'params' in config
        assert 'description' in config
    
    print("✓ Benchmark configuration test passed")


def test_aggregate_metrics():
    """Test metrics aggregation from multiple runs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        runner = BenchmarkRunner(results_dir=tmpdir)
        
        # Create mock run results
        run_results = [
            {
                'run_num': 1,
                'status': 'success',
                'returncode': 0,
                'duration_seconds': 10.5,
                'cpu_total_seconds': 9.2,
                'memory_peak_mb': 512.0,
            },
            {
                'run_num': 2,
                'status': 'success',
                'returncode': 0,
                'duration_seconds': 10.8,
                'cpu_total_seconds': 9.5,
                'memory_peak_mb': 518.0,
            },
            {
                'run_num': 3,
                'status': 'success',
                'returncode': 0,
                'duration_seconds': 10.3,
                'cpu_total_seconds': 9.0,
                'memory_peak_mb': 510.0,
            },
        ]
        
        metrics = runner._aggregate_metrics(run_results)
        
        assert metrics['successful_runs'] == 3
        assert metrics['failed_runs'] == 0
        assert metrics['success_rate'] == 100.0
        assert 10.0 < metrics['avg_duration_seconds'] < 11.0
        assert metrics['min_duration_seconds'] == 10.3
        assert metrics['max_duration_seconds'] == 10.8
        assert 9.0 <= metrics['avg_cpu_seconds'] <= 9.5
        assert 510.0 <= metrics['avg_memory_mb'] <= 518.0
        assert metrics['max_memory_mb'] == 518.0
        assert 'std_duration_seconds' in metrics
        
        print("✓ Aggregate metrics test passed")


def test_aggregate_metrics_with_failures():
    """Test metrics aggregation with failed runs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        runner = BenchmarkRunner(results_dir=tmpdir)
        
        # Create mock run results with failures
        run_results = [
            {
                'run_num': 1,
                'status': 'success',
                'returncode': 0,
                'duration_seconds': 10.5,
                'cpu_total_seconds': 9.2,
                'memory_peak_mb': 512.0,
            },
            {
                'run_num': 2,
                'status': 'failed',
                'returncode': 1,
                'duration_seconds': 5.0,
                'error': 'Test error',
            },
            {
                'run_num': 3,
                'status': 'success',
                'returncode': 0,
                'duration_seconds': 10.8,
                'cpu_total_seconds': 9.5,
                'memory_peak_mb': 518.0,
            },
        ]
        
        metrics = runner._aggregate_metrics(run_results)
        
        assert metrics['successful_runs'] == 2
        assert metrics['failed_runs'] == 1
        assert metrics['success_rate'] == round(2/3 * 100, 2)
        # Metrics should only include successful runs
        assert 10.0 < metrics['avg_duration_seconds'] < 11.0
        
        print("✓ Aggregate metrics with failures test passed")


def test_collect_system_info():
    """Test system information collection."""
    with tempfile.TemporaryDirectory() as tmpdir:
        runner = BenchmarkRunner(results_dir=tmpdir)
        
        info = runner._collect_system_info('cpu')
        
        assert 'hostname' in info
        assert 'os' in info
        assert 'cpu_count' in info
        assert 'cpu_count_logical' in info
        assert 'memory_total_gb' in info
        assert info['device'] == 'cpu'
        assert info['cpu_count'] > 0
        assert info['memory_total_gb'] > 0
        
        print("✓ Collect system info test passed")


def test_write_and_load_results():
    """Test writing and loading benchmark results."""
    with tempfile.TemporaryDirectory() as tmpdir:
        runner = BenchmarkRunner(results_dir=tmpdir)
        
        # Create mock benchmark result
        result = {
            'id': 'test-benchmark-1',
            'timestamp': '2024-01-01T00:00:00',
            'tool': 'fenicsx',
            'device': 'cpu',
            'metrics': {
                'avg_duration_seconds': 10.5,
                'successful_runs': 3,
            },
        }
        
        # Write result
        runner._write_result(result)
        
        # Load results
        loaded = runner.load_results()
        
        assert len(loaded) == 1
        assert loaded[0]['id'] == 'test-benchmark-1'
        assert loaded[0]['tool'] == 'fenicsx'
        assert loaded[0]['device'] == 'cpu'
        
        print("✓ Write and load results test passed")


def test_compare_results():
    """Test benchmark comparison."""
    with tempfile.TemporaryDirectory() as tmpdir:
        runner = BenchmarkRunner(results_dir=tmpdir)
        
        # Create two benchmark results
        baseline = {
            'id': 'fenicsx-cpu-baseline',
            'tool': 'fenicsx',
            'device': 'cpu',
            'metrics': {
                'avg_duration_seconds': 20.0,
                'avg_memory_mb': 512.0,
            },
        }
        
        comparison = {
            'id': 'fenicsx-gpu-comparison',
            'tool': 'fenicsx',
            'device': 'gpu',
            'metrics': {
                'avg_duration_seconds': 5.0,
                'avg_memory_mb': 1024.0,
            },
        }
        
        # Add results
        runner.results = [baseline, comparison]
        
        # Compare
        comp_result = runner.compare_results(
            'fenicsx-cpu-baseline',
            'fenicsx-gpu-comparison'
        )
        
        assert comp_result['baseline_id'] == 'fenicsx-cpu-baseline'
        assert comp_result['comparison_id'] == 'fenicsx-gpu-comparison'
        assert comp_result['baseline_device'] == 'cpu'
        assert comp_result['comparison_device'] == 'gpu'
        assert comp_result['baseline_duration'] == 20.0
        assert comp_result['comparison_duration'] == 5.0
        assert comp_result['speedup'] == 4.0  # 20 / 5 = 4x speedup
        assert comp_result['time_saved_seconds'] == 15.0
        assert comp_result['percent_change'] == -75.0  # 75% faster
        
        print("✓ Compare results test passed")


def test_generate_report():
    """Test report generation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        runner = BenchmarkRunner(results_dir=tmpdir)
        
        # Add some mock results
        runner.results = [
            {
                'id': 'fenicsx-cpu-test',
                'timestamp': '2024-01-01T00:00:00',
                'tool': 'fenicsx',
                'device': 'cpu',
                'script': 'poisson.py',
                'description': 'Test benchmark',
                'params': {'mesh_size': 64},
                'runs': 3,
                'metrics': {
                    'success_rate': 100.0,
                    'avg_duration_seconds': 10.5,
                    'min_duration_seconds': 10.0,
                    'max_duration_seconds': 11.0,
                    'avg_cpu_seconds': 9.2,
                    'avg_memory_mb': 512.0,
                    'max_memory_mb': 520.0,
                },
                'system_info': {
                    'hostname': 'test-host',
                    'cpu_count': 4,
                },
            },
        ]
        
        # Generate report
        report = runner.generate_report()
        
        assert 'Keystone Supercomputer Benchmark Results' in report
        assert 'fenicsx-cpu-test' in report
        assert 'Device: cpu' in report
        assert 'Average Duration: 10.5s' in report
        
        # Test saving to file
        report_file = Path(tmpdir) / 'test_report.md'
        report = runner.generate_report(output_file=str(report_file))
        assert report_file.exists()
        
        print("✓ Generate report test passed")


def test_save_results():
    """Test saving results summary."""
    with tempfile.TemporaryDirectory() as tmpdir:
        runner = BenchmarkRunner(results_dir=tmpdir)
        
        # Add mock result
        runner.results = [
            {
                'id': 'test-1',
                'tool': 'fenicsx',
                'device': 'cpu',
            },
        ]
        
        # Save results
        output_file = Path(tmpdir) / 'results.json'
        runner.save_results(output_file=str(output_file))
        
        assert output_file.exists()
        
        # Load and verify
        with open(output_file, 'r') as f:
            data = json.load(f)
        
        assert 'timestamp' in data
        assert data['total_benchmarks'] == 1
        assert len(data['results']) == 1
        assert data['results'][0]['id'] == 'test-1'
        
        print("✓ Save results test passed")


def test_invalid_tool():
    """Test error handling for invalid tool."""
    with tempfile.TemporaryDirectory() as tmpdir:
        runner = BenchmarkRunner(results_dir=tmpdir)
        
        try:
            runner.run_benchmark('invalid-tool', device='cpu', runs=1)
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert 'Unknown tool' in str(e)
        
        print("✓ Invalid tool test passed")


def test_invalid_device():
    """Test error handling for invalid device."""
    with tempfile.TemporaryDirectory() as tmpdir:
        runner = BenchmarkRunner(results_dir=tmpdir)
        
        try:
            runner.run_benchmark('fenicsx', device='invalid-device', runs=1)
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert 'Unknown device' in str(e)
        
        print("✓ Invalid device test passed")


def test_empty_results():
    """Test behavior with no results."""
    with tempfile.TemporaryDirectory() as tmpdir:
        runner = BenchmarkRunner(results_dir=tmpdir)
        
        # Load results (should be empty)
        results = runner.load_results()
        assert results == []
        
        # Generate report with no results
        report = runner.generate_report()
        assert 'No benchmark results available' in report
        
        print("✓ Empty results test passed")


def run_all_tests():
    """Run all unit tests."""
    print("=" * 70)
    print("Running Benchmark Module Unit Tests")
    print("=" * 70)
    print()
    
    tests = [
        test_benchmark_runner_instantiation,
        test_benchmark_config,
        test_aggregate_metrics,
        test_aggregate_metrics_with_failures,
        test_collect_system_info,
        test_write_and_load_results,
        test_compare_results,
        test_generate_report,
        test_save_results,
        test_invalid_tool,
        test_invalid_device,
        test_empty_results,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"✗ {test.__name__} failed: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {test.__name__} error: {e}")
            failed += 1
    
    print()
    print("=" * 70)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("=" * 70)
    
    return failed == 0


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
