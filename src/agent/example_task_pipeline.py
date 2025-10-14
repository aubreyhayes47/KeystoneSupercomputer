#!/usr/bin/env python3
"""
Example: Task Pipeline Usage
=============================

Demonstrates the TaskPipeline class for agent workflow orchestration.
This example shows various ways to submit, monitor, and manage simulation tasks.
"""

from task_pipeline import TaskPipeline
import time


def example_1_basic_usage():
    """Example 1: Basic task submission and monitoring."""
    print("=" * 70)
    print("Example 1: Basic Task Submission")
    print("=" * 70)
    print()
    
    pipeline = TaskPipeline()
    
    # 1. Health check
    print("1. Checking worker health...")
    try:
        health = pipeline.health_check()
        print(f"   ✓ Worker status: {health['status']}")
        print(f"   Message: {health['message']}")
    except Exception as e:
        print(f"   ✗ Health check failed: {e}")
        return
    print()
    
    # 2. List available simulations
    print("2. Listing available simulations...")
    simulations = pipeline.list_available_simulations()
    for tool, info in simulations['tools'].items():
        print(f"   - {tool}: {info['description']}")
    print()
    
    # 3. Submit a task
    print("3. Submitting FEniCSx simulation...")
    task_id = pipeline.submit_task(
        tool="fenicsx",
        script="poisson.py",
        params={"mesh_size": 64}
    )
    print(f"   Task ID: {task_id}")
    print()
    
    # 4. Monitor task with callback
    print("4. Monitoring task progress...")
    def progress_callback(status):
        if status['state'] == 'RUNNING' and 'progress' in status:
            print(f"   Progress: {status['progress']}%")
        elif status['ready']:
            print(f"   Task completed with state: {status['state']}")
    
    pipeline.monitor_task(task_id, callback=progress_callback, poll_interval=2)
    print()
    
    # 5. Get final result
    print("5. Retrieving final result...")
    result = pipeline.wait_for_task(task_id, timeout=30)
    print(f"   Status: {result['status']}")
    print(f"   Tool: {result['tool']}")
    print(f"   Script: {result['script']}")
    if result['status'] == 'success':
        print("   ✓ Simulation completed successfully!")
    else:
        print(f"   ✗ Simulation failed: {result.get('error', 'Unknown error')}")
    print()


def example_2_workflow_parallel():
    """Example 2: Parallel workflow submission."""
    print("=" * 70)
    print("Example 2: Parallel Workflow")
    print("=" * 70)
    print()
    
    pipeline = TaskPipeline()
    
    # Submit multiple tasks in parallel
    tasks = [
        {"tool": "fenicsx", "script": "poisson.py", "params": {"mesh_size": 32}},
        {"tool": "lammps", "script": "example.lammps", "params": {}},
        {"tool": "openfoam", "script": "example_cavity.py", "params": {}},
    ]
    
    print("1. Submitting parallel workflow (3 tasks)...")
    task_ids = pipeline.submit_workflow(tasks, sequential=False)
    print(f"   Submitted {len(task_ids)} tasks")
    for i, task_id in enumerate(task_ids):
        print(f"   Task {i+1}: {task_id}")
    print()
    
    # Monitor workflow progress
    print("2. Monitoring workflow progress...")
    def workflow_callback(status):
        print(f"   Progress: {status['completed']}/{status['total']} completed, "
              f"{status['running']} running, {status['failed']} failed")
    
    try:
        final_status = pipeline.wait_for_workflow(
            task_ids,
            timeout=600,
            callback=workflow_callback,
            poll_interval=5
        )
        print()
        print("3. Workflow complete!")
        print(f"   Total: {final_status['total']}")
        print(f"   Completed: {final_status['completed']}")
        print(f"   Failed: {final_status['failed']}")
    except TimeoutError as e:
        print(f"   ✗ Workflow timed out: {e}")
    print()


def example_3_workflow_sequential():
    """Example 3: Sequential workflow submission."""
    print("=" * 70)
    print("Example 3: Sequential Workflow")
    print("=" * 70)
    print()
    
    pipeline = TaskPipeline()
    
    # Submit tasks sequentially (wait for each to complete before starting next)
    tasks = [
        {"tool": "fenicsx", "script": "poisson.py", "params": {"mesh_size": 16}},
        {"tool": "lammps", "script": "example.lammps", "params": {}},
    ]
    
    print("1. Submitting sequential workflow (2 tasks)...")
    print("   (Each task waits for previous to complete)")
    task_ids = pipeline.submit_workflow(tasks, sequential=True)
    print(f"   ✓ All {len(task_ids)} tasks completed")
    print()
    
    # Get status of each task
    print("2. Checking individual task results...")
    for i, task_id in enumerate(task_ids):
        status = pipeline.get_task_status(task_id)
        result = status.get('result', {})
        print(f"   Task {i+1} ({result.get('tool', 'unknown')}):")
        print(f"      Status: {result.get('status', 'unknown')}")
        print(f"      Script: {result.get('script', 'unknown')}")
    print()


def example_4_task_cancellation():
    """Example 4: Task cancellation."""
    print("=" * 70)
    print("Example 4: Task Cancellation")
    print("=" * 70)
    print()
    
    pipeline = TaskPipeline()
    
    print("1. Submitting a task...")
    task_id = pipeline.submit_task(
        tool="fenicsx",
        script="poisson.py",
        params={"mesh_size": 128}
    )
    print(f"   Task ID: {task_id}")
    print()
    
    # Wait a bit then cancel
    print("2. Waiting 5 seconds...")
    time.sleep(5)
    print()
    
    print("3. Cancelling task...")
    if pipeline.cancel_task(task_id):
        print("   ✓ Task cancelled successfully")
    else:
        print("   ✗ Task cancellation failed")
    print()
    
    # Check final status
    print("4. Checking final task status...")
    status = pipeline.get_task_status(task_id)
    print(f"   State: {status['state']}")
    print()


def example_5_status_polling():
    """Example 5: Manual status polling."""
    print("=" * 70)
    print("Example 5: Manual Status Polling")
    print("=" * 70)
    print()
    
    pipeline = TaskPipeline()
    
    print("1. Submitting task...")
    task_id = pipeline.submit_task(
        tool="fenicsx",
        script="poisson.py",
        params={"mesh_size": 32}
    )
    print(f"   Task ID: {task_id}")
    print()
    
    print("2. Polling status manually...")
    for i in range(10):
        status = pipeline.get_task_status(task_id)
        print(f"   Poll {i+1}: State={status['state']}, Ready={status['ready']}")
        
        if status['ready']:
            result = status.get('result', {})
            print(f"   Final status: {result.get('status', 'unknown')}")
            break
        
        time.sleep(3)
    print()


def main():
    """Run all examples."""
    print("\n")
    print("#" * 70)
    print("# Task Pipeline Examples")
    print("#" * 70)
    print("\n")
    
    examples = [
        ("Basic Usage", example_1_basic_usage),
        ("Parallel Workflow", example_2_workflow_parallel),
        ("Sequential Workflow", example_3_workflow_sequential),
        ("Task Cancellation", example_4_task_cancellation),
        ("Status Polling", example_5_status_polling),
    ]
    
    print("Available examples:")
    for i, (name, _) in enumerate(examples, 1):
        print(f"  {i}. {name}")
    print()
    
    # For demo purposes, run just the basic example
    # In practice, you would run the example you want
    print("Running Example 1: Basic Usage")
    print("(To run other examples, modify the main() function)")
    print()
    
    try:
        example_1_basic_usage()
    except Exception as e:
        print(f"Example failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n")
    print("#" * 70)
    print("# Examples Complete")
    print("#" * 70)


if __name__ == '__main__':
    main()
