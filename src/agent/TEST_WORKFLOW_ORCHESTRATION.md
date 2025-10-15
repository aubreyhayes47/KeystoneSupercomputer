# Agentic Workflow Orchestration Tests

This directory contains comprehensive tests for validating multi-step workflow execution through orchestrated containers and agent interfaces.

## Test Files

### Unit Tests

#### `test_workflow_orchestration.py`
Unit tests for workflow orchestration that validate the TaskPipeline workflow functionality without requiring running services.

**Tests included:**
- `test_workflow_submission_sequential` - Validates sequential workflow task ordering
- `test_workflow_submission_parallel` - Validates parallel workflow submission
- `test_workflow_status_tracking` - Tests workflow status aggregation
- `test_workflow_validation_missing_fields` - Tests workflow validation
- `test_workflow_error_handling` - Tests graceful error handling
- `test_workflow_wait_completion` - Tests workflow completion monitoring
- `test_workflow_callback_mechanism` - Tests progress callbacks
- `test_workflow_timeout_handling` - Tests timeout handling
- `test_workflow_mixed_results` - Tests mixed success/failure results
- `test_workflow_empty_list` - Tests empty workflow handling

**Run unit tests:**
```bash
cd src/agent
python3 test_workflow_orchestration.py
```

#### `test_task_pipeline.py`
Existing unit tests for TaskPipeline basic functionality.

**Run tests:**
```bash
cd src/agent
python3 test_task_pipeline.py
```

#### `test_cli.py`
Existing unit tests for CLI commands including workflow submission.

**Run tests:**
```bash
cd src/agent
python3 test_cli.py
```

### Integration Tests

#### `test_agentic_workflow_integration.py`
End-to-end integration tests that validate complete agentic workflow orchestration through Docker Compose and Celery workers.

**Tests included:**
- `test_simple_workflow` - Two-step sequential workflow
- `test_parallel_workflow` - Three tasks running concurrently
- `test_workflow_with_agent_state` - Agent-driven workflow with state management
- `test_workflow_error_recovery` - Workflow continuation after task failure
- `test_workflow_cancellation` - Task cancellation in workflows

**Prerequisites:**
```bash
# Start Docker Compose services
docker compose up -d redis celery-worker

# Verify services are running
docker compose ps
```

**Run all integration tests:**
```bash
cd src/agent
python3 test_agentic_workflow_integration.py
```

**Run specific test:**
```bash
python3 test_agentic_workflow_integration.py --test workflow_simple
python3 test_agentic_workflow_integration.py --test workflow_parallel
python3 test_agentic_workflow_integration.py --test workflow_agent_state
python3 test_agentic_workflow_integration.py --test workflow_error_recovery
python3 test_agentic_workflow_integration.py --test workflow_cancellation
```

## Test Coverage

### Workflow Orchestration Features

✅ **Sequential Workflows**
- Tasks execute in order
- Each task waits for previous completion
- Failed tasks are logged but don't block subsequent tasks

✅ **Parallel Workflows**
- Multiple tasks submit simultaneously
- Tasks execute concurrently
- All task results are aggregated

✅ **Agent State Management**
- Agent state updates based on workflow results
- Task parameters derived from agent state
- Artifact paths tracked in agent state
- Messages logged for agent context

✅ **Error Handling**
- Task validation before submission
- Graceful handling of task failures
- Workflow continues after individual failures
- Error messages captured and reported

✅ **Status Tracking**
- Real-time workflow progress monitoring
- Aggregated status across all tasks
- Individual task state tracking
- Completion detection

✅ **Callbacks and Monitoring**
- Progress callbacks during workflow execution
- Configurable polling intervals
- Status updates at regular intervals

✅ **Task Cancellation**
- Cancel individual tasks
- Cancel tasks within workflows
- Cleanup after cancellation

✅ **Timeout Management**
- Configurable timeouts for tasks
- Configurable timeouts for workflows
- TimeoutError raised on expiration

### Container Orchestration

✅ **Docker Compose Integration**
- Multi-service orchestration (Redis, Celery, simulation tools)
- Volume mounting for data persistence
- Network communication between services
- Service health checks

✅ **Celery Task Queue**
- Background task processing
- Task distribution across workers
- Result backend (Redis)
- Task state tracking

✅ **Simulation Tools**
- FEniCSx (Finite Element Method)
- LAMMPS (Molecular Dynamics)
- OpenFOAM (Computational Fluid Dynamics)

## Running All Tests

### Quick Test Suite (Unit Tests Only)
```bash
cd src/agent
python3 test_workflow_orchestration.py
python3 test_task_pipeline.py
python3 test_cli.py
```

### Full Test Suite (Unit + Integration)
```bash
# Start services
docker compose up -d redis celery-worker

# Run unit tests
cd src/agent
python3 test_workflow_orchestration.py
python3 test_task_pipeline.py
python3 test_cli.py

# Run integration tests
python3 test_agentic_workflow_integration.py

# Cleanup
cd ../..
docker compose down
```

## Continuous Integration

For CI/CD pipelines, use the unit tests which don't require running services:

```bash
# Install dependencies
pip install -r requirements.txt

# Run unit tests
python3 src/agent/test_workflow_orchestration.py
python3 src/agent/test_task_pipeline.py
python3 src/agent/test_cli.py
python3 src/test_job_monitor.py
```

## Test Results

All tests validate:

1. **Multi-step workflow execution** - Sequential and parallel task execution
2. **Orchestrated containers** - Docker Compose services working together
3. **Agent interfaces** - TaskPipeline API for agent-driven workflows
4. **Error resilience** - Graceful handling of failures
5. **State management** - Agent state updates throughout workflow
6. **Resource monitoring** - Job tracking and metrics collection

## Troubleshooting

### Redis Connection Errors in Unit Tests
Expected behavior - unit tests mock Redis connections. Errors like "Connection to Redis lost" during unit tests are normal and handled gracefully.

### Integration Tests Fail with Connection Error
Make sure Docker Compose services are running:
```bash
docker compose up -d redis celery-worker
docker compose logs celery-worker
```

### Celery Worker Not Processing Tasks
Restart the worker:
```bash
docker compose restart celery-worker
docker compose logs -f celery-worker
```

### Docker Images Not Available
Build the simulation tool images:
```bash
docker compose build fenicsx lammps openfoam
```

## Related Documentation

- [TASK_PIPELINE.md](../../TASK_PIPELINE.md) - TaskPipeline API reference
- [DOCKER_COMPOSE.md](../../DOCKER_COMPOSE.md) - Docker Compose setup
- [JOB_MONITORING.md](../../JOB_MONITORING.md) - Job monitoring features
- [CLI_REFERENCE.md](../../CLI_REFERENCE.md) - CLI command reference

## Future Enhancements

Potential additional tests:
- [ ] Multi-agent coordination workflows
- [ ] Workflow checkpointing and resume
- [ ] Long-running workflow stability
- [ ] High-volume parallel execution
- [ ] Resource limit enforcement
- [ ] Workflow templates and reuse
- [ ] Performance benchmarks
