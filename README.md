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
- **Local Kubernetes:** Setup with `k3d`, `kubectl`, and `helm` (pending).

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

# Start Redis service
docker compose up -d redis

# Stop all services
docker compose down
```

### Available Services

- **Redis** - Message broker for job queuing
- **Celery Worker** - Background job processing
- **FEniCSx** - Finite Element Method simulations
- **LAMMPS** - Molecular Dynamics simulations
- **OpenFOAM** - Computational Fluid Dynamics simulations

