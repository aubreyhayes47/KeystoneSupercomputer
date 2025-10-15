"""
LangGraph Conductor-Performer Pattern for Multi-Agent Orchestration
===================================================================

This module implements the Conductor-Performer pattern using LangGraph for
orchestrating multi-agent simulation workflows. The pattern separates:

- **Conductor Agent**: Central orchestrator responsible for task planning,
  delegation, error handling, and feedback loops
- **Performer Agents**: Specialized agents for different simulation functions
  (FEniCSx, LAMMPS, OpenFOAM) that execute domain-specific tasks

Architecture:
    The graph implements a hub-and-spoke pattern where the Conductor:
    1. Analyzes incoming requests and creates execution plans
    2. Delegates tasks to appropriate Performer agents
    3. Monitors execution and handles errors
    4. Collects results and provides feedback
    5. Iterates based on validation and refinement needs

Example:
    >>> from conductor_performer_graph import ConductorPerformerGraph
    >>> graph = ConductorPerformerGraph()
    >>> result = graph.execute_workflow({
    ...     "task": "run_structural_analysis",
    ...     "parameters": {"material": "steel", "mesh_size": 64}
    ... })
"""

from typing import TypedDict, Annotated, List, Dict, Any, Optional, Literal
from typing_extensions import NotRequired
import operator
from datetime import datetime
from enum import Enum

from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

# Import existing pipeline components
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from task_pipeline import TaskPipeline, TaskStatus


class AgentRole(str, Enum):
    """Agent role identifiers."""
    CONDUCTOR = "conductor"
    FENICSX_PERFORMER = "fenicsx_performer"
    LAMMPS_PERFORMER = "lammps_performer"
    OPENFOAM_PERFORMER = "openfoam_performer"
    VALIDATOR = "validator"


class WorkflowStatus(str, Enum):
    """Workflow execution status."""
    PENDING = "pending"
    PLANNING = "planning"
    EXECUTING = "executing"
    VALIDATING = "validating"
    COMPLETED = "completed"
    FAILED = "failed"
    NEEDS_REFINEMENT = "needs_refinement"


class ConductorPerformerState(TypedDict):
    """
    State schema for the Conductor-Performer graph.
    
    This state is passed between nodes and accumulates information
    throughout the workflow execution.
    """
    # Conversation history
    messages: Annotated[List[Any], operator.add]
    
    # Current workflow status
    status: WorkflowStatus
    
    # Original user request
    user_request: str
    
    # Execution plan created by Conductor
    execution_plan: NotRequired[Dict[str, Any]]
    
    # Tasks delegated to Performers
    delegated_tasks: NotRequired[List[Dict[str, Any]]]
    
    # Results from Performer agents
    performer_results: NotRequired[Dict[str, Any]]
    
    # Validation feedback
    validation_feedback: NotRequired[Dict[str, Any]]
    
    # Error information
    errors: NotRequired[List[Dict[str, Any]]]
    
    # Number of refinement iterations
    iteration_count: NotRequired[int]
    
    # Maximum refinement iterations allowed
    max_iterations: NotRequired[int]
    
    # Final workflow result
    final_result: NotRequired[Dict[str, Any]]


class ConductorAgent:
    """
    Conductor Agent - Central orchestrator for workflow execution.
    
    Responsibilities:
    - Analyze user requests and create execution plans
    - Select appropriate Performer agents for each task
    - Sequence task execution (sequential vs parallel)
    - Handle errors and implement retry logic
    - Coordinate feedback loops and refinements
    - Aggregate and present final results
    """
    
    def __init__(self, task_pipeline: Optional[TaskPipeline] = None):
        """Initialize Conductor with access to task execution pipeline."""
        self.task_pipeline = task_pipeline or TaskPipeline()
        self.role = AgentRole.CONDUCTOR
    
    def analyze_request(self, state: ConductorPerformerState) -> ConductorPerformerState:
        """
        Analyze user request and create execution plan.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state with execution plan
        """
        user_request = state["user_request"]
        
        # Create execution plan based on request analysis
        execution_plan = {
            "plan_id": f"plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "created_at": datetime.now().isoformat(),
            "request": user_request,
            "phases": []
        }
        
        # Simple keyword-based task identification
        # In production, this would use LLM-based analysis
        if "structural" in user_request.lower() or "finite element" in user_request.lower():
            execution_plan["phases"].append({
                "phase": 1,
                "agent": AgentRole.FENICSX_PERFORMER.value,
                "task": "finite_element_analysis",
                "parallel": False
            })
        
        if "molecular" in user_request.lower() or "dynamics" in user_request.lower():
            execution_plan["phases"].append({
                "phase": 2,
                "agent": AgentRole.LAMMPS_PERFORMER.value,
                "task": "molecular_dynamics",
                "parallel": False
            })
        
        if "fluid" in user_request.lower() or "cfd" in user_request.lower():
            execution_plan["phases"].append({
                "phase": 3,
                "agent": AgentRole.OPENFOAM_PERFORMER.value,
                "task": "computational_fluid_dynamics",
                "parallel": False
            })
        
        # Update state - return new dict to avoid mutation issues
        return {
            **state,
            "execution_plan": execution_plan,
            "status": WorkflowStatus.PLANNING,
            "iteration_count": state.get("iteration_count", 0),
            "max_iterations": state.get("max_iterations", 3),
            "messages": [AIMessage(content=f"Conductor: Created execution plan with {len(execution_plan['phases'])} phases")]
        }
    
    def delegate_tasks(self, state: ConductorPerformerState) -> ConductorPerformerState:
        """
        Delegate tasks to appropriate Performer agents.
        
        Args:
            state: Current workflow state with execution plan
            
        Returns:
            Updated state with delegated tasks
        """
        execution_plan = state.get("execution_plan", {})
        delegated_tasks = []
        
        for phase in execution_plan.get("phases", []):
            task = {
                "task_id": f"task_{phase['phase']}",
                "agent": phase["agent"],
                "task_type": phase["task"],
                "status": "delegated",
                "delegated_at": datetime.now().isoformat()
            }
            delegated_tasks.append(task)
        
        return {
            **state,
            "delegated_tasks": delegated_tasks,
            "status": WorkflowStatus.EXECUTING,
            "messages": [AIMessage(content=f"Conductor: Delegated {len(delegated_tasks)} tasks to Performers")]
        }
    
    def aggregate_results(self, state: ConductorPerformerState) -> ConductorPerformerState:
        """
        Aggregate results from all Performer agents.
        
        Args:
            state: Current workflow state with performer results
            
        Returns:
            Updated state with aggregated final result
        """
        performer_results = state.get("performer_results", {})
        validation_feedback = state.get("validation_feedback", {})
        
        final_result = {
            "workflow_id": state.get("execution_plan", {}).get("plan_id"),
            "status": "completed",
            "performer_results": performer_results,
            "validation": validation_feedback,
            "completed_at": datetime.now().isoformat()
        }
        
        return {
            **state,
            "final_result": final_result,
            "status": WorkflowStatus.COMPLETED,
            "messages": [AIMessage(content="Conductor: Workflow completed successfully")]
        }
    
    def handle_error(self, state: ConductorPerformerState) -> ConductorPerformerState:
        """
        Handle errors and implement retry/recovery logic.
        
        Args:
            state: Current workflow state with error information
            
        Returns:
            Updated state with error handling decisions
        """
        errors = state.get("errors", [])
        iteration_count = state.get("iteration_count", 0)
        max_iterations = state.get("max_iterations", 3)
        
        if iteration_count < max_iterations:
            # Retry with refinement
            return {
                **state,
                "status": WorkflowStatus.NEEDS_REFINEMENT,
                "iteration_count": iteration_count + 1,
                "messages": [AIMessage(content=f"Conductor: Attempting refinement (iteration {iteration_count + 1}/{max_iterations})")]
            }
        else:
            # Max iterations reached, mark as failed
            return {
                **state,
                "status": WorkflowStatus.FAILED,
                "final_result": {
                    "status": "failed",
                    "errors": errors,
                    "message": "Maximum refinement iterations exceeded"
                },
                "messages": [AIMessage(content="Conductor: Workflow failed after maximum refinement attempts")]
            }


class PerformerAgent:
    """
    Base Performer Agent - Executes domain-specific simulation tasks.
    
    Each Performer is specialized for a specific simulation tool and
    understands how to execute tasks using that tool's capabilities.
    """
    
    def __init__(self, tool_name: str, task_pipeline: Optional[TaskPipeline] = None):
        """
        Initialize Performer for a specific simulation tool.
        
        Args:
            tool_name: Name of simulation tool (fenicsx, lammps, openfoam)
            task_pipeline: Task execution pipeline
        """
        self.tool_name = tool_name
        self.task_pipeline = task_pipeline or TaskPipeline()
        self.role = self._get_role_for_tool(tool_name)
    
    @staticmethod
    def _get_role_for_tool(tool_name: str) -> AgentRole:
        """Map tool name to agent role."""
        mapping = {
            "fenicsx": AgentRole.FENICSX_PERFORMER,
            "lammps": AgentRole.LAMMPS_PERFORMER,
            "openfoam": AgentRole.OPENFOAM_PERFORMER
        }
        return mapping.get(tool_name.lower(), AgentRole.FENICSX_PERFORMER)
    
    def execute_task(self, state: ConductorPerformerState) -> ConductorPerformerState:
        """
        Execute simulation task for this Performer's domain.
        
        Args:
            state: Current workflow state with delegated tasks
            
        Returns:
            Updated state with execution results
        """
        # Find tasks delegated to this performer
        delegated_tasks = state.get("delegated_tasks", [])
        my_tasks = [t for t in delegated_tasks if self.role.value in t.get("agent", "")]
        
        if not my_tasks:
            return state
        
        # Get or initialize performer_results
        performer_results = dict(state.get("performer_results", {}))
        new_messages = []
        errors = list(state.get("errors", []))
        
        # Execute each task
        for task in my_tasks:
            try:
                # In a real implementation, this would execute the actual simulation
                # For now, we simulate successful execution
                result = {
                    "task_id": task["task_id"],
                    "performer": self.role.value,
                    "status": "completed",
                    "execution_time": 10.5,  # Simulated
                    "output": f"Simulation completed using {self.tool_name}",
                    "completed_at": datetime.now().isoformat()
                }
                
                performer_results[task["task_id"]] = result
                new_messages.append(
                    AIMessage(content=f"{self.role.value}: Completed {task['task_id']}")
                )
                
            except Exception as e:
                # Record error
                error = {
                    "task_id": task["task_id"],
                    "performer": self.role.value,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
                errors.append(error)
                new_messages.append(
                    AIMessage(content=f"{self.role.value}: Error in {task['task_id']}: {str(e)}")
                )
        
        return {
            **state,
            "performer_results": performer_results,
            "errors": errors,
            "messages": new_messages
        }


class ValidatorAgent:
    """
    Validator Agent - Validates workflow results and provides feedback.
    
    Responsibilities:
    - Validate simulation outputs for correctness
    - Check physical plausibility of results
    - Identify convergence issues
    - Provide feedback for refinement
    """
    
    def __init__(self):
        """Initialize Validator agent."""
        self.role = AgentRole.VALIDATOR
    
    def validate_results(self, state: ConductorPerformerState) -> ConductorPerformerState:
        """
        Validate results from Performer agents.
        
        Args:
            state: Current workflow state with performer results
            
        Returns:
            Updated state with validation feedback
        """
        performer_results = state.get("performer_results", {})
        
        # Simple validation - check all tasks completed
        validation_feedback = {
            "validated_at": datetime.now().isoformat(),
            "all_tasks_completed": len(performer_results) > 0,
            "validation_passed": True,
            "feedback": []
        }
        
        # Check each result
        for task_id, result in performer_results.items():
            if result.get("status") != "completed":
                validation_feedback["validation_passed"] = False
                validation_feedback["feedback"].append({
                    "task_id": task_id,
                    "issue": "Task did not complete successfully"
                })
        
        return {
            **state,
            "validation_feedback": validation_feedback,
            "status": WorkflowStatus.VALIDATING,
            "messages": [AIMessage(content=f"Validator: Validation {'passed' if validation_feedback['validation_passed'] else 'failed'}")]
        }


class ConductorPerformerGraph:
    """
    LangGraph implementation of the Conductor-Performer pattern.
    
    This class builds and manages the workflow graph with proper
    edge routing for task sequencing and feedback loops.
    """
    
    def __init__(self, task_pipeline: Optional[TaskPipeline] = None):
        """
        Initialize the Conductor-Performer graph.
        
        Args:
            task_pipeline: Task execution pipeline (optional)
        """
        self.task_pipeline = task_pipeline or TaskPipeline()
        
        # Initialize agents
        self.conductor = ConductorAgent(self.task_pipeline)
        self.fenicsx_performer = PerformerAgent("fenicsx", self.task_pipeline)
        self.lammps_performer = PerformerAgent("lammps", self.task_pipeline)
        self.openfoam_performer = PerformerAgent("openfoam", self.task_pipeline)
        self.validator = ValidatorAgent()
        
        # Build the graph
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """
        Build the LangGraph workflow graph.
        
        Returns:
            Compiled StateGraph ready for execution
        """
        # Create the graph with our state schema
        workflow = StateGraph(ConductorPerformerState)
        
        # Add nodes for each agent and phase
        workflow.add_node("analyze", self.conductor.analyze_request)
        workflow.add_node("delegate", self.conductor.delegate_tasks)
        workflow.add_node("fenicsx_execute", self.fenicsx_performer.execute_task)
        workflow.add_node("lammps_execute", self.lammps_performer.execute_task)
        workflow.add_node("openfoam_execute", self.openfoam_performer.execute_task)
        workflow.add_node("validate", self.validator.validate_results)
        workflow.add_node("aggregate", self.conductor.aggregate_results)
        workflow.add_node("handle_error", self.conductor.handle_error)
        
        # Set entry point
        workflow.set_entry_point("analyze")
        
        # Add edges for main workflow
        workflow.add_edge("analyze", "delegate")
        workflow.add_edge("delegate", "fenicsx_execute")
        workflow.add_edge("fenicsx_execute", "lammps_execute")
        workflow.add_edge("lammps_execute", "openfoam_execute")
        workflow.add_edge("openfoam_execute", "validate")
        
        # Add conditional edges after validation
        def should_continue_after_validation(state: ConductorPerformerState) -> str:
            """Determine next step after validation."""
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
        
        # Add conditional edges after error handling
        def should_retry_after_error(state: ConductorPerformerState) -> str:
            """Determine if workflow should retry or end."""
            status = state.get("status")
            if status == WorkflowStatus.NEEDS_REFINEMENT:
                return "delegate"  # Retry with refinement
            else:
                return END  # Failed, end workflow
        
        workflow.add_conditional_edges(
            "handle_error",
            should_retry_after_error,
            {
                "delegate": "delegate",
                END: END
            }
        )
        
        # Aggregate leads to END
        workflow.add_edge("aggregate", END)
        
        # Compile the graph
        return workflow.compile()
    
    def execute_workflow(
        self,
        user_request: str,
        max_iterations: int = 3
    ) -> Dict[str, Any]:
        """
        Execute a complete workflow using the Conductor-Performer pattern.
        
        Args:
            user_request: User's simulation request
            max_iterations: Maximum refinement iterations
            
        Returns:
            Final workflow result with all execution details
        """
        # Initialize state
        initial_state: ConductorPerformerState = {
            "messages": [HumanMessage(content=user_request)],
            "status": WorkflowStatus.PENDING,
            "user_request": user_request,
            "max_iterations": max_iterations,
            "iteration_count": 0
        }
        
        # Execute the graph
        final_state = self.graph.invoke(initial_state)
        
        # Return the final result
        return {
            "status": final_state.get("status"),
            "result": final_state.get("final_result"),
            "messages": [msg.content if hasattr(msg, 'content') else str(msg) 
                        for msg in final_state.get("messages", [])],
            "iterations": final_state.get("iteration_count", 0)
        }
    
    def get_graph_visualization(self) -> str:
        """
        Get a text representation of the graph structure.
        
        Returns:
            String representation of the graph for documentation
        """
        return """
Conductor-Performer Workflow Graph:

    [START]
       ↓
   analyze (Conductor: Analyze request & create plan)
       ↓
   delegate (Conductor: Delegate tasks to Performers)
       ↓
   fenicsx_execute (FEniCSx Performer: Execute FEM tasks)
       ↓
   lammps_execute (LAMMPS Performer: Execute MD tasks)
       ↓
   openfoam_execute (OpenFOAM Performer: Execute CFD tasks)
       ↓
   validate (Validator: Check results)
       ↓
   [Decision Point]
       ├─→ aggregate (Conductor: Success path)
       │      ↓
       │    [END]
       │
       └─→ handle_error (Conductor: Error/refinement path)
              ↓
           [Decision Point]
              ├─→ delegate (Retry with refinement)
              │      ↓
              │   (loops back to performer execution)
              │
              └─→ [END] (Max iterations reached)
"""


# Example workflows for common simulation scenarios
EXAMPLE_WORKFLOWS = {
    "structural_analysis": {
        "description": "Finite element structural analysis workflow",
        "request": "Run structural analysis for steel beam under load with mesh size 64",
        "expected_performers": ["fenicsx_performer"],
        "steps": [
            "Conductor analyzes request and identifies FEniCSx task",
            "FEniCSx Performer executes finite element analysis",
            "Validator checks convergence and physical plausibility",
            "Conductor aggregates and returns results"
        ]
    },
    "multiphysics_workflow": {
        "description": "Multi-physics simulation combining structural and fluid dynamics",
        "request": "Perform coupled structural and fluid dynamics analysis",
        "expected_performers": ["fenicsx_performer", "openfoam_performer"],
        "steps": [
            "Conductor creates sequential execution plan",
            "FEniCSx Performer runs structural analysis",
            "Results feed into OpenFOAM for fluid dynamics",
            "Validator ensures coupling consistency",
            "Conductor aggregates multi-physics results"
        ]
    },
    "parameter_sweep": {
        "description": "Parameter sweep across multiple simulation configurations",
        "request": "Run molecular dynamics simulation with parameter sweep",
        "expected_performers": ["lammps_performer"],
        "steps": [
            "Conductor creates parallel execution plan",
            "LAMMPS Performer executes multiple configurations",
            "Validator checks all runs completed successfully",
            "Conductor aggregates sweep results"
        ]
    },
    "error_recovery": {
        "description": "Workflow with error handling and refinement",
        "request": "Run CFD simulation with automatic mesh refinement if needed",
        "expected_performers": ["openfoam_performer"],
        "steps": [
            "Conductor delegates to OpenFOAM Performer",
            "Initial simulation detects convergence issues",
            "Validator provides refinement feedback",
            "Conductor triggers mesh refinement iteration",
            "OpenFOAM Performer re-runs with refined mesh",
            "Workflow completes successfully"
        ]
    }
}


if __name__ == "__main__":
    # Example usage
    print("Conductor-Performer Graph Initialized")
    print("=" * 60)
    
    # Create the graph
    graph = ConductorPerformerGraph()
    
    # Print graph structure
    print(graph.get_graph_visualization())
    
    # Example workflow execution
    print("\nExample Workflow Execution:")
    print("-" * 60)
    
    result = graph.execute_workflow(
        user_request="Run structural finite element analysis for steel component"
    )
    
    print(f"Status: {result['status']}")
    print(f"Iterations: {result['iterations']}")
    print("\nMessages:")
    for msg in result['messages']:
        print(f"  - {msg}")
