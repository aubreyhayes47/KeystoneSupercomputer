#!/usr/bin/env python3
"""
Example: Parallel Orchestration Patterns
=========================================

Demonstrates advanced parallel orchestration patterns including:
- Batch workflow submission
- Parameter sweep workflows
- Wait-for-any patterns
- Parallel execution statistics
- Dynamic load balancing
"""

import sys
import time
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from task_pipeline import TaskPipeline
import multiprocessing


def example_1_batch_workflow():
    """Example 1: Batch workflow submission."""
    print("=" * 70)
    print("Example 1: Batch Workflow Submission")
    print("=" * 70)
    print()
    
    pipeline = TaskPipeline()
    
    # Create a large set of tasks
    tasks = [
        {"tool": "fenicsx", "script": "poisson.py", "params": {"mesh_size": size}}
        for size in [16, 32, 64, 128, 256]
    ]
    
    print(f"Submitting {len(tasks)} tasks in batches...")
    
    def on_batch(info):
        print(f"  Batch {info['batch_num']}: "
              f"Submitted {info['batch_size']} tasks "
              f"({info['submitted']}/{info['total']} total)")
    
    try:
        task_ids = pipeline.submit_batch_workflow(
            tasks,
            batch_size=2,
            callback=on_batch
        )
        print(f"\n✓ Successfully submitted {len(task_ids)} tasks")
        print(f"  Task IDs: {task_ids[:3]}... (showing first 3)")
    except Exception as e:
        print(f"✗ Failed: {e}")
    
    print()


def example_2_parameter_sweep():
    """Example 2: Parameter sweep workflow."""
    print("=" * 70)
    print("Example 2: Parameter Sweep Workflow")
    print("=" * 70)
    print()
    
    pipeline = TaskPipeline()
    
    # Define parameter grid
    param_grid = {
        'mesh_size': [16, 32, 64],
        'time_steps': [100, 200]
    }
    
    print("Parameter grid:")
    for param, values in param_grid.items():
        print(f"  {param}: {values}")
    
    total_combinations = 1
    for values in param_grid.values():
        total_combinations *= len(values)
    print(f"\nTotal combinations: {total_combinations}")
    print()
    
    try:
        print("Submitting parameter sweep...")
        task_ids = pipeline.parameter_sweep(
            tool='fenicsx',
            script='poisson.py',
            param_grid=param_grid
        )
        print(f"✓ Submitted {len(task_ids)} tasks")
        print(f"  Task IDs: {task_ids[:3]}... (showing first 3)")
    except Exception as e:
        print(f"✗ Failed: {e}")
    
    print()


def example_3_wait_for_any():
    """Example 3: Wait for any task to complete."""
    print("=" * 70)
    print("Example 3: Wait-for-Any Pattern")
    print("=" * 70)
    print()
    
    pipeline = TaskPipeline()
    
    # Submit multiple tasks
    tasks = [
        {"tool": "fenicsx", "script": "poisson.py", "params": {"mesh_size": 16}},
        {"tool": "lammps", "script": "example.lammps", "params": {}},
        {"tool": "openfoam", "script": "example_cavity.py", "params": {}},
    ]
    
    print(f"Submitting {len(tasks)} tasks...")
    try:
        task_ids = pipeline.submit_workflow(tasks, sequential=False)
        print(f"✓ Submitted tasks: {task_ids}")
        print()
        
        print("Waiting for first task to complete...")
        print("(Note: This will timeout if no worker is available)")
        
        # In a real scenario, this would wait for actual task completion
        # For this demo, we'll just show the pattern
        print("Pattern: result = pipeline.wait_for_any(task_ids, timeout=300)")
        print("  This returns the first completed task")
        print()
        
    except Exception as e:
        print(f"Note: {e}")
    
    print()


def example_4_parallel_execution_stats():
    """Example 4: Parallel execution statistics."""
    print("=" * 70)
    print("Example 4: Parallel Execution Statistics")
    print("=" * 70)
    print()
    
    pipeline = TaskPipeline()
    
    # Mock some task IDs for demonstration
    print("Demonstrating parallel execution statistics...")
    print()
    
    # In a real scenario, you would have actual task IDs
    print("After workflow completes:")
    print("  stats = pipeline.get_parallel_execution_stats(task_ids)")
    print()
    print("Statistics provided:")
    print("  - total_tasks: Total number of tasks")
    print("  - completed: Number completed successfully")
    print("  - failed: Number failed")
    print("  - running: Number currently running")
    print("  - pending: Number pending")
    print("  - total_duration: Sum of all task durations")
    print("  - avg_duration: Average task duration")
    print("  - max_duration: Maximum task duration")
    print("  - speedup: Parallel speedup factor")
    print("  - efficiency: Parallel efficiency (0-1)")
    print()
    
    print("Example output:")
    print("  Speedup: 3.5x")
    print("  Efficiency: 87.5%")
    print("  Average duration: 45.2s")
    print()


def example_5_dynamic_load_balancing():
    """Example 5: Dynamic load balancing pattern."""
    print("=" * 70)
    print("Example 5: Dynamic Load Balancing")
    print("=" * 70)
    print()
    
    pipeline = TaskPipeline()
    
    # Simulate a large task queue
    print("Dynamic load balancing pattern:")
    print()
    
    print("```python")
    print("all_tasks = [...]  # Large list of tasks")
    print("task_queue = list(all_tasks)")
    print("active_tasks = {}")
    print("max_concurrent = 10")
    print()
    print("while task_queue or active_tasks:")
    print("    # Submit tasks up to max concurrent")
    print("    while len(active_tasks) < max_concurrent and task_queue:")
    print("        task = task_queue.pop(0)")
    print("        task_id = pipeline.submit_task(...")
    print("        active_tasks[task_id] = task")
    print("    ")
    print("    # Check for completions")
    print("    for task_id in list(active_tasks.keys()):")
    print("        status = pipeline.get_task_status(task_id)")
    print("        if status['ready']:")
    print("            del active_tasks[task_id]")
    print("    ")
    print("    time.sleep(2)")
    print("```")
    print()
    
    print("Benefits:")
    print("  - Maintains constant load on workers")
    print("  - Prevents queue saturation")
    print("  - Adapts to task completion rate")
    print()


def example_6_adaptive_parameter_sweep():
    """Example 6: Adaptive parameter sweep."""
    print("=" * 70)
    print("Example 6: Adaptive Parameter Sweep")
    print("=" * 70)
    print()
    
    pipeline = TaskPipeline()
    
    print("Two-stage adaptive parameter sweep:")
    print()
    
    print("Stage 1: Coarse sweep")
    print("  param_grid = {'mesh_size': [16, 32, 64, 128]}")
    print("  task_ids = pipeline.parameter_sweep(...)")
    print("  results = pipeline.wait_for_workflow(task_ids)")
    print()
    
    print("Stage 2: Refined sweep around best value")
    print("  best_mesh = analyze_convergence(results)")
    print("  refined_params = {")
    print("      'mesh_size': [best_mesh - 8, best_mesh, best_mesh + 8],")
    print("      'tolerance': [0.01, 0.001, 0.0001]")
    print("  }")
    print("  task_ids_2 = pipeline.parameter_sweep(...)")
    print()
    
    print("Benefits:")
    print("  - Reduces total computation")
    print("  - Focuses on promising parameter ranges")
    print("  - Achieves better resolution where needed")
    print()


def example_7_hierarchical_workflow():
    """Example 7: Hierarchical workflow with dependencies."""
    print("=" * 70)
    print("Example 7: Hierarchical Workflow")
    print("=" * 70)
    print()
    
    print("Multi-stage workflow with dependencies:")
    print()
    
    print("Stage 1: Preprocessing (parallel)")
    print("  prep_tasks = [...]")
    print("  prep_ids = pipeline.submit_batch_workflow(prep_tasks)")
    print("  prep_results = pipeline.wait_for_workflow(prep_ids)")
    print()
    
    print("Stage 2: Main simulation (parallel, depends on stage 1)")
    print("  sim_tasks = build_tasks_from_results(prep_results)")
    print("  sim_ids = pipeline.submit_batch_workflow(sim_tasks)")
    print("  sim_results = pipeline.wait_for_workflow(sim_ids)")
    print()
    
    print("Stage 3: Analysis (parallel, depends on stage 2)")
    print("  analysis_tasks = build_analysis_tasks(sim_results)")
    print("  analysis_ids = pipeline.submit_batch_workflow(analysis_tasks)")
    print("  final_results = pipeline.wait_for_workflow(analysis_ids)")
    print()
    
    print("Benefits:")
    print("  - Clear workflow structure")
    print("  - Parallel execution within each stage")
    print("  - Dependency management between stages")
    print()


def example_8_resource_aware_submission():
    """Example 8: Resource-aware task submission."""
    print("=" * 70)
    print("Example 8: Resource-Aware Submission")
    print("=" * 70)
    print()
    
    cpu_count = multiprocessing.cpu_count()
    print(f"System CPU count: {cpu_count}")
    print()
    
    print("Recommended batch sizes by scenario:")
    print()
    
    print(f"1. CPU-bound tasks:")
    print(f"   batch_size = {cpu_count}")
    print(f"   (One task per CPU)")
    print()
    
    print(f"2. Mixed workload:")
    print(f"   batch_size = {cpu_count * 2}")
    print(f"   (2x oversubscription for better load balancing)")
    print()
    
    print(f"3. I/O-bound tasks:")
    print(f"   batch_size = {cpu_count * 4}")
    print(f"   (Higher parallelism since tasks wait for I/O)")
    print()
    
    print("Usage:")
    print("  task_ids = pipeline.submit_batch_workflow(")
    print(f"      tasks, batch_size={cpu_count * 2}")
    print("  )")
    print()


def main():
    """Run all parallel orchestration examples."""
    print("\n")
    print("#" * 70)
    print("# Parallel Orchestration Examples")
    print("#" * 70)
    print("\n")
    
    examples = [
        ("Batch Workflow Submission", example_1_batch_workflow),
        ("Parameter Sweep Workflow", example_2_parameter_sweep),
        ("Wait-for-Any Pattern", example_3_wait_for_any),
        ("Parallel Execution Statistics", example_4_parallel_execution_stats),
        ("Dynamic Load Balancing", example_5_dynamic_load_balancing),
        ("Adaptive Parameter Sweep", example_6_adaptive_parameter_sweep),
        ("Hierarchical Workflow", example_7_hierarchical_workflow),
        ("Resource-Aware Submission", example_8_resource_aware_submission),
    ]
    
    print("Available examples:")
    for i, (name, _) in enumerate(examples, 1):
        print(f"  {i}. {name}")
    print()
    
    # Run all examples
    for name, example_func in examples:
        try:
            example_func()
        except Exception as e:
            print(f"Example '{name}' encountered an error: {e}")
            import traceback
            traceback.print_exc()
        
        time.sleep(1)  # Brief pause between examples
    
    print("#" * 70)
    print("# Examples Complete")
    print("#" * 70)
    print()
    
    print("For more information, see:")
    print("  - PARALLEL_ORCHESTRATION.md - Comprehensive guide")
    print("  - TASK_PIPELINE.md - API documentation")
    print("  - ORCHESTRATION_GUIDE.md - General orchestration patterns")
    print()


if __name__ == '__main__':
    main()
