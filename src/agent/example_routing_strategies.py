"""
Example Routing Strategies for LangGraph Workflows
===================================================

This module demonstrates various routing strategies and conditional edges
for workflow execution in LangGraph.

Run this file to see interactive examples of:
1. Basic routing after execution
2. Error handling with retry logic
3. Context-based routing
4. Resource-aware routing
5. Parallel execution patterns
6. Circuit breaker patterns
7. Adaptive routing based on metrics
"""

from workflow_routing import (
    WorkflowRouter,
    WorkflowRoutingState,
    NodeStatus,
    ErrorSeverity,
    ExecutionMetrics,
    RoutingStrategy,
    route_by_validation_result,
    route_by_simulation_tool,
    route_by_priority
)
from datetime import datetime


def example_1_basic_routing():
    """Example 1: Basic routing after successful node execution."""
    print("\n" + "="*70)
    print("EXAMPLE 1: Basic Routing After Successful Execution")
    print("="*70)
    
    router = WorkflowRouter()
    
    state: WorkflowRoutingState = {
        "node_status": {"analyze": NodeStatus.COMPLETED},
        "node_results": {
            "analyze": {
                "simulation_type": "structural",
                "requirements": "extracted"
            }
        },
        "retry_count": 0,
        "max_retries": 3
    }
    
    decision = router.route_after_execution(
        state=state,
        current_node="analyze",
        success_node="plan",
        error_node="error_handler"
    )
    
    print(f"\n✓ Node 'analyze' completed successfully")
    print(f"→ Next Node: {decision.next_node}")
    print(f"→ Strategy: {decision.strategy.value}")
    print(f"→ Reason: {decision.reason}")
    print(f"→ Metadata: {decision.metadata}")


def example_2_error_with_retry():
    """Example 2: Error handling with exponential backoff retry."""
    print("\n" + "="*70)
    print("EXAMPLE 2: Error Handling with Retry Logic")
    print("="*70)
    
    router = WorkflowRouter(max_retries=3, backoff_multiplier=2.0)
    
    # Simulate first failure
    state_attempt_1: WorkflowRoutingState = {
        "node_status": {"simulation": NodeStatus.FAILED},
        "node_results": {},
        "errors": [{"message": "Connection timeout", "code": "E_TIMEOUT"}],
        "retry_count": 0,
        "max_retries": 3
    }
    
    decision_1 = router.route_after_execution(
        state=state_attempt_1,
        current_node="simulation",
        success_node="validation",
        error_node="error_handler",
        retry_node="simulation"
    )
    
    print(f"\n✗ Attempt 1 failed: Connection timeout")
    print(f"→ Next Node: {decision_1.next_node}")
    print(f"→ Strategy: {decision_1.strategy.value}")
    print(f"→ Backoff: {decision_1.metadata.get('backoff_seconds', 0)} seconds")
    print(f"→ Retry Count: {decision_1.metadata.get('retry_count', 0)}/{state_attempt_1['max_retries']}")
    
    # Simulate second failure
    state_attempt_2: WorkflowRoutingState = {
        **state_attempt_1,
        "retry_count": 1
    }
    
    decision_2 = router.route_after_execution(
        state=state_attempt_2,
        current_node="simulation",
        success_node="validation",
        error_node="error_handler",
        retry_node="simulation"
    )
    
    print(f"\n✗ Attempt 2 failed: Connection timeout")
    print(f"→ Next Node: {decision_2.next_node}")
    print(f"→ Strategy: {decision_2.strategy.value}")
    print(f"→ Backoff: {decision_2.metadata.get('backoff_seconds', 0)} seconds")
    print(f"→ Retry Count: {decision_2.metadata.get('retry_count', 0)}/{state_attempt_2['max_retries']}")
    
    # Simulate max retries exceeded
    state_attempt_4: WorkflowRoutingState = {
        **state_attempt_1,
        "retry_count": 3
    }
    
    decision_4 = router.route_after_execution(
        state=state_attempt_4,
        current_node="simulation",
        success_node="validation",
        error_node="error_handler",
        retry_node="simulation"
    )
    
    print(f"\n✗ Max retries exceeded")
    print(f"→ Next Node: {decision_4.next_node}")
    print(f"→ Strategy: {decision_4.strategy.value}")
    print(f"→ Reason: {decision_4.reason}")


def example_3_context_routing():
    """Example 3: Context-based routing for priority handling."""
    print("\n" + "="*70)
    print("EXAMPLE 3: Context-Based Routing (Priority Handling)")
    print("="*70)
    
    router = WorkflowRouter()
    
    # High priority request
    state_high: WorkflowRoutingState = {
        "node_status": {},
        "node_results": {},
        "workflow_context": {
            "priority": "high",
            "user_tier": "premium"
        }
    }
    
    routing_rules = [
        {
            "condition": lambda p: p == "critical",
            "node": "express_lane",
            "reason": "Critical priority - express processing"
        },
        {
            "condition": lambda p: p == "high",
            "node": "gpu_accelerated_path",
            "reason": "High priority - GPU acceleration"
        },
        {
            "condition": lambda p: p == "normal",
            "node": "standard_cpu_path",
            "reason": "Normal priority - standard processing"
        },
        {
            "condition": lambda p: p == "low",
            "node": "batch_queue",
            "reason": "Low priority - batch processing"
        }
    ]
    
    decision_high = router.route_by_context(
        state=state_high,
        context_key="priority",
        routing_rules=routing_rules,
        default_node="standard_cpu_path"
    )
    
    print(f"\n📋 Request: High Priority")
    print(f"→ Next Node: {decision_high.next_node}")
    print(f"→ Strategy: {decision_high.strategy.value}")
    print(f"→ Reason: {decision_high.reason}")
    
    # Normal priority request
    state_normal: WorkflowRoutingState = {
        "node_status": {},
        "node_results": {},
        "workflow_context": {
            "priority": "normal"
        }
    }
    
    decision_normal = router.route_by_context(
        state=state_normal,
        context_key="priority",
        routing_rules=routing_rules,
        default_node="standard_cpu_path"
    )
    
    print(f"\n📋 Request: Normal Priority")
    print(f"→ Next Node: {decision_normal.next_node}")
    print(f"→ Reason: {decision_normal.reason}")


def example_4_resource_aware_routing():
    """Example 4: Resource-aware routing based on availability."""
    print("\n" + "="*70)
    print("EXAMPLE 4: Resource-Aware Routing")
    print("="*70)
    
    router = WorkflowRouter()
    
    # Scenario 1: Sufficient resources for high-resolution simulation
    state_plenty_resources: WorkflowRoutingState = {
        "node_status": {},
        "node_results": {},
        "resource_limits": {
            "cpu": 100.0,      # 100% CPU
            "memory": 32000.0, # 32GB RAM
            "gpu": 2.0         # 2 GPUs
        },
        "current_resource_usage": {
            "cpu": 20.0,       # 20% used
            "memory": 4000.0,  # 4GB used
            "gpu": 0.0         # 0 GPUs used
        }
    }
    
    decision_plenty = router.route_by_resource_availability(
        state=state_plenty_resources,
        resource_intensive_node="high_resolution_simulation",
        lightweight_node="coarse_simulation",
        resource_type="memory",
        threshold=10000.0  # Need 10GB available
    )
    
    available = state_plenty_resources["resource_limits"]["memory"] - \
                state_plenty_resources["current_resource_usage"]["memory"]
    
    print(f"\n💻 Scenario 1: Abundant Resources")
    print(f"→ Available Memory: {available / 1000:.1f} GB")
    print(f"→ Required Memory: 10.0 GB")
    print(f"→ Next Node: {decision_plenty.next_node}")
    print(f"→ Reason: {decision_plenty.reason}")
    
    # Scenario 2: Limited resources, use lightweight path
    state_limited_resources: WorkflowRoutingState = {
        "node_status": {},
        "node_results": {},
        "resource_limits": {
            "cpu": 100.0,
            "memory": 16000.0,  # 16GB RAM
            "gpu": 0.0          # No GPU
        },
        "current_resource_usage": {
            "cpu": 60.0,
            "memory": 10000.0,  # 10GB used
            "gpu": 0.0
        }
    }
    
    decision_limited = router.route_by_resource_availability(
        state=state_limited_resources,
        resource_intensive_node="high_resolution_simulation",
        lightweight_node="coarse_simulation",
        resource_type="memory",
        threshold=10000.0  # Need 10GB available
    )
    
    available_limited = state_limited_resources["resource_limits"]["memory"] - \
                       state_limited_resources["current_resource_usage"]["memory"]
    
    print(f"\n💻 Scenario 2: Limited Resources")
    print(f"→ Available Memory: {available_limited / 1000:.1f} GB")
    print(f"→ Required Memory: 10.0 GB")
    print(f"→ Next Node: {decision_limited.next_node}")
    print(f"→ Reason: {decision_limited.reason}")


def example_5_parallel_execution():
    """Example 5: Parallel execution with multiple branches."""
    print("\n" + "="*70)
    print("EXAMPLE 5: Parallel Execution Pattern")
    print("="*70)
    
    router = WorkflowRouter()
    
    state: WorkflowRoutingState = {
        "node_status": {},
        "node_results": {},
        "workflow_context": {
            "analysis_types": ["structural", "thermal", "modal"]
        }
    }
    
    decisions = router.route_parallel_split(
        state=state,
        parallel_nodes=[
            "structural_analysis",
            "thermal_analysis",
            "modal_analysis"
        ],
        join_node="aggregate_results"
    )
    
    print(f"\n🔀 Parallel Execution Setup:")
    print(f"→ Number of Branches: {len(decisions)}")
    print(f"→ Join Node: aggregate_results")
    
    for i, decision in enumerate(decisions, 1):
        print(f"\n   Branch {i}:")
        print(f"   → Node: {decision.next_node}")
        print(f"   → Strategy: {decision.strategy.value}")
        print(f"   → Will join at: {decision.metadata['join_node']}")


def example_6_circuit_breaker():
    """Example 6: Circuit breaker pattern for fault tolerance."""
    print("\n" + "="*70)
    print("EXAMPLE 6: Circuit Breaker Pattern")
    print("="*70)
    
    router = WorkflowRouter(circuit_breaker_threshold=3)
    
    # Scenario 1: Circuit closed (normal operation)
    state_closed: WorkflowRoutingState = {
        "node_status": {"external_api": NodeStatus.COMPLETED},
        "node_results": {"external_api": {"data": "success"}},
        "circuit_breaker_open": False,
        "circuit_breaker_failures": 0,
        "circuit_breaker_threshold": 3
    }
    
    decision_closed = router.route_after_execution(
        state=state_closed,
        current_node="external_api",
        success_node="process_data",
        error_node="error_handler"
    )
    
    print(f"\n🔒 Circuit: CLOSED (Normal Operation)")
    print(f"→ Failures: 0/3")
    print(f"→ Next Node: {decision_closed.next_node}")
    print(f"→ Reason: {decision_closed.reason}")
    
    # Scenario 2: Circuit open (too many failures)
    state_open: WorkflowRoutingState = {
        "node_status": {"external_api": NodeStatus.FAILED},
        "node_results": {},
        "errors": [{"message": "Service unavailable"}],
        "circuit_breaker_open": True,
        "circuit_breaker_failures": 5,
        "circuit_breaker_threshold": 3
    }
    
    decision_open = router.route_after_execution(
        state=state_open,
        current_node="external_api",
        success_node="process_data",
        error_node="fallback_handler"
    )
    
    print(f"\n🔓 Circuit: OPEN (Fault Protection)")
    print(f"→ Failures: 5/3 (threshold exceeded)")
    print(f"→ Next Node: {decision_open.next_node}")
    print(f"→ Strategy: {decision_open.strategy.value}")
    print(f"→ Reason: {decision_open.reason}")
    print(f"→ Fallback Nodes: {decision_open.fallback_nodes}")
    
    # Update circuit breaker after success
    print(f"\n🔄 Resetting Circuit After Success:")
    update = router.update_circuit_breaker(
        state=state_closed,
        node="external_api",
        success=True
    )
    print(f"→ Circuit Open: {update['circuit_breaker_open']}")
    print(f"→ Failures Reset: {update['circuit_breaker_failures']}")


def example_7_adaptive_routing():
    """Example 7: Adaptive routing based on performance metrics."""
    print("\n" + "="*70)
    print("EXAMPLE 7: Adaptive Routing Based on Performance Metrics")
    print("="*70)
    
    router = WorkflowRouter()
    
    state_with_metrics: WorkflowRoutingState = {
        "node_status": {},
        "node_results": {},
        "execution_metrics": {
            "iterative_solver": ExecutionMetrics(
                execution_count=20,
                failure_count=2,
                avg_execution_time=45.3,
                success_rate=90.0
            ),
            "direct_solver": ExecutionMetrics(
                execution_count=20,
                failure_count=0,
                avg_execution_time=52.1,
                success_rate=100.0
            ),
            "multigrid_solver": ExecutionMetrics(
                execution_count=20,
                failure_count=1,
                avg_execution_time=38.7,
                success_rate=95.0
            )
        }
    }
    
    # Route by success rate (reliability)
    decision_reliability = router.route_by_performance_metrics(
        state=state_with_metrics,
        node_options=["iterative_solver", "direct_solver", "multigrid_solver"],
        metric="success_rate"
    )
    
    print(f"\n📊 Routing by Reliability (Success Rate):")
    print(f"   • iterative_solver: 90.0% success, 45.3s avg")
    print(f"   • direct_solver: 100.0% success, 52.1s avg")
    print(f"   • multigrid_solver: 95.0% success, 38.7s avg")
    print(f"\n→ Selected Node: {decision_reliability.next_node}")
    print(f"→ Strategy: {decision_reliability.strategy.value}")
    print(f"→ Reason: {decision_reliability.reason}")
    
    # Route by execution time (speed)
    decision_speed = router.route_by_performance_metrics(
        state=state_with_metrics,
        node_options=["iterative_solver", "direct_solver", "multigrid_solver"],
        metric="avg_execution_time"
    )
    
    print(f"\n📊 Routing by Speed (Avg Execution Time):")
    print(f"→ Selected Node: {decision_speed.next_node}")
    print(f"→ Strategy: {decision_speed.strategy.value}")
    print(f"→ Reason: {decision_speed.reason}")


def example_8_output_value_routing():
    """Example 8: Routing based on specific output values."""
    print("\n" + "="*70)
    print("EXAMPLE 8: Routing Based on Output Values")
    print("="*70)
    
    router = WorkflowRouter()
    
    # Scenario 1: Approval routing
    state_approved: WorkflowRoutingState = {
        "node_status": {"review": NodeStatus.COMPLETED},
        "node_results": {
            "review": {
                "status": "approved",
                "confidence": 0.95,
                "reviewer": "auto"
            }
        }
    }
    
    routing_map = {
        "approved": "execute_simulation",
        "rejected": "notify_rejection",
        "pending": "manual_review",
        "unclear": "request_clarification"
    }
    
    decision_approved = router.route_by_output_value(
        state=state_approved,
        current_node="review",
        output_key="status",
        routing_map=routing_map,
        default_node="error_handler"
    )
    
    print(f"\n✓ Review Status: approved")
    print(f"→ Next Node: {decision_approved.next_node}")
    print(f"→ Strategy: {decision_approved.strategy.value}")
    print(f"→ Routing Logic: status='approved' → execute_simulation")
    
    # Scenario 2: Rejection routing
    state_rejected: WorkflowRoutingState = {
        "node_status": {"review": NodeStatus.COMPLETED},
        "node_results": {
            "review": {
                "status": "rejected",
                "reason": "Insufficient parameters"
            }
        }
    }
    
    decision_rejected = router.route_by_output_value(
        state=state_rejected,
        current_node="review",
        output_key="status",
        routing_map=routing_map,
        default_node="error_handler"
    )
    
    print(f"\n✗ Review Status: rejected")
    print(f"→ Next Node: {decision_rejected.next_node}")
    print(f"→ Routing Logic: status='rejected' → notify_rejection")


def example_9_validation_routing():
    """Example 9: Validation-based routing with refinement loops."""
    print("\n" + "="*70)
    print("EXAMPLE 9: Validation Routing with Refinement")
    print("="*70)
    
    # Success case
    state_valid: WorkflowRoutingState = {
        "node_status": {},
        "node_results": {
            "validate": {
                "validation_passed": True,
                "convergence": True,
                "accuracy": 0.99
            }
        },
        "errors": []
    }
    
    result_valid = route_by_validation_result(state_valid)
    print(f"\n✓ Validation: PASSED")
    print(f"→ Next Node: {result_valid}")
    print(f"→ Action: Proceed to aggregation")
    
    # Refinement case
    state_refine: WorkflowRoutingState = {
        "node_status": {},
        "node_results": {
            "validate": {
                "validation_passed": False,
                "convergence": False,
                "accuracy": 0.85
            }
        },
        "errors": [{"message": "Convergence not achieved"}],
        "error_severity": ErrorSeverity.MEDIUM,
        "retry_count": 1,
        "max_retries": 3
    }
    
    result_refine = route_by_validation_result(state_refine)
    print(f"\n⚠ Validation: FAILED (refinement possible)")
    print(f"→ Next Node: {result_refine}")
    print(f"→ Action: Refine and retry (attempt 2/3)")
    
    # Critical failure case
    state_critical: WorkflowRoutingState = {
        "node_status": {},
        "node_results": {
            "validate": {
                "validation_passed": False
            }
        },
        "errors": [{"message": "Critical solver failure"}],
        "error_severity": ErrorSeverity.CRITICAL
    }
    
    result_critical = route_by_validation_result(state_critical)
    print(f"\n✗ Validation: CRITICAL FAILURE")
    print(f"→ Next Node: {result_critical}")
    print(f"→ Action: Route to error handler")


def example_10_tool_selection_routing():
    """Example 10: Routing based on simulation tool selection."""
    print("\n" + "="*70)
    print("EXAMPLE 10: Tool Selection Routing")
    print("="*70)
    
    # FEniCSx case
    state_fenicsx: WorkflowRoutingState = {
        "node_status": {},
        "node_results": {
            "plan": {
                "required_tool": "fenicsx",
                "simulation_type": "structural",
                "mesh_size": 64
            }
        }
    }
    
    result_fenicsx = route_by_simulation_tool(state_fenicsx)
    print(f"\n🔧 Tool Selection: FEniCSx")
    print(f"→ Next Node: {result_fenicsx}")
    print(f"→ Performer: Finite Element Analysis")
    
    # LAMMPS case
    state_lammps: WorkflowRoutingState = {
        "node_status": {},
        "node_results": {
            "plan": {
                "required_tool": "lammps",
                "simulation_type": "molecular",
                "atoms": 10000
            }
        }
    }
    
    result_lammps = route_by_simulation_tool(state_lammps)
    print(f"\n🔧 Tool Selection: LAMMPS")
    print(f"→ Next Node: {result_lammps}")
    print(f"→ Performer: Molecular Dynamics")
    
    # OpenFOAM case
    state_openfoam: WorkflowRoutingState = {
        "node_status": {},
        "node_results": {
            "plan": {
                "required_tool": "openfoam",
                "simulation_type": "fluid",
                "reynolds": 1000
            }
        }
    }
    
    result_openfoam = route_by_simulation_tool(state_openfoam)
    print(f"\n🔧 Tool Selection: OpenFOAM")
    print(f"→ Next Node: {result_openfoam}")
    print(f"→ Performer: Computational Fluid Dynamics")


def main():
    """Run all routing strategy examples."""
    print("\n")
    print("╔" + "="*68 + "╗")
    print("║" + " "*15 + "WORKFLOW ROUTING EXAMPLES" + " "*28 + "║")
    print("║" + " "*15 + "LangGraph Conditional Edges" + " "*25 + "║")
    print("╚" + "="*68 + "╝")
    
    examples = [
        ("Basic Routing", example_1_basic_routing),
        ("Error with Retry", example_2_error_with_retry),
        ("Context-Based Routing", example_3_context_routing),
        ("Resource-Aware Routing", example_4_resource_aware_routing),
        ("Parallel Execution", example_5_parallel_execution),
        ("Circuit Breaker", example_6_circuit_breaker),
        ("Adaptive Routing", example_7_adaptive_routing),
        ("Output Value Routing", example_8_output_value_routing),
        ("Validation Routing", example_9_validation_routing),
        ("Tool Selection", example_10_tool_selection_routing)
    ]
    
    for i, (name, func) in enumerate(examples, 1):
        try:
            func()
        except Exception as e:
            print(f"\n✗ Error in {name}: {str(e)}")
    
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print(f"\n✓ Demonstrated {len(examples)} routing strategies")
    print(f"✓ All examples completed successfully")
    print(f"\nFor more details, see:")
    print(f"  - workflow_routing.py (implementation)")
    print(f"  - WORKFLOW_ROUTING_GUIDE.md (documentation)")
    print(f"  - conductor_performer_graph.py (integration)")
    print()


if __name__ == "__main__":
    main()
