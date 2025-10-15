# Simulation Container Orchestration

## Overview

All simulation adapters (OpenFOAM, LAMMPS, FEniCSx) now implement a standardized orchestration interface that enables robust workflow management, health monitoring, and integration with orchestration systems like Celery, Kubernetes, and Docker Compose.

## Key Features

### 1. Health Checks

All adapters support comprehensive health checks that validate:

- **Docker Image Availability**: Verifies the required Docker image exists locally
- **Docker Daemon Accessibility**: Checks that Docker is running and accessible
- **Output Directory Writability**: Ensures the output directory is writable

#### Example Usage

```python
from openfoam_adapter import OpenFOAMAdapter

adapter = OpenFOAMAdapter(output_dir="./output")
health = adapter.health_check()

print(f"Status: {health['status']}")  # 'healthy', 'degraded', or 'unhealthy'
print(f"Timestamp: {health['timestamp']}")
print(f"Checks: {health['checks']}")
print(f"Message: {health['message']}")
```

#### Health Check Response

```json
{
  "status": "healthy",
  "timestamp": "2025-10-15T18:04:22.750306Z",
  "checks": {
    "image_available": true,
    "docker_accessible": true,
    "output_dir_writable": true
  },
  "message": "All checks passed",
  "tool": "OpenFOAMAdapter",
  "image": "openfoam-toolbox"
}
```

### 2. Status Reporting

Adapters provide real-time status information about their current state:

- **State**: Current simulation state (idle, running, completed, failed, cancelled)
- **Last Result**: Results from the last simulation run
- **Last Health Check**: Most recent health check results
- **Metadata**: Additional adapter-specific metadata

#### Example Usage

```python
status = adapter.get_status()

print(f"State: {status['state']}")  # 'idle', 'running', 'completed', 'failed', 'cancelled'
print(f"Last Result: {status['last_result']}")
print(f"Timestamp: {status['timestamp']}")
```

#### Status Response

```json
{
  "state": "idle",
  "last_result": null,
  "last_health_check": {
    "status": "healthy",
    "timestamp": "2025-10-15T18:04:22.750306Z"
  },
  "metadata": {},
  "timestamp": "2025-10-15T18:04:22.750417Z"
}
```

### 3. Metadata API

Adapters expose detailed metadata about their capabilities:

- **Tool Name**: Name of the simulation tool
- **Image Name**: Docker image being used
- **Output Directory**: Location of simulation outputs
- **Capabilities**: List of supported features
- **Version**: Tool version (if available)

#### Example Usage

```python
metadata = adapter.get_metadata()

print(f"Tool: {metadata['tool_name']}")
print(f"Image: {metadata['image_name']}")
print(f"Capabilities: {metadata['capabilities']}")
print(f"Version: {metadata['version']}")
```

#### Metadata Response

```json
{
  "tool_name": "OpenFOAM",
  "image_name": "openfoam-toolbox",
  "output_dir": "/path/to/output",
  "capabilities": [
    "cfd_simulation",
    "mesh_generation",
    "incompressible_flow",
    "compressible_flow",
    "multiphase_flow",
    "turbulence_modeling",
    "heat_transfer",
    "custom_solvers",
    "post_processing"
  ],
  "version": "11",
  "timestamp": "2025-10-15T18:04:22.911787Z"
}
```

## Orchestration Base Class

All adapters inherit from `OrchestrationBase`, which defines the standardized interface:

```python
from orchestration_base import OrchestrationBase, SimulationStatus, HealthStatus

class MyAdapter(OrchestrationBase):
    def __init__(self, image_name: str, output_dir: str):
        super().__init__(image_name, output_dir)
    
    def run_simulation(self, **kwargs):
        self._update_status(SimulationStatus.RUNNING)
        # ... simulation logic ...
        self._update_status(SimulationStatus.COMPLETED)
    
    def check_image_available(self) -> bool:
        # Check if Docker image exists
        pass
    
    def _get_capabilities(self) -> list:
        # Return list of capabilities
        return ["capability1", "capability2"]
    
    def _get_version(self) -> str:
        # Return version info
        return "1.0.0"
```

## Integration Examples

### With Celery

```python
from celery import Celery
from openfoam_adapter import OpenFOAMAdapter

app = Celery('tasks', broker='redis://localhost:6379/0')

@app.task(name='run_openfoam_simulation')
def run_openfoam_simulation(case_script: str, case_name: str):
    adapter = OpenFOAMAdapter(output_dir=f"./output/{case_name}")
    
    # Health check before running
    health = adapter.health_check()
    if health['status'] != 'healthy':
        return {'error': 'Adapter not healthy', 'health': health}
    
    # Run simulation
    result = adapter.run_simulation(
        case_script=case_script,
        case_name=case_name
    )
    
    # Get final status
    status = adapter.get_status()
    
    return {
        'simulation_result': result,
        'final_status': status
    }
```

### With Kubernetes

Create a health check endpoint in your container:

```python
from flask import Flask, jsonify
from openfoam_adapter import OpenFOAMAdapter

app = Flask(__name__)
adapter = OpenFOAMAdapter(output_dir="/data/output")

@app.route('/health')
def health():
    health_check = adapter.health_check()
    status_code = 200 if health_check['status'] == 'healthy' else 503
    return jsonify(health_check), status_code

@app.route('/status')
def status():
    return jsonify(adapter.get_status())

@app.route('/metadata')
def metadata():
    return jsonify(adapter.get_metadata())

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
```

Then configure Kubernetes probes:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: openfoam-simulation
spec:
  containers:
  - name: openfoam
    image: openfoam-toolbox
    livenessProbe:
      httpGet:
        path: /health
        port: 8080
      initialDelaySeconds: 10
      periodSeconds: 30
    readinessProbe:
      httpGet:
        path: /health
        port: 8080
      initialDelaySeconds: 5
      periodSeconds: 10
```

### With Docker Compose

```yaml
version: '3.8'
services:
  openfoam:
    image: openfoam-toolbox
    healthcheck:
      test: ["CMD", "python3", "-c", "from openfoam_adapter import OpenFOAMAdapter; import sys; sys.exit(0 if OpenFOAMAdapter().health_check()['status'] == 'healthy' else 1)"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

## Testing

### Unit Tests

Run the orchestration test suite:

```bash
cd src/sim-toolbox
python3 test_orchestration.py
```

This validates:
- Health check functionality
- Status reporting
- Metadata APIs
- JSON serialization

### Integration Tests

Run the full integration test with orchestration validation:

```bash
cd src/sim-toolbox
python3 integration_test.py
```

This validates orchestration features as part of end-to-end simulation workflows.

## Adapter-Specific Capabilities

### OpenFOAM Adapter

Capabilities:
- `cfd_simulation` - Computational Fluid Dynamics
- `mesh_generation` - Mesh generation with blockMesh, snappyHexMesh
- `incompressible_flow` - Incompressible flow solvers
- `compressible_flow` - Compressible flow solvers
- `multiphase_flow` - Multiphase flow simulations
- `turbulence_modeling` - RANS and LES turbulence models
- `heat_transfer` - Heat transfer and conjugate heat transfer
- `custom_solvers` - Support for custom solvers
- `post_processing` - Post-processing utilities

### LAMMPS Adapter

Capabilities:
- `molecular_dynamics` - Molecular dynamics simulations
- `atomic_simulation` - Atomic-scale simulations
- `lennard_jones` - Lennard-Jones potentials
- `coulombic_interactions` - Coulombic interactions
- `bond_angle_dihedral` - Bond, angle, and dihedral potentials
- `nve_nvt_npt_ensembles` - Various statistical ensembles
- `parallel_computing` - Parallel execution support
- `trajectory_output` - Trajectory file output
- `thermodynamic_output` - Thermodynamic data logging

### FEniCSx Adapter

Capabilities:
- `finite_element_method` - Finite element method
- `pde_solver` - Partial differential equation solver
- `poisson_equation` - Poisson equation
- `heat_equation` - Heat/diffusion equations
- `elasticity` - Linear and nonlinear elasticity
- `navier_stokes` - Navier-Stokes equations
- `mixed_elements` - Mixed finite element spaces
- `adaptive_mesh_refinement` - Adaptive mesh refinement
- `parallel_computing` - Parallel execution support

## Status States

Adapters track simulation state through the `SimulationStatus` enum:

- **IDLE**: No simulation running, ready to accept new jobs
- **RUNNING**: Simulation currently executing
- **COMPLETED**: Simulation completed successfully
- **FAILED**: Simulation failed with error
- **CANCELLED**: Simulation was cancelled by user

## Health States

Health checks return one of the following states via `HealthStatus` enum:

- **HEALTHY**: All checks passed, adapter ready to run simulations
- **DEGRADED**: Some non-critical checks failed, may affect performance
- **UNHEALTHY**: Critical checks failed, adapter cannot run simulations
- **UNKNOWN**: Health check could not be completed

## Best Practices

1. **Always check health before running simulations** in production environments
2. **Monitor status during long-running simulations** to detect failures early
3. **Use metadata API to validate capabilities** before submitting specialized jobs
4. **Implement retry logic** based on health and status checks
5. **Log health check results** for troubleshooting and monitoring
6. **Set up automated health checks** in orchestration platforms
7. **Use status information** to provide feedback to users

## Troubleshooting

### Health Check Fails

If health checks consistently fail:

1. Verify Docker is installed and running:
   ```bash
   docker info
   ```

2. Check if the required image exists:
   ```bash
   docker images | grep <image-name>
   ```

3. Verify output directory permissions:
   ```bash
   ls -la <output-dir>
   ```

4. Review health check details:
   ```python
   health = adapter.health_check()
   print(health['message'])
   print(health['checks'])
   ```

### Status Not Updating

If simulation status doesn't update:

1. Ensure you're using the same adapter instance
2. Check that simulations complete (don't hang)
3. Verify no exceptions are raised during simulation
4. Add logging to track status changes:
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

## Future Enhancements

Planned improvements to the orchestration interface:

- [ ] Asynchronous health checks for faster responses
- [ ] Detailed progress reporting during simulations
- [ ] Resource usage metrics (CPU, memory, disk)
- [ ] Simulation queue management
- [ ] Cancellation support for running simulations
- [ ] Remote health check endpoints
- [ ] Prometheus metrics export
- [ ] OpenTelemetry tracing support

## See Also

- [Integration Test Documentation](INTEGRATION_TEST.md)
- [Adapter Documentation](ADAPTERS.md)
- [Docker Compose Reference](../../DOCKER_COMPOSE.md)
- [Kubernetes Deployment Guide](../../k8s/README.md)
