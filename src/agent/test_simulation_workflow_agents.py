"""
Unit Tests for Simulation Workflow Agents
==========================================

Comprehensive test suite for the six specialized workflow agents:
- RequirementAnalysisAgent
- PlanningAgent
- SimulationAgent
- VisualizationAgent
- ValidationAgent
- SummarizationAgent

Run: python3 test_simulation_workflow_agents.py
"""

import unittest
import sys
from pathlib import Path
from datetime import datetime

# Import agent classes
from simulation_workflow_agents import (
    WorkflowStage,
    AgentStatus,
    AgentInput,
    AgentOutput,
    SimulationWorkflowState,
    RequirementAnalysisAgent,
    PlanningAgent,
    SimulationAgent,
    VisualizationAgent,
    ValidationAgent,
    SummarizationAgent
)


class TestAgentInputOutput(unittest.TestCase):
    """Test AgentInput and AgentOutput data structures."""
    
    def test_agent_input_creation(self):
        """Test AgentInput initialization."""
        input_data = AgentInput(
            stage=WorkflowStage.REQUIREMENT_ANALYSIS,
            data={"user_request": "Test request"},
            context={"key": "value"}
        )
        
        self.assertEqual(input_data.stage, WorkflowStage.REQUIREMENT_ANALYSIS)
        self.assertIn("user_request", input_data.data)
        self.assertIn("key", input_data.context)
        self.assertIsNotNone(input_data.timestamp)
    
    def test_agent_output_creation(self):
        """Test AgentOutput initialization."""
        output = AgentOutput(
            stage=WorkflowStage.PLANNING,
            status=AgentStatus.COMPLETED,
            data={"plan": "test_plan"},
            metadata={"duration": 10}
        )
        
        self.assertEqual(output.stage, WorkflowStage.PLANNING)
        self.assertEqual(output.status, AgentStatus.COMPLETED)
        self.assertIn("plan", output.data)
        self.assertEqual(len(output.errors), 0)
        self.assertEqual(len(output.warnings), 0)
    
    def test_agent_output_to_dict(self):
        """Test AgentOutput to_dict conversion."""
        output = AgentOutput(
            stage=WorkflowStage.SIMULATION,
            status=AgentStatus.COMPLETED,
            data={"results": []},
            errors=["error1"],
            warnings=["warning1"]
        )
        
        output_dict = output.to_dict()
        
        self.assertIsInstance(output_dict, dict)
        self.assertEqual(output_dict["stage"], "simulation")
        self.assertEqual(output_dict["status"], "completed")
        self.assertEqual(len(output_dict["errors"]), 1)
        self.assertEqual(len(output_dict["warnings"]), 1)


class TestRequirementAnalysisAgent(unittest.TestCase):
    """Test RequirementAnalysisAgent functionality."""
    
    def setUp(self):
        """Initialize agent for tests."""
        self.agent = RequirementAnalysisAgent()
    
    def test_agent_initialization(self):
        """Test agent initialization."""
        self.assertEqual(self.agent.stage, WorkflowStage.REQUIREMENT_ANALYSIS)
        self.assertEqual(self.agent.name, "RequirementAnalysisAgent")
        self.assertIsNotNone(self.agent.simulation_types)
    
    def test_structural_analysis_request(self):
        """Test requirement analysis for structural simulation."""
        input_data = AgentInput(
            stage=WorkflowStage.REQUIREMENT_ANALYSIS,
            data={"user_request": "Run finite element analysis on a steel beam under 10kN load"}
        )
        
        output = self.agent.process(input_data)
        
        self.assertEqual(output.status, AgentStatus.COMPLETED)
        self.assertEqual(output.data["simulation_type"], "structural")
        self.assertIn("fenicsx", output.data["required_tools"])
        self.assertIn("resource_estimate", output.data)
        self.assertTrue(output.data["validated"])
    
    def test_fluid_dynamics_request(self):
        """Test requirement analysis for fluid simulation."""
        input_data = AgentInput(
            stage=WorkflowStage.REQUIREMENT_ANALYSIS,
            data={"user_request": "Run CFD simulation on airfoil"}
        )
        
        output = self.agent.process(input_data)
        
        self.assertEqual(output.data["simulation_type"], "fluid")
        self.assertIn("openfoam", output.data["required_tools"])
    
    def test_molecular_dynamics_request(self):
        """Test requirement analysis for molecular dynamics."""
        input_data = AgentInput(
            stage=WorkflowStage.REQUIREMENT_ANALYSIS,
            data={"user_request": "Run molecular dynamics simulation"}
        )
        
        output = self.agent.process(input_data)
        
        self.assertEqual(output.data["simulation_type"], "molecular")
        self.assertIn("lammps", output.data["required_tools"])
    
    def test_multiphysics_request(self):
        """Test requirement analysis for multiphysics simulation."""
        input_data = AgentInput(
            stage=WorkflowStage.REQUIREMENT_ANALYSIS,
            data={"user_request": "Run coupled structural and fluid analysis"}
        )
        
        output = self.agent.process(input_data)
        
        self.assertEqual(output.data["simulation_type"], "multiphysics")
        self.assertTrue(len(output.data["required_tools"]) >= 2)
    
    def test_resource_estimation(self):
        """Test resource estimation."""
        input_data = AgentInput(
            stage=WorkflowStage.REQUIREMENT_ANALYSIS,
            data={"user_request": "Run structural analysis"}
        )
        
        output = self.agent.process(input_data)
        
        estimate = output.data["resource_estimate"]
        self.assertIn("cpu_cores", estimate)
        self.assertIn("memory_gb", estimate)
        self.assertTrue("time_minutes" in estimate or "time_hours" in estimate)
    
    def test_success_criteria_definition(self):
        """Test success criteria definition."""
        input_data = AgentInput(
            stage=WorkflowStage.REQUIREMENT_ANALYSIS,
            data={"user_request": "Run finite element analysis"}
        )
        
        output = self.agent.process(input_data)
        
        self.assertIn("success_criteria", output.data)
        criteria = output.data["success_criteria"]
        self.assertIn("convergence", criteria)


class TestPlanningAgent(unittest.TestCase):
    """Test PlanningAgent functionality."""
    
    def setUp(self):
        """Initialize agent for tests."""
        self.agent = PlanningAgent()
        
        # Create mock requirements output
        self.requirements = {
            "simulation_type": "structural",
            "parameters": {"material": "steel"},
            "required_tools": ["fenicsx"],
            "resource_estimate": {
                "cpu_cores": 4,
                "memory_gb": 8,
                "time_minutes": 15
            }
        }
    
    def test_agent_initialization(self):
        """Test agent initialization."""
        self.assertEqual(self.agent.stage, WorkflowStage.PLANNING)
        self.assertEqual(self.agent.name, "PlanningAgent")
    
    def test_execution_plan_creation(self):
        """Test execution plan creation."""
        input_data = AgentInput(
            stage=WorkflowStage.PLANNING,
            data={},
            previous_stage_output=self.requirements
        )
        
        output = self.agent.process(input_data)
        
        self.assertEqual(output.status, AgentStatus.COMPLETED)
        self.assertIn("execution_plan", output.data)
        plan = output.data["execution_plan"]
        self.assertIn("plan_id", plan)
        self.assertIn("tasks", plan)
    
    def test_task_structure(self):
        """Test task structure in execution plan."""
        input_data = AgentInput(
            stage=WorkflowStage.PLANNING,
            data={},
            previous_stage_output=self.requirements
        )
        
        output = self.agent.process(input_data)
        
        tasks = output.data["execution_plan"]["tasks"]
        self.assertGreater(len(tasks), 0)
        
        # Check task structure
        task = tasks[0]
        self.assertIn("task_id", task)
        self.assertIn("tool", task)
        self.assertIn("depends_on", task)
    
    def test_schedule_generation(self):
        """Test schedule generation."""
        input_data = AgentInput(
            stage=WorkflowStage.PLANNING,
            data={},
            previous_stage_output=self.requirements
        )
        
        output = self.agent.process(input_data)
        
        self.assertIn("schedule", output.data)
        schedule = output.data["schedule"]
        self.assertIn("estimated_duration_minutes", schedule)
        self.assertIn("num_tasks", schedule)
    
    def test_resource_allocation(self):
        """Test resource allocation planning."""
        input_data = AgentInput(
            stage=WorkflowStage.PLANNING,
            data={},
            previous_stage_output=self.requirements,
            context={"available_resources": {"cpu_cores": 16}}
        )
        
        output = self.agent.process(input_data)
        
        self.assertIn("resource_allocation", output.data)
        allocation = output.data["resource_allocation"]
        self.assertIn("per_task", allocation)
        self.assertIn("total", allocation)
    
    def test_checkpointing_strategy(self):
        """Test checkpointing strategy."""
        input_data = AgentInput(
            stage=WorkflowStage.PLANNING,
            data={},
            previous_stage_output=self.requirements
        )
        
        output = self.agent.process(input_data)
        
        self.assertIn("checkpoints", output.data)
        checkpoints = output.data["checkpoints"]
        self.assertIsInstance(checkpoints, list)


class TestSimulationAgent(unittest.TestCase):
    """Test SimulationAgent functionality."""
    
    def setUp(self):
        """Initialize agent for tests."""
        self.agent = SimulationAgent()
        
        # Create mock execution plan
        self.execution_plan = {
            "plan_id": "test_plan_001",
            "tasks": [
                {
                    "task_id": "task_1",
                    "tool": "fenicsx",
                    "simulation_type": "structural",
                    "depends_on": [],
                    "parameters": {}
                }
            ]
        }
    
    def test_agent_initialization(self):
        """Test agent initialization."""
        self.assertEqual(self.agent.stage, WorkflowStage.SIMULATION)
        self.assertEqual(self.agent.name, "SimulationAgent")
        self.assertIsNotNone(self.agent.task_pipeline)
    
    def test_simulation_execution(self):
        """Test simulation execution."""
        input_data = AgentInput(
            stage=WorkflowStage.SIMULATION,
            data={},
            previous_stage_output={"execution_plan": self.execution_plan}
        )
        
        output = self.agent.process(input_data)
        
        self.assertEqual(output.status, AgentStatus.COMPLETED)
        self.assertIn("results", output.data)
        self.assertIn("metrics", output.data)
        self.assertIn("execution_summary", output.data)
    
    def test_results_collection(self):
        """Test results collection."""
        input_data = AgentInput(
            stage=WorkflowStage.SIMULATION,
            data={},
            previous_stage_output={"execution_plan": self.execution_plan}
        )
        
        output = self.agent.process(input_data)
        
        results = output.data["results"]
        self.assertGreater(len(results), 0)
        
        # Check result structure
        result = list(results.values())[0]
        self.assertIn("status", result)
        self.assertIn("tool", result)
    
    def test_metrics_collection(self):
        """Test metrics collection."""
        input_data = AgentInput(
            stage=WorkflowStage.SIMULATION,
            data={},
            previous_stage_output={"execution_plan": self.execution_plan}
        )
        
        output = self.agent.process(input_data)
        
        metrics = output.data["metrics"]
        self.assertIn("total_time_seconds", metrics)
        self.assertIn("num_tasks", metrics)
        self.assertIn("successful_tasks", metrics)
    
    def test_execution_summary(self):
        """Test execution summary."""
        input_data = AgentInput(
            stage=WorkflowStage.SIMULATION,
            data={},
            previous_stage_output={"execution_plan": self.execution_plan}
        )
        
        output = self.agent.process(input_data)
        
        summary = output.data["execution_summary"]
        self.assertIn("total_tasks", summary)
        self.assertIn("successful", summary)
        self.assertIn("failed", summary)


class TestVisualizationAgent(unittest.TestCase):
    """Test VisualizationAgent functionality."""
    
    def setUp(self):
        """Initialize agent for tests."""
        self.agent = VisualizationAgent()
        
        # Create mock simulation results
        self.simulation_results = {
            "task_1": {
                "status": "completed",
                "tool": "fenicsx",
                "output": "/data/task_1_output.xdmf"
            }
        }
    
    def test_agent_initialization(self):
        """Test agent initialization."""
        self.assertEqual(self.agent.stage, WorkflowStage.VISUALIZATION)
        self.assertEqual(self.agent.name, "VisualizationAgent")
        self.assertIsNotNone(self.agent.viz_templates)
    
    def test_visualization_generation(self):
        """Test visualization generation."""
        input_data = AgentInput(
            stage=WorkflowStage.VISUALIZATION,
            data={},
            previous_stage_output={"results": self.simulation_results}
        )
        
        output = self.agent.process(input_data)
        
        self.assertEqual(output.status, AgentStatus.COMPLETED)
        self.assertIn("visualizations", output.data)
        self.assertIn("summary", output.data)
    
    def test_visualization_structure(self):
        """Test visualization structure."""
        input_data = AgentInput(
            stage=WorkflowStage.VISUALIZATION,
            data={},
            previous_stage_output={"results": self.simulation_results}
        )
        
        output = self.agent.process(input_data)
        
        visualizations = output.data["visualizations"]
        self.assertGreater(len(visualizations), 0)
        
        # Check visualization structure
        viz = visualizations[0]
        self.assertIn("type", viz)
        self.assertIn("file", viz)
        self.assertIn("format", viz)
    
    def test_visualization_summary(self):
        """Test visualization summary."""
        input_data = AgentInput(
            stage=WorkflowStage.VISUALIZATION,
            data={},
            previous_stage_output={"results": self.simulation_results}
        )
        
        output = self.agent.process(input_data)
        
        summary = output.data["summary"]
        self.assertIn("total_visualizations", summary)
        self.assertIn("types", summary)
        self.assertIn("formats", summary)


class TestValidationAgent(unittest.TestCase):
    """Test ValidationAgent functionality."""
    
    def setUp(self):
        """Initialize agent for tests."""
        self.agent = ValidationAgent()
        
        # Create mock simulation results
        self.simulation_results = {
            "task_1": {
                "status": "completed",
                "output": "/data/output.xdmf"
            }
        }
        
        # Create mock requirements
        self.requirements = {
            "success_criteria": {
                "convergence": {"tolerance": 1e-6}
            }
        }
    
    def test_agent_initialization(self):
        """Test agent initialization."""
        self.assertEqual(self.agent.stage, WorkflowStage.VALIDATION)
        self.assertEqual(self.agent.name, "ValidationAgent")
    
    def test_successful_validation(self):
        """Test successful validation."""
        input_data = AgentInput(
            stage=WorkflowStage.VALIDATION,
            data={},
            previous_stage_output={"results": self.simulation_results},
            context={"requirements": self.requirements}
        )
        
        output = self.agent.process(input_data)
        
        self.assertEqual(output.status, AgentStatus.COMPLETED)
        self.assertIn("validation_status", output.data)
        self.assertIn("validation_report", output.data)
    
    def test_validation_checks(self):
        """Test validation checks."""
        input_data = AgentInput(
            stage=WorkflowStage.VALIDATION,
            data={},
            previous_stage_output={"results": self.simulation_results},
            context={"requirements": self.requirements}
        )
        
        output = self.agent.process(input_data)
        
        report = output.data["validation_report"]
        self.assertIn("checks", report)
        checks = report["checks"]
        self.assertGreater(len(checks), 0)
        
        # Check structure of validation check
        first_check = list(checks.values())[0]
        self.assertIn("status", first_check)
    
    def test_quality_score(self):
        """Test quality score calculation."""
        input_data = AgentInput(
            stage=WorkflowStage.VALIDATION,
            data={},
            previous_stage_output={"results": self.simulation_results},
            context={"requirements": self.requirements}
        )
        
        output = self.agent.process(input_data)
        
        self.assertIn("quality_score", output.data)
        score = output.data["quality_score"]
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)
    
    def test_validation_with_empty_results(self):
        """Test validation with empty results."""
        input_data = AgentInput(
            stage=WorkflowStage.VALIDATION,
            data={},
            previous_stage_output={"results": {}},
            context={"requirements": self.requirements}
        )
        
        output = self.agent.process(input_data)
        
        # Should fail when no results present
        self.assertEqual(output.status, AgentStatus.FAILED)


class TestSummarizationAgent(unittest.TestCase):
    """Test SummarizationAgent functionality."""
    
    def setUp(self):
        """Initialize agent for tests."""
        self.agent = SummarizationAgent()
        
        # Create mock workflow data
        self.workflow_data = {
            "workflow_id": "test_workflow_001",
            "requirement_analysis": {
                "data": {
                    "simulation_type": "structural",
                    "validated": True
                },
                "status": "completed"
            },
            "simulation": {
                "data": {
                    "metrics": {
                        "total_time_seconds": 120
                    }
                },
                "status": "completed"
            },
            "validation": {
                "data": {
                    "validation_status": "pass",
                    "validation_report": {
                        "recommendations": ["Optimize mesh"]
                    }
                },
                "status": "completed"
            },
            "visualization": {
                "data": {
                    "visualizations": [
                        {"file": "/data/viz1.png"}
                    ]
                },
                "status": "completed"
            }
        }
    
    def test_agent_initialization(self):
        """Test agent initialization."""
        self.assertEqual(self.agent.stage, WorkflowStage.SUMMARIZATION)
        self.assertEqual(self.agent.name, "SummarizationAgent")
    
    def test_summarization(self):
        """Test workflow summarization."""
        input_data = AgentInput(
            stage=WorkflowStage.SUMMARIZATION,
            data=self.workflow_data
        )
        
        output = self.agent.process(input_data)
        
        self.assertEqual(output.status, AgentStatus.COMPLETED)
        self.assertIn("executive_summary", output.data)
        self.assertIn("detailed_report", output.data)
        self.assertIn("recommendations", output.data)
        self.assertIn("artifacts", output.data)
    
    def test_executive_summary(self):
        """Test executive summary generation."""
        input_data = AgentInput(
            stage=WorkflowStage.SUMMARIZATION,
            data=self.workflow_data
        )
        
        output = self.agent.process(input_data)
        
        summary = output.data["executive_summary"]
        self.assertIn("title", summary)
        self.assertIn("status", summary)
        self.assertIn("simulation_type", summary)
        self.assertIn("key_findings", summary)
    
    def test_detailed_report(self):
        """Test detailed report generation."""
        input_data = AgentInput(
            stage=WorkflowStage.SUMMARIZATION,
            data=self.workflow_data
        )
        
        output = self.agent.process(input_data)
        
        report = output.data["detailed_report"]
        self.assertIn("workflow_stages", report)
        self.assertIn("stage_summaries", report)
    
    def test_recommendations_compilation(self):
        """Test recommendations compilation."""
        input_data = AgentInput(
            stage=WorkflowStage.SUMMARIZATION,
            data=self.workflow_data
        )
        
        output = self.agent.process(input_data)
        
        recommendations = output.data["recommendations"]
        self.assertIsInstance(recommendations, list)
    
    def test_artifacts_manifest(self):
        """Test artifacts manifest creation."""
        input_data = AgentInput(
            stage=WorkflowStage.SUMMARIZATION,
            data=self.workflow_data
        )
        
        output = self.agent.process(input_data)
        
        artifacts = output.data["artifacts"]
        self.assertIsInstance(artifacts, dict)
        self.assertIn("visualizations", artifacts)


class TestWorkflowIntegration(unittest.TestCase):
    """Test complete workflow integration."""
    
    def test_sequential_workflow(self):
        """Test sequential execution of all agents."""
        # 1. Requirement Analysis
        req_agent = RequirementAnalysisAgent()
        req_input = AgentInput(
            stage=WorkflowStage.REQUIREMENT_ANALYSIS,
            data={"user_request": "Run structural analysis on steel beam"}
        )
        req_output = req_agent.process(req_input)
        self.assertEqual(req_output.status, AgentStatus.COMPLETED)
        
        # 2. Planning
        plan_agent = PlanningAgent()
        plan_input = AgentInput(
            stage=WorkflowStage.PLANNING,
            data={},
            previous_stage_output=req_output.data
        )
        plan_output = plan_agent.process(plan_input)
        self.assertEqual(plan_output.status, AgentStatus.COMPLETED)
        
        # 3. Simulation
        sim_agent = SimulationAgent()
        sim_input = AgentInput(
            stage=WorkflowStage.SIMULATION,
            data={},
            previous_stage_output=plan_output.data
        )
        sim_output = sim_agent.process(sim_input)
        self.assertEqual(sim_output.status, AgentStatus.COMPLETED)
        
        # 4. Visualization
        viz_agent = VisualizationAgent()
        viz_input = AgentInput(
            stage=WorkflowStage.VISUALIZATION,
            data={},
            previous_stage_output=sim_output.data
        )
        viz_output = viz_agent.process(viz_input)
        self.assertEqual(viz_output.status, AgentStatus.COMPLETED)
        
        # 5. Validation
        val_agent = ValidationAgent()
        val_input = AgentInput(
            stage=WorkflowStage.VALIDATION,
            data={},
            previous_stage_output=sim_output.data,
            context={"requirements": req_output.data}
        )
        val_output = val_agent.process(val_input)
        self.assertEqual(val_output.status, AgentStatus.COMPLETED)
        
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
        self.assertEqual(sum_output.status, AgentStatus.COMPLETED)
        
        # Verify final summary
        self.assertIn("workflow_complete", sum_output.data)
        self.assertTrue(sum_output.data["workflow_complete"])
    
    def test_data_flow_between_agents(self):
        """Test data flows correctly between agents."""
        # Requirement Analysis
        req_agent = RequirementAnalysisAgent()
        req_output = req_agent.process(AgentInput(
            stage=WorkflowStage.REQUIREMENT_ANALYSIS,
            data={"user_request": "Test simulation"}
        ))
        
        # Verify planning receives requirements
        plan_agent = PlanningAgent()
        plan_output = plan_agent.process(AgentInput(
            stage=WorkflowStage.PLANNING,
            data={},
            previous_stage_output=req_output.data
        ))
        
        # Check that planning has access to requirements
        self.assertIsNotNone(plan_output.data["execution_plan"])
        
        # Verify simulation receives plan
        sim_agent = SimulationAgent()
        sim_output = sim_agent.process(AgentInput(
            stage=WorkflowStage.SIMULATION,
            data={},
            previous_stage_output=plan_output.data
        ))
        
        # Check simulation has results
        self.assertIsNotNone(sim_output.data["results"])


def run_tests():
    """Run all tests and display results."""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestAgentInputOutput))
    suite.addTests(loader.loadTestsFromTestCase(TestRequirementAnalysisAgent))
    suite.addTests(loader.loadTestsFromTestCase(TestPlanningAgent))
    suite.addTests(loader.loadTestsFromTestCase(TestSimulationAgent))
    suite.addTests(loader.loadTestsFromTestCase(TestVisualizationAgent))
    suite.addTests(loader.loadTestsFromTestCase(TestValidationAgent))
    suite.addTests(loader.loadTestsFromTestCase(TestSummarizationAgent))
    suite.addTests(loader.loadTestsFromTestCase(TestWorkflowIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"Tests Run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("="*70)
    
    return result


if __name__ == "__main__":
    result = run_tests()
    sys.exit(0 if result.wasSuccessful() else 1)
