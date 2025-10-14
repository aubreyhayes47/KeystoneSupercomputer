"""
Task Pipeline for Agent Workflow Orchestration
================================================

This module provides a high-level interface for submitting, monitoring, and
retrieving simulation tasks via Celery, supporting agent-driven workflow orchestration.

Features:
- Submit individual simulation tasks
- Monitor task progress with callbacks
- Retrieve task results
- Cancel running tasks
- Submit and manage multi-task workflows
- Comprehensive error handling
"""

import time
import sys
from typing import Dict, Any, Optional, List, Callable, Union
from datetime import datetime
from pathlib import Path

# Add parent directory to path for celery_app import
sys.path.insert(0, str(Path(__file__).parent.parent))

from celery_app import run_simulation_task, health_check_task, list_simulations_task
from celery.result import AsyncResult
from celery_app import celery_app


class TaskStatus:
    """Task status constants."""
    PENDING = 'PENDING'
    RUNNING = 'RUNNING'
    SUCCESS = 'SUCCESS'
    FAILURE = 'FAILURE'
    TIMEOUT = 'timeout'
    ERROR = 'error'
    CANCELLED = 'REVOKED'


class TaskPipeline:
    """
    High-level interface for managing simulation tasks via Celery.
    
    This class provides methods to submit, monitor, and retrieve simulation tasks,
    making it easy for agents to orchestrate complex workflows.
    
    Example:
        >>> pipeline = TaskPipeline()
        >>> # Submit a single task
        >>> task_id = pipeline.submit_task("fenicsx", "poisson.py", {"mesh_size": 64})
        >>> # Monitor and wait for completion
        >>> result = pipeline.wait_for_task(task_id, timeout=300)
        >>> print(f"Status: {result['status']}")
    """
    
    def __init__(self):
        """Initialize the task pipeline."""
        self.celery_app = celery_app
        self._active_tasks: Dict[str, AsyncResult] = {}
    
    def health_check(self) -> Dict[str, Any]:
        """
        Check if the Celery worker is healthy and responding.
        
        Returns:
            Dictionary with health status information
            
        Raises:
            Exception: If worker is not responding or unhealthy
        """
        try:
            task = health_check_task.delay()
            result = task.get(timeout=10)
            return result
        except Exception as e:
            raise Exception(f"Health check failed: {str(e)}")
    
    def list_available_simulations(self) -> Dict[str, Any]:
        """
        List all available simulation tools and scripts.
        
        Returns:
            Dictionary with available tools and their configurations
        """
        task = list_simulations_task.delay()
        return task.get(timeout=10)
    
    def submit_task(
        self,
        tool: str,
        script: str,
        params: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Submit a simulation task to the job queue.
        
        Args:
            tool: Simulation tool name (fenicsx, lammps, openfoam)
            script: Script filename to execute
            params: Optional parameters for the simulation
            
        Returns:
            Task ID (string) that can be used to monitor and retrieve results
            
        Example:
            >>> pipeline = TaskPipeline()
            >>> task_id = pipeline.submit_task("fenicsx", "poisson.py", {"mesh_size": 64})
            >>> print(f"Submitted task: {task_id}")
        """
        task = run_simulation_task.delay(tool=tool, script=script, params=params)
        self._active_tasks[task.id] = task
        return task.id
    
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """
        Get the current status of a task.
        
        Args:
            task_id: The task ID returned by submit_task()
            
        Returns:
            Dictionary with task status information including:
            - state: Current task state (PENDING, RUNNING, SUCCESS, FAILURE, etc.)
            - progress: Progress percentage if available
            - result: Task result if completed
            - error: Error information if failed
            
        Example:
            >>> status = pipeline.get_task_status(task_id)
            >>> print(f"State: {status['state']}, Progress: {status.get('progress', 0)}%")
        """
        if task_id in self._active_tasks:
            task = self._active_tasks[task_id]
        else:
            task = AsyncResult(task_id, app=self.celery_app)
            self._active_tasks[task_id] = task
        
        status = {
            'task_id': task_id,
            'state': task.state,
            'ready': task.ready(),
            'successful': task.successful() if task.ready() else None,
            'failed': task.failed() if task.ready() else None,
        }
        
        # Add progress information if available
        if task.state == TaskStatus.RUNNING and task.info:
            if isinstance(task.info, dict):
                status['progress'] = task.info.get('progress', 0)
                status['tool'] = task.info.get('tool')
                status['script'] = task.info.get('script')
        
        # Add result if completed
        if task.ready():
            try:
                status['result'] = task.result
            except Exception as e:
                status['error'] = str(e)
        
        return status
    
    def monitor_task(
        self,
        task_id: str,
        callback: Optional[Callable[[Dict[str, Any]], None]] = None,
        poll_interval: float = 2.0
    ) -> None:
        """
        Monitor a task and call callback function with status updates.
        
        This method continuously polls the task status and invokes the callback
        function with status information until the task completes.
        
        Args:
            task_id: The task ID to monitor
            callback: Optional callback function that receives status dict
            poll_interval: How often to poll for updates (seconds)
            
        Example:
            >>> def on_status_update(status):
            ...     print(f"Progress: {status.get('progress', 0)}%")
            >>> pipeline.monitor_task(task_id, callback=on_status_update)
        """
        if task_id in self._active_tasks:
            task = self._active_tasks[task_id]
        else:
            task = AsyncResult(task_id, app=self.celery_app)
            self._active_tasks[task_id] = task
        
        while not task.ready():
            status = self.get_task_status(task_id)
            if callback:
                callback(status)
            time.sleep(poll_interval)
        
        # Final callback with completion status
        if callback:
            callback(self.get_task_status(task_id))
    
    def wait_for_task(
        self,
        task_id: str,
        timeout: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Wait for a task to complete and return its result.
        
        This is a blocking call that waits until the task completes or times out.
        
        Args:
            task_id: The task ID to wait for
            timeout: Maximum time to wait in seconds (None = wait indefinitely)
            
        Returns:
            Task result dictionary
            
        Raises:
            TimeoutError: If task doesn't complete within timeout
            Exception: If task fails
            
        Example:
            >>> result = pipeline.wait_for_task(task_id, timeout=300)
            >>> if result['status'] == 'success':
            ...     print("Simulation completed successfully!")
        """
        if task_id in self._active_tasks:
            task = self._active_tasks[task_id]
        else:
            task = AsyncResult(task_id, app=self.celery_app)
            self._active_tasks[task_id] = task
        
        try:
            result = task.get(timeout=timeout)
            return result
        except Exception as e:
            raise Exception(f"Task failed or timed out: {str(e)}")
    
    def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a running or pending task.
        
        Args:
            task_id: The task ID to cancel
            
        Returns:
            True if cancellation was successful, False otherwise
            
        Example:
            >>> if pipeline.cancel_task(task_id):
            ...     print("Task cancelled successfully")
        """
        if task_id in self._active_tasks:
            task = self._active_tasks[task_id]
        else:
            task = AsyncResult(task_id, app=self.celery_app)
            self._active_tasks[task_id] = task
        
        try:
            task.revoke(terminate=True)
            return True
        except Exception:
            return False
    
    def submit_workflow(
        self,
        tasks: List[Dict[str, Any]],
        sequential: bool = True
    ) -> List[str]:
        """
        Submit multiple tasks as a workflow.
        
        Args:
            tasks: List of task dictionaries, each containing:
                   - tool: Simulation tool name
                   - script: Script filename
                   - params: Optional parameters
            sequential: If True, wait for each task to complete before starting next
                       If False, submit all tasks in parallel
                       
        Returns:
            List of task IDs
            
        Example:
            >>> tasks = [
            ...     {"tool": "fenicsx", "script": "poisson.py", "params": {"mesh_size": 32}},
            ...     {"tool": "lammps", "script": "example.lammps", "params": {}},
            ... ]
            >>> task_ids = pipeline.submit_workflow(tasks, sequential=True)
            >>> print(f"Submitted {len(task_ids)} tasks")
        """
        task_ids = []
        
        for task_config in tasks:
            tool = task_config.get('tool')
            script = task_config.get('script')
            params = task_config.get('params', {})
            
            if not tool or not script:
                raise ValueError("Each task must have 'tool' and 'script' fields")
            
            task_id = self.submit_task(tool, script, params)
            task_ids.append(task_id)
            
            # If sequential, wait for this task to complete before submitting next
            if sequential and len(tasks) > 1:
                try:
                    self.wait_for_task(task_id)
                except Exception as e:
                    # Log error but continue with workflow
                    print(f"Warning: Task {task_id} failed: {str(e)}")
        
        return task_ids
    
    def get_workflow_status(self, task_ids: List[str]) -> Dict[str, Any]:
        """
        Get the status of all tasks in a workflow.
        
        Args:
            task_ids: List of task IDs from submit_workflow()
            
        Returns:
            Dictionary with overall workflow status and individual task statuses
            
        Example:
            >>> workflow_status = pipeline.get_workflow_status(task_ids)
            >>> print(f"Completed: {workflow_status['completed']}/{workflow_status['total']}")
        """
        statuses = {}
        completed = 0
        failed = 0
        running = 0
        pending = 0
        
        for task_id in task_ids:
            status = self.get_task_status(task_id)
            statuses[task_id] = status
            
            if status['ready']:
                if status['successful']:
                    completed += 1
                else:
                    failed += 1
            elif status['state'] == TaskStatus.RUNNING:
                running += 1
            else:
                pending += 1
        
        return {
            'total': len(task_ids),
            'completed': completed,
            'failed': failed,
            'running': running,
            'pending': pending,
            'all_complete': completed + failed == len(task_ids),
            'tasks': statuses
        }
    
    def wait_for_workflow(
        self,
        task_ids: List[str],
        timeout: Optional[float] = None,
        callback: Optional[Callable[[Dict[str, Any]], None]] = None,
        poll_interval: float = 2.0
    ) -> Dict[str, Any]:
        """
        Wait for all tasks in a workflow to complete.
        
        Args:
            task_ids: List of task IDs to wait for
            timeout: Maximum time to wait in seconds (None = wait indefinitely)
            callback: Optional callback function called with workflow status updates
            poll_interval: How often to check workflow status (seconds)
            
        Returns:
            Dictionary with final workflow status and all results
            
        Example:
            >>> def on_workflow_update(status):
            ...     print(f"Progress: {status['completed']}/{status['total']} tasks completed")
            >>> results = pipeline.wait_for_workflow(task_ids, timeout=600, callback=on_workflow_update)
        """
        start_time = time.time()
        
        while True:
            workflow_status = self.get_workflow_status(task_ids)
            
            if callback:
                callback(workflow_status)
            
            if workflow_status['all_complete']:
                return workflow_status
            
            if timeout and (time.time() - start_time) > timeout:
                raise TimeoutError(f"Workflow did not complete within {timeout} seconds")
            
            time.sleep(poll_interval)
    
    def cleanup(self):
        """
        Clean up internal task tracking.
        
        Call this method to clear the cache of active tasks. Task results
        will still be available via task IDs from Redis.
        """
        self._active_tasks.clear()
