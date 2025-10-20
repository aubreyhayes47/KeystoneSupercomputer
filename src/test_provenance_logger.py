#!/usr/bin/env python3
"""
Unit Tests for Provenance Logging System
=========================================

These tests validate the ProvenanceLogger functionality including:
- Workflow tracking and metadata capture
- Tool call recording
- Agent action tracking
- Input/output file linking
- Software version capture
- Environment capture
- Provenance finalization and retrieval
"""

import sys
import json
import tempfile
import shutil
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent))

from provenance_logger import ProvenanceLogger, get_provenance_logger


def test_provenance_logger_instantiation():
    """Test that ProvenanceLogger can be instantiated."""
    with tempfile.TemporaryDirectory() as tmpdir:
        logger = ProvenanceLogger(log_dir=tmpdir)
        assert logger is not None
        assert logger.log_dir == Path(tmpdir)
        assert logger.log_dir.exists()
    print("✓ ProvenanceLogger instantiation test passed")


def test_start_workflow():
    """Test starting a workflow and capturing initial metadata."""
    with tempfile.TemporaryDirectory() as tmpdir:
        logger = ProvenanceLogger(log_dir=tmpdir)
        
        workflow_id = logger.start_workflow(
            user_prompt="Test simulation run",
            workflow_plan={"tool": "fenicsx", "script": "test.py"}
        )
        
        assert workflow_id is not None
        assert isinstance(workflow_id, str)
        assert len(workflow_id) > 0
        
        # Check that workflow is tracked
        provenance = logger.get_provenance(workflow_id)
        assert provenance is not None
        assert provenance["user_prompt"] == "Test simulation run"
        assert provenance["workflow_plan"]["tool"] == "fenicsx"
        assert "software_versions" in provenance
        assert "environment" in provenance
        assert "random_seeds" in provenance
        
    print("✓ Start workflow test passed")


def test_record_tool_call():
    """Test recording tool calls."""
    with tempfile.TemporaryDirectory() as tmpdir:
        logger = ProvenanceLogger(log_dir=tmpdir)
        
        workflow_id = logger.start_workflow(
            user_prompt="Test tool call",
            workflow_plan={}
        )
        
        # Record a tool call
        logger.record_tool_call(
            workflow_id=workflow_id,
            tool="fenicsx",
            parameters={"mesh_size": 64},
            script="poisson.py",
            task_id="task-123"
        )
        
        # Verify tool call was recorded
        provenance = logger.get_provenance(workflow_id)
        assert len(provenance["tool_calls"]) == 1
        assert provenance["tool_calls"][0]["tool"] == "fenicsx"
        assert provenance["tool_calls"][0]["parameters"]["mesh_size"] == 64
        assert provenance["tool_calls"][0]["script"] == "poisson.py"
        assert provenance["tool_calls"][0]["task_id"] == "task-123"
        
    print("✓ Record tool call test passed")


def test_record_agent_action():
    """Test recording agent actions."""
    with tempfile.TemporaryDirectory() as tmpdir:
        logger = ProvenanceLogger(log_dir=tmpdir)
        
        workflow_id = logger.start_workflow(
            user_prompt="Test agent actions",
            workflow_plan={}
        )
        
        # Record agent actions
        logger.record_agent_action(
            workflow_id=workflow_id,
            agent_role="conductor",
            action="analyze_request",
            details={"complexity": "high"}
        )
        
        logger.record_agent_action(
            workflow_id=workflow_id,
            agent_role="performer",
            action="execute_simulation"
        )
        
        # Verify actions were recorded in timeline
        provenance = logger.get_provenance(workflow_id)
        timeline = provenance["execution_timeline"]
        
        # Should have: workflow_started, agent_action x2
        assert len(timeline) >= 3
        
        agent_actions = [e for e in timeline if e["event"] == "agent_action"]
        assert len(agent_actions) == 2
        assert agent_actions[0]["details"]["agent_role"] == "conductor"
        assert agent_actions[1]["details"]["agent_role"] == "performer"
        
    print("✓ Record agent action test passed")


def test_add_input_output_files():
    """Test linking input and output files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        logger = ProvenanceLogger(log_dir=tmpdir)
        
        workflow_id = logger.start_workflow(
            user_prompt="Test file linking",
            workflow_plan={}
        )
        
        # Create test files
        input_file = Path(tmpdir) / "input.txt"
        input_file.write_text("test input data")
        
        output_file = Path(tmpdir) / "output.txt"
        output_file.write_text("test output data")
        
        # Add files to provenance
        logger.add_input_file(
            workflow_id=workflow_id,
            filepath=input_file,
            description="Test input file"
        )
        
        logger.add_output_file(
            workflow_id=workflow_id,
            filepath=output_file,
            description="Test output file"
        )
        
        # Verify files were linked
        provenance = logger.get_provenance(workflow_id)
        assert len(provenance["input_files"]) == 1
        assert len(provenance["output_files"]) == 1
        
        # Check input file metadata
        input_info = provenance["input_files"][0]
        assert input_info["filename"] == "input.txt"
        assert input_info["description"] == "Test input file"
        assert "checksum" in input_info
        assert input_info["size_bytes"] > 0
        
        # Check output file metadata
        output_info = provenance["output_files"][0]
        assert output_info["filename"] == "output.txt"
        assert output_info["description"] == "Test output file"
        assert "checksum" in output_info
        
    print("✓ Add input/output files test passed")


def test_finalize_workflow():
    """Test finalizing workflow and saving provenance.json."""
    with tempfile.TemporaryDirectory() as tmpdir:
        logger = ProvenanceLogger(log_dir=tmpdir)
        
        workflow_id = logger.start_workflow(
            user_prompt="Test finalization",
            workflow_plan={"tool": "fenicsx"}
        )
        
        # Record some activity
        logger.record_tool_call(
            workflow_id=workflow_id,
            tool="fenicsx",
            parameters={}
        )
        
        # Finalize workflow
        provenance_file = logger.finalize_workflow(
            workflow_id=workflow_id,
            status="completed",
            final_result={"output": "success"}
        )
        
        # Verify file was created
        assert provenance_file.exists()
        assert provenance_file.name == f"provenance_{workflow_id}.json"
        
        # Verify file contents
        with open(provenance_file, 'r') as f:
            saved_provenance = json.load(f)
        
        assert saved_provenance["workflow_id"] == workflow_id
        assert saved_provenance["status"] == "completed"
        assert saved_provenance["final_result"]["output"] == "success"
        assert "completed_at" in saved_provenance
        assert "duration_seconds" in saved_provenance
        
        # Verify workflow was removed from active workflows
        assert workflow_id not in logger._active_workflows
        
        # But can still be retrieved
        provenance = logger.get_provenance(workflow_id)
        assert provenance is not None
        assert provenance["status"] == "completed"
        
    print("✓ Finalize workflow test passed")


def test_finalize_workflow_with_error():
    """Test finalizing workflow with error status."""
    with tempfile.TemporaryDirectory() as tmpdir:
        logger = ProvenanceLogger(log_dir=tmpdir)
        
        workflow_id = logger.start_workflow(
            user_prompt="Test error case",
            workflow_plan={}
        )
        
        # Finalize with error
        provenance_file = logger.finalize_workflow(
            workflow_id=workflow_id,
            status="failed",
            error="Simulation crashed"
        )
        
        # Verify error was recorded
        with open(provenance_file, 'r') as f:
            saved_provenance = json.load(f)
        
        assert saved_provenance["status"] == "failed"
        assert saved_provenance["error"] == "Simulation crashed"
        
    print("✓ Finalize workflow with error test passed")


def test_list_workflows():
    """Test listing workflow provenance records."""
    with tempfile.TemporaryDirectory() as tmpdir:
        logger = ProvenanceLogger(log_dir=tmpdir)
        
        # Create multiple workflows
        wf1 = logger.start_workflow("Workflow 1", {})
        logger.finalize_workflow(wf1, status="completed")
        
        wf2 = logger.start_workflow("Workflow 2", {})
        logger.finalize_workflow(wf2, status="failed")
        
        wf3 = logger.start_workflow("Workflow 3", {})
        logger.finalize_workflow(wf3, status="completed")
        
        # List all workflows
        all_workflows = logger.list_workflows()
        assert len(all_workflows) == 3
        
        # List only completed workflows
        completed = logger.list_workflows(status="completed")
        assert len(completed) == 2
        
        # List only failed workflows
        failed = logger.list_workflows(status="failed")
        assert len(failed) == 1
        assert failed[0]["user_prompt"] == "Workflow 2"
        
    print("✓ List workflows test passed")


def test_software_versions_capture():
    """Test that software versions are captured."""
    with tempfile.TemporaryDirectory() as tmpdir:
        logger = ProvenanceLogger(log_dir=tmpdir)
        
        workflow_id = logger.start_workflow("Test versions", {})
        provenance = logger.get_provenance(workflow_id)
        
        versions = provenance["software_versions"]
        assert "python" in versions
        assert "platform" in versions
        # Other packages may or may not be installed
        
    print("✓ Software versions capture test passed")


def test_environment_capture():
    """Test that environment is captured."""
    with tempfile.TemporaryDirectory() as tmpdir:
        logger = ProvenanceLogger(log_dir=tmpdir)
        
        workflow_id = logger.start_workflow("Test environment", {})
        provenance = logger.get_provenance(workflow_id)
        
        env = provenance["environment"]
        assert "hostname" in env
        assert "processor" in env
        assert "python_executable" in env
        assert "working_directory" in env
        assert "user" in env
        assert "environment_variables" in env
        
    print("✓ Environment capture test passed")


def test_global_logger_singleton():
    """Test that get_provenance_logger returns a singleton."""
    logger1 = get_provenance_logger()
    logger2 = get_provenance_logger()
    
    assert logger1 is logger2
    print("✓ Global logger singleton test passed")


def test_workflow_id_generation():
    """Test workflow ID generation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        logger = ProvenanceLogger(log_dir=tmpdir)
        
        # Generate multiple IDs
        id1 = logger.start_workflow("Test 1", {})
        id2 = logger.start_workflow("Test 2", {})
        id3 = logger.start_workflow("Test 1", {})  # Same prompt
        
        # All should be unique
        assert id1 != id2
        assert id1 != id3
        assert id2 != id3
        
    print("✓ Workflow ID generation test passed")


def test_custom_workflow_id():
    """Test using custom workflow ID."""
    with tempfile.TemporaryDirectory() as tmpdir:
        logger = ProvenanceLogger(log_dir=tmpdir)
        
        custom_id = "my-custom-id-12345"
        workflow_id = logger.start_workflow(
            user_prompt="Test custom ID",
            workflow_plan={},
            workflow_id=custom_id
        )
        
        assert workflow_id == custom_id
        
        provenance = logger.get_provenance(custom_id)
        assert provenance["workflow_id"] == custom_id
        
    print("✓ Custom workflow ID test passed")


def test_metadata_field():
    """Test custom metadata field."""
    with tempfile.TemporaryDirectory() as tmpdir:
        logger = ProvenanceLogger(log_dir=tmpdir)
        
        workflow_id = logger.start_workflow(
            user_prompt="Test metadata",
            workflow_plan={},
            metadata={
                "project": "test_project",
                "priority": "high",
                "tags": ["simulation", "test"]
            }
        )
        
        provenance = logger.get_provenance(workflow_id)
        assert provenance["metadata"]["project"] == "test_project"
        assert provenance["metadata"]["priority"] == "high"
        assert "simulation" in provenance["metadata"]["tags"]
        
    print("✓ Metadata field test passed")


def run_all_tests():
    """Run all unit tests."""
    print("=" * 70)
    print("Running Provenance Logger Unit Tests")
    print("=" * 70)
    print()
    
    tests = [
        test_provenance_logger_instantiation,
        test_start_workflow,
        test_record_tool_call,
        test_record_agent_action,
        test_add_input_output_files,
        test_finalize_workflow,
        test_finalize_workflow_with_error,
        test_list_workflows,
        test_software_versions_capture,
        test_environment_capture,
        test_global_logger_singleton,
        test_workflow_id_generation,
        test_custom_workflow_id,
        test_metadata_field,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"✗ {test.__name__} failed: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {test.__name__} error: {e}")
            failed += 1
    
    print()
    print("=" * 70)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("=" * 70)
    
    return failed == 0


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
