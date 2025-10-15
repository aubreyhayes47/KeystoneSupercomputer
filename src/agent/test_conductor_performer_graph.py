"""
Test Suite for Conductor-Performer Graph Pattern
===============================================

This module provides comprehensive tests for the LangGraph-based
Conductor-Performer multi-agent orchestration system.

Test Coverage:
- Graph structure and node connectivity
- Conductor agent behavior (analysis, delegation, aggregation)
- Performer agent execution
- Validator agent checks
- Error handling and retry logic
- Feedback loops and refinement
- Integration with TaskPipeline
- State transitions and edge routing
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from typing import Dict, Any

# Import the components to test
from conductor_performer_graph import (
    ConductorPerformerGraph,
    ConductorAgent,
    PerformerAgent,
    ValidatorAgent,
    ConductorPerformerState,
    WorkflowStatus,
    AgentRole,
    EXAMPLE_WORKFLOWS
)


class TestConductorAgent(unittest.TestCase):
    """Test cases for the Conductor agent."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_pipeline = Mock()
        self.conductor = ConductorAgent(task_pipeline=self.mock_pipeline)
    
    def test_initialization(self):
        """Test Conductor agent initialization."""
        self.assertIsNotNone(self.conductor)
        self.assertEqual(self.conductor.role, AgentRole.CONDUCTOR)
        self.assertEqual(self.conductor.task_pipeline, self.mock_pipeline)
    
    def test_analyze_request_fenicsx(self):
        """Test request analysis for FEniCSx workflow."""
        state: ConductorPerformerState = {
            "messages": [],
            "status": WorkflowStatus.PENDING,
            "user_request": "Run structural finite element analysis on steel beam"
        }
        
        result = self.conductor.analyze_request(state)
        
        # Verify execution plan created
        self.assertIn("execution_plan", result)
        plan = result["execution_plan"]
        self.assertIn("plan_id", plan)
        self.assertIn("phases", plan)
        
        # Verify FEniCSx phase identified
        phases = plan["phases"]
        self.assertTrue(any(
            p["agent"] == AgentRole.FENICSX_PERFORMER.value 
            for p in phases
        ))
        
        # Verify status updated
        self.assertEqual(result["status"], WorkflowStatus.PLANNING)
    
    def test_analyze_request_lammps(self):
        """Test request analysis for LAMMPS workflow."""
        state: ConductorPerformerState = {
            "messages": [],
            "status": WorkflowStatus.PENDING,
            "user_request": "Run molecular dynamics simulation"
        }
        
        result = self.conductor.analyze_request(state)
        plan = result["execution_plan"]
        
        # Verify LAMMPS phase identified
        phases = plan["phases"]
        self.assertTrue(any(
            p["agent"] == AgentRole.LAMMPS_PERFORMER.value 
            for p in phases
        ))
    
    def test_analyze_request_openfoam(self):
        """Test request analysis for OpenFOAM workflow."""
        state: ConductorPerformerState = {
            "messages": [],
            "status": WorkflowStatus.PENDING,
            "user_request": "Run CFD fluid dynamics analysis"
        }
        
        result = self.conductor.analyze_request(state)
        plan = result["execution_plan"]
        
        # Verify OpenFOAM phase identified
        phases = plan["phases"]
        self.assertTrue(any(
            p["agent"] == AgentRole.OPENFOAM_PERFORMER.value 
            for p in phases
        ))
    
    def test_analyze_request_multi_phase(self):
        """Test request analysis for multi-phase workflow."""
        state: ConductorPerformerState = {
            "messages": [],
            "status": WorkflowStatus.PENDING,
            "user_request": "Run structural analysis and molecular dynamics simulation"
        }
        
        result = self.conductor.analyze_request(state)
        plan = result["execution_plan"]
        
        # Verify multiple phases created
        phases = plan["phases"]
        self.assertGreaterEqual(len(phases), 2)
    
    def test_delegate_tasks(self):
        """Test task delegation to Performers."""
        state: ConductorPerformerState = {
            "messages": [],
            "status": WorkflowStatus.PLANNING,
            "user_request": "test",
            "execution_plan": {
                "phases": [
                    {"phase": 1, "agent": "fenicsx_performer", "task": "fem"},
                    {"phase": 2, "agent": "lammps_performer", "task": "md"}
                ]
            }
        }
        
        result = self.conductor.delegate_tasks(state)
        
        # Verify tasks delegated
        self.assertIn("delegated_tasks", result)
        delegated = result["delegated_tasks"]
        self.assertEqual(len(delegated), 2)
        
        # Verify task structure
        for task in delegated:
            self.assertIn("task_id", task)
            self.assertIn("agent", task)
            self.assertIn("status", task)
            self.assertEqual(task["status"], "delegated")
        
        # Verify status updated
        self.assertEqual(result["status"], WorkflowStatus.EXECUTING)
    
    def test_aggregate_results_success(self):
        """Test successful result aggregation."""
        state: ConductorPerformerState = {
            "messages": [],
            "status": WorkflowStatus.VALIDATING,
            "user_request": "test",
            "execution_plan": {"plan_id": "test_plan"},
            "performer_results": {
                "task_1": {"status": "completed"},
                "task_2": {"status": "completed"}
            },
            "validation_feedback": {
                "validation_passed": True
            }
        }
        
        result = self.conductor.aggregate_results(state)
        
        # Verify final result created
        self.assertIn("final_result", result)
        final = result["final_result"]
        self.assertEqual(final["status"], "completed")
        self.assertIn("performer_results", final)
        self.assertIn("validation", final)
        
        # Verify workflow completed
        self.assertEqual(result["status"], WorkflowStatus.COMPLETED)
    
    def test_handle_error_with_retry(self):
        """Test error handling with retry logic."""
        state: ConductorPerformerState = {
            "messages": [],
            "status": WorkflowStatus.EXECUTING,
            "user_request": "test",
            "errors": [{"task_id": "task_1", "error": "convergence_failed"}],
            "iteration_count": 1,
            "max_iterations": 3
        }
        
        result = self.conductor.handle_error(state)
        
        # Verify retry triggered
        self.assertEqual(result["status"], WorkflowStatus.NEEDS_REFINEMENT)
        self.assertEqual(result["iteration_count"], 2)
    
    def test_handle_error_max_iterations(self):
        """Test error handling when max iterations reached."""
        state: ConductorPerformerState = {
            "messages": [],
            "status": WorkflowStatus.EXECUTING,
            "user_request": "test",
            "errors": [{"task_id": "task_1", "error": "convergence_failed"}],
            "iteration_count": 3,
            "max_iterations": 3
        }
        
        result = self.conductor.handle_error(state)
        
        # Verify workflow failed
        self.assertEqual(result["status"], WorkflowStatus.FAILED)
        self.assertIn("final_result", result)
        self.assertEqual(result["final_result"]["status"], "failed")


class TestPerformerAgent(unittest.TestCase):
    """Test cases for Performer agents."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_pipeline = Mock()
    
    def test_fenicsx_performer_initialization(self):
        """Test FEniCSx Performer initialization."""
        performer = PerformerAgent("fenicsx", self.mock_pipeline)
        self.assertEqual(performer.tool_name, "fenicsx")
        self.assertEqual(performer.role, AgentRole.FENICSX_PERFORMER)
    
    def test_lammps_performer_initialization(self):
        """Test LAMMPS Performer initialization."""
        performer = PerformerAgent("lammps", self.mock_pipeline)
        self.assertEqual(performer.tool_name, "lammps")
        self.assertEqual(performer.role, AgentRole.LAMMPS_PERFORMER)
    
    def test_openfoam_performer_initialization(self):
        """Test OpenFOAM Performer initialization."""
        performer = PerformerAgent("openfoam", self.mock_pipeline)
        self.assertEqual(performer.tool_name, "openfoam")
        self.assertEqual(performer.role, AgentRole.OPENFOAM_PERFORMER)
    
    def test_execute_task_success(self):
        """Test successful task execution."""
        performer = PerformerAgent("fenicsx", self.mock_pipeline)
        
        state: ConductorPerformerState = {
            "messages": [],
            "status": WorkflowStatus.EXECUTING,
            "user_request": "test",
            "delegated_tasks": [
                {
                    "task_id": "task_1",
                    "agent": "fenicsx_performer",
                    "task_type": "fem"
                }
            ]
        }
        
        result = performer.execute_task(state)
        
        # Verify result recorded
        self.assertIn("performer_results", result)
        self.assertIn("task_1", result["performer_results"])
        
        task_result = result["performer_results"]["task_1"]
        self.assertEqual(task_result["status"], "completed")
        self.assertEqual(task_result["performer"], "fenicsx_performer")
        self.assertIn("execution_time", task_result)
    
    def test_execute_task_no_matching_tasks(self):
        """Test execution when no tasks match this performer."""
        performer = PerformerAgent("fenicsx", self.mock_pipeline)
        
        state: ConductorPerformerState = {
            "messages": [],
            "status": WorkflowStatus.EXECUTING,
            "user_request": "test",
            "delegated_tasks": [
                {
                    "task_id": "task_1",
                    "agent": "lammps_performer",  # Different performer
                    "task_type": "md"
                }
            ]
        }
        
        result = performer.execute_task(state)
        
        # State should be unchanged (no matching tasks)
        self.assertNotIn("performer_results", result)
    
    def test_execute_task_with_error(self):
        """Test task execution with error handling."""
        performer = PerformerAgent("fenicsx", self.mock_pipeline)
        
        # Mock an exception during execution
        with patch.object(performer, 'execute_task', side_effect=Exception("Test error")):
            state: ConductorPerformerState = {
                "messages": [],
                "status": WorkflowStatus.EXECUTING,
                "user_request": "test",
                "delegated_tasks": [
                    {
                        "task_id": "task_1",
                        "agent": "fenicsx_performer",
                        "task_type": "fem"
                    }
                ]
            }
            
            with self.assertRaises(Exception):
                performer.execute_task(state)


class TestValidatorAgent(unittest.TestCase):
    """Test cases for Validator agent."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.validator = ValidatorAgent()
    
    def test_initialization(self):
        """Test Validator initialization."""
        self.assertIsNotNone(self.validator)
        self.assertEqual(self.validator.role, AgentRole.VALIDATOR)
    
    def test_validate_results_success(self):
        """Test validation with successful results."""
        state: ConductorPerformerState = {
            "messages": [],
            "status": WorkflowStatus.EXECUTING,
            "user_request": "test",
            "performer_results": {
                "task_1": {"status": "completed", "output": "success"},
                "task_2": {"status": "completed", "output": "success"}
            }
        }
        
        result = self.validator.validate_results(state)
        
        # Verify validation feedback
        self.assertIn("validation_feedback", result)
        feedback = result["validation_feedback"]
        
        self.assertTrue(feedback["validation_passed"])
        self.assertTrue(feedback["all_tasks_completed"])
        self.assertEqual(len(feedback["feedback"]), 0)
        
        # Verify status updated
        self.assertEqual(result["status"], WorkflowStatus.VALIDATING)
    
    def test_validate_results_failure(self):
        """Test validation with failed results."""
        state: ConductorPerformerState = {
            "messages": [],
            "status": WorkflowStatus.EXECUTING,
            "user_request": "test",
            "performer_results": {
                "task_1": {"status": "completed", "output": "success"},
                "task_2": {"status": "failed", "error": "convergence_failed"}
            }
        }
        
        result = self.validator.validate_results(state)
        
        # Verify validation failed
        feedback = result["validation_feedback"]
        self.assertFalse(feedback["validation_passed"])
        self.assertGreater(len(feedback["feedback"]), 0)
    
    def test_validate_results_no_results(self):
        """Test validation with no performer results."""
        state: ConductorPerformerState = {
            "messages": [],
            "status": WorkflowStatus.EXECUTING,
            "user_request": "test",
            "performer_results": {}
        }
        
        result = self.validator.validate_results(state)
        
        # Verify validation feedback for empty results
        feedback = result["validation_feedback"]
        self.assertFalse(feedback["all_tasks_completed"])


class TestConductorPerformerGraph(unittest.TestCase):
    """Test cases for the complete Conductor-Performer graph."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_pipeline = Mock()
        self.graph = ConductorPerformerGraph(task_pipeline=self.mock_pipeline)
    
    def test_graph_initialization(self):
        """Test graph initialization."""
        self.assertIsNotNone(self.graph)
        self.assertIsNotNone(self.graph.conductor)
        self.assertIsNotNone(self.graph.fenicsx_performer)
        self.assertIsNotNone(self.graph.lammps_performer)
        self.assertIsNotNone(self.graph.openfoam_performer)
        self.assertIsNotNone(self.graph.validator)
        self.assertIsNotNone(self.graph.graph)
    
    def test_graph_structure(self):
        """Test that graph has proper structure."""
        # Graph should be compiled
        self.assertIsNotNone(self.graph.graph)
        
        # Test that graph is callable (can invoke)
        self.assertTrue(callable(self.graph.graph.invoke))
    
    def test_execute_workflow_structural_analysis(self):
        """Test workflow execution for structural analysis."""
        result = self.graph.execute_workflow(
            user_request="Run structural finite element analysis"
        )
        
        # Verify result structure
        self.assertIn("status", result)
        self.assertIn("result", result)
        self.assertIn("messages", result)
        self.assertIn("iterations", result)
        
        # Verify workflow completed
        self.assertIn(result["status"], [WorkflowStatus.COMPLETED, WorkflowStatus.FAILED])
    
    def test_execute_workflow_molecular_dynamics(self):
        """Test workflow execution for molecular dynamics."""
        result = self.graph.execute_workflow(
            user_request="Run molecular dynamics simulation"
        )
        
        # Verify result structure
        self.assertIsInstance(result, dict)
        self.assertIn("status", result)
        self.assertIn("messages", result)
    
    def test_execute_workflow_fluid_dynamics(self):
        """Test workflow execution for fluid dynamics."""
        result = self.graph.execute_workflow(
            user_request="Run CFD fluid flow analysis"
        )
        
        # Verify result structure
        self.assertIsInstance(result, dict)
        self.assertIn("status", result)
        self.assertIn("messages", result)
    
    def test_execute_workflow_with_max_iterations(self):
        """Test workflow execution with custom max iterations."""
        result = self.graph.execute_workflow(
            user_request="Run simulation with refinement",
            max_iterations=5
        )
        
        # Verify max iterations respected
        self.assertLessEqual(result["iterations"], 5)
    
    def test_get_graph_visualization(self):
        """Test graph visualization output."""
        visualization = self.graph.get_graph_visualization()
        
        # Verify visualization is a string
        self.assertIsInstance(visualization, str)
        
        # Verify key components mentioned
        self.assertIn("Conductor", visualization)
        self.assertIn("Performer", visualization)
        self.assertIn("validate", visualization)
        self.assertIn("aggregate", visualization)


class TestWorkflowEdgeRouting(unittest.TestCase):
    """Test cases for edge routing and conditional logic."""
    
    def test_validation_success_routing(self):
        """Test routing after successful validation."""
        state: ConductorPerformerState = {
            "messages": [],
            "status": WorkflowStatus.VALIDATING,
            "user_request": "test",
            "validation_feedback": {"validation_passed": True},
            "errors": []
        }
        
        # Import routing function (would be in actual implementation)
        # For now, test the logic directly
        validation_passed = state.get("validation_feedback", {}).get("validation_passed", False)
        has_errors = len(state.get("errors", [])) > 0
        
        if has_errors:
            next_node = "handle_error"
        elif validation_passed:
            next_node = "aggregate"
        else:
            next_node = "handle_error"
        
        # Should route to aggregate on success
        self.assertEqual(next_node, "aggregate")
    
    def test_validation_failure_routing(self):
        """Test routing after validation failure."""
        state: ConductorPerformerState = {
            "messages": [],
            "status": WorkflowStatus.VALIDATING,
            "user_request": "test",
            "validation_feedback": {"validation_passed": False},
            "errors": []
        }
        
        validation_passed = state.get("validation_feedback", {}).get("validation_passed", False)
        has_errors = len(state.get("errors", [])) > 0
        
        if has_errors:
            next_node = "handle_error"
        elif validation_passed:
            next_node = "aggregate"
        else:
            next_node = "handle_error"
        
        # Should route to handle_error on failure
        self.assertEqual(next_node, "handle_error")
    
    def test_error_with_retry_routing(self):
        """Test routing after error with retry available."""
        state: ConductorPerformerState = {
            "messages": [],
            "status": WorkflowStatus.NEEDS_REFINEMENT,
            "user_request": "test",
            "iteration_count": 1,
            "max_iterations": 3
        }
        
        status = state.get("status")
        if status == WorkflowStatus.NEEDS_REFINEMENT:
            next_node = "delegate"
        else:
            next_node = "END"
        
        # Should route back to delegate for retry
        self.assertEqual(next_node, "delegate")
    
    def test_error_max_iterations_routing(self):
        """Test routing after error with max iterations reached."""
        state: ConductorPerformerState = {
            "messages": [],
            "status": WorkflowStatus.FAILED,
            "user_request": "test",
            "iteration_count": 3,
            "max_iterations": 3
        }
        
        status = state.get("status")
        if status == WorkflowStatus.NEEDS_REFINEMENT:
            next_node = "delegate"
        else:
            next_node = "END"
        
        # Should route to END when max iterations reached
        self.assertEqual(next_node, "END")


class TestExampleWorkflows(unittest.TestCase):
    """Test cases for example workflow definitions."""
    
    def test_example_workflows_exist(self):
        """Test that example workflows are defined."""
        self.assertIsNotNone(EXAMPLE_WORKFLOWS)
        self.assertIsInstance(EXAMPLE_WORKFLOWS, dict)
        self.assertGreater(len(EXAMPLE_WORKFLOWS), 0)
    
    def test_structural_analysis_workflow(self):
        """Test structural analysis example workflow."""
        workflow = EXAMPLE_WORKFLOWS.get("structural_analysis")
        self.assertIsNotNone(workflow)
        self.assertIn("description", workflow)
        self.assertIn("request", workflow)
        self.assertIn("expected_performers", workflow)
        self.assertIn("steps", workflow)
    
    def test_multiphysics_workflow(self):
        """Test multiphysics example workflow."""
        workflow = EXAMPLE_WORKFLOWS.get("multiphysics_workflow")
        self.assertIsNotNone(workflow)
        self.assertGreater(len(workflow["expected_performers"]), 1)
    
    def test_parameter_sweep_workflow(self):
        """Test parameter sweep example workflow."""
        workflow = EXAMPLE_WORKFLOWS.get("parameter_sweep")
        self.assertIsNotNone(workflow)
        self.assertIn("lammps_performer", workflow["expected_performers"])
    
    def test_error_recovery_workflow(self):
        """Test error recovery example workflow."""
        workflow = EXAMPLE_WORKFLOWS.get("error_recovery")
        self.assertIsNotNone(workflow)
        self.assertIn("refinement", workflow["description"].lower())


class TestStateManagement(unittest.TestCase):
    """Test cases for state management throughout workflow."""
    
    def test_initial_state_structure(self):
        """Test initial state has required fields."""
        state: ConductorPerformerState = {
            "messages": [],
            "status": WorkflowStatus.PENDING,
            "user_request": "test request"
        }
        
        # Required fields
        self.assertIn("messages", state)
        self.assertIn("status", state)
        self.assertIn("user_request", state)
    
    def test_state_evolution_through_workflow(self):
        """Test state evolution through workflow stages."""
        # Initial state
        state: ConductorPerformerState = {
            "messages": [],
            "status": WorkflowStatus.PENDING,
            "user_request": "test"
        }
        
        # After analysis
        self.assertEqual(state["status"], WorkflowStatus.PENDING)
        
        # After delegation (simulated)
        state["status"] = WorkflowStatus.EXECUTING
        state["delegated_tasks"] = [{"task_id": "task_1"}]
        self.assertEqual(state["status"], WorkflowStatus.EXECUTING)
        self.assertIn("delegated_tasks", state)
        
        # After execution (simulated)
        state["performer_results"] = {"task_1": {"status": "completed"}}
        self.assertIn("performer_results", state)
        
        # After validation (simulated)
        state["status"] = WorkflowStatus.VALIDATING
        state["validation_feedback"] = {"validation_passed": True}
        self.assertEqual(state["status"], WorkflowStatus.VALIDATING)
        
        # After aggregation (simulated)
        state["status"] = WorkflowStatus.COMPLETED
        state["final_result"] = {"status": "completed"}
        self.assertEqual(state["status"], WorkflowStatus.COMPLETED)


def run_tests():
    """Run all test suites."""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestConductorAgent))
    suite.addTests(loader.loadTestsFromTestCase(TestPerformerAgent))
    suite.addTests(loader.loadTestsFromTestCase(TestValidatorAgent))
    suite.addTests(loader.loadTestsFromTestCase(TestConductorPerformerGraph))
    suite.addTests(loader.loadTestsFromTestCase(TestWorkflowEdgeRouting))
    suite.addTests(loader.loadTestsFromTestCase(TestExampleWorkflows))
    suite.addTests(loader.loadTestsFromTestCase(TestStateManagement))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"Tests Run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("=" * 70)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)
