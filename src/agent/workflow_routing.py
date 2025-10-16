"""
LangGraph Workflow Routing Logic and Conditional Edges
=======================================================

This module implements comprehensive routing logic and conditional edges for 
workflow execution in LangGraph. It provides decision-making capabilities based 
on agent outputs, error states, and workflow context.

Key Features:
- Conditional edge routing based on multiple criteria
- Error handling with fallback paths
- Dynamic workflow branching
- Parallel execution patterns with join nodes
- Adaptive retry strategies
- Circuit breaker patterns for fault tolerance

Example:
    >>> from workflow_routing import WorkflowRouter, RoutingDecision
    >>> router = WorkflowRouter()
    >>> decision = router.route_after_execution(state)
    >>> print(f"Next node: {decision.next_node}")
"""

from typing import TypedDict, Dict, Any, List, Optional, Literal, Callable
from enum import Enum
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import operator
from typing_extensions import NotRequired

from langgraph.graph import StateGraph, END


class RoutingStrategy(str, Enum):
    """Available routing strategies for workflow execution."""
    SUCCESS_PATH = "success_path"
    ERROR_FALLBACK = "error_fallback"
    RETRY_WITH_BACKOFF = "retry_with_backoff"
    PARALLEL_BRANCH = "parallel_branch"
    ADAPTIVE_SELECTION = "adaptive_selection"
    CIRCUIT_BREAKER = "circuit_breaker"
    CONDITIONAL_BRANCH = "conditional_branch"


class NodeStatus(str, Enum):
    """Status of a workflow node execution."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    SKIPPED = "skipped"


class ErrorSeverity(str, Enum):
    """Severity levels for errors."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class RoutingDecision:
    """
    Encapsulates a routing decision for workflow execution.
    
    Attributes:
        next_node: Name of the next node to execute
        strategy: Routing strategy used for this decision
        reason: Human-readable explanation for the decision
        metadata: Additional context about the decision
        fallback_nodes: Alternative nodes if primary fails
    """
    next_node: str
    strategy: RoutingStrategy
    reason: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    fallback_nodes: List[str] = field(default_factory=list)


@dataclass
class ExecutionMetrics:
    """
    Metrics for node execution tracking.
    
    Attributes:
        execution_count: Number of times node has executed
        failure_count: Number of failures
        avg_execution_time: Average execution time in seconds
        last_execution_time: Timestamp of last execution
        success_rate: Percentage of successful executions
    """
    execution_count: int = 0
    failure_count: int = 0
    avg_execution_time: float = 0.0
    last_execution_time: Optional[datetime] = None
    success_rate: float = 100.0
    
    def update_success(self, execution_time: float):
        """Update metrics after successful execution."""
        self.execution_count += 1
        self.avg_execution_time = (
            (self.avg_execution_time * (self.execution_count - 1) + execution_time) 
            / self.execution_count
        )
        self.last_execution_time = datetime.now()
        self.success_rate = (
            (self.execution_count - self.failure_count) / self.execution_count * 100
        )
    
    def update_failure(self):
        """Update metrics after failed execution."""
        self.execution_count += 1
        self.failure_count += 1
        self.last_execution_time = datetime.now()
        self.success_rate = (
            (self.execution_count - self.failure_count) / self.execution_count * 100
        )


class WorkflowRoutingState(TypedDict):
    """
    State schema for workflow routing decisions.
    
    This state includes all information needed for intelligent routing decisions.
    """
    # Execution status and results
    node_status: Dict[str, NodeStatus]
    node_results: Dict[str, Any]
    
    # Error tracking
    errors: NotRequired[List[Dict[str, Any]]]
    error_severity: NotRequired[ErrorSeverity]
    
    # Execution metrics
    execution_metrics: NotRequired[Dict[str, ExecutionMetrics]]
    
    # Retry management
    retry_count: NotRequired[int]
    max_retries: NotRequired[int]
    backoff_multiplier: NotRequired[float]
    
    # Circuit breaker state
    circuit_breaker_open: NotRequired[bool]
    circuit_breaker_failures: NotRequired[int]
    circuit_breaker_threshold: NotRequired[int]
    
    # Workflow context
    workflow_context: NotRequired[Dict[str, Any]]
    user_preferences: NotRequired[Dict[str, Any]]
    
    # Resource constraints
    resource_limits: NotRequired[Dict[str, Any]]
    current_resource_usage: NotRequired[Dict[str, Any]]


class WorkflowRouter:
    """
    Intelligent routing engine for LangGraph workflows.
    
    Provides sophisticated routing logic based on:
    - Agent execution results and outputs
    - Error states and severity levels
    - Workflow context and user preferences
    - Resource availability and constraints
    - Historical execution metrics
    """
    
    def __init__(
        self, 
        max_retries: int = 3,
        circuit_breaker_threshold: int = 5,
        backoff_multiplier: float = 2.0
    ):
        """
        Initialize the workflow router.
        
        Args:
            max_retries: Maximum retry attempts for failed nodes
            circuit_breaker_threshold: Failures before circuit breaker opens
            backoff_multiplier: Exponential backoff multiplier for retries
        """
        self.max_retries = max_retries
        self.circuit_breaker_threshold = circuit_breaker_threshold
        self.backoff_multiplier = backoff_multiplier
        self.routing_history: List[RoutingDecision] = []
    
    def route_after_execution(
        self, 
        state: WorkflowRoutingState,
        current_node: str,
        success_node: str,
        error_node: str,
        retry_node: Optional[str] = None
    ) -> RoutingDecision:
        """
        Route workflow after node execution based on results and errors.
        
        This is the main routing method that considers:
        - Execution success/failure
        - Error severity
        - Retry attempts
        - Circuit breaker state
        - Resource availability
        
        Args:
            state: Current workflow state
            current_node: Node that just completed
            success_node: Node to route to on success
            error_node: Node to route to on error
            retry_node: Optional node to retry execution
            
        Returns:
            RoutingDecision with next node and routing strategy
        """
        # Check node status
        node_status = state.get("node_status", {}).get(current_node)
        
        # Check for critical errors first
        errors = state.get("errors", [])
        error_severity = state.get("error_severity", ErrorSeverity.LOW)
        
        if error_severity == ErrorSeverity.CRITICAL:
            return RoutingDecision(
                next_node=END,
                strategy=RoutingStrategy.ERROR_FALLBACK,
                reason=f"Critical error in {current_node}, terminating workflow",
                metadata={"errors": errors}
            )
        
        # Check circuit breaker
        circuit_open = state.get("circuit_breaker_open", False)
        if circuit_open:
            return RoutingDecision(
                next_node=error_node,
                strategy=RoutingStrategy.CIRCUIT_BREAKER,
                reason=f"Circuit breaker open for {current_node}",
                metadata={"circuit_breaker_state": "open"},
                fallback_nodes=[END]
            )
        
        # Check execution status
        if node_status == NodeStatus.COMPLETED:
            # Success path
            return RoutingDecision(
                next_node=success_node,
                strategy=RoutingStrategy.SUCCESS_PATH,
                reason=f"Node {current_node} completed successfully",
                metadata={"execution_status": "success"}
            )
        
        elif node_status == NodeStatus.FAILED:
            # Determine if retry is appropriate
            retry_count = state.get("retry_count", 0)
            max_retries = state.get("max_retries", self.max_retries)
            
            if retry_count < max_retries and retry_node:
                # Retry with exponential backoff
                backoff = self.backoff_multiplier ** retry_count
                return RoutingDecision(
                    next_node=retry_node,
                    strategy=RoutingStrategy.RETRY_WITH_BACKOFF,
                    reason=f"Retrying {current_node} (attempt {retry_count + 1}/{max_retries})",
                    metadata={
                        "retry_count": retry_count + 1,
                        "backoff_seconds": backoff,
                        "errors": errors
                    },
                    fallback_nodes=[error_node, END]
                )
            else:
                # Max retries exceeded, route to error handler
                return RoutingDecision(
                    next_node=error_node,
                    strategy=RoutingStrategy.ERROR_FALLBACK,
                    reason=f"Max retries exceeded for {current_node}",
                    metadata={"retry_count": retry_count, "errors": errors}
                )
        
        elif node_status == NodeStatus.TIMEOUT:
            # Timeout - route to error with special handling
            return RoutingDecision(
                next_node=error_node,
                strategy=RoutingStrategy.ERROR_FALLBACK,
                reason=f"Timeout in {current_node}",
                metadata={"error_type": "timeout"}
            )
        
        # Default to success path if status unclear
        return RoutingDecision(
            next_node=success_node,
            strategy=RoutingStrategy.SUCCESS_PATH,
            reason=f"Default routing for {current_node}",
            metadata={"note": "Status unclear, proceeding with success path"}
        )
    
    def route_by_output_value(
        self,
        state: WorkflowRoutingState,
        current_node: str,
        output_key: str,
        routing_map: Dict[Any, str],
        default_node: str
    ) -> RoutingDecision:
        """
        Route based on specific output value from node execution.
        
        Example:
            If node output contains {"status": "approved"}, route to approval node
            If node output contains {"status": "rejected"}, route to rejection node
        
        Args:
            state: Current workflow state
            current_node: Node that produced output
            output_key: Key in node results to check
            routing_map: Mapping from output values to next nodes
            default_node: Default node if output not in routing_map
            
        Returns:
            RoutingDecision based on output value
        """
        node_results = state.get("node_results", {}).get(current_node, {})
        output_value = node_results.get(output_key)
        
        next_node = routing_map.get(output_value, default_node)
        
        return RoutingDecision(
            next_node=next_node,
            strategy=RoutingStrategy.CONDITIONAL_BRANCH,
            reason=f"Routing based on {output_key}={output_value}",
            metadata={
                "output_key": output_key,
                "output_value": output_value,
                "routing_map": routing_map
            }
        )
    
    def route_by_context(
        self,
        state: WorkflowRoutingState,
        context_key: str,
        routing_rules: List[Dict[str, Any]],
        default_node: str
    ) -> RoutingDecision:
        """
        Route based on workflow context and user preferences.
        
        Routing rules are evaluated in order, first match wins.
        
        Example rule:
            {
                "condition": lambda ctx: ctx.get("priority") == "high",
                "node": "fast_path",
                "reason": "High priority request"
            }
        
        Args:
            state: Current workflow state
            context_key: Key in workflow context to evaluate
            routing_rules: List of rules with condition, node, and reason
            default_node: Default node if no rules match
            
        Returns:
            RoutingDecision based on context evaluation
        """
        workflow_context = state.get("workflow_context", {})
        context_value = workflow_context.get(context_key)
        
        for rule in routing_rules:
            condition = rule.get("condition")
            if callable(condition) and condition(context_value):
                return RoutingDecision(
                    next_node=rule["node"],
                    strategy=RoutingStrategy.CONDITIONAL_BRANCH,
                    reason=rule.get("reason", f"Context rule matched: {context_key}"),
                    metadata={
                        "context_key": context_key,
                        "context_value": context_value,
                        "rule": str(rule)
                    }
                )
        
        return RoutingDecision(
            next_node=default_node,
            strategy=RoutingStrategy.CONDITIONAL_BRANCH,
            reason=f"No context rules matched for {context_key}, using default",
            metadata={"context_key": context_key, "context_value": context_value}
        )
    
    def route_parallel_split(
        self,
        state: WorkflowRoutingState,
        parallel_nodes: List[str],
        join_node: str
    ) -> List[RoutingDecision]:
        """
        Create routing decisions for parallel execution branches.
        
        This method enables parallel execution of multiple nodes that will
        later converge at a join node.
        
        Args:
            state: Current workflow state
            parallel_nodes: List of nodes to execute in parallel
            join_node: Node where parallel branches converge
            
        Returns:
            List of RoutingDecisions, one for each parallel branch
        """
        decisions = []
        
        for node in parallel_nodes:
            decisions.append(RoutingDecision(
                next_node=node,
                strategy=RoutingStrategy.PARALLEL_BRANCH,
                reason=f"Parallel execution of {node}",
                metadata={
                    "parallel_group": parallel_nodes,
                    "join_node": join_node,
                    "branch_node": node
                }
            ))
        
        return decisions
    
    def route_by_resource_availability(
        self,
        state: WorkflowRoutingState,
        resource_intensive_node: str,
        lightweight_node: str,
        resource_type: str,
        threshold: float
    ) -> RoutingDecision:
        """
        Route based on resource availability and constraints.
        
        Useful for adaptive workflows that choose different execution paths
        based on available CPU, memory, GPU, or other resources.
        
        Args:
            state: Current workflow state
            resource_intensive_node: Node for high-resource path
            lightweight_node: Node for low-resource path
            resource_type: Type of resource to check (cpu, memory, gpu)
            threshold: Resource threshold for decision
            
        Returns:
            RoutingDecision based on resource availability
        """
        resource_limits = state.get("resource_limits", {})
        current_usage = state.get("current_resource_usage", {})
        
        available = resource_limits.get(resource_type, 100.0) - current_usage.get(resource_type, 0.0)
        
        if available >= threshold:
            return RoutingDecision(
                next_node=resource_intensive_node,
                strategy=RoutingStrategy.ADAPTIVE_SELECTION,
                reason=f"Sufficient {resource_type} available for intensive path",
                metadata={
                    "resource_type": resource_type,
                    "available": available,
                    "threshold": threshold
                }
            )
        else:
            return RoutingDecision(
                next_node=lightweight_node,
                strategy=RoutingStrategy.ADAPTIVE_SELECTION,
                reason=f"Insufficient {resource_type}, using lightweight path",
                metadata={
                    "resource_type": resource_type,
                    "available": available,
                    "threshold": threshold
                }
            )
    
    def route_by_performance_metrics(
        self,
        state: WorkflowRoutingState,
        node_options: List[str],
        metric: str = "success_rate"
    ) -> RoutingDecision:
        """
        Route to the best-performing node based on historical metrics.
        
        This adaptive routing strategy learns from past executions to
        choose the most reliable or fastest path.
        
        Args:
            state: Current workflow state
            node_options: List of possible next nodes
            metric: Metric to optimize (success_rate, avg_execution_time)
            
        Returns:
            RoutingDecision for best-performing node
        """
        execution_metrics = state.get("execution_metrics", {})
        
        best_node = None
        best_value = None
        
        for node in node_options:
            metrics = execution_metrics.get(node)
            if metrics:
                value = getattr(metrics, metric, 0)
                
                # For success_rate, higher is better
                # For avg_execution_time, lower is better
                if metric == "success_rate":
                    if best_value is None or value > best_value:
                        best_value = value
                        best_node = node
                elif metric == "avg_execution_time":
                    if best_value is None or value < best_value:
                        best_value = value
                        best_node = node
        
        # Default to first option if no metrics available
        if best_node is None:
            best_node = node_options[0]
            best_value = "N/A"
        
        return RoutingDecision(
            next_node=best_node,
            strategy=RoutingStrategy.ADAPTIVE_SELECTION,
            reason=f"Selected {best_node} based on {metric}={best_value}",
            metadata={
                "metric": metric,
                "value": best_value,
                "node_options": node_options
            }
        )
    
    def update_circuit_breaker(
        self,
        state: WorkflowRoutingState,
        node: str,
        success: bool
    ) -> Dict[str, Any]:
        """
        Update circuit breaker state based on execution result.
        
        Circuit breaker pattern prevents cascading failures by temporarily
        blocking routes that consistently fail.
        
        Args:
            state: Current workflow state
            node: Node that executed
            success: Whether execution succeeded
            
        Returns:
            Updated circuit breaker state
        """
        failures = state.get("circuit_breaker_failures", 0)
        threshold = state.get("circuit_breaker_threshold", self.circuit_breaker_threshold)
        
        if success:
            # Reset failures on success
            return {
                "circuit_breaker_open": False,
                "circuit_breaker_failures": 0
            }
        else:
            # Increment failures
            failures += 1
            if failures >= threshold:
                return {
                    "circuit_breaker_open": True,
                    "circuit_breaker_failures": failures
                }
            else:
                return {
                    "circuit_breaker_open": False,
                    "circuit_breaker_failures": failures
                }
    
    def get_routing_history(self) -> List[RoutingDecision]:
        """
        Get the history of routing decisions made by this router.
        
        Returns:
            List of all routing decisions
        """
        return self.routing_history.copy()
    
    def clear_routing_history(self):
        """Clear the routing history."""
        self.routing_history.clear()


# Example routing functions for use with LangGraph conditional edges

def route_by_validation_result(state: WorkflowRoutingState) -> str:
    """
    Example routing function for validation results.
    
    Routes to different nodes based on validation outcome:
    - "aggregate" if validation passed
    - "refine" if validation failed but refinement possible
    - "error" if validation failed critically
    
    Args:
        state: Workflow state with validation results
        
    Returns:
        Name of next node
    """
    validation = state.get("node_results", {}).get("validate", {})
    validation_passed = validation.get("validation_passed", False)
    errors = state.get("errors", [])
    error_severity = state.get("error_severity", ErrorSeverity.LOW)
    
    if validation_passed:
        return "aggregate"
    elif error_severity == ErrorSeverity.CRITICAL:
        return "error"
    else:
        retry_count = state.get("retry_count", 0)
        max_retries = state.get("max_retries", 3)
        
        if retry_count < max_retries:
            return "refine"
        else:
            return "error"


def route_by_simulation_tool(state: WorkflowRoutingState) -> str:
    """
    Example routing function for tool selection.
    
    Routes to appropriate performer based on required simulation tool:
    - "fenicsx_performer" for finite element analysis
    - "lammps_performer" for molecular dynamics
    - "openfoam_performer" for computational fluid dynamics
    
    Args:
        state: Workflow state with tool selection
        
    Returns:
        Name of next node (performer agent)
    """
    plan = state.get("node_results", {}).get("plan", {})
    required_tool = plan.get("required_tool", "fenicsx")
    
    tool_mapping = {
        "fenicsx": "fenicsx_performer",
        "lammps": "lammps_performer",
        "openfoam": "openfoam_performer"
    }
    
    return tool_mapping.get(required_tool.lower(), "fenicsx_performer")


def route_after_error_handling(state: WorkflowRoutingState) -> str:
    """
    Example routing function after error handling.
    
    Determines whether to:
    - Retry the workflow
    - Use an alternative path
    - Terminate with failure
    
    Args:
        state: Workflow state with error handling results
        
    Returns:
        Name of next node or END
    """
    error_resolution = state.get("node_results", {}).get("handle_error", {})
    resolution_strategy = error_resolution.get("strategy", "terminate")
    
    if resolution_strategy == "retry":
        return "delegate"
    elif resolution_strategy == "alternative_path":
        return "alternative_execution"
    else:
        return END


def route_by_priority(state: WorkflowRoutingState) -> str:
    """
    Example routing function based on request priority.
    
    High priority requests get fast-tracked to optimized paths,
    while normal priority uses standard paths.
    
    Args:
        state: Workflow state with priority information
        
    Returns:
        Name of next node based on priority
    """
    workflow_context = state.get("workflow_context", {})
    priority = workflow_context.get("priority", "normal")
    
    if priority == "high":
        return "fast_execution_path"
    elif priority == "low":
        return "batch_queue"
    else:
        return "standard_execution_path"


# Example: Building a graph with conditional routing

def build_example_routing_graph() -> StateGraph:
    """
    Build an example LangGraph with comprehensive conditional routing.
    
    This example demonstrates:
    - Multiple routing strategies
    - Error handling with fallbacks
    - Parallel execution with join
    - Adaptive path selection
    
    Returns:
        Compiled StateGraph with routing logic
    """
    workflow = StateGraph(WorkflowRoutingState)
    
    # Define example node functions
    def analyze_node(state: WorkflowRoutingState) -> WorkflowRoutingState:
        """Example analysis node."""
        return {
            **state,
            "node_status": {**state.get("node_status", {}), "analyze": NodeStatus.COMPLETED},
            "node_results": {**state.get("node_results", {}), "analyze": {"analysis_complete": True}}
        }
    
    def plan_node(state: WorkflowRoutingState) -> WorkflowRoutingState:
        """Example planning node."""
        return {
            **state,
            "node_status": {**state.get("node_status", {}), "plan": NodeStatus.COMPLETED},
            "node_results": {**state.get("node_results", {}), "plan": {"required_tool": "fenicsx"}}
        }
    
    def execute_node(state: WorkflowRoutingState) -> WorkflowRoutingState:
        """Example execution node."""
        return {
            **state,
            "node_status": {**state.get("node_status", {}), "execute": NodeStatus.COMPLETED},
            "node_results": {**state.get("node_results", {}), "execute": {"execution_complete": True}}
        }
    
    def validate_node(state: WorkflowRoutingState) -> WorkflowRoutingState:
        """Example validation node."""
        return {
            **state,
            "node_status": {**state.get("node_status", {}), "validate": NodeStatus.COMPLETED},
            "node_results": {
                **state.get("node_results", {}), 
                "validate": {"validation_passed": True}
            }
        }
    
    def aggregate_node(state: WorkflowRoutingState) -> WorkflowRoutingState:
        """Example aggregation node."""
        return {
            **state,
            "node_status": {**state.get("node_status", {}), "aggregate": NodeStatus.COMPLETED}
        }
    
    def error_node(state: WorkflowRoutingState) -> WorkflowRoutingState:
        """Example error handling node."""
        return {
            **state,
            "node_status": {**state.get("node_status", {}), "error": NodeStatus.COMPLETED}
        }
    
    # Add nodes
    workflow.add_node("analyze", analyze_node)
    workflow.add_node("plan", plan_node)
    workflow.add_node("execute", execute_node)
    workflow.add_node("validate", validate_node)
    workflow.add_node("aggregate", aggregate_node)
    workflow.add_node("error", error_node)
    
    # Set entry point
    workflow.set_entry_point("analyze")
    
    # Add simple edges
    workflow.add_edge("analyze", "plan")
    workflow.add_edge("plan", "execute")
    workflow.add_edge("execute", "validate")
    
    # Add conditional edge after validation
    workflow.add_conditional_edges(
        "validate",
        route_by_validation_result,
        {
            "aggregate": "aggregate",
            "refine": "plan",
            "error": "error"
        }
    )
    
    # Terminal edges
    workflow.add_edge("aggregate", END)
    workflow.add_edge("error", END)
    
    return workflow.compile()


if __name__ == "__main__":
    print("Workflow Routing Logic Module")
    print("=" * 60)
    
    # Example 1: Basic routing decision
    print("\n1. Example: Basic Routing After Execution")
    print("-" * 60)
    
    router = WorkflowRouter(max_retries=3)
    
    state: WorkflowRoutingState = {
        "node_status": {"simulation": NodeStatus.COMPLETED},
        "node_results": {"simulation": {"output": "success"}},
        "retry_count": 0,
        "max_retries": 3
    }
    
    decision = router.route_after_execution(
        state=state,
        current_node="simulation",
        success_node="validation",
        error_node="error_handler"
    )
    
    print(f"Next Node: {decision.next_node}")
    print(f"Strategy: {decision.strategy.value}")
    print(f"Reason: {decision.reason}")
    
    # Example 2: Routing with retry
    print("\n2. Example: Routing with Retry Logic")
    print("-" * 60)
    
    state_failed: WorkflowRoutingState = {
        "node_status": {"simulation": NodeStatus.FAILED},
        "node_results": {},
        "errors": [{"message": "Connection timeout"}],
        "retry_count": 1,
        "max_retries": 3
    }
    
    decision = router.route_after_execution(
        state=state_failed,
        current_node="simulation",
        success_node="validation",
        error_node="error_handler",
        retry_node="simulation"
    )
    
    print(f"Next Node: {decision.next_node}")
    print(f"Strategy: {decision.strategy.value}")
    print(f"Reason: {decision.reason}")
    print(f"Backoff: {decision.metadata.get('backoff_seconds', 0)} seconds")
    
    # Example 3: Context-based routing
    print("\n3. Example: Context-Based Routing")
    print("-" * 60)
    
    state_context: WorkflowRoutingState = {
        "node_status": {},
        "node_results": {},
        "workflow_context": {"priority": "high"}
    }
    
    routing_rules = [
        {
            "condition": lambda p: p == "high",
            "node": "fast_path",
            "reason": "High priority execution"
        },
        {
            "condition": lambda p: p == "low",
            "node": "batch_queue",
            "reason": "Low priority batch processing"
        }
    ]
    
    decision = router.route_by_context(
        state=state_context,
        context_key="priority",
        routing_rules=routing_rules,
        default_node="standard_path"
    )
    
    print(f"Next Node: {decision.next_node}")
    print(f"Strategy: {decision.strategy.value}")
    print(f"Reason: {decision.reason}")
    
    print("\n" + "=" * 60)
    print("See documentation for more routing examples and patterns")
