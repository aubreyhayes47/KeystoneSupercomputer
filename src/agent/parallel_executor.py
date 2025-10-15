"""
Parallel Executor for Agent Orchestration
==========================================

This module provides parallel execution capabilities for agent workflows,
enabling efficient multi-core task scheduling and batch processing.

Features:
- ProcessPoolExecutor for CPU-bound parallel tasks
- ThreadPoolExecutor for I/O-bound parallel tasks  
- Resource-aware task scheduling
- Batch processing for parameter sweeps
- Progress tracking and error handling
"""

import time
import logging
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from typing import Dict, Any, Optional, List, Callable, Union
from dataclasses import dataclass
from datetime import datetime
import multiprocessing

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class TaskResult:
    """Result of a parallel task execution."""
    task_id: str
    status: str
    result: Any
    error: Optional[str] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    
    @property
    def duration(self) -> Optional[float]:
        """Calculate task duration in seconds."""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return None


class ParallelExecutor:
    """
    Parallel executor for running multiple tasks concurrently across cores.
    
    This class provides high-level interfaces for parallel task execution
    using ProcessPoolExecutor or ThreadPoolExecutor based on task type.
    
    Example:
        >>> executor = ParallelExecutor(max_workers=4)
        >>> tasks = [{'id': '1', 'func': my_func, 'args': (1,)}]
        >>> results = executor.execute_parallel(tasks)
    """
    
    def __init__(self, max_workers: Optional[int] = None, use_processes: bool = True):
        """
        Initialize parallel executor.
        
        Args:
            max_workers: Maximum number of parallel workers (default: CPU count)
            use_processes: If True, use ProcessPoolExecutor; if False, use ThreadPoolExecutor
        """
        if max_workers is None:
            max_workers = multiprocessing.cpu_count()
        
        self.max_workers = max_workers
        self.use_processes = use_processes
        self._executor = None
        logger.info(f"Initialized ParallelExecutor with {max_workers} workers "
                   f"({'processes' if use_processes else 'threads'})")
    
    def __enter__(self):
        """Context manager entry."""
        executor_class = ProcessPoolExecutor if self.use_processes else ThreadPoolExecutor
        self._executor = executor_class(max_workers=self.max_workers)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if self._executor:
            self._executor.shutdown(wait=True)
            self._executor = None
    
    def execute_parallel(
        self,
        tasks: List[Dict[str, Any]],
        callback: Optional[Callable[[TaskResult], None]] = None,
        timeout: Optional[float] = None
    ) -> List[TaskResult]:
        """
        Execute multiple tasks in parallel.
        
        Args:
            tasks: List of task dictionaries with 'id', 'func', 'args', 'kwargs'
            callback: Optional callback function called when each task completes
            timeout: Optional timeout in seconds for each task
            
        Returns:
            List of TaskResult objects
            
        Example:
            >>> def my_task(x):
            ...     return x * 2
            >>> tasks = [
            ...     {'id': '1', 'func': my_task, 'args': (5,)},
            ...     {'id': '2', 'func': my_task, 'args': (10,)}
            ... ]
            >>> results = executor.execute_parallel(tasks)
        """
        if not self._executor:
            raise RuntimeError("Executor not initialized. Use with context manager.")
        
        # Submit all tasks
        future_to_task = {}
        for task in tasks:
            task_id = task['id']
            func = task['func']
            args = task.get('args', ())
            kwargs = task.get('kwargs', {})
            
            future = self._executor.submit(func, *args, **kwargs)
            future_to_task[future] = {
                'id': task_id,
                'start_time': time.time()
            }
            logger.debug(f"Submitted task {task_id}")
        
        # Collect results as they complete
        results = []
        for future in as_completed(future_to_task, timeout=timeout):
            task_info = future_to_task[future]
            task_id = task_info['id']
            start_time = task_info['start_time']
            end_time = time.time()
            
            try:
                result = future.result()
                task_result = TaskResult(
                    task_id=task_id,
                    status='success',
                    result=result,
                    start_time=start_time,
                    end_time=end_time
                )
                logger.info(f"Task {task_id} completed in {task_result.duration:.2f}s")
            except Exception as e:
                task_result = TaskResult(
                    task_id=task_id,
                    status='failed',
                    result=None,
                    error=str(e),
                    start_time=start_time,
                    end_time=end_time
                )
                logger.error(f"Task {task_id} failed: {e}")
            
            results.append(task_result)
            
            # Call callback if provided
            if callback:
                callback(task_result)
        
        return results
    
    def execute_map(
        self,
        func: Callable,
        items: List[Any],
        callback: Optional[Callable[[int, Any], None]] = None,
        timeout: Optional[float] = None
    ) -> List[Any]:
        """
        Execute a function over a list of items in parallel (map operation).
        
        Args:
            func: Function to execute for each item
            items: List of items to process
            callback: Optional callback(index, result) called for each completion
            timeout: Optional timeout in seconds for each task
            
        Returns:
            List of results in the same order as input items
            
        Example:
            >>> def square(x):
            ...     return x * x
            >>> results = executor.execute_map(square, [1, 2, 3, 4, 5])
        """
        if not self._executor:
            raise RuntimeError("Executor not initialized. Use with context manager.")
        
        logger.info(f"Executing map over {len(items)} items")
        results = []
        
        try:
            for i, result in enumerate(self._executor.map(func, items, timeout=timeout)):
                results.append(result)
                if callback:
                    callback(i, result)
                logger.debug(f"Completed item {i+1}/{len(items)}")
        except Exception as e:
            logger.error(f"Map execution failed: {e}")
            raise
        
        return results


class BatchProcessor:
    """
    Batch processor for parameter sweep and multi-configuration workflows.
    
    This class provides convenient methods for running simulations with
    multiple parameter combinations in parallel.
    
    Example:
        >>> processor = BatchProcessor(max_workers=4)
        >>> param_grid = {'mesh_size': [16, 32, 64], 'time_steps': [100, 200]}
        >>> results = processor.parameter_sweep(run_simulation, param_grid)
    """
    
    def __init__(self, max_workers: Optional[int] = None):
        """
        Initialize batch processor.
        
        Args:
            max_workers: Maximum number of parallel workers
        """
        self.max_workers = max_workers or multiprocessing.cpu_count()
        logger.info(f"Initialized BatchProcessor with {self.max_workers} workers")
    
    def parameter_sweep(
        self,
        func: Callable,
        param_dict: Dict[str, List[Any]],
        callback: Optional[Callable[[Dict, Any], None]] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute a parameter sweep over a grid of parameter values.
        
        Args:
            func: Function to execute for each parameter combination
            param_dict: Dictionary mapping parameter names to lists of values
            callback: Optional callback(params, result) called for each completion
            
        Returns:
            List of dictionaries with 'params' and 'result' keys
            
        Example:
            >>> def simulate(mesh_size, time_steps):
            ...     return mesh_size * time_steps
            >>> param_dict = {'mesh_size': [16, 32], 'time_steps': [100, 200]}
            >>> results = processor.parameter_sweep(simulate, param_dict)
        """
        # Generate all parameter combinations
        param_combinations = self._generate_combinations(param_dict)
        logger.info(f"Running parameter sweep with {len(param_combinations)} combinations")
        
        # Execute in parallel
        with ParallelExecutor(max_workers=self.max_workers, use_processes=True) as executor:
            tasks = []
            for i, params in enumerate(param_combinations):
                task = {
                    'id': f'sweep_{i}',
                    'func': func,
                    'kwargs': params
                }
                tasks.append(task)
            
            task_results = executor.execute_parallel(tasks)
        
        # Format results
        results = []
        for i, task_result in enumerate(task_results):
            result_dict = {
                'params': param_combinations[i],
                'status': task_result.status,
                'result': task_result.result,
                'error': task_result.error,
                'duration': task_result.duration
            }
            results.append(result_dict)
            
            if callback:
                callback(param_combinations[i], task_result.result)
        
        # Summary
        successful = sum(1 for r in results if r['status'] == 'success')
        logger.info(f"Parameter sweep complete: {successful}/{len(results)} successful")
        
        return results
    
    def batch_execute(
        self,
        func: Callable,
        batch_items: List[Any],
        callback: Optional[Callable[[int, Any], None]] = None,
        chunk_size: Optional[int] = None
    ) -> List[Any]:
        """
        Execute a function over a batch of items in parallel.
        
        Args:
            func: Function to execute for each item
            batch_items: List of items to process
            callback: Optional callback(index, result) called for each completion
            chunk_size: Optional chunk size for batching
            
        Returns:
            List of results
            
        Example:
            >>> def process(item):
            ...     return item * 2
            >>> results = processor.batch_execute(process, [1, 2, 3, 4, 5])
        """
        logger.info(f"Batch executing {len(batch_items)} items")
        
        with ParallelExecutor(max_workers=self.max_workers, use_processes=True) as executor:
            results = executor.execute_map(func, batch_items, callback=callback)
        
        return results
    
    def _generate_combinations(self, param_dict: Dict[str, List[Any]]) -> List[Dict[str, Any]]:
        """
        Generate all combinations of parameters.
        
        Args:
            param_dict: Dictionary mapping parameter names to lists of values
            
        Returns:
            List of parameter dictionaries
        """
        if not param_dict:
            return [{}]
        
        # Get parameter names and values
        param_names = list(param_dict.keys())
        param_values = [param_dict[name] for name in param_names]
        
        # Generate cartesian product
        combinations = []
        self._cartesian_product(param_names, param_values, 0, {}, combinations)
        
        return combinations
    
    def _cartesian_product(
        self,
        param_names: List[str],
        param_values: List[List[Any]],
        index: int,
        current: Dict[str, Any],
        results: List[Dict[str, Any]]
    ):
        """Recursive helper for generating cartesian product."""
        if index == len(param_names):
            results.append(current.copy())
            return
        
        param_name = param_names[index]
        for value in param_values[index]:
            current[param_name] = value
            self._cartesian_product(param_names, param_values, index + 1, current, results)


def create_parallel_executor(max_workers: Optional[int] = None) -> ParallelExecutor:
    """
    Factory function to create a parallel executor.
    
    Args:
        max_workers: Maximum number of parallel workers
        
    Returns:
        ParallelExecutor instance
    """
    return ParallelExecutor(max_workers=max_workers)


def create_batch_processor(max_workers: Optional[int] = None) -> BatchProcessor:
    """
    Factory function to create a batch processor.
    
    Args:
        max_workers: Maximum number of parallel workers
        
    Returns:
        BatchProcessor instance
    """
    return BatchProcessor(max_workers=max_workers)
