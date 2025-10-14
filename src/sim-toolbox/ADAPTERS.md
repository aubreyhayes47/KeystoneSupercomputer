# Simulation Tool Adapters

This directory contains Python adapter scripts for containerized simulation tools in the Keystone Supercomputer project. These adapters provide a standardized interface for running simulations, parsing results, and enabling agentic orchestration.

## Overview

Each simulation toolbox (FEniCSx, LAMMPS, OpenFOAM) has a corresponding Python adapter that:

- **Accepts input parameters** - Flexible configuration through Python APIs
- **Automates container execution** - Handles Docker command construction and execution
- **Parses output** - Extracts results, metadata, and performance metrics
- **Reports results** - Provides structured JSON output for downstream tools
- **Enables LLM integration** - Ready for MCP-based tool calling and agentic workflows

## Available Adapters

### FEniCSx Adapter

**Location:** `src/sim-toolbox/fenicsx/fenicsx_adapter.py`

**Purpose:** Run finite element method (FEM) simulations for partial differential equations (PDEs).

**Key Features:**
- Run default Poisson solver or custom Python scripts
- Parse solution statistics (min, max, mean values)
- Extract mesh and DOF information
- Export results in XDMF format for ParaView visualization

**Quick Start:**
```python
from fenicsx_adapter import FEniCSxAdapter

adapter = FEniCSxAdapter(
    image_name="fenicsx-toolbox",
    output_dir="./output"
)

result = adapter.run_simulation()
adapter.save_result_json()
```

**CLI Usage:**
```bash
cd src/sim-toolbox/fenicsx
python3 fenicsx_adapter.py --output-dir ./my_output --check
python3 fenicsx_adapter.py --output-dir ./my_output --build
python3 fenicsx_adapter.py --output-dir ./my_output
```

### LAMMPS Adapter

**Location:** `src/sim-toolbox/lammps/lammps_adapter.py`

**Purpose:** Run molecular dynamics (MD) simulations for atomic and molecular systems.

**Key Features:**
- Run LAMMPS input scripts with flexible parameters
- Parse thermodynamic output (temperature, energy, pressure)
- Extract trajectory data and final configurations
- Support custom LAMMPS command-line arguments

**Quick Start:**
```python
from lammps_adapter import LAMMPSAdapter

adapter = LAMMPSAdapter(
    image_name="keystone/lammps:latest",
    output_dir="./output"
)

result = adapter.run_simulation(
    input_script="example.lammps",
    log_file="lammps.log"
)
adapter.save_result_json()
```

**CLI Usage:**
```bash
cd src/sim-toolbox/lammps
python3 lammps_adapter.py --output-dir ./my_output --check
python3 lammps_adapter.py --output-dir ./my_output --input-script example.lammps
```

### OpenFOAM Adapter

**Location:** `src/sim-toolbox/openfoam/openfoam_adapter.py`

**Purpose:** Run computational fluid dynamics (CFD) simulations.

**Key Features:**
- Run Python case setup scripts or existing OpenFOAM cases
- Parse solver convergence data and residuals
- Extract mesh statistics and field information
- Support multiple solvers (icoFoam, simpleFoam, etc.)

**Quick Start:**
```python
from openfoam_adapter import OpenFOAMAdapter

adapter = OpenFOAMAdapter(
    image_name="openfoam-toolbox",
    output_dir="./output"
)

# Using case script
result = adapter.run_simulation(case_name="cavity")

# Or using existing case directory
result = adapter.run_case_direct(
    case_dir="/path/to/case",
    solver="icoFoam"
)

adapter.save_result_json()
```

**CLI Usage:**
```bash
cd src/sim-toolbox/openfoam
python3 openfoam_adapter.py --output-dir ./my_output --check
python3 openfoam_adapter.py --output-dir ./my_output --case-name cavity
python3 openfoam_adapter.py --output-dir ./my_output --case-dir /path/to/case --solver icoFoam
```

## Common API Patterns

All adapters follow consistent design patterns:

### Initialization

```python
adapter = AdapterClass(
    image_name="docker-image-name",
    output_dir="./output",
    # Optional parameters
    input_dir="./input",
    work_dir="./work"
)
```

### Running Simulations

```python
result = adapter.run_simulation(
    # Adapter-specific parameters
)
```

### Result Structure

All adapters return a dictionary with:

```python
{
    "success": bool,              # Whether simulation succeeded
    "returncode": int,            # Process return code
    "stdout": str,                # Standard output
    "stderr": str,                # Standard error
    "output_files": List[str],    # List of generated files
    "metadata": Dict[str, Any],   # Simulation metadata
    "output_dir": str             # Path to output directory
    # Additional adapter-specific fields
}
```

### Utility Methods

All adapters provide:

```python
# Check if Docker image exists
adapter.check_image_available() -> bool

# Build Docker image
adapter.build_image(dockerfile_dir=".") -> bool

# Get last result
adapter.get_last_result() -> Dict[str, Any]

# Save result to JSON
adapter.save_result_json(filepath="simulation_result.json")
```

## Example Usage Scripts

Each adapter includes an example usage script demonstrating common patterns:

- `src/sim-toolbox/fenicsx/example_adapter_usage.py`
- `src/sim-toolbox/lammps/example_adapter_usage.py`
- `src/sim-toolbox/openfoam/example_adapter_usage.py`

Run examples:
```bash
cd src/sim-toolbox/fenicsx
python3 example_adapter_usage.py

cd src/sim-toolbox/lammps
python3 example_adapter_usage.py

cd src/sim-toolbox/openfoam
python3 example_adapter_usage.py
```

## Integration with Agentic Core

These adapters are designed to integrate with the Keystone Supercomputer agentic workflow system:

### LLM Tool Calling

Adapters can be exposed as tools to language models via MCP (Model Context Protocol):

```python
# Example MCP tool definition
tool_definition = {
    "name": "run_fenicsx_simulation",
    "description": "Run a FEniCSx finite element simulation",
    "parameters": {
        "script_content": "Python script for FEniCSx simulation",
        "mesh_size": "Number of mesh elements per dimension"
    }
}

def run_fenicsx_simulation(script_content: str, mesh_size: int = 32):
    adapter = FEniCSxAdapter(output_dir=f"./output/sim_{timestamp}")
    result = adapter.run_simulation(script_content=script_content)
    return result
```

### Workflow Orchestration

Multiple simulations can be chained:

```python
# Example workflow
def coupled_simulation_workflow():
    # Step 1: Run FEniCSx structural analysis
    fem_adapter = FEniCSxAdapter(output_dir="./fem_results")
    fem_result = fem_adapter.run_simulation()
    
    # Step 2: Extract boundary conditions
    boundary_data = extract_boundary_conditions(fem_result)
    
    # Step 3: Run OpenFOAM fluid analysis
    cfd_adapter = OpenFOAMAdapter(output_dir="./cfd_results")
    cfd_result = cfd_adapter.run_simulation(
        boundary_conditions=boundary_data
    )
    
    # Step 4: Analyze coupled results
    return analyze_fsi_coupling(fem_result, cfd_result)
```

## Docker Image Requirements

Each adapter requires its corresponding Docker image to be built:

```bash
# Build FEniCSx image
cd src/sim-toolbox/fenicsx
docker build -t fenicsx-toolbox .

# Build LAMMPS image
cd src/sim-toolbox/lammps
docker build -t keystone/lammps:latest .

# Build OpenFOAM image
cd src/sim-toolbox/openfoam
docker build -t openfoam-toolbox .
```

Or use the adapter's `build_image()` method:

```python
adapter = FEniCSxAdapter()
if not adapter.check_image_available():
    adapter.build_image(dockerfile_dir=".")
```

## Output Structure

All adapters follow a consistent output structure:

```
output/
├── simulation_result.json    # Metadata and summary
├── [tool-specific files]     # Simulation outputs
│   ├── solution.xdmf        # (FEniCSx)
│   ├── trajectory.lammpstrj # (LAMMPS)
│   ├── log.* files          # (OpenFOAM)
│   └── ...
```

## Error Handling

Adapters provide detailed error information:

```python
result = adapter.run_simulation(...)

if not result['success']:
    print(f"Simulation failed with code {result['returncode']}")
    print(f"Error output:\n{result['stderr']}")
    
    # Check for common issues
    if 'No such file' in result['stderr']:
        print("Input file not found")
    elif 'out of memory' in result['stderr'].lower():
        print("Insufficient memory for simulation")
```

## Performance Considerations

- **Container Overhead**: First run may be slower due to Docker image pull/setup
- **Volume Mounts**: Use local paths for best I/O performance
- **Resource Limits**: Add Docker resource constraints via `docker_args`

```python
result = adapter.run_simulation(
    docker_args=["--memory", "4g", "--cpus", "2"]
)
```

## Testing

Basic testing can be done with the `--check` and `--build` flags:

```bash
# Check if image is available
python3 fenicsx_adapter.py --check

# Build image and run test
python3 fenicsx_adapter.py --build --output-dir ./test_output
```

## Future Enhancements

Planned improvements for the adapters:

1. **Async Execution**: Support for non-blocking simulation runs
2. **Progress Monitoring**: Real-time progress tracking and callbacks
3. **Checkpoint/Resume**: Ability to checkpoint and resume long simulations
4. **Parameter Sweeps**: Built-in support for parameter studies
5. **Resource Optimization**: Automatic tuning of container resources
6. **Result Validation**: Automated sanity checks on outputs
7. **Provenance Logging**: Detailed tracking of inputs, parameters, and outputs

## Contributing

When extending or modifying adapters:

1. Maintain consistent API patterns across all adapters
2. Preserve backward compatibility when possible
3. Add comprehensive docstrings and type hints
4. Update example scripts to demonstrate new features
5. Test with actual Docker containers before committing

## Testing

### Integration Test

A comprehensive integration test validates the end-to-end functionality of all simulation toolboxes. The test runs simulations in FEniCSx, LAMMPS, and OpenFOAM to ensure:

- Adapters can successfully automate workflows
- Simulations complete without errors
- Output results are collected and validated
- End-to-end orchestration works properly

Run the integration test:

```bash
cd src/sim-toolbox
python3 integration_test.py --build
```

See [INTEGRATION_TEST.md](./INTEGRATION_TEST.md) for detailed documentation.

### Basic Validation

For quick API validation without running actual simulations:

```bash
python3 validate_adapters.py
```

## Related Documentation

- [Integration Test Documentation](./INTEGRATION_TEST.md)
- [FEniCSx README](./fenicsx/README.md)
- [LAMMPS README](./lammps/README.md)
- [OpenFOAM README](./openfoam/README.md)
- [Keystone Supercomputer Project README](../../README.md)

---

**Part of Phase 3: Simulation Toolbox** - Keystone Supercomputer Project
