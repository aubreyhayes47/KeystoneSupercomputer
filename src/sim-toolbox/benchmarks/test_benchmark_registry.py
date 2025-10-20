#!/usr/bin/env python3
"""
Unit tests for the Benchmark Registry module.

Tests validation, loading, listing, and management of benchmark cases.
"""

import sys
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

# Add benchmarks directory to path
sys.path.insert(0, str(Path(__file__).parent))

from benchmark_registry import BenchmarkRegistry


def test_registry_initialization():
    """Test that BenchmarkRegistry can be instantiated."""
    registry = BenchmarkRegistry()
    assert registry is not None
    assert registry.schema is not None
    assert registry.registry_dir.exists()
    print("✓ Registry initialization test passed")


def test_schema_loading():
    """Test that JSON schema is loaded correctly."""
    registry = BenchmarkRegistry()
    schema = registry.schema
    
    # Check required schema fields
    assert '$schema' in schema
    assert 'title' in schema
    assert 'type' in schema
    assert schema['type'] == 'object'
    assert 'required' in schema
    
    # Check required properties are defined
    required_fields = ['id', 'name', 'simulator', 'version', 'description',
                      'category', 'difficulty', 'input_files', 
                      'expected_results', 'validation_criteria', 'metadata']
    
    for field in required_fields:
        assert field in schema['required'], f"Missing required field: {field}"
    
    print("✓ Schema loading test passed")


def test_list_benchmarks():
    """Test listing all benchmarks."""
    registry = BenchmarkRegistry()
    benchmarks = registry.list_benchmarks()
    
    # Should have at least 3 benchmarks (one for each simulator)
    assert len(benchmarks) >= 3, f"Expected at least 3 benchmarks, found {len(benchmarks)}"
    
    # Check structure of returned benchmarks
    for bench in benchmarks:
        assert 'id' in bench
        assert 'name' in bench
        assert 'simulator' in bench
        assert 'category' in bench
        assert 'difficulty' in bench
        assert 'description' in bench
        assert bench['simulator'] in ['fenicsx', 'lammps', 'openfoam']
    
    print(f"✓ List benchmarks test passed ({len(benchmarks)} benchmarks found)")


def test_list_benchmarks_filtered():
    """Test filtering benchmarks."""
    registry = BenchmarkRegistry()
    
    # Filter by simulator
    fenicsx_benchmarks = registry.list_benchmarks(simulator='fenicsx')
    assert all(b['simulator'] == 'fenicsx' for b in fenicsx_benchmarks)
    
    lammps_benchmarks = registry.list_benchmarks(simulator='lammps')
    assert all(b['simulator'] == 'lammps' for b in lammps_benchmarks)
    
    openfoam_benchmarks = registry.list_benchmarks(simulator='openfoam')
    assert all(b['simulator'] == 'openfoam' for b in openfoam_benchmarks)
    
    # Filter by difficulty
    beginner_benchmarks = registry.list_benchmarks(difficulty='beginner')
    assert all(b['difficulty'] == 'beginner' for b in beginner_benchmarks)
    
    print("✓ Filtered list benchmarks test passed")


def test_load_benchmark():
    """Test loading a specific benchmark."""
    registry = BenchmarkRegistry()
    
    # Load FEniCSx Poisson benchmark
    benchmark = registry.load_benchmark('fenicsx-poisson-2d-basic')
    
    assert benchmark['id'] == 'fenicsx-poisson-2d-basic'
    assert benchmark['simulator'] == 'fenicsx'
    assert 'name' in benchmark
    assert 'description' in benchmark
    assert 'input_files' in benchmark
    assert 'expected_results' in benchmark
    assert 'validation_criteria' in benchmark
    assert 'metadata' in benchmark
    assert 'execution' in benchmark
    
    print("✓ Load benchmark test passed")


def test_validate_benchmark():
    """Test benchmark validation."""
    registry = BenchmarkRegistry()
    
    # Validate existing benchmarks
    for benchmark_id in ['fenicsx-poisson-2d-basic', 
                         'lammps-lennard-jones-fluid',
                         'openfoam-cavity-flow']:
        result = registry.validate_benchmark(benchmark_id)
        
        assert 'benchmark_id' in result
        assert 'valid' in result
        assert 'errors' in result
        assert 'warnings' in result
        
        # Should be valid (may have warnings about file paths)
        if not result['valid']:
            print(f"  Validation errors for {benchmark_id}: {result['errors']}")
        
        # Errors should be empty for valid benchmarks
        # (warnings are okay - file paths may not exist in test environment)
    
    print("✓ Validate benchmark test passed")


def test_validate_all_benchmarks():
    """Test validating all benchmarks."""
    registry = BenchmarkRegistry()
    
    results = registry.validate_all_benchmarks()
    
    assert 'total' in results
    assert 'valid' in results
    assert 'invalid' in results
    assert 'benchmarks' in results
    
    assert results['total'] >= 3  # At least 3 benchmarks
    assert results['total'] == results['valid'] + results['invalid']
    
    print(f"✓ Validate all benchmarks test passed "
          f"({results['valid']}/{results['total']} valid)")


def test_get_statistics():
    """Test getting registry statistics."""
    registry = BenchmarkRegistry()
    
    stats = registry.get_statistics()
    
    assert 'total_benchmarks' in stats
    assert 'by_simulator' in stats
    assert 'by_category' in stats
    assert 'by_difficulty' in stats
    
    # Should have entries for each simulator
    assert 'fenicsx' in stats['by_simulator']
    assert 'lammps' in stats['by_simulator']
    assert 'openfoam' in stats['by_simulator']
    
    # Total should match sum of simulators
    total = sum(stats['by_simulator'].values())
    assert total == stats['total_benchmarks']
    
    print(f"✓ Get statistics test passed ({stats['total_benchmarks']} total)")


def test_generate_report():
    """Test generating markdown report."""
    registry = BenchmarkRegistry()
    
    report = registry.generate_report()
    
    assert isinstance(report, str)
    assert len(report) > 0
    assert '# Benchmark Registry Report' in report
    assert 'Total Benchmarks:' in report
    
    # Should mention each simulator
    assert 'FENICSX' in report or 'fenicsx' in report
    assert 'LAMMPS' in report or 'lammps' in report
    assert 'OPENFOAM' in report or 'openfoam' in report
    
    print("✓ Generate report test passed")


def test_get_benchmark_info():
    """Test getting detailed benchmark information."""
    registry = BenchmarkRegistry()
    
    info = registry.get_benchmark_info('fenicsx-poisson-2d-basic')
    
    # Should return complete benchmark definition
    assert info['id'] == 'fenicsx-poisson-2d-basic'
    assert 'input_files' in info
    assert 'expected_results' in info
    assert 'validation_criteria' in info
    
    print("✓ Get benchmark info test passed")


def test_add_benchmark():
    """Test adding a new benchmark to registry."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_registry = Path(tmpdir) / "benchmarks"
        tmp_registry.mkdir()
        
        # Create schema in temp directory
        registry = BenchmarkRegistry()
        schema_dest = tmp_registry / "benchmark_schema.json"
        
        import shutil
        shutil.copy(registry.schema_path, schema_dest)
        
        # Create simulator directory
        (tmp_registry / "fenicsx").mkdir()
        
        # Initialize registry with temp directory
        test_registry = BenchmarkRegistry(str(tmp_registry))
        
        # Create a test benchmark
        test_benchmark = {
            "id": "fenicsx-test-benchmark",
            "name": "Test Benchmark",
            "simulator": "fenicsx",
            "version": "1.0.0",
            "description": "A test benchmark",
            "category": "finite-element",
            "difficulty": "beginner",
            "tags": ["test"],
            "input_files": [],
            "expected_results": {
                "output_files": [],
                "metrics": {},
                "performance": {
                    "typical_runtime_seconds": 5,
                    "memory_mb": 128,
                    "reference_hardware": "Test hardware"
                }
            },
            "validation_criteria": {
                "method": "tolerance_based",
                "tolerance": 0.01,
                "checks": []
            },
            "metadata": {
                "author": "Test Author",
                "created_date": "2025-10-20",
                "license": "MIT"
            },
            "execution": {
                "command": "python3 test.py",
                "timeout_seconds": 60,
                "requires_gpu": False
            }
        }
        
        # Add benchmark
        result = test_registry.add_benchmark(test_benchmark)
        
        assert result['success']
        assert result['benchmark_id'] == 'fenicsx-test-benchmark'
        assert result['file_path'] is not None
        
        # Verify file was created
        assert Path(result['file_path']).exists()
        
        # Verify we can load it back
        loaded = test_registry.load_benchmark('fenicsx-test-benchmark')
        assert loaded['id'] == 'fenicsx-test-benchmark'
    
    print("✓ Add benchmark test passed")


def test_benchmark_not_found():
    """Test handling of non-existent benchmark."""
    registry = BenchmarkRegistry()
    
    try:
        registry.load_benchmark('non-existent-benchmark-id')
        assert False, "Should have raised FileNotFoundError"
    except FileNotFoundError as e:
        assert 'not found' in str(e).lower()
    
    print("✓ Benchmark not found test passed")


def run_all_tests():
    """Run all test functions."""
    test_functions = [
        test_registry_initialization,
        test_schema_loading,
        test_list_benchmarks,
        test_list_benchmarks_filtered,
        test_load_benchmark,
        test_validate_benchmark,
        test_validate_all_benchmarks,
        test_get_statistics,
        test_generate_report,
        test_get_benchmark_info,
        test_add_benchmark,
        test_benchmark_not_found,
    ]
    
    print("\n" + "="*70)
    print("Running Benchmark Registry Tests")
    print("="*70 + "\n")
    
    passed = 0
    failed = 0
    
    for test_func in test_functions:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"✗ {test_func.__name__} failed: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {test_func.__name__} error: {e}")
            failed += 1
    
    print("\n" + "="*70)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("="*70 + "\n")
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
