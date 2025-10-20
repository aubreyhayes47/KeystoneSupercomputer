# Automated Post-Run Validation Guide

## Overview

Keystone Supercomputer includes a comprehensive automated validation framework that performs post-run checks on all simulation workflows. The framework integrates convergence analysis, conservation law validation, and regression comparison against established benchmarks.

## Features

### Core Validation Capabilities

1. **Convergence Analysis**
   - Monitors residual convergence for iterative solvers
   - Detects monotonic decrease in residuals
   - Identifies stalled convergence
   - Calculates convergence rates

2. **Conservation Law Validation**
   - Validates mass conservation
   - Validates momentum conservation
   - Validates energy conservation
   - Configurable tolerance levels per law type

3. **Regression Comparison**
   - Compares results against benchmark expectations
   - File existence verification
   - Metric value comparison with tolerances
   - Performance regression detection

4. **Integration Features**
   - Automatic execution after successful simulations
   - Results recorded in provenance logs
   - Alert mechanism for failed checks
   - Validation history and statistics

## Quick Start

### Automatic Validation

Validation is automatically performed after every successful simulation run through the Celery task queue:

```python
from agent.task_pipeline import TaskPipeline

pipeline = TaskPipeline()

# Submit a task - validation happens automatically
task_id = pipeline.submit_task(
    tool="fenicsx",
    script="poisson.py",
    params={"mesh_size": 64, "benchmark_id": "fenicsx-poisson-2d-basic"}
)

# Wait for completion
result = pipeline.wait_for_task(task_id, timeout=300)

# Check validation results
if 'validation' in result:
    validation = result['validation']
    print(f"Validation: {validation['checks_passed']}/{validation['total_checks']} checks passed")
    
    if not validation['validation_passed']:
        print("Failed checks:")
        for check in validation['failed_checks']:
            print(f"  - {check['check_name']}: {check['details']}")
```

### Manual Validation

You can also perform validation manually on existing simulation results:

```python
from validation_integration import validate_task

# Validate existing results
validation_result = validate_task(
    task_id="my-task-123",
    tool="fenicsx",
    output_dir="/path/to/simulation/output",
    benchmark_id="fenicsx-poisson-2d-basic",
    workflow_id="workflow-456"  # Optional for provenance tracking
)

if validation_result['validation_passed']:
    print("All validation checks passed!")
else:
    print(f"Failed checks: {len(validation_result['failed_checks'])}")
```

## Configuration

### Configuration File

Validation behavior is controlled through `validation_config.json`:

```json
{
  "convergence": {
    "max_residual": 1e-6,
    "min_convergence_rate": 0.1,
    "stall_threshold": 5
  },
  "conservation": {
    "mass_tolerance": 1e-6,
    "momentum_tolerance": 1e-6,
    "energy_tolerance": 1e-5
  },
  "regression": {
    "default_tolerance": 0.01
  },
  "alert_on_failure": true
}
```

### Tool-Specific Configuration

Different simulators can have different validation criteria:

```json
{
  "tool_specific": {
    "fenicsx": {
      "convergence": {
        "max_residual": 1e-8
      },
      "regression": {
        "default_tolerance": 0.005
      }
    },
    "lammps": {
      "conservation": {
        "energy_tolerance": 1e-4
      }
    },
    "openfoam": {
      "convergence": {
        "max_residual": 1e-6
      },
      "conservation": {
        "mass_tolerance": 1e-8
      }
    }
  }
}
```

### Configuration Options Reference

#### Convergence Configuration

| Parameter | Description | Default | Example |
|-----------|-------------|---------|---------|
| `max_residual` | Maximum acceptable final residual | `1e-6` | `1e-8` for stricter convergence |
| `min_convergence_rate` | Minimum convergence rate | `0.1` | `0.2` for faster convergence requirement |
| `stall_threshold` | Number of iterations to detect stall | `5` | `10` for more iterations before stall |

#### Conservation Configuration

| Parameter | Description | Default | Example |
|-----------|-------------|---------|---------|
| `mass_tolerance` | Relative tolerance for mass conservation | `1e-6` | `1e-8` for stricter mass conservation |
| `momentum_tolerance` | Relative tolerance for momentum conservation | `1e-6` | `1e-5` for relaxed momentum check |
| `energy_tolerance` | Relative tolerance for energy conservation | `1e-5` | `1e-4` for MD simulations |

#### Regression Configuration

| Parameter | Description | Default | Example |
|-----------|-------------|---------|---------|
| `default_tolerance` | Default relative tolerance for metrics | `0.01` (1%) | `0.005` (0.5%) for tighter checks |

## Validation Workflow

### 1. Convergence Checks

The framework analyzes solver log files to check convergence:

**Log File Format:**
```
Iteration 1: residual = 1.0e-1
Iteration 2: residual = 1.0e-2
Iteration 3: residual = 1.0e-4
Iteration 4: residual = 1.0e-7
```

**Checks Performed:**
- Final residual < `max_residual`
- Monotonic decrease in residuals
- Detection of stalled convergence
- Convergence rate calculation

### 2. Conservation Law Validation

The framework checks conservation laws from results files:

**Results File Format (JSON):**
```json
{
  "mass": [100.0, 100.0, 100.0, 100.0],
  "momentum": [50.0, 49.99, 50.01, 50.0],
  "energy": [1000.0, 1000.01, 999.99, 1000.0]
}
```

**Checks Performed:**
- Relative change from initial to final value
- Comparison against tolerance thresholds
- Reports for each conservation law type

### 3. Regression Comparison

Compares against benchmark definitions:

**Output File Checks:**
- Verifies existence of expected output files
- Reports missing files as failures

**Metric Checks:**
- Extracts actual values from `metrics.json` or log files
- Compares against expected values with tolerance
- Calculates relative error

**Example metrics.json:**
```json
{
  "solution_max": 0.975,
  "solution_min": 0.0,
  "solution_mean": 0.042
}
```

## Alert System

### Built-in Alert Handlers

The framework includes two default alert handlers:

1. **Console Alert Handler**
   - Logs warnings to console for failed checks
   - Includes check names and failure details

2. **File Alert Handler**
   - Writes alert details to `/tmp/keystone_validation/alerts/`
   - Creates one JSON file per failed validation

### Custom Alert Handlers

Register custom handlers for notifications:

```python
from validation_integration import get_validation_integration

def email_alert(alert_data):
    """Send email notification for validation failures."""
    task_id = alert_data['task_id']
    failed_checks = alert_data['failed_checks']
    
    # Send email notification
    send_email(
        to="user@example.com",
        subject=f"Validation Failed: Task {task_id}",
        body=f"Failed checks: {failed_checks}"
    )

# Register handler
validator = get_validation_integration()
validator.validator.register_alert_handler(email_alert)
```

### Slack/Discord Notifications

```python
def slack_alert(alert_data):
    """Post to Slack channel."""
    import requests
    
    webhook_url = "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
    
    message = {
        "text": f"⚠️ Validation Failed: Task {alert_data['task_id']}",
        "attachments": [{
            "color": "danger",
            "fields": [
                {
                    "title": "Failed Checks",
                    "value": str(len(alert_data['failed_checks'])),
                    "short": True
                }
            ]
        }]
    }
    
    requests.post(webhook_url, json=message)

# Register
validator.validator.register_alert_handler(slack_alert)
```

## Provenance Integration

Validation results are automatically recorded in provenance logs:

### Provenance Events

A validation event is added to the execution timeline:

```json
{
  "event_type": "validation",
  "timestamp": "2025-10-20T16:30:00.000Z",
  "event_data": {
    "validation_passed": true,
    "checks_passed": 5,
    "checks_failed": 0,
    "total_checks": 5,
    "failed_checks": [],
    "warnings": []
  }
}
```

### Provenance Metadata

Summary validation metadata is added to the workflow:

```json
{
  "validation_performed": true,
  "validation_timestamp": "2025-10-20T16:30:00.000Z",
  "validation_passed": true,
  "validation_summary": {
    "total_checks": 5,
    "checks_passed": 5,
    "checks_failed": 0
  }
}
```

## Validation History and Statistics

### Query Validation History

```python
from validation_integration import get_validation_integration

validator = get_validation_integration()

# Get all validations for a specific tool
fenicsx_validations = validator.get_validation_history(
    tool="fenicsx",
    limit=50
)

# Get only failed validations
failed_validations = validator.get_validation_history(
    failed_only=True,
    limit=20
)

# Print summary
for validation in fenicsx_validations:
    task_id = validation['metadata']['task_id']
    passed = validation['validation_passed']
    status = "✓ PASSED" if passed else "✗ FAILED"
    print(f"{task_id}: {status}")
```

### Validation Statistics

```python
# Get aggregate statistics
stats = validator.get_validation_statistics()

print(f"Total validations: {stats['total_validations']}")
print(f"Success rate: {stats['success_rate']:.1%}")
print(f"\nBy tool:")
for tool, tool_stats in stats['by_tool'].items():
    print(f"  {tool}: {tool_stats['passed']}/{tool_stats['passed'] + tool_stats['failed']}")

print(f"\nCommon failures:")
for check_name, count in stats['common_failures'].items():
    print(f"  {check_name}: {count} times")
```

## Integration with New Simulators

### Step 1: Define Expected Results in Benchmark

Add a benchmark definition with validation criteria:

```json
{
  "id": "mysim-test-case",
  "simulator": "mysim",
  "expected_results": {
    "output_files": [
      {
        "filename": "solution.dat",
        "description": "Solution data file"
      }
    ],
    "metrics": {
      "solution_norm": {
        "value": 1.234,
        "tolerance": 0.01,
        "unit": "dimensionless"
      }
    }
  },
  "validation_criteria": {
    "method": "tolerance_based",
    "tolerance": 0.01,
    "checks": [
      {
        "name": "solution_output_exists",
        "type": "file_exists",
        "parameters": {
          "filename": "/data/solution.dat"
        }
      }
    ]
  }
}
```

### Step 2: Configure Simulator-Specific Settings

Add to `validation_config.json`:

```json
{
  "tool_specific": {
    "mysim": {
      "convergence": {
        "max_residual": 1e-7,
        "min_convergence_rate": 0.15
      },
      "conservation": {
        "energy_tolerance": 1e-6
      },
      "regression": {
        "default_tolerance": 0.005
      }
    }
  }
}
```

### Step 3: Output Required Files

Ensure your simulator outputs:

1. **simulation.log** - Convergence information
   ```
   Iteration 1: residual = 1.0e-1
   Iteration 2: residual = 1.0e-3
   ...
   ```

2. **results.json** - Conservation values (if applicable)
   ```json
   {
     "mass": [100.0, 100.0, 100.0],
     "energy": [1000.0, 999.99, 1000.01]
   }
   ```

3. **metrics.json** - Computed metrics for comparison
   ```json
   {
     "solution_norm": 1.235,
     "max_value": 0.95,
     "min_value": 0.01
   }
   ```

### Step 4: Test Validation

```python
from validation_integration import validate_task

# Test validation on sample output
result = validate_task(
    task_id="test-mysim",
    tool="mysim",
    output_dir="/path/to/test/output",
    benchmark_id="mysim-test-case"
)

assert result['validation_passed'], "Validation should pass for test case"
```

## Custom Validation Checks

Add custom validation logic for specific needs:

```python
from validation_framework import ValidationFramework

def custom_check(output_dir):
    """Custom validation check."""
    # Read custom metric file
    metric_file = output_dir / 'custom_metric.txt'
    
    if not metric_file.exists():
        return {'passed': False, 'reason': 'Metric file missing'}
    
    with open(metric_file, 'r') as f:
        value = float(f.read().strip())
    
    # Check against threshold
    passed = 0.9 <= value <= 1.1
    
    return {
        'passed': passed,
        'value': value,
        'threshold': [0.9, 1.1],
        'details': 'Custom metric validation'
    }

# Use custom check
framework = ValidationFramework()
result = framework.validate_simulation(
    task_id="task-123",
    tool="fenicsx",
    output_dir="/path/to/output",
    custom_checks={'metric_check': custom_check}
)
```

## Troubleshooting

### Validation Not Running

**Problem:** Validation not executing after simulation

**Solutions:**
1. Check that simulation completed successfully (status == 'success')
2. Verify output directory exists: `/tmp/keystone_output/<task_id>`
3. Check validation logs: `/tmp/keystone_validation/`
4. Ensure validation_integration is imported in celery_app.py

### Missing Convergence Data

**Problem:** Convergence check shows warning "No residuals found"

**Solutions:**
1. Verify log file exists: `simulation.log` in output directory
2. Check log format matches expected patterns (e.g., "residual = 1.0e-4")
3. Add custom log parsing for your solver format

### Conservation Checks Not Running

**Problem:** Conservation law checks skipped

**Solutions:**
1. Ensure `results.json` exists in output directory
2. Check JSON format includes conservation law data
3. Values must be arrays with at least 2 elements

### Metric Comparison Failures

**Problem:** Metrics not matching expected values

**Solutions:**
1. Verify `metrics.json` exists in output directory
2. Check metric names match exactly between actual and expected
3. Review tolerance settings in benchmark definition
4. Check for numerical precision issues

## Best Practices

### 1. Define Realistic Tolerances

- Use appropriate tolerances for each metric type
- Consider numerical precision of your solver
- Account for machine/platform differences

### 2. Include Multiple Validation Checks

- Combine convergence, conservation, and regression checks
- Add custom checks for domain-specific requirements
- Use file existence checks as sanity tests

### 3. Monitor Validation Trends

- Review validation statistics regularly
- Investigate recurring failures
- Update tolerances based on historical data

### 4. Document Expected Behavior

- Document why specific tolerances are chosen
- Note any known platform-specific variations
- Maintain benchmark registry with clear descriptions

### 5. Handle Edge Cases

- Account for simulations without iterative solvers
- Handle optional conservation laws
- Provide meaningful warnings for missing data

## API Reference

### ValidationFramework

Main validation orchestrator class.

```python
ValidationFramework(config: Optional[Dict[str, Any]] = None)
```

**Methods:**

- `validate_simulation(task_id, tool, output_dir, benchmark_id, custom_checks)` - Perform comprehensive validation
- `register_alert_handler(handler)` - Register callback for alerts

### ValidationIntegration

Integration with Keystone systems.

```python
ValidationIntegration(config_file: Optional[Union[str, Path]] = None)
```

**Methods:**

- `validate_task_result(task_id, tool, output_dir, benchmark_id, workflow_id)` - Validate and integrate with provenance
- `get_validation_history(tool, passed_only, failed_only, limit)` - Query validation history
- `get_validation_statistics()` - Get aggregate statistics

### Helper Functions

```python
# Get global validation integration instance
get_validation_integration(config_file: Optional[Union[str, Path]] = None)

# Validate task with automatic integration
validate_task(task_id, tool, output_dir, benchmark_id, workflow_id)

# Load validation configuration
load_validation_config(config_file: Optional[Union[str, Path]] = None)
```

## Examples

See complete examples in:

- `src/example_validation.py` - Basic validation usage
- `src/test_validation_framework.py` - Comprehensive test suite
- `src/validation_integration.py` - Integration examples

## Related Documentation

- [PROVENANCE_SCHEMA.md](PROVENANCE_SCHEMA.md) - Provenance logging schema
- [BENCHMARK_REGISTRY.md](BENCHMARK_REGISTRY.md) - Benchmark registry documentation
- [JOB_MONITORING.md](JOB_MONITORING.md) - Job monitoring system
- [TASK_PIPELINE.md](TASK_PIPELINE.md) - Task pipeline API

## Support

For issues or questions:
1. Check validation logs in `/tmp/keystone_validation/`
2. Review test suite: `python3 src/test_validation_framework.py`
3. Open an issue on GitHub with validation results and logs
