# Multi-Agent System Quick Reference

## Overview

The Keystone Supercomputer multi-agent system uses a **Conductor-Performer pattern** built with LangGraph to orchestrate complex simulation workflows across multiple specialized agents.

## Quick Start

### Basic Usage

```python
from conductor_performer_graph import ConductorPerformerGraph

# Initialize the graph
graph = ConductorPerformerGraph()

# Execute a workflow
result = graph.execute_workflow(
    user_request="Run structural analysis on steel beam"
)

# Check results
print(f"Status: {result['status']}")
print(f"Iterations: {result['iterations']}")
```

### With Custom Configuration

```python
# Set maximum refinement iterations
result = graph.execute_workflow(
    user_request="Run CFD with automatic refinement",
    max_iterations=5
)
```

## Agent Types

| Agent | Role | Specialization |
|-------|------|---------------|
| **Conductor** | Orchestrator | Task planning, delegation, error handling, result aggregation |
| **FEniCSx Performer** | Executor | Finite Element Method (FEM) simulations |
| **LAMMPS Performer** | Executor | Molecular Dynamics (MD) simulations |
| **OpenFOAM Performer** | Executor | Computational Fluid Dynamics (CFD) |
| **Validator** | Quality Control | Result validation, feedback generation |

## Request Keywords

The Conductor analyzes user requests using keyword matching:

- **FEniCSx**: "structural", "finite element"
- **LAMMPS**: "molecular", "dynamics"
- **OpenFOAM**: "fluid", "cfd"

**Example Requests:**
- "Run structural finite element analysis" → FEniCSx
- "Perform molecular dynamics simulation" → LAMMPS
- "Execute CFD fluid flow analysis" → OpenFOAM
- "Run coupled structural and fluid dynamics" → FEniCSx + OpenFOAM

## Workflow Patterns

### 1. Single-Tool Workflow
```
User Request → Conductor → Performer → Validator → Conductor → Result
```

### 2. Multi-Tool Workflow
```
User Request → Conductor → Performer 1 → Performer 2 → Performer 3 → Validator → Conductor → Result
```

### 3. Error Recovery Workflow
```
User Request → Conductor → Performer → Validator
                  ↑                        ↓
                  └─────── [Error] ────────┘
                        (Refinement Loop)
```

## Result Structure

```python
{
    "status": "WorkflowStatus.COMPLETED",
    "iterations": 0,
    "result": {
        "workflow_id": "plan_20251015_143022",
        "status": "completed",
        "performer_results": {
            "task_1": {
                "performer": "fenicsx_performer",
                "status": "completed",
                "execution_time": 10.5,
                "output": "Simulation completed"
            }
        },
        "validation": {
            "validation_passed": True,
            "feedback": []
        }
    },
    "messages": [...]
}
```

## Common Operations

### Run Tests
```bash
cd src/agent
python3 test_conductor_performer_graph.py
```

### Interactive Demo
```bash
cd src/agent
python3 example_conductor_performer.py
```

### View Graph Structure
```python
graph = ConductorPerformerGraph()
print(graph.get_graph_visualization())
```

## Example Workflows

### Structural Analysis
```python
result = graph.execute_workflow(
    user_request="Run structural analysis on steel component"
)
```

### Multi-Physics Simulation
```python
result = graph.execute_workflow(
    user_request="Perform coupled structural and fluid dynamics analysis"
)
```

### Parameter Sweep
```python
result = graph.execute_workflow(
    user_request="Run molecular dynamics with parameter sweep"
)
```

### With Error Recovery
```python
result = graph.execute_workflow(
    user_request="Run CFD with automatic mesh refinement",
    max_iterations=5  # Allow up to 5 refinement attempts
)
```

## Integration with TaskPipeline

The Conductor-Performer graph integrates seamlessly with the existing TaskPipeline:

```python
from conductor_performer_graph import ConductorPerformerGraph
from task_pipeline import TaskPipeline

# Use custom pipeline
pipeline = TaskPipeline()
graph = ConductorPerformerGraph(task_pipeline=pipeline)

# Execute workflow (uses your custom pipeline)
result = graph.execute_workflow(user_request="Run simulation")
```

## Error Handling

The system automatically handles errors with refinement loops:

1. **Execution Error**: Task fails during execution
2. **Convergence Error**: Solver fails to converge
3. **Validation Error**: Results fail quality checks

**Default Behavior:**
- Attempts refinement up to `max_iterations` (default: 3)
- Each iteration adjusts parameters (mesh, solver settings, etc.)
- Returns failure status if max iterations exceeded

## Status Codes

| Status | Meaning |
|--------|---------|
| `PENDING` | Workflow initialized |
| `PLANNING` | Conductor analyzing request |
| `EXECUTING` | Performers running tasks |
| `VALIDATING` | Validator checking results |
| `COMPLETED` | Workflow successful |
| `FAILED` | Workflow failed after retries |
| `NEEDS_REFINEMENT` | Retry with adjusted parameters |

## File Locations

| File | Location |
|------|----------|
| Main Implementation | `src/agent/conductor_performer_graph.py` |
| Tests | `src/agent/test_conductor_performer_graph.py` |
| Examples | `src/agent/example_conductor_performer.py` |
| Architecture Docs | `CONDUCTOR_PERFORMER_ARCHITECTURE.md` |
| Implementation Summary | `MULTI_AGENT_IMPLEMENTATION_SUMMARY.md` |

## Additional Documentation

- **Full Architecture**: [CONDUCTOR_PERFORMER_ARCHITECTURE.md](CONDUCTOR_PERFORMER_ARCHITECTURE.md)
- **Implementation Details**: [MULTI_AGENT_IMPLEMENTATION_SUMMARY.md](MULTI_AGENT_IMPLEMENTATION_SUMMARY.md)
- **Main README**: [README.md](README.md#multi-agent-system-with-langgraph)

## Troubleshooting

### Import Error
```python
# Ensure you're in the correct directory
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
```

### LangGraph Not Found
```bash
pip install langgraph==0.2.59
```

### Tests Failing
```bash
# Ensure all dependencies installed
pip install -r requirements.txt

# Run tests with verbose output
cd src/agent
python3 test_conductor_performer_graph.py
```

## Performance Tips

1. **Max Iterations**: Set appropriate `max_iterations` based on workflow complexity
2. **Pipeline Reuse**: Reuse `ConductorPerformerGraph` instances for multiple workflows
3. **Monitoring**: Use message logs to track workflow progress
4. **Validation**: Customize validator logic for domain-specific checks

## Next Steps

1. Review the [full architecture documentation](CONDUCTOR_PERFORMER_ARCHITECTURE.md)
2. Run the [interactive examples](src/agent/example_conductor_performer.py)
3. Explore [test cases](src/agent/test_conductor_performer_graph.py) for usage patterns
4. Integrate with your existing workflows using TaskPipeline

---

**Need Help?** See the comprehensive documentation in [CONDUCTOR_PERFORMER_ARCHITECTURE.md](CONDUCTOR_PERFORMER_ARCHITECTURE.md)
