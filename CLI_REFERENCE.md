# CLI Reference - Workflow Submission and Monitoring

## Overview

The Keystone Supercomputer CLI provides a command-line interface for submitting and monitoring simulation workflows. The CLI leverages the `TaskPipeline` module to provide agent-friendly workflow orchestration.

## Installation

The CLI requires the following dependencies (already in `requirements.txt`):

```bash
pip install -r requirements.txt
```

## Quick Start

```bash
# Check worker health
cd src/agent
python3 cli.py health

# List available simulation tools
python3 cli.py list-tools

# Submit a single simulation task
python3 cli.py submit fenicsx poisson.py

# Submit with parameters and wait for completion
python3 cli.py submit fenicsx poisson.py -p '{"mesh_size": 64}' --wait

# Check task status
python3 cli.py status <task-id>

# Monitor task until completion
python3 cli.py status <task-id> --monitor

# Submit a workflow from file
python3 cli.py submit-workflow workflow.json --parallel --wait

# Cancel a task
python3 cli.py cancel <task-id>
```

## Command Reference

### `health`

Check the health of the Celery worker.

**Usage:**
```bash
python3 cli.py health
```

**Example Output:**
```
✓ Worker is healthy
Status: healthy
Message: Worker is ready to process tasks
```

### `list-tools`

List all available simulation tools and their scripts.

**Usage:**
```bash
python3 cli.py list-tools
```

**Example Output:**
```
Available Simulation Tools:

fenicsx:
  Description: Finite Element Method simulations
  Scripts: poisson.py

lammps:
  Description: Molecular Dynamics simulations
  Scripts: example.lammps

openfoam:
  Description: Computational Fluid Dynamics simulations
  Scripts: example_cavity.py
```

### `submit`

Submit a simulation task to the job queue.

**Usage:**
```bash
python3 cli.py submit <TOOL> <SCRIPT> [OPTIONS]
```

**Arguments:**
- `TOOL`: Simulation tool name (e.g., fenicsx, lammps, openfoam)
- `SCRIPT`: Script filename to execute

**Options:**
- `-p, --params TEXT`: JSON string of parameters (default: `{}`)
- `--wait / --no-wait`: Wait for task to complete (default: no-wait)
- `-t, --timeout INTEGER`: Timeout in seconds when waiting (default: 300)

**Examples:**

Basic submission:
```bash
python3 cli.py submit fenicsx poisson.py
```

With parameters:
```bash
python3 cli.py submit fenicsx poisson.py -p '{"mesh_size": 64}'
```

Wait for completion:
```bash
python3 cli.py submit fenicsx poisson.py --wait --timeout 600
```

With parameters and wait:
```bash
python3 cli.py submit fenicsx poisson.py -p '{"mesh_size": 128}' --wait
```

**Example Output:**
```
Submitting fenicsx simulation: poisson.py
Parameters: {'mesh_size': 64}
✓ Task submitted: abc123-def456-task-id

Use 'cli.py status abc123-def456-task-id' to check the status
```

### `status`

Check the status of a submitted task.

**Usage:**
```bash
python3 cli.py status <TASK_ID> [OPTIONS]
```

**Arguments:**
- `TASK_ID`: The task ID returned from submit command

**Options:**
- `-m, --monitor`: Monitor task until completion
- `-i, --interval INTEGER`: Polling interval in seconds (default: 2)

**Examples:**

Check status once:
```bash
python3 cli.py status abc123-def456-task-id
```

Monitor until completion:
```bash
python3 cli.py status abc123-def456-task-id --monitor
```

Monitor with custom interval:
```bash
python3 cli.py status abc123-def456-task-id -m -i 5
```

**Example Output (single check):**
```
Task ID: abc123-def456-task-id
State: RUNNING
Ready: False
Progress: 45%
Tool: fenicsx
Script: poisson.py
```

**Example Output (monitoring):**
```
Monitoring task abc123-def456-task-id...
Press Ctrl+C to stop monitoring

[14:23:45] State: RUNNING, Ready: False
  Progress: 25%
[14:23:47] State: RUNNING, Ready: False
  Progress: 50%
[14:23:49] State: SUCCESS, Ready: True

✓ Task completed successfully!
Artifacts: ['/data/output/result.png']
```

### `cancel`

Cancel a running or pending task.

**Usage:**
```bash
python3 cli.py cancel <TASK_ID>
```

**Arguments:**
- `TASK_ID`: The task ID to cancel

**Example:**
```bash
python3 cli.py cancel abc123-def456-task-id
```

**Example Output:**
```
Cancelling task abc123-def456-task-id...
✓ Task cancelled successfully
```

### `submit-workflow`

Submit multiple tasks as a workflow from a JSON file.

**Usage:**
```bash
python3 cli.py submit-workflow <WORKFLOW_FILE> [OPTIONS]
```

**Arguments:**
- `WORKFLOW_FILE`: Path to JSON workflow file

**Options:**
- `--sequential / --parallel`: Run tasks sequentially or in parallel (default: sequential)
- `--wait / --no-wait`: Wait for workflow to complete (default: no-wait)
- `-t, --timeout INTEGER`: Timeout in seconds when waiting (default: 600)

**Workflow File Format:**

The workflow file should be a JSON array of task objects:

```json
[
  {
    "tool": "fenicsx",
    "script": "poisson.py",
    "params": {
      "mesh_size": 32
    }
  },
  {
    "tool": "lammps",
    "script": "example.lammps",
    "params": {}
  },
  {
    "tool": "openfoam",
    "script": "example_cavity.py",
    "params": {}
  }
]
```

Each task object must have:
- `tool` (required): Simulation tool name
- `script` (required): Script filename
- `params` (optional): Parameters dictionary

**Examples:**

Submit workflow (no wait):
```bash
python3 cli.py submit-workflow workflow.json
```

Submit workflow in parallel and wait:
```bash
python3 cli.py submit-workflow workflow.json --parallel --wait
```

Submit workflow sequentially with custom timeout:
```bash
python3 cli.py submit-workflow workflow.json --sequential --wait --timeout 1200
```

**Example Output:**
```
Submitting workflow with 3 tasks (parallel)...
✓ Workflow submitted: 3 tasks
  Task 1: task-id-1
  Task 2: task-id-2
  Task 3: task-id-3

Waiting for workflow to complete (timeout: 600s)...
Progress: 0/3 completed, 3 running, 0 failed
Progress: 1/3 completed, 2 running, 0 failed
Progress: 2/3 completed, 1 running, 0 failed
Progress: 3/3 completed, 0 running, 0 failed

✓ Workflow completed!
Total tasks: 3
Completed: 3
Failed: 0
```

### `workflow-status`

Check the status of multiple tasks in a workflow.

**Usage:**
```bash
python3 cli.py workflow-status <TASK_ID>...
```

**Arguments:**
- `TASK_IDS`: One or more task IDs separated by spaces

**Example:**
```bash
python3 cli.py workflow-status task-id-1 task-id-2 task-id-3
```

**Example Output:**
```
Workflow Status:
Total tasks: 3
Completed: 2
Failed: 0
Running: 1
Pending: 0
All complete: False

Individual Task Status:
  task-id-1...: SUCCESS (Ready: True)
  task-id-2...: SUCCESS (Ready: True)
  task-id-3...: RUNNING (Ready: False)
```

### `job-history`

Display job execution history with resource usage and outcomes.

**Usage:**
```bash
python3 cli.py job-history [OPTIONS]
```

**Options:**
- `--limit, -l INTEGER`: Number of jobs to show (default: 10)
- `--tool, -t TEXT`: Filter by tool name (fenicsx, lammps, openfoam)
- `--status, -s TEXT`: Filter by status (success, failed, timeout, error)

**Examples:**
```bash
# Show last 10 jobs
python3 cli.py job-history

# Show last 20 jobs
python3 cli.py job-history --limit 20

# Show only failed fenicsx jobs
python3 cli.py job-history --tool fenicsx --status failed
```

**Example Output:**
```
Job History (showing 3 jobs):

1. Task: 3f8a21b2c4d5...
   Tool: fenicsx, Script: poisson.py
   Status: SUCCESS
   Started: 2025-10-15T10:30:00.000000
   Duration: 330.12s
   CPU Time: 297.79s (user: 285.45s, system: 12.34s)
   Memory Peak: 2048.56 MB

2. Task: 7b9e3f1a8c2d...
   Tool: lammps, Script: example.lammps
   Status: FAILED
   Started: 2025-10-15T10:25:00.000000
   Duration: 45.67s
   CPU Time: 42.33s (user: 40.12s, system: 2.21s)
   Memory Peak: 512.34 MB
   Error: Simulation failed with non-zero exit code...
```

### `job-stats`

Display aggregate statistics for all jobs.

**Usage:**
```bash
python3 cli.py job-stats
```

**Example Output:**
```
Job Statistics Summary:

Overall:
  Total Jobs: 15
  Successful: 12 (80.0%)
  Failed: 3
  Success Rate: 80.0%

Resource Usage:
  Total CPU Time: 4523.45s
  Total Duration: 5234.67s
  Average Duration: 348.98s

By Tool:
  fenicsx:
    Jobs: 8
    Successful: 7 (87.5%)
    Failed: 1
    Total Duration: 2876.34s
  lammps:
    Jobs: 4
    Successful: 3 (75.0%)
    Failed: 1
    Total Duration: 1456.78s
  openfoam:
    Jobs: 3
    Successful: 2 (66.67%)
    Failed: 1
    Total Duration: 901.55s
```

### `job-details`

Show detailed information for a specific job including resource usage and parameters.

**Usage:**
```bash
python3 cli.py job-details <TASK_ID>
```

**Arguments:**
- `TASK_ID`: Task identifier to query

**Example:**
```bash
python3 cli.py job-details 3f8a21b2c4d5e6f7a8b9c0d1e2f3a4b5
```

**Example Output:**
```
Job Details: 3f8a21b2c4d5e6f7a8b9c0d1e2f3a4b5

Basic Information:
  Tool: fenicsx
  Script: poisson.py
  Status: SUCCESS
  Return Code: 0

Timing:
  Started: 2025-10-15T10:30:00.000000
  Ended: 2025-10-15T10:35:30.123456
  Duration: 330.12s

Parameters:
  {
    "mesh_size": 64,
    "iterations": 1000
  }

Resource Usage:
  CPU User Time: 285.45s
  CPU System Time: 12.34s
  CPU Total Time: 297.79s
  Memory Peak: 2048.56 MB
```

### `ask`

Send a message to the LLM agent for conversational interaction.

**Usage:**
```bash
python3 cli.py ask "your message here"
```

**Example:**
```bash
python3 cli.py ask "What simulation tools are available?"
```

**Note:** This command requires an Ollama server running at `http://127.0.0.1:11434` with the `llama3:8b` model (or modify the model in `cli.py`).

## Workflow Examples

### Example 1: Simple Task Submission

```bash
# Submit a single task and get task ID
python3 cli.py submit fenicsx poisson.py -p '{"mesh_size": 64}'

# Output: Task ID: abc123-task-id

# Check status
python3 cli.py status abc123-task-id
```

### Example 2: Monitor Task Progress

```bash
# Submit and monitor in real-time
python3 cli.py submit fenicsx poisson.py --wait
```

### Example 3: Parallel Workflow

Create `parallel_workflow.json`:
```json
[
  {"tool": "fenicsx", "script": "poisson.py", "params": {"mesh_size": 32}},
  {"tool": "lammps", "script": "example.lammps", "params": {}},
  {"tool": "openfoam", "script": "example_cavity.py", "params": {}}
]
```

Submit and wait:
```bash
python3 cli.py submit-workflow parallel_workflow.json --parallel --wait
```

### Example 4: Sequential Workflow

```bash
# Same workflow file, but run sequentially
python3 cli.py submit-workflow parallel_workflow.json --sequential --wait
```

### Example 5: Background Workflow with Status Checks

```bash
# Submit workflow without waiting
python3 cli.py submit-workflow workflow.json --parallel

# Output shows task IDs:
# Task 1: task-id-1
# Task 2: task-id-2
# Task 3: task-id-3

# Check overall workflow status
python3 cli.py workflow-status task-id-1 task-id-2 task-id-3

# Monitor individual tasks
python3 cli.py status task-id-1 --monitor
```

### Example 6: Cancel a Running Task

```bash
# Submit a long-running task
python3 cli.py submit fenicsx poisson.py -p '{"mesh_size": 256}'

# Output: Task ID: abc123-task-id

# Cancel it
python3 cli.py cancel abc123-task-id
```

## Integration with Services

### Prerequisites

Before using the CLI, ensure the following services are running:

```bash
# Start Redis and Celery worker
docker compose up -d redis celery-worker

# Check service status
docker compose ps
```

### Health Check

Always start with a health check to ensure the worker is ready:

```bash
python3 cli.py health
```

If the health check fails, the worker may not be running. Check with:

```bash
docker compose logs celery-worker
```

## Tips and Best Practices

1. **Always check health first**: Run `python3 cli.py health` before submitting tasks
2. **Use --wait for short tasks**: For quick simulations, use `--wait` to see results immediately
3. **Use background mode for long workflows**: Submit without `--wait` and check status periodically
4. **Monitor parallel workflows**: Use `workflow-status` to track multiple tasks at once
5. **Set appropriate timeouts**: Use `-t` option to set timeouts based on expected task duration
6. **Save workflow files**: Store complex workflows in JSON files for reusability
7. **Check logs on failure**: Use `docker compose logs celery-worker` to debug failed tasks

## Error Handling

### Connection Errors

If you see connection errors:
```
✗ Health check failed: [Errno 111] Connection refused
```

Solution:
```bash
# Start Redis and worker services
docker compose up -d redis celery-worker
```

### Invalid JSON Parameters

If you see JSON errors:
```
✗ Invalid JSON in params: ...
```

Solution: Ensure parameters are valid JSON with proper quotes:
```bash
# Correct:
python3 cli.py submit fenicsx poisson.py -p '{"mesh_size": 64}'

# Incorrect:
python3 cli.py submit fenicsx poisson.py -p {mesh_size: 64}
```

### Task Timeout

If tasks timeout:
```
✗ Task timed out after 300s
```

Solution: Increase timeout:
```bash
python3 cli.py submit fenicsx poisson.py --wait --timeout 600
```

---

## Benchmark Commands

The CLI includes commands for running performance benchmarks and comparing simulation performance across different hardware configurations.

### `benchmark run`

Run a performance benchmark for simulation tools.

**Usage:**
```bash
python3 cli.py benchmark run [OPTIONS]
```

**Options:**
- `--tool [fenicsx|lammps|openfoam|all]` - Simulation tool to benchmark (default: fenicsx)
- `--device [cpu|gpu|intel-gpu|all]` - Device type for benchmark (default: cpu)
- `--runs INTEGER` - Number of benchmark runs (default: 3)
- `--results-dir TEXT` - Directory for benchmark results

**Examples:**

Run CPU benchmark for FEniCSx:
```bash
python3 cli.py benchmark run --tool fenicsx --device cpu --runs 5
```

Run GPU benchmark for all tools:
```bash
python3 cli.py benchmark run --tool all --device gpu --runs 3
```

Compare CPU vs GPU for LAMMPS:
```bash
# Run CPU benchmark
python3 cli.py benchmark run --tool lammps --device cpu --runs 5

# Run GPU benchmark
python3 cli.py benchmark run --tool lammps --device gpu --runs 5
```

### `benchmark compare`

Compare two benchmark results to see performance differences.

**Usage:**
```bash
python3 cli.py benchmark compare BASELINE_ID COMPARISON_ID [OPTIONS]
```

**Arguments:**
- `BASELINE_ID` - Benchmark ID for baseline (e.g., fenicsx-cpu-20241015-120000)
- `COMPARISON_ID` - Benchmark ID to compare against baseline

**Options:**
- `--results-dir TEXT` - Directory for benchmark results

**Example:**
```bash
python3 cli.py benchmark compare fenicsx-cpu-20241015-120000 fenicsx-gpu-20241015-120500
```

**Output:**
```
======================================================================
Benchmark Comparison
======================================================================

Baseline: fenicsx-cpu-20241015-120000
  Device: cpu
  Duration: 12.345s

Comparison: fenicsx-gpu-20241015-120500
  Device: gpu
  Duration: 3.456s

Results:
  Speedup: 3.57x
  Time Saved: 8.889s
  Performance Change: -72.00%
======================================================================
```

### `benchmark report`

Generate a comprehensive markdown report of all benchmark results.

**Usage:**
```bash
python3 cli.py benchmark report [OPTIONS]
```

**Options:**
- `--results-dir TEXT` - Directory for benchmark results
- `--output TEXT` - Output file for report (default: BENCHMARK_REPORT.md)

**Example:**
```bash
python3 cli.py benchmark report --output MY_BENCHMARK_REPORT.md
```

**Output:**
```
✓ Report generated: /tmp/keystone_benchmarks/BENCHMARK_REPORT.md

Report summary:
  Total benchmarks: 6
  Tools tested: fenicsx, lammps, openfoam
    - fenicsx: 2 benchmarks
    - lammps: 2 benchmarks
    - openfoam: 2 benchmarks
```

### `benchmark list`

List all stored benchmark results.

**Usage:**
```bash
python3 cli.py benchmark list [OPTIONS]
```

**Options:**
- `--results-dir TEXT` - Directory for benchmark results

**Example:**
```bash
python3 cli.py benchmark list
```

**Output:**
```
======================================================================
Benchmark Results (6 total)
======================================================================

ID: fenicsx-cpu-20241015-120000
  Tool: fenicsx
  Device: cpu
  Duration: 12.345s
  Success Rate: 100.0%

ID: fenicsx-gpu-20241015-120500
  Tool: fenicsx
  Device: gpu
  Duration: 3.456s
  Success Rate: 100.0%

...
```

### Benchmark Workflow Example

Complete workflow for benchmarking and comparing performance:

```bash
# 1. Run CPU benchmark
python3 cli.py benchmark run --tool fenicsx --device cpu --runs 5

# Note the benchmark ID from output (e.g., fenicsx-cpu-20241015-120000)

# 2. Run GPU benchmark
python3 cli.py benchmark run --tool fenicsx --device gpu --runs 5

# Note the benchmark ID from output (e.g., fenicsx-gpu-20241015-120500)

# 3. Compare results
python3 cli.py benchmark compare fenicsx-cpu-20241015-120000 fenicsx-gpu-20241015-120500

# 4. Generate comprehensive report
python3 cli.py benchmark report

# 5. List all benchmarks
python3 cli.py benchmark list
```

For more information on benchmarking, see [BENCHMARK_GUIDE.md](BENCHMARK_GUIDE.md).

---

## Related Documentation

- [Task Pipeline API](TASK_PIPELINE.md) - Lower-level Python API
- [Docker Compose Setup](DOCKER_COMPOSE.md) - Service orchestration
- [Celery Quick Reference](CELERY_QUICK_REFERENCE.md) - Celery details
- [Benchmark Guide](BENCHMARK_GUIDE.md) - Performance benchmarking documentation

## Future Enhancements

Potential future CLI features:
- Interactive workflow builder
- Task result visualization
- Workflow templates and library
- Task history and replay
- Resource usage monitoring
- Multi-cluster support
