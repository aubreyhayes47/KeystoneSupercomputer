# Validation Quick Start Guide

Quick reference for automated post-run validation in Keystone Supercomputer.

## 3-Minute Quick Start

### 1. Automatic Validation (Default)

Validation runs automatically after every successful simulation:

```python
from agent.task_pipeline import TaskPipeline

pipeline = TaskPipeline()
task_id = pipeline.submit_task(
    tool="fenicsx",
    script="poisson.py",
    params={"benchmark_id": "fenicsx-poisson-2d-basic"}  # Optional
)

result = pipeline.wait_for_task(task_id, timeout=300)

# Check validation
if 'validation' in result:
    v = result['validation']
    print(f"✓ {v['checks_passed']}/{v['total_checks']} checks passed")
```

### 2. Manual Validation

Validate existing results:

```python
from validation_integration import validate_task

result = validate_task(
    task_id="my-task-123",
    tool="fenicsx",
    output_dir="/path/to/output",
    benchmark_id="fenicsx-poisson-2d-basic"
)

print(f"Passed: {result['validation_passed']}")
```

### 3. View Validation History

```python
from validation_integration import get_validation_integration

validator = get_validation_integration()

# Recent validations
history = validator.get_validation_history(limit=10)

# Statistics
stats = validator.get_validation_statistics()
print(f"Success rate: {stats['success_rate']:.1%}")
```

## Validation Types

### Convergence Analysis

Checks solver convergence from log files:

**Required:** `simulation.log` with residual patterns like:
```
Iteration 1: residual = 1.0e-1
Iteration 2: residual = 1.0e-7
```

**Checks:**
- Final residual < threshold
- Monotonic decrease
- Stalled convergence detection

### Conservation Laws

Validates physical conservation from results:

**Required:** `results.json` with conservation data:
```json
{
  "mass": [100.0, 100.0, 100.0],
  "energy": [1000.0, 1000.01, 999.99]
}
```

**Checks:**
- Mass conservation
- Momentum conservation  
- Energy conservation

### Regression Comparison

Compares against benchmark expectations:

**Required:** Benchmark ID and expected results

**Checks:**
- Output files exist
- Metrics match expected values
- Within tolerance thresholds

## Configuration

Edit `src/validation_config.json`:

```json
{
  "convergence": {
    "max_residual": 1e-6
  },
  "conservation": {
    "mass_tolerance": 1e-6,
    "energy_tolerance": 1e-5
  },
  "regression": {
    "default_tolerance": 0.01
  }
}
```

## Custom Validation

Add custom checks:

```python
from validation_framework import ValidationFramework

def custom_check(output_dir):
    # Check custom convergence criterion
    metric_file = output_dir / 'custom_metric.txt'
    if not metric_file.exists():
        return {'passed': False, 'details': 'Metric file missing'}
    
    with open(metric_file, 'r') as f:
        value = float(f.read().strip())
    
    passed = 0.9 <= value <= 1.1  # Within 10% of expected
    return {
        'passed': passed,
        'value': value,
        'details': f'Custom metric: {value} (expected: 0.9-1.1)'
    }

validator = ValidationFramework()
result = validator.validate_simulation(
    task_id="task-123",
    tool="fenicsx",
    output_dir="/path/to/output",
    custom_checks={'my_check': custom_check}
)
```

## Alert Handlers

Register custom alerts:

```python
from validation_integration import get_validation_integration

def my_alert(alert_data):
    print(f"⚠️  Task {alert_data['task_id']} failed validation!")
    # Send email, Slack message, etc.

validator = get_validation_integration()
validator.validator.register_alert_handler(my_alert)
```

## Output Files Required

For full validation, simulations should produce:

1. **simulation.log** - Convergence information
2. **results.json** - Conservation values (optional)
3. **metrics.json** - Computed metrics (optional)

Example metrics.json:
```json
{
  "solution_max": 0.975,
  "solution_mean": 0.042
}
```

## Common Commands

```bash
# Run examples
python3 src/example_validation.py

# Run tests
python3 src/test_validation_framework.py

# View configuration
cat src/validation_config.json

# Check validation logs
ls /tmp/keystone_validation/results/
ls /tmp/keystone_validation/alerts/
```

## Troubleshooting

### No Validation Results

**Problem:** `'validation'` key not in result

**Fix:** 
- Check simulation succeeded (status == 'success')
- Verify output directory exists
- Check celery_app.py imports validation_integration

### Convergence Check Fails

**Problem:** "No residuals found in log file"

**Fix:**
- Ensure simulation.log exists
- Check log format matches patterns
- Verify residual lines like "residual = 1.0e-4"

### Conservation Check Skipped

**Problem:** Conservation checks not running

**Fix:**
- Create results.json in output directory
- Include arrays with 2+ values
- Format: `{"mass": [100.0, 100.0]}`

### Metric Comparison Fails

**Problem:** Metrics don't match expected

**Fix:**
- Create metrics.json in output directory  
- Check metric names match exactly
- Review tolerance in benchmark definition

## Integration with New Simulators

### Step 1: Define Benchmark

Create benchmark with expected results:

```json
{
  "id": "mysim-test",
  "simulator": "mysim",
  "expected_results": {
    "output_files": [
      {"filename": "solution.dat"}
    ],
    "metrics": {
      "solution_norm": {
        "value": 1.234,
        "tolerance": 0.01
      }
    }
  }
}
```

### Step 2: Configure Validation

Add to validation_config.json:

```json
{
  "tool_specific": {
    "mysim": {
      "convergence": {
        "max_residual": 1e-7
      },
      "conservation": {
        "energy_tolerance": 1e-6
      }
    }
  }
}
```

### Step 3: Output Required Files

Ensure simulator outputs:
- simulation.log (convergence)
- results.json (conservation, optional)
- metrics.json (regression comparison)

### Step 4: Test

```python
from validation_integration import validate_task

result = validate_task(
    task_id="test-mysim",
    tool="mysim",
    output_dir="/test/output",
    benchmark_id="mysim-test"
)

assert result['validation_passed']
```

## Full Documentation

See [VALIDATION_GUIDE.md](VALIDATION_GUIDE.md) for:
- Complete API reference
- Advanced configuration
- Custom validation examples
- Alert system details
- Integration patterns
