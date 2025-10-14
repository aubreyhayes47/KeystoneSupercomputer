# LAMMPS Simulation Toolbox

This directory contains the Docker environment and example scripts for running LAMMPS (Large-scale Atomic/Molecular Massively Parallel Simulator) molecular dynamics simulations.

## Overview

LAMMPS is a classical molecular dynamics code that can be used to model atoms, molecules, and mesoscale particles in various states (solid, liquid, gas) and on different length and time scales.

## Files

- `Dockerfile` - Container definition for LAMMPS simulation environment
- `example.lammps` - Minimal Lennard-Jones fluid simulation demonstrating LAMMPS capabilities
- `README.md` - This documentation file

## Building the Docker Image

```bash
cd src/sim-toolbox/lammps
docker build -t keystone/lammps:latest .
```

## Running the Example Simulation

### Quick Start

Run the example Lennard-Jones fluid simulation:

```bash
docker run --rm \
  -v $(pwd)/example.lammps:/data/input/example.lammps \
  -v $(pwd)/output:/data/output \
  keystone/lammps:latest \
  lmp -in /data/input/example.lammps
```

### Step-by-Step

1. **Create an output directory**:
   ```bash
   mkdir -p output
   ```

2. **Run the simulation**:
   ```bash
   docker run --rm \
     -v $(pwd)/example.lammps:/data/input/example.lammps \
     -v $(pwd)/output:/data/output \
     keystone/lammps:latest \
     lmp -in /data/input/example.lammps
   ```

3. **Check the results**:
   ```bash
   ls output/
   # Should contain: trajectory.lammpstrj, final.data
   ```

## Standard Data Mount Points

The container uses standardized mount points for reproducibility:

- `/data/input` - Mount your input files here
- `/data/output` - Simulation outputs are written here

## Example Simulation Details

The included `example.lammps` script demonstrates:

- **System**: Lennard-Jones fluid with FCC lattice initialization
- **Ensemble**: NVE (constant number of particles, volume, and energy)
- **Duration**: 1000 timesteps
- **Outputs**: 
  - Thermodynamic data printed every 100 steps
  - Trajectory file (`trajectory.lammpstrj`)
  - Final configuration (`final.data`)

## Customizing Simulations

To run your own LAMMPS input script:

1. Create your LAMMPS input file (e.g., `my_simulation.lammps`)
2. Mount it to `/data/input/` in the container
3. Run: `docker run --rm -v $(pwd)/my_simulation.lammps:/data/input/my_simulation.lammps -v $(pwd)/output:/data/output keystone/lammps:latest lmp -in /data/input/my_simulation.lammps`

## Resources

- [LAMMPS Official Documentation](https://docs.lammps.org/)
- [LAMMPS Tutorials](https://lammpstutorials.github.io/)
- [LAMMPS GitHub Repository](https://github.com/lammps/lammps)

## Python Adapter

The LAMMPS toolbox includes a Python adapter (`lammps_adapter.py`) that provides a standardized interface for programmatic simulation execution. This enables:

- Automated container orchestration
- Thermodynamic data parsing
- Result metadata extraction
- Integration with agentic workflows

### Using the Adapter

```python
from lammps_adapter import LAMMPSAdapter

# Create adapter instance
adapter = LAMMPSAdapter(
    image_name="keystone/lammps:latest",
    output_dir="./output"
)

# Run simulation
result = adapter.run_simulation(
    input_script="example.lammps",
    log_file="lammps.log"
)

# Access thermodynamic data
if result['thermo_data']:
    print(f"Timesteps: {result['thermo_data']['summary']['total_steps']}")
    print(f"Final state: {result['thermo_data']['summary']['final']}")

# Save metadata
adapter.save_result_json()
```

### CLI Usage

```bash
# Check if Docker image is available
python3 lammps_adapter.py --check

# Build Docker image
python3 lammps_adapter.py --build

# Run simulation
python3 lammps_adapter.py --output-dir ./my_output --input-script example.lammps
```

See [`lammps_adapter.py`](./lammps_adapter.py) and [`example_adapter_usage.py`](./example_adapter_usage.py) for more details.

For comprehensive adapter documentation, see [ADAPTERS.md](../ADAPTERS.md).

## Integration with Keystone Supercomputer

This toolbox is part of the Keystone Supercomputer project's Phase 3: Simulation Toolbox. It provides:

- **Containerized execution**: Reproducible LAMMPS environment
- **Standardized interfaces**: Common `/data` mount points across all simulation tools
- **Agent integration**: ~~Ready for orchestration via the agentic core~~ ✓ Python adapter implemented

---

~~**Next Steps**: This toolbox will be integrated with Python adapters for automated workflow orchestration.~~ ✓ Completed
