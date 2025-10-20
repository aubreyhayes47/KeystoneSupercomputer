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
- **Parallel Orchestration:** ✔️ Batch workflow submission, parameter sweeps, and multi-core scheduling - see [PARALLEL_ORCHESTRATION.md](PARALLEL_ORCHESTRATION.md).

---


### **Phase 5: Performance Optimization** ✔️ **(Completed)**
- **Hardware Acceleration:** GPU/NPU access in containers - see [GPU_ACCELERATION.md](GPU_ACCELERATION.md).
- **Performance Benchmarking:** ✔️ Standardized benchmarks for CPU vs GPU/NPU performance comparison - see [BENCHMARK_GUIDE.md](BENCHMARK_GUIDE.md).
- **Container Optimization:** ✔️ Optimized container images for size, build time, and runtime performance - see [CONTAINER_OPTIMIZATION.md](CONTAINER_OPTIMIZATION.md).
- **Resource Profiling:** ✔️ Comprehensive resource profiling for CPU, memory, GPU, I/O during simulations - see [RESOURCE_PROFILING.md](RESOURCE_PROFILING.md).
- **Performance Tuning Guide:** ✔️ Comprehensive end-user guide for maximizing simulation performance - see [PERFORMANCE_TUNING_GUIDE.md](PERFORMANCE_TUNING_GUIDE.md).
- **Parallelism:** OpenMP/MPI configuration.

---

### **Phase 6: Multi-Agent System** ✔️ **(Completed)**
- **Agent Architecture:** ✔️ LangGraph conductor-performer graphs implemented - see [CONDUCTOR_PERFORMER_ARCHITECTURE.md](CONDUCTOR_PERFORMER_ARCHITECTURE.md).
- **Specialized Agents:** ✔️ Conductor, Performer (FEniCSx, LAMMPS, OpenFOAM), and Validator agents.
- **Workflow Orchestration:** ✔️ Task planning, delegation, error handling, and feedback loops.
- **Example Workflows:** ✔️ Structural analysis, multi-physics, parameter sweeps, and error recovery.
- **Testing:** ✔️ Comprehensive test suite with 37 tests covering all agent behaviors.

---

### **Phase 7: Reproducibility & Trust** ✔️ **(Completed)**
- **Provenance Logging:** ✔️ Automated `provenance.json` for every run - see [PROVENANCE_SCHEMA.md](PROVENANCE_SCHEMA.md).
- **Benchmark Registry:** ✔️ Curated reference cases with validation for all simulators - see [BENCHMARK_REGISTRY.md](BENCHMARK_REGISTRY.md).

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

- **[PROVENANCE_SCHEMA.md](PROVENANCE_SCHEMA.md)** - Provenance logging schema and reproducibility guide
- **[BENCHMARK_REGISTRY.md](BENCHMARK_REGISTRY.md)** - Reference benchmark cases for all simulators (NEW!)
- **[WORKFLOW_ROUTING_GUIDE.md](WORKFLOW_ROUTING_GUIDE.md)** - LangGraph routing logic and conditional edges
- **[WORKFLOW_ROUTING_QUICK_REFERENCE.md](WORKFLOW_ROUTING_QUICK_REFERENCE.md)** - Quick reference for routing patterns
- **[SIMULATION_WORKFLOW_AGENTS.md](SIMULATION_WORKFLOW_AGENTS.md)** - Specialized agents for simulation workflow stages
- **[CONDUCTOR_PERFORMER_ARCHITECTURE.md](CONDUCTOR_PERFORMER_ARCHITECTURE.md)** - Multi-agent system architecture
- **[ORCHESTRATION_GUIDE.md](ORCHESTRATION_GUIDE.md)** - Complete workflow orchestration guide (START HERE)
- **[PERFORMANCE_TUNING_GUIDE.md](PERFORMANCE_TUNING_GUIDE.md)** - Comprehensive performance optimization guide
- **[PARALLEL_ORCHESTRATION.md](PARALLEL_ORCHESTRATION.md)** - Parallel agent orchestration patterns
- **[PARALLEL_SIMULATIONS.md](PARALLEL_SIMULATIONS.md)** - OpenMP and MPI parallel computing guide
- **[PARALLEL_EXAMPLES.md](PARALLEL_EXAMPLES.md)** - Quick parallel execution examples
- **[GPU_ACCELERATION.md](GPU_ACCELERATION.md)** - GPU/NPU hardware acceleration setup
- **[CONTAINER_OPTIMIZATION.md](CONTAINER_OPTIMIZATION.md)** - Container image optimization techniques
- **[BENCHMARK_GUIDE.md](BENCHMARK_GUIDE.md)** - Performance benchmarking and comparison
- **[RESOURCE_PROFILING.md](RESOURCE_PROFILING.md)** - Comprehensive resource profiling and analysis
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
- **Resource Profiling**: Detailed CPU, memory, GPU, I/O statistics during execution
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
- **NEW**: Comprehensive resource profiling with CPU, memory, GPU, and I/O metrics over time

### Quick Examples

```bash
# View recent job history with resource usage
python3 cli.py job-history --limit 20

# Show aggregate statistics
python3 cli.py job-stats

# Get details for a specific job (includes detailed profile)
python3 cli.py job-details <task-id>

# Filter by tool or status
python3 cli.py job-history --tool fenicsx --status failed
```

### Job History Storage

Job history is stored in `/tmp/keystone_jobs/jobs_history.jsonl` as newline-delimited JSON with complete resource metrics and detailed profiling data for each execution.

For comprehensive documentation, see [JOB_MONITORING.md](JOB_MONITORING.md) and [RESOURCE_PROFILING.md](RESOURCE_PROFILING.md).

---

## Provenance Logging and Reproducibility

Keystone Supercomputer automatically generates **provenance.json** files for every simulation run, ensuring complete reproducibility and audit capability. See [PROVENANCE_SCHEMA.md](PROVENANCE_SCHEMA.md) for comprehensive documentation.

### Automatic Provenance Tracking

Every workflow execution captures:
- **User Prompt**: Original request that initiated the workflow
- **Workflow Plan**: Planned execution strategy and configuration
- **Tool Calls**: All simulation tools executed with parameters
- **Software Versions**: Python, Celery, LangChain, and other dependencies
- **Environment State**: Runtime variables, system information, and settings
- **Random Seeds**: RNG states for reproducibility
- **Input/Output Files**: Complete artifact lineage with checksums
- **Execution Timeline**: Chronological log of all workflow events
- **Resource Usage**: CPU, memory, and duration metrics
- **Agent Actions**: Multi-agent workflow decisions and state changes

### Features

- **Zero-Configuration**: Provenance logging is automatically integrated into all workflows
- **Complete Metadata**: Captures everything needed for exact reproduction
- **Audit Trail**: Comprehensive timeline of all workflow events
- **File Integrity**: SHA256 checksums for all input/output files
- **Schema Versioning**: Forward and backward compatible schema
- **Query API**: List, filter, and retrieve provenance records

### Quick Example

```python
from provenance_logger import get_provenance_logger

# Get global logger (or use automatic integration)
logger = get_provenance_logger()

# Retrieve provenance for a workflow
provenance = logger.get_provenance(workflow_id)
print(f"Status: {provenance['status']}")
print(f"Duration: {provenance['duration_seconds']}s")
print(f"Tool calls: {len(provenance['tool_calls'])}")

# List completed workflows
completed = logger.list_workflows(status="completed", limit=10)
for wf in completed:
    print(f"{wf['workflow_id']}: {wf['user_prompt']}")
```

### Provenance File Location

Provenance files are stored in `/tmp/keystone_provenance/`:

```
/tmp/keystone_provenance/
├── provenance_20251020_153045_abc12345.json
├── provenance_20251020_154030_def67890.json
└── provenance_20251020_160000_xyz98765.json
```

### Use Cases

- **Result Verification**: Validate simulation results and parameters
- **Exact Reproduction**: Reproduce workflows with identical conditions
- **Performance Analysis**: Track resource usage and timing trends
- **Error Diagnosis**: Debug failed workflows with complete context
- **Compliance Auditing**: Meet regulatory requirements for documentation

For complete schema documentation, usage examples, and best practices, see [PROVENANCE_SCHEMA.md](PROVENANCE_SCHEMA.md).

---

## Multi-Agent System with LangGraph

Keystone Supercomputer implements a sophisticated multi-agent orchestration system using the **Conductor-Performer pattern** built with LangGraph. See [CONDUCTOR_PERFORMER_ARCHITECTURE.md](CONDUCTOR_PERFORMER_ARCHITECTURE.md) for comprehensive documentation.

### Architecture Overview

The system features:
- **Conductor Agent**: Central orchestrator for task planning, delegation, and error handling
- **Performer Agents**: Specialized agents for FEniCSx, LAMMPS, and OpenFOAM simulations
- **Validator Agent**: Quality control and feedback generation
- **Feedback Loops**: Automatic refinement and error recovery

### Simulation Workflow Agents

In addition to the Conductor-Performer pattern, Keystone includes specialized agents for managing complete simulation workflows. See [SIMULATION_WORKFLOW_AGENTS.md](SIMULATION_WORKFLOW_AGENTS.md) for detailed specifications.

**Six Specialized Agents:**

1. **RequirementAnalysisAgent** - Analyze and validate simulation requirements
2. **PlanningAgent** - Create detailed execution plans and resource allocation
3. **SimulationAgent** - Execute simulations and manage compute resources
4. **VisualizationAgent** - Generate visualizations from results
5. **ValidationAgent** - Validate results against success criteria
6. **SummarizationAgent** - Generate comprehensive reports and summaries

**Key Features:**
- Standardized input/output protocols with `AgentInput` and `AgentOutput`
- Clear separation of concerns with single-responsibility agents
- Comprehensive error handling and validation
- Support for refinement loops and iterative improvement
- Full integration with LangGraph for state management

**Quick Example:**

```python
from simulation_workflow_agents import (
    RequirementAnalysisAgent,
    PlanningAgent,
    SimulationAgent,
    VisualizationAgent,
    ValidationAgent,
    SummarizationAgent,
    AgentInput,
    WorkflowStage
)

# 1. Analyze Requirements
req_agent = RequirementAnalysisAgent()
req_output = req_agent.process(AgentInput(
    stage=WorkflowStage.REQUIREMENT_ANALYSIS,
    data={"user_request": "Run FEA on steel beam under 10kN load"}
))

# 2. Create Plan
plan_agent = PlanningAgent()
plan_output = plan_agent.process(AgentInput(
    stage=WorkflowStage.PLANNING,
    previous_stage_output=req_output.data
))

# 3-6: Execute remaining workflow stages...
# See SIMULATION_WORKFLOW_AGENTS.md for complete examples
```

**Interactive Demo:**

```bash
cd src/agent
python3 example_simulation_workflow_agents.py
```

### Conductor-Performer Quick Start

```python
from conductor_performer_graph import ConductorPerformerGraph

# Initialize the graph
graph = ConductorPerformerGraph()

# Execute a workflow
result = graph.execute_workflow(
    user_request="Run structural analysis on steel beam"
)

print(f"Status: {result['status']}")
print(f"Iterations: {result['iterations']}")
```

### Example Workflows

The system includes pre-configured example workflows for:
- **Structural Analysis**: Single-tool FEniCSx finite element analysis
- **Multi-Physics**: Coupled structural and fluid dynamics simulations
- **Parameter Sweeps**: Molecular dynamics with multiple configurations
- **Error Recovery**: Automatic mesh refinement on convergence issues

### Interactive Demo

```bash
cd src/agent
python3 example_conductor_performer.py
```

### Testing

Comprehensive test suite with 37 tests covering all agent behaviors:

```bash
cd src/agent
python3 test_conductor_performer_graph.py
```

For detailed architecture documentation, agent responsibilities, edge routing logic, and example workflows, see [CONDUCTOR_PERFORMER_ARCHITECTURE.md](CONDUCTOR_PERFORMER_ARCHITECTURE.md).

---

## Workflow Routing and Conditional Edges

Keystone Supercomputer includes comprehensive **routing logic and conditional edges** for intelligent workflow execution in LangGraph. This enables adaptive, fault-tolerant, and context-aware workflow orchestration. See [WORKFLOW_ROUTING_GUIDE.md](WORKFLOW_ROUTING_GUIDE.md) for comprehensive documentation.

### Routing Strategies

**8 Built-in Routing Strategies:**

1. ✅ **Success Path** - Normal workflow progression
2. ✅ **Error Fallback** - Graceful degradation with severity levels
3. ✅ **Retry with Backoff** - Exponential backoff for transient failures
4. ✅ **Conditional Branch** - Output value and context-based routing
5. ✅ **Resource-Aware** - Adaptive paths based on CPU/memory/GPU availability
6. ✅ **Performance-Based** - Learn from historical metrics to optimize routing
7. ✅ **Parallel Execution** - Fan-out/fan-in patterns with join nodes
8. ✅ **Circuit Breaker** - Fault tolerance for external dependencies

### Quick Start

```python
from workflow_routing import WorkflowRouter, WorkflowRoutingState, NodeStatus

# Initialize router
router = WorkflowRouter(max_retries=3)

# Make routing decision
state: WorkflowRoutingState = {
    "node_status": {"simulation": NodeStatus.COMPLETED},
    "node_results": {"simulation": {"output": "success"}},
    "retry_count": 0
}

decision = router.route_after_execution(
    state=state,
    current_node="simulation",
    success_node="validation",
    error_node="error_handler"
)

print(f"Route to: {decision.next_node}")  # "validation"
```

### Key Features

**Decision-Making Based On:**
- Agent outputs and execution results
- Error states with severity classification (LOW, MEDIUM, HIGH, CRITICAL)
- Workflow context (priority, user preferences, environment)
- Resource availability (CPU, memory, GPU)
- Historical performance metrics
- Circuit breaker state for fault tolerance

**Advanced Patterns:**
- Multi-way branching with complex conditions
- Validation with refinement loops
- Dynamic workflow composition
- Priority-based execution (critical, high, normal, low)
- Adaptive solver selection

### Example: Priority-Based Routing

```python
# High-priority requests get GPU acceleration
state: WorkflowRoutingState = {
    "workflow_context": {"priority": "high"}
}

routing_rules = [
    {
        "condition": lambda p: p == "high",
        "node": "gpu_accelerated_path",
        "reason": "High priority - GPU acceleration"
    },
    {
        "condition": lambda p: p == "normal",
        "node": "standard_cpu_path",
        "reason": "Standard processing"
    }
]

decision = router.route_by_context(
    state=state,
    context_key="priority",
    routing_rules=routing_rules,
    default_node="standard_path"
)
```

### Interactive Examples

```bash
cd src/agent

# Run 10 routing strategy examples
python3 example_routing_strategies.py

# Enhanced conductor-performer with routing
python3 example_enhanced_routing.py

# Run routing tests (35 tests)
python3 test_workflow_routing.py
```

### Documentation

- **[WORKFLOW_ROUTING_GUIDE.md](WORKFLOW_ROUTING_GUIDE.md)** - Comprehensive guide with patterns and examples
- **[WORKFLOW_ROUTING_QUICK_REFERENCE.md](WORKFLOW_ROUTING_QUICK_REFERENCE.md)** - Quick reference cheat sheet
- **[src/agent/workflow_routing.py](src/agent/workflow_routing.py)** - Core implementation
- **[src/agent/example_routing_strategies.py](src/agent/example_routing_strategies.py)** - 10 interactive examples
- **[src/agent/test_workflow_routing.py](src/agent/test_workflow_routing.py)** - Comprehensive test suite

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

---

## Benchmark Registry - Reference Cases for Validation

Keystone Supercomputer includes a comprehensive benchmark registry with curated reference test cases for all supported simulators. The registry provides standardized benchmarks with expected results, validation criteria, and complete metadata for reproducibility. See [BENCHMARK_REGISTRY.md](BENCHMARK_REGISTRY.md) for complete documentation.

### Purpose

The benchmark registry serves multiple purposes:
- **Quality Assurance**: Validate that simulation tools are installed and working correctly
- **Reproducibility**: Provide standardized test cases with documented expected results
- **Education**: Offer learning resources for new users with increasing difficulty levels
- **Regression Testing**: Detect when code changes break existing functionality
- **Performance Comparison**: Compare results across different hardware configurations

### Available Benchmarks

#### FEniCSx (Finite Element Method)
- **poisson-2d-basic**: 2D Poisson equation with Dirichlet boundary conditions (beginner)

#### LAMMPS (Molecular Dynamics)
- **lennard-jones-fluid**: Classical MD simulation of Lennard-Jones fluid (beginner)

#### OpenFOAM (Computational Fluid Dynamics)
- **cavity-flow**: Lid-driven cavity flow using icoFoam solver (beginner)

### Quick Start

```bash
cd src/sim-toolbox/benchmarks

# List all benchmarks
python3 benchmark_registry.py list

# Filter by simulator
python3 benchmark_registry.py list --simulator fenicsx

# View benchmark details
python3 benchmark_registry.py info --benchmark-id fenicsx-poisson-2d-basic

# Validate all benchmarks
python3 benchmark_registry.py validate-all

# Get statistics
python3 benchmark_registry.py stats

# Generate report
python3 benchmark_registry.py report --output BENCHMARK_REPORT.md
```

### Python API

```python
from benchmark_registry import BenchmarkRegistry

# Initialize registry
registry = BenchmarkRegistry()

# List benchmarks
benchmarks = registry.list_benchmarks(simulator="fenicsx", difficulty="beginner")
for bench in benchmarks:
    print(f"{bench['id']}: {bench['name']}")

# Load benchmark details
benchmark = registry.load_benchmark("fenicsx-poisson-2d-basic")
print(f"Description: {benchmark['description']}")
print(f"Expected results: {benchmark['expected_results']}")

# Validate benchmark
result = registry.validate_benchmark("fenicsx-poisson-2d-basic")
if result['valid']:
    print("✓ Benchmark is valid")
```

### Benchmark Structure

Each benchmark includes:
- **Identification**: Unique ID, name, simulator, version
- **Description**: Detailed problem statement with equations and boundary conditions
- **Classification**: Category, difficulty level, tags
- **Input Files**: All required files with SHA256 checksums
- **Expected Results**: Output files, numerical metrics with tolerances, performance data
- **Validation Criteria**: Methods and checks for validating results
- **Metadata**: Author, date, license, references
- **Execution**: Command, parameters, timeout, parallelization settings

### Contributing Benchmarks

We welcome contributions of new benchmark cases! See [src/sim-toolbox/benchmarks/CONTRIBUTING_BENCHMARKS.md](src/sim-toolbox/benchmarks/CONTRIBUTING_BENCHMARKS.md) for detailed guidelines.

**Submission process:**
1. Create benchmark definition following the JSON schema
2. Include all input files with checksums
3. Document expected results with appropriate tolerances
4. Test execution and validation
5. Submit pull request with complete documentation

For comprehensive documentation, see [BENCHMARK_REGISTRY.md](BENCHMARK_REGISTRY.md).

