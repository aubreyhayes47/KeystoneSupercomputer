# CLI Quick Reference Card

## Keystone Supercomputer CLI - Workflow Submission & Monitoring

### Setup
```bash
cd src/agent
pip install -r ../../requirements.txt
```

### Prerequisites
```bash
# Start services
docker compose up -d redis celery-worker

# Check services
docker compose ps
```

---

## Commands

### Health & Discovery
```bash
# Check worker health
python3 cli.py health

# List available tools
python3 cli.py list-tools
```

### Single Task Operations
```bash
# Submit task
python3 cli.py submit <tool> <script> [-p '{"key": "value"}'] [--wait] [-t timeout]

# Check status
python3 cli.py status <task-id> [--monitor] [-i interval]

# Cancel task
python3 cli.py cancel <task-id>
```

### Workflow Operations
```bash
# Submit workflow
python3 cli.py submit-workflow <file.json> [--parallel|--sequential] [--wait] [-t timeout]

# Check workflow status
python3 cli.py workflow-status <task-id-1> <task-id-2> ...
```

### LLM Agent
```bash
# Ask agent
python3 cli.py ask "your question"
```

---

## Examples

### Quick Task
```bash
python3 cli.py submit fenicsx poisson.py --wait
```

### Task with Parameters
```bash
python3 cli.py submit fenicsx poisson.py -p '{"mesh_size": 64}' --wait
```

### Monitor Background Task
```bash
# Submit
python3 cli.py submit lammps example.lammps
# Returns: Task ID: abc123...

# Monitor
python3 cli.py status abc123... --monitor
```

### Parallel Workflow
```bash
python3 cli.py submit-workflow workflow.json --parallel --wait
```

### Sequential Workflow
```bash
python3 cli.py submit-workflow workflow.json --sequential --wait
```

---

## Workflow File Format

**workflow.json:**
```json
[
  {
    "tool": "fenicsx",
    "script": "poisson.py",
    "params": {"mesh_size": 32}
  },
  {
    "tool": "lammps",
    "script": "example.lammps",
    "params": {}
  }
]
```

---

## Common Options

- `--wait` / `--no-wait` - Wait for completion (default: no-wait)
- `-t, --timeout INTEGER` - Timeout in seconds
- `-p, --params TEXT` - JSON parameters
- `-m, --monitor` - Monitor until completion
- `-i, --interval INTEGER` - Polling interval (default: 2s)
- `--parallel` / `--sequential` - Workflow execution mode

---

## Tips

✓ Always check health before submitting: `python3 cli.py health`

✓ Use `--wait` for quick tasks, background mode for long ones

✓ Save complex workflows in JSON files for reusability

✓ Use workflow-status to monitor multiple tasks at once

✓ Check logs on failure: `docker compose logs celery-worker`

---

## Documentation

- **CLI_REFERENCE.md** - Complete CLI documentation
- **TASK_PIPELINE.md** - Python API reference
- **DOCKER_COMPOSE.md** - Service orchestration guide
- **example_workflow.json** - Sample workflow file
- **cli_demo.sh** - Interactive demo script

---

## Troubleshooting

**Connection Error:**
```bash
docker compose up -d redis celery-worker
```

**Invalid JSON:**
```bash
# Use single quotes around JSON, double quotes inside
python3 cli.py submit tool script -p '{"key": "value"}'
```

**Task Timeout:**
```bash
# Increase timeout
python3 cli.py submit tool script --wait --timeout 600
```
