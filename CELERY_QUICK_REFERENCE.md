# Celery Job Queue Quick Reference

## Starting Services

```bash
# Start Redis and Celery worker
docker compose up -d redis celery-worker

# Check status
docker compose ps

# View logs
docker compose logs -f celery-worker
```

## Submitting Jobs

### Python API

```python
from celery_app import run_simulation_task

# Submit a task
task = run_simulation_task.delay(
    tool="fenicsx",
    script="poisson.py",
    params={"mesh_size": 64}
)

# Get task ID and state
print(f"Task ID: {task.id}")
print(f"State: {task.state}")

# Wait for result
result = task.get(timeout=300)
print(result)
```

### Command Line

```bash
# Run example script
cd src/agent
python3 example_job_submission.py

# Quick health check
python3 -c "from celery_app import health_check_task; print(health_check_task.delay().get())"
```

## Monitoring Tasks

```python
import time

# Poll task status
while not task.ready():
    if task.state == 'RUNNING':
        meta = task.info
        print(f"Progress: {meta.get('progress', 0)}%")
    time.sleep(2)

# Get result
result = task.get()
```

## Available Tasks

1. **run_simulation** - Execute a simulation
   - Parameters: `tool`, `script`, `params` (optional)
   - Returns: Task result with status, output, artifacts

2. **health_check** - Verify worker health
   - Parameters: None
   - Returns: Health status

3. **list_simulations** - List available tools
   - Parameters: None
   - Returns: Dictionary of tools and scripts

## Task States

- `PENDING` - Task waiting in queue
- `RUNNING` - Task being executed
- `SUCCESS` - Task completed successfully
- `FAILURE` - Task failed

## Troubleshooting

### Worker Not Processing Tasks

```bash
# Restart worker
docker compose restart celery-worker

# Check logs
docker compose logs celery-worker

# Verify Redis connection
docker compose exec redis redis-cli ping
```

### Task Stuck in PENDING

```bash
# Check worker is running
docker compose ps celery-worker

# Check queue length
docker compose exec redis redis-cli llen celery

# Restart services
docker compose restart redis celery-worker
```

## Configuration

Environment variables in `.env`:

```bash
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
CELERY_WORKER_CONCURRENCY=2
```

## More Information

See [DOCKER_COMPOSE.md](DOCKER_COMPOSE.md) for comprehensive documentation.
