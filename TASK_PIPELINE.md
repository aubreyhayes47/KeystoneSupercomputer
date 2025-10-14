# Task Pipeline for Agent Workflow Orchestration

## Overview

The Task Pipeline module (`task_pipeline.py`) provides a high-level Python interface for submitting, monitoring, and managing simulation tasks via Celery. It simplifies agent-driven workflow orchestration by abstracting away the complexity of direct Celery interaction.

## Features

- **Task Submission**: Submit simulation tasks to the job queue with a simple API
- **Progress Monitoring**: Monitor task progress with callbacks and polling
- **Result Retrieval**: Retrieve task results with timeout support
- **Task Cancellation**: Cancel running or pending tasks
- **Workflow Management**: Submit and manage multi-task workflows (sequential or parallel)
- **Comprehensive Error Handling**: Graceful handling of timeouts, failures, and errors
- **Agent-Friendly**: Designed for easy integration with LangGraph agents

## Installation

The Task Pipeline requires Celery and Redis dependencies:

```bash
pip install celery[redis]==5.3.4 redis==4.6.0
```

These are already included in `requirements.txt`.

## Quick Start

### Basic Task Submission

```python
from task_pipeline import TaskPipeline

# Initialize the pipeline
pipeline = TaskPipeline()

# Submit a simulation task
task_id = pipeline.submit_task(
    tool="fenicsx",
    script="poisson.py",
    params={"mesh_size": 64}
)

# Wait for completion and get result
result = pipeline.wait_for_task(task_id, timeout=300)
print(f"Status: {result['status']}")
```

### Monitoring Task Progress

```python
# Define a callback for progress updates
def on_progress(status):
    if status['state'] == 'RUNNING':
        print(f"Progress: {status.get('progress', 0)}%")
    elif status['ready']:
        print(f"Task completed: {status['state']}")

# Monitor task with callback
pipeline.monitor_task(task_id, callback=on_progress, poll_interval=2)
```

### Parallel Workflow

```python
# Define multiple tasks
tasks = [
    {"tool": "fenicsx", "script": "poisson.py", "params": {"mesh_size": 32}},
    {"tool": "lammps", "script": "example.lammps", "params": {}},
    {"tool": "openfoam", "script": "example_cavity.py", "params": {}},
]

# Submit all tasks in parallel
task_ids = pipeline.submit_workflow(tasks, sequential=False)

# Wait for all to complete
workflow_status = pipeline.wait_for_workflow(task_ids, timeout=600)
print(f"Completed: {workflow_status['completed']}/{workflow_status['total']}")
```

### Sequential Workflow

```python
# Submit tasks sequentially (each waits for previous to complete)
task_ids = pipeline.submit_workflow(tasks, sequential=True)
```

## API Reference

### TaskPipeline Class

#### `__init__()`

Initialize the task pipeline.

```python
pipeline = TaskPipeline()
```

#### `health_check() -> Dict[str, Any]`

Check if the Celery worker is healthy and responding.

**Returns**: Dictionary with health status information

**Raises**: Exception if worker is not responding

```python
health = pipeline.health_check()
print(health['status'])  # 'healthy'
```

#### `list_available_simulations() -> Dict[str, Any]`

List all available simulation tools and scripts.

**Returns**: Dictionary with available tools and their configurations

```python
simulations = pipeline.list_available_simulations()
for tool, info in simulations['tools'].items():
    print(f"{tool}: {info['description']}")
```

#### `submit_task(tool: str, script: str, params: Optional[Dict] = None) -> str`

Submit a simulation task to the job queue.

**Parameters**:
- `tool`: Simulation tool name (fenicsx, lammps, openfoam)
- `script`: Script filename to execute
- `params`: Optional parameters for the simulation

**Returns**: Task ID (string)

```python
task_id = pipeline.submit_task("fenicsx", "poisson.py", {"mesh_size": 64})
```

#### `get_task_status(task_id: str) -> Dict[str, Any]`

Get the current status of a task.

**Parameters**:
- `task_id`: The task ID returned by submit_task()

**Returns**: Dictionary with task status information including:
- `state`: Current task state (PENDING, RUNNING, SUCCESS, FAILURE, etc.)
- `progress`: Progress percentage if available
- `result`: Task result if completed
- `error`: Error information if failed

```python
status = pipeline.get_task_status(task_id)
print(f"State: {status['state']}, Ready: {status['ready']}")
```

#### `monitor_task(task_id: str, callback: Optional[Callable] = None, poll_interval: float = 2.0) -> None`

Monitor a task and call callback function with status updates.

**Parameters**:
- `task_id`: The task ID to monitor
- `callback`: Optional callback function that receives status dict
- `poll_interval`: How often to poll for updates (seconds)

```python
def on_update(status):
    print(f"Progress: {status.get('progress', 0)}%")

pipeline.monitor_task(task_id, callback=on_update)
```

#### `wait_for_task(task_id: str, timeout: Optional[float] = None) -> Dict[str, Any]`

Wait for a task to complete and return its result (blocking).

**Parameters**:
- `task_id`: The task ID to wait for
- `timeout`: Maximum time to wait in seconds (None = wait indefinitely)

**Returns**: Task result dictionary

**Raises**: TimeoutError if task doesn't complete within timeout

```python
result = pipeline.wait_for_task(task_id, timeout=300)
print(f"Status: {result['status']}")
```

#### `cancel_task(task_id: str) -> bool`

Cancel a running or pending task.

**Parameters**:
- `task_id`: The task ID to cancel

**Returns**: True if cancellation was successful, False otherwise

```python
if pipeline.cancel_task(task_id):
    print("Task cancelled")
```

#### `submit_workflow(tasks: List[Dict], sequential: bool = True) -> List[str]`

Submit multiple tasks as a workflow.

**Parameters**:
- `tasks`: List of task dictionaries, each containing:
  - `tool`: Simulation tool name
  - `script`: Script filename
  - `params`: Optional parameters
- `sequential`: If True, wait for each task to complete before starting next; if False, submit all in parallel

**Returns**: List of task IDs

```python
tasks = [
    {"tool": "fenicsx", "script": "poisson.py", "params": {"mesh_size": 32}},
    {"tool": "lammps", "script": "example.lammps", "params": {}},
]
task_ids = pipeline.submit_workflow(tasks, sequential=True)
```

#### `get_workflow_status(task_ids: List[str]) -> Dict[str, Any]`

Get the status of all tasks in a workflow.

**Parameters**:
- `task_ids`: List of task IDs from submit_workflow()

**Returns**: Dictionary with overall workflow status and individual task statuses

```python
workflow_status = pipeline.get_workflow_status(task_ids)
print(f"{workflow_status['completed']}/{workflow_status['total']} completed")
```

#### `wait_for_workflow(task_ids: List[str], timeout: Optional[float] = None, callback: Optional[Callable] = None, poll_interval: float = 2.0) -> Dict[str, Any]`

Wait for all tasks in a workflow to complete.

**Parameters**:
- `task_ids`: List of task IDs to wait for
- `timeout`: Maximum time to wait in seconds
- `callback`: Optional callback function for status updates
- `poll_interval`: How often to check workflow status (seconds)

**Returns**: Dictionary with final workflow status and all results

```python
def on_update(status):
    print(f"Progress: {status['completed']}/{status['total']}")

results = pipeline.wait_for_workflow(task_ids, timeout=600, callback=on_update)
```

#### `cleanup()`

Clean up internal task tracking. Task results remain available via Redis.

```python
pipeline.cleanup()
```

### TaskStatus Class

Constants for task states:

- `TaskStatus.PENDING`: Task waiting in queue
- `TaskStatus.RUNNING`: Task being executed
- `TaskStatus.SUCCESS`: Task completed successfully
- `TaskStatus.FAILURE`: Task failed
- `TaskStatus.TIMEOUT`: Task timed out
- `TaskStatus.ERROR`: Task encountered an error
- `TaskStatus.CANCELLED`: Task was cancelled

## Examples

See `example_task_pipeline.py` for comprehensive examples including:

1. Basic task submission and monitoring
2. Parallel workflow submission
3. Sequential workflow submission
4. Task cancellation
5. Manual status polling

Run the examples:

```bash
cd src/agent
python3 example_task_pipeline.py
```

## Integration with Agents

The Task Pipeline is designed for easy integration with LangGraph agents:

```python
from task_pipeline import TaskPipeline
from agent_state import AgentState

# In your agent node
def simulation_node(state: AgentState):
    pipeline = TaskPipeline()
    
    # Extract simulation parameters from state
    params = state['simulation_params']
    
    # Submit task
    task_id = pipeline.submit_task(
        tool=params['tool'],
        script=params['script'],
        params=params.get('params', {})
    )
    
    # Wait for result
    result = pipeline.wait_for_task(task_id, timeout=600)
    
    # Update state with results
    return {
        **state,
        'artifact_paths': result.get('artifacts', []),
        'messages': state['messages'] + [
            SystemMessage(content=f"Simulation completed: {result['status']}")
        ]
    }
```

## Comparison with Direct Celery Usage

### Before (Direct Celery):

```python
from celery_app import run_simulation_task
import time

# Submit task
task = run_simulation_task.delay("fenicsx", "poisson.py", {"mesh_size": 64})

# Manual polling
while not task.ready():
    if task.state == 'RUNNING':
        meta = task.info
        if isinstance(meta, dict) and 'progress' in meta:
            print(f"Progress: {meta['progress']}%")
    time.sleep(2)

# Get result
result = task.get(timeout=300)
```

### After (Task Pipeline):

```python
from task_pipeline import TaskPipeline

pipeline = TaskPipeline()

# Submit and monitor with callback
task_id = pipeline.submit_task("fenicsx", "poisson.py", {"mesh_size": 64})
result = pipeline.wait_for_task(task_id, timeout=300)
```

## Architecture

```
┌─────────────────┐
│  Agent / User   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  TaskPipeline   │  ← High-level API
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   celery_app    │  ← Celery tasks
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Celery Worker  │  ← Background processing
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Docker Compose  │  ← Simulation execution
└─────────────────┘
```

## Testing

Run the unit tests:

```bash
cd src/agent
python3 test_task_pipeline.py
```

The tests validate:
- TaskPipeline instantiation
- Method availability
- TaskStatus constants
- Cleanup functionality
- Workflow validation

## Requirements

- Python 3.8+
- Celery 5.3.4+
- Redis 4.6.0+
- Running Redis server
- Running Celery worker

## Starting Services

Before using the Task Pipeline, ensure Redis and Celery worker are running:

```bash
# Start Redis and Celery worker
docker compose up -d redis celery-worker

# Verify worker is running
docker compose ps celery-worker

# Check worker logs
docker compose logs -f celery-worker
```

## Troubleshooting

### Connection Errors

If you get connection errors, ensure Redis is running:

```bash
docker compose ps redis
docker compose exec redis redis-cli ping  # Should return PONG
```

### Worker Not Processing Tasks

Restart the Celery worker:

```bash
docker compose restart celery-worker
docker compose logs -f celery-worker
```

### Task Stuck in PENDING

Check that the worker is running and connected to Redis:

```bash
# Check worker status
docker compose ps celery-worker

# Check Redis connection
docker compose exec redis redis-cli llen celery
```

## Future Enhancements

Planned features for future versions:

- Task priority support
- Task chaining and dependencies
- Progress callbacks with more granular updates
- Task result caching
- Workflow templates
- Integration with LangGraph checkpointing
- Automatic retry logic
- Task scheduling
- Performance metrics

## See Also

- [CELERY_QUICK_REFERENCE.md](CELERY_QUICK_REFERENCE.md) - Celery command reference
- [DOCKER_COMPOSE.md](DOCKER_COMPOSE.md) - Docker Compose documentation
- `src/celery_app.py` - Low-level Celery task definitions
- `src/agent/example_job_submission.py` - Direct Celery usage example

## License

Part of the Keystone Supercomputer project.
