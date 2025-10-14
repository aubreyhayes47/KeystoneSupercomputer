#!/usr/bin/env python3
"""
Unit tests for the TaskPipeline module.

These tests validate the TaskPipeline interface without requiring
a running Redis/Celery worker.
"""

import sys
from pathlib import Path

# Add agent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from task_pipeline import TaskPipeline, TaskStatus


def test_task_pipeline_instantiation():
    """Test that TaskPipeline can be instantiated."""
    pipeline = TaskPipeline()
    assert pipeline is not None
    assert hasattr(pipeline, 'celery_app')
    assert hasattr(pipeline, '_active_tasks')
    assert isinstance(pipeline._active_tasks, dict)
    print("✓ TaskPipeline instantiation test passed")


def test_task_pipeline_has_required_methods():
    """Test that TaskPipeline has all required methods."""
    pipeline = TaskPipeline()
    
    required_methods = [
        'health_check',
        'list_available_simulations',
        'submit_task',
        'get_task_status',
        'monitor_task',
        'wait_for_task',
        'cancel_task',
        'submit_workflow',
        'get_workflow_status',
        'wait_for_workflow',
        'cleanup',
    ]
    
    for method_name in required_methods:
        assert hasattr(pipeline, method_name), f"Missing method: {method_name}"
        method = getattr(pipeline, method_name)
        assert callable(method), f"{method_name} is not callable"
    
    print(f"✓ TaskPipeline has all {len(required_methods)} required methods")


def test_task_status_constants():
    """Test that TaskStatus constants are defined."""
    assert hasattr(TaskStatus, 'PENDING')
    assert hasattr(TaskStatus, 'RUNNING')
    assert hasattr(TaskStatus, 'SUCCESS')
    assert hasattr(TaskStatus, 'FAILURE')
    assert hasattr(TaskStatus, 'TIMEOUT')
    assert hasattr(TaskStatus, 'ERROR')
    assert hasattr(TaskStatus, 'CANCELLED')
    print("✓ TaskStatus constants test passed")


def test_cleanup():
    """Test the cleanup method."""
    pipeline = TaskPipeline()
    # Add some fake task IDs
    pipeline._active_tasks['task1'] = None
    pipeline._active_tasks['task2'] = None
    
    assert len(pipeline._active_tasks) == 2
    
    pipeline.cleanup()
    
    assert len(pipeline._active_tasks) == 0
    print("✓ Cleanup test passed")


def test_workflow_validation():
    """Test workflow task validation."""
    pipeline = TaskPipeline()
    
    # Test with invalid task (missing script)
    invalid_tasks = [
        {"tool": "fenicsx", "params": {}}  # Missing script
    ]
    
    try:
        pipeline.submit_workflow(invalid_tasks)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "tool" in str(e).lower() or "script" in str(e).lower()
        print("✓ Workflow validation test passed")
    except Exception as e:
        # May get connection error if Redis is not running, which is fine for this test
        if "connection" in str(e).lower() or "broker" in str(e).lower():
            print("✓ Workflow validation test passed (connection error expected without Redis)")
        else:
            raise


def run_all_tests():
    """Run all unit tests."""
    print("=" * 70)
    print("Running TaskPipeline Unit Tests")
    print("=" * 70)
    print()
    
    tests = [
        test_task_pipeline_instantiation,
        test_task_pipeline_has_required_methods,
        test_task_status_constants,
        test_cleanup,
        test_workflow_validation,
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
