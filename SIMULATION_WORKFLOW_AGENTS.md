# Simulation Workflow Agents

## Overview

This document provides comprehensive specifications for the six specialized agents that manage the complete simulation workflow lifecycle in Keystone Supercomputer. These agents extend the existing Conductor-Performer pattern to provide fine-grained control over each stage of simulation execution.

---

## Table of Contents

- [Agent Architecture](#agent-architecture)
- [Agent Specifications](#agent-specifications)
  - [1. Requirement Analysis Agent](#1-requirement-analysis-agent)
  - [2. Planning Agent](#2-planning-agent)
  - [3. Simulation Agent](#3-simulation-agent)
  - [4. Visualization Agent](#4-visualization-agent)
  - [5. Validation Agent](#5-validation-agent)
  - [6. Summarization Agent](#6-summarization-agent)
- [Agent Lifecycle](#agent-lifecycle)
- [Communication Protocols](#communication-protocols)
- [Integration with LangGraph](#integration-with-langgraph)
- [Example Workflows](#example-workflows)
- [Extension Guide](#extension-guide)

---

## Agent Architecture

### Design Philosophy

The simulation workflow agents follow these principles:

1. **Single Responsibility**: Each agent handles one specific stage of the workflow
2. **Standardized I/O**: All agents use `AgentInput` and `AgentOutput` for communication
3. **Stateless Operation**: Agents are stateless; state is managed by LangGraph
4. **Composable**: Agents can be chained in different configurations
5. **Observable**: All agent actions are logged and traceable

### Workflow Stages

```
User Request
     ↓
[1. Requirement Analysis] ─→ Extract & validate requirements
     ↓
[2. Planning] ─────────────→ Create execution plan
     ↓
[3. Simulation] ───────────→ Execute simulations
     ↓
[4. Visualization] ────────→ Generate visualizations
     ↓
[5. Validation] ───────────→ Validate results
     ↓
[6. Summarization] ────────→ Generate reports
     ↓
Final Report
```

### Data Flow

Each agent receives:
- **Primary Input**: Output from previous stage
- **Context**: Additional information (resources, constraints, preferences)
- **Metadata**: Workflow ID, timestamps, provenance

Each agent produces:
- **Output Data**: Stage-specific results
- **Metadata**: Execution details, timing, resource usage
- **Status**: Success/failure indicators
- **Errors/Warnings**: Issues encountered

---

## Agent Specifications

### 1. Requirement Analysis Agent

**Class**: `RequirementAnalysisAgent`

**Purpose**: Analyze and validate simulation requirements from user requests.

#### Responsibilities

- Parse user requests (natural language or structured)
- Extract simulation parameters and constraints
- Identify required simulation tools
- Validate parameter ranges and physical constraints
- Define success criteria for validation
- Estimate computational resource needs
- Detect missing or ambiguous requirements

#### Inputs

| Field | Type | Description | Required |
|-------|------|-------------|----------|
| `user_request` | `str` | Natural language description of simulation needs | Yes |
| `context.domain` | `str` | Simulation domain (structural, fluid, molecular) | No |
| `context.constraints` | `dict` | Physical or computational constraints | No |
| `context.preferences` | `dict` | User preferences (accuracy, speed, cost) | No |

#### Outputs

| Field | Type | Description |
|-------|------|-------------|
| `simulation_type` | `str` | Type of simulation (structural, fluid, molecular, multiphysics) |
| `parameters` | `dict` | Validated simulation parameters |
| `required_tools` | `list[str]` | Required simulation tools (fenicsx, lammps, openfoam) |
| `success_criteria` | `dict` | Metrics for validation (convergence, accuracy) |
| `constraints` | `dict` | Physical and computational constraints |
| `resource_estimate` | `dict` | Estimated CPU, memory, time requirements |
| `warnings` | `list[str]` | Missing or ambiguous requirements |

#### Example Usage

```python
from simulation_workflow_agents import RequirementAnalysisAgent, AgentInput, WorkflowStage

agent = RequirementAnalysisAgent()

input_data = AgentInput(
    stage=WorkflowStage.REQUIREMENT_ANALYSIS,
    data={
        "user_request": "Run finite element analysis on a steel beam under 10kN load"
    },
    context={
        "constraints": {"max_time_minutes": 30}
    }
)

output = agent.process(input_data)

print(f"Simulation Type: {output.data['simulation_type']}")
print(f"Required Tools: {output.data['required_tools']}")
print(f"Estimated Time: {output.data['resource_estimate']['time_minutes']} min")
```

#### Success Criteria Detection

The agent automatically defines success criteria based on simulation type:

| Simulation Type | Success Criteria |
|-----------------|------------------|
| Structural | Convergence tolerance, displacement limits, stress limits |
| Fluid | Residual convergence, mass conservation, energy balance |
| Molecular | Energy drift, temperature/pressure stability, equilibration |
| Multiphysics | Individual criteria + coupling convergence |

---

### 2. Planning Agent

**Class**: `PlanningAgent`

**Purpose**: Create detailed execution plans for simulation workflows.

#### Responsibilities

- Create task execution plans from requirements
- Determine task dependencies and sequencing
- Plan resource allocation (CPU, memory, GPU)
- Identify parallelization opportunities
- Generate workflow schedules with time estimates
- Plan checkpointing and intermediate saves
- Optimize for user preferences (speed vs accuracy)

#### Inputs

| Field | Type | Description | Required |
|-------|------|-------------|----------|
| `previous_stage_output` | `dict` | Requirements from RequirementAnalysisAgent | Yes |
| `context.available_resources` | `dict` | System resources (CPUs, memory, GPUs) | No |
| `context.constraints` | `dict` | Time/cost/resource constraints | No |

#### Outputs

| Field | Type | Description |
|-------|------|-------------|
| `execution_plan` | `dict` | Detailed task execution plan |
| `task_graph` | `dict` | Task dependency graph |
| `resource_allocation` | `dict` | CPU/memory/GPU per task |
| `schedule` | `dict` | Timeline with estimates |
| `parallelization` | `dict` | Parallel execution strategy |
| `checkpoints` | `list[dict]` | Checkpointing strategy |

#### Execution Plan Structure

```json
{
  "plan_id": "plan_20241015_001",
  "created_at": "2024-10-15T22:00:00Z",
  "tasks": [
    {
      "task_id": "task_1",
      "tool": "fenicsx",
      "task_type": "mesh_generation",
      "depends_on": [],
      "priority": 1,
      "resources": {
        "cpu_cores": 2,
        "memory_gb": 4,
        "estimated_time_minutes": 5
      }
    },
    {
      "task_id": "task_2",
      "tool": "fenicsx",
      "task_type": "solve_system",
      "depends_on": ["task_1"],
      "priority": 1,
      "resources": {
        "cpu_cores": 8,
        "memory_gb": 16,
        "estimated_time_minutes": 20
      }
    }
  ]
}
```

#### Scheduling Strategies

1. **Sequential**: Tasks executed one after another
2. **Parallel**: Independent tasks run simultaneously
3. **Pipeline**: Overlapping execution with dependencies
4. **Adaptive**: Dynamic scheduling based on resource availability

---

### 3. Simulation Agent

**Class**: `SimulationAgent`

**Purpose**: Execute simulations according to the execution plan.

#### Responsibilities

- Execute simulations using TaskPipeline
- Monitor progress and resource usage
- Handle errors and implement retries
- Collect intermediate and final results
- Checkpoint simulation state
- Report progress to orchestrator
- Manage parallel execution

#### Inputs

| Field | Type | Description | Required |
|-------|------|-------------|----------|
| `previous_stage_output.execution_plan` | `dict` | Execution plan from PlanningAgent | Yes |
| `context.task_pipeline` | `TaskPipeline` | TaskPipeline instance for execution | No |

#### Outputs

| Field | Type | Description |
|-------|------|-------------|
| `results` | `dict` | Results per task |
| `metrics` | `dict` | Performance metrics (time, memory) |
| `artifacts` | `list[str]` | Output file paths |
| `execution_summary` | `dict` | Overall execution statistics |
| `checkpoints` | `list[dict]` | Checkpoint information |

#### Integration with TaskPipeline

```python
from simulation_workflow_agents import SimulationAgent, AgentInput
from task_pipeline import TaskPipeline

# Initialize with TaskPipeline
pipeline = TaskPipeline()
agent = SimulationAgent(task_pipeline=pipeline)

# Process execution
input_data = AgentInput(
    stage=WorkflowStage.SIMULATION,
    previous_stage_output=planning_output.data,
    context={"monitor_progress": True}
)

output = agent.process(input_data)

print(f"Tasks: {output.data['execution_summary']['total_tasks']}")
print(f"Success: {output.data['execution_summary']['successful']}")
print(f"Time: {output.data['metrics']['total_time_seconds']}s")
```

#### Error Handling

The Simulation Agent implements robust error handling:

1. **Retry Logic**: Automatic retry with exponential backoff
2. **Checkpointing**: Resume from last successful checkpoint
3. **Partial Success**: Continue with successful tasks if some fail
4. **Error Propagation**: Detailed error information for debugging

---

### 4. Visualization Agent

**Class**: `VisualizationAgent`

**Purpose**: Generate visualizations from simulation results.

#### Responsibilities

- Generate standard visualizations (contour plots, vector fields)
- Create custom visualizations based on result type
- Produce animations for time-dependent simulations
- Generate comparison plots for parameter sweeps
- Create interactive visualizations
- Export in multiple formats (PNG, PDF, interactive)
- Annotate plots with key metrics

#### Inputs

| Field | Type | Description | Required |
|-------|------|-------------|----------|
| `previous_stage_output.results` | `dict` | Simulation results | Yes |
| `context.visualization_config` | `dict` | Visualization preferences | No |
| `context.formats` | `list[str]` | Output formats | No |

#### Outputs

| Field | Type | Description |
|-------|------|-------------|
| `visualizations` | `list[dict]` | Generated visualization files |
| `thumbnails` | `list[str]` | Preview images |
| `interactive_views` | `list[dict]` | Interactive visualization descriptors |
| `summary_plot` | `str` | Combined summary visualization |

#### Visualization Types by Simulation

| Simulation Type | Visualization Types |
|-----------------|---------------------|
| Structural | Displacement contour, stress contour, deformation animation |
| Fluid | Velocity field, pressure contour, streamlines, vorticity |
| Molecular | Trajectory animation, RDF plots, energy time series |
| Multiphysics | Combined field plots, interface visualization |

#### Example Output

```python
{
  "visualizations": [
    {
      "type": "contour",
      "field": "displacement",
      "file": "/data/viz/displacement_contour.png",
      "format": "png",
      "resolution": [1920, 1080],
      "colormap": "viridis",
      "annotations": {
        "max_value": 12.5,
        "min_value": 0.0,
        "units": "mm"
      }
    },
    {
      "type": "animation",
      "field": "time_evolution",
      "file": "/data/viz/evolution.mp4",
      "format": "mp4",
      "frames": 100,
      "fps": 30
    }
  ],
  "summary_plot": "/data/viz/summary.png"
}
```

---

### 5. Validation Agent

**Class**: `ValidationAgent`

**Purpose**: Validate simulation results against expected outcomes.

#### Responsibilities

- Validate against success criteria
- Check physical plausibility (conservation laws, bounds)
- Compare with reference solutions
- Assess numerical quality (convergence, stability)
- Identify anomalies or unexpected behavior
- Generate validation report
- Provide feedback for refinement

#### Inputs

| Field | Type | Description | Required |
|-------|------|-------------|----------|
| `previous_stage_output.results` | `dict` | Simulation results | Yes |
| `context.requirements` | `dict` | Original requirements with success criteria | Yes |
| `context.reference_data` | `dict` | Optional reference solutions | No |

#### Outputs

| Field | Type | Description |
|-------|------|-------------|
| `validation_status` | `str` | Overall status (pass/fail/warning) |
| `validation_report` | `dict` | Detailed validation results |
| `quality_metrics` | `dict` | Numerical quality indicators |
| `issues` | `list[str]` | Identified problems |
| `recommendations` | `list[str]` | Improvement suggestions |

#### Validation Checks

##### 1. Convergence Validation

```python
{
  "check": "convergence",
  "status": "pass",
  "residual": 1.2e-7,
  "threshold": 1e-6,
  "iterations": 45,
  "max_iterations": 1000
}
```

##### 2. Physical Constraints

```python
{
  "check": "stress_limits",
  "status": "pass",
  "max_stress_mpa": 185,
  "yield_strength_mpa": 250,
  "safety_factor": 1.35
}
```

##### 3. Conservation Laws

```python
{
  "check": "mass_conservation",
  "status": "warning",
  "error_percent": 0.02,
  "threshold_percent": 0.01,
  "message": "Minor mass conservation error"
}
```

#### Validation Report Structure

```json
{
  "validation_status": "pass",
  "timestamp": "2024-10-15T22:30:00Z",
  "checks": {
    "convergence": {"status": "pass", ...},
    "displacement_bounds": {"status": "pass", ...},
    "stress_limits": {"status": "pass", ...}
  },
  "quality_score": 0.95,
  "issues": [],
  "recommendations": []
}
```

---

### 6. Summarization Agent

**Class**: `SummarizationAgent`

**Purpose**: Summarize workflow results and generate comprehensive reports.

#### Responsibilities

- Summarize key findings from all stages
- Generate comprehensive reports (text, markdown, PDF)
- Create executive summaries
- Highlight important results and insights
- Document workflow execution details
- Provide actionable recommendations
- Archive workflow artifacts

#### Inputs

| Field | Type | Description | Required |
|-------|------|-------------|----------|
| `data` | `dict` | All workflow stage outputs | Yes |
| `context.report_format` | `str` | Desired format (markdown/pdf/json) | No |

#### Outputs

| Field | Type | Description |
|-------|------|-------------|
| `executive_summary` | `dict` | High-level findings |
| `detailed_report` | `dict` | Full technical documentation |
| `recommendations` | `list[str]` | Next steps and improvements |
| `artifacts_manifest` | `dict` | List of all generated files |
| `workflow_complete` | `bool` | Completion status |

#### Executive Summary Structure

```json
{
  "title": "Structural Analysis: Steel Beam Under Load",
  "status": "Success",
  "simulation_type": "structural",
  "key_findings": [
    "Maximum displacement: 12.5 mm (within 50 mm limit)",
    "Maximum stress: 185 MPa (safety factor: 1.35)",
    "Convergence achieved in 45 iterations"
  ],
  "performance": {
    "total_time_minutes": 18,
    "resource_usage": "4 cores, 8GB memory",
    "cost_estimate": "$0.12"
  },
  "recommendations": [
    "Current design meets safety requirements",
    "Consider optimization to reduce weight by 15%"
  ]
}
```

#### Report Formats

1. **Markdown**: Human-readable format for documentation
2. **JSON**: Machine-readable for integration
3. **PDF**: Professional reports for stakeholders
4. **HTML**: Interactive web reports

---

## Agent Lifecycle

### Initialization Phase

```python
# Create agents
req_agent = RequirementAnalysisAgent()
plan_agent = PlanningAgent()
sim_agent = SimulationAgent(task_pipeline=TaskPipeline())
viz_agent = VisualizationAgent()
val_agent = ValidationAgent()
sum_agent = SummarizationAgent()
```

### Execution Phase

```
1. RequirementAnalysisAgent.process(user_request)
   ↓
2. PlanningAgent.process(requirements)
   ↓
3. SimulationAgent.process(execution_plan)
   ↓
4. VisualizationAgent.process(simulation_results)
   ↓
5. ValidationAgent.process(results + requirements)
   ↓
6. SummarizationAgent.process(all_stage_outputs)
```

### State Management

Each agent:
- Receives state from previous agent via `previous_stage_output`
- Updates state with its own output
- Passes updated state to next agent
- Does not maintain internal state between calls

### Error Handling

Each stage can:
- Return `AgentStatus.FAILED` to halt workflow
- Return warnings without stopping execution
- Trigger refinement loops through validation
- Provide detailed error messages

---

## Communication Protocols

### Input/Output Standardization

All agents use standardized `AgentInput` and `AgentOutput` classes:

```python
@dataclass
class AgentInput:
    stage: WorkflowStage
    data: Dict[str, Any]
    context: Dict[str, Any] = field(default_factory=dict)
    previous_stage_output: Optional[Dict[str, Any]] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

@dataclass
class AgentOutput:
    stage: WorkflowStage
    status: AgentStatus
    data: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
```

### Message Passing

Agents communicate through LangGraph state:

```python
state["requirement_analysis"] = req_output.to_dict()
state["planning"] = plan_output.to_dict()
state["simulation"] = sim_output.to_dict()
# ... etc
```

### Context Propagation

Context flows through the workflow:

```python
context = {
    "workflow_id": "wf_001",
    "user_preferences": {"accuracy": "high"},
    "available_resources": {"cpu_cores": 16},
    "constraints": {"max_time_minutes": 60}
}

# Context is available to all agents
input_data = AgentInput(..., context=context)
```

---

## Integration with LangGraph

### Graph Construction

```python
from langgraph.graph import StateGraph, END
from simulation_workflow_agents import (
    SimulationWorkflowState,
    RequirementAnalysisAgent,
    PlanningAgent,
    SimulationAgent,
    VisualizationAgent,
    ValidationAgent,
    SummarizationAgent
)

# Create workflow graph
workflow = StateGraph(SimulationWorkflowState)

# Initialize agents
req_agent = RequirementAnalysisAgent()
plan_agent = PlanningAgent()
sim_agent = SimulationAgent()
viz_agent = VisualizationAgent()
val_agent = ValidationAgent()
sum_agent = SummarizationAgent()

# Add nodes
workflow.add_node("analyze_requirements", lambda state: req_agent.process(...))
workflow.add_node("create_plan", lambda state: plan_agent.process(...))
workflow.add_node("execute_simulation", lambda state: sim_agent.process(...))
workflow.add_node("generate_visualizations", lambda state: viz_agent.process(...))
workflow.add_node("validate_results", lambda state: val_agent.process(...))
workflow.add_node("summarize_workflow", lambda state: sum_agent.process(...))

# Add edges
workflow.add_edge("analyze_requirements", "create_plan")
workflow.add_edge("create_plan", "execute_simulation")
workflow.add_edge("execute_simulation", "generate_visualizations")
workflow.add_edge("generate_visualizations", "validate_results")
workflow.add_edge("validate_results", "summarize_workflow")
workflow.add_edge("summarize_workflow", END)

# Set entry point
workflow.set_entry_point("analyze_requirements")

# Compile graph
app = workflow.compile()
```

### Conditional Routing

Add validation-based routing:

```python
def should_refine(state) -> str:
    """Route based on validation status."""
    validation = state.get("validation", {})
    status = validation.get("validation_status")
    
    if status == "fail":
        # Go back to planning for refinement
        return "create_plan"
    else:
        # Continue to summarization
        return "summarize_workflow"

workflow.add_conditional_edges(
    "validate_results",
    should_refine,
    {
        "create_plan": "create_plan",
        "summarize_workflow": "summarize_workflow"
    }
)
```

---

## Example Workflows

### Example 1: Simple Structural Analysis

```python
from simulation_workflow_agents import (
    RequirementAnalysisAgent,
    PlanningAgent,
    SimulationAgent,
    VisualizationAgent,
    ValidationAgent,
    SummarizationAgent,
    AgentInput,
    WorkflowStage
)

# 1. Requirement Analysis
req_agent = RequirementAnalysisAgent()
req_input = AgentInput(
    stage=WorkflowStage.REQUIREMENT_ANALYSIS,
    data={"user_request": "Run FEA on steel beam under 10kN load"}
)
req_output = req_agent.process(req_input)
print(f"✓ Requirements: {req_output.data['simulation_type']}")

# 2. Planning
plan_agent = PlanningAgent()
plan_input = AgentInput(
    stage=WorkflowStage.PLANNING,
    data={},
    previous_stage_output=req_output.data
)
plan_output = plan_agent.process(plan_input)
print(f"✓ Plan: {len(plan_output.data['execution_plan']['tasks'])} tasks")

# 3. Simulation
sim_agent = SimulationAgent()
sim_input = AgentInput(
    stage=WorkflowStage.SIMULATION,
    data={},
    previous_stage_output=plan_output.data
)
sim_output = sim_agent.process(sim_input)
print(f"✓ Simulation: {sim_output.data['execution_summary']['successful']} tasks completed")

# 4. Visualization
viz_agent = VisualizationAgent()
viz_input = AgentInput(
    stage=WorkflowStage.VISUALIZATION,
    data={},
    previous_stage_output=sim_output.data
)
viz_output = viz_agent.process(viz_input)
print(f"✓ Visualization: {len(viz_output.data['visualizations'])} plots generated")

# 5. Validation
val_agent = ValidationAgent()
val_input = AgentInput(
    stage=WorkflowStage.VALIDATION,
    data={},
    previous_stage_output=sim_output.data,
    context={"requirements": req_output.data}
)
val_output = val_agent.process(val_input)
print(f"✓ Validation: {val_output.data['validation_status']}")

# 6. Summarization
sum_agent = SummarizationAgent()
sum_input = AgentInput(
    stage=WorkflowStage.SUMMARIZATION,
    data={
        "requirement_analysis": req_output,
        "planning": plan_output,
        "simulation": sim_output,
        "visualization": viz_output,
        "validation": val_output
    }
)
sum_output = sum_agent.process(sum_input)
print(f"✓ Summary: {sum_output.data['executive_summary']['title']}")
```

### Example 2: Multi-Physics with Validation Loop

```python
# Initial requirements
user_request = "Couple structural and fluid analysis for wing design"

# Run workflow (will loop if validation fails)
max_iterations = 3
iteration = 0

while iteration < max_iterations:
    iteration += 1
    print(f"\n=== Iteration {iteration} ===")
    
    # Execute workflow stages
    req_output = req_agent.process(req_input)
    plan_output = plan_agent.process(plan_input)
    sim_output = sim_agent.process(sim_input)
    viz_output = viz_agent.process(viz_input)
    val_output = val_agent.process(val_input)
    
    # Check validation
    if val_output.data['validation_status'] == 'pass':
        print("✓ Validation passed!")
        break
    else:
        print(f"⚠ Validation failed: {val_output.errors}")
        print(f"Refinement: {val_output.data['validation_report']['recommendations']}")
        # Update requirements based on recommendations
        # ... refinement logic ...

# Final summary
sum_output = sum_agent.process(sum_input)
print(f"\n✓ Workflow complete in {iteration} iterations")
```

---

## Extension Guide

### Adding a New Agent

1. **Create agent class** inheriting from base pattern:

```python
class CustomAgent:
    def __init__(self):
        self.stage = WorkflowStage.CUSTOM
        self.name = "CustomAgent"
    
    def process(self, agent_input: AgentInput) -> AgentOutput:
        # Agent logic here
        return AgentOutput(
            stage=self.stage,
            status=AgentStatus.COMPLETED,
            data={...}
        )
```

2. **Add to workflow graph**:

```python
workflow.add_node("custom_stage", lambda state: custom_agent.process(...))
workflow.add_edge("previous_stage", "custom_stage")
workflow.add_edge("custom_stage", "next_stage")
```

3. **Update state schema**:

```python
class SimulationWorkflowState(TypedDict):
    # ... existing fields ...
    custom_stage: NotRequired[Dict[str, Any]]
```

### Customizing Existing Agents

Override specific methods:

```python
class CustomRequirementAnalysisAgent(RequirementAnalysisAgent):
    def _analyze_request(self, request: str, context: Dict) -> Dict[str, Any]:
        # Custom analysis logic using LLM
        llm_response = self.llm.invoke(request)
        return self._parse_llm_response(llm_response)
```

### Adding Validation Rules

Extend ValidationAgent:

```python
class CustomValidationAgent(ValidationAgent):
    def _validate_results(self, results: Dict, criteria: Dict) -> Dict[str, Any]:
        report = super()._validate_results(results, criteria)
        
        # Add custom checks
        report["checks"]["custom_check"] = self._custom_validation(results)
        
        return report
    
    def _custom_validation(self, results: Dict) -> Dict[str, Any]:
        # Custom validation logic
        return {"status": "pass", ...}
```

---

## Best Practices

### 1. Error Handling

Always include comprehensive error information:

```python
try:
    result = self._process_data(input_data)
except Exception as e:
    return AgentOutput(
        stage=self.stage,
        status=AgentStatus.FAILED,
        data={},
        errors=[f"Processing failed: {str(e)}"],
        metadata={"exception_type": type(e).__name__}
    )
```

### 2. Logging

Log all agent actions:

```python
import logging

logger = logging.getLogger(__name__)

def process(self, agent_input: AgentInput) -> AgentOutput:
    logger.info(f"{self.name}: Starting {self.stage.value}")
    # ... processing ...
    logger.info(f"{self.name}: Completed in {elapsed}s")
```

### 3. Resource Management

Always cleanup resources:

```python
def process(self, agent_input: AgentInput) -> AgentOutput:
    temp_files = []
    try:
        # Processing
        result = self._execute(...)
        return AgentOutput(...)
    finally:
        # Cleanup
        for f in temp_files:
            if os.path.exists(f):
                os.remove(f)
```

### 4. Testing

Test each agent independently:

```python
def test_requirement_analysis_agent():
    agent = RequirementAnalysisAgent()
    
    input_data = AgentInput(
        stage=WorkflowStage.REQUIREMENT_ANALYSIS,
        data={"user_request": "Test request"}
    )
    
    output = agent.process(input_data)
    
    assert output.status == AgentStatus.COMPLETED
    assert "simulation_type" in output.data
    assert len(output.errors) == 0
```

---

## Performance Considerations

### 1. Parallelization

Agents that can run in parallel:
- Multiple simulations in SimulationAgent
- Multiple visualizations in VisualizationAgent
- Independent validation checks in ValidationAgent

### 2. Caching

Cache expensive operations:
- Requirement analysis results
- Execution plan templates
- Visualization configurations

### 3. Incremental Processing

Support incremental workflows:
- Save checkpoints after each stage
- Resume from last successful stage
- Skip unchanged stages on refinement

---

## Troubleshooting

### Common Issues

**Issue**: Agent fails with "missing previous_stage_output"
**Solution**: Ensure previous agent completed successfully and state was updated

**Issue**: Validation always fails
**Solution**: Check success criteria are realistic and properly defined

**Issue**: High memory usage in SimulationAgent
**Solution**: Implement streaming results, increase checkpointing frequency

**Issue**: Visualizations not generated
**Solution**: Check result file paths exist and are accessible

---

## References

- [Conductor-Performer Architecture](CONDUCTOR_PERFORMER_ARCHITECTURE.md)
- [Task Pipeline Documentation](TASK_PIPELINE.md)
- [LangGraph Documentation](https://github.com/langchain-ai/langgraph)
- [Multi-Agent Implementation Summary](MULTI_AGENT_IMPLEMENTATION_SUMMARY.md)

---

## Conclusion

The Simulation Workflow Agents provide a comprehensive, extensible framework for managing complex simulation workflows. Each agent has clearly defined responsibilities, standardized communication protocols, and seamless integration with LangGraph. This architecture enables:

- **Modularity**: Easy to add, modify, or replace agents
- **Observability**: Complete tracing of workflow execution
- **Reliability**: Robust error handling and validation
- **Scalability**: Support for parallel and distributed execution
- **Reproducibility**: Comprehensive logging and artifact management

For implementation details, see `src/agent/simulation_workflow_agents.py`.
