# Job Monitoring and Resource Tracking

## Overview

The Keystone Supercomputer includes comprehensive job monitoring and resource tracking for all simulation tasks executed through the Celery task queue. This system provides:

- **Resource Usage Tracking**: Monitor CPU time, memory consumption, and execution duration
- **Failure Monitoring**: Track job failures with detailed error information
- **Job History**: Persistent storage of all job outcomes
- **Statistics**: Aggregate statistics across all jobs and by simulation tool

## Features

### Resource Metrics

For every job, the following metrics are tracked:

- **CPU Time**: User and system CPU time in seconds
- **Memory**: Peak memory usage in MB
- **Duration**: Total execution time in seconds
- **Timestamps**: Start and end times (ISO 8601 format)

### Job Outcomes

All jobs are logged with their final status:

- `success`: Job completed successfully
- `failed`: Job failed with non-zero exit code
- `timeout`: Job exceeded time limit
- `error`: Job encountered an exception

### Persistent Storage

Job history is stored in `/tmp/keystone_jobs/jobs_history.jsonl` as newline-delimited JSON. Each entry includes:

```json
{
  "task_id": "abc-123-xyz",
  "tool": "fenicsx",
  "script": "poisson.py",
  "params": {"mesh_size": 64},
  "start_time": "2025-10-15T10:30:00.000000",
  "end_time": "2025-10-15T10:35:30.123456",
  "duration_seconds": 330.12,
  "status": "success",
  "returncode": 0,
  "resource_usage": {
    "cpu_user_seconds": 285.45,
    "cpu_system_seconds": 12.34,
    "cpu_total_seconds": 297.79,
    "memory_peak_mb": 2048.56
  },
  "error": null,
  "has_result": true
}
```

## CLI Usage

### View Job History

Display recent job executions with resource usage:

```bash
# Show last 10 jobs
python3 cli.py job-history

# Show last 20 jobs
python3 cli.py job-history --limit 20

# Filter by tool
python3 cli.py job-history --tool fenicsx

# Filter by status
python3 cli.py job-history --status failed
```

Example output:

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

### View Aggregate Statistics

Display summary statistics for all jobs:

```bash
python3 cli.py job-stats
```

Example output:

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

### View Job Details

Get detailed information for a specific job:

```bash
python3 cli.py job-details <task-id>
```

Example output:

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

## Python API

### Using JobMonitor Directly

```python
from job_monitor import JobMonitor

# Initialize monitor
monitor = JobMonitor()

# Start monitoring a job
monitor.start_monitoring(
    task_id="my-task-123",
    tool="fenicsx",
    script="poisson.py",
    params={"mesh_size": 64}
)

# ... execute job ...

# Stop monitoring and record outcome
job_stats = monitor.stop_monitoring(
    task_id="my-task-123",
    status="success",
    returncode=0
)

print(f"Duration: {job_stats['duration_seconds']}s")
print(f"CPU Time: {job_stats['resource_usage']['cpu_total_seconds']}s")
```

### Using Context Manager

```python
from job_monitor import get_monitor

monitor = get_monitor()

# Track job with context manager
with monitor.track_job("task-456", "lammps", "example.lammps", {}) as tracker:
    # Execute simulation
    result = run_simulation()
    
    # Optionally set status manually
    if result['returncode'] != 0:
        tracker.set_status("failed", returncode=result['returncode'], error=result['stderr'])
```

### Retrieving Job History

```python
from job_monitor import get_monitor

monitor = get_monitor()

# Get all jobs
all_jobs = monitor.get_job_history()

# Get last 10 jobs
recent_jobs = monitor.get_job_history(limit=10)

# Get specific job
job = monitor.get_job_stats("task-id-123")

# Get summary statistics
stats = monitor.get_summary_statistics()
print(f"Success rate: {stats['success_rate']}%")
print(f"Total CPU time: {stats['total_cpu_time_seconds']}s")
```

## Integration with Celery Tasks

The monitoring system is automatically integrated into all Celery simulation tasks. Every task execution is tracked without any changes to user code:

```python
from task_pipeline import TaskPipeline

pipeline = TaskPipeline()

# Submit task - monitoring happens automatically
task_id = pipeline.submit_task("fenicsx", "poisson.py", {"mesh_size": 64})

# Wait for completion
result = pipeline.wait_for_task(task_id)

# Result includes resource usage
print(f"Duration: {result['duration_seconds']}s")
print(f"CPU Time: {result['resource_usage']['cpu_total_seconds']}s")
print(f"Memory Peak: {result['resource_usage']['memory_peak_mb']} MB")
```

## Workflow Monitoring

When submitting workflows, all tasks are monitored individually:

```python
from task_pipeline import TaskPipeline

pipeline = TaskPipeline()

# Submit workflow
tasks = [
    {"tool": "fenicsx", "script": "poisson.py", "params": {"mesh_size": 32}},
    {"tool": "lammps", "script": "example.lammps", "params": {}},
]

task_ids = pipeline.submit_workflow(tasks, sequential=True)

# Wait for completion
results = pipeline.wait_for_workflow(task_ids)

# View history for all workflow tasks
from job_monitor import get_monitor
monitor = get_monitor()

for task_id in task_ids:
    job = monitor.get_job_stats(task_id)
    print(f"{job['tool']}: {job['status']} - {job['duration_seconds']}s")
```

## Logging

All job outcomes are logged using Python's logging module:

- **INFO**: Successful job completions with duration and resource usage
- **WARNING**: Jobs that timeout
- **ERROR**: Failed jobs with return codes and error messages

Example log messages:

```
INFO - Starting job 3f8a21b2c4d5: tool=fenicsx, script=poisson.py, params={'mesh_size': 64}
INFO - Job 3f8a21b2c4d5 completed successfully - Duration: 330.12s, CPU: 297.79s
ERROR - Job 7b9e3f1a8c2d failed with return code 1 - Duration: 45.67s
WARNING - Job 9c8d7e6f5a4b timed out
```

## Configuration

### Custom Log Directory

By default, job history is stored in `/tmp/keystone_jobs`. To use a custom directory:

```python
from job_monitor import JobMonitor

monitor = JobMonitor(log_dir="/path/to/custom/logs")
```

### Environment Variables

The Celery worker uses the global monitor instance, which stores logs in `/tmp/keystone_jobs` by default. To customize:

1. Modify `celery_app.py` to pass a custom log directory
2. Or create a configuration file loaded by the worker

## Architecture

```
┌────────────────────┐
│   Celery Task      │
│  (run_simulation)  │
└─────────┬──────────┘
          │
          ▼
┌────────────────────┐
│   JobMonitor       │
│  - start_monitoring│
│  - stop_monitoring │
│  - track resources │
└─────────┬──────────┘
          │
          ▼
┌────────────────────┐
│ Persistent Storage │
│  jobs_history.jsonl│
└────────────────────┘
          │
          ▼
┌────────────────────┐
│   CLI Commands     │
│  - job-history     │
│  - job-stats       │
│  - job-details     │
└────────────────────┘
```

## Best Practices

### 1. Regular Monitoring

Periodically check job statistics to identify trends:

```bash
# Daily check
python3 cli.py job-stats

# Review recent failures
python3 cli.py job-history --status failed --limit 5
```

### 2. Resource Optimization

Use resource metrics to optimize simulations:

- Identify memory-intensive jobs
- Compare CPU efficiency across tools
- Detect abnormally long-running jobs

```python
from job_monitor import get_monitor

monitor = get_monitor()
jobs = monitor.get_job_history()

# Find memory-intensive jobs
high_memory = [j for j in jobs if j['resource_usage']['memory_peak_mb'] > 4000]

# Find slow jobs
slow_jobs = [j for j in jobs if j['duration_seconds'] > 600]
```

### 3. Failure Analysis

Analyze failures to improve reliability:

```bash
# Review failed jobs
python3 cli.py job-history --status failed

# Get details for specific failures
python3 cli.py job-details <task-id>
```

### 4. Workflow Optimization

Compare sequential vs parallel execution:

```python
stats = monitor.get_summary_statistics()

# Calculate average duration by tool
for tool, tool_stats in stats['by_tool'].items():
    avg = tool_stats['total_duration'] / tool_stats['count']
    print(f"{tool}: avg {avg:.2f}s per job")
```

## Troubleshooting

### Job History Not Found

If `job-history` returns no results:

1. Check if `/tmp/keystone_jobs/jobs_history.jsonl` exists
2. Verify Celery worker has write permissions
3. Ensure jobs have been executed since monitoring was enabled

### Inaccurate Resource Metrics

Resource tracking uses `psutil` to monitor the Celery worker process. Metrics may be inaccurate if:

- Docker containers are resource-constrained
- Jobs are very short-lived (< 1 second)
- Multiple jobs run concurrently in the same worker

### Large Log Files

The job history file grows with each job. To manage size:

```bash
# Archive old logs
mv /tmp/keystone_jobs/jobs_history.jsonl /tmp/keystone_jobs/jobs_history.$(date +%Y%m%d).jsonl

# Or rotate with logrotate
```

## Future Enhancements

Planned improvements:

- [ ] Docker container resource limits tracking
- [ ] Real-time resource monitoring dashboards
- [ ] Automatic alerting for failures
- [ ] Historical trend analysis
- [ ] Integration with Prometheus/Grafana
- [ ] Per-task resource limits and quotas
- [ ] Cost estimation based on resource usage

## See Also

- [TASK_PIPELINE.md](TASK_PIPELINE.md) - Task Pipeline documentation
- [CELERY_QUICK_REFERENCE.md](CELERY_QUICK_REFERENCE.md) - Celery commands
- [CLI_REFERENCE.md](CLI_REFERENCE.md) - Complete CLI documentation
- `src/job_monitor.py` - Monitor implementation
- `src/test_job_monitor.py` - Monitor tests
