#!/usr/bin/env python3
"""
Example: Complete Parameter Sweep Workflow
===========================================

A comprehensive example demonstrating a complete parameter sweep workflow
with parallel execution, progress monitoring, and result analysis.

This example shows how to:
1. Define a parameter sweep
2. Submit tasks with batch processing
3. Monitor parallel execution
4. Analyze results and performance
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from task_pipeline import TaskPipeline


def main():
    """Run a complete parameter sweep example."""
    print("=" * 70)
    print("Complete Parameter Sweep Workflow Example")
    print("=" * 70)
    print()
    
    # Initialize pipeline
    pipeline = TaskPipeline()
    
    # Define parameter grid for convergence study
    param_grid = {
        'mesh_size': [16, 32, 64, 128],
        'tolerance': [0.01, 0.001]
    }
    
    print("Step 1: Define parameter grid")
    print("-" * 70)
    for param, values in param_grid.items():
        print(f"  {param}: {values}")
    
    # Calculate total combinations
    total_combinations = 1
    for values in param_grid.values():
        total_combinations *= len(values)
    print(f"\n  Total combinations: {total_combinations}")
    print()
    
    # Define progress callback
    batch_count = [0]
    
    def on_batch_progress(info):
        batch_count[0] += 1
        print(f"  Batch {info['batch_num']}: "
              f"Submitted {info['batch_size']} tasks "
              f"({info['submitted']}/{info['total']} total)")
    
    print("Step 2: Submit parameter sweep")
    print("-" * 70)
    
    try:
        task_ids = pipeline.parameter_sweep(
            tool='fenicsx',
            script='poisson.py',
            param_grid=param_grid,
            callback=on_batch_progress
        )
        
        print(f"\n✓ Successfully submitted {len(task_ids)} tasks")
        print(f"  Submitted in {batch_count[0]} batches")
        print()
        
    except Exception as e:
        print(f"✗ Submission failed: {e}")
        print("\nNote: This requires a running Redis + Celery worker")
        print("Start with: docker compose up -d redis celery-worker")
        return
    
    print("Step 3: Monitor workflow execution")
    print("-" * 70)
    print("In a real workflow, you would monitor progress:")
    print()
    print("```python")
    print("def on_workflow_progress(status):")
    print("    print(f\"Progress: {status['completed']}/{status['total']}\")")
    print("    print(f\"Running: {status['running']}, Failed: {status['failed']}\")")
    print()
    print("results = pipeline.wait_for_workflow(")
    print("    task_ids,")
    print("    callback=on_workflow_progress,")
    print("    poll_interval=5,")
    print("    timeout=3600")
    print(")")
    print("```")
    print()
    
    print("Step 4: Analyze results")
    print("-" * 70)
    print("After workflow completes:")
    print()
    print("```python")
    print("# Get parallel execution statistics")
    print("stats = pipeline.get_parallel_execution_stats(task_ids)")
    print()
    print("print(f\"Parallel Performance:\")")
    print("print(f\"  Speedup: {stats['speedup']:.2f}x\")")
    print("print(f\"  Efficiency: {stats['efficiency']:.2%}\")")
    print("print(f\"  Avg duration: {stats['avg_duration']:.2f}s\")")
    print()
    print("# Analyze individual results")
    print("for task_id in task_ids:")
    print("    status = pipeline.get_task_status(task_id)")
    print("    if status['successful']:")
    print("        result = status['result']")
    print("        params = result['params']")
    print("        duration = result.get('duration_seconds', 0)")
    print("        print(f\"Params {params}: {duration:.2f}s\")")
    print("```")
    print()
    
    print("Step 5: Find optimal parameters")
    print("-" * 70)
    print("Example analysis to find best parameters:")
    print()
    print("```python")
    print("best_result = None")
    print("best_error = float('inf')")
    print()
    print("for task_id in task_ids:")
    print("    status = pipeline.get_task_status(task_id)")
    print("    if status['successful']:")
    print("        result = status['result']")
    print("        error = result.get('error_norm', 0)")
    print("        if error < best_error:")
    print("            best_error = error")
    print("            best_result = result")
    print()
    print("print(f\"Best parameters: {best_result['params']}\")")
    print("print(f\"Error: {best_error}\")")
    print("```")
    print()
    
    print("=" * 70)
    print("Example Complete!")
    print("=" * 70)
    print()
    print("Summary:")
    print(f"  - Defined parameter grid with {total_combinations} combinations")
    print(f"  - Submitted tasks using batch workflow")
    print("  - Demonstrated progress monitoring pattern")
    print("  - Showed result analysis approach")
    print("  - Illustrated parameter optimization")
    print()
    print("For more examples, see:")
    print("  - example_parallel_orchestration.py")
    print("  - PARALLEL_ORCHESTRATION.md")
    print()


if __name__ == '__main__':
    main()
