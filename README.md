# Keystone Supercomputer

Keystone Supercomputer is a personal open-source scientific computing platform designed to orchestrate simulations, automate workflows, and leverage local and cloud resources—all managed by agentic AI interfaces. This project aims to make advanced simulation, reproducibility, and intelligent automation accessible and scalable for individual researchers, engineers, and power users.

---

## Project Roadmap & Progress

Below is the full 10-phase roadmap for developing Keystone Supercomputer, with completed steps clearly marked.

---

### **Phase 0: Foundational Infrastructure** ✔️ **(Completed)**
- **Hardware Provisioning:** Framework Laptop 13 assembled, 500GB NVMe installed.
- **OS Installation:** Ubuntu 24.04 LTS.
- **Disk Partitioning:** Default single partition.
- **Driver Setup:** Intel GPU and OpenCL working; oneAPI Base Toolkit installed.
- **User Workspace:** Dedicated user (`sim_user`) and organized project directories.

---

### **Phase 1: Development Environment** ✔️ **(Completed)**
- **Python Environment:** `uv` installed, virtualenv created.
- **Container Engine:** Docker Engine installed and verified.
- **Version Control:** Git repo initialized with `.gitignore` and `README.md`.

---

### **Phase 2: Agentic Core** ✔️ **(Completed)**
- **Agent Framework:** Installed LangChain and LangGraph; agent state model scaffolded.
- **Conversational CLI:** CLI built using `click`, integrated with local Ollama LLM for agent interaction.
- **Workflow CLI:** Comprehensive CLI commands for workflow submission and monitoring - see [CLI_REFERENCE.md](CLI_REFERENCE.md).

---

### **Phase 3: Simulation Toolbox** ✔️ **(Completed)**
- **Containerized Tools:** Scaffolded `sim-toolbox` directory; Dockerfile and demo for FEniCSx in progress.
- **Standardized Entrypoints:** Planning `/data` volume mounts and uniform container interfaces.
- **Tool Adapter Pattern:** Writing Python adapters for simulation tools.
- **Integration Testing:** Created comprehensive integration test validating end-to-end workflow automation across FEniCSx, LAMMPS, and OpenFOAM.

---

### **Phase 4: Orchestration & Workflows** ✔️ **(Completed)**
- **Docker Compose:** ✔️ Multi-service orchestration with `docker-compose.yml` - see [DOCKER_COMPOSE.md](DOCKER_COMPOSE.md).
- **Job Queue:** ✔️ Celery + Redis integration for background task processing with worker service.
- **Local Kubernetes:** ✔️ Multi-node k3d cluster setup with `kubectl` and `helm` - see [K3D.md](K3D.md).

---

### **Phase 5: Performance Optimization** 🔜 **(Upcoming)**
- **Hardware Acceleration:** GPU/NPU access in containers.
- **Parallelism:** OpenMP/MPI configuration.

---

### **Phase 6: Multi-Agent System** 🔜 **(Upcoming)**
- **Agent Architecture:** LangGraph conductor-performer graphs.
- **Specialized Agents:** For requirements, planning, simulation, visualization, and validation.

---

### **Phase 7: Reproducibility & Trust** 🔜 **(Upcoming)**
- **Provenance Logging:** Automated `provenance.json` for every run.
- **Benchmark Registry:** Curated cases and automated validation.

---

### **Phase 8: Scaling Out (Optional)** 🔜 **(Upcoming)**
- **Home Lab Cluster:** Multi-node local cluster with k3s.
- **Cloud Burst:** Agent for on-demand cloud compute.

---

### **Phase 9: User Interfaces** 🔜 **(Upcoming)**
- **CLI Features:** Expanding CLI commands.
- **Web Dashboard:** Flask API backend, Next.js frontend.
- **Visualization:** Automated plotting and ParaView integration.

---

### **Phase 10: Governance & Safety** 🔜 **(Upcoming)**
- **Policy as Code:** Enforce resource and cost limits via `policy.yaml`.
- **Human-in-the-Loop:** Interrupt and checkpoint logic for agent workflows.
- **Audit Logging:** Append-only logs for actions and safety events.

---

## Progress Legend

- ✔️ Completed
- ⏳ In Progress
- 🔜 Upcoming

---

## Getting Started

Clone the repo and see the latest phase’s instructions or open an issue for help.  
Project is evolving—please check back for new documentation, examples, and simulation tool adapters.

---

## CLI - Workflow Submission and Monitoring

The Keystone Supercomputer CLI provides comprehensive commands for workflow submission and job monitoring. See [CLI_REFERENCE.md](CLI_REFERENCE.md) for complete documentation.

### Quick Start

```bash
cd src/agent

# Check worker health
python3 cli.py health

# List available simulation tools
python3 cli.py list-tools

# Submit a simulation task
python3 cli.py submit fenicsx poisson.py -p '{"mesh_size": 64}' --wait

# Submit a workflow
python3 cli.py submit-workflow ../../example_workflow.json --parallel --wait

# Check task status
python3 cli.py status <task-id> --monitor
```

### Available Commands

- `health` - Check Celery worker health
- `list-tools` - List available simulation tools
- `submit` - Submit a single simulation task
- `status` - Check task status and monitor progress
- `cancel` - Cancel a running task
- `submit-workflow` - Submit multiple tasks as a workflow
- `workflow-status` - Check status of workflow tasks
- `ask` - Interact with LLM agent

---

## Docker Compose Orchestration

The project includes a comprehensive Docker Compose setup for multi-service orchestration. See [DOCKER_COMPOSE.md](DOCKER_COMPOSE.md) for full documentation.

### Quick Start

```bash
# Run the quick start script
./docker-compose-quickstart.sh

# Build simulation images
docker compose build

# Run a test simulation
docker compose run --rm fenicsx poisson.py

# Start Redis and Celery worker
docker compose up -d redis celery-worker

# Stop all services
docker compose down
```

### Available Services

- **Redis** - Message broker for job queuing
- **Celery Worker** - Background job processing
- **FEniCSx** - Finite Element Method simulations
- **LAMMPS** - Molecular Dynamics simulations
- **OpenFOAM** - Computational Fluid Dynamics simulations

### Job Queue Management

The Celery worker provides asynchronous job execution. Use the Task Pipeline module for a high-level, agent-friendly interface:

```python
from task_pipeline import TaskPipeline

# Initialize pipeline
pipeline = TaskPipeline()

# Submit and monitor a simulation task
task_id = pipeline.submit_task(
    tool="fenicsx",
    script="poisson.py",
    params={"mesh_size": 64}
)

# Wait for completion
result = pipeline.wait_for_task(task_id, timeout=300)
```

See [TASK_PIPELINE.md](TASK_PIPELINE.md) for comprehensive documentation and examples.

For direct Celery usage, see [CELERY_QUICK_REFERENCE.md](CELERY_QUICK_REFERENCE.md).

---

## Local Kubernetes with k3d

The project includes a multi-node Kubernetes cluster setup using k3d for advanced orchestration, scaling, and production-like testing. See [K3D.md](K3D.md) for full documentation.

### Quick Start

```bash
# Create and configure the k3d cluster
./k3d-setup.sh

# Check cluster status
kubectl get nodes
kubectl get pods -n keystone

# Run a simulation
./k3d-manage.sh run-simulation fenicsx poisson.py

# Scale Celery workers
./k3d-manage.sh scale celery-worker 5

# View logs
./k3d-manage.sh logs celery-worker

# Stop the cluster
./k3d-manage.sh stop
```

### Cluster Architecture

- **2 Server Nodes**: High-availability control plane
- **3 Agent Nodes**: Distributed worker nodes
- **Local Registry**: For custom container images
- **Load Balancer**: Automatic service load balancing

### Kubernetes Services

- **Redis** - Message broker (ClusterIP)
- **Celery Workers** - Background job processing (2+ replicas)
- **Simulation Jobs** - On-demand FEniCSx, LAMMPS, OpenFOAM jobs

See [K3D.md](K3D.md) for comprehensive cluster management, troubleshooting, and advanced usage.

