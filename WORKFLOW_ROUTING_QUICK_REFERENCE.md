# Workflow Routing Quick Reference

## Quick Start

```python
from workflow_routing import WorkflowRouter, WorkflowRoutingState, NodeStatus

# Initialize router
router = WorkflowRouter(max_retries=3)

# Make routing decision
state: WorkflowRoutingState = {
    "node_status": {"simulation": NodeStatus.COMPLETED},
    "node_results": {"simulation": {"output": "success"}},
    "retry_count": 0
}

decision = router.route_after_execution(
    state=state,
    current_node="simulation",
    success_node="validation",
    error_node="error_handler"
)

print(f"Route to: {decision.next_node}")
```

---

## Routing Strategies Cheat Sheet

### 1. Success Path (Normal Flow)
```python
# When: Node completes successfully
# Route: Continue to next step
decision = router.route_after_execution(
    state=state,
    current_node="current",
    success_node="next_step",
    error_node="error_handler"
)
```

### 2. Error with Retry
```python
# When: Transient failure (timeout, network)
# Route: Retry with exponential backoff
decision = router.route_after_execution(
    state=state,
    current_node="api_call",
    success_node="process",
    error_node="error_handler",
    retry_node="api_call"  # Enable retry
)
# Backoff: 2^0, 2^1, 2^2... seconds
```

### 3. Route by Output Value
```python
# When: Decision based on node output
# Route: Different paths for different values
routing_map = {
    "approved": "execute",
    "rejected": "notify",
    "pending": "manual_review"
}

decision = router.route_by_output_value(
    state=state,
    current_node="approval",
    output_key="status",
    routing_map=routing_map,
    default_node="error"
)
```

### 4. Route by Context/Priority
```python
# When: Priority-based execution
# Route: Fast path for high priority
routing_rules = [
    {
        "condition": lambda p: p == "high",
        "node": "gpu_path",
        "reason": "High priority"
    },
    {
        "condition": lambda p: p == "normal",
        "node": "cpu_path",
        "reason": "Standard processing"
    }
]

decision = router.route_by_context(
    state=state,
    context_key="priority",
    routing_rules=routing_rules,
    default_node="standard"
)
```

### 5. Resource-Aware Routing
```python
# When: Limited resources
# Route: Based on availability
decision = router.route_by_resource_availability(
    state=state,
    resource_intensive_node="high_res_sim",
    lightweight_node="coarse_sim",
    resource_type="memory",
    threshold=8000.0  # 8GB
)
```

### 6. Performance-Based Adaptive
```python
# When: Multiple options available
# Route: Based on historical success rate
decision = router.route_by_performance_metrics(
    state=state,
    node_options=["solver_a", "solver_b", "solver_c"],
    metric="success_rate"  # or "avg_execution_time"
)
```

### 7. Parallel Execution
```python
# When: Independent tasks
# Route: Execute in parallel, join later
decisions = router.route_parallel_split(
    state=state,
    parallel_nodes=["task_a", "task_b", "task_c"],
    join_node="aggregate"
)
```

### 8. Circuit Breaker
```python
# When: Repeated failures
# Route: Use fallback to prevent cascade
state["circuit_breaker_open"] = True  # Set by router

decision = router.route_after_execution(
    state=state,
    current_node="external_api",
    success_node="process",
    error_node="fallback"
)
# Automatically routes to fallback if circuit open
```

---

## LangGraph Conditional Edge Patterns

### Pattern 1: Simple Binary Decision
```python
def route_function(state: WorkflowRoutingState) -> str:
    if state["success"]:
        return "success_node"
    else:
        return "error_node"

workflow.add_conditional_edges(
    "validate",
    route_function,
    {
        "success_node": "aggregate",
        "error_node": "error_handler"
    }
)
```

### Pattern 2: Multi-Way Branch
```python
def route_by_tool(state: WorkflowRoutingState) -> str:
    tool = state["node_results"]["plan"]["required_tool"]
    
    mapping = {
        "fenicsx": "fenicsx_performer",
        "lammps": "lammps_performer",
        "openfoam": "openfoam_performer"
    }
    
    return mapping.get(tool, "error")

workflow.add_conditional_edges(
    "plan",
    route_by_tool,
    {
        "fenicsx_performer": "fenicsx_performer",
        "lammps_performer": "lammps_performer",
        "openfoam_performer": "openfoam_performer",
        "error": "error_handler"
    }
)
```

### Pattern 3: Validation with Retry Loop
```python
def route_after_validation(state: WorkflowRoutingState) -> str:
    validation = state["node_results"]["validate"]
    retry_count = state.get("retry_count", 0)
    
    if validation["passed"]:
        return "aggregate"
    elif retry_count < 3:
        return "refine"  # Retry
    else:
        return "error"  # Give up

workflow.add_conditional_edges(
    "validate",
    route_after_validation,
    {
        "aggregate": "aggregate",
        "refine": "plan",  # Loop back
        "error": "error_handler"
    }
)
```

---

## Common Use Cases

### Use Case 1: Retry with Backoff
**Scenario**: API call that may timeout

```python
state: WorkflowRoutingState = {
    "node_status": {"api_call": NodeStatus.FAILED},
    "errors": [{"message": "Connection timeout"}],
    "retry_count": 1,
    "max_retries": 3
}

decision = router.route_after_execution(
    state=state,
    current_node="api_call",
    success_node="process",
    error_node="fallback",
    retry_node="api_call"
)

# Result: Retry with 2^1 = 2 second backoff
```

### Use Case 2: Priority Queue
**Scenario**: Fast-track high-priority requests

```python
state: WorkflowRoutingState = {
    "workflow_context": {"priority": "high"}
}

routing_rules = [
    {"condition": lambda p: p == "high", "node": "express"},
    {"condition": lambda p: p == "low", "node": "batch"}
]

decision = router.route_by_context(
    state=state,
    context_key="priority",
    routing_rules=routing_rules,
    default_node="standard"
)

# Result: Routes to "express" for high priority
```

### Use Case 3: Resource Limits
**Scenario**: Choose simulation resolution based on memory

```python
state: WorkflowRoutingState = {
    "resource_limits": {"memory": 16000.0},
    "current_resource_usage": {"memory": 10000.0}
}

decision = router.route_by_resource_availability(
    state=state,
    resource_intensive_node="fine_mesh",
    lightweight_node="coarse_mesh",
    resource_type="memory",
    threshold=8000.0
)

# Result: Routes to "coarse_mesh" (only 6GB available)
```

### Use Case 4: A/B Testing Solvers
**Scenario**: Choose best solver based on history

```python
state: WorkflowRoutingState = {
    "execution_metrics": {
        "iterative": ExecutionMetrics(success_rate=85.0),
        "direct": ExecutionMetrics(success_rate=95.0)
    }
}

decision = router.route_by_performance_metrics(
    state=state,
    node_options=["iterative", "direct"],
    metric="success_rate"
)

# Result: Routes to "direct" (95% > 85%)
```

---

## Error Severity Levels

```python
from workflow_routing import ErrorSeverity

# LOW: Continue workflow with warning
state["error_severity"] = ErrorSeverity.LOW

# MEDIUM: Attempt recovery
state["error_severity"] = ErrorSeverity.MEDIUM

# HIGH: Route to error handler
state["error_severity"] = ErrorSeverity.HIGH

# CRITICAL: Immediate termination
state["error_severity"] = ErrorSeverity.CRITICAL
```

---

## State Schema

```python
WorkflowRoutingState = TypedDict({
    # Required
    "node_status": Dict[str, NodeStatus],
    "node_results": Dict[str, Any],
    
    # Optional - Error tracking
    "errors": List[Dict[str, Any]],
    "error_severity": ErrorSeverity,
    
    # Optional - Retry management
    "retry_count": int,
    "max_retries": int,
    
    # Optional - Circuit breaker
    "circuit_breaker_open": bool,
    "circuit_breaker_failures": int,
    
    # Optional - Context
    "workflow_context": Dict[str, Any],
    
    # Optional - Resources
    "resource_limits": Dict[str, Any],
    "current_resource_usage": Dict[str, Any],
    
    # Optional - Metrics
    "execution_metrics": Dict[str, ExecutionMetrics]
})
```

---

## Integration Example

```python
from langgraph.graph import StateGraph, END
from workflow_routing import (
    WorkflowRouter, 
    route_by_validation_result
)

# Create graph
workflow = StateGraph(WorkflowRoutingState)
router = WorkflowRouter()

# Add nodes
workflow.add_node("analyze", analyze_fn)
workflow.add_node("execute", execute_fn)
workflow.add_node("validate", validate_fn)
workflow.add_node("aggregate", aggregate_fn)
workflow.add_node("error", error_fn)

# Set entry point
workflow.set_entry_point("analyze")

# Add edges
workflow.add_edge("analyze", "execute")
workflow.add_edge("execute", "validate")

# Add conditional edge with routing
workflow.add_conditional_edges(
    "validate",
    route_by_validation_result,  # Use predefined function
    {
        "aggregate": "aggregate",
        "refine": "analyze",  # Loop back
        "error": "error"
    }
)

workflow.add_edge("aggregate", END)
workflow.add_edge("error", END)

# Compile
graph = workflow.compile()
```

---

## Testing Routing Logic

```python
import unittest
from workflow_routing import WorkflowRouter, NodeStatus

class TestMyRouting(unittest.TestCase):
    def setUp(self):
        self.router = WorkflowRouter()
    
    def test_success_routing(self):
        state = {
            "node_status": {"task": NodeStatus.COMPLETED},
            "node_results": {},
            "retry_count": 0
        }
        
        decision = self.router.route_after_execution(
            state=state,
            current_node="task",
            success_node="next",
            error_node="error"
        )
        
        self.assertEqual(decision.next_node, "next")
```

---

## Performance Tips

1. **Use Metrics for Adaptive Routing**
   ```python
   # Track execution metrics
   metrics = ExecutionMetrics()
   metrics.update_success(execution_time)
   
   # Use for routing decisions
   state["execution_metrics"]["solver"] = metrics
   ```

2. **Implement Circuit Breakers**
   ```python
   # Prevent cascade failures
   if failures >= threshold:
       state["circuit_breaker_open"] = True
   ```

3. **Cache Routing Decisions**
   ```python
   # Review routing history
   history = router.get_routing_history()
   ```

4. **Set Appropriate Retry Limits**
   ```python
   # Balance reliability vs latency
   router = WorkflowRouter(max_retries=3)
   ```

---

## Common Pitfalls

❌ **Don't**: Forget to handle circuit breaker state
```python
# Bad: Ignores circuit breaker
decision = router.route_after_execution(...)
```

✅ **Do**: Check circuit breaker before routing
```python
# Good: Checks circuit breaker
if state.get("circuit_breaker_open"):
    return "fallback"
```

❌ **Don't**: Use infinite retries
```python
# Bad: No limit
while True:
    retry()
```

✅ **Do**: Set reasonable retry limits
```python
# Good: Max 3 retries with backoff
router = WorkflowRouter(max_retries=3)
```

❌ **Don't**: Ignore error severity
```python
# Bad: Treats all errors the same
if errors:
    return "error"
```

✅ **Do**: Route based on severity
```python
# Good: Different paths for different severities
if error_severity == ErrorSeverity.CRITICAL:
    return END
elif error_severity == ErrorSeverity.MEDIUM:
    return "retry"
```

---

## Additional Resources

- **Full Documentation**: `WORKFLOW_ROUTING_GUIDE.md`
- **Implementation**: `src/agent/workflow_routing.py`
- **Examples**: `src/agent/example_routing_strategies.py`
- **Tests**: `src/agent/test_workflow_routing.py`
- **Integration**: `src/agent/example_enhanced_routing.py`

---

## Support

For questions or issues:
1. Check the comprehensive guide: `WORKFLOW_ROUTING_GUIDE.md`
2. Run examples: `python3 example_routing_strategies.py`
3. Review tests: `python3 test_workflow_routing.py`
4. See integration: `python3 example_enhanced_routing.py`
