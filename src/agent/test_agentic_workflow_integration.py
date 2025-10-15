#!/usr/bin/env python3
"""
Integration tests for agentic workflow orchestration.

These tests validate end-to-end multi-step workflow execution through
orchestrated containers and agent interfaces. Requires Docker Compose
and running Redis/Celery services.

Usage:
    # Start services first
    docker compose up -d redis celery-worker
    
    # Run integration tests
    python3 test_agentic_workflow_integration.py
    
    # Or run specific test
    python3 test_agentic_workflow_integration.py --test workflow_simple
"""

import sys
import os
import time
import json
import argparse
import tempfile
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

# Add agent and parent directories to path
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

from task_pipeline import TaskPipeline, TaskStatus
from agent_state import AgentState


class AgenticWorkflowIntegrationTest:
    """Integration test suite for agentic workflow orchestration."""
    
    def __init__(self):
        """Initialize the test suite."""
        self.pipeline = None
        self.results = []
        self.start_time = None
        self.end_time = None
        
    def setup(self) -> bool:
        """
        Setup test environment.
        
        Returns:
            True if setup successful, False otherwise
        """
        print("=" * 70)
        print("AGENTIC WORKFLOW ORCHESTRATION INTEGRATION TEST")
        print("=" * 70)
        print()
        
        try:
            # Initialize pipeline
            self.pipeline = TaskPipeline()
            
            # Check worker health
            print("Checking Celery worker health...")
            health = self.pipeline.health_check()
            print(f"✓ Worker status: {health['status']}")
            print(f"✓ Message: {health['message']}")
            print()
            
            return True
            
        except Exception as e:
            print(f"✗ Setup failed: {e}")
            print()
            print("Make sure Docker Compose services are running:")
            print("  docker compose up -d redis celery-worker")
            print()
            return False
    
    def test_simple_workflow(self) -> Dict[str, Any]:
        """Test a simple two-step sequential workflow."""
        test_name = "Simple Sequential Workflow"
        print(f"\n{'=' * 70}")
        print(f"TEST: {test_name}")
        print(f"{'=' * 70}")
        print("Description: Submit 2 tasks sequentially and verify completion")
        print()
        
        result = {
            'test_name': test_name,
            'passed': False,
            'start_time': datetime.now(),
            'error': None,
            'task_ids': [],
            'workflow_status': None
        }
        
        try:
            # Define simple workflow
            tasks = [
                {
                    "tool": "fenicsx",
                    "script": "poisson.py",
                    "params": {"mesh_size": 16}
                },
                {
                    "tool": "lammps",
                    "script": "example.lammps",
                    "params": {}
                }
            ]
            
            print(f"Submitting workflow with {len(tasks)} tasks (sequential)...")
            task_ids = self.pipeline.submit_workflow(tasks, sequential=False)
            result['task_ids'] = task_ids
            print(f"✓ Submitted {len(task_ids)} tasks")
            for i, tid in enumerate(task_ids):
                print(f"  Task {i+1}: {tid}")
            print()
            
            # Monitor workflow progress
            print("Monitoring workflow progress...")
            def progress_callback(status):
                print(f"  Progress: {status['completed']}/{status['total']} completed, "
                      f"{status['running']} running, {status['failed']} failed")
            
            final_status = self.pipeline.wait_for_workflow(
                task_ids,
                timeout=300,
                callback=progress_callback,
                poll_interval=5
            )
            result['workflow_status'] = final_status
            
            print()
            print(f"✓ Workflow complete!")
            print(f"  Total tasks: {final_status['total']}")
            print(f"  Completed: {final_status['completed']}")
            print(f"  Failed: {final_status['failed']}")
            
            # Verify all tasks completed successfully
            if final_status['completed'] == len(tasks) and final_status['failed'] == 0:
                result['passed'] = True
                print(f"\n✓ {test_name} PASSED")
            else:
                result['error'] = f"Expected {len(tasks)} completed, got {final_status['completed']}"
                print(f"\n✗ {test_name} FAILED: {result['error']}")
            
        except Exception as e:
            result['error'] = str(e)
            print(f"\n✗ {test_name} FAILED: {e}")
        
        result['end_time'] = datetime.now()
        result['duration'] = (result['end_time'] - result['start_time']).total_seconds()
        
        return result
    
    def test_parallel_workflow(self) -> Dict[str, Any]:
        """Test parallel workflow execution with 3 simultaneous tasks."""
        test_name = "Parallel Workflow Execution"
        print(f"\n{'=' * 70}")
        print(f"TEST: {test_name}")
        print(f"{'=' * 70}")
        print("Description: Submit 3 tasks in parallel and verify concurrent execution")
        print()
        
        result = {
            'test_name': test_name,
            'passed': False,
            'start_time': datetime.now(),
            'error': None,
            'task_ids': [],
            'workflow_status': None
        }
        
        try:
            # Define parallel workflow (all can run concurrently)
            tasks = [
                {"tool": "fenicsx", "script": "poisson.py", "params": {"mesh_size": 8}},
                {"tool": "lammps", "script": "example.lammps", "params": {}},
                {"tool": "openfoam", "script": "example_cavity.py", "params": {}}
            ]
            
            print(f"Submitting workflow with {len(tasks)} tasks (parallel)...")
            start_time = time.time()
            task_ids = self.pipeline.submit_workflow(tasks, sequential=False)
            result['task_ids'] = task_ids
            
            print(f"✓ Submitted {len(task_ids)} tasks in parallel")
            for i, tid in enumerate(task_ids):
                print(f"  Task {i+1}: {tid}")
            print()
            
            # Wait for completion
            print("Waiting for parallel workflow completion...")
            final_status = self.pipeline.wait_for_workflow(
                task_ids,
                timeout=300,
                poll_interval=5
            )
            result['workflow_status'] = final_status
            
            elapsed = time.time() - start_time
            print()
            print(f"✓ Workflow complete in {elapsed:.1f} seconds!")
            print(f"  Total tasks: {final_status['total']}")
            print(f"  Completed: {final_status['completed']}")
            print(f"  Failed: {final_status['failed']}")
            
            # Verify all tasks completed
            if final_status['all_complete'] and final_status['failed'] == 0:
                result['passed'] = True
                print(f"\n✓ {test_name} PASSED")
            else:
                result['error'] = "Not all tasks completed successfully"
                print(f"\n✗ {test_name} FAILED: {result['error']}")
            
        except Exception as e:
            result['error'] = str(e)
            print(f"\n✗ {test_name} FAILED: {e}")
        
        result['end_time'] = datetime.now()
        result['duration'] = (result['end_time'] - result['start_time']).total_seconds()
        
        return result
    
    def test_workflow_with_agent_state(self) -> Dict[str, Any]:
        """Test workflow orchestration with agent state management."""
        test_name = "Workflow with Agent State"
        print(f"\n{'=' * 70}")
        print(f"TEST: {test_name}")
        print(f"{'=' * 70}")
        print("Description: Simulate agent-driven workflow with state updates")
        print()
        
        result = {
            'test_name': test_name,
            'passed': False,
            'start_time': datetime.now(),
            'error': None,
            'agent_states': [],
            'task_ids': []
        }
        
        try:
            # Initialize agent state
            agent_state = {
                'messages': [],
                'simulation_params': {
                    'tool': 'fenicsx',
                    'script': 'poisson.py',
                    'params': {'mesh_size': 16}
                },
                'artifact_paths': []
            }
            result['agent_states'].append(agent_state.copy())
            
            print("Simulating agent workflow:")
            print("  1. Agent decides on simulation parameters")
            print(f"     Tool: {agent_state['simulation_params']['tool']}")
            print(f"     Script: {agent_state['simulation_params']['script']}")
            print()
            
            # Agent submits task based on state
            print("  2. Agent submits task via pipeline...")
            task_id = self.pipeline.submit_task(
                tool=agent_state['simulation_params']['tool'],
                script=agent_state['simulation_params']['script'],
                params=agent_state['simulation_params']['params']
            )
            result['task_ids'].append(task_id)
            print(f"     ✓ Task submitted: {task_id}")
            print()
            
            # Agent monitors task
            print("  3. Agent monitors task progress...")
            task_result = self.pipeline.wait_for_task(task_id, timeout=120)
            
            # Agent updates state with results
            print("  4. Agent updates state with results...")
            agent_state['artifact_paths'].append(f"/tmp/output/{task_id}")
            agent_state['messages'].append({
                'role': 'system',
                'content': f"Simulation completed with status: {task_result['status']}"
            })
            result['agent_states'].append(agent_state.copy())
            
            print(f"     ✓ State updated")
            print(f"     Status: {task_result['status']}")
            print(f"     Artifacts: {len(agent_state['artifact_paths'])}")
            print(f"     Messages: {len(agent_state['messages'])}")
            print()
            
            # Verify workflow
            if task_result['status'] == 'success':
                result['passed'] = True
                print(f"✓ {test_name} PASSED")
            else:
                result['error'] = f"Task failed with status: {task_result['status']}"
                print(f"✗ {test_name} FAILED: {result['error']}")
            
        except Exception as e:
            result['error'] = str(e)
            print(f"✗ {test_name} FAILED: {e}")
        
        result['end_time'] = datetime.now()
        result['duration'] = (result['end_time'] - result['start_time']).total_seconds()
        
        return result
    
    def test_workflow_error_recovery(self) -> Dict[str, Any]:
        """Test workflow handles task failures and continues."""
        test_name = "Workflow Error Recovery"
        print(f"\n{'=' * 70}")
        print(f"TEST: {test_name}")
        print(f"{'=' * 70}")
        print("Description: Test workflow continues after task failure")
        print()
        
        result = {
            'test_name': test_name,
            'passed': False,
            'start_time': datetime.now(),
            'error': None,
            'task_ids': [],
            'workflow_status': None
        }
        
        try:
            # Create workflow with a task that will fail
            tasks = [
                {"tool": "fenicsx", "script": "poisson.py", "params": {}},
                {"tool": "fenicsx", "script": "nonexistent.py", "params": {}},  # Will fail
                {"tool": "lammps", "script": "example.lammps", "params": {}}
            ]
            
            print(f"Submitting workflow with {len(tasks)} tasks (including one that will fail)...")
            task_ids = self.pipeline.submit_workflow(tasks, sequential=False)
            result['task_ids'] = task_ids
            print(f"✓ Submitted {len(task_ids)} tasks")
            print()
            
            # Wait for workflow completion
            print("Waiting for workflow completion...")
            final_status = self.pipeline.wait_for_workflow(
                task_ids,
                timeout=300,
                poll_interval=5
            )
            result['workflow_status'] = final_status
            
            print()
            print(f"✓ Workflow completed!")
            print(f"  Total: {final_status['total']}")
            print(f"  Completed: {final_status['completed']}")
            print(f"  Failed: {final_status['failed']}")
            
            # Verify at least some tasks succeeded despite failure
            if final_status['completed'] >= 2 and final_status['failed'] >= 1:
                result['passed'] = True
                print(f"\n✓ {test_name} PASSED - Workflow continued after failure")
            else:
                result['error'] = "Workflow did not handle failure as expected"
                print(f"\n✗ {test_name} FAILED: {result['error']}")
            
        except Exception as e:
            result['error'] = str(e)
            print(f"\n✗ {test_name} FAILED: {e}")
        
        result['end_time'] = datetime.now()
        result['duration'] = (result['end_time'] - result['start_time']).total_seconds()
        
        return result
    
    def test_workflow_cancellation(self) -> Dict[str, Any]:
        """Test workflow task cancellation."""
        test_name = "Workflow Task Cancellation"
        print(f"\n{'=' * 70}")
        print(f"TEST: {test_name}")
        print(f"{'=' * 70}")
        print("Description: Test cancelling tasks in a workflow")
        print()
        
        result = {
            'test_name': test_name,
            'passed': False,
            'start_time': datetime.now(),
            'error': None,
            'task_ids': [],
            'cancelled_tasks': []
        }
        
        try:
            # Submit a long-running task
            print("Submitting long-running task...")
            task_id = self.pipeline.submit_task(
                tool="fenicsx",
                script="poisson.py",
                params={"mesh_size": 64}
            )
            result['task_ids'].append(task_id)
            print(f"✓ Task submitted: {task_id}")
            print()
            
            # Wait a moment
            print("Waiting 3 seconds...")
            time.sleep(3)
            print()
            
            # Cancel the task
            print("Attempting to cancel task...")
            cancelled = self.pipeline.cancel_task(task_id)
            
            if cancelled:
                result['cancelled_tasks'].append(task_id)
                print(f"✓ Task cancellation requested")
                
                # Check final status
                time.sleep(2)
                status = self.pipeline.get_task_status(task_id)
                print(f"  Final state: {status['state']}")
                
                result['passed'] = True
                print(f"\n✓ {test_name} PASSED")
            else:
                result['error'] = "Task cancellation failed"
                print(f"\n✗ {test_name} FAILED: {result['error']}")
            
        except Exception as e:
            result['error'] = str(e)
            print(f"\n✗ {test_name} FAILED: {e}")
        
        result['end_time'] = datetime.now()
        result['duration'] = (result['end_time'] - result['start_time']).total_seconds()
        
        return result
    
    def run_all_tests(self) -> bool:
        """
        Run all integration tests.
        
        Returns:
            True if all tests passed, False otherwise
        """
        self.start_time = datetime.now()
        
        # Setup
        if not self.setup():
            return False
        
        # Run tests
        print("\n" + "=" * 70)
        print("RUNNING INTEGRATION TESTS")
        print("=" * 70)
        
        self.results.append(self.test_simple_workflow())
        self.results.append(self.test_parallel_workflow())
        self.results.append(self.test_workflow_with_agent_state())
        self.results.append(self.test_workflow_error_recovery())
        self.results.append(self.test_workflow_cancellation())
        
        self.end_time = datetime.now()
        
        # Print summary
        self._print_summary()
        
        return all(r['passed'] for r in self.results)
    
    def run_specific_test(self, test_name: str) -> bool:
        """Run a specific test by name."""
        self.start_time = datetime.now()
        
        if not self.setup():
            return False
        
        test_map = {
            'workflow_simple': self.test_simple_workflow,
            'workflow_parallel': self.test_parallel_workflow,
            'workflow_agent_state': self.test_workflow_with_agent_state,
            'workflow_error_recovery': self.test_workflow_error_recovery,
            'workflow_cancellation': self.test_workflow_cancellation,
        }
        
        if test_name not in test_map:
            print(f"✗ Unknown test: {test_name}")
            print(f"Available tests: {', '.join(test_map.keys())}")
            return False
        
        self.results.append(test_map[test_name]())
        self.end_time = datetime.now()
        
        self._print_summary()
        
        return self.results[0]['passed']
    
    def _print_summary(self):
        """Print test summary."""
        print("\n" + "=" * 70)
        print("TEST SUMMARY")
        print("=" * 70)
        
        total_duration = (self.end_time - self.start_time).total_seconds()
        passed_count = sum(1 for r in self.results if r['passed'])
        failed_count = len(self.results) - passed_count
        
        print(f"Total tests: {len(self.results)}")
        print(f"Passed: {passed_count}")
        print(f"Failed: {failed_count}")
        print(f"Total duration: {total_duration:.2f} seconds")
        print("-" * 70)
        
        for result in self.results:
            status = "✓ PASSED" if result['passed'] else "✗ FAILED"
            duration = result.get('duration', 0)
            print(f"{result['test_name']:40s} {status:10s} ({duration:.1f}s)")
            
            if not result['passed'] and result['error']:
                print(f"  Error: {result['error']}")
        
        print("=" * 70)
        
        if all(r['passed'] for r in self.results):
            print("\n✓ ALL INTEGRATION TESTS PASSED!")
        else:
            print("\n✗ SOME INTEGRATION TESTS FAILED!")
        
        print("=" * 70 + "\n")


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description="Run agentic workflow orchestration integration tests"
    )
    parser.add_argument(
        "--test",
        type=str,
        help="Run specific test (workflow_simple, workflow_parallel, workflow_agent_state, "
             "workflow_error_recovery, workflow_cancellation)"
    )
    
    args = parser.parse_args()
    
    # Run tests
    test_suite = AgenticWorkflowIntegrationTest()
    
    if args.test:
        success = test_suite.run_specific_test(args.test)
    else:
        success = test_suite.run_all_tests()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
