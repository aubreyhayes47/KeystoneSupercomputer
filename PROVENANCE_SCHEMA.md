# Provenance Schema Documentation

## Overview

Keystone Supercomputer automatically generates `provenance.json` files for every simulation run, ensuring complete reproducibility and audit capability. Each provenance record captures comprehensive metadata about workflow execution, tool calls, environment state, and artifact lineage.

## Provenance Schema Version 1.0.0

### Top-Level Schema

```json
{
  "provenance_version": "1.0.0",
  "workflow_id": "string",
  "created_at": "ISO 8601 timestamp with Z suffix",
  "completed_at": "ISO 8601 timestamp with Z suffix",
  "duration_seconds": "number",
  "status": "string (running|completed|failed|timeout)",
  "user_prompt": "string",
  "workflow_plan": "object",
  "tool_calls": "array of tool call objects",
  "software_versions": "object",
  "environment": "object",
  "random_seeds": "object",
  "input_files": "array of file metadata objects",
  "output_files": "array of file metadata objects",
  "execution_timeline": "array of event objects",
  "final_result": "object (optional)",
  "error": "string (optional)",
  "metadata": "object (optional, user-defined)"
}
```

### Field Definitions

#### Core Metadata Fields

| Field | Type | Description | Required |
|-------|------|-------------|----------|
| `provenance_version` | string | Schema version (currently "1.0.0") | Yes |
| `workflow_id` | string | Unique identifier for this workflow execution | Yes |
| `created_at` | string | ISO 8601 timestamp when workflow started | Yes |
| `completed_at` | string | ISO 8601 timestamp when workflow finished | No |
| `duration_seconds` | number | Total execution time in seconds | No |
| `status` | string | Workflow status: `running`, `completed`, `failed`, `timeout` | Yes |
| `user_prompt` | string | Original user request or prompt that initiated the workflow | Yes |
| `workflow_plan` | object | Planned execution strategy and configuration | Yes |

#### Tool Calls

The `tool_calls` array contains records of all simulation tools executed during the workflow:

```json
{
  "timestamp": "ISO 8601 timestamp with Z suffix",
  "tool": "string (fenicsx|lammps|openfoam|etc)",
  "script": "string (script filename)",
  "parameters": "object (tool parameters)",
  "task_id": "string (optional Celery task ID)"
}
```

**Example:**
```json
{
  "timestamp": "2025-10-20T15:30:45.123456Z",
  "tool": "fenicsx",
  "script": "poisson.py",
  "parameters": {
    "mesh_size": 64,
    "solver": "cg"
  },
  "task_id": "abc123-def456-789"
}
```

#### Software Versions

The `software_versions` object captures versions of all relevant software components:

```json
{
  "python": "3.11.5 (main, Sep 11 2023, 13:54:46) [GCC 11.2.0]",
  "platform": "Linux-5.15.0-97-generic-x86_64-with-glibc2.35",
  "celery": "5.3.4",
  "redis": "4.6.0",
  "psutil": "5.9.6",
  "langchain_core": "0.3.29",
  "langgraph": "0.2.59"
}
```

#### Environment

The `environment` object captures runtime environment state:

```json
{
  "hostname": "keystone-worker-01",
  "processor": "x86_64",
  "python_executable": "/usr/bin/python3",
  "working_directory": "/home/user/simulations",
  "user": "sim_user",
  "environment_variables": {
    "OMP_NUM_THREADS": "8",
    "CUDA_VISIBLE_DEVICES": "0",
    "PATH": "/usr/local/bin:/usr/bin:/bin"
  }
}
```

**Note:** Sensitive information in environment variables (e.g., passwords in URLs) is automatically redacted.

#### Random Seeds

The `random_seeds` object captures random number generator states for reproducibility:

```json
{
  "python_random_state": [123456, 789012, 345678, ...]
}
```

#### Input/Output Files

File metadata arrays link workflow artifacts to provenance records:

```json
{
  "path": "/absolute/path/to/file.vtk",
  "filename": "file.vtk",
  "description": "Simulation output mesh",
  "created_at": "2025-10-20T15:31:22.456789Z",
  "checksum": "sha256:abc123...",
  "size_bytes": 1048576
}
```

**Fields:**
- `path`: Absolute path to the file
- `filename`: Base filename
- `description`: Human-readable description (optional)
- `created_at` or `added_at`: Timestamp when file was linked
- `checksum`: SHA256 hash for integrity verification
- `size_bytes`: File size in bytes

#### Execution Timeline

The `execution_timeline` array provides a chronological log of all workflow events:

```json
[
  {
    "timestamp": "2025-10-20T15:30:00.000000Z",
    "event": "workflow_started",
    "details": {}
  },
  {
    "timestamp": "2025-10-20T15:30:05.123456Z",
    "event": "agent_action",
    "details": {
      "agent_role": "conductor",
      "action": "analyze_request",
      "complexity": "high"
    }
  },
  {
    "timestamp": "2025-10-20T15:30:10.234567Z",
    "event": "tool_call",
    "details": {
      "tool": "fenicsx",
      "task_id": "abc123"
    }
  },
  {
    "timestamp": "2025-10-20T15:31:45.567890Z",
    "event": "workflow_completed",
    "details": {
      "status": "completed"
    }
  }
]
```

**Event Types:**
- `workflow_started`: Workflow initiation
- `workflow_completed`: Workflow completion
- `agent_action`: Agent state changes and decisions
- `tool_call`: Simulation tool execution
- Custom events as needed

#### Final Result

The `final_result` object contains the workflow's final output (structure varies by workflow type):

```json
{
  "status": "success",
  "tool": "fenicsx",
  "script": "poisson.py",
  "returncode": 0,
  "resource_usage": {
    "cpu_total_seconds": 123.45,
    "memory_peak_mb": 512.0,
    "duration_seconds": 95.5
  }
}
```

#### Error Handling

For failed workflows, the `error` field contains diagnostic information:

```json
{
  "status": "failed",
  "error": "Simulation crashed: Memory allocation failed",
  "final_result": {
    "returncode": -1,
    "stderr": "Error: Out of memory..."
  }
}
```

#### Custom Metadata

The `metadata` field accepts arbitrary user-defined metadata:

```json
{
  "metadata": {
    "project": "steel_beam_analysis",
    "priority": "high",
    "researcher": "J. Smith",
    "tags": ["structural", "validation"],
    "budget_code": "NSF-12345"
  }
}
```

---

## Usage Examples

### Example 1: Single Simulation Task

```json
{
  "provenance_version": "1.0.0",
  "workflow_id": "20251020_153045_abc12345",
  "created_at": "2025-10-20T15:30:45.000000Z",
  "completed_at": "2025-10-20T15:32:20.500000Z",
  "duration_seconds": 95.5,
  "status": "completed",
  "user_prompt": "Run fenicsx simulation: poisson.py",
  "workflow_plan": {
    "task_id": "abc123-def456-789",
    "tool": "fenicsx",
    "script": "poisson.py",
    "params": {
      "mesh_size": 64
    }
  },
  "tool_calls": [
    {
      "timestamp": "2025-10-20T15:30:45.123456Z",
      "tool": "fenicsx",
      "script": "poisson.py",
      "parameters": {
        "mesh_size": 64
      },
      "task_id": "abc123-def456-789"
    }
  ],
  "software_versions": {
    "python": "3.11.5",
    "celery": "5.3.4",
    "redis": "4.6.0"
  },
  "environment": {
    "hostname": "keystone-worker-01",
    "processor": "x86_64",
    "user": "sim_user",
    "environment_variables": {
      "OMP_NUM_THREADS": "8"
    }
  },
  "random_seeds": {
    "python_random_state": [123456, 789012, 345678]
  },
  "input_files": [],
  "output_files": [
    {
      "path": "/data/output/result.vtk",
      "filename": "result.vtk",
      "description": "FEniCS output mesh",
      "created_at": "2025-10-20T15:32:20.000000Z",
      "checksum": "sha256:abc123def456...",
      "size_bytes": 1048576
    }
  ],
  "execution_timeline": [
    {
      "timestamp": "2025-10-20T15:30:45.000000Z",
      "event": "workflow_started",
      "details": {}
    },
    {
      "timestamp": "2025-10-20T15:30:45.123456Z",
      "event": "tool_call",
      "details": {
        "tool": "fenicsx",
        "task_id": "abc123-def456-789"
      }
    },
    {
      "timestamp": "2025-10-20T15:32:20.500000Z",
      "event": "workflow_completed",
      "details": {
        "status": "completed"
      }
    }
  ],
  "final_result": {
    "status": "success",
    "tool": "fenicsx",
    "script": "poisson.py",
    "returncode": 0,
    "resource_usage": {
      "cpu_total_seconds": 89.2,
      "memory_peak_mb": 256.5,
      "duration_seconds": 95.5
    }
  },
  "metadata": {}
}
```

### Example 2: Multi-Agent Conductor-Performer Workflow

```json
{
  "provenance_version": "1.0.0",
  "workflow_id": "20251020_160000_xyz98765",
  "created_at": "2025-10-20T16:00:00.000000Z",
  "completed_at": "2025-10-20T16:05:30.000000Z",
  "duration_seconds": 330.0,
  "status": "completed",
  "user_prompt": "Run structural analysis on steel beam under 10kN load",
  "workflow_plan": {
    "pattern": "conductor_performer",
    "max_iterations": 3
  },
  "tool_calls": [
    {
      "timestamp": "2025-10-20T16:01:00.000000Z",
      "tool": "fenicsx",
      "script": "structural_analysis.py",
      "parameters": {
        "load": 10000,
        "material": "steel"
      },
      "task_id": "task-001"
    }
  ],
  "software_versions": {
    "python": "3.11.5",
    "celery": "5.3.4",
    "langchain_core": "0.3.29",
    "langgraph": "0.2.59"
  },
  "environment": {
    "hostname": "keystone-controller",
    "processor": "x86_64",
    "user": "sim_user",
    "environment_variables": {}
  },
  "random_seeds": {
    "python_random_state": [987654, 321098, 765432]
  },
  "input_files": [
    {
      "path": "/data/input/beam_geometry.step",
      "filename": "beam_geometry.step",
      "description": "CAD geometry",
      "added_at": "2025-10-20T16:00:30.000000Z",
      "checksum": "sha256:def789abc012...",
      "size_bytes": 524288
    }
  ],
  "output_files": [
    {
      "path": "/data/output/stress_field.vtk",
      "filename": "stress_field.vtk",
      "description": "Stress distribution",
      "created_at": "2025-10-20T16:05:00.000000Z",
      "checksum": "sha256:fed321cba987...",
      "size_bytes": 2097152
    }
  ],
  "execution_timeline": [
    {
      "timestamp": "2025-10-20T16:00:00.000000Z",
      "event": "workflow_started",
      "details": {}
    },
    {
      "timestamp": "2025-10-20T16:00:05.000000Z",
      "event": "agent_action",
      "details": {
        "agent_role": "conductor",
        "action": "workflow_started",
        "user_request": "Run structural analysis on steel beam under 10kN load"
      }
    },
    {
      "timestamp": "2025-10-20T16:00:30.000000Z",
      "event": "agent_action",
      "details": {
        "agent_role": "conductor",
        "action": "analyze_request"
      }
    },
    {
      "timestamp": "2025-10-20T16:01:00.000000Z",
      "event": "agent_action",
      "details": {
        "agent_role": "performer",
        "action": "execute_simulation"
      }
    },
    {
      "timestamp": "2025-10-20T16:05:00.000000Z",
      "event": "agent_action",
      "details": {
        "agent_role": "validator",
        "action": "validate_results"
      }
    },
    {
      "timestamp": "2025-10-20T16:05:30.000000Z",
      "event": "agent_action",
      "details": {
        "agent_role": "conductor",
        "action": "workflow_completed",
        "status": "completed",
        "iterations": 0
      }
    },
    {
      "timestamp": "2025-10-20T16:05:30.000000Z",
      "event": "workflow_completed",
      "details": {
        "status": "completed"
      }
    }
  ],
  "final_result": {
    "status": "completed",
    "result": {
      "workflow_id": "plan_20251020_160030",
      "status": "completed",
      "performer_results": {
        "fenicsx": {
          "max_stress": 250.5,
          "displacement": 0.05
        }
      },
      "validation": {
        "validation_passed": true
      }
    },
    "iterations": 0
  },
  "metadata": {
    "orchestration_type": "langgraph_conductor_performer"
  }
}
```

---

## Audit and Reproducibility Use Cases

### Use Case 1: Result Verification

To verify a simulation result:

1. Locate the `provenance_{workflow_id}.json` file
2. Check `final_result.status` to confirm success
3. Review `tool_calls` for exact parameters used
4. Verify `software_versions` match expected versions
5. Check `input_files` checksums for data integrity

### Use Case 2: Exact Reproduction

To reproduce a workflow exactly:

1. Load the provenance file
2. Extract `tool_calls` array for execution sequence
3. Use `software_versions` to set up identical environment
4. Apply `random_seeds` to RNG state
5. Verify `input_files` checksums before execution
6. Compare `output_files` checksums after execution

### Use Case 3: Performance Analysis

To analyze workflow performance:

1. Review `execution_timeline` for event sequencing
2. Check `duration_seconds` for total time
3. Examine `final_result.resource_usage` for CPU/memory
4. Compare multiple provenance files for performance trends

### Use Case 4: Error Diagnosis

When workflows fail:

1. Check `status` field (should be "failed" or "timeout")
2. Read `error` field for error message
3. Review `execution_timeline` to identify failure point
4. Examine `final_result` for additional diagnostic info
5. Check `tool_calls` to identify problematic parameters

### Use Case 5: Compliance Auditing

For regulatory compliance:

1. Use `list_workflows()` API to enumerate all runs
2. Verify `provenance_version` for schema compatibility
3. Check `user_prompt` for authorized activities
4. Review `environment.user` for access control
5. Validate `created_at` timestamps are within audit period

---

## API Reference

### Python API

```python
from provenance_logger import ProvenanceLogger, get_provenance_logger, validate_provenance_file

# Get global logger instance
logger = get_provenance_logger()

# Start tracking a workflow
workflow_id = logger.start_workflow(
    user_prompt="Run simulation X",
    workflow_plan={"tool": "fenicsx", "script": "test.py"},
    metadata={"project": "my_project"}
)

# Record tool calls
logger.record_tool_call(
    workflow_id=workflow_id,
    tool="fenicsx",
    parameters={"mesh_size": 64},
    script="poisson.py"
)

# Record agent actions
logger.record_agent_action(
    workflow_id=workflow_id,
    agent_role="conductor",
    action="analyze_request"
)

# Link files
logger.add_input_file(workflow_id, "/path/to/input.dat")
logger.add_output_file(workflow_id, "/path/to/output.vtk")

# Finalize and save
provenance_file = logger.finalize_workflow(
    workflow_id=workflow_id,
    status="completed",
    final_result={"result": "success"}
)

# Retrieve provenance
prov = logger.get_provenance(workflow_id)

# List all workflows
workflows = logger.list_workflows(status="completed", limit=100)

# Validate provenance record
validation_result = logger.validate_provenance(prov, strict=True)
if validation_result["valid"]:
    print("Provenance is valid!")
else:
    print("Errors:", validation_result["errors"])
    print("Warnings:", validation_result["warnings"])

# Validate provenance file
result = validate_provenance_file("provenance_abc123.json", strict=True)
if not result["valid"]:
    print(f"Invalid provenance: {result['errors']}")
```

### Automatic Integration

Provenance logging is **automatically integrated** into:
- **Celery Tasks** (`celery_app.py`): All simulation tasks automatically generate provenance
- **LangGraph Workflows** (`conductor_performer_graph.py`): Multi-agent workflows track provenance
- **Task Pipeline** (`task_pipeline.py`): Workflow orchestration includes provenance

No manual instrumentation needed for standard workflows!

---

## Storage and Retrieval

### File Location

Provenance files are stored in `/tmp/keystone_provenance/` by default:

```
/tmp/keystone_provenance/
├── provenance_20251020_153045_abc12345.json
├── provenance_20251020_154030_def67890.json
└── provenance_20251020_160000_xyz98765.json
```

### File Naming Convention

Files follow the pattern: `provenance_{workflow_id}.json`

Where `workflow_id` includes:
- Timestamp: `YYYYMMDD_HHMMSS_microseconds`
- Hash: 8-character MD5 hash of user prompt

Example: `provenance_20251020_153045_123456_abc12345.json`

### Retention Policy

**Recommendation:** Implement a retention policy based on your organization's requirements:

- **Short-term (7-30 days):** Keep all provenance files for active projects
- **Medium-term (6-12 months):** Archive provenance for completed projects
- **Long-term (indefinite):** Retain provenance for published results

### Backup and Archive

For production deployments:

1. **Periodic Backup:** Copy `/tmp/keystone_provenance/` to persistent storage
2. **Database Integration:** Store provenance in PostgreSQL/MongoDB for querying
3. **Object Storage:** Archive to S3/MinIO for long-term retention
4. **Compliance:** Follow data retention regulations (GDPR, HIPAA, etc.)

---

## Best Practices

### 1. Consistent Metadata

Always include relevant metadata:

```python
logger.start_workflow(
    user_prompt="...",
    workflow_plan={...},
    metadata={
        "project": "project_name",
        "researcher": "name",
        "tags": ["category1", "category2"]
    }
)
```

### 2. Descriptive Prompts

Use clear, descriptive user prompts:

✅ Good: `"Run FEniCSx structural analysis on steel beam with 10kN load"`
❌ Bad: `"Run simulation"`

### 3. Link All Artifacts

Always link input and output files:

```python
logger.add_input_file(workflow_id, input_path, description="Mesh file")
logger.add_output_file(workflow_id, output_path, description="Stress field")
```

### 4. Verify Checksums

Before reproducing, verify input file checksums:

```python
import hashlib

def verify_checksum(filepath, expected_checksum):
    sha256 = hashlib.sha256()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256.update(chunk)
    return sha256.hexdigest() == expected_checksum
```

### 5. Version Control Integration

Link provenance to version control:

```python
import subprocess

git_commit = subprocess.check_output(['git', 'rev-parse', 'HEAD']).decode().strip()
logger.start_workflow(
    user_prompt="...",
    metadata={"git_commit": git_commit}
)
```

### 6. Custom Timeline Events

Add custom events for important milestones:

```python
logger.record_agent_action(
    workflow_id=workflow_id,
    agent_role="custom",
    action="checkpoint",
    details={"iteration": 5, "convergence": 0.001}
)
```

---

## Validation and Completeness Checks

### Validation Overview

Keystone Supercomputer includes built-in validation to ensure provenance records are complete and conform to the schema. Validation helps catch missing or malformed metadata that could impact reproducibility.

### Validation Modes

**Strict Mode (default):**
- Both errors and warnings fail validation
- Recommended for production use and compliance auditing
- Ensures maximum completeness of provenance records

**Non-Strict Mode:**
- Only errors fail validation; warnings are informational
- Useful during development or for legacy provenance files
- Allows some flexibility in metadata completeness

### Python API Validation

```python
from provenance_logger import ProvenanceLogger, validate_provenance_file

# Method 1: Validate a provenance dictionary
logger = ProvenanceLogger()
provenance = logger.get_provenance(workflow_id)
result = logger.validate_provenance(provenance, strict=True)

if result["valid"]:
    print("✓ Provenance is valid")
else:
    print("✗ Validation failed")
    for error in result["errors"]:
        print(f"  Error: {error}")
    for warning in result["warnings"]:
        print(f"  Warning: {warning}")

# Method 2: Validate a provenance file
result = validate_provenance_file("/tmp/keystone_provenance/provenance_abc123.json")
print(f"Valid: {result['valid']}")
print(f"Schema version: {result['version']}")
```

### Command-Line Validation Tool

The `validate_provenance.py` tool provides command-line validation:

```bash
# Validate a single file
python3 src/validate_provenance.py provenance_abc123.json

# Validate all files in a directory
python3 src/validate_provenance.py /tmp/keystone_provenance/

# Non-strict mode (warnings don't fail validation)
python3 src/validate_provenance.py --non-strict provenance_abc123.json

# Verbose output (show all warnings)
python3 src/validate_provenance.py --verbose provenance_abc123.json

# Combine options
python3 src/validate_provenance.py --non-strict --verbose /tmp/keystone_provenance/
```

### Validation Checks

The validator performs the following checks:

#### Required Field Validation
- All required fields must be present: `provenance_version`, `workflow_id`, `created_at`, `status`, `user_prompt`, `workflow_plan`, `tool_calls`, `software_versions`, `environment`, `random_seeds`, `input_files`, `output_files`, `execution_timeline`
- Field types must match schema (e.g., `tool_calls` must be a list)

#### Status-Dependent Validation
- Completed/failed/timeout workflows must include:
  - `completed_at` timestamp
  - `duration_seconds` field

#### Timestamp Format Validation
- Timestamps should be ISO 8601 format with Z suffix
- Example: `2025-10-20T15:30:45.123456Z`

#### Tool Call Validation
- Each tool call should include: `timestamp`, `tool`, `parameters`
- Missing fields generate warnings

#### Software Version Validation
- `software_versions` should not be empty
- Should include at minimum: `python`, `platform`

#### Environment Validation
- Environment should include: `hostname`, `processor`, `python_executable`, `working_directory`, `user`, `environment_variables`

#### File Metadata Validation
- Input/output files should include: `path`, `filename`
- Should include `checksum` for reproducibility (warning if missing)

#### Timeline Validation
- Timeline should not be empty
- Should include `workflow_started` event
- Completed workflows should include `workflow_completed` event

#### Error and Result Validation
- Failed workflows should include `error` field
- Completed workflows should include `final_result` field

### Validation Result Structure

```python
{
    "valid": bool,           # True if provenance passes validation
    "errors": [str],         # List of error messages (always fail)
    "warnings": [str],       # List of warnings (fail only in strict mode)
    "version": str,          # Provenance schema version
    "filepath": str          # File path (when using validate_provenance_file)
}
```

### Example Validation Workflow

```python
from provenance_logger import get_provenance_logger, validate_provenance_file
import sys

# Start and finalize a workflow
logger = get_provenance_logger()
workflow_id = logger.start_workflow(
    user_prompt="Run FEniCS simulation",
    workflow_plan={"tool": "fenicsx", "script": "poisson.py"}
)

logger.record_tool_call(workflow_id, "fenicsx", {"mesh_size": 64})
provenance_file = logger.finalize_workflow(
    workflow_id, 
    status="completed",
    final_result={"status": "success"}
)

# Validate the generated provenance file
result = validate_provenance_file(provenance_file, strict=True)
if not result["valid"]:
    print("Provenance validation failed!")
    for error in result["errors"]:
        print(f"  Error: {error}")
    sys.exit(1)

print("✓ Provenance validated successfully")
```

### Batch Validation for Auditing

For compliance auditing, validate all provenance files:

```bash
# Audit all provenance files in strict mode
python3 src/validate_provenance.py --verbose /tmp/keystone_provenance/

# The tool returns exit code 0 if all files are valid, 1 otherwise
# This can be integrated into CI/CD pipelines or cron jobs
```

Example audit script:

```bash
#!/bin/bash
# audit_provenance.sh

PROVENANCE_DIR="/tmp/keystone_provenance"
LOG_FILE="/var/log/provenance_audit.log"

echo "Starting provenance audit: $(date)" >> "$LOG_FILE"

if python3 src/validate_provenance.py --verbose "$PROVENANCE_DIR" >> "$LOG_FILE" 2>&1; then
    echo "✓ All provenance files valid" >> "$LOG_FILE"
    exit 0
else
    echo "✗ Some provenance files invalid" >> "$LOG_FILE"
    # Send alert notification here
    exit 1
fi
```

---

## Troubleshooting

### Provenance File Not Created

**Symptom:** Workflow completes but no provenance file exists.

**Solutions:**
1. Check write permissions on `/tmp/keystone_provenance/`
2. Verify `finalize_workflow()` was called
3. Check for exceptions in logs

### Missing Tool Calls

**Symptom:** `tool_calls` array is empty.

**Solutions:**
1. Ensure `record_tool_call()` is called for each tool execution
2. Check that workflow_id is correct
3. Verify task execution completed

### Incomplete Timeline

**Symptom:** `execution_timeline` missing events.

**Solutions:**
1. Check that `record_agent_action()` is called at key points
2. Verify workflow didn't crash before finalization
3. Review exception logs

### Large File Sizes

**Symptom:** Provenance files are very large (>10MB).

**Solutions:**
1. Reduce `final_result` verbosity (truncate stdout/stderr)
2. Avoid storing large arrays in timeline events
3. Use references instead of embedding data

---

## Schema Evolution

The provenance schema uses semantic versioning:

- **Major version** (X.0.0): Breaking changes to required fields
- **Minor version** (1.X.0): New optional fields
- **Patch version** (1.0.X): Bug fixes, no schema changes

Current version: **1.0.0**

### Backward Compatibility

Older provenance files remain valid. Tools should:
1. Check `provenance_version` field
2. Handle missing optional fields gracefully
3. Validate required fields based on version

---

## Related Documentation

- **[README.md](README.md)** - Project overview and quick start
- **[JOB_MONITORING.md](JOB_MONITORING.md)** - Resource usage tracking
- **[ORCHESTRATION_GUIDE.md](ORCHESTRATION_GUIDE.md)** - Workflow orchestration
- **[CONDUCTOR_PERFORMER_ARCHITECTURE.md](CONDUCTOR_PERFORMER_ARCHITECTURE.md)** - Multi-agent system
- **[CLI_REFERENCE.md](CLI_REFERENCE.md)** - Command-line interface

---

## Support

For questions or issues with provenance logging:

1. Check this documentation
2. Review example provenance files in `/tmp/keystone_provenance/`
3. Run tests: `python3 src/test_provenance_logger.py`
4. Open a GitHub issue with example provenance file

---

**Last Updated:** 2025-10-20  
**Schema Version:** 1.0.0  
**Maintainer:** Keystone Supercomputer Team
