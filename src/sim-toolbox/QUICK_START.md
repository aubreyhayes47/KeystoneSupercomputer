# Quick Reference: Integration Test

## Running the Integration Test

### Prerequisites
```bash
# Ensure Docker is running
docker --version

# Navigate to the test directory
cd src/sim-toolbox
```

### Run Test (Images Already Built)
```bash
python3 integration_test.py
```

### Run Test with Image Building
```bash
python3 integration_test.py --build
```
**Note:** This will take 15-30 minutes to build all images.

### Custom Output Location
```bash
python3 integration_test.py \
  --output-dir /path/to/output \
  --report /path/to/report.md
```

## Expected Outputs

### Console Output
```
================================================================================
SIMULATION TOOLBOX INTEGRATION TEST
================================================================================
Start time: 2025-10-14 15:30:00
Output directory: ./integration_test_output
Build images: False
================================================================================

TEST 1: FEniCSx (Finite Element Analysis)
...
✓ Simulation completed successfully!

TEST 2: LAMMPS (Molecular Dynamics)
...
✓ Simulation completed successfully!

TEST 3: OpenFOAM (Computational Fluid Dynamics)
...
✓ Simulation completed successfully!

================================================================================
INTEGRATION TEST SUMMARY
================================================================================
Total tests: 3
Passed: 3
Failed: 0
Total duration: 45.23 seconds
...
✓ ALL INTEGRATION TESTS PASSED!
```

### Generated Files
- `integration_test_report.md` - Detailed markdown report
- `integration_test_output/` - Directory with all simulation outputs
  - `fenicsx/simulation_result.json` + output files
  - `lammps/simulation_result.json` + output files
  - `openfoam/simulation_result.json` + output files

## Exit Codes
- `0` - All tests passed
- `1` - One or more tests failed

## What's Validated
1. ✓ Docker images are available or can be built
2. ✓ Adapters successfully automate container workflows
3. ✓ Simulations run to completion without errors
4. ✓ Output results are collected and saved properly
5. ✓ Results have proper structure and metadata
6. ✓ End-to-end orchestration functions correctly

## Full Documentation
See [INTEGRATION_TEST.md](./INTEGRATION_TEST.md) for complete documentation.
