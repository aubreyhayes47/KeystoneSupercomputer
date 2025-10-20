#!/usr/bin/env python3
"""
Unit Tests for Provenance Validation
=====================================

These tests validate the provenance validation functionality including:
- Required field validation
- Type checking
- Status-dependent field validation
- Timestamp format validation
- Tool call structure validation
- File metadata validation
- Timeline event validation
"""

import sys
import json
import tempfile
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent))

from provenance_logger import ProvenanceLogger, validate_provenance_file


def test_validate_complete_provenance():
    """Test validation of a complete, valid provenance record."""
    with tempfile.TemporaryDirectory() as tmpdir:
        logger = ProvenanceLogger(log_dir=tmpdir)
        
        # Create a complete workflow
        workflow_id = logger.start_workflow(
            user_prompt="Test workflow",
            workflow_plan={"tool": "fenicsx"},
            metadata={"test": "value"}
        )
        
        logger.record_tool_call(
            workflow_id=workflow_id,
            tool="fenicsx",
            parameters={"param": "value"}
        )
        
        logger.finalize_workflow(
            workflow_id=workflow_id,
            status="completed",
            final_result={"result": "success"}
        )
        
        # Validate the provenance
        provenance = logger.get_provenance(workflow_id)
        result = logger.validate_provenance(provenance)
        
        assert result["valid"] is True, f"Validation failed: {result['errors']}"
        assert len(result["errors"]) == 0
        assert result["version"] == "1.0.0"
        
    print("✓ Validate complete provenance test passed")


def test_validate_missing_required_fields():
    """Test validation catches missing required fields."""
    logger = ProvenanceLogger()
    
    # Create incomplete provenance
    incomplete_provenance = {
        "provenance_version": "1.0.0",
        "workflow_id": "test-123",
        # Missing many required fields
    }
    
    result = logger.validate_provenance(incomplete_provenance)
    
    assert result["valid"] is False
    assert len(result["errors"]) > 0
    
    # Check that specific required fields are reported
    error_text = " ".join(result["errors"])
    assert "user_prompt" in error_text
    assert "workflow_plan" in error_text
    assert "tool_calls" in error_text
    
    print("✓ Validate missing required fields test passed")


def test_validate_wrong_field_types():
    """Test validation catches wrong field types."""
    logger = ProvenanceLogger()
    
    provenance = {
        "provenance_version": "1.0.0",
        "workflow_id": "test-123",
        "created_at": "2025-10-20T15:00:00Z",
        "status": "completed",
        "user_prompt": "Test",
        "workflow_plan": "should be dict not string",  # Wrong type
        "tool_calls": "should be list",  # Wrong type
        "software_versions": {},
        "environment": {},
        "random_seeds": {},
        "input_files": [],
        "output_files": [],
        "execution_timeline": []
    }
    
    result = logger.validate_provenance(provenance)
    
    assert result["valid"] is False
    assert len(result["errors"]) > 0
    
    error_text = " ".join(result["errors"])
    assert "workflow_plan" in error_text
    assert "tool_calls" in error_text
    
    print("✓ Validate wrong field types test passed")


def test_validate_status_dependent_fields():
    """Test validation of status-dependent required fields."""
    logger = ProvenanceLogger()
    
    # Completed workflow without completed_at
    provenance = {
        "provenance_version": "1.0.0",
        "workflow_id": "test-123",
        "created_at": "2025-10-20T15:00:00Z",
        "status": "completed",  # Completed status
        "user_prompt": "Test",
        "workflow_plan": {},
        "tool_calls": [],
        "software_versions": {},
        "environment": {},
        "random_seeds": {},
        "input_files": [],
        "output_files": [],
        "execution_timeline": []
        # Missing completed_at and duration_seconds
    }
    
    result = logger.validate_provenance(provenance)
    
    assert result["valid"] is False
    error_text = " ".join(result["errors"])
    assert "completed_at" in error_text
    assert "duration_seconds" in error_text
    
    print("✓ Validate status-dependent fields test passed")


def test_validate_timestamp_format():
    """Test validation of timestamp formats."""
    logger = ProvenanceLogger()
    
    provenance = {
        "provenance_version": "1.0.0",
        "workflow_id": "test-123",
        "created_at": "2025-10-20T15:00:00",  # Missing Z suffix
        "status": "running",
        "user_prompt": "Test",
        "workflow_plan": {},
        "tool_calls": [],
        "software_versions": {},
        "environment": {},
        "random_seeds": {},
        "input_files": [],
        "output_files": [],
        "execution_timeline": []
    }
    
    result = logger.validate_provenance(provenance, strict=False)
    
    # Should have warnings about timestamp format
    assert len(result["warnings"]) > 0
    warning_text = " ".join(result["warnings"])
    assert "created_at" in warning_text
    assert "Z suffix" in warning_text
    
    print("✓ Validate timestamp format test passed")


def test_validate_tool_calls_structure():
    """Test validation of tool call structure."""
    logger = ProvenanceLogger()
    
    provenance = {
        "provenance_version": "1.0.0",
        "workflow_id": "test-123",
        "created_at": "2025-10-20T15:00:00Z",
        "status": "running",
        "user_prompt": "Test",
        "workflow_plan": {},
        "tool_calls": [
            {
                # Missing timestamp, tool, parameters
                "script": "test.py"
            }
        ],
        "software_versions": {},
        "environment": {},
        "random_seeds": {},
        "input_files": [],
        "output_files": [],
        "execution_timeline": []
    }
    
    result = logger.validate_provenance(provenance, strict=False)
    
    # Should have warnings about missing tool call fields
    assert len(result["warnings"]) > 0
    warning_text = " ".join(result["warnings"])
    assert "tool_calls[0]" in warning_text
    
    print("✓ Validate tool calls structure test passed")


def test_validate_software_versions():
    """Test validation of software versions."""
    logger = ProvenanceLogger()
    
    # Empty software versions
    provenance = {
        "provenance_version": "1.0.0",
        "workflow_id": "test-123",
        "created_at": "2025-10-20T15:00:00Z",
        "status": "running",
        "user_prompt": "Test",
        "workflow_plan": {},
        "tool_calls": [],
        "software_versions": {},  # Empty
        "environment": {},
        "random_seeds": {},
        "input_files": [],
        "output_files": [],
        "execution_timeline": []
    }
    
    result = logger.validate_provenance(provenance, strict=False)
    
    warning_text = " ".join(result["warnings"])
    assert "software_versions is empty" in warning_text
    
    print("✓ Validate software versions test passed")


def test_validate_environment_structure():
    """Test validation of environment structure."""
    logger = ProvenanceLogger()
    
    provenance = {
        "provenance_version": "1.0.0",
        "workflow_id": "test-123",
        "created_at": "2025-10-20T15:00:00Z",
        "status": "running",
        "user_prompt": "Test",
        "workflow_plan": {},
        "tool_calls": [],
        "software_versions": {},
        "environment": {
            "hostname": "test-host"
            # Missing other required fields
        },
        "random_seeds": {},
        "input_files": [],
        "output_files": [],
        "execution_timeline": []
    }
    
    result = logger.validate_provenance(provenance, strict=False)
    
    warning_text = " ".join(result["warnings"])
    assert "processor" in warning_text or "python_executable" in warning_text
    
    print("✓ Validate environment structure test passed")


def test_validate_file_metadata():
    """Test validation of file metadata."""
    logger = ProvenanceLogger()
    
    provenance = {
        "provenance_version": "1.0.0",
        "workflow_id": "test-123",
        "created_at": "2025-10-20T15:00:00Z",
        "status": "running",
        "user_prompt": "Test",
        "workflow_plan": {},
        "tool_calls": [],
        "software_versions": {},
        "environment": {},
        "random_seeds": {},
        "input_files": [],
        "output_files": [
            {
                "path": "/test/output.txt"
                # Missing filename and checksum
            }
        ],
        "execution_timeline": []
    }
    
    result = logger.validate_provenance(provenance, strict=False)
    
    warning_text = " ".join(result["warnings"])
    assert "output_files[0]" in warning_text
    assert "filename" in warning_text or "checksum" in warning_text
    
    print("✓ Validate file metadata test passed")


def test_validate_execution_timeline():
    """Test validation of execution timeline."""
    logger = ProvenanceLogger()
    
    # Empty timeline
    provenance = {
        "provenance_version": "1.0.0",
        "workflow_id": "test-123",
        "created_at": "2025-10-20T15:00:00Z",
        "status": "running",
        "user_prompt": "Test",
        "workflow_plan": {},
        "tool_calls": [],
        "software_versions": {},
        "environment": {},
        "random_seeds": {},
        "input_files": [],
        "output_files": [],
        "execution_timeline": []  # Empty
    }
    
    result = logger.validate_provenance(provenance, strict=False)
    
    warning_text = " ".join(result["warnings"])
    assert "execution_timeline is empty" in warning_text
    
    print("✓ Validate execution timeline test passed")


def test_validate_failed_workflow():
    """Test validation of failed workflow."""
    logger = ProvenanceLogger()
    
    provenance = {
        "provenance_version": "1.0.0",
        "workflow_id": "test-123",
        "created_at": "2025-10-20T15:00:00Z",
        "completed_at": "2025-10-20T15:01:00Z",
        "duration_seconds": 60,
        "status": "failed",
        "user_prompt": "Test",
        "workflow_plan": {},
        "tool_calls": [],
        "software_versions": {},
        "environment": {},
        "random_seeds": {},
        "input_files": [],
        "output_files": [],
        "execution_timeline": [
            {"timestamp": "2025-10-20T15:00:00Z", "event": "workflow_started"},
            {"timestamp": "2025-10-20T15:01:00Z", "event": "workflow_completed"}
        ]
        # Missing error field
    }
    
    result = logger.validate_provenance(provenance, strict=False)
    
    warning_text = " ".join(result["warnings"])
    assert "error" in warning_text.lower()
    
    print("✓ Validate failed workflow test passed")


def test_validate_provenance_file():
    """Test validation of provenance file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        logger = ProvenanceLogger(log_dir=tmpdir)
        
        # Create and finalize a workflow with final_result
        workflow_id = logger.start_workflow(
            user_prompt="Test",
            workflow_plan={}
        )
        provenance_file = logger.finalize_workflow(
            workflow_id=workflow_id,
            status="completed",
            final_result={"status": "success"}
        )
        
        # Validate the file
        result = validate_provenance_file(provenance_file)
        
        assert result["valid"] is True, f"Validation failed: {result}"
        assert len(result["errors"]) == 0
        assert "filepath" in result
        
    print("✓ Validate provenance file test passed")


def test_validate_nonexistent_file():
    """Test validation of non-existent file."""
    result = validate_provenance_file("/nonexistent/file.json")
    
    assert result["valid"] is False
    assert len(result["errors"]) > 0
    assert "not found" in result["errors"][0].lower()
    
    print("✓ Validate non-existent file test passed")


def test_validate_invalid_json():
    """Test validation of invalid JSON file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        invalid_file = Path(tmpdir) / "invalid.json"
        invalid_file.write_text("{ invalid json }")
        
        result = validate_provenance_file(invalid_file)
        
        assert result["valid"] is False
        assert len(result["errors"]) > 0
        assert "json" in result["errors"][0].lower()
    
    print("✓ Validate invalid JSON test passed")


def test_strict_vs_non_strict_validation():
    """Test difference between strict and non-strict validation."""
    logger = ProvenanceLogger()
    
    # Provenance with warnings but no errors
    provenance = {
        "provenance_version": "1.0.0",
        "workflow_id": "test-123",
        "created_at": "2025-10-20T15:00:00Z",
        "status": "running",
        "user_prompt": "Test",
        "workflow_plan": {},
        "tool_calls": [],
        "software_versions": {},  # Empty - will generate warning
        "environment": {},
        "random_seeds": {},
        "input_files": [],
        "output_files": [],
        "execution_timeline": []
    }
    
    # Non-strict mode: warnings don't fail validation
    result_non_strict = logger.validate_provenance(provenance, strict=False)
    assert result_non_strict["valid"] is True
    assert len(result_non_strict["warnings"]) > 0
    
    # Strict mode: warnings fail validation
    result_strict = logger.validate_provenance(provenance, strict=True)
    assert result_strict["valid"] is False
    assert len(result_strict["warnings"]) > 0
    
    print("✓ Strict vs non-strict validation test passed")


def run_all_tests():
    """Run all validation tests."""
    print("=" * 70)
    print("Running Provenance Validation Tests")
    print("=" * 70)
    print()
    
    tests = [
        test_validate_complete_provenance,
        test_validate_missing_required_fields,
        test_validate_wrong_field_types,
        test_validate_status_dependent_fields,
        test_validate_timestamp_format,
        test_validate_tool_calls_structure,
        test_validate_software_versions,
        test_validate_environment_structure,
        test_validate_file_metadata,
        test_validate_execution_timeline,
        test_validate_failed_workflow,
        test_validate_provenance_file,
        test_validate_nonexistent_file,
        test_validate_invalid_json,
        test_strict_vs_non_strict_validation,
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
