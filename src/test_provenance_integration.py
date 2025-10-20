#!/usr/bin/env python3
"""
Integration Test for Provenance System
=======================================

This test simulates a complete workflow and verifies that provenance
files are generated correctly by the integrated system.
"""

import sys
import json
import time
from pathlib import Path
import tempfile

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent))

from provenance_logger import ProvenanceLogger, get_provenance_logger


def test_end_to_end_provenance():
    """Test complete end-to-end provenance generation."""
    print("\n" + "=" * 70)
    print("Integration Test: End-to-End Provenance Generation")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        logger = ProvenanceLogger(log_dir=tmpdir)
        
        # Simulate a complete simulation workflow
        print("\n1. Starting workflow (simulating Celery task)...")
        workflow_id = logger.start_workflow(
            user_prompt="Run fenicsx simulation: poisson.py",
            workflow_plan={
                "task_id": "test-task-123",
                "tool": "fenicsx",
                "script": "poisson.py",
                "params": {"mesh_size": 64}
            },
            workflow_id="test-task-123"
        )
        print(f"   Workflow ID: {workflow_id}")
        
        # Simulate tool call
        print("\n2. Recording tool call...")
        logger.record_tool_call(
            workflow_id=workflow_id,
            tool="fenicsx",
            script="poisson.py",
            parameters={"mesh_size": 64},
            task_id="test-task-123"
        )
        
        # Simulate some processing time
        time.sleep(0.1)
        
        # Simulate output file creation
        print("\n3. Linking output files...")
        output_file = Path(tmpdir) / "solution.vtk"
        output_file.write_text("VTK output data here")
        logger.add_output_file(
            workflow_id=workflow_id,
            filepath=output_file,
            description="FEM solution field"
        )
        
        # Finalize workflow
        print("\n4. Finalizing workflow...")
        provenance_file = logger.finalize_workflow(
            workflow_id=workflow_id,
            status="completed",
            final_result={
                "status": "success",
                "tool": "fenicsx",
                "returncode": 0,
                "resource_usage": {
                    "cpu_total_seconds": 89.2,
                    "memory_peak_mb": 256.5,
                    "duration_seconds": 95.5
                }
            }
        )
        
        print(f"   Provenance file: {provenance_file}")
        
        # Verify provenance file
        print("\n5. Verifying provenance file...")
        assert provenance_file.exists(), "Provenance file not created"
        
        with open(provenance_file, 'r') as f:
            prov = json.load(f)
        
        # Verify all required fields
        required_fields = [
            "provenance_version",
            "workflow_id",
            "created_at",
            "completed_at",
            "duration_seconds",
            "status",
            "user_prompt",
            "workflow_plan",
            "tool_calls",
            "software_versions",
            "environment",
            "random_seeds",
            "output_files",
            "execution_timeline",
            "final_result"
        ]
        
        for field in required_fields:
            assert field in prov, f"Missing field: {field}"
            print(f"   ✓ {field}")
        
        # Verify field contents
        print("\n6. Verifying field contents...")
        assert prov["provenance_version"] == "1.0.0"
        assert prov["workflow_id"] == "test-task-123"
        assert prov["status"] == "completed"
        assert len(prov["tool_calls"]) == 1
        assert prov["tool_calls"][0]["tool"] == "fenicsx"
        assert len(prov["output_files"]) == 1
        assert prov["output_files"][0]["filename"] == "solution.vtk"
        print("   ✓ All field contents valid")
        
        # Display summary
        print("\n7. Provenance summary:")
        print(f"   - Workflow ID: {prov['workflow_id']}")
        print(f"   - Status: {prov['status']}")
        print(f"   - Duration: {prov['duration_seconds']:.3f}s")
        print(f"   - Tool calls: {len(prov['tool_calls'])}")
        print(f"   - Timeline events: {len(prov['execution_timeline'])}")
        print(f"   - Output files: {len(prov['output_files'])}")
        print(f"   - Software versions: {len(prov['software_versions'])}")
        
        print("\n✓ End-to-end test passed!")
        return True


def test_multi_agent_workflow_provenance():
    """Test provenance generation for multi-agent workflow."""
    print("\n" + "=" * 70)
    print("Integration Test: Multi-Agent Workflow Provenance")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        logger = ProvenanceLogger(log_dir=tmpdir)
        
        # Simulate conductor-performer workflow
        print("\n1. Starting conductor-performer workflow...")
        workflow_id = logger.start_workflow(
            user_prompt="Run structural analysis on steel beam",
            workflow_plan={
                "pattern": "conductor_performer",
                "max_iterations": 3
            },
            metadata={
                "orchestration_type": "langgraph_conductor_performer"
            }
        )
        
        # Simulate conductor actions
        print("\n2. Recording conductor actions...")
        logger.record_agent_action(
            workflow_id=workflow_id,
            agent_role="conductor",
            action="workflow_started",
            details={"user_request": "Run structural analysis on steel beam"}
        )
        
        logger.record_agent_action(
            workflow_id=workflow_id,
            agent_role="conductor",
            action="analyze_request",
            details={"complexity": "medium"}
        )
        
        # Simulate performer execution
        print("\n3. Recording performer execution...")
        logger.record_agent_action(
            workflow_id=workflow_id,
            agent_role="fenicsx_performer",
            action="execute_simulation"
        )
        
        logger.record_tool_call(
            workflow_id=workflow_id,
            tool="fenicsx",
            parameters={"material": "steel", "load": 10000}
        )
        
        # Simulate validation
        print("\n4. Recording validation...")
        logger.record_agent_action(
            workflow_id=workflow_id,
            agent_role="validator",
            action="validate_results",
            details={"validation_passed": True}
        )
        
        # Finalize
        provenance_file = logger.finalize_workflow(
            workflow_id=workflow_id,
            status="completed",
            final_result={
                "status": "completed",
                "iterations": 0
            }
        )
        
        # Verify timeline
        print("\n5. Verifying execution timeline...")
        with open(provenance_file, 'r') as f:
            prov = json.load(f)
        
        timeline = prov["execution_timeline"]
        
        # Should have: workflow_started + 4 agent actions + tool_call + workflow_completed
        assert len(timeline) >= 6, f"Timeline too short: {len(timeline)}"
        
        # Count agent actions
        agent_actions = [e for e in timeline if e["event"] == "agent_action"]
        assert len(agent_actions) >= 4, f"Not enough agent actions: {len(agent_actions)}"
        print(f"   ✓ Timeline has {len(timeline)} events")
        print(f"   ✓ Including {len(agent_actions)} agent actions")
        
        # Verify agent roles
        roles = set(e["details"].get("agent_role") for e in agent_actions if "agent_role" in e["details"])
        expected_roles = {"conductor", "fenicsx_performer", "validator"}
        assert expected_roles.issubset(roles), f"Missing roles: {expected_roles - roles}"
        print(f"   ✓ All expected agent roles present")
        
        print("\n✓ Multi-agent workflow test passed!")
        return True


def test_error_handling_provenance():
    """Test provenance generation for failed workflows."""
    print("\n" + "=" * 70)
    print("Integration Test: Error Handling Provenance")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        logger = ProvenanceLogger(log_dir=tmpdir)
        
        # Simulate failed workflow
        print("\n1. Starting workflow that will fail...")
        workflow_id = logger.start_workflow(
            user_prompt="Run simulation with invalid parameters",
            workflow_plan={"tool": "fenicsx", "invalid": True}
        )
        
        # Record tool call
        logger.record_tool_call(
            workflow_id=workflow_id,
            tool="fenicsx",
            parameters={"mesh_size": -1}  # Invalid parameter
        )
        
        # Finalize with error
        print("\n2. Finalizing with error status...")
        provenance_file = logger.finalize_workflow(
            workflow_id=workflow_id,
            status="failed",
            error="Invalid mesh size: must be positive"
        )
        
        # Verify error handling
        print("\n3. Verifying error information...")
        with open(provenance_file, 'r') as f:
            prov = json.load(f)
        
        assert prov["status"] == "failed"
        assert "error" in prov
        assert "Invalid mesh size" in prov["error"]
        print("   ✓ Error status recorded")
        print("   ✓ Error message captured")
        
        print("\n✓ Error handling test passed!")
        return True


def run_all_tests():
    """Run all integration tests."""
    print("\n" + "=" * 70)
    print("PROVENANCE INTEGRATION TESTS")
    print("=" * 70)
    print("\nThese tests verify that provenance logging works correctly")
    print("in real-world scenarios with complete workflows.")
    
    tests = [
        test_end_to_end_provenance,
        test_multi_agent_workflow_provenance,
        test_error_handling_provenance
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
        except AssertionError as e:
            print(f"\n✗ {test.__name__} failed: {e}")
            failed += 1
        except Exception as e:
            print(f"\n✗ {test.__name__} error: {e}")
            failed += 1
    
    print("\n" + "=" * 70)
    print("INTEGRATION TEST SUMMARY")
    print("=" * 70)
    print(f"Tests passed: {passed}/{len(tests)}")
    print(f"Tests failed: {failed}/{len(tests)}")
    
    if failed == 0:
        print("\n✓ ALL INTEGRATION TESTS PASSED!")
        print("\nProvenance logging is working correctly across all scenarios.")
    else:
        print("\n✗ SOME TESTS FAILED")
        print("\nPlease review the failures above.")
    
    print()
    return failed == 0


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
