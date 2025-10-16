"""
Simulation Workflow Agents for Multi-Stage Workflow Orchestration
==================================================================

This module defines specialized agents for each stage of the simulation workflow:
1. RequirementAnalysisAgent - Analyze and validate simulation requirements
2. PlanningAgent - Plan simulation workflows and resource allocation
3. SimulationAgent - Execute simulations and manage compute resources
4. VisualizationAgent - Generate visualizations from simulation results
5. ValidationAgent - Validate results against expected outcomes
6. SummarizationAgent - Summarize findings and generate reports

Each agent has clearly defined:
- Purpose and responsibilities
- Input and output specifications
- Communication protocols with other agents
- Lifecycle management within the LangGraph system

This extends the existing Conductor-Performer pattern to provide more specialized
workflow stage management for complex simulation scenarios.
"""

from typing import TypedDict, Annotated, List, Dict, Any, Optional, Literal
from typing_extensions import NotRequired
import operator
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field
import json

from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

# Import existing pipeline components
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from task_pipeline import TaskPipeline, TaskStatus


class WorkflowStage(str, Enum):
    """Simulation workflow stages."""
    REQUIREMENT_ANALYSIS = "requirement_analysis"
    PLANNING = "planning"
    SIMULATION = "simulation"
    VISUALIZATION = "visualization"
    VALIDATION = "validation"
    SUMMARIZATION = "summarization"


class AgentStatus(str, Enum):
    """Agent execution status."""
    IDLE = "idle"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    WAITING = "waiting"


@dataclass
class AgentInput:
    """Standard input format for workflow agents."""
    stage: WorkflowStage
    data: Dict[str, Any]
    context: Dict[str, Any] = field(default_factory=dict)
    previous_stage_output: Optional[Dict[str, Any]] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class AgentOutput:
    """Standard output format for workflow agents."""
    stage: WorkflowStage
    status: AgentStatus
    data: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert output to dictionary."""
        return {
            "stage": self.stage.value,
            "status": self.status.value,
            "data": self.data,
            "metadata": self.metadata,
            "errors": self.errors,
            "warnings": self.warnings,
            "timestamp": self.timestamp
        }


class SimulationWorkflowState(TypedDict):
    """
    State schema for simulation workflow graph.
    
    Tracks the complete workflow lifecycle across all stages.
    """
    # Conversation and message history
    messages: Annotated[List[Any], operator.add]
    
    # Current workflow stage
    current_stage: WorkflowStage
    
    # Overall workflow status
    status: AgentStatus
    
    # Original user request
    user_request: str
    
    # Stage outputs
    requirement_analysis: NotRequired[Dict[str, Any]]
    planning: NotRequired[Dict[str, Any]]
    simulation: NotRequired[Dict[str, Any]]
    visualization: NotRequired[Dict[str, Any]]
    validation: NotRequired[Dict[str, Any]]
    summarization: NotRequired[Dict[str, Any]]
    
    # Workflow metadata
    workflow_id: NotRequired[str]
    started_at: NotRequired[str]
    completed_at: NotRequired[str]
    
    # Error tracking
    errors: NotRequired[List[Dict[str, Any]]]


class RequirementAnalysisAgent:
    """
    Requirement Analysis Agent
    ==========================
    
    **Purpose:**
    Analyze and validate simulation requirements from user requests. Extract key
    parameters, validate inputs, identify required resources, and establish success
    criteria for the simulation workflow.
    
    **Responsibilities:**
    - Parse user requests and extract simulation parameters
    - Validate parameter ranges and constraints
    - Identify required simulation tools and resources
    - Define success criteria and validation metrics
    - Detect potential issues or missing requirements
    - Estimate computational resource needs
    
    **Inputs:**
    - user_request: Natural language description of simulation needs
    - context: Additional context (domain, constraints, preferences)
    
    **Outputs:**
    - simulation_type: Type of simulation (structural, fluid, molecular, etc.)
    - parameters: Validated simulation parameters
    - constraints: Physical and computational constraints
    - required_tools: List of required simulation tools
    - success_criteria: Metrics for validation
    - resource_estimate: Estimated CPU, memory, time requirements
    - warnings: Potential issues or missing information
    
    **Communication Protocol:**
    - Receives: Initial user request from workflow initiator
    - Sends to: PlanningAgent with validated requirements
    - Error handling: Returns warnings for incomplete/invalid requirements
    
    **Lifecycle:**
    1. Initialize with user request
    2. Parse and extract requirements
    3. Validate against known constraints
    4. Estimate resource needs
    5. Produce structured requirement specification
    6. Pass to PlanningAgent for workflow planning
    
    **Example Scenarios:**
    
    Scenario 1: Structural Analysis
    ```
    Input: "Run finite element analysis on a steel beam under 10kN load"
    Output: {
        "simulation_type": "structural_analysis",
        "parameters": {
            "material": "steel",
            "load": {"value": 10, "unit": "kN"},
            "mesh_size": 64  # default
        },
        "required_tools": ["fenicsx"],
        "success_criteria": {
            "max_displacement": {"threshold": 50, "unit": "mm"},
            "max_stress": {"threshold": 250, "unit": "MPa"}
        },
        "resource_estimate": {
            "cpu_cores": 4,
            "memory_gb": 8,
            "time_minutes": 15
        }
    }
    ```
    
    Scenario 2: Multi-Physics Simulation
    ```
    Input: "Couple structural and fluid analysis for wing design"
    Output: {
        "simulation_type": "multiphysics",
        "phases": ["structural", "fluid", "coupled"],
        "parameters": {
            "geometry": "wing_profile",
            "flow_velocity": {"value": 50, "unit": "m/s"}
        },
        "required_tools": ["fenicsx", "openfoam"],
        "coupling": "two_way",
        "resource_estimate": {
            "cpu_cores": 16,
            "memory_gb": 32,
            "time_hours": 2
        }
    }
    ```
    """
    
    def __init__(self):
        """Initialize RequirementAnalysisAgent."""
        self.stage = WorkflowStage.REQUIREMENT_ANALYSIS
        self.name = "RequirementAnalysisAgent"
        
        # Known simulation types and their requirements
        self.simulation_types = {
            "structural": {
                "tools": ["fenicsx"],
                "required_params": ["material", "geometry"],
                "optional_params": ["mesh_size", "solver_type"]
            },
            "fluid": {
                "tools": ["openfoam"],
                "required_params": ["flow_conditions", "boundary_conditions"],
                "optional_params": ["turbulence_model", "time_step"]
            },
            "molecular": {
                "tools": ["lammps"],
                "required_params": ["force_field", "initial_structure"],
                "optional_params": ["temperature", "pressure", "ensemble"]
            },
            "multiphysics": {
                "tools": ["fenicsx", "openfoam"],
                "required_params": ["coupling_type", "domains"],
                "optional_params": ["iteration_scheme"]
            }
        }
    
    def process(self, agent_input: AgentInput) -> AgentOutput:
        """
        Process requirement analysis.
        
        Args:
            agent_input: Input specification with user request
            
        Returns:
            AgentOutput with validated requirements
        """
        user_request = agent_input.data.get("user_request", "")
        context = agent_input.context
        
        # Analyze request and extract requirements
        requirements = self._analyze_request(user_request, context)
        
        # Validate requirements
        validation_result = self._validate_requirements(requirements)
        
        # Estimate resources
        resource_estimate = self._estimate_resources(requirements)
        
        # Create output
        output_data = {
            **requirements,
            "resource_estimate": resource_estimate,
            "validated": validation_result["is_valid"]
        }
        
        status = AgentStatus.COMPLETED if validation_result["is_valid"] else AgentStatus.FAILED
        
        return AgentOutput(
            stage=self.stage,
            status=status,
            data=output_data,
            metadata={
                "agent": self.name,
                "request_length": len(user_request)
            },
            errors=validation_result.get("errors", []),
            warnings=validation_result.get("warnings", [])
        )
    
    def _analyze_request(self, request: str, context: Dict) -> Dict[str, Any]:
        """Analyze user request and extract requirements."""
        request_lower = request.lower()
        
        # Determine simulation type (order matters - check multiphysics first)
        sim_type = "structural"  # default
        if "coupled" in request_lower or "multiphysics" in request_lower:
            sim_type = "multiphysics"
        elif "fluid" in request_lower or "cfd" in request_lower:
            sim_type = "fluid"
        elif "molecular" in request_lower or "dynamics" in request_lower:
            sim_type = "molecular"
        
        # Extract parameters (keyword-based, could use LLM)
        parameters = {}
        
        # Material extraction
        materials = ["steel", "aluminum", "concrete", "composite"]
        for material in materials:
            if material in request_lower:
                parameters["material"] = material
                break
        
        # Load extraction
        if "kn" in request_lower:
            # Simple extraction, real version would use regex
            parameters["load"] = {"value": 10, "unit": "kN"}
        
        # Get default parameters for simulation type
        sim_config = self.simulation_types.get(sim_type, {})
        required_tools = sim_config.get("tools", ["fenicsx"])
        
        return {
            "simulation_type": sim_type,
            "parameters": parameters,
            "required_tools": required_tools,
            "success_criteria": self._define_success_criteria(sim_type),
            "constraints": context.get("constraints", {}),
            "original_request": request
        }
    
    def _validate_requirements(self, requirements: Dict) -> Dict[str, Any]:
        """Validate extracted requirements."""
        errors = []
        warnings = []
        
        sim_type = requirements.get("simulation_type")
        if sim_type not in self.simulation_types:
            errors.append(f"Unknown simulation type: {sim_type}")
        
        # Check for required parameters
        if sim_type in self.simulation_types:
            required_params = self.simulation_types[sim_type]["required_params"]
            params = requirements.get("parameters", {})
            
            for req_param in required_params:
                if req_param not in params:
                    warnings.append(f"Missing recommended parameter: {req_param}")
        
        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    
    def _define_success_criteria(self, sim_type: str) -> Dict[str, Any]:
        """Define success criteria based on simulation type."""
        criteria = {
            "structural": {
                "convergence": {"tolerance": 1e-6},
                "quality_metrics": ["displacement", "stress"]
            },
            "fluid": {
                "convergence": {"residuals": 1e-5},
                "quality_metrics": ["velocity", "pressure"]
            },
            "molecular": {
                "convergence": {"energy_drift": 0.01},
                "quality_metrics": ["temperature", "pressure", "energy"]
            }
        }
        return criteria.get(sim_type, {"convergence": {"default": True}})
    
    def _estimate_resources(self, requirements: Dict) -> Dict[str, Any]:
        """Estimate computational resource needs."""
        sim_type = requirements.get("simulation_type")
        
        # Simple heuristics, could use ML models
        base_estimates = {
            "structural": {"cpu_cores": 4, "memory_gb": 8, "time_minutes": 15},
            "fluid": {"cpu_cores": 8, "memory_gb": 16, "time_minutes": 30},
            "molecular": {"cpu_cores": 16, "memory_gb": 32, "time_hours": 1},
            "multiphysics": {"cpu_cores": 16, "memory_gb": 32, "time_hours": 2}
        }
        
        return base_estimates.get(sim_type, {"cpu_cores": 4, "memory_gb": 8, "time_minutes": 10})


class PlanningAgent:
    """
    Planning Agent
    ==============
    
    **Purpose:**
    Create detailed execution plans for simulation workflows. Determine task sequences,
    resource allocation, parallelization strategies, and dependencies between workflow
    stages.
    
    **Responsibilities:**
    - Create task execution plans from requirements
    - Determine task dependencies and sequencing
    - Plan resource allocation (CPU, memory, GPU)
    - Identify opportunities for parallelization
    - Generate workflow schedules
    - Plan checkpointing and intermediate outputs
    - Estimate workflow completion time
    
    **Inputs:**
    - requirements: Output from RequirementAnalysisAgent
    - available_resources: System resources (CPUs, memory, GPUs)
    - constraints: Time limits, cost limits, resource constraints
    
    **Outputs:**
    - execution_plan: Detailed task execution plan
    - task_graph: Task dependency graph
    - resource_allocation: CPU/memory/GPU allocation per task
    - schedule: Estimated timeline for workflow
    - parallelization: Tasks that can run in parallel
    - checkpoints: Intermediate save points
    
    **Communication Protocol:**
    - Receives: Requirements from RequirementAnalysisAgent
    - Sends to: SimulationAgent with execution plan
    - Coordinates with: ResourceManager for availability
    
    **Lifecycle:**
    1. Receive validated requirements
    2. Analyze task dependencies
    3. Plan resource allocation
    4. Identify parallelization opportunities
    5. Generate execution schedule
    6. Create checkpointing strategy
    7. Send plan to SimulationAgent
    
    **Example Scenarios:**
    
    Scenario 1: Sequential Structural Analysis
    ```
    Input: Requirements for steel beam FEA
    Output: {
        "execution_plan": {
            "plan_id": "plan_20241015_001",
            "tasks": [
                {
                    "task_id": "mesh_generation",
                    "tool": "fenicsx",
                    "depends_on": [],
                    "resources": {"cpu_cores": 2, "memory_gb": 4}
                },
                {
                    "task_id": "solve_system",
                    "tool": "fenicsx",
                    "depends_on": ["mesh_generation"],
                    "resources": {"cpu_cores": 4, "memory_gb": 8}
                }
            ]
        },
        "schedule": {
            "estimated_duration_minutes": 20,
            "critical_path": ["mesh_generation", "solve_system"]
        }
    }
    ```
    
    Scenario 2: Parallel Parameter Sweep
    ```
    Input: Requirements for 10 molecular dynamics runs
    Output: {
        "execution_plan": {
            "tasks": [
                {"task_id": "md_run_1", "parallel_group": 1, "resources": {...}},
                {"task_id": "md_run_2", "parallel_group": 1, "resources": {...}},
                ...
            ]
        },
        "parallelization": {
            "max_parallel": 5,
            "total_runs": 10,
            "resource_pool": {"total_cores": 40, "cores_per_run": 4}
        },
        "schedule": {
            "estimated_duration_hours": 2,
            "parallel_batches": 2
        }
    }
    ```
    """
    
    def __init__(self):
        """Initialize PlanningAgent."""
        self.stage = WorkflowStage.PLANNING
        self.name = "PlanningAgent"
    
    def process(self, agent_input: AgentInput) -> AgentOutput:
        """
        Process workflow planning.
        
        Args:
            agent_input: Input with validated requirements
            
        Returns:
            AgentOutput with execution plan
        """
        requirements = agent_input.previous_stage_output or {}
        available_resources = agent_input.context.get("available_resources", {})
        
        # Create execution plan
        execution_plan = self._create_execution_plan(requirements, available_resources)
        
        # Generate schedule
        schedule = self._generate_schedule(execution_plan, requirements)
        
        # Plan resource allocation
        resource_allocation = self._plan_resource_allocation(
            execution_plan, 
            requirements.get("resource_estimate", {}),
            available_resources
        )
        
        output_data = {
            "execution_plan": execution_plan,
            "schedule": schedule,
            "resource_allocation": resource_allocation,
            "checkpoints": self._plan_checkpoints(execution_plan)
        }
        
        return AgentOutput(
            stage=self.stage,
            status=AgentStatus.COMPLETED,
            data=output_data,
            metadata={
                "agent": self.name,
                "num_tasks": len(execution_plan.get("tasks", [])),
                "estimated_duration": schedule.get("estimated_duration_minutes", 0)
            }
        )
    
    def _create_execution_plan(self, requirements: Dict, resources: Dict) -> Dict[str, Any]:
        """Create detailed execution plan."""
        sim_type = requirements.get("simulation_type", "structural")
        tools = requirements.get("required_tools", ["fenicsx"])
        
        tasks = []
        task_counter = 1
        
        # Create tasks based on simulation type
        for tool in tools:
            task = {
                "task_id": f"task_{task_counter}",
                "tool": tool,
                "simulation_type": sim_type,
                "depends_on": [] if task_counter == 1 else [f"task_{task_counter-1}"],
                "parameters": requirements.get("parameters", {}),
                "priority": 1
            }
            tasks.append(task)
            task_counter += 1
        
        return {
            "plan_id": f"plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "created_at": datetime.now().isoformat(),
            "tasks": tasks,
            "simulation_type": sim_type
        }
    
    def _generate_schedule(self, plan: Dict, requirements: Dict) -> Dict[str, Any]:
        """Generate execution schedule."""
        num_tasks = len(plan.get("tasks", []))
        resource_estimate = requirements.get("resource_estimate", {})
        
        # Simple scheduling - could use critical path method
        estimated_duration = resource_estimate.get("time_minutes", 10) * num_tasks
        
        return {
            "estimated_duration_minutes": estimated_duration,
            "num_tasks": num_tasks,
            "parallelizable": num_tasks > 1,
            "critical_path": [task["task_id"] for task in plan.get("tasks", [])]
        }
    
    def _plan_resource_allocation(self, plan: Dict, estimate: Dict, available: Dict) -> Dict[str, Any]:
        """Plan resource allocation for tasks."""
        cpu_cores = estimate.get("cpu_cores", 4)
        memory_gb = estimate.get("memory_gb", 8)
        
        allocation = {
            "per_task": {
                "cpu_cores": cpu_cores,
                "memory_gb": memory_gb
            },
            "total": {
                "cpu_cores": cpu_cores * len(plan.get("tasks", [])),
                "memory_gb": memory_gb
            }
        }
        
        return allocation
    
    def _plan_checkpoints(self, plan: Dict) -> List[Dict[str, Any]]:
        """Plan checkpointing strategy."""
        checkpoints = []
        tasks = plan.get("tasks", [])
        
        # Checkpoint after each major task
        for i, task in enumerate(tasks):
            checkpoints.append({
                "checkpoint_id": f"checkpoint_{i+1}",
                "after_task": task["task_id"],
                "save_outputs": True
            })
        
        return checkpoints


class SimulationAgent:
    """
    Simulation Agent
    ================
    
    **Purpose:**
    Execute simulations according to the execution plan. Manage simulation lifecycles,
    monitor progress, handle errors, and collect results.
    
    **Responsibilities:**
    - Execute simulations using appropriate tools
    - Monitor simulation progress and resource usage
    - Handle simulation errors and retries
    - Collect intermediate and final results
    - Checkpoint simulation state
    - Report progress to workflow orchestrator
    - Manage parallel execution
    
    **Inputs:**
    - execution_plan: Detailed plan from PlanningAgent
    - simulation_scripts: Scripts or configurations to execute
    - resource_allocation: Allocated compute resources
    
    **Outputs:**
    - results: Simulation output data
    - metrics: Performance metrics (time, memory, convergence)
    - artifacts: Output files, logs, checkpoints
    - status: Execution status per task
    - errors: Error information if failures occur
    
    **Communication Protocol:**
    - Receives: Execution plan from PlanningAgent
    - Sends to: VisualizationAgent and ValidationAgent with results
    - Integrates with: TaskPipeline for actual execution
    - Reports to: Workflow orchestrator for progress updates
    
    **Lifecycle:**
    1. Receive execution plan
    2. Initialize simulation environment
    3. Execute tasks according to schedule
    4. Monitor progress and resource usage
    5. Handle errors and implement retries
    6. Collect results and artifacts
    7. Pass results to next stage
    
    **Example Scenarios:**
    
    Scenario 1: Single FEA Simulation
    ```
    Input: Execution plan with FEniCSx task
    Output: {
        "results": {
            "task_mesh_generation": {
                "status": "completed",
                "output_file": "/data/mesh.xdmf",
                "mesh_stats": {"elements": 50000, "nodes": 12500}
            },
            "task_solve_system": {
                "status": "completed",
                "output_file": "/data/solution.xdmf",
                "convergence": {"iterations": 45, "residual": 1e-7}
            }
        },
        "metrics": {
            "total_time_seconds": 245,
            "peak_memory_mb": 1024,
            "cpu_utilization": 0.85
        }
    }
    ```
    
    Scenario 2: Parallel Parameter Sweep
    ```
    Input: Plan with 10 parallel LAMMPS runs
    Output: {
        "results": {
            "md_run_1": {"status": "completed", "energy": -12.5, ...},
            "md_run_2": {"status": "completed", "energy": -12.8, ...},
            ...
        },
        "parallel_execution": {
            "max_concurrent": 5,
            "total_runs": 10,
            "successful": 10,
            "failed": 0
        }
    }
    ```
    """
    
    def __init__(self, task_pipeline: Optional[TaskPipeline] = None):
        """Initialize SimulationAgent."""
        self.stage = WorkflowStage.SIMULATION
        self.name = "SimulationAgent"
        self.task_pipeline = task_pipeline or TaskPipeline()
    
    def process(self, agent_input: AgentInput) -> AgentOutput:
        """
        Process simulation execution.
        
        Args:
            agent_input: Input with execution plan
            
        Returns:
            AgentOutput with simulation results
        """
        execution_plan = agent_input.previous_stage_output.get("execution_plan", {})
        
        # Execute tasks
        results = self._execute_tasks(execution_plan)
        
        # Collect metrics
        metrics = self._collect_metrics(results)
        
        # Check for errors
        errors = [r.get("error") for r in results.values() if "error" in r]
        status = AgentStatus.COMPLETED if not errors else AgentStatus.FAILED
        
        output_data = {
            "results": results,
            "metrics": metrics,
            "execution_summary": {
                "total_tasks": len(execution_plan.get("tasks", [])),
                "successful": len([r for r in results.values() if r.get("status") == "completed"]),
                "failed": len(errors)
            }
        }
        
        return AgentOutput(
            stage=self.stage,
            status=status,
            data=output_data,
            metadata={
                "agent": self.name,
                "execution_plan_id": execution_plan.get("plan_id")
            },
            errors=[str(e) for e in errors]
        )
    
    def _execute_tasks(self, plan: Dict) -> Dict[str, Any]:
        """Execute tasks from plan."""
        results = {}
        
        for task in plan.get("tasks", []):
            task_id = task["task_id"]
            tool = task["tool"]
            
            # Simulate execution (in production, would use TaskPipeline)
            # For now, return mock results
            results[task_id] = {
                "status": "completed",
                "tool": tool,
                "execution_time": 120,
                "output": f"/data/{task_id}_output.xdmf"
            }
        
        return results
    
    def _collect_metrics(self, results: Dict) -> Dict[str, Any]:
        """Collect execution metrics."""
        total_time = sum(r.get("execution_time", 0) for r in results.values())
        
        return {
            "total_time_seconds": total_time,
            "num_tasks": len(results),
            "successful_tasks": len([r for r in results.values() if r.get("status") == "completed"])
        }


class VisualizationAgent:
    """
    Visualization Agent
    ===================
    
    **Purpose:**
    Generate visualizations from simulation results. Create plots, animations, and
    interactive visualizations to help understand simulation outcomes.
    
    **Responsibilities:**
    - Generate standard visualization types (contour plots, vector fields, etc.)
    - Create custom visualizations based on result type
    - Produce animations for time-dependent simulations
    - Generate comparison plots for parameter sweeps
    - Create interactive visualizations
    - Export visualizations in multiple formats
    - Annotate plots with key metrics
    
    **Inputs:**
    - simulation_results: Output from SimulationAgent
    - visualization_config: Type and style of visualizations requested
    - result_metadata: Information about result structure
    
    **Outputs:**
    - visualizations: List of generated visualization files
    - thumbnails: Preview images
    - interactive_views: Interactive visualization descriptors
    - visualization_metadata: Information about each visualization
    
    **Communication Protocol:**
    - Receives: Simulation results from SimulationAgent
    - Sends to: SummarizationAgent with visualization references
    - May receive feedback from: ValidationAgent for comparison plots
    
    **Lifecycle:**
    1. Receive simulation results
    2. Analyze result structure and data types
    3. Select appropriate visualization types
    4. Generate visualizations
    5. Create thumbnails and previews
    6. Package visualization outputs
    7. Pass to next stage
    
    **Example Scenarios:**
    
    Scenario 1: Structural Analysis Visualization
    ```
    Input: FEA results with displacement and stress fields
    Output: {
        "visualizations": [
            {
                "type": "contour",
                "field": "displacement",
                "file": "/data/viz/displacement_contour.png",
                "format": "png",
                "resolution": [1920, 1080]
            },
            {
                "type": "contour",
                "field": "von_mises_stress",
                "file": "/data/viz/stress_contour.png",
                "format": "png"
            }
        ],
        "summary_plot": "/data/viz/summary.png",
        "interactive": {
            "type": "paraview_state",
            "file": "/data/viz/interactive.pvsm"
        }
    }
    ```
    
    Scenario 2: Parameter Sweep Comparison
    ```
    Input: 10 molecular dynamics results
    Output: {
        "visualizations": [
            {
                "type": "line_plot",
                "title": "Energy vs Temperature",
                "file": "/data/viz/energy_comparison.png"
            },
            {
                "type": "bar_chart",
                "title": "Convergence Time",
                "file": "/data/viz/timing_comparison.png"
            }
        ],
        "analysis": {
            "trends": ["Energy decreases with temperature"],
            "outliers": ["run_7 showed anomalous behavior"]
        }
    }
    ```
    """
    
    def __init__(self):
        """Initialize VisualizationAgent."""
        self.stage = WorkflowStage.VISUALIZATION
        self.name = "VisualizationAgent"
        
        # Visualization templates by simulation type
        self.viz_templates = {
            "structural": ["displacement_contour", "stress_contour", "deformation"],
            "fluid": ["velocity_field", "pressure_contour", "streamlines"],
            "molecular": ["trajectory", "energy_plot", "rdf"]
        }
    
    def process(self, agent_input: AgentInput) -> AgentOutput:
        """
        Process visualization generation.
        
        Args:
            agent_input: Input with simulation results
            
        Returns:
            AgentOutput with visualization files
        """
        simulation_results = agent_input.previous_stage_output.get("results", {})
        viz_config = agent_input.context.get("visualization_config", {})
        
        # Generate visualizations
        visualizations = self._generate_visualizations(simulation_results, viz_config)
        
        # Create summary
        summary = self._create_visualization_summary(visualizations)
        
        output_data = {
            "visualizations": visualizations,
            "summary": summary,
            "formats": list(set(v.get("format") for v in visualizations))
        }
        
        return AgentOutput(
            stage=self.stage,
            status=AgentStatus.COMPLETED,
            data=output_data,
            metadata={
                "agent": self.name,
                "num_visualizations": len(visualizations)
            }
        )
    
    def _generate_visualizations(self, results: Dict, config: Dict) -> List[Dict[str, Any]]:
        """Generate visualizations from results."""
        visualizations = []
        
        # Mock visualization generation
        for task_id, result in results.items():
            viz = {
                "task_id": task_id,
                "type": "contour",
                "file": f"/data/viz/{task_id}_viz.png",
                "format": "png",
                "resolution": [1920, 1080],
                "created_at": datetime.now().isoformat()
            }
            visualizations.append(viz)
        
        return visualizations
    
    def _create_visualization_summary(self, visualizations: List[Dict]) -> Dict[str, Any]:
        """Create summary of visualizations."""
        return {
            "total_visualizations": len(visualizations),
            "types": list(set(v.get("type") for v in visualizations)),
            "formats": list(set(v.get("format") for v in visualizations))
        }


class ValidationAgent:
    """
    Validation Agent
    ================
    
    **Purpose:**
    Validate simulation results against expected outcomes, physical constraints, and
    success criteria. Ensure result quality and identify potential issues.
    
    **Responsibilities:**
    - Validate results against success criteria
    - Check physical plausibility (conservation laws, bounds)
    - Compare with reference solutions if available
    - Assess numerical quality (convergence, stability)
    - Identify anomalies or unexpected behavior
    - Generate validation report
    - Provide feedback for refinement
    
    **Inputs:**
    - simulation_results: Output from SimulationAgent
    - success_criteria: From RequirementAnalysisAgent
    - reference_data: Optional reference solutions for comparison
    - validation_rules: Physical and numerical constraints
    
    **Outputs:**
    - validation_status: Pass/fail/warning
    - validation_report: Detailed validation findings
    - quality_metrics: Numerical quality indicators
    - issues: List of identified problems
    - recommendations: Suggestions for improvement
    
    **Communication Protocol:**
    - Receives: Results from SimulationAgent
    - Receives: Success criteria from RequirementAnalysisAgent
    - Sends to: SummarizationAgent with validation report
    - May trigger: Refinement loop if validation fails
    
    **Lifecycle:**
    1. Receive simulation results and criteria
    2. Apply validation rules
    3. Check physical constraints
    4. Assess numerical quality
    5. Compare with references if available
    6. Generate validation report
    7. Determine pass/fail status
    8. Provide recommendations
    
    **Example Scenarios:**
    
    Scenario 1: Successful Structural Analysis Validation
    ```
    Input: FEA results, success criteria
    Output: {
        "validation_status": "pass",
        "checks": {
            "convergence": {
                "status": "pass",
                "residual": 1.2e-7,
                "threshold": 1e-6
            },
            "displacement_bounds": {
                "status": "pass",
                "max_displacement": 12.5,
                "threshold": 50
            },
            "stress_limits": {
                "status": "pass",
                "max_stress": 185,
                "yield_strength": 250
            }
        },
        "quality_score": 0.95,
        "recommendations": []
    }
    ```
    
    Scenario 2: Failed Validation with Recommendations
    ```
    Input: CFD results with convergence issues
    Output: {
        "validation_status": "fail",
        "checks": {
            "convergence": {
                "status": "fail",
                "residual": 1.5e-3,
                "threshold": 1e-5,
                "message": "Solver did not converge"
            },
            "mass_conservation": {
                "status": "warning",
                "error": 0.02,
                "threshold": 0.01
            }
        },
        "issues": [
            "Poor convergence indicates mesh quality or solver settings issue",
            "Mass conservation error slightly elevated"
        ],
        "recommendations": [
            "Refine mesh in high-gradient regions",
            "Reduce time step for better stability",
            "Try different solver algorithm"
        ]
    }
    ```
    """
    
    def __init__(self):
        """Initialize ValidationAgent."""
        self.stage = WorkflowStage.VALIDATION
        self.name = "ValidationAgent"
    
    def process(self, agent_input: AgentInput) -> AgentOutput:
        """
        Process result validation.
        
        Args:
            agent_input: Input with simulation results and criteria
            
        Returns:
            AgentOutput with validation report
        """
        results = agent_input.previous_stage_output.get("results", {})
        
        # Get success criteria from requirement analysis
        requirements = agent_input.context.get("requirements", {})
        success_criteria = requirements.get("success_criteria", {})
        
        # Perform validation
        validation_report = self._validate_results(results, success_criteria)
        
        # Determine overall status
        all_passed = all(
            check.get("status") == "pass" 
            for check in validation_report.get("checks", {}).values()
        )
        status = AgentStatus.COMPLETED if all_passed else AgentStatus.FAILED
        
        output_data = {
            "validation_status": "pass" if all_passed else "fail",
            "validation_report": validation_report,
            "quality_score": validation_report.get("quality_score", 0.0)
        }
        
        return AgentOutput(
            stage=self.stage,
            status=status,
            data=output_data,
            metadata={
                "agent": self.name,
                "checks_performed": len(validation_report.get("checks", {}))
            },
            warnings=validation_report.get("warnings", []),
            errors=validation_report.get("issues", []) if not all_passed else []
        )
    
    def _validate_results(self, results: Dict, criteria: Dict) -> Dict[str, Any]:
        """Validate results against criteria."""
        checks = {}
        warnings = []
        issues = []
        recommendations = []
        
        # Mock validation checks
        checks["convergence"] = {
            "status": "pass",
            "residual": 1.2e-7,
            "threshold": criteria.get("convergence", {}).get("tolerance", 1e-6)
        }
        
        checks["completeness"] = {
            "status": "pass" if results else "fail",
            "message": f"Found {len(results)} task results"
        }
        
        # Calculate quality score
        num_checks = len(checks)
        passed_checks = len([c for c in checks.values() if c.get("status") == "pass"])
        quality_score = passed_checks / num_checks if num_checks > 0 else 0.0
        
        return {
            "checks": checks,
            "quality_score": quality_score,
            "warnings": warnings,
            "issues": issues,
            "recommendations": recommendations
        }


class SummarizationAgent:
    """
    Summarization Agent
    ===================
    
    **Purpose:**
    Summarize simulation workflow results, generate reports, and provide actionable
    insights. Create comprehensive documentation of the workflow execution.
    
    **Responsibilities:**
    - Summarize key findings from all workflow stages
    - Generate comprehensive reports (text, markdown, PDF)
    - Create executive summaries
    - Highlight important results and insights
    - Document workflow execution details
    - Generate actionable recommendations
    - Archive workflow artifacts
    
    **Inputs:**
    - All previous stage outputs
    - Workflow metadata and timeline
    - User preferences for report format
    
    **Outputs:**
    - summary_report: Comprehensive workflow summary
    - executive_summary: High-level findings
    - detailed_report: Full technical documentation
    - recommendations: Next steps and improvements
    - artifacts_manifest: List of all generated files
    
    **Communication Protocol:**
    - Receives: Outputs from all previous stages
    - Sends to: User/workflow initiator with final report
    - Archives: All workflow artifacts for reproducibility
    
    **Lifecycle:**
    1. Collect outputs from all stages
    2. Extract key findings and metrics
    3. Generate executive summary
    4. Create detailed technical report
    5. Compile recommendations
    6. Package all artifacts
    7. Return final summary
    
    **Example Scenarios:**
    
    Scenario 1: Successful Structural Analysis Summary
    ```
    Input: All stage outputs for steel beam FEA
    Output: {
        "executive_summary": {
            "title": "Structural Analysis: Steel Beam Under Load",
            "status": "Success",
            "key_findings": [
                "Maximum displacement: 12.5 mm (within limits)",
                "Maximum stress: 185 MPa (safe margin)",
                "Convergence achieved in 45 iterations"
            ],
            "recommendations": [
                "Current design meets safety requirements",
                "Consider optimization to reduce weight"
            ]
        },
        "performance": {
            "total_time_minutes": 18,
            "resource_usage": "Efficient - 4 cores, 8GB memory",
            "cost_estimate": "$0.12"
        },
        "artifacts": {
            "results": ["/data/solution.xdmf"],
            "visualizations": ["/data/viz/displacement.png", "/data/viz/stress.png"],
            "reports": ["/data/reports/detailed_report.md"]
        }
    }
    ```
    
    Scenario 2: Failed Simulation with Analysis
    ```
    Input: All stage outputs for failed CFD simulation
    Output: {
        "executive_summary": {
            "title": "CFD Analysis: Wing Aerodynamics",
            "status": "Failed - Convergence Issues",
            "issues": [
                "Solver failed to converge after 1000 iterations",
                "Mass conservation error exceeded threshold"
            ],
            "root_cause": "Mesh quality insufficient in high-gradient regions",
            "recommendations": [
                "Refine mesh near wing surface (target y+ < 1)",
                "Reduce time step to 1e-5 seconds",
                "Consider different turbulence model (k-omega SST)"
            ]
        },
        "attempted_iterations": 2,
        "resource_usage": {
            "total_time_minutes": 45,
            "wasted_compute": "Significant - early detection recommended"
        }
    }
    ```
    """
    
    def __init__(self):
        """Initialize SummarizationAgent."""
        self.stage = WorkflowStage.SUMMARIZATION
        self.name = "SummarizationAgent"
    
    def process(self, agent_input: AgentInput) -> AgentOutput:
        """
        Process workflow summarization.
        
        Args:
            agent_input: Input with all workflow stage outputs
            
        Returns:
            AgentOutput with comprehensive summary
        """
        # Collect all stage outputs
        workflow_data = agent_input.data
        
        # Generate executive summary
        executive_summary = self._generate_executive_summary(workflow_data)
        
        # Create detailed report
        detailed_report = self._generate_detailed_report(workflow_data)
        
        # Compile recommendations
        recommendations = self._compile_recommendations(workflow_data)
        
        # Create artifacts manifest
        artifacts = self._create_artifacts_manifest(workflow_data)
        
        output_data = {
            "executive_summary": executive_summary,
            "detailed_report": detailed_report,
            "recommendations": recommendations,
            "artifacts": artifacts,
            "workflow_complete": True
        }
        
        return AgentOutput(
            stage=self.stage,
            status=AgentStatus.COMPLETED,
            data=output_data,
            metadata={
                "agent": self.name,
                "workflow_stages_completed": len([k for k in workflow_data.keys() if k != "workflow_id"])
            }
        )
    
    def _generate_executive_summary(self, workflow_data: Dict) -> Dict[str, Any]:
        """Generate executive summary."""
        requirements = workflow_data.get("requirement_analysis", {})
        simulation = workflow_data.get("simulation", {})
        validation = workflow_data.get("validation", {})
        
        # Handle both dict and AgentOutput types
        if hasattr(requirements, 'data'):
            requirements = requirements.data
        if hasattr(simulation, 'data'):
            simulation = simulation.data
        if hasattr(validation, 'data'):
            validation = validation.data
        
        # Extract key information
        sim_type = requirements.get("data", {}).get("simulation_type", "unknown") if "data" in requirements else requirements.get("simulation_type", "unknown")
        validation_status = validation.get("data", {}).get("validation_status", "unknown") if "data" in validation else validation.get("validation_status", "unknown")
        
        return {
            "title": f"Simulation Workflow: {sim_type.title()}",
            "status": validation_status.title(),
            "simulation_type": sim_type,
            "key_findings": self._extract_key_findings(workflow_data),
            "timestamp": datetime.now().isoformat()
        }
    
    def _generate_detailed_report(self, workflow_data: Dict) -> Dict[str, Any]:
        """Generate detailed technical report."""
        return {
            "workflow_stages": list(workflow_data.keys()),
            "stage_summaries": {
                stage: self._summarize_stage(data)
                for stage, data in workflow_data.items()
                if stage != "workflow_id"
            }
        }
    
    def _summarize_stage(self, stage_data: Dict) -> Dict[str, Any]:
        """Summarize a single workflow stage."""
        if not isinstance(stage_data, dict):
            return {"summary": str(stage_data)}
        
        return {
            "status": stage_data.get("status", "unknown"),
            "key_outputs": list(stage_data.get("data", {}).keys())[:5]
        }
    
    def _extract_key_findings(self, workflow_data: Dict) -> List[str]:
        """Extract key findings from workflow."""
        findings = []
        
        validation = workflow_data.get("validation", {})
        if validation:
            # Handle both dict and AgentOutput types
            if hasattr(validation, 'data'):
                validation = validation.data
            
            status = validation.get("data", {}).get("validation_status", "unknown") if "data" in validation else validation.get("validation_status", "unknown")
            findings.append(f"Validation: {status}")
        
        simulation = workflow_data.get("simulation", {})
        if simulation:
            # Handle both dict and AgentOutput types
            if hasattr(simulation, 'data'):
                simulation = simulation.data
            
            metrics = simulation.get("data", {}).get("metrics", {}) if "data" in simulation else simulation.get("metrics", {})
            if "total_time_seconds" in metrics:
                findings.append(f"Execution time: {metrics['total_time_seconds']} seconds")
        
        return findings
    
    def _compile_recommendations(self, workflow_data: Dict) -> List[str]:
        """Compile recommendations from all stages."""
        recommendations = []
        
        # Extract recommendations from validation
        validation = workflow_data.get("validation", {})
        if validation:
            # Handle both dict and AgentOutput types
            if hasattr(validation, 'data'):
                validation = validation.data
            
            val_report = validation.get("data", {}).get("validation_report", {}) if "data" in validation else validation.get("validation_report", {})
            recommendations.extend(val_report.get("recommendations", []))
        
        return recommendations
    
    def _create_artifacts_manifest(self, workflow_data: Dict) -> Dict[str, List[str]]:
        """Create manifest of all workflow artifacts."""
        artifacts = {
            "results": [],
            "visualizations": [],
            "reports": [],
            "logs": []
        }
        
        # Collect result files
        simulation = workflow_data.get("simulation", {})
        if simulation:
            # Handle both dict and AgentOutput types
            if hasattr(simulation, 'data'):
                simulation = simulation.data
            
            results = simulation.get("data", {}).get("results", {}) if "data" in simulation else simulation.get("results", {})
            artifacts["results"] = [
                r.get("output", "") 
                for r in results.values() 
                if "output" in r
            ]
        
        # Collect visualizations
        visualization = workflow_data.get("visualization", {})
        if visualization:
            # Handle both dict and AgentOutput types
            if hasattr(visualization, 'data'):
                visualization = visualization.data
            
            viz_list = visualization.get("data", {}).get("visualizations", []) if "data" in visualization else visualization.get("visualizations", [])
            artifacts["visualizations"] = [v.get("file", "") for v in viz_list]
        
        return artifacts


# Export all agent classes
__all__ = [
    "WorkflowStage",
    "AgentStatus",
    "AgentInput",
    "AgentOutput",
    "SimulationWorkflowState",
    "RequirementAnalysisAgent",
    "PlanningAgent",
    "SimulationAgent",
    "VisualizationAgent",
    "ValidationAgent",
    "SummarizationAgent"
]
