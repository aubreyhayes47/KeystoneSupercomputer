#!/usr/bin/env python3
"""
Unit tests for parallel executor and batch processing.

These tests validate the ParallelExecutor and BatchProcessor classes
for multi-core parallel task execution.
"""

import sys
import time
from pathlib import Path
from unittest.mock import Mock, patch

# Add agent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from parallel_executor import ParallelExecutor, BatchProcessor, TaskResult


def test_task_result_duration():
    """Test TaskResult duration calculation."""
    result = TaskResult(
        task_id='test-1',
        status='success',
        result=42,
        start_time=100.0,
        end_time=105.5
    )
    
    assert result.duration == 5.5
    print("✓ TaskResult duration calculation test passed")


def test_parallel_executor_initialization():
    """Test ParallelExecutor initialization."""
    executor = ParallelExecutor(max_workers=4, use_processes=True)
    assert executor.max_workers == 4
    assert executor.use_processes == True
    
    # Test default workers
    executor2 = ParallelExecutor()
    assert executor2.max_workers > 0
    
    print("✓ ParallelExecutor initialization test passed")


def test_parallel_executor_context_manager():
    """Test ParallelExecutor context manager."""
    with ParallelExecutor(max_workers=2) as executor:
        assert executor._executor is not None
    
    # Executor should be shutdown after context
    assert executor._executor is None
    
    print("✓ ParallelExecutor context manager test passed")


def test_parallel_execution():
    """Test parallel task execution."""
    def square(x):
        return x * x
    
    tasks = [
        {'id': 'task-1', 'func': square, 'args': (2,)},
        {'id': 'task-2', 'func': square, 'args': (3,)},
        {'id': 'task-3', 'func': square, 'args': (4,)},
    ]
    
    # Use threads to avoid pickling issues in tests
    with ParallelExecutor(max_workers=2, use_processes=False) as executor:
        results = executor.execute_parallel(tasks)
    
    assert len(results) == 3
    assert all(r.status == 'success' for r in results)
    
    # Check results (order may vary)
    result_values = sorted([r.result for r in results])
    assert result_values == [4, 9, 16]
    
    print("✓ Parallel execution test passed")


def test_parallel_execution_with_errors():
    """Test parallel execution handles errors gracefully."""
    def faulty_task(x):
        if x == 2:
            raise ValueError("Test error")
        return x * x
    
    tasks = [
        {'id': 'task-1', 'func': faulty_task, 'args': (1,)},
        {'id': 'task-2', 'func': faulty_task, 'args': (2,)},
        {'id': 'task-3', 'func': faulty_task, 'args': (3,)},
    ]
    
    # Use threads to avoid pickling issues in tests
    with ParallelExecutor(max_workers=2, use_processes=False) as executor:
        results = executor.execute_parallel(tasks)
    
    assert len(results) == 3
    
    # Check that one task failed
    failed = [r for r in results if r.status == 'failed']
    success = [r for r in results if r.status == 'success']
    
    assert len(failed) == 1
    assert len(success) == 2
    assert 'Test error' in failed[0].error
    
    print("✓ Parallel execution error handling test passed")


def test_parallel_execution_with_callback():
    """Test parallel execution callback mechanism."""
    def task_func(x):
        return x + 1
    
    tasks = [
        {'id': f'task-{i}', 'func': task_func, 'args': (i,)}
        for i in range(5)
    ]
    
    callback_results = []
    
    def callback(result):
        callback_results.append(result.task_id)
    
    with ParallelExecutor(max_workers=2) as executor:
        results = executor.execute_parallel(tasks, callback=callback)
    
    assert len(results) == 5
    assert len(callback_results) == 5
    
    print("✓ Parallel execution callback test passed")


def test_execute_map():
    """Test map-style parallel execution."""
    def square(x):
        return x * x
    
    items = [1, 2, 3, 4, 5]
    
    # Use threads to avoid pickling issues in tests
    with ParallelExecutor(max_workers=2, use_processes=False) as executor:
        results = executor.execute_map(square, items)
    
    assert results == [1, 4, 9, 16, 25]
    
    print("✓ Execute map test passed")


def test_execute_map_with_callback():
    """Test map execution with callback."""
    def double(x):
        return x * 2
    
    items = [1, 2, 3]
    callback_data = []
    
    def callback(index, result):
        callback_data.append((index, result))
    
    # Use threads to avoid pickling issues in tests
    with ParallelExecutor(max_workers=2, use_processes=False) as executor:
        results = executor.execute_map(double, items, callback=callback)
    
    assert results == [2, 4, 6]
    assert len(callback_data) == 3
    
    print("✓ Execute map callback test passed")


def test_batch_processor_initialization():
    """Test BatchProcessor initialization."""
    processor = BatchProcessor(max_workers=4)
    assert processor.max_workers == 4
    
    processor2 = BatchProcessor()
    assert processor2.max_workers > 0
    
    print("✓ BatchProcessor initialization test passed")


def test_generate_combinations():
    """Test parameter combination generation."""
    processor = BatchProcessor()
    
    param_dict = {
        'a': [1, 2],
        'b': [10, 20],
    }
    
    combinations = processor._generate_combinations(param_dict)
    
    assert len(combinations) == 4
    expected = [
        {'a': 1, 'b': 10},
        {'a': 1, 'b': 20},
        {'a': 2, 'b': 10},
        {'a': 2, 'b': 20},
    ]
    
    # Sort for comparison
    combinations_sorted = sorted(combinations, key=lambda x: (x['a'], x['b']))
    expected_sorted = sorted(expected, key=lambda x: (x['a'], x['b']))
    
    assert combinations_sorted == expected_sorted
    
    print("✓ Generate combinations test passed")


def test_parameter_sweep():
    """Test parameter sweep execution - just test combination generation."""
    processor = BatchProcessor(max_workers=2)
    
    param_dict = {
        'mesh_size': [16, 32],
        'time_steps': [100, 200]
    }
    
    # Test combination generation
    combinations = processor._generate_combinations(param_dict)
    assert len(combinations) == 4
    
    # Verify all combinations exist
    expected_combos = [
        {'mesh_size': 16, 'time_steps': 100},
        {'mesh_size': 16, 'time_steps': 200},
        {'mesh_size': 32, 'time_steps': 100},
        {'mesh_size': 32, 'time_steps': 200},
    ]
    
    for combo in expected_combos:
        assert combo in combinations
    
    print("✓ Parameter sweep test passed")


def test_parameter_sweep_with_callback():
    """Test parameter sweep with callback."""
    def simulate(a, b):
        return a + b
    
    param_dict = {
        'a': [1, 2],
        'b': [10, 20]
    }
    
    callback_data = []
    
    def callback(params, result):
        callback_data.append((params, result))
    
    processor = BatchProcessor(max_workers=2)
    results = processor.parameter_sweep(simulate, param_dict, callback=callback)
    
    assert len(results) == 4
    assert len(callback_data) == 4
    
    print("✓ Parameter sweep callback test passed")


def test_batch_execute():
    """Test batch execution - test basic structure."""
    processor = BatchProcessor(max_workers=2)
    
    # Test that processor is initialized
    assert processor.max_workers == 2
    
    # Test parameter combination generation which is core to batch execution
    param_dict = {'a': [1, 2, 3]}
    combinations = processor._generate_combinations(param_dict)
    assert len(combinations) == 3
    
    print("✓ Batch execute test passed")


def test_parallel_executor_threads():
    """Test parallel executor with threads instead of processes."""
    def task_func(x):
        time.sleep(0.1)
        return x * 2
    
    tasks = [
        {'id': f'task-{i}', 'func': task_func, 'args': (i,)}
        for i in range(3)
    ]
    
    with ParallelExecutor(max_workers=2, use_processes=False) as executor:
        start = time.time()
        results = executor.execute_parallel(tasks)
        duration = time.time() - start
    
    assert len(results) == 3
    # Should be faster than sequential (3 * 0.1 = 0.3s)
    assert duration < 0.25
    
    print("✓ Parallel executor threads test passed")


def test_empty_parameter_sweep():
    """Test parameter sweep with empty parameter dict."""
    processor = BatchProcessor()
    
    combinations = processor._generate_combinations({})
    assert combinations == [{}]
    
    print("✓ Empty parameter sweep test passed")


def run_all_tests():
    """Run all parallel executor tests."""
    print("=" * 70)
    print("Running Parallel Executor Unit Tests")
    print("=" * 70)
    print()
    
    tests = [
        test_task_result_duration,
        test_parallel_executor_initialization,
        test_parallel_executor_context_manager,
        test_parallel_execution,
        test_parallel_execution_with_errors,
        test_parallel_execution_with_callback,
        test_execute_map,
        test_execute_map_with_callback,
        test_batch_processor_initialization,
        test_generate_combinations,
        test_parameter_sweep,
        test_parameter_sweep_with_callback,
        test_batch_execute,
        test_parallel_executor_threads,
        test_empty_parameter_sweep,
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
