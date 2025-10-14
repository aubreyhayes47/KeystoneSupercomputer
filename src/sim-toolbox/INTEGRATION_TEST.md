# Simulation Toolbox Integration Test

## Overview

This integration test validates the end-to-end functionality of the Keystone Supercomputer simulation toolbox by running at least one simulation in each of the three containerized tools:

1. **FEniCSx** - Finite Element Analysis (Poisson equation)
2. **LAMMPS** - Molecular Dynamics (Lennard-Jones fluid)
3. **OpenFOAM** - Computational Fluid Dynamics (cavity flow)

The test ensures that:
- Docker images can be built or are available
- Adapters successfully automate container execution
- Simulations run to completion without errors
- Output results are collected and saved
- Results are properly structured and parseable
- End-to-end workflow orchestration is functional

## Quick Start

### Run Without Building Images

If you already have the Docker images built:

```bash
cd src/sim-toolbox
python3 integration_test.py
```

### Run With Image Building

To build all Docker images before running tests:

```bash
cd src/sim-toolbox
python3 integration_test.py --build
```

**Note:** Building images can take 15-30 minutes depending on your system.

### Custom Output Location

Specify a custom output directory and report file:

```bash
python3 integration_test.py \
  --output-dir /path/to/output \
  --report /path/to/report.md
```

## Command Line Options

- `--build` - Build Docker images before running tests
- `--output-dir OUTPUT_DIR` - Base directory for test outputs (default: `./integration_test_output`)
- `--report REPORT` - Path to save test report (default: `integration_test_report.md`)

## Test Details

### Test 1: FEniCSx - Poisson Equation

**Simulation Type:** Finite Element Analysis

**Description:** Solves the 2D Poisson equation `-∇²u = f` in a unit square with Dirichlet boundary conditions.

**Script:** `fenicsx/poisson.py`

**Expected Outputs:**
- Solution files (`.xdmf`, `.h5`)
- Simulation metadata (mesh cells, DOF count)
- `simulation_result.json`

**Validation:** 
- Simulation completes successfully
- Output files are generated
- Metadata is extracted and reported

### Test 2: LAMMPS - Lennard-Jones Fluid

**Simulation Type:** Molecular Dynamics

**Description:** MD simulation of argon-like atoms with Lennard-Jones potential in a periodic box.

**Script:** `lammps/example.lammps`

**Expected Outputs:**
- Trajectory file (`trajectory.lammpstrj`)
- Final configuration (`final.data`)
- Log file with thermodynamic data
- `simulation_result.json`

**Validation:**
- Simulation completes 1000 timesteps
- Thermodynamic data is extracted
- Final state values are reported

### Test 3: OpenFOAM - Cavity Flow

**Simulation Type:** Computational Fluid Dynamics

**Description:** Incompressible laminar flow in a lid-driven cavity using icoFoam solver.

**Script:** `openfoam/example_cavity.py`

**Expected Outputs:**
- Time directory results (`0/`, `0.1/`, `0.2/`, etc.)
- Log files (`log.blockMesh`, `log.icoFoam`)
- `simulation_result.json`

**Validation:**
- Mesh generation succeeds (blockMesh)
- Solver completes all timesteps
- Solution fields are written

## Output Structure

Test outputs are organized in the following structure:

```
integration_test_output/
├── fenicsx/
│   ├── simulation_result.json
│   ├── solution.xdmf
│   ├── solution.h5
│   └── [other FEniCSx outputs]
├── lammps/
│   ├── simulation_result.json
│   ├── trajectory.lammpstrj
│   ├── final.data
│   └── lammps.log
└── openfoam/
    ├── simulation_result.json
    ├── 0/
    ├── 0.1/
    ├── 0.2/
    └── [time directories and logs]
```

Each subdirectory contains:
- `simulation_result.json` - Structured metadata about the simulation
- Tool-specific output files
- Any logs or diagnostic information

## Test Report

After running, a markdown report is automatically generated with:

- Test execution summary
- Pass/fail status for each test
- Timing information
- Detailed results and metadata
- Error messages (if any)
- Validation criteria checklist

Example report header:

```markdown
# Simulation Toolbox Integration Test Report

**Generated:** 2025-10-14 20:29:08
**Total Duration:** 45.23 seconds

## Summary
- **Total Tests:** 3
- **Passed:** 3
- **Failed:** 0
- **Success Rate:** 100.0%

**Status:** ✓ ALL TESTS PASSED
```

## Prerequisites

### System Requirements

- Docker installed and running
- Python 3.8 or higher
- At least 4GB free disk space for images
- At least 2GB RAM

### Python Dependencies

The test uses only standard library modules and the existing adapter implementations:
- `sys`, `json`, `argparse`, `pathlib`, `datetime`
- `fenicsx_adapter`, `lammps_adapter`, `openfoam_adapter`

No additional pip packages required.

### Docker Images

The test requires the following Docker images:

- `fenicsx-toolbox` - FEniCSx finite element framework
- `keystone/lammps:latest` - LAMMPS molecular dynamics
- `openfoam-toolbox` - OpenFOAM CFD toolkit

These can be built automatically with the `--build` flag, or manually:

```bash
# FEniCSx
cd src/sim-toolbox/fenicsx
docker build -t fenicsx-toolbox .

# LAMMPS
cd src/sim-toolbox/lammps
docker build -t keystone/lammps:latest .

# OpenFOAM
cd src/sim-toolbox/openfoam
docker build -t openfoam-toolbox .
```

## Troubleshooting

### Docker Images Not Available

**Error:** `Docker image not available`

**Solution:** Run with `--build` flag to build images automatically:

```bash
python3 integration_test.py --build
```

Or build images manually as shown above.

### Docker Daemon Not Running

**Error:** `Cannot connect to the Docker daemon`

**Solution:** Start Docker:

```bash
sudo systemctl start docker
# or on macOS/Windows: Start Docker Desktop
```

### Permission Denied

**Error:** `Permission denied while trying to connect to Docker`

**Solution:** Add your user to the docker group:

```bash
sudo usermod -aG docker $USER
# Log out and back in for changes to take effect
```

### Insufficient Resources

**Error:** Simulation fails with out-of-memory or similar errors

**Solution:** 
- Close other applications to free up RAM
- Increase Docker resource limits (Docker Desktop → Settings → Resources)
- Run tests individually instead of all at once

### Script Not Found

**Error:** `No such file or directory: 'fenicsx/poisson.py'`

**Solution:** Make sure you're running from the correct directory:

```bash
cd src/sim-toolbox
python3 integration_test.py
```

## Integration with CI/CD

The integration test is designed to be CI/CD friendly:

### Exit Codes

- `0` - All tests passed
- `1` - One or more tests failed

### Example GitHub Actions Workflow

```yaml
name: Integration Test

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      
      - name: Build Docker images
        run: |
          cd src/sim-toolbox/fenicsx && docker build -t fenicsx-toolbox .
          cd ../lammps && docker build -t keystone/lammps:latest .
          cd ../openfoam && docker build -t openfoam-toolbox .
      
      - name: Run integration test
        run: |
          cd src/sim-toolbox
          python3 integration_test.py --output-dir $GITHUB_WORKSPACE/test_output
      
      - name: Upload test report
        uses: actions/upload-artifact@v2
        with:
          name: integration-test-report
          path: src/sim-toolbox/integration_test_report.md
      
      - name: Upload test outputs
        uses: actions/upload-artifact@v2
        if: always()
        with:
          name: integration-test-outputs
          path: $GITHUB_WORKSPACE/test_output/
```

## Extending the Test

To add new simulations or toolboxes:

1. Add the adapter to the imports
2. Create a new test method (e.g., `test_new_tool()`)
3. Add the test to `run_all_tests()`:
   ```python
   self.results.append(self.test_new_tool())
   ```
4. Follow the same pattern as existing tests

## Related Documentation

- [ADAPTERS.md](./ADAPTERS.md) - Detailed adapter documentation
- [FEniCSx README](./fenicsx/README.md) - FEniCSx-specific details
- [LAMMPS README](./lammps/README.md) - LAMMPS-specific details
- [OpenFOAM README](./openfoam/README.md) - OpenFOAM-specific details
- [Project README](../../README.md) - Overall project documentation

---

**Part of Phase 3: Simulation Toolbox** - Keystone Supercomputer Project
