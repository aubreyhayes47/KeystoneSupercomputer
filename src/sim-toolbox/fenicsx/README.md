# FEniCSx Simulation Toolbox

FEniCSx is a popular open-source computing platform for solving partial differential equations (PDEs) using finite element methods. This containerized toolbox provides a reproducible environment for running FEniCSx simulations with standardized input/output via the `/data` volume mount.

## Features

- **Official FEniCSx Image**: Based on the stable `dolfinx/dolfinx:stable` Docker image
- **Standardized Data Mount**: Uses `/data` directory for inputs and outputs
- **Minimal Example**: Includes a Poisson equation solver demonstrating basic FEniCSx capabilities
- **Reproducible Builds**: Dockerfile ensures consistent environment across platforms

## Quick Start

### Build the Docker Image

```bash
cd src/sim-toolbox/fenicsx
docker build -t fenicsx-toolbox .
```

### Run the Example Simulation

Run the default Poisson example with output to a local `./output` directory:

```bash
docker run --rm -v $(pwd)/output:/data fenicsx-toolbox
```

This will:
1. Solve the 2D Poisson equation on a unit square domain
2. Save results to `./output/poisson_solution.xdmf`
3. Print solution statistics to console

### Run Custom Scripts

To run your own Python script:

```bash
docker run --rm -v $(pwd)/my_script.py:/app/my_script.py -v $(pwd)/output:/data fenicsx-toolbox my_script.py
```

### Interactive Shell

For interactive development and debugging:

```bash
docker run --rm -it -v $(pwd)/output:/data fenicsx-toolbox bash
```

## Example: Poisson Equation

The included `poisson.py` demonstrates:
- Mesh creation (unit square, 32×32 triangular elements)
- Function space definition (piecewise linear Lagrange elements)
- Boundary condition application (Dirichlet u=0 on boundary)
- Variational formulation with UFL (Unified Form Language)
- Linear system solving with PETSc
- Solution export to XDMF format for visualization

### Mathematical Problem

Solves:
```
-∇²u = f  in Ω = [0,1] × [0,1]
u = 0     on ∂Ω
```

where the source term is a Gaussian:
```
f = 10 * exp(-((x-0.5)² + (y-0.5)²) / 0.02)
```

### Visualizing Results

The output XDMF file can be visualized with [ParaView](https://www.paraview.org/):

```bash
paraview output/poisson_solution.xdmf
```

## Container Architecture

### Directory Structure

```
/app/          # Working directory containing Python scripts
/data/         # Standardized mount point for inputs and outputs
```

### Entrypoint

- Default entrypoint: `python3`
- Default command: `poisson.py`
- Override with custom scripts as needed

### Environment Variables

- `PYTHONUNBUFFERED=1`: Ensures real-time output logging

## Integration with Keystone Supercomputer

This toolbox follows the Keystone Supercomputer standardized container pattern:

1. **Uniform Interface**: All simulation containers use `/data` for I/O
2. **Agent Compatibility**: Can be orchestrated via the agentic workflow system
3. **Reproducibility**: Containerized environment ensures consistent results
4. **Scalability**: Ready for orchestration with Docker Compose or Kubernetes

## Python Adapter

The FEniCSx toolbox includes a Python adapter (`fenicsx_adapter.py`) that provides a standardized interface for programmatic simulation execution. This enables:

- Automated container orchestration
- Result parsing and metadata extraction
- Integration with agentic workflows
- LLM-based tool calling via MCP

### Using the Adapter

```python
from fenicsx_adapter import FEniCSxAdapter

# Create adapter instance
adapter = FEniCSxAdapter(
    image_name="fenicsx-toolbox",
    output_dir="./output"
)

# Run simulation
result = adapter.run_simulation()

# Access results
print(f"Success: {result['success']}")
print(f"Solution range: [{result['metadata']['min_value']}, {result['metadata']['max_value']}]")

# Save metadata
adapter.save_result_json()
```

### CLI Usage

```bash
# Check if Docker image is available
python3 fenicsx_adapter.py --check

# Build Docker image
python3 fenicsx_adapter.py --build

# Run simulation
python3 fenicsx_adapter.py --output-dir ./my_output

# Run with custom script
python3 fenicsx_adapter.py --output-dir ./my_output --script my_simulation.py
```

See [`fenicsx_adapter.py`](./fenicsx_adapter.py) and [`example_adapter_usage.py`](./example_adapter_usage.py) for more details.

For comprehensive adapter documentation, see [ADAPTERS.md](../ADAPTERS.md).

## Next Steps

- Add more example problems (elasticity, fluid dynamics, heat transfer)
- ~~Implement Python adapter for agent integration~~ ✓ Completed
- Configure MPI for parallel simulations
- Add provenance logging for reproducibility tracking

## References

- [FEniCSx Documentation](https://docs.fenicsproject.org/)
- [DOLFINx (FEniCSx Core)](https://github.com/FEniCS/dolfinx)
- [FEniCS Tutorial](https://fenicsproject.org/tutorial/)

---

Part of the **Keystone Supercomputer** project - Phase 3: Simulation Toolbox
