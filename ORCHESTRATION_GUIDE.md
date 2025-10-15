# Orchestration Usage and Workflow Patterns

## Overview

This guide explains how to launch, monitor, and manage orchestrated simulation workflows in Keystone Supercomputer. Whether you're running a single simulation or complex multi-step workflows, this guide covers deployment options, monitoring strategies, and common workflow patterns.

**Quick Navigation:**
- [Getting Started](#getting-started)
- [Deployment Options](#deployment-options)
- [Launching Workflows](#launching-workflows)
- [Monitoring and Management](#monitoring-and-management)
- [Common Workflow Patterns](#common-workflow-patterns)
- [Troubleshooting](#troubleshooting)

---

## Getting Started

### Prerequisites

Before launching orchestrated workflows, ensure you have:

- **Docker**: Version 20.10+ with Docker Compose V2
- **Python**: Version 3.8+ with requirements installed
- **Resources**: 8GB+ RAM, 20GB+ disk space
- **Optional**: kubectl and helm (for Kubernetes deployments)

### Quick Setup

```bash
# 1. Clone the repository (if not already done)
git clone https://github.com/aubreyhayes47/KeystoneSupercomputer.git
cd KeystoneSupercomputer

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Create environment configuration
cp .env.example .env

# 4. Start with Docker Compose (recommended for beginners)
./docker-compose-quickstart.sh
```

---

## Deployment Options

Keystone Supercomputer supports three deployment modes, each suited for different use cases:

### 1. Docker Compose (Recommended for Local Development)

**Best for:** Single-machine development, testing, and small-scale workflows

**Advantages:**
- Simple setup and management
- Minimal resource overhead
- Fast iteration cycles
- No Kubernetes knowledge required

**Start services:**
```bash
# Start Redis and Celery worker
docker compose up -d redis celery-worker

# Verify services are running
docker compose ps
```

**Documentation:** [DOCKER_COMPOSE.md](DOCKER_COMPOSE.md)

### 2. k3d Kubernetes Cluster (Recommended for Testing at Scale)

**Best for:** Testing production-like deployments, multi-node simulations, scaling experiments

**Advantages:**
- Production-like Kubernetes environment
- Multi-node worker distribution
- Load balancing and service discovery
- Horizontal scaling capabilities

**Start cluster:**
```bash
# Create and configure k3d cluster
./k3d-setup.sh

# Verify cluster is running
kubectl get nodes
kubectl get pods -n keystone
```

**Documentation:** [K3D.md](K3D.md), [K3D_EXAMPLES.md](K3D_EXAMPLES.md)

### 3. Helm Charts (Recommended for Production)

**Best for:** Production deployments, enterprise environments, reproducible configurations

**Advantages:**
- Configuration management via values files
- Easy upgrades and rollbacks
- Production-ready defaults
- Version control for deployments

**Deploy with Helm:**
```bash
# Install complete simulation stack
helm install keystone-sim k8s/helm/keystone-simulation \
  -n keystone \
  --create-namespace

# Use production configuration
helm install keystone-sim k8s/helm/keystone-simulation \
  -n keystone \
  --create-namespace \
  -f k8s/helm/values-production.yaml
```

**Documentation:** [HELM_QUICKSTART.md](HELM_QUICKSTART.md), [k8s/helm/README.md](k8s/helm/README.md)

### Choosing the Right Deployment

| Use Case | Recommended Deployment | Why |
|----------|----------------------|-----|
| Learning the system | Docker Compose | Simplest setup, fastest feedback |
| Single simulations | Docker Compose | Minimal overhead |
| Development & testing | Docker Compose | Easy iteration and debugging |
| Testing scalability | k3d | Multi-node without cloud costs |
| Production workloads | Helm + k3d/k8s | Robust, scalable, maintainable |
| Multi-user environment | Helm + k3d/k8s | Resource isolation and scaling |

---

## Launching Workflows

### Method 1: Command-Line Interface (CLI)

The CLI provides the most user-friendly interface for workflow submission and monitoring.

#### Single Task Submission

```bash
cd src/agent

# Submit a FEniCSx simulation
python3 cli.py submit fenicsx poisson.py \
  -p '{"mesh_size": 64}' \
  --wait

# Submit with custom output description
python3 cli.py submit openfoam example_cavity.py \
  --wait \
  --output "Cavity flow simulation results"
```

**Key CLI Commands:**
- `health` - Check worker availability
- `list-tools` - Show available simulation tools
- `submit` - Submit a single simulation
- `status` - Check task status
- `cancel` - Cancel a running task

**See:** [CLI_REFERENCE.md](CLI_REFERENCE.md) for complete command documentation

#### Workflow Submission

Submit multiple tasks from a JSON file:

```bash
# Parallel execution (all tasks run simultaneously)
python3 cli.py submit-workflow ../../example_workflow.json \
  --parallel \
  --wait

# Sequential execution (tasks run one after another)
python3 cli.py submit-workflow ../../example_workflow.json \
  --wait

# Monitor workflow progress
python3 cli.py workflow-status <workflow-id-1> <workflow-id-2> <workflow-id-3>
```

**Workflow JSON Format:**
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

### Method 2: Python Task Pipeline API

For programmatic control or agent integration, use the TaskPipeline API.

#### Basic Usage

```python
from task_pipeline import TaskPipeline

# Initialize pipeline
pipeline = TaskPipeline()

# Check system health
health = pipeline.health_check()
print(f"Worker status: {health['status']}")

# Submit and monitor a task
task_id = pipeline.submit_task(
    tool="fenicsx",
    script="poisson.py",
    params={"mesh_size": 64}
)

# Wait for completion
result = pipeline.wait_for_task(task_id, timeout=300)
print(f"Status: {result['status']}")
```

#### Parallel Workflow

```python
# Define workflow tasks
tasks = [
    {"tool": "fenicsx", "script": "poisson.py", "params": {"mesh_size": 32}},
    {"tool": "lammps", "script": "example.lammps", "params": {}},
    {"tool": "openfoam", "script": "example_cavity.py", "params": {}},
]

# Submit all tasks in parallel
task_ids = pipeline.submit_workflow(tasks, sequential=False)

# Monitor with callback
def on_progress(status):
    print(f"Progress: {status['completed']}/{status['total']} tasks completed")

# Wait for all tasks
results = pipeline.wait_for_workflow(
    task_ids, 
    timeout=600, 
    callback=on_progress
)
```

#### Sequential Workflow

```python
# Submit tasks one after another
task_ids = pipeline.submit_workflow(tasks, sequential=True)

# Each task waits for the previous one to complete
results = pipeline.wait_for_workflow(task_ids, timeout=1200)
```

**See:** [TASK_PIPELINE.md](TASK_PIPELINE.md) for complete API documentation

### Method 3: Direct Celery (Advanced)

For low-level control, interact directly with Celery tasks.

```python
from celery_app import run_simulation_task

# Submit task
task = run_simulation_task.delay(
    "fenicsx",
    "poisson.py",
    {"mesh_size": 64}
)

# Poll for status
while not task.ready():
    if task.state == 'RUNNING':
        print(f"Progress: {task.info.get('progress', 0)}%")
    time.sleep(2)

# Get result
result = task.get(timeout=300)
```

**See:** [CELERY_QUICK_REFERENCE.md](CELERY_QUICK_REFERENCE.md)

### Method 4: Kubernetes Jobs (k3d/Helm Deployments)

For Kubernetes deployments, use kubectl or the k3d management script.

```bash
# Using k3d-manage.sh
./k3d-manage.sh run-simulation fenicsx poisson.py

# Using kubectl directly
kubectl create job -n keystone fenicsx-run-1 \
  --from=job/fenicsx-simulation

# Monitor job
kubectl get jobs -n keystone -w
kubectl logs -n keystone job/fenicsx-run-1 -f
```

**See:** [K3D.md](K3D.md) for Kubernetes workflow management

---

## Monitoring and Management

### Health Checks

Always verify system health before launching workflows:

#### CLI Health Check
```bash
cd src/agent
python3 cli.py health
```

#### Python Health Check
```python
from task_pipeline import TaskPipeline

pipeline = TaskPipeline()
health = pipeline.health_check()

if health['status'] == 'healthy':
    print("System ready for workflows")
else:
    print(f"System degraded: {health['message']}")
```

#### Docker Compose Health
```bash
# Check service status
docker compose ps

# Check Redis connectivity
docker compose exec redis redis-cli ping

# Check Celery worker logs
docker compose logs -f celery-worker
```

#### Kubernetes Health
```bash
# Check pod status
kubectl get pods -n keystone

# Check service endpoints
kubectl get svc -n keystone

# View worker logs
./k3d-manage.sh logs celery-worker
```

### Task Monitoring

#### Real-time Monitoring with CLI

```bash
# Monitor a specific task
python3 cli.py status <task-id> --monitor

# Monitor workflow tasks
python3 cli.py workflow-status <task-id-1> <task-id-2> <task-id-3>
```

#### Programmatic Monitoring

```python
# Define progress callback
def on_progress(status):
    state = status['state']
    if state == 'RUNNING':
        progress = status.get('progress', 0)
        print(f"Running: {progress}%")
    elif status['ready']:
        print(f"Completed: {state}")

# Monitor task with callback
pipeline.monitor_task(task_id, callback=on_progress, poll_interval=2)
```

### Job History and Statistics

View historical job execution data with resource metrics:

```bash
# View recent job history
python3 cli.py job-history --limit 20

# Filter by tool
python3 cli.py job-history --tool fenicsx

# Filter by status
python3 cli.py job-history --status failed

# Show aggregate statistics
python3 cli.py job-stats

# Get detailed job information
python3 cli.py job-details <task-id>
```

**Tracked Metrics:**
- CPU time (user and system)
- Memory usage (peak)
- Execution duration
- Job status (success/failure)
- Error messages

**See:** [JOB_MONITORING.md](JOB_MONITORING.md) for comprehensive monitoring documentation

### Scaling Workers

Adjust worker capacity based on workload:

#### Docker Compose Scaling
```bash
# Scale to 3 workers
docker compose up -d --scale celery-worker=3

# Verify scaling
docker compose ps celery-worker
```

#### Kubernetes Scaling
```bash
# Using k3d-manage.sh
./k3d-manage.sh scale celery-worker 5

# Using kubectl
kubectl scale deployment celery-worker -n keystone --replicas=5

# Using Helm
helm upgrade keystone-sim k8s/helm/keystone-simulation \
  -n keystone \
  --set celeryWorker.replicaCount=10
```

### Cancelling Tasks

Stop running or pending tasks:

```bash
# Cancel via CLI
python3 cli.py cancel <task-id>
```

```python
# Cancel via Python
if pipeline.cancel_task(task_id):
    print("Task cancelled successfully")
```

---

## Common Workflow Patterns

### Pattern 1: Single Simulation

**Use case:** Run a single simulation with specific parameters

```bash
# Via CLI
python3 cli.py submit fenicsx poisson.py \
  -p '{"mesh_size": 128}' \
  --wait
```

```python
# Via Python
pipeline = TaskPipeline()
task_id = pipeline.submit_task(
    tool="fenicsx",
    script="poisson.py",
    params={"mesh_size": 128}
)
result = pipeline.wait_for_task(task_id, timeout=300)
```

**When to use:** Testing, quick computations, debugging

---

### Pattern 2: Parameter Sweep (Parallel)

**Use case:** Run the same simulation with different parameters simultaneously

```python
from task_pipeline import TaskPipeline

pipeline = TaskPipeline()

# Define parameter sweep
mesh_sizes = [16, 32, 64, 128, 256]
tasks = [
    {
        "tool": "fenicsx",
        "script": "poisson.py",
        "params": {"mesh_size": size}
    }
    for size in mesh_sizes
]

# Submit all in parallel
task_ids = pipeline.submit_workflow(tasks, sequential=False)

# Wait for all to complete
results = pipeline.wait_for_workflow(task_ids, timeout=1200)

# Analyze results
for task_id, result in zip(task_ids, results['results']):
    if result['status'] == 'success':
        print(f"Mesh size {result['params']['mesh_size']}: Success")
```

**When to use:** Parameter optimization, sensitivity analysis, convergence studies

---

### Pattern 3: Multi-Tool Workflow (Sequential)

**Use case:** Run different simulations in sequence, where each depends on previous results

```python
# Define sequential workflow
tasks = [
    # Step 1: Generate mesh with OpenFOAM
    {
        "tool": "openfoam",
        "script": "mesh_generation.py",
        "params": {"domain_size": 10}
    },
    # Step 2: Run CFD simulation
    {
        "tool": "openfoam",
        "script": "cavity_flow.py",
        "params": {"time_steps": 1000}
    },
    # Step 3: Post-process with FEniCSx
    {
        "tool": "fenicsx",
        "script": "analysis.py",
        "params": {"field": "velocity"}
    }
]

# Submit sequentially (each waits for previous)
task_ids = pipeline.submit_workflow(tasks, sequential=True)
results = pipeline.wait_for_workflow(task_ids, timeout=3600)
```

**When to use:** Multi-physics simulations, preprocessing → simulation → postprocessing pipelines

---

### Pattern 4: Multi-Tool Workflow (Parallel)

**Use case:** Run different types of simulations simultaneously

```python
# Define parallel workflow
tasks = [
    {"tool": "fenicsx", "script": "poisson.py", "params": {"mesh_size": 64}},
    {"tool": "lammps", "script": "molecular_dynamics.lammps", "params": {}},
    {"tool": "openfoam", "script": "turbulent_flow.py", "params": {}}
]

# Submit all in parallel
task_ids = pipeline.submit_workflow(tasks, sequential=False)

# Monitor with progress callback
def on_update(status):
    print(f"{status['completed']}/{status['total']} simulations completed")

results = pipeline.wait_for_workflow(
    task_ids,
    timeout=1800,
    callback=on_update
)
```

**When to use:** Comparing different simulation methods, running independent analyses

---

### Pattern 5: Conditional Workflow

**Use case:** Run simulations conditionally based on previous results

```python
pipeline = TaskPipeline()

# Step 1: Initial simulation
task_id_1 = pipeline.submit_task(
    tool="fenicsx",
    script="convergence_test.py",
    params={"mesh_size": 32}
)
result_1 = pipeline.wait_for_task(task_id_1, timeout=300)

# Step 2: Conditional refinement
if result_1['status'] == 'success':
    convergence = result_1.get('convergence', 0)
    
    if convergence < 0.01:  # Not converged
        print("Refining mesh and rerunning...")
        task_id_2 = pipeline.submit_task(
            tool="fenicsx",
            script="convergence_test.py",
            params={"mesh_size": 64}
        )
        result_2 = pipeline.wait_for_task(task_id_2, timeout=300)
    else:
        print("Convergence achieved!")
```

**When to use:** Adaptive refinement, iterative optimization, quality checks

---

### Pattern 6: Batch Processing

**Use case:** Process multiple independent simulation cases from files

```python
import json
import glob

pipeline = TaskPipeline()

# Load simulation cases from directory
case_files = glob.glob("cases/*.json")
tasks = []

for case_file in case_files:
    with open(case_file) as f:
        case = json.load(f)
        tasks.append({
            "tool": case['tool'],
            "script": case['script'],
            "params": case['params']
        })

# Submit all cases
task_ids = pipeline.submit_workflow(tasks, sequential=False)

# Wait for batch completion
results = pipeline.wait_for_workflow(task_ids, timeout=7200)

# Generate summary report
success_count = sum(1 for r in results['results'] if r['status'] == 'success')
print(f"Batch complete: {success_count}/{len(tasks)} successful")
```

**When to use:** Processing multiple datasets, running simulation suites, nightly builds

---

### Pattern 7: Retry with Backoff

**Use case:** Automatically retry failed simulations with increasing delays

```python
import time

def submit_with_retry(pipeline, tool, script, params, max_retries=3):
    """Submit task with exponential backoff retry."""
    for attempt in range(max_retries):
        task_id = pipeline.submit_task(tool, script, params)
        
        try:
            result = pipeline.wait_for_task(task_id, timeout=300)
            
            if result['status'] == 'success':
                return result
            
            print(f"Attempt {attempt + 1} failed: {result.get('error')}")
            
            # Exponential backoff
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                print(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
                
        except TimeoutError:
            print(f"Attempt {attempt + 1} timed out")
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                time.sleep(wait_time)
    
    return None

# Use retry logic
result = submit_with_retry(
    pipeline,
    tool="fenicsx",
    script="poisson.py",
    params={"mesh_size": 64}
)
```

**When to use:** Handling transient failures, unreliable resources, production workflows

---

### Pattern 8: Resource-Aware Scheduling

**Use case:** Schedule tasks based on available resources

```python
from task_pipeline import TaskPipeline
import psutil

def get_available_resources():
    """Check system resource availability."""
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    
    return {
        'cpu_available': 100 - cpu_percent,
        'memory_available_gb': memory.available / (1024**3)
    }

def schedule_tasks_by_resources(pipeline, tasks):
    """Schedule tasks based on resource requirements."""
    for task in tasks:
        # Check resources before submission
        resources = get_available_resources()
        
        if resources['cpu_available'] > 20 and resources['memory_available_gb'] > 2:
            task_id = pipeline.submit_task(
                tool=task['tool'],
                script=task['script'],
                params=task['params']
            )
            print(f"Submitted task {task_id}")
        else:
            print("Insufficient resources, waiting...")
            time.sleep(30)

# Schedule resource-intensive tasks
heavy_tasks = [
    {"tool": "openfoam", "script": "large_simulation.py", "params": {}},
    {"tool": "lammps", "script": "large_md.lammps", "params": {}},
]

schedule_tasks_by_resources(pipeline, heavy_tasks)
```

**When to use:** Resource-constrained environments, preventing system overload

---

## Troubleshooting

### Problem: Worker Not Responding

**Symptoms:**
- `health` check fails
- Tasks stuck in PENDING state
- No task progress

**Solutions:**

1. Check if services are running:
```bash
# Docker Compose
docker compose ps

# Kubernetes
kubectl get pods -n keystone
```

2. Restart worker:
```bash
# Docker Compose
docker compose restart celery-worker

# Kubernetes
kubectl rollout restart deployment/celery-worker -n keystone
```

3. Check worker logs:
```bash
# Docker Compose
docker compose logs -f celery-worker

# Kubernetes
./k3d-manage.sh logs celery-worker
```

4. Verify Redis connection:
```bash
# Docker Compose
docker compose exec redis redis-cli ping

# Kubernetes
kubectl exec -n keystone deployment/redis -- redis-cli ping
```

---

### Problem: Task Fails Immediately

**Symptoms:**
- Task moves to FAILURE state quickly
- Error message in result

**Solutions:**

1. Check task details:
```bash
python3 cli.py job-details <task-id>
```

2. Verify simulation tool is available:
```bash
# List available tools
python3 cli.py list-tools

# Check Docker images
docker images | grep -E "fenicsx|lammps|openfoam"
```

3. Validate input parameters:
```bash
# Review the error message
python3 cli.py status <task-id>
```

4. Test the simulation directly:
```bash
# Run without queue for debugging
docker compose run --rm fenicsx poisson.py
```

---

### Problem: Task Stuck in RUNNING State

**Symptoms:**
- Task shows RUNNING but no progress
- Timeout occurs

**Solutions:**

1. Increase timeout:
```python
# Increase timeout for long-running simulations
result = pipeline.wait_for_task(task_id, timeout=1800)  # 30 minutes
```

2. Check if simulation is actually running:
```bash
# Check container logs
docker compose logs -f celery-worker
```

3. Cancel and resubmit:
```bash
python3 cli.py cancel <task-id>
python3 cli.py submit fenicsx poisson.py --wait
```

---

### Problem: Out of Memory Errors

**Symptoms:**
- Tasks fail with memory errors
- System becomes unresponsive

**Solutions:**

1. Reduce concurrent tasks:
```bash
# Scale down workers
docker compose up -d --scale celery-worker=1
```

2. Reduce simulation size:
```python
# Use smaller parameters
params = {"mesh_size": 32}  # Instead of 256
```

3. Monitor resource usage:
```bash
python3 cli.py job-history --limit 10
```

4. Increase Docker memory limit:
```bash
# Edit Docker Desktop settings or docker-compose.yml
# Add memory limits to services
```

---

### Problem: Workflow Partially Completes

**Symptoms:**
- Some tasks succeed, others fail
- Mixed status in workflow results

**Solutions:**

1. Check individual task status:
```bash
python3 cli.py workflow-status <task-id-1> <task-id-2> <task-id-3>
```

2. Review failed tasks:
```python
results = pipeline.get_workflow_status(task_ids)
for task_id, status in zip(task_ids, results['tasks']):
    if status['state'] == 'FAILURE':
        print(f"Task {task_id} failed: {status.get('error')}")
```

3. Retry failed tasks:
```python
failed_tasks = [
    task for task, status in zip(tasks, results['tasks'])
    if status['state'] == 'FAILURE'
]
retry_ids = pipeline.submit_workflow(failed_tasks, sequential=False)
```

---

### Problem: Cannot Connect to k3d Cluster

**Symptoms:**
- `kubectl` commands fail
- Cluster not accessible

**Solutions:**

1. Check cluster status:
```bash
k3d cluster list
kubectl cluster-info
```

2. Restart cluster:
```bash
./k3d-manage.sh stop
./k3d-setup.sh
```

3. Verify kubeconfig:
```bash
export KUBECONFIG=~/.kube/config
kubectl config current-context
```

---

## Best Practices

### 1. Always Check Health First

Before submitting workflows, verify system health:

```python
pipeline = TaskPipeline()
health = pipeline.health_check()
assert health['status'] == 'healthy', "System not ready"
```

### 2. Use Appropriate Timeouts

Set realistic timeouts based on simulation complexity:

```python
# Quick test: 5 minutes
result = pipeline.wait_for_task(task_id, timeout=300)

# Standard simulation: 30 minutes
result = pipeline.wait_for_task(task_id, timeout=1800)

# Long-running: 2 hours
result = pipeline.wait_for_task(task_id, timeout=7200)
```

### 3. Monitor Long-Running Workflows

Use callbacks for visibility:

```python
def progress_callback(status):
    print(f"Progress: {status['completed']}/{status['total']}")
    logging.info(f"Workflow status: {status}")

pipeline.wait_for_workflow(task_ids, callback=progress_callback)
```

### 4. Handle Failures Gracefully

Always check task status and handle errors:

```python
result = pipeline.wait_for_task(task_id, timeout=300)

if result['status'] == 'success':
    print("Simulation successful")
    artifacts = result.get('artifacts', [])
else:
    print(f"Simulation failed: {result.get('error')}")
    # Log error, retry, or alert user
```

### 5. Clean Up Resources

Stop services when not in use:

```bash
# Docker Compose
docker compose down

# Kubernetes (careful with this!)
./k3d-manage.sh stop
```

### 6. Use Configuration Files

Store workflows in version-controlled JSON:

```json
{
  "workflow_name": "convergence_study",
  "tasks": [
    {"tool": "fenicsx", "script": "poisson.py", "params": {"mesh_size": 32}},
    {"tool": "fenicsx", "script": "poisson.py", "params": {"mesh_size": 64}},
    {"tool": "fenicsx", "script": "poisson.py", "params": {"mesh_size": 128}}
  ]
}
```

### 7. Log Everything

Keep records of workflow execution:

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('workflow.log'),
        logging.StreamHandler()
    ]
)

logging.info(f"Starting workflow with {len(tasks)} tasks")
task_ids = pipeline.submit_workflow(tasks)
logging.info(f"Submitted tasks: {task_ids}")
```

### 8. Test Incrementally

Start small and scale up:

```python
# 1. Test single task
task_id = pipeline.submit_task("fenicsx", "poisson.py", {"mesh_size": 16})
result = pipeline.wait_for_task(task_id, timeout=60)

# 2. Test small workflow
tasks = [{"tool": "fenicsx", "script": "poisson.py", "params": {"mesh_size": i}} 
         for i in [16, 32]]
task_ids = pipeline.submit_workflow(tasks)

# 3. Scale to full workflow
# ... full parameter sweep ...
```

---

## Related Documentation

- **[CLI_REFERENCE.md](CLI_REFERENCE.md)** - Complete CLI command reference
- **[TASK_PIPELINE.md](TASK_PIPELINE.md)** - Python API documentation
- **[DOCKER_COMPOSE.md](DOCKER_COMPOSE.md)** - Docker Compose setup and usage
- **[K3D.md](K3D.md)** - Kubernetes cluster management
- **[HELM_QUICKSTART.md](HELM_QUICKSTART.md)** - Helm deployment guide
- **[JOB_MONITORING.md](JOB_MONITORING.md)** - Monitoring and metrics
- **[CELERY_QUICK_REFERENCE.md](CELERY_QUICK_REFERENCE.md)** - Low-level Celery usage
- **[src/sim-toolbox/ORCHESTRATION.md](src/sim-toolbox/ORCHESTRATION.md)** - Adapter implementation details

---

## Examples and Demos

### Example Scripts

The repository includes several example scripts:

- `src/agent/example_task_pipeline.py` - TaskPipeline usage examples
- `src/agent/example_cli_integration.py` - CLI integration examples
- `src/agent/example_job_submission.py` - Direct Celery examples
- `cli_demo.sh` - CLI demonstration script

### Running Examples

```bash
# Run TaskPipeline examples
cd src/agent
python3 example_task_pipeline.py

# Run CLI demo
cd ../..
./cli_demo.sh
```

### Sample Workflows

- `example_workflow.json` - Multi-tool parallel workflow
- Create custom workflows in the same format

---

## Next Steps

1. **Start with Docker Compose** for local development
2. **Experiment with single simulations** using the CLI
3. **Try the example workflows** to understand patterns
4. **Create custom workflows** for your use cases
5. **Scale to k3d** when you need multi-node capabilities
6. **Deploy with Helm** for production environments

For questions or issues, refer to the troubleshooting section or open an issue on the GitHub repository.
