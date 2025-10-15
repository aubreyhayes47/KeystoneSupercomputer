# Conductor-Performer Architecture for Multi-Agent Systems

## Overview

This document describes the **Conductor-Performer pattern** implemented using LangGraph for orchestrating multi-agent simulation workflows in Keystone Supercomputer. This architecture enables scalable, fault-tolerant, and intelligent workflow execution across multiple simulation domains.

---

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Agent Roles and Responsibilities](#agent-roles-and-responsibilities)
- [Workflow Graph Structure](#workflow-graph-structure)
- [Edge Routing Logic](#edge-routing-logic)
- [Example Workflows](#example-workflows)
- [Error Handling and Feedback Loops](#error-handling-and-feedback-loops)
- [Integration with Task Pipeline](#integration-with-task-pipeline)
- [Usage Examples](#usage-examples)

---

## Architecture Overview

### Pattern Description

The **Conductor-Performer pattern** is a hub-and-spoke architecture where:

- **Conductor Agent** acts as the central orchestrator
- **Performer Agents** are specialized workers for specific simulation domains
- **Validator Agent** ensures quality and provides feedback

```
┌─────────────────────────────────────────────────────────────┐
│                     USER REQUEST                             │
│  "Run structural analysis with fluid coupling"              │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
       ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
       ┃   CONDUCTOR AGENT             ┃
       ┃   - Analyzes request          ┃
       ┃   - Creates execution plan    ┃
       ┃   - Delegates to Performers   ┃
       ┃   - Handles errors            ┃
       ┃   - Aggregates results        ┃
       ┗━━━━━━━━━━━┬━━━━━━━━━━━━━━━━━━┛
                   │
         ┌─────────┼─────────┐
         │         │         │
         ▼         ▼         ▼
    ┌────────┐ ┌────────┐ ┌────────┐
    │FEniCSx │ │LAMMPS  │ │OpenFOAM│
    │Performer│ │Performer│ │Performer│
    └───┬────┘ └───┬────┘ └───┬────┘
        │          │          │
        └──────────┼──────────┘
                   │
                   ▼
          ┌────────────────┐
          │ VALIDATOR      │
          │ - Checks results│
          │ - Provides     │
          │   feedback     │
          └────────┬───────┘
                   │
                   ▼
    ┌──────────────────────────┐
    │  FINAL RESULT            │
    │  - Aggregated outputs    │
    │  - Validation status     │
    │  - Execution metrics     │
    └──────────────────────────┘
```

### Key Design Principles

1. **Separation of Concerns**: Conductor handles orchestration; Performers handle execution
2. **Domain Specialization**: Each Performer is expert in one simulation tool
3. **Fault Tolerance**: Error handling and retry logic built into workflow
4. **Feedback Loops**: Validator provides feedback for iterative refinement
5. **Extensibility**: Easy to add new Performer agents for additional tools

---

## Agent Roles and Responsibilities

### 1. Conductor Agent

**Primary Responsibilities:**

- **Request Analysis**: Parse and understand user simulation requests
- **Task Planning**: Create structured execution plans with phases
- **Agent Selection**: Choose appropriate Performers for each task
- **Task Sequencing**: Determine sequential vs parallel execution
- **Error Handling**: Implement retry logic and failure recovery
- **Result Aggregation**: Combine outputs from multiple Performers
- **Feedback Coordination**: Manage refinement loops based on validation

**Key Methods:**

```python
def analyze_request(state) -> state:
    """Analyze user request and create execution plan"""
    
def delegate_tasks(state) -> state:
    """Delegate tasks to appropriate Performers"""
    
def aggregate_results(state) -> state:
    """Collect and combine Performer results"""
    
def handle_error(state) -> state:
    """Handle errors and coordinate retries"""
```

**Decision Making:**

- Identifies simulation type from request keywords
- Determines task dependencies and execution order
- Selects retry strategies based on error types
- Decides when to terminate vs refine workflows

---

### 2. Performer Agents

**Specialized Agents:**

#### FEniCSx Performer
- **Domain**: Finite Element Method (FEM) simulations
- **Use Cases**: Structural analysis, heat transfer, electromagnetics
- **Capabilities**: 
  - Mesh generation and refinement
  - Linear and nonlinear solvers
  - Multi-physics coupling

#### LAMMPS Performer
- **Domain**: Molecular Dynamics (MD) simulations
- **Use Cases**: Material properties, molecular interactions, nanoscale phenomena
- **Capabilities**:
  - Classical molecular dynamics
  - Parallel force calculations
  - Trajectory analysis

#### OpenFOAM Performer
- **Domain**: Computational Fluid Dynamics (CFD)
- **Use Cases**: Fluid flow, turbulence, heat transfer in fluids
- **Capabilities**:
  - Incompressible and compressible flow
  - Multi-phase simulations
  - Complex geometries

**Common Performer Pattern:**

```python
class PerformerAgent:
    def __init__(self, tool_name: str):
        self.tool_name = tool_name
        self.role = self._get_role_for_tool(tool_name)
    
    def execute_task(self, state) -> state:
        """Execute simulation using specialized tool"""
        # 1. Extract task parameters
        # 2. Prepare simulation inputs
        # 3. Execute via task pipeline
        # 4. Collect outputs and metrics
        # 5. Return results in state
```

---

### 3. Validator Agent

**Responsibilities:**

- **Result Verification**: Check that all tasks completed successfully
- **Physical Plausibility**: Verify results make physical sense
- **Convergence Analysis**: Ensure solvers converged properly
- **Quality Metrics**: Calculate and report quality indicators
- **Feedback Generation**: Provide actionable refinement suggestions

**Validation Checks:**

1. **Completion Check**: All delegated tasks finished
2. **Error Check**: No execution errors reported
3. **Convergence Check**: Solver residuals below threshold
4. **Physical Bounds**: Results within expected ranges
5. **Consistency Check**: Multi-physics coupling is consistent

---

## Workflow Graph Structure

### LangGraph Implementation

The workflow is implemented as a **StateGraph** with the following structure:

```python
workflow = StateGraph(ConductorPerformerState)

# Nodes (processing steps)
workflow.add_node("analyze", conductor.analyze_request)
workflow.add_node("delegate", conductor.delegate_tasks)
workflow.add_node("fenicsx_execute", fenicsx_performer.execute_task)
workflow.add_node("lammps_execute", lammps_performer.execute_task)
workflow.add_node("openfoam_execute", openfoam_performer.execute_task)
workflow.add_node("validate", validator.validate_results)
workflow.add_node("aggregate", conductor.aggregate_results)
workflow.add_node("handle_error", conductor.handle_error)

# Entry point
workflow.set_entry_point("analyze")
```

### State Schema

```python
class ConductorPerformerState(TypedDict):
    # Conversation and messages
    messages: List[Any]
    
    # Workflow control
    status: WorkflowStatus
    user_request: str
    
    # Execution tracking
    execution_plan: Dict[str, Any]
    delegated_tasks: List[Dict[str, Any]]
    performer_results: Dict[str, Any]
    
    # Quality control
    validation_feedback: Dict[str, Any]
    errors: List[Dict[str, Any]]
    
    # Iteration management
    iteration_count: int
    max_iterations: int
    
    # Output
    final_result: Dict[str, Any]
```

### Visual Representation

```
START
  │
  ├─→ analyze (Conductor)
  │     │
  │     ├─→ delegate (Conductor)
  │           │
  │           ├─→ fenicsx_execute (FEniCSx Performer)
  │           │     │
  │           │     ├─→ lammps_execute (LAMMPS Performer)
  │           │           │
  │           │           ├─→ openfoam_execute (OpenFOAM Performer)
  │           │                 │
  │           │                 ├─→ validate (Validator)
  │           │                       │
  │           │                       ├─→ [DECISION]
  │           │                           ├─→ aggregate (Success) → END
  │           │                           └─→ handle_error
  │           │                                 │
  │           │                                 ├─→ [DECISION]
  │           │                                     ├─→ delegate (Retry)
  │           │                                     └─→ END (Failed)
  │           │
  │           └─→ (loops back to delegate on retry)
  │
  └─→ END
```

---

## Edge Routing Logic

### 1. Sequential Execution Edges

**Purpose**: Ensure tasks execute in correct order when dependencies exist

```python
# Linear progression through main workflow
workflow.add_edge("analyze", "delegate")
workflow.add_edge("delegate", "fenicsx_execute")
workflow.add_edge("fenicsx_execute", "lammps_execute")
workflow.add_edge("lammps_execute", "openfoam_execute")
workflow.add_edge("openfoam_execute", "validate")
```

**Use Cases**:
- Sequential multi-physics simulations
- Results from one stage feed into next
- Ordered task execution

---

### 2. Conditional Edges (Decision Points)

#### Post-Validation Routing

**Logic**: After validation, decide success or error path

```python
def should_continue_after_validation(state) -> str:
    validation = state.get("validation_feedback", {})
    errors = state.get("errors", [])
    
    if errors:
        return "handle_error"
    elif validation.get("validation_passed", False):
        return "aggregate"
    else:
        return "handle_error"

workflow.add_conditional_edges(
    "validate",
    should_continue_after_validation,
    {
        "aggregate": "aggregate",
        "handle_error": "handle_error"
    }
)
```

**Outcomes**:
- ✅ **Validation Passed** → Proceed to aggregate results
- ❌ **Validation Failed** → Error handling and potential retry
- ⚠️ **Errors Present** → Error handling

---

#### Post-Error-Handling Routing

**Logic**: After error handling, decide retry or terminate

```python
def should_retry_after_error(state) -> str:
    status = state.get("status")
    if status == WorkflowStatus.NEEDS_REFINEMENT:
        return "delegate"  # Retry with refinement
    else:
        return END  # Max iterations, terminate

workflow.add_conditional_edges(
    "handle_error",
    should_retry_after_error,
    {
        "delegate": "delegate",
        END: END
    }
)
```

**Outcomes**:
- 🔄 **Needs Refinement** → Loop back to delegate with updated parameters
- 🛑 **Max Iterations** → Terminate workflow with failure status

---

### 3. Feedback Loop Implementation

The graph implements a **refinement feedback loop**:

```
    validate
        │
        ├─→ [Error detected]
        │     │
        │     ├─→ handle_error
        │           │
        │           ├─→ iteration_count < max_iterations?
        │                 │
        │                 ├─→ YES: delegate (with refinement)
        │                 │        │
        │                 │        └─→ (back to performers)
        │                 │
        │                 └─→ NO: END (failure)
```

**Refinement Strategies**:
- Mesh refinement for convergence issues
- Parameter adjustment for physical plausibility
- Timeout extension for long-running tasks
- Alternative solver selection

---

## Example Workflows

### 1. Single-Tool Structural Analysis

**Scenario**: Run finite element analysis on a steel beam

**Request**: 
```python
"Run structural analysis for steel beam under load with mesh size 64"
```

**Execution Flow**:
1. **Conductor** analyzes → Identifies FEniCSx task
2. **Conductor** delegates → Assigns to FEniCSx Performer
3. **FEniCSx Performer** executes → Runs FEM simulation
4. **Validator** checks → Verifies convergence and results
5. **Conductor** aggregates → Returns final results

**Expected Output**:
```json
{
  "status": "completed",
  "result": {
    "workflow_id": "plan_20250115_143022",
    "performer_results": {
      "task_1": {
        "performer": "fenicsx_performer",
        "status": "completed",
        "execution_time": 10.5,
        "output": "Simulation completed using fenicsx"
      }
    },
    "validation": {
      "validation_passed": true,
      "feedback": []
    }
  },
  "iterations": 0
}
```

---

### 2. Multi-Physics Coupled Simulation

**Scenario**: Structural analysis followed by fluid dynamics on results

**Request**:
```python
"Perform coupled structural and fluid dynamics analysis"
```

**Execution Flow**:
1. **Conductor** analyzes → Identifies FEniCSx + OpenFOAM sequential workflow
2. **Conductor** creates plan → Phase 1: FEniCSx, Phase 2: OpenFOAM
3. **FEniCSx Performer** executes → Structural deformation analysis
4. **OpenFOAM Performer** executes → CFD with deformed geometry
5. **Validator** checks → Coupling consistency verification
6. **Conductor** aggregates → Combined multi-physics results

**Workflow Diagram**:
```
User Request
    ↓
Conductor (plan: structural → fluid)
    ↓
FEniCSx Performer (structural)
    ↓ (deformed geometry)
OpenFOAM Performer (fluid on deformed)
    ↓
Validator (check coupling)
    ↓
Conductor (aggregate both results)
```

---

### 3. Parameter Sweep with Parallel Execution

**Scenario**: Molecular dynamics with multiple parameter configurations

**Request**:
```python
"Run molecular dynamics simulation with parameter sweep"
```

**Execution Flow**:
1. **Conductor** analyzes → Identifies parameter sweep pattern
2. **Conductor** creates parallel plan → Multiple LAMMPS tasks
3. **LAMMPS Performer** executes → Parallel parameter configurations
4. **Validator** checks → All runs completed successfully
5. **Conductor** aggregates → Statistical analysis of sweep results

**Implementation Note**: 
Current implementation shows sequential execution structure. For true parallel execution, the graph can be extended to support concurrent Performer execution:

```python
# Future enhancement for parallel execution
workflow.add_parallel_node("parallel_performers", [
    fenicsx_performer.execute_task,
    lammps_performer.execute_task,
    openfoam_performer.execute_task
])
```

---

### 4. Error Recovery and Refinement

**Scenario**: CFD simulation with automatic mesh refinement on convergence issues

**Request**:
```python
"Run CFD simulation with automatic mesh refinement if needed"
```

**Execution Flow (with refinement)**:

**Iteration 1**:
1. **Conductor** delegates → OpenFOAM with initial mesh
2. **OpenFOAM Performer** executes → Detects convergence issue
3. **Validator** checks → Reports convergence failure
4. **Conductor** handles error → Triggers refinement (iteration 1/3)

**Iteration 2**:
5. **Conductor** delegates → OpenFOAM with refined mesh (2x density)
6. **OpenFOAM Performer** executes → Successfully converges
7. **Validator** checks → Validation passes
8. **Conductor** aggregates → Returns successful results

**Refinement Loop**:
```
delegate → execute → validate
    ↓           ↓        ↓
    │           │     [convergence issue]
    │           │        ↓
    │           │    handle_error
    │           │        ↓
    │           │    [needs refinement]
    │           │        ↓
    └───────────┴────────┘
  (loop with refined parameters)
```

---

## Error Handling and Feedback Loops

### Error Categories

1. **Execution Errors**: Task fails to run or crashes
2. **Convergence Errors**: Solver fails to converge
3. **Validation Errors**: Results fail quality checks
4. **Resource Errors**: Timeout or resource exhaustion

### Error Handling Strategy

```python
def handle_error(state) -> state:
    errors = state.get("errors", [])
    iteration_count = state.get("iteration_count", 0)
    max_iterations = state.get("max_iterations", 3)
    
    if iteration_count < max_iterations:
        # Analyze error and determine refinement
        refinement = determine_refinement(errors)
        
        # Update parameters for retry
        state = apply_refinement(state, refinement)
        state["status"] = WorkflowStatus.NEEDS_REFINEMENT
        state["iteration_count"] = iteration_count + 1
    else:
        # Max iterations exceeded
        state["status"] = WorkflowStatus.FAILED
        state["final_result"] = create_failure_result(errors)
    
    return state
```

### Feedback Loop Types

#### 1. Convergence Refinement
- **Trigger**: Solver fails to converge
- **Action**: Refine mesh, adjust solver parameters
- **Max Iterations**: 3

#### 2. Physical Validation Refinement
- **Trigger**: Results outside physical bounds
- **Action**: Adjust boundary conditions, material properties
- **Max Iterations**: 2

#### 3. Quality Improvement
- **Trigger**: Results acceptable but quality metrics low
- **Action**: Increase resolution, refine critical regions
- **Max Iterations**: 2

---

## Integration with Task Pipeline

### Connection to Existing Infrastructure

The Conductor-Performer graph integrates with the existing **TaskPipeline** for actual simulation execution:

```python
class PerformerAgent:
    def __init__(self, tool_name: str, task_pipeline: TaskPipeline):
        self.tool_name = tool_name
        self.task_pipeline = task_pipeline
    
    def execute_task(self, state) -> state:
        # Extract parameters from state
        params = extract_params(state)
        
        # Submit to TaskPipeline (Celery backend)
        task_id = self.task_pipeline.submit_task(
            tool=self.tool_name,
            script=params["script"],
            params=params["params"]
        )
        
        # Wait for completion and collect results
        result = self.task_pipeline.wait_for_task(task_id)
        
        # Update state with results
        state["performer_results"][task_id] = result
        return state
```

### Architecture Layers

```
┌─────────────────────────────────────────┐
│   Conductor-Performer Graph (LangGraph) │  ← Orchestration Layer
│   - Workflow logic                      │
│   - Agent coordination                  │
│   - Error handling                      │
└──────────────┬──────────────────────────┘
               │
               ↓
┌─────────────────────────────────────────┐
│   TaskPipeline (Python API)             │  ← Abstraction Layer
│   - Task submission                     │
│   - Status monitoring                   │
│   - Result collection                   │
└──────────────┬──────────────────────────┘
               │
               ↓
┌─────────────────────────────────────────┐
│   Celery + Redis (Task Queue)          │  ← Execution Layer
│   - Async job processing                │
│   - Distributed workers                 │
│   - Resource management                 │
└──────────────┬──────────────────────────┘
               │
               ↓
┌─────────────────────────────────────────┐
│   Simulation Tools (Containers)         │  ← Compute Layer
│   - FEniCSx, LAMMPS, OpenFOAM          │
│   - Actual simulations                  │
└─────────────────────────────────────────┘
```

---

## Usage Examples

### Basic Usage

```python
from conductor_performer_graph import ConductorPerformerGraph

# Initialize the graph
graph = ConductorPerformerGraph()

# Execute a workflow
result = graph.execute_workflow(
    user_request="Run structural analysis on steel beam"
)

print(f"Status: {result['status']}")
print(f"Iterations: {result['iterations']}")
```

### With Custom Configuration

```python
from conductor_performer_graph import ConductorPerformerGraph
from task_pipeline import TaskPipeline

# Custom task pipeline with monitoring
pipeline = TaskPipeline()

# Initialize graph with custom pipeline
graph = ConductorPerformerGraph(task_pipeline=pipeline)

# Execute with custom max iterations
result = graph.execute_workflow(
    user_request="Run CFD analysis with mesh refinement",
    max_iterations=5
)
```

### Accessing Detailed Results

```python
# Execute workflow
result = graph.execute_workflow(
    user_request="Run multi-physics coupled simulation"
)

# Access detailed information
final_result = result['result']
workflow_id = final_result['workflow_id']
performer_results = final_result['performer_results']
validation_status = final_result['validation']

# Check specific performer outputs
for task_id, task_result in performer_results.items():
    print(f"Task {task_id}:")
    print(f"  Performer: {task_result['performer']}")
    print(f"  Status: {task_result['status']}")
    print(f"  Time: {task_result['execution_time']}s")
```

### Handling Errors

```python
result = graph.execute_workflow(
    user_request="Run simulation with potential convergence issues"
)

if result['status'] == 'failed':
    print("Workflow failed after maximum iterations")
    errors = result['result'].get('errors', [])
    for error in errors:
        print(f"Error in {error['task_id']}: {error['error']}")
else:
    print("Workflow completed successfully")
    print(f"Required {result['iterations']} refinement iterations")
```

### Graph Visualization

```python
# Get textual representation of graph structure
graph = ConductorPerformerGraph()
print(graph.get_graph_visualization())

# Output: ASCII diagram of workflow graph
```

---

## Extending the Architecture

### Adding New Performer Agents

To add support for a new simulation tool:

1. **Create Performer Instance**:
```python
gromacs_performer = PerformerAgent("gromacs", task_pipeline)
```

2. **Add Node to Graph**:
```python
workflow.add_node("gromacs_execute", gromacs_performer.execute_task)
```

3. **Update Edge Routing**:
```python
workflow.add_edge("lammps_execute", "gromacs_execute")
workflow.add_edge("gromacs_execute", "validate")
```

### Custom Validation Logic

Extend the Validator agent with domain-specific checks:

```python
class CustomValidator(ValidatorAgent):
    def validate_results(self, state):
        # Call base validation
        state = super().validate_results(state)
        
        # Add custom checks
        if custom_check_failed(state):
            state["validation_feedback"]["validation_passed"] = False
            state["validation_feedback"]["feedback"].append({
                "issue": "Custom validation failed",
                "suggestion": "Adjust parameters X and Y"
            })
        
        return state
```

---

## Performance Considerations

### Scalability

- **Horizontal Scaling**: Add more Celery workers for parallel Performer execution
- **Vertical Scaling**: Increase resources for individual simulation containers
- **Graph Optimization**: Identify parallel execution opportunities

### Resource Management

- **Memory**: Monitor state size, especially for large result datasets
- **Compute**: Balance worker allocation across Performer types
- **Storage**: Manage intermediate artifacts and final outputs

### Monitoring

Track key metrics:
- Workflow execution time
- Performer task distribution
- Error rates and refinement frequency
- Resource utilization per agent

---

## Conclusion

The Conductor-Performer pattern provides a robust, scalable architecture for multi-agent simulation orchestration. Key benefits:

✅ **Clear Separation of Concerns**: Orchestration vs execution
✅ **Domain Specialization**: Expert agents for each tool
✅ **Fault Tolerance**: Built-in error handling and retry logic
✅ **Extensibility**: Easy to add new agents and workflows
✅ **Observability**: Clear state tracking and message history

This architecture positions Keystone Supercomputer for advanced multi-agent capabilities in Phase 6 and beyond.
