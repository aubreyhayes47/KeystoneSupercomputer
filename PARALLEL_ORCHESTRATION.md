# Parallel Agent Orchestration Patterns

## Overview

This guide covers parallel agent execution and task scheduling patterns for the Keystone Supercomputer. The parallel orchestration system enables efficient multi-core and multi-node workflow execution through enhanced TaskPipeline capabilities and dedicated parallel execution modules.

**New Features:**
- **Batch workflow submission** - Submit multiple tasks efficiently
- **Parameter sweep workflows** - Automatically generate and run parameter combinations
- **Parallel execution stats** - Track speedup and efficiency
- **Resource-aware scheduling** - Optimize task distribution
- **Wait-for-any semantics** - React to first completed task
- **ProcessPool and ThreadPool support** - Choose execution model

---

## Table of Contents

- [Quick Start](#quick-start)
- [Parallel Execution Models](#parallel-execution-models)
- [Batch Workflow Submission](#batch-workflow-submission)
- [Parameter Sweep Workflows](#parameter-sweep-workflows)
- [Advanced Patterns](#advanced-patterns)
- [Performance Monitoring](#performance-monitoring)
- [API Reference](#api-reference)
- [Best Practices](#best-practices)

---

## Quick Start

### Basic Parallel Workflow

```python
from task_pipeline import TaskPipeline

pipeline = TaskPipeline()

# Define tasks to run in parallel
tasks = [
    {"tool": "fenicsx", "script": "poisson.py", "params": {"mesh_size": 32}},
    {"tool": "fenicsx", "script": "poisson.py", "params": {"mesh_size": 64}},
    {"tool": "fenicsx", "script": "poisson.py", "params": {"mesh_size": 128}},
]

# Submit all tasks in parallel (non-blocking submission)
task_ids = pipeline.submit_workflow(tasks, sequential=False)

# Monitor progress
def on_progress(status):
    print(f"Progress: {status['completed']}/{status['total']} completed")

results = pipeline.wait_for_workflow(task_ids, callback=on_progress)
```

### Parameter Sweep

```python
# Define parameter grid
param_grid = {
    'mesh_size': [16, 32, 64, 128],
    'time_steps': [100, 200, 500]
}

# Submit all combinations (4 × 3 = 12 tasks)
task_ids = pipeline.parameter_sweep(
    tool='fenicsx',
    script='poisson.py',
    param_grid=param_grid
)

# Wait for completion
results = pipeline.wait_for_workflow(task_ids, timeout=1800)

# Analyze parallel execution
stats = pipeline.get_parallel_execution_stats(task_ids)
print(f"Speedup: {stats['speedup']:.2f}x")
print(f"Efficiency: {stats['efficiency']:.2%}")
```

---

## Parallel Execution Models

### Celery-based Distributed Execution

The default execution model uses Celery with Redis for distributed task queueing. This approach:

- **Scales across multiple nodes** - Workers can run on different machines
- **Provides fault tolerance** - Tasks can be retried on failure
- **Enables priority queues** - Important tasks can jump the queue
- **Supports long-running tasks** - Hours or days of execution time

**Best for:** Production workflows, multi-node clusters, long-running simulations

```python
# Standard workflow submission uses Celery
task_ids = pipeline.submit_workflow(tasks, sequential=False)
```

### Local Parallel Execution

For local multi-core parallelism without Celery overhead, use the `ParallelExecutor`:

```python
from parallel_executor import ParallelExecutor

# Execute tasks using process pool
with ParallelExecutor(max_workers=4, use_processes=True) as executor:
    tasks = [
        {'id': 'task-1', 'func': my_function, 'args': (arg1,)},
        {'id': 'task-2', 'func': my_function, 'args': (arg2,)},
    ]
    results = executor.execute_parallel(tasks)
```

**Best for:** Quick local computations, development, testing

---

## Batch Workflow Submission

Batch workflow submission optimizes task submission by grouping tasks into batches:

### Basic Batch Submission

```python
# Submit 100 tasks in batches of 10
tasks = [
    {"tool": "fenicsx", "script": "poisson.py", "params": {"mesh_size": i}}
    for i in range(16, 116)
]

task_ids = pipeline.submit_batch_workflow(tasks, batch_size=10)
```

### With Progress Callback

```python
def on_batch_submitted(info):
    print(f"Batch {info['batch_num']}: "
          f"Submitted {info['submitted']}/{info['total']} tasks")

task_ids = pipeline.submit_batch_workflow(
    tasks,
    batch_size=10,
    callback=on_batch_submitted
)
```

### Auto-sizing Batches

```python
# Automatically determine batch size based on CPU count
task_ids = pipeline.submit_batch_workflow(tasks)  # batch_size=None
```

---

## Parameter Sweep Workflows

Parameter sweeps automatically generate and submit all parameter combinations:

### Single Parameter Sweep

```python
param_grid = {
    'mesh_size': [16, 32, 64, 128, 256]
}

# Submits 5 tasks
task_ids = pipeline.parameter_sweep(
    tool='fenicsx',
    script='poisson.py',
    param_grid=param_grid
)
```

### Multi-Parameter Sweep (Cartesian Product)

```python
param_grid = {
    'mesh_size': [16, 32, 64],        # 3 values
    'time_steps': [100, 200, 500],    # 3 values
    'tolerance': [0.01, 0.001]        # 2 values
}

# Submits 3 × 3 × 2 = 18 tasks
task_ids = pipeline.parameter_sweep(
    tool='fenicsx',
    script='poisson.py',
    param_grid=param_grid
)
```

### With Progress Tracking

```python
def on_sweep_progress(info):
    print(f"Sweep progress: Batch {info['batch_num']}, "
          f"{info['submitted']} tasks submitted")

task_ids = pipeline.parameter_sweep(
    tool='fenicsx',
    script='poisson.py',
    param_grid=param_grid,
    callback=on_sweep_progress
)
```

### Analyzing Sweep Results

```python
# Wait for all sweep tasks to complete
results = pipeline.wait_for_workflow(task_ids, timeout=3600)

# Get execution statistics
stats = pipeline.get_parallel_execution_stats(task_ids)

print(f"Total tasks: {stats['total_tasks']}")
print(f"Completed: {stats['completed']}")
print(f"Failed: {stats['failed']}")
print(f"Average duration: {stats['avg_duration']:.2f}s")
print(f"Parallel speedup: {stats['speedup']:.2f}x")
print(f"Efficiency: {stats['efficiency']:.2%}")

# Analyze individual results
for task_id in task_ids:
    status = pipeline.get_task_status(task_id)
    if status['ready'] and status['successful']:
        result = status['result']
        params = result.get('params', {})
        duration = result.get('duration_seconds', 0)
        print(f"Params {params}: {duration:.2f}s")
```

---

## Advanced Patterns

### Pattern 1: Wait for Any Task

React to the first task that completes:

```python
# Submit multiple tasks
task_ids = pipeline.submit_workflow(tasks, sequential=False)

# Wait for the first one to complete
first_result = pipeline.wait_for_any(task_ids, timeout=300)

print(f"First task completed: {first_result['task_id']}")
print(f"Status: {first_result['status']}")

# Optionally cancel remaining tasks
for task_id in task_ids:
    if task_id != first_result['task_id']:
        pipeline.cancel_task(task_id)
```

**Use cases:**
- Racing multiple algorithms to find fastest
- Early stopping when condition is met
- Competitive task scheduling

### Pattern 2: Progressive Result Analysis

Analyze results as they complete:

```python
task_ids = pipeline.submit_workflow(tasks, sequential=False)

completed = set()
while len(completed) < len(task_ids):
    # Wait for next completion
    result = pipeline.wait_for_any(
        [tid for tid in task_ids if tid not in completed],
        timeout=60
    )
    
    task_id = result['task_id']
    completed.add(task_id)
    
    # Analyze result immediately
    status = result['status']
    if status['successful']:
        process_result(status['result'])
    
    print(f"Progress: {len(completed)}/{len(task_ids)}")
```

### Pattern 3: Adaptive Parameter Sweep

Adjust parameters based on initial results:

```python
# Initial coarse sweep
initial_params = {'mesh_size': [16, 32, 64, 128]}
task_ids = pipeline.parameter_sweep('fenicsx', 'poisson.py', initial_params)
results = pipeline.wait_for_workflow(task_ids)

# Analyze convergence
best_mesh = analyze_convergence(results)

# Refined sweep around best value
refined_params = {
    'mesh_size': [best_mesh - 8, best_mesh, best_mesh + 8],
    'tolerance': [0.01, 0.001, 0.0001]
}
task_ids_2 = pipeline.parameter_sweep('fenicsx', 'poisson.py', refined_params)
results_2 = pipeline.wait_for_workflow(task_ids_2)
```

### Pattern 4: Hierarchical Workflow

Run tasks in stages with dependencies:

```python
# Stage 1: Preprocessing (parallel)
prep_tasks = [
    {"tool": "openfoam", "script": "mesh_gen.py", "params": {"size": i}}
    for i in [10, 20, 30]
]
prep_ids = pipeline.submit_batch_workflow(prep_tasks)
prep_results = pipeline.wait_for_workflow(prep_ids)

# Stage 2: Main simulation (parallel, based on stage 1)
sim_tasks = [
    {"tool": "fenicsx", "script": "solve.py", "params": {"mesh_id": i}}
    for i in range(len(prep_results['results']))
]
sim_ids = pipeline.submit_batch_workflow(sim_tasks)
sim_results = pipeline.wait_for_workflow(sim_ids)

# Stage 3: Analysis (parallel)
analysis_tasks = [
    {"tool": "fenicsx", "script": "analyze.py", "params": {"sim_id": i}}
    for i in range(len(sim_results['results']))
]
analysis_ids = pipeline.submit_batch_workflow(analysis_tasks)
final_results = pipeline.wait_for_workflow(analysis_ids)
```

### Pattern 5: Dynamic Load Balancing

Submit tasks dynamically based on completion rate:

```python
all_tasks = [...]  # Large list of tasks
task_queue = list(all_tasks)
active_tasks = {}
max_concurrent = 10

while task_queue or active_tasks:
    # Submit tasks up to max concurrent
    while len(active_tasks) < max_concurrent and task_queue:
        task = task_queue.pop(0)
        task_id = pipeline.submit_task(
            task['tool'],
            task['script'],
            task['params']
        )
        active_tasks[task_id] = task
    
    # Check for completions
    for task_id in list(active_tasks.keys()):
        status = pipeline.get_task_status(task_id)
        if status['ready']:
            print(f"Task {task_id} completed")
            del active_tasks[task_id]
    
    time.sleep(2)
```

---

## Performance Monitoring

### Real-time Monitoring

```python
def monitor_workflow(task_ids, poll_interval=5):
    """Monitor workflow with real-time stats."""
    start_time = time.time()
    
    while True:
        workflow_status = pipeline.get_workflow_status(task_ids)
        stats = pipeline.get_parallel_execution_stats(task_ids)
        
        elapsed = time.time() - start_time
        
        print(f"\nElapsed: {elapsed:.0f}s")
        print(f"Completed: {workflow_status['completed']}/{workflow_status['total']}")
        print(f"Running: {workflow_status['running']}")
        print(f"Failed: {workflow_status['failed']}")
        print(f"Current speedup: {stats['speedup']:.2f}x")
        
        if workflow_status['all_complete']:
            break
        
        time.sleep(poll_interval)

# Use with workflow
task_ids = pipeline.submit_workflow(tasks, sequential=False)
monitor_workflow(task_ids)
```

### Performance Analysis

```python
# After workflow completes
stats = pipeline.get_parallel_execution_stats(task_ids)

# Calculate various metrics
total_compute_time = stats['total_duration']
wall_clock_time = stats['max_duration']
speedup = stats['speedup']
efficiency = stats['efficiency']
parallelism = speedup / efficiency if efficiency > 0 else 0

print(f"""
Parallel Execution Report
========================
Total tasks: {stats['total_tasks']}
Successful: {stats['completed']}
Failed: {stats['failed']}

Timing:
  Total compute time: {total_compute_time:.2f}s
  Wall clock time: {wall_clock_time:.2f}s
  Average task time: {stats['avg_duration']:.2f}s

Performance:
  Speedup: {speedup:.2f}x
  Efficiency: {efficiency:.2%}
  Average parallelism: {parallelism:.1f} tasks
""")
```

---

## API Reference

### TaskPipeline Enhanced Methods

#### `submit_batch_workflow()`

```python
task_ids = pipeline.submit_batch_workflow(
    tasks,                  # List of task dictionaries
    batch_size=None,       # Batch size (default: CPU count)
    callback=None          # Callback for batch progress
)
```

**Parameters:**
- `tasks` - List of dicts with 'tool', 'script', 'params'
- `batch_size` - Number of tasks per batch (default: CPU count)
- `callback` - Function called with batch info dict

**Returns:** List of task IDs

#### `parameter_sweep()`

```python
task_ids = pipeline.parameter_sweep(
    tool,                  # Simulation tool name
    script,                # Script filename
    param_grid,            # Dict of param_name: [values]
    callback=None          # Progress callback
)
```

**Parameters:**
- `tool` - Tool name ('fenicsx', 'lammps', 'openfoam')
- `script` - Script filename
- `param_grid` - Dict mapping parameter names to value lists
- `callback` - Progress callback function

**Returns:** List of task IDs for all combinations

#### `wait_for_any()`

```python
result = pipeline.wait_for_any(
    task_ids,              # List of task IDs
    timeout=None           # Timeout in seconds
)
```

**Parameters:**
- `task_ids` - List of task IDs to monitor
- `timeout` - Maximum wait time (None = wait forever)

**Returns:** Dict with 'task_id' and 'status'

#### `get_parallel_execution_stats()`

```python
stats = pipeline.get_parallel_execution_stats(task_ids)
```

**Parameters:**
- `task_ids` - List of task IDs to analyze

**Returns:** Dict with:
- `total_tasks` - Total number of tasks
- `completed` - Number completed successfully
- `failed` - Number failed
- `running` - Number currently running
- `pending` - Number pending
- `total_duration` - Sum of all task durations
- `avg_duration` - Average task duration
- `max_duration` - Maximum task duration
- `speedup` - Parallel speedup factor
- `efficiency` - Parallel efficiency (0-1)

### ParallelExecutor

For local multi-core execution:

```python
from parallel_executor import ParallelExecutor

with ParallelExecutor(max_workers=4, use_processes=True) as executor:
    tasks = [
        {'id': 'task-1', 'func': function, 'args': (arg,), 'kwargs': {}}
    ]
    results = executor.execute_parallel(tasks, callback=callback)
```

### BatchProcessor

For parameter sweeps and batch operations:

```python
from parallel_executor import BatchProcessor

processor = BatchProcessor(max_workers=4)

# Parameter sweep
results = processor.parameter_sweep(func, param_dict, callback=callback)

# Batch execute
results = processor.batch_execute(func, items, callback=callback)
```

---

## Best Practices

### 1. Choose Appropriate Batch Size

```python
import multiprocessing

# Rule of thumb: 2-4x CPU count for good load balancing
cpu_count = multiprocessing.cpu_count()
batch_size = cpu_count * 2

task_ids = pipeline.submit_batch_workflow(tasks, batch_size=batch_size)
```

### 2. Monitor Long-Running Workflows

```python
# Use callbacks for visibility
def progress_callback(status):
    print(f"{status['completed']}/{status['total']} tasks completed")
    
    # Alert on failures
    if status['failed'] > 0:
        print(f"Warning: {status['failed']} tasks have failed!")

results = pipeline.wait_for_workflow(
    task_ids,
    callback=progress_callback,
    poll_interval=10  # Check every 10 seconds
)
```

### 3. Handle Failures Gracefully

```python
results = pipeline.wait_for_workflow(task_ids)

# Identify failed tasks
failed_tasks = []
for task_id, task_info in results['tasks'].items():
    if task_info['state'] == 'FAILURE':
        failed_tasks.append(task_id)

# Retry failed tasks
if failed_tasks:
    print(f"Retrying {len(failed_tasks)} failed tasks...")
    # Reconstruct task configs and resubmit
    retry_ids = pipeline.submit_batch_workflow(failed_task_configs)
```

### 4. Optimize Parameter Sweeps

```python
# Start with coarse sweep
coarse_params = {'mesh_size': [16, 64, 256]}
task_ids = pipeline.parameter_sweep('fenicsx', 'poisson.py', coarse_params)
results = pipeline.wait_for_workflow(task_ids)

# Analyze to find promising region
optimal_range = find_optimal_range(results)

# Then fine-grained sweep
fine_params = {'mesh_size': range(optimal_range[0], optimal_range[1], 4)}
task_ids = pipeline.parameter_sweep('fenicsx', 'poisson.py', fine_params)
```

### 5. Profile and Tune

```python
# Profile a small run first
small_tasks = tasks[:10]
task_ids = pipeline.submit_batch_workflow(small_tasks)
results = pipeline.wait_for_workflow(task_ids, timeout=300)

stats = pipeline.get_parallel_execution_stats(task_ids)

# Adjust based on efficiency
if stats['efficiency'] < 0.5:
    print("Low efficiency - consider reducing parallelism")
    max_workers = multiprocessing.cpu_count() // 2
elif stats['efficiency'] > 0.9:
    print("High efficiency - can increase parallelism")
    max_workers = multiprocessing.cpu_count() * 2
```

### 6. Set Appropriate Timeouts

```python
# Short tasks: tight timeout
short_task_ids = pipeline.submit_workflow(quick_tasks, sequential=False)
results = pipeline.wait_for_workflow(short_task_ids, timeout=300)  # 5 min

# Long tasks: generous timeout
long_task_ids = pipeline.submit_workflow(heavy_tasks, sequential=False)
results = pipeline.wait_for_workflow(long_task_ids, timeout=7200)  # 2 hours
```

---

## Related Documentation

- **[ORCHESTRATION_GUIDE.md](ORCHESTRATION_GUIDE.md)** - General orchestration guide
- **[TASK_PIPELINE.md](TASK_PIPELINE.md)** - TaskPipeline API documentation
- **[PARALLEL_SIMULATIONS.md](PARALLEL_SIMULATIONS.md)** - OpenMP/MPI parallelism
- **[PARALLEL_EXAMPLES.md](PARALLEL_EXAMPLES.md)** - Quick parallel examples
- **[RESOURCE_PROFILING.md](RESOURCE_PROFILING.md)** - Resource monitoring
- **[BENCHMARK_GUIDE.md](BENCHMARK_GUIDE.md)** - Performance benchmarking

---

## Examples

Complete example scripts demonstrating parallel orchestration:

- `src/agent/example_parallel_orchestration.py` - Comprehensive examples
- `src/agent/example_parameter_sweep.py` - Parameter sweep patterns
- `src/agent/example_adaptive_workflow.py` - Adaptive scheduling

Run examples:

```bash
cd src/agent
python3 example_parallel_orchestration.py
```

---

## Troubleshooting

### Problem: Low Speedup

**Symptoms:** Speedup << number of workers

**Solutions:**
1. Check task granularity - tasks may be too small
2. Reduce batch size if tasks are CPU-bound
3. Check for I/O bottlenecks
4. Monitor resource usage with profiler

### Problem: Tasks Queuing

**Symptoms:** Many tasks in PENDING state

**Solutions:**
1. Scale up Celery workers: `docker compose up -d --scale celery-worker=N`
2. Reduce concurrent task submission with smaller batch sizes
3. Check worker health: `python3 cli.py health`

### Problem: Memory Exhaustion

**Symptoms:** Tasks failing with memory errors

**Solutions:**
1. Reduce parallelism: use smaller batch sizes
2. Submit tasks more gradually using dynamic load balancing
3. Increase worker memory limits in docker-compose.yml
4. Use parameter sweeps with smaller parameter ranges

---

## Summary

The parallel orchestration system provides:

✓ **Batch workflow submission** for efficient task queueing  
✓ **Parameter sweep workflows** for automatic parameter exploration  
✓ **Parallel execution statistics** for performance analysis  
✓ **Wait-for-any semantics** for reactive scheduling  
✓ **Resource-aware patterns** for optimal utilization  
✓ **Comprehensive monitoring** for workflow visibility  

These capabilities enable sophisticated multi-core and multi-node workflow orchestration for scientific computing at scale.
