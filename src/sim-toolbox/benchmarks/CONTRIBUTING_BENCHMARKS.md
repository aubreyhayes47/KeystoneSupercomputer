# Contributing Benchmarks to sim-toolbox

Thank you for your interest in contributing benchmarks to the sim-toolbox registry! This guide will help you create high-quality benchmark cases that are valuable to the community.

## Overview

Benchmarks serve multiple purposes:
- **Validation**: Verify simulator installations work correctly
- **Education**: Teach users how to use simulation tools
- **Performance**: Compare hardware and software configurations
- **Regression Testing**: Detect when changes break functionality
- **Reproducibility**: Provide standardized test cases

## Before You Start

1. **Check existing benchmarks**: Review similar benchmarks to understand the format
2. **Verify it's needed**: Ensure your benchmark adds value and doesn't duplicate existing ones
3. **Test locally**: Make sure your benchmark works before submitting
4. **Read the schema**: Familiarize yourself with `benchmark_schema.json`

## Step-by-Step Guide

### 1. Prepare Your Benchmark

#### Choose a Problem
- **Relevant**: Address real simulation needs
- **Well-defined**: Clear problem statement and expected results
- **Documented**: Reference papers or standards if applicable
- **Appropriate scope**: Reasonable execution time (beginner: < 5 min, intermediate: < 15 min)

#### Create Input Files
- Place input files in the appropriate simulator directory (`fenicsx/`, `lammps/`, or `openfoam/`)
- Use descriptive filenames
- Include comments explaining the setup
- Ensure files are minimal but complete

#### Determine Expected Results
- Run the benchmark multiple times to verify consistency
- Document output files produced
- Record key metrics (with tolerances for numerical precision)
- Note typical performance on reference hardware

### 2. Create the Benchmark Definition

Create a JSON file in the appropriate directory: `{simulator}/{benchmark-name}.json`

#### Naming Convention
```
{simulator}-{problem-type}-{variant}
```

Examples:
- `fenicsx-heat-equation-1d`
- `lammps-water-box-equilibration`
- `openfoam-pipe-flow-laminar`

#### Required Sections

**Identification**
```json
{
  "id": "fenicsx-heat-equation-1d",
  "name": "1D Heat Equation",
  "simulator": "fenicsx",
  "version": "1.0.0"
}
```

**Description**
```json
{
  "description": "Detailed description of the problem, including equations, boundary conditions, and physical setup.",
  "category": "thermal-analysis",
  "difficulty": "beginner",
  "tags": ["heat-equation", "transient", "1d"]
}
```

**Input Files**
```json
{
  "input_files": [
    {
      "filename": "heat_1d.py",
      "description": "FEniCSx script for 1D heat equation",
      "path": "../../fenicsx/heat_1d.py",
      "checksum": "compute_this_after_creating_file"
    }
  ]
}
```

**Expected Results**
```json
{
  "expected_results": {
    "output_files": [
      {
        "filename": "temperature.xdmf",
        "description": "Temperature field over time"
      }
    ],
    "metrics": {
      "final_temperature_max": {
        "value": 1.0,
        "tolerance": 0.01,
        "unit": "K"
      }
    },
    "performance": {
      "typical_runtime_seconds": 10,
      "memory_mb": 128,
      "reference_hardware": "Intel Core i7-1165G7 @ 2.80GHz, 16GB RAM"
    }
  }
}
```

**Validation Criteria**
```json
{
  "validation_criteria": {
    "method": "tolerance_based",
    "tolerance": 0.01,
    "checks": [
      {
        "name": "output_exists",
        "type": "file_exists",
        "parameters": {
          "filename": "/data/temperature.xdmf"
        }
      },
      {
        "name": "max_temperature",
        "type": "metric_value",
        "parameters": {
          "metric": "final_temperature_max",
          "expected": 1.0,
          "tolerance": 0.01
        }
      }
    ]
  }
}
```

**Metadata**
```json
{
  "metadata": {
    "author": "Your Name",
    "created_date": "2025-10-20",
    "license": "MIT",
    "references": [
      "Reference paper or textbook",
      "Relevant URL"
    ]
  }
}
```

**Execution**
```json
{
  "execution": {
    "command": "python3 heat_1d.py",
    "parameters": {
      "time_steps": 100,
      "dt": 0.01
    },
    "timeout_seconds": 120,
    "requires_gpu": false,
    "parallel": {
      "enabled": false,
      "processes": 1,
      "threads": 1
    }
  }
}
```

### 3. Compute Checksums

Calculate SHA256 checksums for all input files:

```bash
sha256sum path/to/input/file.py
```

Update the `checksum` field in your benchmark definition.

### 4. Validate Your Benchmark

```bash
cd src/sim-toolbox/benchmarks

# Validate schema compliance
python3 benchmark_registry.py validate --benchmark-id your-benchmark-id
```

Fix any validation errors before proceeding.

### 5. Test Execution

Run your benchmark to ensure it works:

```bash
# For FEniCSx
cd ../../fenicsx
docker compose run --rm fenicsx your_script.py

# For LAMMPS
cd ../../lammps
docker compose run --rm lammps -in your_script.lammps

# For OpenFOAM
cd ../../openfoam
docker compose run --rm openfoam python3 your_script.py
```

Verify:
- ✅ Execution completes without errors
- ✅ Output files are created
- ✅ Results match expected values (within tolerances)
- ✅ Execution time is reasonable

### 6. Submit Your Contribution

#### Create Pull Request

1. Fork the repository
2. Create a new branch: `git checkout -b add-benchmark-{name}`
3. Add your files:
   - Benchmark JSON definition
   - Input files (if new)
   - Any validation scripts
4. Commit with clear message: `git commit -m "Add {benchmark-name} benchmark for {simulator}"`
5. Push and create pull request

#### Pull Request Description

Include in your PR description:
- **Purpose**: What does this benchmark test?
- **Validation**: How did you verify it works?
- **Hardware**: What system did you test on?
- **References**: Any relevant documentation
- **Checklist**: Complete the checklist below

## Contribution Checklist

Before submitting your pull request, ensure:

### Technical Requirements
- [ ] Benchmark JSON validates against schema
- [ ] Unique benchmark ID following naming convention
- [ ] All input files present with correct checksums
- [ ] Expected results documented with tolerances
- [ ] Execution tested and works correctly
- [ ] Completes within specified timeout
- [ ] Validation criteria clearly defined

### Quality Requirements
- [ ] Clear, detailed problem description
- [ ] Scientifically or educationally relevant
- [ ] Reproducible results verified
- [ ] Appropriate difficulty level assigned
- [ ] Reasonable execution time for difficulty level
- [ ] Appropriate tolerances for numerical precision

### Documentation Requirements
- [ ] Complete metadata (author, date, license)
- [ ] References to literature or standards (if applicable)
- [ ] Description of expected output
- [ ] Explanation of validation criteria
- [ ] Hardware requirements specified

### Code Quality
- [ ] Input scripts well-commented
- [ ] Clear variable names
- [ ] Minimal but complete examples
- [ ] Follows simulator best practices

## Difficulty Guidelines

### Beginner
- **Purpose**: Learning and validation
- **Complexity**: Single physics, simple geometry
- **Runtime**: < 5 minutes
- **Examples**: Poisson equation, Lennard-Jones fluid, cavity flow

### Intermediate
- **Purpose**: Realistic applications
- **Complexity**: Multi-step workflows, moderate geometry
- **Runtime**: 5-15 minutes
- **Examples**: Structural analysis, polymer equilibration, turbulent flow

### Advanced
- **Purpose**: Complex simulations
- **Complexity**: Coupled physics, large systems
- **Runtime**: 15-60 minutes
- **Examples**: Multi-physics, large MD systems, complex CFD

### Expert
- **Purpose**: Research-grade simulations
- **Complexity**: Cutting-edge problems
- **Runtime**: > 60 minutes
- **Examples**: Extreme-scale simulations, novel methods

## Best Practices

### Input Files
- Use standard formats
- Include comments
- Set reasonable defaults
- Make parameters clear

### Expected Results
- Run multiple times to ensure consistency
- Set tolerances accounting for:
  - Numerical precision (typically 1e-6 to 1e-3)
  - Hardware variations (CPU vs GPU)
  - Solver algorithms (iterative vs direct)
- Document reference hardware clearly

### Validation
- Prefer tolerance-based over exact match
- Include multiple checks (files exist, values correct)
- Test validation on different systems
- Consider edge cases

### Documentation
- Explain the physics/chemistry
- Cite original sources
- Describe assumptions
- Note limitations

## Common Issues

### Problem: Benchmark fails on different hardware
**Solution**: Increase tolerances or specify hardware requirements

### Problem: Results are non-deterministic
**Solution**: Set random seeds, document expected variation

### Problem: Execution time varies widely
**Solution**: Specify reference hardware, note scaling behavior

### Problem: Output format changes between simulator versions
**Solution**: Document required simulator version, use stable formats

## Review Process

After submission:
1. **Automated checks**: Schema validation, syntax checks
2. **Manual review**: Quality, relevance, completeness
3. **Testing**: Execution on reference hardware
4. **Feedback**: Reviewers may request changes
5. **Approval**: Merged once all criteria met

## Examples

Refer to existing benchmarks for examples:
- [fenicsx/poisson-2d-basic.json](fenicsx/poisson-2d-basic.json)
- [lammps/lennard-jones-fluid.json](lammps/lennard-jones-fluid.json)
- [openfoam/cavity-flow.json](openfoam/cavity-flow.json)

## Getting Help

If you need assistance:
1. Review existing benchmarks
2. Check the [BENCHMARK_REGISTRY.md](../../../BENCHMARK_REGISTRY.md) documentation
3. Open a GitHub issue with tag `benchmark-contribution`
4. Ask in discussions

## License

By contributing benchmarks, you agree to license them under an open-source license (MIT, Apache 2.0, or similar). Specify the license in the benchmark metadata.

## Acknowledgments

Thank you for contributing to sim-toolbox! Your benchmarks help others learn, validate installations, and advance scientific computing.

---

**Questions?** Open an issue or discussion on GitHub.
