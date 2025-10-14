#!/usr/bin/env python3
"""
Unit tests for the CLI module.

These tests validate the CLI commands structure and basic functionality
without requiring a running Redis/Celery worker.
"""

import sys
import json
import tempfile
from pathlib import Path
from click.testing import CliRunner

# Add agent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from cli import cli


def test_cli_help():
    """Test that CLI help is displayed correctly."""
    runner = CliRunner()
    result = runner.invoke(cli, ['--help'])
    assert result.exit_code == 0
    assert 'Keystone Supercomputer CLI' in result.output
    assert 'submit' in result.output
    assert 'status' in result.output
    assert 'health' in result.output
    print("✓ CLI help test passed")


def test_submit_command_help():
    """Test that submit command help is displayed correctly."""
    runner = CliRunner()
    result = runner.invoke(cli, ['submit', '--help'])
    assert result.exit_code == 0
    assert 'Submit a simulation task' in result.output
    assert 'TOOL' in result.output
    assert 'SCRIPT' in result.output
    assert '--params' in result.output
    assert '--wait' in result.output
    print("✓ Submit command help test passed")


def test_status_command_help():
    """Test that status command help is displayed correctly."""
    runner = CliRunner()
    result = runner.invoke(cli, ['status', '--help'])
    assert result.exit_code == 0
    assert 'Check the status of a task' in result.output
    assert 'TASK_ID' in result.output
    assert '--monitor' in result.output
    print("✓ Status command help test passed")


def test_health_command_help():
    """Test that health command help is displayed correctly."""
    runner = CliRunner()
    result = runner.invoke(cli, ['health', '--help'])
    assert result.exit_code == 0
    assert 'Check the health of the Celery worker' in result.output
    print("✓ Health command help test passed")


def test_list_tools_command_help():
    """Test that list-tools command help is displayed correctly."""
    runner = CliRunner()
    result = runner.invoke(cli, ['list-tools', '--help'])
    assert result.exit_code == 0
    assert 'List available simulation tools' in result.output
    print("✓ List-tools command help test passed")


def test_cancel_command_help():
    """Test that cancel command help is displayed correctly."""
    runner = CliRunner()
    result = runner.invoke(cli, ['cancel', '--help'])
    assert result.exit_code == 0
    assert 'Cancel a running or pending task' in result.output
    assert 'TASK_ID' in result.output
    print("✓ Cancel command help test passed")


def test_submit_workflow_command_help():
    """Test that submit-workflow command help is displayed correctly."""
    runner = CliRunner()
    result = runner.invoke(cli, ['submit-workflow', '--help'])
    assert result.exit_code == 0
    assert 'Submit a workflow from a JSON file' in result.output
    assert 'WORKFLOW_FILE' in result.output
    assert '--sequential' in result.output
    assert '--parallel' in result.output
    print("✓ Submit-workflow command help test passed")


def test_workflow_status_command_help():
    """Test that workflow-status command help is displayed correctly."""
    runner = CliRunner()
    result = runner.invoke(cli, ['workflow-status', '--help'])
    assert result.exit_code == 0
    assert 'Check the status of multiple tasks' in result.output
    assert 'TASK_IDS' in result.output
    print("✓ Workflow-status command help test passed")


def test_submit_with_invalid_json_params():
    """Test that submit command validates JSON parameters."""
    runner = CliRunner()
    result = runner.invoke(cli, ['submit', 'fenicsx', 'poisson.py', '-p', 'invalid json'])
    assert result.exit_code != 0
    assert 'Invalid JSON' in result.output or 'JSONDecodeError' in str(result.exception)
    print("✓ Submit with invalid JSON params test passed")


def test_submit_workflow_with_invalid_file():
    """Test that submit-workflow validates file existence."""
    runner = CliRunner()
    result = runner.invoke(cli, ['submit-workflow', '/nonexistent/file.json'])
    assert result.exit_code != 0
    # Click will handle the file validation
    print("✓ Submit-workflow with invalid file test passed")


def test_submit_workflow_with_valid_json_structure():
    """Test that submit-workflow accepts valid JSON workflow files."""
    runner = CliRunner()
    
    # Create a temporary workflow file
    workflow = [
        {"tool": "fenicsx", "script": "poisson.py", "params": {"mesh_size": 32}},
        {"tool": "lammps", "script": "example.lammps", "params": {}}
    ]
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(workflow, f)
        temp_file = f.name
    
    try:
        # This will fail because Redis is not running, but it should validate the JSON
        result = runner.invoke(cli, ['submit-workflow', temp_file, '--no-wait'])
        # Either succeeds or fails with connection error (not JSON error)
        if 'Invalid JSON' in result.output:
            assert False, "Should not complain about JSON structure"
        print("✓ Submit-workflow with valid JSON structure test passed")
    finally:
        Path(temp_file).unlink()


def test_all_commands_exist():
    """Test that all expected commands are registered."""
    runner = CliRunner()
    result = runner.invoke(cli, ['--help'])
    
    expected_commands = [
        'ask',
        'health',
        'list-tools',
        'submit',
        'status',
        'cancel',
        'submit-workflow',
        'workflow-status'
    ]
    
    for command in expected_commands:
        assert command in result.output, f"Command '{command}' not found in CLI"
    
    print(f"✓ All {len(expected_commands)} expected commands exist")


def run_all_tests():
    """Run all CLI tests."""
    print("=" * 70)
    print("Running CLI Unit Tests")
    print("=" * 70)
    print()
    
    tests = [
        test_cli_help,
        test_submit_command_help,
        test_status_command_help,
        test_health_command_help,
        test_list_tools_command_help,
        test_cancel_command_help,
        test_submit_workflow_command_help,
        test_workflow_status_command_help,
        test_submit_with_invalid_json_params,
        test_submit_workflow_with_invalid_file,
        test_submit_workflow_with_valid_json_structure,
        test_all_commands_exist,
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
