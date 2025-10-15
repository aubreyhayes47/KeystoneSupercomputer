#!/usr/bin/env python3
"""
Unit tests for enhanced TaskPipeline parallel orchestration features.

Tests validate batch workflow submission, parameter sweeps, and parallel execution stats.
"""

import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add agent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from task_pipeline import TaskPipeline, TaskStatus


def test_submit_batch_workflow():
    """Test batch workflow submission."""
    pipeline = TaskPipeline()
    
    tasks = [
        {"tool": "fenicsx", "script": "poisson.py", "params": {"mesh_size": 16}},
        {"tool": "fenicsx", "script": "poisson.py", "params": {"mesh_size": 32}},
        {"tool": "fenicsx", "script": "poisson.py", "params": {"mesh_size": 64}},
    ]
    
    with patch.object(pipeline, 'submit_task', side_effect=['task-1', 'task-2', 'task-3']) as mock_submit:
        task_ids = pipeline.submit_batch_workflow(tasks, batch_size=2)
        
        assert len(task_ids) == 3
        assert mock_submit.call_count == 3
        
        print("✓ Submit batch workflow test passed")


def test_submit_batch_workflow_with_callback():
    """Test batch workflow submission with callback."""
    pipeline = TaskPipeline()
    
    tasks = [
        {"tool": "fenicsx", "script": "poisson.py", "params": {"mesh_size": i}}
        for i in [16, 32, 64, 128]
    ]
    
    callback_data = []
    
    def callback(info):
        callback_data.append(info)
    
    with patch.object(pipeline, 'submit_task', side_effect=[f'task-{i}' for i in range(4)]):
        task_ids = pipeline.submit_batch_workflow(tasks, batch_size=2, callback=callback)
        
        assert len(task_ids) == 4
        assert len(callback_data) == 2  # 2 batches
        
        # Verify batch info
        assert callback_data[0]['batch_num'] == 1
        assert callback_data[0]['batch_size'] == 2
        assert callback_data[1]['batch_num'] == 2
        assert callback_data[1]['batch_size'] == 2
        
        print("✓ Submit batch workflow callback test passed")


def test_parameter_sweep():
    """Test parameter sweep workflow submission."""
    pipeline = TaskPipeline()
    
    param_grid = {
        'mesh_size': [16, 32],
        'time_steps': [100, 200]
    }
    
    # Should generate 4 combinations (2 x 2)
    with patch.object(pipeline, 'submit_task', side_effect=[f'task-{i}' for i in range(4)]):
        task_ids = pipeline.parameter_sweep(
            tool='fenicsx',
            script='poisson.py',
            param_grid=param_grid
        )
        
        assert len(task_ids) == 4
        
        print("✓ Parameter sweep test passed")


def test_parameter_sweep_single_param():
    """Test parameter sweep with single parameter."""
    pipeline = TaskPipeline()
    
    param_grid = {
        'mesh_size': [16, 32, 64]
    }
    
    with patch.object(pipeline, 'submit_task', side_effect=['task-1', 'task-2', 'task-3']):
        task_ids = pipeline.parameter_sweep(
            tool='fenicsx',
            script='poisson.py',
            param_grid=param_grid
        )
        
        assert len(task_ids) == 3
        
        print("✓ Parameter sweep single param test passed")


def test_parameter_sweep_three_params():
    """Test parameter sweep with three parameters."""
    pipeline = TaskPipeline()
    
    param_grid = {
        'mesh_size': [16, 32],
        'time_steps': [100, 200],
        'tolerance': [0.01, 0.001]
    }
    
    # Should generate 8 combinations (2 x 2 x 2)
    with patch.object(pipeline, 'submit_task', side_effect=[f'task-{i}' for i in range(8)]):
        task_ids = pipeline.parameter_sweep(
            tool='fenicsx',
            script='poisson.py',
            param_grid=param_grid
        )
        
        assert len(task_ids) == 8
        
        print("✓ Parameter sweep three params test passed")


def test_wait_for_any():
    """Test waiting for any task to complete."""
    pipeline = TaskPipeline()
    
    task_ids = ['task-1', 'task-2', 'task-3']
    
    # Mock status - task-2 completes first
    call_count = [0]
    
    def mock_get_status(task_id):
        call_count[0] += 1
        if task_id == 'task-2' and call_count[0] > 2:
            return {'ready': True, 'state': TaskStatus.SUCCESS, 'result': {'status': 'success'}}
        return {'ready': False, 'state': TaskStatus.RUNNING}
    
    with patch.object(pipeline, 'get_task_status', side_effect=mock_get_status):
        result = pipeline.wait_for_any(task_ids, timeout=10)
        
        assert result['task_id'] == 'task-2'
        assert result['status']['ready'] == True
        
        print("✓ Wait for any test passed")


def test_wait_for_any_timeout():
    """Test wait_for_any timeout handling."""
    pipeline = TaskPipeline()
    
    task_ids = ['task-1', 'task-2']
    
    def mock_get_status(task_id):
        return {'ready': False, 'state': TaskStatus.RUNNING}
    
    with patch.object(pipeline, 'get_task_status', side_effect=mock_get_status):
        try:
            result = pipeline.wait_for_any(task_ids, timeout=0.5)
            assert False, "Should have raised TimeoutError"
        except TimeoutError as e:
            assert "No task completed" in str(e)
            print("✓ Wait for any timeout test passed")


def test_get_parallel_execution_stats():
    """Test parallel execution statistics calculation."""
    pipeline = TaskPipeline()
    
    task_ids = ['task-1', 'task-2', 'task-3', 'task-4']
    
    # Mock task statuses with varying durations
    def mock_get_status(task_id):
        status_map = {
            'task-1': {
                'ready': True,
                'successful': True,
                'state': TaskStatus.SUCCESS,
                'result': {'status': 'success', 'duration_seconds': 10.0}
            },
            'task-2': {
                'ready': True,
                'successful': True,
                'state': TaskStatus.SUCCESS,
                'result': {'status': 'success', 'duration_seconds': 15.0}
            },
            'task-3': {
                'ready': True,
                'successful': False,
                'state': TaskStatus.FAILURE,
                'result': {'status': 'failed'}
            },
            'task-4': {
                'ready': False,
                'successful': None,
                'state': TaskStatus.RUNNING
            }
        }
        return status_map.get(task_id, {})
    
    with patch.object(pipeline, 'get_task_status', side_effect=mock_get_status):
        stats = pipeline.get_parallel_execution_stats(task_ids)
        
        assert stats['total_tasks'] == 4
        assert stats['completed'] == 2
        assert stats['failed'] == 1
        assert stats['running'] == 1
        assert stats['total_duration'] == 25.0
        assert stats['avg_duration'] == 12.5
        assert stats['max_duration'] == 15.0
        
        # Speedup: total_duration / max_duration = 25.0 / 15.0 = 1.67
        assert abs(stats['speedup'] - 1.67) < 0.01
        
        print("✓ Get parallel execution stats test passed")


def test_get_parallel_execution_stats_all_success():
    """Test parallel execution stats with all successful tasks."""
    pipeline = TaskPipeline()
    
    task_ids = ['task-1', 'task-2', 'task-3']
    
    def mock_get_status(task_id):
        return {
            'ready': True,
            'successful': True,
            'state': TaskStatus.SUCCESS,
            'result': {'status': 'success', 'duration_seconds': 5.0}
        }
    
    with patch.object(pipeline, 'get_task_status', side_effect=mock_get_status):
        stats = pipeline.get_parallel_execution_stats(task_ids)
        
        assert stats['completed'] == 3
        assert stats['failed'] == 0
        assert stats['total_duration'] == 15.0
        assert stats['speedup'] == 3.0  # Perfect parallelization
        
        print("✓ Get parallel execution stats all success test passed")


def test_get_parallel_execution_stats_empty():
    """Test parallel execution stats with no completed tasks."""
    pipeline = TaskPipeline()
    
    task_ids = ['task-1', 'task-2']
    
    def mock_get_status(task_id):
        return {
            'ready': False,
            'successful': None,
            'state': TaskStatus.PENDING
        }
    
    with patch.object(pipeline, 'get_task_status', side_effect=mock_get_status):
        stats = pipeline.get_parallel_execution_stats(task_ids)
        
        assert stats['completed'] == 0
        assert stats['total_duration'] == 0
        assert stats['avg_duration'] == 0
        assert stats['speedup'] == 1.0
        
        print("✓ Get parallel execution stats empty test passed")


def test_batch_workflow_validation():
    """Test batch workflow validates task structure."""
    pipeline = TaskPipeline()
    
    invalid_tasks = [
        {"tool": "fenicsx", "params": {}}  # Missing 'script'
    ]
    
    try:
        pipeline.submit_batch_workflow(invalid_tasks)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "script" in str(e).lower() or "tool" in str(e).lower()
        print("✓ Batch workflow validation test passed")


def test_parameter_sweep_with_callback():
    """Test parameter sweep with progress callback."""
    pipeline = TaskPipeline()
    
    param_grid = {
        'a': [1, 2],
        'b': [10, 20]
    }
    
    callback_data = []
    
    def callback(info):
        callback_data.append(info)
    
    with patch.object(pipeline, 'submit_task', side_effect=[f'task-{i}' for i in range(4)]):
        task_ids = pipeline.parameter_sweep(
            tool='fenicsx',
            script='poisson.py',
            param_grid=param_grid,
            callback=callback
        )
        
        assert len(task_ids) == 4
        assert len(callback_data) > 0
        
        print("✓ Parameter sweep with callback test passed")


def run_all_tests():
    """Run all enhanced TaskPipeline tests."""
    print("=" * 70)
    print("Running Enhanced TaskPipeline Parallel Orchestration Tests")
    print("=" * 70)
    print()
    
    tests = [
        test_submit_batch_workflow,
        test_submit_batch_workflow_with_callback,
        test_parameter_sweep,
        test_parameter_sweep_single_param,
        test_parameter_sweep_three_params,
        test_wait_for_any,
        test_wait_for_any_timeout,
        test_get_parallel_execution_stats,
        test_get_parallel_execution_stats_all_success,
        test_get_parallel_execution_stats_empty,
        test_batch_workflow_validation,
        test_parameter_sweep_with_callback,
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
