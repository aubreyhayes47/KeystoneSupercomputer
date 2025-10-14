# Docker Compose for Keystone Supercomputer

## Overview

This Docker Compose configuration orchestrates multiple services for the Keystone Supercomputer project, enabling multi-service workflows for simulation execution, job queuing, and agentic coordination.

### Architecture

The orchestration includes the following services:

1. **Redis** - Message broker and cache for background job queue
2. **Celery Worker** - Background job processing for simulation tasks
3. **FEniCSx** - Finite Element Method (FEM) simulation service
4. **LAMMPS** - Molecular Dynamics (MD) simulation service
5. **OpenFOAM** - Computational Fluid Dynamics (CFD) simulation service
6. **Agent Service** - Agentic core for orchestration (future enhancement)

```
┌─────────────────────────────────────────────────────────┐
│                   Keystone Network                       │
│                                                          │
│  ┌──────────┐                                           │
│  │  Redis   │  ◄──── Message Broker & Cache             │
│  └────┬─────┘                                           │
│       │                                                  │
│       ├──────► ┌───────────────┐                       │
│       │        │ Celery Worker │  (Job Queue)           │
│       │        └───────┬───────┘                       │
│       │                │                                 │
│       │                ├──────► ┌──────────┐           │
│       │                │        │ FEniCSx  │  (FEM)    │
│       │                │        └──────────┘           │
│       │                │                                 │
│       │                ├──────► ┌──────────┐           │
│       │                │        │  LAMMPS  │  (MD)     │
│       │                │        └──────────┘           │
│       │                │                                 │
│       │                └──────► ┌──────────┐           │
│       │                         │ OpenFOAM │  (CFD)    │
│       │                         └──────────┘           │
│       │                                                  │
│       └──────► ┌──────────┐                            │
│                │  Agent   │  (Orchestration - Future)   │
│                └──────────┘                            │
└─────────────────────────────────────────────────────────┘
```

---

## Quick Start

### Prerequisites

- Docker Engine 20.10+
- Docker Compose V2 (or docker-compose 1.29+)
- 8GB+ RAM recommended
- 20GB+ free disk space

### Starting Services

#### Start all core services (Redis only by default):
```bash
docker compose up -d
```

#### Build all simulation images:
```bash
docker compose build
```

#### Run a specific simulation service:
```bash
# FEniCSx example
docker compose run --rm fenicsx python3 poisson.py

# LAMMPS example
docker compose run --rm lammps lmp -in /data/input/example.lammps

# OpenFOAM example
docker compose run --rm openfoam python3 /workspace/example_cavity.py
```

#### Start services with simulation profile:
```bash
docker compose --profile simulation up -d
```

### Stopping Services

```bash
# Stop all running services
docker compose down

# Stop and remove volumes (WARNING: deletes data)
docker compose down -v
```

---

## Service Details

### Redis Service

**Purpose:** Message broker and cache for background job queuing (Celery integration active).

**Port:** `6379` (exposed to host)

**Volumes:**
- `redis-data:/data` - Persistent Redis data with AOF (Append-Only File) enabled

**Health Check:** Pings Redis every 5 seconds to ensure availability

**Usage:**
```bash
# Connect to Redis CLI
docker compose exec redis redis-cli

# Check Redis status
docker compose exec redis redis-cli ping
```

---

### Celery Worker Service

**Purpose:** Background job processing for simulation task orchestration.

**Broker:** Uses Redis as message broker

**Backend:** Uses Redis for result storage

**Concurrency:** 2 workers by default (configurable via environment)

**Features:**
- Asynchronous task execution
- Task progress tracking
- Result persistence
- Automatic retries on failure
- Health monitoring

**Usage:**
```bash
# Check worker status
docker compose ps celery-worker

# View worker logs
docker compose logs -f celery-worker

# Restart worker
docker compose restart celery-worker
```

**Available Tasks:**
- `run_simulation` - Execute a simulation task
- `health_check` - Verify worker health
- `list_simulations` - List available tools and scripts

---

### FEniCSx Service

**Purpose:** Run finite element method simulations for PDEs.

**Image:** `fenicsx-toolbox:latest`

**Volumes:**
- `./data/fenicsx:/data` - All data (input scripts and output results)
- `./src/sim-toolbox/fenicsx:/app` - Source code (for development)

**Environment Variables:**
- `PYTHONUNBUFFERED=1` - Immediate output logging
- `SIMULATION_TYPE=fenicsx` - Service identifier

**Example Usage:**
```bash
# Run default Poisson equation
docker compose run --rm fenicsx poisson.py

# Run custom script with mounted data
cp my_script.py data/fenicsx/
docker compose run --rm fenicsx /data/my_script.py

# Interactive shell for debugging
docker compose run --rm fenicsx bash
```

**Using Python Adapter:**
```python
from fenicsx_adapter import FEniCSxAdapter

adapter = FEniCSxAdapter(
    image_name="fenicsx-toolbox",
    output_dir="./data/fenicsx/output"
)
result = adapter.run_simulation()
```

---

### LAMMPS Service

**Purpose:** Run molecular dynamics simulations for atomic/molecular systems.

**Image:** `keystone/lammps:latest`

**Volumes:**
- `./data/lammps:/data` - All data (input scripts and output results)

**Environment Variables:**
- `SIMULATION_TYPE=lammps` - Service identifier

**Example Usage:**
```bash
# Run example Lennard-Jones simulation
cp src/sim-toolbox/lammps/example.lammps data/lammps/
docker compose run --rm lammps lmp -in /data/example.lammps

# Check output
ls data/lammps/

# Interactive LAMMPS shell
docker compose run --rm lammps bash
```

**Using Python Adapter:**
```python
from lammps_adapter import LAMMPSAdapter

adapter = LAMMPSAdapter(
    image_name="keystone/lammps:latest",
    output_dir="./data/lammps/output"
)
result = adapter.run_simulation(
    input_script="example.lammps",
    log_file="lammps.log"
)
```

---

### OpenFOAM Service

**Purpose:** Run computational fluid dynamics simulations.

**Image:** `openfoam-toolbox:latest`

**Volumes:**
- `./data/openfoam:/data` - All data (case files and results)
- `./src/sim-toolbox/openfoam:/workspace` - Scripts and utilities

**Environment Variables:**
- `PYTHONUNBUFFERED=1` - Immediate output logging
- `SIMULATION_TYPE=openfoam` - Service identifier
- `FOAM_RUN=/workspace/foam-run` - OpenFOAM run directory

**Example Usage:**
```bash
# Run cavity flow example
docker compose run --rm openfoam python3 /workspace/example_cavity.py

# Run existing OpenFOAM case
cp -r my_case/ data/openfoam/
docker compose run --rm openfoam bash -c "cd /data/my_case && blockMesh && icoFoam"

# Check solver output
ls data/openfoam/

# Interactive shell
docker compose run --rm openfoam bash
```

**Using Python Adapter:**
```python
from openfoam_adapter import OpenFOAMAdapter

adapter = OpenFOAMAdapter(
    image_name="openfoam-toolbox",
    output_dir="./data/openfoam/output"
)
result = adapter.run_simulation(
    case_setup_script="example_cavity.py"
)
```

---

## Configuration

### Environment Variables

You can customize service behavior using environment variables. Create a `.env` file in the project root:

```bash
# Redis Configuration
REDIS_PORT=6379
REDIS_PASSWORD=your_secure_password

# Simulation Resources
FENICSX_MEMORY_LIMIT=4g
LAMMPS_MEMORY_LIMIT=4g
OPENFOAM_MEMORY_LIMIT=8g

# Data Directories
DATA_ROOT=./data
```

Then reference in `docker-compose.yml`:
```yaml
services:
  redis:
    ports:
      - "${REDIS_PORT}:6379"
```

See `.env.example` for a complete template.

---

### Volume Mounts

All simulation services use standardized volume mount patterns:

```
./data/<service>  → /data  (in container)
```

This ensures:
- **Consistent paths** across all services
- **Easy data transfer** between host and container
- **Persistent results** after container shutdown
- **Simplified management** with a single mount point per service

#### Creating Data Directories

```bash
# Create all required data directories
mkdir -p data/{fenicsx,lammps,openfoam}

# Verify structure
tree data/
# data/
# ├── fenicsx
# ├── lammps
# └── openfoam
```

---

### Resource Limits

To prevent resource exhaustion, you can add resource limits to services:

```yaml
services:
  fenicsx:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          cpus: '1.0'
          memory: 2G
```

---

## Networking

All services are connected via the `keystone-network` bridge network. This enables:

- **Service discovery** by name (e.g., `redis://redis:6379`)
- **Inter-service communication** for job queuing and coordination
- **Network isolation** from other Docker networks

### Accessing Services from Host

- Redis: `localhost:6379`
- Ollama (external): `localhost:11434`

### Accessing Services Between Containers

- Redis: `redis:6379`
- FEniCSx: `fenicsx:8080` (if service exposes port)

---

## Common Workflows

### Workflow 1: Run Integration Tests

```bash
# Build all images
docker compose build

# Run integration test using adapters
cd src/sim-toolbox
python3 integration_test.py --build

# Or run tests with Docker Compose
docker compose run --rm fenicsx python3 /app/fenicsx_adapter.py
docker compose run --rm lammps python3 /data/input/lammps_adapter.py
docker compose run --rm openfoam python3 /workspace/openfoam_adapter.py
```

### Workflow 2: Batch Simulations

```bash
# Prepare multiple input files
for i in {1..5}; do
  cp simulation_template.py data/fenicsx/input/sim_$i.py
done

# Run batch simulations
for i in {1..5}; do
  docker compose run --rm fenicsx python3 /data/input/sim_$i.py
done

# Collect results
ls data/fenicsx/output/
```

### Workflow 3: Development and Debugging

```bash
# Start Redis for queue backend
docker compose up -d redis

# Enter interactive container
docker compose run --rm fenicsx bash

# Inside container:
# - Edit scripts
# - Run tests
# - Debug issues
python3 /app/poisson.py
exit

# View logs
docker compose logs redis
```

### Workflow 4: Job Queue Management

```bash
# Start Redis and Celery worker
docker compose up -d redis celery-worker

# Submit a job programmatically
python3 << EOF
from celery_app import run_simulation_task
task = run_simulation_task.delay(
    tool="fenicsx",
    script="poisson.py",
    params={"mesh_size": 32}
)
print(f"Task ID: {task.id}")
EOF

# Check worker status
docker compose logs celery-worker

# Monitor Redis queue
docker compose exec redis redis-cli llen celery

# Run example job submission script
cd src/agent
python3 example_job_submission.py
```

---

## Integration with Agentic Core

The Docker Compose setup integrates with Celery for automated job queue management and orchestration:

### Celery Job Queue Integration

The Celery worker service provides background job processing with Redis as the message broker. This enables asynchronous simulation execution and result tracking.

**Key Features:**
- Asynchronous task execution
- Task progress monitoring
- Result persistence in Redis
- Automatic retries on failure
- Scalable worker pool

### Agent Job Submission

Agents can submit simulation tasks to the job queue using the Celery API:

**Basic Job Submission:**
```python
from celery_app import run_simulation_task

# Submit a simulation task
task = run_simulation_task.delay(
    tool="fenicsx",
    script="poisson.py",
    params={"mesh_size": 64}
)

print(f"Task ID: {task.id}")
print(f"Task State: {task.state}")
```

**Monitor Task Progress:**
```python
import time

# Poll task status
while not task.ready():
    if task.state == 'RUNNING':
        meta = task.info
        if isinstance(meta, dict) and 'progress' in meta:
            print(f"Progress: {meta['progress']}%")
    time.sleep(2)
```

**Retrieve Results:**
```python
# Get task result (blocking until complete)
result = task.get(timeout=300)

print(f"Status: {result['status']}")
print(f"Tool: {result['tool']}")
print(f"Script: {result['script']}")
print(f"Return Code: {result['returncode']}")

if result['status'] == 'success':
    print("Simulation completed successfully!")
    print(f"Output: {result['stdout']}")
```

**Complete Example:**
```python
# Full agent workflow with job queue
from agent_state import AgentState
from langchain_ollama import ChatOllama
from celery_app import run_simulation_task, health_check_task

# 1. Agent decides which simulation to run (using LLM)
llm = ChatOllama(model="llama3:8b")
# ... agent decision logic ...

# 2. Check worker health
health = health_check_task.delay()
print(health.get())  # {'status': 'healthy', 'worker': 'operational'}

# 3. Submit job to queue
task = run_simulation_task.delay(
    tool="fenicsx",
    script="poisson.py",
    params={"mesh_size": 64}
)

# 4. Monitor task progress
while not task.ready():
    time.sleep(2)

# 5. Retrieve and process results
result = task.get()
if result['status'] == 'success':
    # Update agent state with results
    state = AgentState(
        messages=[],
        simulation_params=result['params'],
        artifact_paths=result.get('artifacts', [])
    )
```

**Run the Example:**
```bash
# Start services
docker compose up -d redis celery-worker

# Run example script
cd src/agent
python3 example_job_submission.py
```

### Available Tasks

The Celery worker provides the following tasks:

1. **run_simulation** - Execute a simulation task
   - Parameters: `tool` (str), `script` (str), `params` (dict)
   - Returns: Task result with status, output, and artifacts

2. **health_check** - Verify worker health
   - Parameters: None
   - Returns: Health status and message

3. **list_simulations** - List available tools and scripts
   - Parameters: None
   - Returns: Dictionary of available simulation tools

### Future Agent Service

The `agent` service (currently commented out in docker-compose.yml) will:
- Connect to Ollama LLM for decision-making
- Use the Celery job queue for task orchestration
- Orchestrate complex multi-step workflows
- Monitor and report results
- Enable conversational interfaces for simulation management

---

## Troubleshooting

### Issue: Cannot connect to Redis

**Symptom:** `Error connecting to redis://localhost:6379`

**Solution:**
```bash
# Check if Redis is running
docker compose ps

# Check Redis logs
docker compose logs redis

# Restart Redis
docker compose restart redis

# Test connection
docker compose exec redis redis-cli ping
```

---

### Issue: Celery worker not processing tasks

**Symptom:** Tasks stuck in PENDING state, no worker activity

**Solution:**
```bash
# Check if Celery worker is running
docker compose ps celery-worker

# Check worker logs for errors
docker compose logs celery-worker

# Restart worker
docker compose restart celery-worker

# Verify Redis connection
docker compose exec celery-worker python3 -c "from celery_app import celery_app; print(celery_app.connection().connect())"

# Check task queue in Redis
docker compose exec redis redis-cli llen celery
```

---

### Issue: Task execution fails

**Symptom:** Task returns 'failed' or 'error' status

**Solution:**
```bash
# Check worker logs for detailed error
docker compose logs celery-worker | tail -50

# Verify Docker socket is mounted
docker compose exec celery-worker ls -l /var/run/docker.sock

# Test docker command inside worker
docker compose exec celery-worker docker ps

# Check if simulation images are built
docker images | grep -E "fenicsx|lammps|openfoam"
```

---

### Issue: Simulation containers exit immediately

**Symptom:** `docker compose run fenicsx` exits without output

**Solution:**
```bash
# Check if image exists
docker images | grep fenicsx

# Rebuild image
docker compose build fenicsx

# Run with explicit command
docker compose run --rm fenicsx python3 --version

# Check for errors in logs
docker compose logs fenicsx
```

---

### Issue: Volume mount permission denied

**Symptom:** `Permission denied: '/data/output'`

**Solution:**
```bash
# Fix directory permissions
sudo chown -R $USER:$USER data/

# Or run with user override (Linux)
docker compose run --rm -u $(id -u):$(id -g) fenicsx python3 poisson.py
```

---

### Issue: Out of disk space

**Symptom:** `no space left on device`

**Solution:**
```bash
# Check disk usage
docker system df

# Remove unused images and containers
docker system prune -a

# Remove unused volumes (WARNING: deletes data)
docker volume prune
```

---

### Issue: Container build fails

**Symptom:** Build errors during `docker compose build`

**Solution:**
```bash
# Build with no cache
docker compose build --no-cache fenicsx

# Check Dockerfile syntax
cd src/sim-toolbox/fenicsx
docker build -t test-image .

# Check available resources
docker info | grep -i memory
```

---

## Advanced Usage

### Using Docker Compose Override

Create `docker-compose.override.yml` for local customizations (already in `.gitignore`):

```yaml
# docker-compose.override.yml
version: '3.8'

services:
  fenicsx:
    volumes:
      - /my/custom/path:/data/custom
    deploy:
      resources:
        limits:
          cpus: '4.0'
          memory: 8G
```

### Using Profiles

Profiles allow selective service startup:

```bash
# Start only Redis (default)
docker compose up -d

# Start simulation services
docker compose --profile simulation up -d

# Start all services (when agent is ready)
docker compose --profile simulation --profile agent up -d
```

---

## Performance Tips

1. **Use volume caching** for better I/O performance:
   ```yaml
   volumes:
     - ./data/fenicsx/output:/data/output:cached
   ```

2. **Limit container resources** to prevent system overload:
   ```yaml
   deploy:
     resources:
       limits:
         cpus: '2.0'
         memory: 4G
   ```

3. **Use BuildKit** for faster builds:
   ```bash
   DOCKER_BUILDKIT=1 docker compose build
   ```

4. **Pre-pull base images**:
   ```bash
   docker pull dolfinx/dolfinx:stable
   docker pull ubuntu:22.04
   docker pull openfoam/openfoam11-paraview510:latest
   ```

---

## Security Considerations

1. **Redis Authentication:** Add password protection for production:
   ```yaml
   redis:
     command: redis-server --requirepass your_secure_password
   ```

2. **Network Isolation:** Use internal networks for service-to-service communication:
   ```yaml
   networks:
     keystone-internal:
       internal: true
   ```

3. **Read-only Volumes:** Mount input directories as read-only:
   ```yaml
   volumes:
     - ./data/fenicsx/input:/data/input:ro
   ```

---

## References

- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Docker Networking Guide](https://docs.docker.com/network/)
- [Phase 4 Roadmap](../README.md#phase-4-orchestration--workflows)
- [Simulation Adapters](src/sim-toolbox/ADAPTERS.md)
- [Integration Tests](src/sim-toolbox/INTEGRATION_TEST.md)

---

## Next Steps

1. **Test the configuration:**
   ```bash
   docker compose config  # Validate syntax
   docker compose build   # Build images
   docker compose up -d redis celery-worker  # Start Redis and Celery
   ```

2. **Run integration tests:**
   ```bash
   cd src/sim-toolbox
   python3 integration_test.py --build
   ```

3. **Test Celery job queue:**
   ```bash
   # Run example job submission
   cd src/agent
   python3 example_job_submission.py
   
   # Or submit jobs programmatically
   python3 -c "from celery_app import health_check_task; print(health_check_task.delay().get())"
   ```

4. **Enable Agent Service:**
   - Uncomment agent service in `docker-compose.yml`
   - Create agent Dockerfile
   - Connect to Ollama and Celery job queue

---

**Last Updated:** 2025-10-14  
**Version:** 1.0.0  
**Maintainer:** Keystone Supercomputer Project
