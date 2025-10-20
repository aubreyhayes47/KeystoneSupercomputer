"""
Test Suite for Workflow Routing Logic
======================================

Comprehensive tests for routing logic and conditional edges in LangGraph workflows.

Test Coverage:
- Basic routing decisions (success/error paths)
- Error handling with retry logic
- Exponential backoff calculations
- Context-based routing
- Resource-aware routing
- Performance-based adaptive routing
- Parallel execution routing
- Circuit breaker patterns
- Output value-based routing
- Validation routing
"""

import unittest
from unittest.mock import Mock, patch
from datetime import datetime

from workflow_routing import (
    WorkflowRouter,
    WorkflowRoutingState,
    NodeStatus,
    ErrorSeverity,
    RoutingStrategy,
    RoutingDecision,
    ExecutionMetrics,
    route_by_validation_result,
    route_by_simulation_tool,
    route_by_priority,
    route_after_error_handling,
    build_example_routing_graph
)


class TestWorkflowRouter(unittest.TestCase):
    """Test cases for WorkflowRouter class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.router = WorkflowRouter(max_retries=3, circuit_breaker_threshold=5)
    
    def test_initialization(self):
        """Test router initialization with parameters."""
        self.assertEqual(self.router.max_retries, 3)
        self.assertEqual(self.router.circuit_breaker_threshold, 5)
        self.assertEqual(self.router.backoff_multiplier, 2.0)
        self.assertEqual(len(self.router.routing_history), 0)
    
    def test_route_after_execution_success(self):
        """Test routing after successful node execution."""
        state: WorkflowRoutingState = {
            "node_status": {"analyze": NodeStatus.COMPLETED},
            "node_results": {"analyze": {"result": "success"}},
            "retry_count": 0,
            "max_retries": 3
        }
        
        decision = self.router.route_after_execution(
            state=state,
            current_node="analyze",
            success_node="plan",
            error_node="error_handler"
        )
        
        self.assertEqual(decision.next_node, "plan")
        self.assertEqual(decision.strategy, RoutingStrategy.SUCCESS_PATH)
        self.assertIn("completed successfully", decision.reason.lower())
    
    def test_route_after_execution_failure_with_retry(self):
        """Test routing after failed execution with retry logic."""
        state: WorkflowRoutingState = {
            "node_status": {"simulation": NodeStatus.FAILED},
            "node_results": {},
            "errors": [{"message": "Connection timeout"}],
            "retry_count": 0,
            "max_retries": 3
        }
        
        decision = self.router.route_after_execution(
            state=state,
            current_node="simulation",
            success_node="validation",
            error_node="error_handler",
            retry_node="simulation"
        )
        
        self.assertEqual(decision.next_node, "simulation")
        self.assertEqual(decision.strategy, RoutingStrategy.RETRY_WITH_BACKOFF)
        self.assertEqual(decision.metadata["retry_count"], 1)
        self.assertEqual(decision.metadata["backoff_seconds"], 1.0)  # 2^0
    
    def test_route_after_execution_max_retries_exceeded(self):
        """Test routing when max retries exceeded."""
        state: WorkflowRoutingState = {
            "node_status": {"simulation": NodeStatus.FAILED},
            "node_results": {},
            "errors": [{"message": "Persistent error"}],
            "retry_count": 3,
            "max_retries": 3
        }
        
        decision = self.router.route_after_execution(
            state=state,
            current_node="simulation",
            success_node="validation",
            error_node="error_handler",
            retry_node="simulation"
        )
        
        self.assertEqual(decision.next_node, "error_handler")
        self.assertEqual(decision.strategy, RoutingStrategy.ERROR_FALLBACK)
        self.assertIn("max retries", decision.reason.lower())
    
    def test_route_after_execution_critical_error(self):
        """Test routing on critical error immediately terminates."""
        from langgraph.graph import END
        
        state: WorkflowRoutingState = {
            "node_status": {"simulation": NodeStatus.FAILED},
            "node_results": {},
            "errors": [{"message": "Fatal error"}],
            "error_severity": ErrorSeverity.CRITICAL,
            "retry_count": 0
        }
        
        decision = self.router.route_after_execution(
            state=state,
            current_node="simulation",
            success_node="validation",
            error_node="error_handler"
        )
        
        self.assertEqual(decision.next_node, END)
        self.assertEqual(decision.strategy, RoutingStrategy.ERROR_FALLBACK)
        self.assertIn("critical", decision.reason.lower())
    
    def test_route_after_execution_circuit_breaker_open(self):
        """Test routing when circuit breaker is open."""
        state: WorkflowRoutingState = {
            "node_status": {"external_api": NodeStatus.FAILED},
            "node_results": {},
            "circuit_breaker_open": True,
            "retry_count": 0
        }
        
        decision = self.router.route_after_execution(
            state=state,
            current_node="external_api",
            success_node="process",
            error_node="fallback"
        )
        
        self.assertEqual(decision.next_node, "fallback")
        self.assertEqual(decision.strategy, RoutingStrategy.CIRCUIT_BREAKER)
        self.assertIn("circuit breaker", decision.reason.lower())
    
    def test_exponential_backoff_calculation(self):
        """Test exponential backoff calculation for retries."""
        state: WorkflowRoutingState = {
            "node_status": {"task": NodeStatus.FAILED},
            "node_results": {},
            "errors": [{"message": "timeout"}],
            "retry_count": 2,
            "max_retries": 5
        }
        
        decision = self.router.route_after_execution(
            state=state,
            current_node="task",
            success_node="next",
            error_node="error",
            retry_node="task"
        )
        
        # Backoff should be 2^2 = 4 seconds
        self.assertEqual(decision.metadata["backoff_seconds"], 4.0)
    
    def test_route_by_output_value(self):
        """Test routing based on specific output value."""
        state: WorkflowRoutingState = {
            "node_status": {"approval": NodeStatus.COMPLETED},
            "node_results": {
                "approval": {
                    "status": "approved",
                    "confidence": 0.95
                }
            }
        }
        
        routing_map = {
            "approved": "execute",
            "rejected": "notify",
            "pending": "review"
        }
        
        decision = self.router.route_by_output_value(
            state=state,
            current_node="approval",
            output_key="status",
            routing_map=routing_map,
            default_node="error"
        )
        
        self.assertEqual(decision.next_node, "execute")
        self.assertEqual(decision.strategy, RoutingStrategy.CONDITIONAL_BRANCH)
    
    def test_route_by_output_value_default(self):
        """Test routing to default when output value not in map."""
        state: WorkflowRoutingState = {
            "node_status": {"check": NodeStatus.COMPLETED},
            "node_results": {
                "check": {"status": "unknown"}
            }
        }
        
        routing_map = {
            "approved": "execute",
            "rejected": "notify"
        }
        
        decision = self.router.route_by_output_value(
            state=state,
            current_node="check",
            output_key="status",
            routing_map=routing_map,
            default_node="error_handler"
        )
        
        self.assertEqual(decision.next_node, "error_handler")
    
    def test_route_by_context(self):
        """Test context-based routing with rules."""
        state: WorkflowRoutingState = {
            "node_status": {},
            "node_results": {},
            "workflow_context": {"priority": "high"}
        }
        
        routing_rules = [
            {
                "condition": lambda p: p == "high",
                "node": "fast_path",
                "reason": "High priority"
            },
            {
                "condition": lambda p: p == "low",
                "node": "slow_path",
                "reason": "Low priority"
            }
        ]
        
        decision = self.router.route_by_context(
            state=state,
            context_key="priority",
            routing_rules=routing_rules,
            default_node="standard"
        )
        
        self.assertEqual(decision.next_node, "fast_path")
        self.assertEqual(decision.strategy, RoutingStrategy.CONDITIONAL_BRANCH)
    
    def test_route_by_context_default(self):
        """Test context-based routing defaults when no rules match."""
        state: WorkflowRoutingState = {
            "node_status": {},
            "node_results": {},
            "workflow_context": {"priority": "medium"}
        }
        
        routing_rules = [
            {
                "condition": lambda p: p == "high",
                "node": "fast_path",
                "reason": "High priority"
            }
        ]
        
        decision = self.router.route_by_context(
            state=state,
            context_key="priority",
            routing_rules=routing_rules,
            default_node="standard"
        )
        
        self.assertEqual(decision.next_node, "standard")
    
    def test_route_parallel_split(self):
        """Test parallel execution routing."""
        state: WorkflowRoutingState = {
            "node_status": {},
            "node_results": {}
        }
        
        parallel_nodes = ["task_a", "task_b", "task_c"]
        decisions = self.router.route_parallel_split(
            state=state,
            parallel_nodes=parallel_nodes,
            join_node="aggregate"
        )
        
        self.assertEqual(len(decisions), 3)
        for decision in decisions:
            self.assertEqual(decision.strategy, RoutingStrategy.PARALLEL_BRANCH)
            self.assertEqual(decision.metadata["join_node"], "aggregate")
            self.assertIn(decision.next_node, parallel_nodes)
    
    def test_route_by_resource_availability_sufficient(self):
        """Test resource-aware routing with sufficient resources."""
        state: WorkflowRoutingState = {
            "node_status": {},
            "node_results": {},
            "resource_limits": {"memory": 16000.0},
            "current_resource_usage": {"memory": 4000.0}
        }
        
        decision = self.router.route_by_resource_availability(
            state=state,
            resource_intensive_node="high_res",
            lightweight_node="low_res",
            resource_type="memory",
            threshold=8000.0
        )
        
        self.assertEqual(decision.next_node, "high_res")
        self.assertEqual(decision.strategy, RoutingStrategy.ADAPTIVE_SELECTION)
    
    def test_route_by_resource_availability_insufficient(self):
        """Test resource-aware routing with insufficient resources."""
        state: WorkflowRoutingState = {
            "node_status": {},
            "node_results": {},
            "resource_limits": {"memory": 16000.0},
            "current_resource_usage": {"memory": 12000.0}
        }
        
        decision = self.router.route_by_resource_availability(
            state=state,
            resource_intensive_node="high_res",
            lightweight_node="low_res",
            resource_type="memory",
            threshold=8000.0
        )
        
        self.assertEqual(decision.next_node, "low_res")
        self.assertIn("insufficient", decision.reason.lower())
    
    def test_route_by_performance_metrics_success_rate(self):
        """Test adaptive routing based on success rate."""
        metrics_a = ExecutionMetrics(
            execution_count=10,
            failure_count=2,
            success_rate=80.0
        )
        metrics_b = ExecutionMetrics(
            execution_count=10,
            failure_count=0,
            success_rate=100.0
        )
        
        state: WorkflowRoutingState = {
            "node_status": {},
            "node_results": {},
            "execution_metrics": {
                "solver_a": metrics_a,
                "solver_b": metrics_b
            }
        }
        
        decision = self.router.route_by_performance_metrics(
            state=state,
            node_options=["solver_a", "solver_b"],
            metric="success_rate"
        )
        
        self.assertEqual(decision.next_node, "solver_b")
        self.assertEqual(decision.strategy, RoutingStrategy.ADAPTIVE_SELECTION)
    
    def test_route_by_performance_metrics_execution_time(self):
        """Test adaptive routing based on execution time."""
        metrics_fast = ExecutionMetrics(avg_execution_time=10.0)
        metrics_slow = ExecutionMetrics(avg_execution_time=50.0)
        
        state: WorkflowRoutingState = {
            "node_status": {},
            "node_results": {},
            "execution_metrics": {
                "fast_solver": metrics_fast,
                "slow_solver": metrics_slow
            }
        }
        
        decision = self.router.route_by_performance_metrics(
            state=state,
            node_options=["fast_solver", "slow_solver"],
            metric="avg_execution_time"
        )
        
        self.assertEqual(decision.next_node, "fast_solver")
    
    def test_update_circuit_breaker_success(self):
        """Test circuit breaker update after success."""
        state: WorkflowRoutingState = {
            "circuit_breaker_failures": 3,
            "circuit_breaker_threshold": 5
        }
        
        update = self.router.update_circuit_breaker(
            state=state,
            node="test_node",
            success=True
        )
        
        self.assertFalse(update["circuit_breaker_open"])
        self.assertEqual(update["circuit_breaker_failures"], 0)
    
    def test_update_circuit_breaker_failure(self):
        """Test circuit breaker update after failure."""
        state: WorkflowRoutingState = {
            "circuit_breaker_failures": 4,
            "circuit_breaker_threshold": 5
        }
        
        update = self.router.update_circuit_breaker(
            state=state,
            node="test_node",
            success=False
        )
        
        self.assertTrue(update["circuit_breaker_open"])
        self.assertEqual(update["circuit_breaker_failures"], 5)


class TestExecutionMetrics(unittest.TestCase):
    """Test cases for ExecutionMetrics class."""
    
    def test_initialization(self):
        """Test metrics initialization."""
        metrics = ExecutionMetrics()
        
        self.assertEqual(metrics.execution_count, 0)
        self.assertEqual(metrics.failure_count, 0)
        self.assertEqual(metrics.avg_execution_time, 0.0)
        self.assertEqual(metrics.success_rate, 100.0)
        self.assertIsNone(metrics.last_execution_time)
    
    def test_update_success(self):
        """Test metrics update after successful execution."""
        metrics = ExecutionMetrics()
        
        metrics.update_success(10.0)
        
        self.assertEqual(metrics.execution_count, 1)
        self.assertEqual(metrics.failure_count, 0)
        self.assertEqual(metrics.avg_execution_time, 10.0)
        self.assertEqual(metrics.success_rate, 100.0)
        self.assertIsNotNone(metrics.last_execution_time)
    
    def test_update_success_multiple(self):
        """Test metrics update after multiple successes."""
        metrics = ExecutionMetrics()
        
        metrics.update_success(10.0)
        metrics.update_success(20.0)
        metrics.update_success(30.0)
        
        self.assertEqual(metrics.execution_count, 3)
        self.assertEqual(metrics.failure_count, 0)
        self.assertEqual(metrics.avg_execution_time, 20.0)  # (10+20+30)/3
        self.assertEqual(metrics.success_rate, 100.0)
    
    def test_update_failure(self):
        """Test metrics update after failed execution."""
        metrics = ExecutionMetrics()
        
        metrics.update_failure()
        
        self.assertEqual(metrics.execution_count, 1)
        self.assertEqual(metrics.failure_count, 1)
        self.assertEqual(metrics.success_rate, 0.0)
        self.assertIsNotNone(metrics.last_execution_time)
    
    def test_update_mixed_success_failure(self):
        """Test metrics with mixed success and failure."""
        metrics = ExecutionMetrics()
        
        metrics.update_success(10.0)
        metrics.update_success(20.0)
        metrics.update_failure()
        metrics.update_success(30.0)
        
        self.assertEqual(metrics.execution_count, 4)
        self.assertEqual(metrics.failure_count, 1)
        self.assertEqual(metrics.success_rate, 75.0)  # 3/4


class TestRoutingFunctions(unittest.TestCase):
    """Test cases for standalone routing functions."""
    
    def test_route_by_validation_result_success(self):
        """Test validation routing on success."""
        state: WorkflowRoutingState = {
            "node_results": {
                "validate": {"validation_passed": True}
            },
            "errors": []
        }
        
        result = route_by_validation_result(state)
        self.assertEqual(result, "aggregate")
    
    def test_route_by_validation_result_failure_with_retry(self):
        """Test validation routing on failure with retry available."""
        state: WorkflowRoutingState = {
            "node_results": {
                "validate": {"validation_passed": False}
            },
            "errors": [{"message": "Validation failed"}],
            "error_severity": ErrorSeverity.MEDIUM,
            "retry_count": 1,
            "max_retries": 3
        }
        
        result = route_by_validation_result(state)
        self.assertEqual(result, "refine")
    
    def test_route_by_validation_result_critical_error(self):
        """Test validation routing on critical error."""
        state: WorkflowRoutingState = {
            "node_results": {
                "validate": {"validation_passed": False}
            },
            "errors": [{"message": "Critical failure"}],
            "error_severity": ErrorSeverity.CRITICAL
        }
        
        result = route_by_validation_result(state)
        self.assertEqual(result, "error")
    
    def test_route_by_simulation_tool_fenicsx(self):
        """Test tool selection routing for FEniCSx."""
        state: WorkflowRoutingState = {
            "node_results": {
                "plan": {"required_tool": "fenicsx"}
            }
        }
        
        result = route_by_simulation_tool(state)
        self.assertEqual(result, "fenicsx_performer")
    
    def test_route_by_simulation_tool_lammps(self):
        """Test tool selection routing for LAMMPS."""
        state: WorkflowRoutingState = {
            "node_results": {
                "plan": {"required_tool": "lammps"}
            }
        }
        
        result = route_by_simulation_tool(state)
        self.assertEqual(result, "lammps_performer")
    
    def test_route_by_simulation_tool_openfoam(self):
        """Test tool selection routing for OpenFOAM."""
        state: WorkflowRoutingState = {
            "node_results": {
                "plan": {"required_tool": "openfoam"}
            }
        }
        
        result = route_by_simulation_tool(state)
        self.assertEqual(result, "openfoam_performer")
    
    def test_route_by_priority_high(self):
        """Test priority-based routing for high priority."""
        state: WorkflowRoutingState = {
            "workflow_context": {"priority": "high"}
        }
        
        result = route_by_priority(state)
        self.assertEqual(result, "fast_execution_path")
    
    def test_route_by_priority_low(self):
        """Test priority-based routing for low priority."""
        state: WorkflowRoutingState = {
            "workflow_context": {"priority": "low"}
        }
        
        result = route_by_priority(state)
        self.assertEqual(result, "batch_queue")
    
    def test_route_after_error_handling_retry(self):
        """Test routing after error handling with retry."""
        state: WorkflowRoutingState = {
            "node_results": {
                "handle_error": {"strategy": "retry"}
            }
        }
        
        result = route_after_error_handling(state)
        self.assertEqual(result, "delegate")
    
    def test_route_after_error_handling_alternative(self):
        """Test routing after error handling with alternative path."""
        state: WorkflowRoutingState = {
            "node_results": {
                "handle_error": {"strategy": "alternative_path"}
            }
        }
        
        result = route_after_error_handling(state)
        self.assertEqual(result, "alternative_execution")


class TestExampleGraph(unittest.TestCase):
    """Test cases for example routing graph."""
    
    def test_build_example_graph(self):
        """Test that example graph builds successfully."""
        graph = build_example_routing_graph()
        self.assertIsNotNone(graph)
    
    def test_example_graph_execution(self):
        """Test execution of example routing graph."""
        graph = build_example_routing_graph()
        
        initial_state: WorkflowRoutingState = {
            "node_status": {},
            "node_results": {},
            "retry_count": 0,
            "max_retries": 3
        }
        
        # Execute graph
        result = graph.invoke(initial_state)
        
        # Verify execution completed
        self.assertIn("node_status", result)
        self.assertIn("node_results", result)


if __name__ == "__main__":
    # Run tests
    unittest.main(verbosity=2)
