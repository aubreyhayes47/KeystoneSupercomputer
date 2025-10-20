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
from provenance_logger import ProvenanceLogger, get_provenance_logger

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
