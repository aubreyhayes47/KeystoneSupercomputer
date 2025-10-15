# Testing the Job Monitoring Implementation

## Overview

This document provides instructions for testing the newly implemented job monitoring and resource tracking features.

## Prerequisites

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Ensure Redis and Celery worker are running (if testing with real jobs):
```bash
docker compose up -d redis celery-worker
```

## Unit Tests

Run the job monitor unit tests:

```bash
cd src
python3 test_job_monitor.py
```

Expected output: All 9 tests should pass.

## Integration Examples

Run the monitoring examples:

```bash
cd src
python3 example_job_monitoring.py
```

This will:
- Create sample monitored jobs
- Store job history in `/tmp/keystone_jobs/jobs_history.jsonl`
- Display various monitoring features

## CLI Testing (Without Running Simulations)

After running the examples above, you can test the CLI commands:

```bash
cd src/agent

# View job history
python3 cli.py job-history

# View statistics
python3 cli.py job-stats

# View specific job details (use a task-id from job-history output)
python3 cli.py job-details example-task-1
```

## CLI Testing (With Running Simulations)

If you have Docker services running:

```bash
cd src/agent

# Submit a task
python3 cli.py submit fenicsx poisson.py --wait

# View the job in history
python3 cli.py job-history --limit 1

# View updated statistics
python3 cli.py job-stats
```

## Verify Job History File

Check that job history is being persisted:

```bash
# View the file
cat /tmp/keystone_jobs/jobs_history.jsonl

# Pretty print first entry
head -1 /tmp/keystone_jobs/jobs_history.jsonl | python3 -m json.tool
```

Expected format:
```json
{
    "task_id": "...",
    "tool": "fenicsx",
    "script": "poisson.py",
    "params": {...},
    "start_time": "2025-10-15T...",
    "end_time": "2025-10-15T...",
    "duration_seconds": 1.5,
    "status": "success",
    "returncode": 0,
    "resource_usage": {
        "cpu_user_seconds": 1.2,
        "cpu_system_seconds": 0.1,
        "cpu_total_seconds": 1.3,
        "memory_peak_mb": 256.5
    },
    "error": null,
    "has_result": true
}
```

## Test Scenarios

### 1. Successful Job
```bash
cd src/agent
python3 cli.py submit fenicsx poisson.py --wait
python3 cli.py job-history --status success --limit 1
```

Expected: Job appears with status=success, resource metrics populated

### 2. Failed Job
Submit a job that will fail (e.g., non-existent script):
```bash
python3 cli.py submit fenicsx nonexistent.py --wait
python3 cli.py job-history --status failed --limit 1
```

Expected: Job appears with status=failed, error message populated

### 3. Multiple Jobs
```bash
python3 cli.py submit-workflow ../../example_workflow.json --parallel --wait
python3 cli.py job-stats
```

Expected: Statistics show multiple jobs with breakdown by tool

### 4. Filter by Tool
```bash
python3 cli.py job-history --tool fenicsx
```

Expected: Only fenicsx jobs displayed

### 5. Resource Metrics
Look for jobs with significant CPU/memory usage:
```bash
python3 cli.py job-history --limit 10
```

Check that:
- Duration values are reasonable
- CPU time values are present
- Memory peak values are in MB

## Validation Checklist

- [ ] All unit tests pass (9/9)
- [ ] Example script runs without errors
- [ ] Job history file is created at `/tmp/keystone_jobs/jobs_history.jsonl`
- [ ] CLI commands `job-history`, `job-stats`, `job-details` work
- [ ] Job outcomes (success/failed) are tracked correctly
- [ ] Resource metrics (CPU, memory, duration) are recorded
- [ ] Error messages are captured for failed jobs
- [ ] Filtering by tool and status works
- [ ] Statistics show correct aggregations
- [ ] No breaking changes to existing functionality

## Troubleshooting

### Issue: "No job history found"

**Solution**: Run `python3 example_job_monitoring.py` first to create some history.

### Issue: "Permission denied" writing to /tmp/keystone_jobs

**Solution**: Ensure the directory is writable:
```bash
mkdir -p /tmp/keystone_jobs
chmod 755 /tmp/keystone_jobs
```

### Issue: Import errors

**Solution**: Ensure you're in the correct directory and dependencies are installed:
```bash
cd /home/runner/work/KeystoneSupercomputer/KeystoneSupercomputer/src
pip install psutil
```

### Issue: Resource metrics show 0 values

**Explanation**: For very short jobs (< 0.01s), CPU time may round to 0. This is expected and normal for quick test jobs.

## Success Criteria

The implementation is successful if:

1. ✅ All unit tests pass
2. ✅ Job outcomes are logged for every task execution
3. ✅ Resource usage (CPU, memory, duration) is tracked
4. ✅ Job history is persisted in JSONL format
5. ✅ CLI commands provide useful monitoring information
6. ✅ Failed jobs are tracked with error details
7. ✅ Statistics aggregate correctly across all jobs
8. ✅ No breaking changes to existing code

## Documentation

For detailed usage information, see:
- [JOB_MONITORING.md](../JOB_MONITORING.md) - Comprehensive monitoring guide
- [CLI_REFERENCE.md](../CLI_REFERENCE.md) - CLI command reference
- [README.md](../README.md) - Updated with monitoring features
