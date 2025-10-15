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
- **Workflow Testing:** ✔️ Comprehensive unit and integration tests for agentic workflow orchestration - see [src/agent/TEST_WORKFLOW_ORCHESTRATION.md](src/agent/TEST_WORKFLOW_ORCHESTRATION.md).

---


### **Phase 5: Performance Optimization** ⏳ **(In Progress)**
- **Hardware Acceleration:** GPU/NPU access in containers - see [GPU_ACCELERATION.md](GPU_ACCELERATION.md).
- **Performance Benchmarking:** ✔️ Standardized benchmarks for CPU vs GPU/NPU performance comparison - see [BENCHMARK_GUIDE.md](BENCHMARK_GUIDE.md).
- **Container Optimization:** ✔️ Optimized container images for size, build time, and runtime performance - see [CONTAINER_OPTIMIZATION.md](CONTAINER_OPTIMIZATION.md).
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

For a comprehensive guide to launching, monitoring, and managing orchestrated simulation workflows, see **[ORCHESTRATION_GUIDE.md](ORCHESTRATION_GUIDE.md)**.

### Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/aubreyhayes47/KeystoneSupercomputer.git
cd KeystoneSupercomputer

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start orchestration services
./docker-compose-quickstart.sh

# 4. Submit your first simulation
cd src/agent
python3 cli.py submit fenicsx poisson.py --wait
```

### Documentation Quick Links

- **[ORCHESTRATION_GUIDE.md](ORCHESTRATION_GUIDE.md)** - Complete workflow orchestration guide (START HERE)
- **[PARALLEL_SIMULATIONS.md](PARALLEL_SIMULATIONS.md)** - OpenMP and MPI parallel computing guide
- **[PARALLEL_EXAMPLES.md](PARALLEL_EXAMPLES.md)** - Quick parallel execution examples
- **[GPU_ACCELERATION.md](GPU_ACCELERATION.md)** - GPU/NPU hardware acceleration setup
- **[CONTAINER_OPTIMIZATION.md](CONTAINER_OPTIMIZATION.md)** - Container image optimization techniques
- **[BENCHMARK_GUIDE.md](BENCHMARK_GUIDE.md)** - Performance benchmarking and comparison
- **[CLI_REFERENCE.md](CLI_REFERENCE.md)** - CLI command reference
- **[TASK_PIPELINE.md](TASK_PIPELINE.md)** - Python API documentation
- **[DOCKER_COMPOSE.md](DOCKER_COMPOSE.md)** - Docker Compose setup
- **[K3D.md](K3D.md)** - Kubernetes cluster setup
- **[HELM_QUICKSTART.md](HELM_QUICKSTART.md)** - Helm deployment guide
- **[JOB_MONITORING.md](JOB_MONITORING.md)** - Monitoring and metrics

Clone the repo and see the latest phase's instructions or open an issue for help.  
Project is evolving—please check back for new documentation, examples, and simulation tool adapters.
---

## CLI - Workflow Submission and Monitoring

The Keystone Supercomputer CLI provides comprehensive commands for workflow submission, job monitoring, and resource tracking. See [CLI_REFERENCE.md](CLI_REFERENCE.md) for complete documentation and [JOB_MONITORING.md](JOB_MONITORING.md) for monitoring details.

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

# View job history with resource usage
python3 cli.py job-history

# Display aggregate job statistics
python3 cli.py job-stats

# Get detailed information for a specific job
python3 cli.py job-details <task-id>
```

### Available Commands

- `health` - Check Celery worker health
- `list-tools` - List available simulation tools
- `submit` - Submit a single simulation task
- `status` - Check task status and monitor progress
- `cancel` - Cancel a running task
- `submit-workflow` - Submit multiple tasks as a workflow
- `workflow-status` - Check status of workflow tasks
- `job-history` - View job execution history with resource usage
- `job-stats` - Display aggregate job statistics
- `job-details` - Show detailed information for a specific job
- `ask` - Interact with LLM agent

---

## Job Monitoring and Resource Tracking

Keystone Supercomputer includes comprehensive monitoring for all simulation jobs with automatic tracking of:

- **Resource Usage**: CPU time, memory consumption, execution duration
- **Job Outcomes**: Success/failure status with detailed error information
- **Job History**: Persistent storage of all job executions
- **Statistics**: Aggregate metrics by tool and overall success rates

### Monitoring Features

Every job is automatically tracked with:
- CPU time (user and system) in seconds
- Peak memory usage in MB
- Total execution duration
- Job status (success, failed, timeout, error)
- Detailed error messages for failures

### Quick Examples

```bash
# View recent job history with resource usage
python3 cli.py job-history --limit 20

# Show aggregate statistics
python3 cli.py job-stats

# Get details for a specific job
python3 cli.py job-details <task-id>

# Filter by tool or status
python3 cli.py job-history --tool fenicsx --status failed
```

### Job History Storage

Job history is stored in `/tmp/keystone_jobs/jobs_history.jsonl` as newline-delimited JSON with complete resource metrics for each execution.

For comprehensive documentation, see [JOB_MONITORING.md](JOB_MONITORING.md).

---

## Testing & Quality Assurance

Keystone Supercomputer includes comprehensive test suites for agentic workflow orchestration and multi-step simulation execution.

### Test Coverage

- **Unit Tests:** Validate workflow orchestration, task pipeline, CLI, and job monitoring components
- **Integration Tests:** End-to-end testing of agentic workflows through Docker Compose services
- **Orchestration Tests:** Validate multi-step workflows with sequential and parallel execution

### Running Tests

```bash
# Run all unit tests
cd src/agent
python3 run_all_tests.py

# Run specific test suites
python3 test_workflow_orchestration.py  # Workflow orchestration
python3 test_task_pipeline.py           # Task pipeline
python3 test_cli.py                     # CLI commands
python3 ../test_job_monitor.py          # Job monitoring

# Run integration tests (requires Docker Compose services)
docker compose up -d redis celery-worker
python3 test_agentic_workflow_integration.py
```

### What's Tested

✅ **Workflow Orchestration**
- Sequential and parallel task execution
- Multi-step workflow coordination
- Agent state management throughout workflows
- Error handling and recovery
- Task cancellation and cleanup

✅ **Container Orchestration**
- Docker Compose service integration
- Celery task queue processing
- Redis message broker communication
- Simulation tool execution (FEniCSx, LAMMPS, OpenFOAM)

✅ **Agent Interfaces**
- TaskPipeline API for agent-driven workflows
- Status tracking and monitoring
- Progress callbacks and notifications
- Result collection and artifact management

For comprehensive testing documentation, see [src/agent/TEST_WORKFLOW_ORCHESTRATION.md](src/agent/TEST_WORKFLOW_ORCHESTRATION.md).

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

---

## Helm Charts for Kubernetes Deployment

Keystone Supercomputer provides Helm charts for simplified, production-ready Kubernetes deployments. See [HELM_QUICKSTART.md](HELM_QUICKSTART.md) and [k8s/helm/README.md](k8s/helm/README.md) for comprehensive documentation.

### Quick Start

```bash
# Install complete simulation stack
helm install keystone-sim k8s/helm/keystone-simulation \
  -n keystone \
  --create-namespace

# Install with custom configuration
helm install keystone-sim k8s/helm/keystone-simulation \
  -n keystone \
  --create-namespace \
  -f k8s/helm/values-production.yaml

# Check deployment
kubectl get all -n keystone

# Run a simulation
kubectl create job -n keystone fenicsx-run-1 \
  --from=job/fenicsx-simulation
```

### Available Configurations

- **`values-dev.yaml`** - Development environment with minimal resources
- **`values-production.yaml`** - Production setup with high availability
- **`values-minimal.yaml`** - Minimal deployment for testing
- **`values-hpc.yaml`** - High-performance computing configuration

### Chart Components

The Helm chart deploys:
- Redis message broker with persistent storage
- Scalable Celery workers
- Job templates for FEniCSx, LAMMPS, and OpenFOAM simulations
- ConfigMaps for environment configuration
- Proper resource limits and health checks

### Upgrading

```bash
# Scale workers
helm upgrade keystone-sim k8s/helm/keystone-simulation \
  -n keystone \
  --set celeryWorker.replicaCount=10

# Update resources
helm upgrade keystone-sim k8s/helm/keystone-simulation \
  -n keystone \
  -f custom-values.yaml
```

See [k8s/helm/README.md](k8s/helm/README.md) for detailed configuration options, examples, and best practices.

---

## GPU/NPU Hardware Acceleration

Keystone Supercomputer supports GPU and NPU acceleration for computationally intensive simulations. See [GPU_ACCELERATION.md](GPU_ACCELERATION.md) for comprehensive setup instructions.

### Supported Hardware

- **NVIDIA GPUs**: CUDA-capable GPUs with Container Toolkit
- **Intel GPUs/NPUs**: Intel Integrated/Discrete GPUs with oneAPI support
- **AMD GPUs**: ROCm-compatible AMD GPUs

### Quick Start with GPU

```bash
# Docker Compose with NVIDIA GPU
docker compose -f docker-compose.gpu.yml --profile nvidia-gpu up -d
docker compose -f docker-compose.gpu.yml run --rm fenicsx-nvidia poisson.py

# Kubernetes with GPU support
helm install keystone-sim k8s/helm/keystone-simulation \
  -n keystone --create-namespace \
  -f k8s/helm/values-gpu.yaml
```

### What's Included

- Docker Compose GPU configurations ([docker-compose.gpu.yml](docker-compose.gpu.yml))
- Kubernetes GPU values file ([k8s/helm/values-gpu.yaml](k8s/helm/values-gpu.yaml))
- Detailed setup instructions for NVIDIA, Intel, and AMD hardware
- Device plugin installation guides
- GPU resource management and troubleshooting

For complete documentation, see [GPU_ACCELERATION.md](GPU_ACCELERATION.md).

---

## Performance Benchmarking

Keystone Supercomputer includes a comprehensive benchmarking system for measuring and comparing simulation performance across CPU, GPU, and NPU configurations. See [BENCHMARK_GUIDE.md](BENCHMARK_GUIDE.md) for complete documentation.

### Features

- **Standardized Benchmarks**: Pre-configured benchmarks for FEniCSx, LAMMPS, and OpenFOAM
- **Multi-Device Support**: Test performance on CPU, NVIDIA GPU, and Intel GPU/NPU
- **Performance Metrics**: Track execution time, CPU usage, memory consumption, and GPU utilization
- **Result Comparison**: Compare performance across different hardware configurations
- **Reproducibility**: Store detailed system information and benchmark parameters

### Quick Start

```bash
# Run CPU benchmark
cd src
python3 benchmark.py --tool fenicsx --device cpu --runs 3

# Run GPU benchmark
python3 benchmark.py --tool fenicsx --device gpu --runs 3

# Compare CPU vs GPU
python3 benchmark.py --compare <cpu-benchmark-id> <gpu-benchmark-id>

# Generate report
python3 benchmark.py --report
```

### Python API

```python
from benchmark import BenchmarkRunner

# Create runner
runner = BenchmarkRunner()

# Run benchmarks
cpu_result = runner.run_benchmark("fenicsx", device="cpu", runs=3)
gpu_result = runner.run_benchmark("fenicsx", device="gpu", runs=3)

# Compare results
comparison = runner.compare_results(cpu_result['id'], gpu_result['id'])
print(f"Speedup: {comparison['speedup']}x")

# Generate report
runner.generate_report(output_file="BENCHMARK_REPORT.md")
```

### Benchmark Results

Benchmarks record comprehensive performance metrics:
- **Execution Time**: Average, min, max, and standard deviation across runs
- **CPU Usage**: User and system CPU time consumed
- **Memory Usage**: Average and peak memory consumption
- **System Info**: Hardware specifications for reproducibility
- **Success Rate**: Percentage of successful benchmark runs

Results are stored in `/tmp/keystone_benchmarks/` and include:
- Line-delimited JSON log of all benchmarks
- Summary JSON file with aggregate results
- Markdown report for easy sharing

For comprehensive documentation and examples, see [BENCHMARK_GUIDE.md](BENCHMARK_GUIDE.md).

