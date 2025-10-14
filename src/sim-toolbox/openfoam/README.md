# OpenFOAM Simulation Toolbox

This directory contains a containerized OpenFOAM environment for computational fluid dynamics (CFD) simulations with standardized `/data` mount points for reproducible input/output transfer.

## Overview

OpenFOAM (Open Field Operation and Manipulation) is a free, open-source CFD software package that can simulate complex fluid flows involving turbulence, heat transfer, chemical reactions, and more.

This toolbox provides:
- **Containerized Environment**: OpenFOAM 11 with ParaView 5.10 for visualization
- **Standardized Data Mounts**: `/data/input` and `/data/output` for reproducible workflows
- **Example Scripts**: Python-based automation for running simulations
- **Integration Ready**: Designed to work with the Keystone Supercomputer agent framework

## Quick Start

### 1. Build the Docker Image

```bash
cd src/sim-toolbox/openfoam
docker build -t keystone-openfoam:latest .
```

### 2. Run the Example Cavity Simulation

```bash
docker run --rm \
  -v $(pwd)/output:/data/output \
  keystone-openfoam:latest \
  python3 /workspace/example_cavity.py
```

### 3. View Results

Results will be saved to `./output/cavity/` directory.

## Usage

### Interactive Shell

To explore OpenFOAM interactively:

```bash
docker run -it --rm \
  -v $(pwd)/input:/data/input \
  -v $(pwd)/output:/data/output \
  keystone-openfoam:latest \
  bash
```

Inside the container, OpenFOAM is already sourced and ready to use:

```bash
# Check OpenFOAM version
icoFoam -help

# List available tutorials
ls /opt/openfoam11/tutorials/

# Run mesh generator
blockMesh

# Run solvers
icoFoam
simpleFoam
# etc.
```

### Running Custom Simulations

Mount your case directory to `/data/input` and run your simulation:

```bash
docker run --rm \
  -v /path/to/your/case:/data/input \
  -v $(pwd)/results:/data/output \
  keystone-openfoam:latest \
  bash -c "cd /data/input && blockMesh && icoFoam && cp -r [0-9]* /data/output/"
```

### Using the Python Example Script

The included `example_cavity.py` demonstrates how to:
- Set up an OpenFOAM case programmatically
- Run mesh generation and solvers
- Collect and organize results

Run with custom output location:

```bash
docker run --rm \
  -v $(pwd)/my-results:/data/output \
  keystone-openfoam:latest \
  python3 /workspace/example_cavity.py --output-dir /data/output/my-cavity
```

## Container Details

### Base Image
- `openfoam/openfoam11-paraview510:latest`
- Includes OpenFOAM 11 and ParaView 5.10

### Standard Mount Points
- `/data/input` - Mount your input cases and meshes here
- `/data/output` - Simulation results are written here
- `/workspace` - Working directory for running simulations

### Environment Variables
- `FOAM_RUN=/workspace/foam-run` - Default run directory
- `DATA_INPUT=/data/input` - Input data location
- `DATA_OUTPUT=/data/output` - Output data location

## Example: Cavity Flow Simulation

The cavity flow case is a classic CFD benchmark simulating flow in a 2D square cavity with a moving lid. It demonstrates:
- Mesh generation with `blockMesh`
- Incompressible laminar flow solving with `icoFoam`
- Time-series output of velocity and pressure fields

### Cavity Case Structure

```
cavity/
├── 0/           # Initial conditions
│   ├── U        # Velocity field
│   └── p        # Pressure field
├── constant/    # Physical properties
│   └── transportProperties
└── system/      # Simulation controls
    ├── controlDict
    ├── fvSchemes
    └── fvSolution
```

## Integration with Keystone Supercomputer

This OpenFOAM toolbox is designed to integrate with the Keystone Supercomputer agent framework:

1. **Agents can invoke simulations** via Docker container execution
2. **Standardized I/O** through `/data` mounts enables automated workflows
3. **Python scripts** provide programmatic interfaces for agent control
4. **Results collection** is automated to `/data/output` for downstream analysis

## Extending This Toolbox

To add more OpenFOAM examples or solvers:

1. Create new Python scripts following the pattern in `example_cavity.py`
2. Add documentation for specific use cases
3. Consider creating solver-specific Docker images for optimization
4. Integrate with agent tool adapters in `src/agent/`

## Available OpenFOAM Solvers

OpenFOAM includes numerous solvers for different physics:

- **Incompressible Flow**: `icoFoam`, `simpleFoam`, `pimpleFoam`
- **Compressible Flow**: `rhoCentralFoam`, `sonicFoam`
- **Multiphase**: `interFoam`, `multiphaseEulerFoam`
- **Heat Transfer**: `buoyantSimpleFoam`, `chtMultiRegionFoam`
- **Combustion**: `reactingFoam`, `fireFoam`

See OpenFOAM documentation for complete solver list and usage.

## Resources

- [OpenFOAM Documentation](https://www.openfoam.com/documentation)
- [OpenFOAM Tutorials](https://www.openfoam.com/documentation/tutorial-guide)
- [OpenFOAM User Guide](https://www.openfoam.com/documentation/user-guide)
- [CFD Online Forums](https://www.cfd-online.com/Forums/openfoam/)

## Troubleshooting

### Docker Build Issues

If the build fails to find the OpenFOAM image:
```bash
docker pull openfoam/openfoam11-paraview510:latest
```

### Permission Issues

If you encounter permission errors with mounted volumes:
```bash
docker run --rm -v $(pwd)/output:/data/output --user $(id -u):$(id -g) keystone-openfoam:latest ...
```

### Memory Issues

OpenFOAM simulations can be memory-intensive. Increase Docker memory limits if needed:
```bash
docker run --rm -m 4g keystone-openfoam:latest ...
```

## Next Steps

- Explore more OpenFOAM tutorials in `/opt/openfoam11/tutorials/`
- Create custom case files for your specific CFD problems
- Integrate with Python automation scripts
- Connect to Keystone Supercomputer agent workflows
- Set up ParaView for visualization of results

---

*Part of the Keystone Supercomputer project - Phase 3: Simulation Toolbox*
