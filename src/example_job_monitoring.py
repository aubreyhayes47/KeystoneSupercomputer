#!/usr/bin/env python3
"""
Example demonstrating job monitoring and resource tracking.

This script shows how to use the monitoring system to track job
execution, resource usage, and view job history.
"""

import sys
import time
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent))

from job_monitor import get_monitor


def example_basic_monitoring():
    """Basic monitoring example."""
    print("=" * 70)
    print("Example 1: Basic Job Monitoring")
    print("=" * 70)
    print()
    
    monitor = get_monitor()
    
    # Start monitoring a job
    print("Starting job monitoring...")
    job_info = monitor.start_monitoring(
        task_id="example-task-1",
        tool="fenicsx",
        script="poisson.py",
        params={"mesh_size": 64}
    )
    print(f"✓ Monitoring started for task: {job_info['task_id']}")
    print(f"  Tool: {job_info['tool']}")
    print(f"  Script: {job_info['script']}")
    print()
    
    # Simulate work
    print("Simulating job execution...")
    time.sleep(1.0)
    
    # Stop monitoring
    print("Stopping monitoring...")
    job_stats = monitor.stop_monitoring(
        task_id="example-task-1",
        status="success",
        returncode=0
    )
    
    print(f"✓ Job completed!")
    print(f"  Duration: {job_stats['duration_seconds']}s")
    print(f"  CPU Time: {job_stats['resource_usage']['cpu_total_seconds']}s")
    print(f"  Memory Peak: {job_stats['resource_usage']['memory_peak_mb']} MB")
    print()


def example_context_manager():
    """Context manager monitoring example."""
    print("=" * 70)
    print("Example 2: Context Manager Usage")
    print("=" * 70)
    print()
    
    monitor = get_monitor()
    
    print("Running job with context manager...")
    with monitor.track_job("example-task-2", "lammps", "example.lammps", {}) as tracker:
        print("✓ Monitoring started automatically")
        time.sleep(0.5)
        print("✓ Job executing...")
        # Optionally set custom status
        # tracker.set_status("failed", returncode=1, error="Test error")
    
    print("✓ Monitoring stopped automatically")
    
    # Retrieve job stats
    job = monitor.get_job_stats("example-task-2")
    print(f"  Status: {job['status']}")
    print(f"  Duration: {job['duration_seconds']}s")
    print()


def example_multiple_jobs():
    """Monitor multiple jobs."""
    print("=" * 70)
    print("Example 3: Multiple Jobs with Mixed Outcomes")
    print("=" * 70)
    print()
    
    monitor = get_monitor()
    
    jobs = [
        ("task-3a", "fenicsx", "success", 0),
        ("task-3b", "lammps", "success", 0),
        ("task-3c", "openfoam", "failed", 1),
        ("task-3d", "fenicsx", "success", 0),
    ]
    
    for task_id, tool, status, returncode in jobs:
        print(f"Running {task_id} ({tool})...")
        monitor.start_monitoring(task_id, tool, "test.py", {})
        time.sleep(0.1)
        monitor.stop_monitoring(task_id, status, returncode, 
                               error="Test error" if status == "failed" else None)
        print(f"  ✓ {status.upper()}")
    
    print()


def example_job_history():
    """View job history."""
    print("=" * 70)
    print("Example 4: Job History")
    print("=" * 70)
    print()
    
    monitor = get_monitor()
    
    # Get all job history
    jobs = monitor.get_job_history(limit=5)
    
    print(f"Recent Job History (last {len(jobs)} jobs):")
    print()
    
    for i, job in enumerate(jobs, 1):
        status_color = {
            'success': '✓',
            'failed': '✗',
            'error': '⚠',
            'timeout': '⏱'
        }.get(job['status'], '?')
        
        print(f"{i}. {status_color} {job['task_id'][:20]}...")
        print(f"   Tool: {job['tool']}, Status: {job['status'].upper()}")
        print(f"   Duration: {job['duration_seconds']}s, " +
              f"CPU: {job['resource_usage']['cpu_total_seconds']}s, " +
              f"Memory: {job['resource_usage']['memory_peak_mb']} MB")
        if job.get('error'):
            print(f"   Error: {job['error'][:50]}...")
        print()


def example_statistics():
    """View aggregate statistics."""
    print("=" * 70)
    print("Example 5: Aggregate Statistics")
    print("=" * 70)
    print()
    
    monitor = get_monitor()
    stats = monitor.get_summary_statistics()
    
    print("Overall Statistics:")
    print(f"  Total Jobs: {stats['total_jobs']}")
    print(f"  Successful: {stats['successful']} ({stats['success_rate']}%)")
    print(f"  Failed: {stats['failed']}")
    print(f"  Success Rate: {stats['success_rate']}%")
    print()
    
    print("Resource Usage:")
    print(f"  Total CPU Time: {stats['total_cpu_time_seconds']}s")
    print(f"  Total Duration: {stats['total_duration_seconds']}s")
    print(f"  Average Duration: {stats['average_duration_seconds']}s")
    print()
    
    if stats['by_tool']:
        print("By Tool:")
        for tool, tool_stats in stats['by_tool'].items():
            success_rate = (tool_stats['successful'] / tool_stats['count'] * 100) if tool_stats['count'] > 0 else 0
            print(f"  {tool}:")
            print(f"    Jobs: {tool_stats['count']}")
            print(f"    Successful: {tool_stats['successful']} ({success_rate:.1f}%)")
            print(f"    Failed: {tool_stats['failed']}")
        print()


def main():
    """Run all examples."""
    print()
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 15 + "Job Monitoring Examples" + " " * 30 + "║")
    print("╚" + "=" * 68 + "╝")
    print()
    
    try:
        # Run examples
        example_basic_monitoring()
        example_context_manager()
        example_multiple_jobs()
        example_job_history()
        example_statistics()
        
        print("=" * 70)
        print("All examples completed successfully!")
        print("=" * 70)
        print()
        print("Job history is stored in: /tmp/keystone_jobs/jobs_history.jsonl")
        print()
        
    except Exception as e:
        print(f"Error running examples: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
