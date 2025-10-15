#!/usr/bin/env python3
"""
Unit tests for the Job Monitor module.

These tests validate resource tracking and failure monitoring functionality.
"""

import sys
import time
import tempfile
import shutil
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent))

from job_monitor import JobMonitor, get_monitor


def test_job_monitor_instantiation():
    """Test that JobMonitor can be instantiated."""
    with tempfile.TemporaryDirectory() as tmpdir:
        monitor = JobMonitor(log_dir=tmpdir)
        assert monitor is not None
        assert monitor.log_dir.exists()
        print("✓ JobMonitor instantiation test passed")


def test_start_stop_monitoring():
    """Test basic start/stop monitoring workflow."""
    with tempfile.TemporaryDirectory() as tmpdir:
        monitor = JobMonitor(log_dir=tmpdir)
        
        # Start monitoring
        job_info = monitor.start_monitoring(
            task_id="test-task-1",
            tool="fenicsx",
            script="test.py",
            params={"mesh_size": 32}
        )
        
        assert job_info['task_id'] == "test-task-1"
        assert job_info['tool'] == "fenicsx"
        assert job_info['script'] == "test.py"
        assert 'start_time' in job_info
        assert 'process_id' in job_info
        
        # Simulate some work
        time.sleep(0.1)
        
        # Stop monitoring
        job_stats = monitor.stop_monitoring(
            task_id="test-task-1",
            status="success",
            returncode=0
        )
        
        assert job_stats['task_id'] == "test-task-1"
        assert job_stats['status'] == "success"
        assert job_stats['returncode'] == 0
        assert job_stats['duration_seconds'] >= 0.1
        assert 'resource_usage' in job_stats
        assert 'cpu_total_seconds' in job_stats['resource_usage']
        
        print("✓ Start/stop monitoring test passed")


def test_job_history_persistence():
    """Test that job history is persisted to file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        monitor = JobMonitor(log_dir=tmpdir)
        
        # Record a few jobs
        for i in range(3):
            monitor.start_monitoring(
                task_id=f"test-task-{i}",
                tool="fenicsx",
                script="test.py",
                params={}
            )
            time.sleep(0.01)
            monitor.stop_monitoring(
                task_id=f"test-task-{i}",
                status="success" if i % 2 == 0 else "failed",
                returncode=0 if i % 2 == 0 else 1
            )
        
        # Get history
        history = monitor.get_job_history()
        assert len(history) == 3
        
        # Most recent should be first
        assert history[0]['task_id'] == "test-task-2"
        assert history[2]['task_id'] == "test-task-0"
        
        # Test with limit
        limited = monitor.get_job_history(limit=2)
        assert len(limited) == 2
        
        print("✓ Job history persistence test passed")


def test_get_job_stats():
    """Test retrieving stats for a specific job."""
    with tempfile.TemporaryDirectory() as tmpdir:
        monitor = JobMonitor(log_dir=tmpdir)
        
        # Record jobs
        monitor.start_monitoring("task-abc", "fenicsx", "test.py", {})
        time.sleep(0.01)
        monitor.stop_monitoring("task-abc", "success", 0)
        
        monitor.start_monitoring("task-xyz", "lammps", "test.lammps", {})
        time.sleep(0.01)
        monitor.stop_monitoring("task-xyz", "failed", 1, error="Test error")
        
        # Get specific job
        job_abc = monitor.get_job_stats("task-abc")
        assert job_abc is not None
        assert job_abc['task_id'] == "task-abc"
        assert job_abc['status'] == "success"
        
        job_xyz = monitor.get_job_stats("task-xyz")
        assert job_xyz is not None
        assert job_xyz['status'] == "failed"
        assert job_xyz['error'] == "Test error"
        
        # Non-existent job
        job_none = monitor.get_job_stats("nonexistent")
        assert job_none is None
        
        print("✓ Get job stats test passed")


def test_summary_statistics():
    """Test aggregate statistics calculation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        monitor = JobMonitor(log_dir=tmpdir)
        
        # Record mix of successful and failed jobs
        jobs_data = [
            ("task-1", "fenicsx", "success", 0),
            ("task-2", "fenicsx", "success", 0),
            ("task-3", "fenicsx", "failed", 1),
            ("task-4", "lammps", "success", 0),
            ("task-5", "lammps", "failed", 1),
        ]
        
        for task_id, tool, status, returncode in jobs_data:
            monitor.start_monitoring(task_id, tool, "test.py", {})
            time.sleep(0.01)
            monitor.stop_monitoring(task_id, status, returncode)
        
        # Get summary
        stats = monitor.get_summary_statistics()
        
        assert stats['total_jobs'] == 5
        assert stats['successful'] == 3
        assert stats['failed'] == 2
        assert stats['success_rate'] == 60.0
        assert stats['total_duration_seconds'] > 0
        assert stats['average_duration_seconds'] > 0
        
        # Check by-tool stats
        assert 'fenicsx' in stats['by_tool']
        assert 'lammps' in stats['by_tool']
        
        fenicsx_stats = stats['by_tool']['fenicsx']
        assert fenicsx_stats['count'] == 3
        assert fenicsx_stats['successful'] == 2
        assert fenicsx_stats['failed'] == 1
        
        lammps_stats = stats['by_tool']['lammps']
        assert lammps_stats['count'] == 2
        assert lammps_stats['successful'] == 1
        assert lammps_stats['failed'] == 1
        
        print("✓ Summary statistics test passed")


def test_context_manager():
    """Test using JobMonitor with context manager."""
    with tempfile.TemporaryDirectory() as tmpdir:
        monitor = JobMonitor(log_dir=tmpdir)
        
        # Success case
        with monitor.track_job("task-ctx-1", "fenicsx", "test.py", {}) as tracker:
            time.sleep(0.01)
            # Job completes successfully
        
        job = monitor.get_job_stats("task-ctx-1")
        assert job is not None
        assert job['status'] == "success"
        
        # Failure case with manual status
        with monitor.track_job("task-ctx-2", "lammps", "test.lammps", {}) as tracker:
            time.sleep(0.01)
            tracker.set_status("failed", returncode=1, error="Simulation error")
        
        job = monitor.get_job_stats("task-ctx-2")
        assert job is not None
        assert job['status'] == "failed"
        assert job['error'] == "Simulation error"
        
        print("✓ Context manager test passed")


def test_context_manager_with_exception():
    """Test context manager handles exceptions."""
    with tempfile.TemporaryDirectory() as tmpdir:
        monitor = JobMonitor(log_dir=tmpdir)
        
        try:
            with monitor.track_job("task-exc", "fenicsx", "test.py", {}):
                raise ValueError("Test exception")
        except ValueError:
            pass  # Expected
        
        # Job should be recorded with error status
        job = monitor.get_job_stats("task-exc")
        assert job is not None
        assert job['status'] == "error"
        assert "Test exception" in job['error']
        
        print("✓ Context manager exception test passed")


def test_global_monitor():
    """Test global monitor singleton."""
    monitor1 = get_monitor()
    monitor2 = get_monitor()
    
    # Should be the same instance
    assert monitor1 is monitor2
    
    print("✓ Global monitor test passed")


def test_empty_history():
    """Test behavior with no job history."""
    with tempfile.TemporaryDirectory() as tmpdir:
        monitor = JobMonitor(log_dir=tmpdir)
        
        history = monitor.get_job_history()
        assert history == []
        
        stats = monitor.get_summary_statistics()
        assert stats['total_jobs'] == 0
        assert stats['successful'] == 0
        assert stats['failed'] == 0
        assert stats['success_rate'] == 0.0
        
        print("✓ Empty history test passed")


def run_all_tests():
    """Run all unit tests."""
    print("=" * 70)
    print("Running Job Monitor Unit Tests")
    print("=" * 70)
    print()
    
    tests = [
        test_job_monitor_instantiation,
        test_start_stop_monitoring,
        test_job_history_persistence,
        test_get_job_stats,
        test_summary_statistics,
        test_context_manager,
        test_context_manager_with_exception,
        test_global_monitor,
        test_empty_history,
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
