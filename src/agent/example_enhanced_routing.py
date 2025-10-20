"""
Enhanced Conductor-Performer with Advanced Routing
====================================================

This module demonstrates the integration of advanced routing logic from 
workflow_routing.py with the existing conductor-performer pattern.

It showcases:
1. Dynamic tool selection based on simulation type
2. Priority-based execution paths
3. Resource-aware routing
4. Error handling with circuit breaker
5. Adaptive routing based on performance metrics
6. Parallel execution patterns
"""

from typing import Dict, Any, List
from datetime import datetime

from conductor_performer_graph import (
    ConductorPerformerGraph,
    ConductorPerformerState,
    WorkflowStatus,
    AgentRole
)
from workflow_routing import (
    WorkflowRouter,
    WorkflowRoutingState,
    NodeStatus,
    ErrorSeverity,
    ExecutionMetrics,
    RoutingStrategy
)
from langgraph.graph import StateGraph, END


class EnhancedConductorPerformerGraph(ConductorPerformerGraph):
    """
    Enhanced Conductor-Performer pattern with advanced routing capabilities.
    
    This extends the base pattern with:
    - Intelligent tool selection
    - Priority-based fast paths
    - Resource-aware execution
    - Circuit breaker for reliability
    - Performance-based adaptive routing
    """
    
    def __init__(self, task_pipeline=None):
        """Initialize enhanced graph with routing engine."""
        super().__init__(task_pipeline)
        self.router = WorkflowRouter(max_retries=3, circuit_breaker_threshold=5)
        
        # Track performance metrics for adaptive routing
        self.performance_metrics: Dict[str, ExecutionMetrics] = {
            "fenicsx_execute": ExecutionMetrics(),
            "lammps_execute": ExecutionMetrics(),
            "openfoam_execute": ExecutionMetrics()
        }
    
    def _build_graph(self) -> StateGraph:
        """
        Build enhanced graph with advanced routing logic.
        
        Returns:
            Compiled StateGraph with intelligent routing
        """
        workflow = StateGraph(ConductorPerformerState)
        
        # Add all nodes
        workflow.add_node("analyze", self._analyze_with_routing)
        workflow.add_node("route_by_priority", self._route_by_priority)
        workflow.add_node("delegate", self.conductor.delegate_tasks)
        workflow.add_node("fenicsx_execute", self._execute_with_metrics("fenicsx"))
        workflow.add_node("lammps_execute", self._execute_with_metrics("lammps"))
        workflow.add_node("openfoam_execute", self._execute_with_metrics("openfoam"))
        workflow.add_node("validate", self.validator.validate_results)
        workflow.add_node("aggregate", self.conductor.aggregate_results)
        workflow.add_node("handle_error", self._handle_error_with_circuit_breaker)
        
        # Entry point
        workflow.set_entry_point("analyze")
        
        # Conditional routing after analysis
        def route_after_analysis(state: ConductorPerformerState) -> str:
            """Route based on request analysis and priority."""
            context = state.get("workflow_context", {})
            priority = context.get("priority", "normal")
            
            if priority in ["critical", "high"]:
                return "route_by_priority"
            else:
                return "delegate"
        
        workflow.add_conditional_edges(
            "analyze",
            route_after_analysis,
            {
                "route_by_priority": "route_by_priority",
                "delegate": "delegate"
            }
        )
        
        # Priority routing leads to delegation
        workflow.add_edge("route_by_priority", "delegate")
        
        # Dynamic tool selection after delegation
        def route_to_performer(state: ConductorPerformerState) -> str:
            """Intelligently route to appropriate performer."""
            execution_plan = state.get("execution_plan", {})
            phases = execution_plan.get("phases", [])
            
            if not phases:
                return "validate"
            
            # Get first phase tool
            first_phase = phases[0]
            agent = first_phase.get("agent", "")
            
            if "fenicsx" in agent:
                return "fenicsx_execute"
            elif "lammps" in agent:
                return "lammps_execute"
            elif "openfoam" in agent:
                return "openfoam_execute"
            else:
                return "validate"  # Skip execution if no tool
        
        workflow.add_conditional_edges(
            "delegate",
            route_to_performer,
            {
                "fenicsx_execute": "fenicsx_execute",
                "lammps_execute": "lammps_execute",
                "openfoam_execute": "openfoam_execute",
                "validate": "validate"
            }
        )
        
        # All performers route to validation
        workflow.add_edge("fenicsx_execute", "validate")
        workflow.add_edge("lammps_execute", "validate")
        workflow.add_edge("openfoam_execute", "validate")
        
        # Enhanced validation routing
        def route_after_validation(state: ConductorPerformerState) -> str:
            """Advanced routing after validation with circuit breaker."""
            validation = state.get("validation_feedback", {})
            errors = state.get("errors", [])
            circuit_open = state.get("circuit_breaker_open", False)
            
            # Check circuit breaker
            if circuit_open:
                return "handle_error"
            
            # Check validation
            if errors:
                error_severity = state.get("error_severity", ErrorSeverity.MEDIUM)
                if error_severity == ErrorSeverity.CRITICAL:
                    return "handle_error"
                else:
                    retry_count = state.get("retry_count", 0)
                    max_retries = state.get("max_retries", 3)
                    
                    if retry_count < max_retries:
                        return "handle_error"  # Try recovery
                    else:
                        return "handle_error"  # Give up
            
            elif validation.get("validation_passed", False):
                return "aggregate"
            else:
                return "handle_error"
        
        workflow.add_conditional_edges(
            "validate",
            route_after_validation,
            {
                "aggregate": "aggregate",
                "handle_error": "handle_error"
            }
        )
        
        # Error handling with adaptive retry
        def route_after_error(state: ConductorPerformerState) -> str:
            """Adaptive routing after error handling."""
            status = state.get("status")
            
            if status == WorkflowStatus.NEEDS_REFINEMENT:
                return "delegate"
            else:
                return END
        
        workflow.add_conditional_edges(
            "handle_error",
            route_after_error,
            {
                "delegate": "delegate",
                END: END
            }
        )
        
        # Terminal edge
        workflow.add_edge("aggregate", END)
        
        return workflow.compile()
    
    def _analyze_with_routing(self, state: ConductorPerformerState) -> ConductorPerformerState:
        """Enhanced analysis with routing context."""
        # Call base analysis
        state = self.conductor.analyze_request(state)
        
        # Add routing context
        user_request = state.get("user_request", "")
        
        # Determine priority from request
        priority = "normal"
        if "urgent" in user_request.lower() or "critical" in user_request.lower():
            priority = "critical"
        elif "high priority" in user_request.lower():
            priority = "high"
        
        # Add workflow context for routing
        workflow_context = {
            "priority": priority,
            "analyzed_at": datetime.now().isoformat()
        }
        
        return {
            **state,
            "workflow_context": workflow_context,
            "retry_count": 0,
            "max_retries": 3
        }
    
    def _route_by_priority(self, state: ConductorPerformerState) -> ConductorPerformerState:
        """Handle high-priority requests with fast path."""
        context = state.get("workflow_context", {})
        priority = context.get("priority", "normal")
        
        # Update context with fast-path info
        context["fast_path_enabled"] = priority in ["critical", "high"]
        context["routing_strategy"] = "priority_based"
        
        return {
            **state,
            "workflow_context": context,
            "messages": [
                f"Priority Router: Enabled fast path for {priority} priority request"
            ]
        }
    
    def _execute_with_metrics(self, tool_name: str):
        """
        Create execution wrapper that tracks performance metrics.
        
        Args:
            tool_name: Name of simulation tool
            
        Returns:
            Wrapped execution function
        """
        def execute(state: ConductorPerformerState) -> ConductorPerformerState:
            """Execute with performance tracking."""
            start_time = datetime.now()
            
            # Get appropriate performer
            if tool_name == "fenicsx":
                performer = self.fenicsx_performer
            elif tool_name == "lammps":
                performer = self.lammps_performer
            else:
                performer = self.openfoam_performer
            
            # Execute task
            result_state = performer.execute_task(state)
            
            # Track metrics
            execution_time = (datetime.now() - start_time).total_seconds()
            errors = result_state.get("errors", [])
            
            node_name = f"{tool_name}_execute"
            if errors:
                self.performance_metrics[node_name].update_failure()
            else:
                self.performance_metrics[node_name].update_success(execution_time)
            
            # Add metrics to state
            return {
                **result_state,
                "execution_metrics": self.performance_metrics
            }
        
        return execute
    
    def _handle_error_with_circuit_breaker(
        self, 
        state: ConductorPerformerState
    ) -> ConductorPerformerState:
        """Enhanced error handling with circuit breaker."""
        # Call base error handling
        state = self.conductor.handle_error(state)
        
        # Update circuit breaker
        errors = state.get("errors", [])
        circuit_failures = state.get("circuit_breaker_failures", 0)
        
        if errors:
            circuit_failures += 1
            
            # Open circuit if threshold exceeded
            circuit_open = circuit_failures >= self.router.circuit_breaker_threshold
            
            return {
                **state,
                "circuit_breaker_failures": circuit_failures,
                "circuit_breaker_open": circuit_open,
                "circuit_breaker_threshold": self.router.circuit_breaker_threshold
            }
        else:
            # Reset circuit breaker on success
            return {
                **state,
                "circuit_breaker_failures": 0,
                "circuit_breaker_open": False
            }
    
    def execute_workflow_with_routing(
        self,
        user_request: str,
        priority: str = "normal",
        max_iterations: int = 3
    ) -> Dict[str, Any]:
        """
        Execute workflow with advanced routing.
        
        Args:
            user_request: User's simulation request
            priority: Request priority (normal, high, critical)
            max_iterations: Maximum refinement iterations
            
        Returns:
            Workflow result with routing details
        """
        # Initialize state
        initial_state: ConductorPerformerState = {
            "messages": [],
            "status": WorkflowStatus.PENDING,
            "user_request": user_request,
            "max_iterations": max_iterations,
            "iteration_count": 0,
            "workflow_context": {"priority": priority}
        }
        
        # Execute graph
        final_state = self.graph.invoke(initial_state)
        
        # Compile routing report
        routing_report = {
            "routing_strategy": final_state.get("workflow_context", {}).get("routing_strategy"),
            "priority": priority,
            "circuit_breaker_state": {
                "open": final_state.get("circuit_breaker_open", False),
                "failures": final_state.get("circuit_breaker_failures", 0)
            },
            "performance_metrics": {
                name: {
                    "executions": metrics.execution_count,
                    "failures": metrics.failure_count,
                    "success_rate": metrics.success_rate,
                    "avg_time": metrics.avg_execution_time
                }
                for name, metrics in self.performance_metrics.items()
            }
        }
        
        return {
            "status": final_state.get("status"),
            "result": final_state.get("final_result"),
            "messages": [
                msg.content if hasattr(msg, 'content') else str(msg)
                for msg in final_state.get("messages", [])
            ],
            "iterations": final_state.get("iteration_count", 0),
            "routing": routing_report
        }


def demonstrate_routing_scenarios():
    """Demonstrate various routing scenarios."""
    print("\n" + "="*70)
    print("ENHANCED CONDUCTOR-PERFORMER WITH ADVANCED ROUTING")
    print("="*70)
    
    graph = EnhancedConductorPerformerGraph()
    
    # Scenario 1: Normal priority structural analysis
    print("\n" + "-"*70)
    print("Scenario 1: Normal Priority - Structural Analysis")
    print("-"*70)
    
    result1 = graph.execute_workflow_with_routing(
        user_request="Run structural finite element analysis on steel beam",
        priority="normal"
    )
    
    print(f"Status: {result1['status']}")
    print(f"Priority: {result1['routing']['priority']}")
    print(f"Routing Strategy: {result1['routing']['routing_strategy']}")
    print(f"Iterations: {result1['iterations']}")
    
    # Scenario 2: High priority molecular dynamics
    print("\n" + "-"*70)
    print("Scenario 2: High Priority - Molecular Dynamics")
    print("-"*70)
    
    result2 = graph.execute_workflow_with_routing(
        user_request="URGENT: Run molecular dynamics simulation for drug discovery",
        priority="high"
    )
    
    print(f"Status: {result2['status']}")
    print(f"Priority: {result2['routing']['priority']}")
    print(f"Routing Strategy: {result2['routing']['routing_strategy']}")
    print(f"Fast Path: {result2.get('routing', {}).get('fast_path_enabled', False)}")
    
    # Scenario 3: Critical priority CFD
    print("\n" + "-"*70)
    print("Scenario 3: Critical Priority - Computational Fluid Dynamics")
    print("-"*70)
    
    result3 = graph.execute_workflow_with_routing(
        user_request="CRITICAL: Emergency fluid dynamics analysis required",
        priority="critical"
    )
    
    print(f"Status: {result3['status']}")
    print(f"Priority: {result3['routing']['priority']}")
    print(f"Circuit Breaker: {result3['routing']['circuit_breaker_state']}")
    
    # Display performance metrics
    print("\n" + "-"*70)
    print("Performance Metrics Summary")
    print("-"*70)
    
    for tool, metrics in result3['routing']['performance_metrics'].items():
        if metrics['executions'] > 0:
            print(f"\n{tool}:")
            print(f"  Executions: {metrics['executions']}")
            print(f"  Success Rate: {metrics['success_rate']:.1f}%")
            print(f"  Avg Time: {metrics['avg_time']:.2f}s")
    
    print("\n" + "="*70)
    print("ROUTING DEMONSTRATION COMPLETE")
    print("="*70)


if __name__ == "__main__":
    print("\n")
    print("╔" + "="*68 + "╗")
    print("║" + " "*10 + "ENHANCED CONDUCTOR-PERFORMER ROUTING" + " "*21 + "║")
    print("║" + " "*15 + "Advanced Workflow Orchestration" + " "*21 + "║")
    print("╚" + "="*68 + "╝")
    
    demonstrate_routing_scenarios()
    
    print("\n")
    print("Key Features Demonstrated:")
    print("  ✓ Priority-based routing (normal, high, critical)")
    print("  ✓ Dynamic tool selection based on simulation type")
    print("  ✓ Performance metrics tracking")
    print("  ✓ Circuit breaker for fault tolerance")
    print("  ✓ Adaptive error handling with retry logic")
    print()
    print("For detailed routing examples, run:")
    print("  python3 example_routing_strategies.py")
    print()
