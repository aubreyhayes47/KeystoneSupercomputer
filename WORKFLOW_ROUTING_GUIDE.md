# Workflow Routing Logic and Conditional Edges Guide

## Overview

This guide provides comprehensive documentation for implementing routing logic and conditional edges in LangGraph workflows. It covers decision-making strategies, error handling patterns, and adaptive workflow execution.

---

## Table of Contents

- [Core Concepts](#core-concepts)
- [Routing Strategies](#routing-strategies)
- [Conditional Edge Patterns](#conditional-edge-patterns)
- [Error Handling and Fallback Paths](#error-handling-and-fallback-paths)
- [Workflow Branching Strategies](#workflow-branching-strategies)
- [Advanced Patterns](#advanced-patterns)
- [Code Examples](#code-examples)
- [Best Practices](#best-practices)

---

## Core Concepts

### What is Workflow Routing?

Workflow routing is the process of determining which node should execute next in a LangGraph workflow based on:

- **Agent Outputs**: Results from previous node executions
- **Error States**: Failures, timeouts, or exceptions
- **Workflow Context**: User preferences, priorities, resource constraints
- **Historical Metrics**: Performance data from previous executions

### Routing Decision Components

Every routing decision includes:

1. **Next Node**: The target node to execute
2. **Routing Strategy**: The logic used to make the decision
3. **Reason**: Human-readable explanation
4. **Metadata**: Additional context for debugging and monitoring
5. **Fallback Nodes**: Alternative paths if the primary route fails

---

## Routing Strategies

### 1. Success Path Routing

**When to Use**: Normal workflow progression when nodes complete successfully.

```python
from workflow_routing import WorkflowRouter, WorkflowRoutingState, NodeStatus

router = WorkflowRouter()

state: WorkflowRoutingState = {
    "node_status": {"analyze": NodeStatus.COMPLETED},
    "node_results": {"analyze": {"requirements": "extracted"}},
    "retry_count": 0,
    "max_retries": 3
}

decision = router.route_after_execution(
    state=state,
    current_node="analyze",
    success_node="plan",
    error_node="error_handler"
)

# Result: Routes to "plan" node
print(f"Next: {decision.next_node}")  # "plan"
print(f"Strategy: {decision.strategy}")  # SUCCESS_PATH
```

**Key Features**:
- Straightforward progression through workflow
- Carries forward execution results
- Updates execution metrics for performance tracking

### 2. Error Fallback Routing

**When to Use**: Handle failures, timeouts, or exceptions with graceful degradation.

```python
state_failed: WorkflowRoutingState = {
    "node_status": {"simulation": NodeStatus.FAILED},
    "node_results": {},
    "errors": [{"message": "Solver convergence failed", "code": "E001"}],
    "error_severity": ErrorSeverity.MEDIUM,
    "retry_count": 0
}

decision = router.route_after_execution(
    state=state_failed,
    current_node="simulation",
    success_node="validation",
    error_node="error_handler"
)

# Result: Routes to "error_handler" node
print(f"Next: {decision.next_node}")  # "error_handler"
print(f"Fallbacks: {decision.fallback_nodes}")  # Alternative paths
```

**Error Severity Levels**:
- **LOW**: Minor issues, continue workflow
- **MEDIUM**: Significant issues, attempt recovery
- **HIGH**: Critical issues, engage error handling
- **CRITICAL**: Catastrophic failure, terminate workflow

### 3. Retry with Backoff

**When to Use**: Transient failures that may succeed on retry (network issues, resource contention).

```python
state_transient_error: WorkflowRoutingState = {
    "node_status": {"api_call": NodeStatus.FAILED},
    "errors": [{"message": "Connection timeout"}],
    "retry_count": 1,
    "max_retries": 3,
    "backoff_multiplier": 2.0
}

decision = router.route_after_execution(
    state=state_transient_error,
    current_node="api_call",
    success_node="process_response",
    error_node="error_handler",
    retry_node="api_call"
)

# Result: Retries with exponential backoff
print(f"Next: {decision.next_node}")  # "api_call" (retry)
print(f"Backoff: {decision.metadata['backoff_seconds']} sec")  # 2.0 seconds
```

**Exponential Backoff Formula**:
```
backoff_time = backoff_multiplier ^ retry_count
```

**Example Progression**:
- Attempt 1: 0 seconds (immediate)
- Attempt 2: 2 seconds (2^1)
- Attempt 3: 4 seconds (2^2)
- Attempt 4: 8 seconds (2^3)

### 4. Conditional Branch Routing

**When to Use**: Make routing decisions based on specific output values or conditions.

```python
# Route based on output value
state_with_output: WorkflowRoutingState = {
    "node_status": {"approval": NodeStatus.COMPLETED},
    "node_results": {
        "approval": {
            "status": "approved",
            "confidence": 0.95
        }
    }
}

routing_map = {
    "approved": "execute_workflow",
    "rejected": "notify_user",
    "pending": "request_manual_review"
}

decision = router.route_by_output_value(
    state=state_with_output,
    current_node="approval",
    output_key="status",
    routing_map=routing_map,
    default_node="error_handler"
)

# Result: Routes to "execute_workflow"
print(f"Next: {decision.next_node}")  # "execute_workflow"
```

### 5. Context-Based Routing

**When to Use**: Adapt workflow based on user preferences, priorities, or environmental factors.

```python
state_with_context: WorkflowRoutingState = {
    "node_status": {},
    "node_results": {},
    "workflow_context": {
        "priority": "high",
        "user_tier": "premium"
    }
}

routing_rules = [
    {
        "condition": lambda p: p == "high",
        "node": "gpu_accelerated_path",
        "reason": "High priority requests use GPU acceleration"
    },
    {
        "condition": lambda p: p == "normal",
        "node": "standard_cpu_path",
        "reason": "Standard priority uses CPU processing"
    }
]

decision = router.route_by_context(
    state=state_with_context,
    context_key="priority",
    routing_rules=routing_rules,
    default_node="standard_cpu_path"
)

# Result: Routes to GPU path for high priority
print(f"Next: {decision.next_node}")  # "gpu_accelerated_path"
```

### 6. Resource-Aware Routing

**When to Use**: Choose execution paths based on available computational resources.

```python
state_with_resources: WorkflowRoutingState = {
    "node_status": {},
    "node_results": {},
    "resource_limits": {
        "cpu": 100.0,  # 100% available
        "memory": 16000.0,  # 16GB
        "gpu": 1.0  # 1 GPU
    },
    "current_resource_usage": {
        "cpu": 30.0,  # 30% used
        "memory": 4000.0,  # 4GB used
        "gpu": 0.0  # 0 GPUs used
    }
}

decision = router.route_by_resource_availability(
    state=state_with_resources,
    resource_intensive_node="high_res_simulation",
    lightweight_node="coarse_simulation",
    resource_type="memory",
    threshold=8000.0  # Need 8GB available
)

# Result: Enough memory for high-resolution simulation
print(f"Next: {decision.next_node}")  # "high_res_simulation"
print(f"Available: {decision.metadata['available']} MB")  # 12000.0 MB
```

### 7. Performance-Based Adaptive Routing

**When to Use**: Learn from historical executions to choose the most reliable or fastest path.

```python
from workflow_routing import ExecutionMetrics

state_with_metrics: WorkflowRoutingState = {
    "node_status": {},
    "node_results": {},
    "execution_metrics": {
        "fenicsx_solver": ExecutionMetrics(
            execution_count=10,
            failure_count=1,
            avg_execution_time=45.2,
            success_rate=90.0
        ),
        "lammps_solver": ExecutionMetrics(
            execution_count=10,
            failure_count=0,
            avg_execution_time=38.5,
            success_rate=100.0
        )
    }
}

decision = router.route_by_performance_metrics(
    state=state_with_metrics,
    node_options=["fenicsx_solver", "lammps_solver"],
    metric="success_rate"
)

# Result: Routes to most reliable solver
print(f"Next: {decision.next_node}")  # "lammps_solver" (100% success)
```

### 8. Parallel Branch Routing

**When to Use**: Execute multiple independent tasks simultaneously, then join results.

```python
parallel_decisions = router.route_parallel_split(
    state={},
    parallel_nodes=[
        "structural_analysis",
        "thermal_analysis",
        "modal_analysis"
    ],
    join_node="aggregate_results"
)

# Result: Three parallel execution paths
for decision in parallel_decisions:
    print(f"Parallel Node: {decision.next_node}")
    print(f"Join at: {decision.metadata['join_node']}")
```

**Parallel Execution Pattern**:
```
        start
          |
    ┌─────┼─────┐
    │     │     │
   [A]   [B]   [C]  (parallel execution)
    │     │     │
    └─────┼─────┘
          |
        join
          |
        next
```

---

## Conditional Edge Patterns

### Pattern 1: Binary Decision

**Use Case**: Simple yes/no or success/failure routing.

```python
def binary_router(state: WorkflowRoutingState) -> str:
    """Route to success or error path."""
    validation = state.get("node_results", {}).get("validate", {})
    
    if validation.get("passed", False):
        return "success_path"
    else:
        return "error_path"

# Add to LangGraph
workflow.add_conditional_edges(
    "validate",
    binary_router,
    {
        "success_path": "aggregate",
        "error_path": "error_handler"
    }
)
```

### Pattern 2: Multi-Way Branch

**Use Case**: Route to different nodes based on multiple possible outcomes.

```python
def multiway_router(state: WorkflowRoutingState) -> str:
    """Route based on simulation type."""
    analysis = state.get("node_results", {}).get("analyze", {})
    sim_type = analysis.get("simulation_type", "unknown")
    
    type_mapping = {
        "structural": "fenicsx_performer",
        "molecular": "lammps_performer",
        "fluid": "openfoam_performer",
        "multiphysics": "coupled_solver"
    }
    
    return type_mapping.get(sim_type, "error_handler")

# Add to LangGraph
workflow.add_conditional_edges(
    "analyze",
    multiway_router,
    {
        "fenicsx_performer": "fenicsx_performer",
        "lammps_performer": "lammps_performer",
        "openfoam_performer": "openfoam_performer",
        "coupled_solver": "coupled_solver",
        "error_handler": "error_handler"
    }
)
```

### Pattern 3: Validation with Retry

**Use Case**: Validate results and retry with refinement if validation fails.

```python
def validation_retry_router(state: WorkflowRoutingState) -> str:
    """Route with retry logic after validation."""
    validation = state.get("node_results", {}).get("validate", {})
    retry_count = state.get("retry_count", 0)
    max_retries = state.get("max_retries", 3)
    
    if validation.get("passed", False):
        return "aggregate"
    elif retry_count < max_retries:
        return "refine"  # Retry with refinement
    else:
        return "error"  # Max retries exceeded

# Add to LangGraph
workflow.add_conditional_edges(
    "validate",
    validation_retry_router,
    {
        "aggregate": "aggregate",
        "refine": "plan",  # Loop back to planning
        "error": "error_handler"
    }
)
```

### Pattern 4: Circuit Breaker

**Use Case**: Prevent cascading failures by blocking consistently failing paths.

```python
def circuit_breaker_router(state: WorkflowRoutingState) -> str:
    """Route with circuit breaker protection."""
    circuit_open = state.get("circuit_breaker_open", False)
    
    if circuit_open:
        # Circuit is open, use fallback path
        return "fallback_path"
    else:
        # Circuit is closed, use normal path
        node_status = state.get("node_status", {}).get("simulation")
        
        if node_status == NodeStatus.COMPLETED:
            return "validation"
        else:
            return "error_handler"

# Add to LangGraph with circuit breaker state management
workflow.add_conditional_edges(
    "simulation",
    circuit_breaker_router,
    {
        "validation": "validate",
        "fallback_path": "simple_simulation",
        "error_handler": "error_handler"
    }
)
```

---

## Error Handling and Fallback Paths

### Graceful Degradation Strategy

```python
def graceful_degradation_router(state: WorkflowRoutingState) -> str:
    """
    Implement graceful degradation with multiple fallback levels.
    
    Fallback hierarchy:
    1. Retry with same parameters
    2. Retry with relaxed parameters
    3. Use simplified model
    4. Return partial results
    5. Fail gracefully
    """
    errors = state.get("errors", [])
    retry_count = state.get("retry_count", 0)
    
    if not errors:
        return "validation"
    
    # Level 1: Simple retry (transient errors)
    if retry_count == 0:
        return "retry_same"
    
    # Level 2: Retry with relaxed parameters
    elif retry_count == 1:
        return "retry_relaxed"
    
    # Level 3: Use simplified model
    elif retry_count == 2:
        return "simplified_model"
    
    # Level 4: Return partial results
    elif retry_count == 3:
        return "partial_results"
    
    # Level 5: Fail gracefully
    else:
        return "graceful_failure"

workflow.add_conditional_edges(
    "simulation",
    graceful_degradation_router,
    {
        "validation": "validate",
        "retry_same": "simulation",
        "retry_relaxed": "simulation_relaxed",
        "simplified_model": "simple_simulation",
        "partial_results": "collect_partial",
        "graceful_failure": "error_handler"
    }
)
```

### Error Classification and Routing

```python
from enum import Enum

class ErrorCategory(str, Enum):
    TRANSIENT = "transient"  # Temporary, retry likely to succeed
    CONFIGURATION = "configuration"  # Parameter or setup issues
    RESOURCE = "resource"  # Insufficient resources
    CONVERGENCE = "convergence"  # Numerical convergence failure
    FATAL = "fatal"  # Unrecoverable error

def classify_error(error_msg: str) -> ErrorCategory:
    """Classify error based on message."""
    if "timeout" in error_msg.lower() or "connection" in error_msg.lower():
        return ErrorCategory.TRANSIENT
    elif "memory" in error_msg.lower() or "resource" in error_msg.lower():
        return ErrorCategory.RESOURCE
    elif "convergence" in error_msg.lower():
        return ErrorCategory.CONVERGENCE
    elif "parameter" in error_msg.lower() or "invalid" in error_msg.lower():
        return ErrorCategory.CONFIGURATION
    else:
        return ErrorCategory.FATAL

def error_category_router(state: WorkflowRoutingState) -> str:
    """Route based on error category."""
    errors = state.get("errors", [])
    
    if not errors:
        return "success"
    
    error_msg = errors[0].get("message", "")
    category = classify_error(error_msg)
    
    routing = {
        ErrorCategory.TRANSIENT: "retry",
        ErrorCategory.CONFIGURATION: "reconfigure",
        ErrorCategory.RESOURCE: "reduce_resources",
        ErrorCategory.CONVERGENCE: "refine_mesh",
        ErrorCategory.FATAL: "fail"
    }
    
    return routing.get(category, "fail")

workflow.add_conditional_edges(
    "simulation",
    error_category_router,
    {
        "success": "validate",
        "retry": "simulation",
        "reconfigure": "plan",
        "reduce_resources": "lightweight_simulation",
        "refine_mesh": "mesh_refinement",
        "fail": "error_handler"
    }
)
```

---

## Workflow Branching Strategies

### Strategy 1: Priority-Based Branching

Route high-priority requests to fast paths, normal requests to standard paths.

```python
def priority_branch_router(state: WorkflowRoutingState) -> str:
    """Branch based on request priority."""
    context = state.get("workflow_context", {})
    priority = context.get("priority", "normal")
    
    priority_routing = {
        "critical": "express_path",      # Fastest, most resources
        "high": "gpu_accelerated_path",  # GPU acceleration
        "normal": "standard_path",       # Standard CPU processing
        "low": "batch_queue"             # Batched, delayed processing
    }
    
    return priority_routing.get(priority, "standard_path")
```

### Strategy 2: Resource-Based Branching

Select execution path based on available computational resources.

```python
def resource_branch_router(state: WorkflowRoutingState) -> str:
    """Branch based on resource availability."""
    limits = state.get("resource_limits", {})
    usage = state.get("current_resource_usage", {})
    
    # Calculate available resources
    available_memory = limits.get("memory", 0) - usage.get("memory", 0)
    gpu_available = limits.get("gpu", 0) - usage.get("gpu", 0)
    
    # Select path based on availability
    if gpu_available > 0:
        return "gpu_path"
    elif available_memory > 8000:  # 8GB threshold
        return "high_memory_path"
    else:
        return "lightweight_path"
```

### Strategy 3: Accuracy vs Speed Trade-off

Let users choose between accuracy and execution speed.

```python
def accuracy_speed_router(state: WorkflowRoutingState) -> str:
    """Balance accuracy and speed based on user preference."""
    preferences = state.get("user_preferences", {})
    mode = preferences.get("mode", "balanced")
    
    mode_routing = {
        "accuracy": "fine_mesh_high_order",    # Highest accuracy, slowest
        "balanced": "medium_mesh_medium_order", # Balanced
        "speed": "coarse_mesh_low_order"       # Fastest, lower accuracy
    }
    
    return mode_routing.get(mode, "balanced")
```

### Strategy 4: Adaptive Branching with Learning

Learn from past executions to choose optimal paths.

```python
def adaptive_branch_router(state: WorkflowRoutingState) -> str:
    """Adaptively select path based on historical performance."""
    metrics = state.get("execution_metrics", {})
    problem_size = state.get("workflow_context", {}).get("problem_size", "medium")
    
    # Get metrics for each path
    fast_path_metrics = metrics.get("fast_path")
    accurate_path_metrics = metrics.get("accurate_path")
    
    # For small problems, use fast path if reliable
    if problem_size == "small":
        if fast_path_metrics and fast_path_metrics.success_rate > 95:
            return "fast_path"
    
    # For large problems, use accurate path
    elif problem_size == "large":
        return "accurate_path"
    
    # Default to balanced path
    return "balanced_path"
```

---

## Advanced Patterns

### Pattern: Dynamic Workflow Composition

Build workflows dynamically based on problem characteristics.

```python
def dynamic_workflow_router(state: WorkflowRoutingState) -> str:
    """Dynamically compose workflow based on problem type."""
    analysis = state.get("node_results", {}).get("analyze", {})
    
    is_multiphysics = analysis.get("multiphysics", False)
    needs_optimization = analysis.get("optimization_required", False)
    needs_validation = analysis.get("validation_required", True)
    
    # Build dynamic routing path
    if is_multiphysics:
        return "coupled_physics_setup"
    elif needs_optimization:
        return "optimization_loop"
    elif needs_validation:
        return "standard_simulation"
    else:
        return "fast_simulation"
```

### Pattern: State Machine Workflow

Implement complex state machines with explicit state transitions.

```python
class WorkflowState(str, Enum):
    INITIALIZING = "initializing"
    RUNNING = "running"
    VALIDATING = "validating"
    REFINING = "refining"
    COMPLETED = "completed"
    FAILED = "failed"

def state_machine_router(state: WorkflowRoutingState) -> str:
    """Route based on workflow state machine."""
    current_state = state.get("workflow_context", {}).get("state", WorkflowState.INITIALIZING)
    
    state_transitions = {
        WorkflowState.INITIALIZING: "setup",
        WorkflowState.RUNNING: "execute",
        WorkflowState.VALIDATING: "validate",
        WorkflowState.REFINING: "refine",
        WorkflowState.COMPLETED: END,
        WorkflowState.FAILED: "error_handler"
    }
    
    return state_transitions.get(current_state, "error_handler")
```

### Pattern: Fan-Out / Fan-In

Execute multiple variations in parallel, then aggregate results.

```python
def fan_out_router(state: WorkflowRoutingState) -> List[str]:
    """Fan out to multiple parallel executions."""
    parameter_sweep = state.get("workflow_context", {}).get("parameter_sweep", [])
    
    # Create parallel execution for each parameter set
    parallel_nodes = [
        f"simulation_{i}" for i in range(len(parameter_sweep))
    ]
    
    return parallel_nodes

def fan_in_router(state: WorkflowRoutingState) -> str:
    """Fan in to aggregate parallel results."""
    parallel_results = state.get("node_results", {})
    
    # Check if all parallel nodes completed
    expected_count = state.get("workflow_context", {}).get("expected_parallel", 0)
    completed_count = len([r for r in parallel_results.values() if r.get("completed")])
    
    if completed_count >= expected_count:
        return "aggregate_parallel"
    else:
        return "wait_for_parallel"
```

---

## Code Examples

### Example 1: Complete Routing Graph

```python
from langgraph.graph import StateGraph, END
from workflow_routing import (
    WorkflowRouter, 
    WorkflowRoutingState, 
    NodeStatus,
    route_by_validation_result
)

def build_comprehensive_routing_graph():
    """Build a graph with comprehensive routing strategies."""
    
    # Initialize router
    router = WorkflowRouter(max_retries=3, circuit_breaker_threshold=5)
    
    # Create graph
    workflow = StateGraph(WorkflowRoutingState)
    
    # Define nodes
    def analyze(state):
        # Analyze requirements
        return {
            **state,
            "node_status": {**state.get("node_status", {}), "analyze": NodeStatus.COMPLETED},
            "node_results": {
                **state.get("node_results", {}),
                "analyze": {"simulation_type": "structural", "tool": "fenicsx"}
            }
        }
    
    def plan(state):
        # Create execution plan
        return {
            **state,
            "node_status": {**state.get("node_status", {}), "plan": NodeStatus.COMPLETED},
            "node_results": {
                **state.get("node_results", {}),
                "plan": {"mesh_size": 64, "solver": "iterative"}
            }
        }
    
    def simulate(state):
        # Execute simulation
        import random
        success = random.random() > 0.3  # 70% success rate
        
        if success:
            return {
                **state,
                "node_status": {**state.get("node_status", {}), "simulate": NodeStatus.COMPLETED},
                "node_results": {
                    **state.get("node_results", {}),
                    "simulate": {"converged": True, "iterations": 42}
                }
            }
        else:
            return {
                **state,
                "node_status": {**state.get("node_status", {}), "simulate": NodeStatus.FAILED},
                "errors": [{"message": "Convergence failure", "code": "E001"}],
                "retry_count": state.get("retry_count", 0)
            }
    
    def validate(state):
        # Validate results
        results = state.get("node_results", {}).get("simulate", {})
        converged = results.get("converged", False)
        
        return {
            **state,
            "node_status": {**state.get("node_status", {}), "validate": NodeStatus.COMPLETED},
            "node_results": {
                **state.get("node_results", {}),
                "validate": {"validation_passed": converged}
            }
        }
    
    def aggregate(state):
        return {
            **state,
            "node_status": {**state.get("node_status", {}), "aggregate": NodeStatus.COMPLETED}
        }
    
    def handle_error(state):
        retry_count = state.get("retry_count", 0)
        
        if retry_count < 3:
            return {
                **state,
                "retry_count": retry_count + 1,
                "node_status": {}  # Reset for retry
            }
        else:
            return {
                **state,
                "node_status": {**state.get("node_status", {}), "error": NodeStatus.COMPLETED}
            }
    
    # Add nodes to graph
    workflow.add_node("analyze", analyze)
    workflow.add_node("plan", plan)
    workflow.add_node("simulate", simulate)
    workflow.add_node("validate", validate)
    workflow.add_node("aggregate", aggregate)
    workflow.add_node("handle_error", handle_error)
    
    # Set entry point
    workflow.set_entry_point("analyze")
    
    # Add edges
    workflow.add_edge("analyze", "plan")
    
    # Conditional edge after planning (could branch to different simulators)
    workflow.add_edge("plan", "simulate")
    
    # Conditional edge after simulation
    def route_after_simulation(state):
        status = state.get("node_status", {}).get("simulate")
        if status == NodeStatus.COMPLETED:
            return "validate"
        else:
            return "handle_error"
    
    workflow.add_conditional_edges(
        "simulate",
        route_after_simulation,
        {
            "validate": "validate",
            "handle_error": "handle_error"
        }
    )
    
    # Conditional edge after validation
    workflow.add_conditional_edges(
        "validate",
        route_by_validation_result,
        {
            "aggregate": "aggregate",
            "refine": "plan",
            "error": "handle_error"
        }
    )
    
    # Conditional edge after error handling
    def route_after_error(state):
        retry_count = state.get("retry_count", 0)
        if retry_count < 3:
            return "plan"  # Retry from planning
        else:
            return END  # Give up
    
    workflow.add_conditional_edges(
        "handle_error",
        route_after_error,
        {
            "plan": "plan",
            END: END
        }
    )
    
    # Aggregate leads to end
    workflow.add_edge("aggregate", END)
    
    return workflow.compile()

# Use the graph
if __name__ == "__main__":
    graph = build_comprehensive_routing_graph()
    
    initial_state: WorkflowRoutingState = {
        "node_status": {},
        "node_results": {},
        "retry_count": 0,
        "max_retries": 3
    }
    
    result = graph.invoke(initial_state)
    print("Workflow completed!")
    print(f"Final status: {result.get('node_status')}")
```

### Example 2: Parallel Execution with Join

```python
def build_parallel_execution_graph():
    """Build graph with parallel execution branches."""
    
    workflow = StateGraph(WorkflowRoutingState)
    
    # Define nodes
    def setup(state):
        return {
            **state,
            "node_status": {**state.get("node_status", {}), "setup": NodeStatus.COMPLETED},
            "workflow_context": {"parallel_tasks": ["task_a", "task_b", "task_c"]}
        }
    
    def task_a(state):
        return {
            **state,
            "node_status": {**state.get("node_status", {}), "task_a": NodeStatus.COMPLETED},
            "node_results": {**state.get("node_results", {}), "task_a": {"result": "A"}}
        }
    
    def task_b(state):
        return {
            **state,
            "node_status": {**state.get("node_status", {}), "task_b": NodeStatus.COMPLETED},
            "node_results": {**state.get("node_results", {}), "task_b": {"result": "B"}}
        }
    
    def task_c(state):
        return {
            **state,
            "node_status": {**state.get("node_status", {}), "task_c": NodeStatus.COMPLETED},
            "node_results": {**state.get("node_results", {}), "task_c": {"result": "C"}}
        }
    
    def join(state):
        # Aggregate parallel results
        results = state.get("node_results", {})
        combined = {
            "task_a": results.get("task_a", {}).get("result"),
            "task_b": results.get("task_b", {}).get("result"),
            "task_c": results.get("task_c", {}).get("result")
        }
        
        return {
            **state,
            "node_status": {**state.get("node_status", {}), "join": NodeStatus.COMPLETED},
            "node_results": {**state.get("node_results", {}), "join": combined}
        }
    
    # Add nodes
    workflow.add_node("setup", setup)
    workflow.add_node("task_a", task_a)
    workflow.add_node("task_b", task_b)
    workflow.add_node("task_c", task_c)
    workflow.add_node("join", join)
    
    # Set entry
    workflow.set_entry_point("setup")
    
    # Fan out to parallel tasks
    workflow.add_edge("setup", "task_a")
    workflow.add_edge("setup", "task_b")
    workflow.add_edge("setup", "task_c")
    
    # Fan in to join
    workflow.add_edge("task_a", "join")
    workflow.add_edge("task_b", "join")
    workflow.add_edge("task_c", "join")
    
    # End
    workflow.add_edge("join", END)
    
    return workflow.compile()
```

---

## Best Practices

### 1. Design for Observability

Always include detailed metadata in routing decisions:

```python
decision = RoutingDecision(
    next_node="simulation",
    strategy=RoutingStrategy.RETRY_WITH_BACKOFF,
    reason="Retrying after transient network error",
    metadata={
        "error_code": "E001",
        "retry_count": 2,
        "max_retries": 3,
        "backoff_seconds": 4.0,
        "timestamp": datetime.now().isoformat()
    }
)
```

### 2. Implement Proper Error Boundaries

Use error severity levels to prevent minor issues from cascading:

```python
if error_severity == ErrorSeverity.CRITICAL:
    return END  # Immediate termination
elif error_severity == ErrorSeverity.HIGH:
    return "error_handler"  # Attempt recovery
else:
    # Continue with degraded service
    return "fallback_path"
```

### 3. Use Circuit Breakers for External Services

Prevent repeated failures from overwhelming external resources:

```python
circuit_failures = state.get("circuit_breaker_failures", 0)

if circuit_failures >= 5:
    # Open circuit, use fallback
    return "local_cache_path"
else:
    # Closed circuit, try external service
    return "external_api_path"
```

### 4. Provide Clear Fallback Paths

Always define what happens when primary paths fail:

```python
decision = RoutingDecision(
    next_node="gpu_simulation",
    strategy=RoutingStrategy.ADAPTIVE_SELECTION,
    reason="GPU available for acceleration",
    fallback_nodes=["cpu_simulation", "simplified_model", END]
)
```

### 5. Log Routing Decisions

Maintain history for debugging and optimization:

```python
router = WorkflowRouter()

# Make routing decision
decision = router.route_after_execution(...)

# Router automatically logs decision
history = router.get_routing_history()
```

### 6. Test Edge Cases

Test routing logic with various scenarios:

- All nodes succeed
- All nodes fail
- Mixed success/failure
- Timeout scenarios
- Resource exhaustion
- Circuit breaker activation
- Maximum retry attempts

### 7. Balance Complexity vs Maintainability

Avoid over-complicated routing logic:

```python
# Good: Clear and maintainable
def simple_router(state):
    if state["success"]:
        return "next_node"
    else:
        return "error_node"

# Avoid: Overly complex nested conditions
def complex_router(state):
    if state.get("a", {}).get("b", {}).get("c", {}).get("d"):
        if state.get("x") and not state.get("y"):
            if random.random() > 0.5:
                # ... many more conditions
                pass
```

### 8. Document Routing Strategies

Clearly document why specific routing strategies are used:

```python
def priority_router(state: WorkflowRoutingState) -> str:
    """
    Route based on request priority.
    
    Strategy:
    - Critical: Express lane with maximum resources
    - High: GPU-accelerated processing
    - Normal: Standard CPU processing
    - Low: Batch queue for off-peak processing
    
    This routing ensures SLA compliance for high-priority requests
    while efficiently utilizing resources for lower priorities.
    """
    # Implementation...
```

---

## Summary

This guide covered:

✅ **8 Core Routing Strategies**: Success path, error fallback, retry with backoff, conditional branching, context-based, resource-aware, performance-based, and parallel execution

✅ **4 Conditional Edge Patterns**: Binary decisions, multi-way branches, validation with retry, and circuit breakers

✅ **Error Handling**: Graceful degradation, error classification, and fallback hierarchies

✅ **Branching Strategies**: Priority-based, resource-based, accuracy vs speed, and adaptive learning

✅ **Advanced Patterns**: Dynamic composition, state machines, and fan-out/fan-in

✅ **Best Practices**: Observability, error boundaries, circuit breakers, fallbacks, logging, testing, and documentation

For implementation details, see `src/agent/workflow_routing.py`.

For integration with existing workflows, see `src/agent/conductor_performer_graph.py`.

For examples, run:
```bash
cd src/agent
python3 workflow_routing.py
python3 example_routing_strategies.py
```
