#!/usr/bin/env python3
"""
Unit tests for the Resource Profiler module.

These tests validate comprehensive resource tracking functionality including
CPU, memory, GPU, I/O, and container metrics.
"""

import sys
import time
import tempfile
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent))

from resource_profiler import ResourceProfiler, ContainerResourceMonitor, get_profiler


def test_resource_profiler_instantiation():
    """Test that ResourceProfiler can be instantiated."""
    profiler = ResourceProfiler()
    assert profiler is not None
    print("✓ ResourceProfiler instantiation test passed")


def test_start_stop_profiling():
    """Test basic start/stop profiling workflow."""
    profiler = ResourceProfiler()
    
    # Start profiling
    profiler.start_profiling()
    
    # Simulate some work
    time.sleep(1.0)
    result = sum(i**2 for i in range(10000))
    
    # Stop profiling
    profile = profiler.stop_profiling()
    
    # Verify profile structure
    assert 'duration_seconds' in profile
    assert 'samples_collected' in profile
    assert profile['duration_seconds'] >= 1.0
    assert profile['samples_collected'] > 0
    
    # Check for CPU metrics
    if 'cpu' in profile:
        assert 'mean_percent' in profile['cpu']
        assert 'max_percent' in profile['cpu']
        assert profile['cpu']['mean_percent'] >= 0
        print(f"  CPU mean: {profile['cpu']['mean_percent']}%")
    
    # Check for memory metrics
    if 'memory' in profile:
        assert 'mean_used_mb' in profile['memory']
        assert 'max_used_mb' in profile['memory']
        assert profile['memory']['mean_used_mb'] > 0
        print(f"  Memory mean: {profile['memory']['mean_used_mb']} MB")
    
    # Check for I/O metrics
    if 'io_stats' in profile:
        print(f"  I/O read: {profile['io_stats'].get('read_mb', 0)} MB")
        print(f"  I/O write: {profile['io_stats'].get('write_mb', 0)} MB")
    
    print("✓ Start/stop profiling test passed")


def test_profiler_multiple_samples():
    """Test that profiler collects multiple samples over time."""
    profiler = ResourceProfiler()
    
    profiler.start_profiling()
    
    # Do some work over 2 seconds
    for i in range(4):
        time.sleep(0.5)
        _ = sum(j**2 for j in range(5000))
    
    profile = profiler.stop_profiling()
    
    # Should have collected at least 3 samples (2 seconds / 0.5s interval)
    assert profile['samples_collected'] >= 3
    print(f"  Collected {profile['samples_collected']} samples in {profile['duration_seconds']}s")
    print("✓ Multiple samples test passed")


def test_io_statistics():
    """Test I/O statistics collection."""
    profiler = ResourceProfiler()
    
    profiler.start_profiling()
    
    # Create temporary file to generate I/O
    with tempfile.NamedTemporaryFile(mode='w', delete=True) as f:
        # Write some data
        for i in range(1000):
            f.write(f"Line {i}: " + "x" * 100 + "\n")
        f.flush()
    
    time.sleep(0.5)
    profile = profiler.stop_profiling()
    
    # Check I/O stats
    if 'io_stats' in profile:
        io = profile['io_stats']
        print(f"  I/O statistics: read={io.get('read_mb', 0)}MB, write={io.get('write_mb', 0)}MB")
        print("✓ I/O statistics test passed")
    else:
        print("⚠ I/O statistics not available on this system")


def test_gpu_detection():
    """Test GPU detection and statistics (if available)."""
    profiler = ResourceProfiler()
    
    profiler.start_profiling()
    time.sleep(0.5)
    profile = profiler.stop_profiling()
    
    if 'gpu_stats' in profile and profile['gpu_stats']:
        print("  GPU detected:")
        
        if 'nvidia' in profile['gpu_stats']:
            nvidia = profile['gpu_stats']['nvidia']
            print(f"    NVIDIA GPU: {nvidia.get('gpu_utilization_percent', 0)}% utilization")
            print(f"    Memory: {nvidia.get('memory_used_mb', 0)}MB / {nvidia.get('memory_total_mb', 0)}MB")
        
        if 'intel' in profile['gpu_stats']:
            print(f"    Intel GPU: available")
        
        print("✓ GPU detection test passed")
    else:
        print("⚠ No GPU detected on this system")


def test_global_profiler():
    """Test the global profiler singleton."""
    profiler1 = get_profiler()
    profiler2 = get_profiler()
    
    # Should be the same instance
    assert profiler1 is profiler2
    assert profiler1 is not None
    print("✓ Global profiler singleton test passed")


def test_profiler_with_container_name():
    """Test profiling with container name."""
    profiler = ResourceProfiler()
    
    # Start with a fake container name
    profiler.start_profiling(container_name="test-container")
    
    time.sleep(0.5)
    profile = profiler.stop_profiling()
    
    # Should have attempted to collect container stats (will fail for non-existent container)
    assert 'container_stats' in profile
    print("✓ Profiler with container name test passed")


def test_container_resource_monitor():
    """Test ContainerResourceMonitor class."""
    monitor = ContainerResourceMonitor("test-container")
    
    assert monitor.container_name == "test-container"
    assert monitor.profiler is not None
    
    # Try to get container info (will fail for non-existent container)
    info = monitor.get_container_info()
    # Should return empty dict for non-existent container
    assert isinstance(info, dict)
    
    print("✓ ContainerResourceMonitor test passed")


def test_profiler_statistics_computation():
    """Test that profiler computes statistics correctly."""
    profiler = ResourceProfiler()
    
    profiler.start_profiling()
    
    # Do varying amounts of work to generate different CPU loads
    for i in range(5):
        workload = 1000 * (i + 1)
        _ = sum(j**2 for j in range(workload))
        time.sleep(0.2)
    
    profile = profiler.stop_profiling()
    
    # Verify statistics are present and reasonable
    assert profile['duration_seconds'] >= 1.0
    
    if 'cpu' in profile:
        cpu = profile['cpu']
        # Max should be >= mean, mean should be >= min
        assert cpu['max_percent'] >= cpu['mean_percent'] >= cpu['min_percent'] >= 0
        print(f"  CPU: min={cpu['min_percent']}%, mean={cpu['mean_percent']}%, max={cpu['max_percent']}%")
    
    if 'process_memory' in profile:
        mem = profile['process_memory']
        assert mem['max_mb'] >= mem['mean_mb'] >= mem['min_mb'] > 0
        print(f"  Memory: min={mem['min_mb']}MB, mean={mem['mean_mb']}MB, max={mem['max_mb']}MB")
    
    print("✓ Statistics computation test passed")


def run_all_tests():
    """Run all resource profiler tests."""
    print("\n" + "="*60)
    print("Resource Profiler Tests")
    print("="*60 + "\n")
    
    tests = [
        test_resource_profiler_instantiation,
        test_start_stop_profiling,
        test_profiler_multiple_samples,
        test_io_statistics,
        test_gpu_detection,
        test_global_profiler,
        test_profiler_with_container_name,
        test_container_resource_monitor,
        test_profiler_statistics_computation,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            print(f"\nRunning {test.__name__}...")
            test()
            passed += 1
        except AssertionError as e:
            print(f"✗ {test.__name__} failed: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {test.__name__} error: {e}")
            failed += 1
    
    print("\n" + "="*60)
    print(f"Results: {passed} passed, {failed} failed")
    print("="*60 + "\n")
    
    return failed == 0


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
