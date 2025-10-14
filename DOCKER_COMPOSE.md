# Docker Compose for Keystone Supercomputer

## Overview

This Docker Compose configuration orchestrates multiple services for the Keystone Supercomputer project, enabling multi-service workflows for simulation execution, job queuing, and agentic coordination.

### Architecture

The orchestration includes the following services:

1. **Redis** - Message broker and cache for background job queue
2. **FEniCSx** - Finite Element Method (FEM) simulation service
3. **LAMMPS** - Molecular Dynamics (MD) simulation service
4. **OpenFOAM** - Computational Fluid Dynamics (CFD) simulation service
5. **Agent Service** - Agentic core for orchestration (future enhancement)

```
┌─────────────────────────────────────────────────────────┐
│                   Keystone Network                       │
│                                                          │
│  ┌──────────┐                                           │
│  │  Redis   │  ◄──── Message Broker & Cache             │
│  └────┬─────┘                                           │
│       │                                                  │
│       ├──────► ┌──────────┐                            │
│       │        │ FEniCSx  │  (FEM Simulations)         │
│       │        └──────────┘                            │
│       │                                                  │
│       ├──────► ┌──────────┐                            │
│       │        │  LAMMPS  │  (MD Simulations)          │
│       │        └──────────┘                            │
│       │                                                  │
│       ├──────► ┌──────────┐                            │
│       │        │ OpenFOAM │  (CFD Simulations)         │
│       │        └──────────┘                            │
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

**Purpose:** Message broker and cache for background job queuing (Celery integration planned).

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

---

## Integration with Agentic Core

The Docker Compose setup is designed to integrate with the agentic core for automated orchestration:

### Future Agent Service

The `agent` service (currently commented out) will:
- Connect to Ollama LLM for decision-making
- Use Redis for job queuing with Celery
- Orchestrate simulation workflows
- Monitor and report results

**Planned Integration:**
```python
# Agent decides which simulation to run
from agent_state import AgentState
from langchain_ollama import ChatOllama

# Agent submits job to queue
from celery_app import run_simulation_task

task = run_simulation_task.delay(
    tool="fenicsx",
    script="poisson.py",
    params={"mesh_size": 64}
)

# Monitor task progress
result = task.get()
```

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
   docker compose up -d redis  # Start Redis
   ```

2. **Run integration tests:**
   ```bash
   cd src/sim-toolbox
   python3 integration_test.py --build
   ```

3. **Integrate with Celery:**
   - Create `celery_app.py` for background tasks
   - Configure Celery workers to use Redis backend
   - Define simulation tasks for queued execution

4. **Enable Agent Service:**
   - Uncomment agent service in `docker-compose.yml`
   - Create agent Dockerfile
   - Connect to Ollama and Redis

---

**Last Updated:** 2025-10-14  
**Version:** 1.0.0  
**Maintainer:** Keystone Supercomputer Project
