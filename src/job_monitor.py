"""
Job Monitoring System for Keystone Supercomputer
==================================================

This module provides resource usage tracking and failure monitoring for all
simulation jobs executed through the Celery task queue.

Features:
- Resource usage tracking (CPU time, memory, execution duration)
- Failure tracking with detailed error information
- Job history persistence
- Outcome logging for all workflows
"""

import json
import time
import psutil
import os
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path
import threading


class JobMonitor:
    """
    Monitor resource usage and outcomes for simulation jobs.
    
    This class tracks:
    - Job execution time
    - Resource usage (CPU, memory)
    - Success/failure outcomes
    - Error details for failed jobs
    
    Example:
        >>> monitor = JobMonitor()
        >>> with monitor.track_job(task_id="task-123", tool="fenicsx", script="poisson.py"):
        ...     # Execute simulation
        ...     result = run_simulation()
        >>> stats = monitor.get_job_stats("task-123")
    """
    
    def __init__(self, log_dir: Optional[str] = None):
        """
        Initialize the job monitor.
        
        Args:
            log_dir: Directory to store job logs (default: /tmp/keystone_jobs)
        """
        self.log_dir = Path(log_dir) if log_dir else Path("/tmp/keystone_jobs")
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.jobs_file = self.log_dir / "jobs_history.jsonl"
        self._monitoring = {}
        self._lock = threading.Lock()
    
    def start_monitoring(self, task_id: str, tool: str, script: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Start monitoring a job.
        
        Args:
            task_id: Unique task identifier
            tool: Simulation tool name
            script: Script being executed
            params: Job parameters
            
        Returns:
            Job metadata dictionary
        """
        process = psutil.Process()
        
        job_info = {
            'task_id': task_id,
            'tool': tool,
            'script': script,
            'params': params,
            'start_time': time.time(),
            'start_datetime': datetime.utcnow().isoformat(),
            'initial_cpu_times': process.cpu_times()._asdict(),
            'initial_memory': process.memory_info()._asdict(),
            'process_id': process.pid,
        }
        
        with self._lock:
            self._monitoring[task_id] = job_info
        
        return job_info
    
    def stop_monitoring(
        self,
        task_id: str,
        status: str,
        returncode: int = 0,
        error: Optional[str] = None,
        result: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Stop monitoring a job and record its outcome.
        
        Args:
            task_id: Task identifier
            status: Job status (success, failed, timeout, error)
            returncode: Process return code
            error: Error message if failed
            result: Job result data
            
        Returns:
            Complete job statistics
        """
        with self._lock:
            if task_id not in self._monitoring:
                return {}
            
            job_info = self._monitoring.pop(task_id)
        
        end_time = time.time()
        duration = end_time - job_info['start_time']
        
        try:
            process = psutil.Process(job_info['process_id'])
            final_cpu_times = process.cpu_times()._asdict()
            final_memory = process.memory_info()._asdict()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            # Process may have ended, use last known values
            final_cpu_times = job_info['initial_cpu_times']
            final_memory = job_info['initial_memory']
        
        # Calculate resource usage
        cpu_user_time = final_cpu_times.get('user', 0) - job_info['initial_cpu_times'].get('user', 0)
        cpu_system_time = final_cpu_times.get('system', 0) - job_info['initial_cpu_times'].get('system', 0)
        
        job_stats = {
            'task_id': task_id,
            'tool': job_info['tool'],
            'script': job_info['script'],
            'params': job_info['params'],
            'start_time': job_info['start_datetime'],
            'end_time': datetime.utcnow().isoformat(),
            'duration_seconds': round(duration, 2),
            'status': status,
            'returncode': returncode,
            'resource_usage': {
                'cpu_user_seconds': round(cpu_user_time, 2),
                'cpu_system_seconds': round(cpu_system_time, 2),
                'cpu_total_seconds': round(cpu_user_time + cpu_system_time, 2),
                'memory_peak_mb': round(final_memory.get('rss', 0) / (1024 * 1024), 2),
            },
            'error': error,
            'has_result': result is not None,
        }
        
        # Log to file
        self._write_job_log(job_stats)
        
        return job_stats
    
    def _write_job_log(self, job_stats: Dict[str, Any]) -> None:
        """
        Write job statistics to log file.
        
        Args:
            job_stats: Job statistics dictionary
        """
        try:
            with open(self.jobs_file, 'a') as f:
                f.write(json.dumps(job_stats) + '\n')
        except Exception as e:
            # Don't fail the job if logging fails
            print(f"Warning: Failed to write job log: {e}")
    
    def get_job_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get job history from log file.
        
        Args:
            limit: Maximum number of jobs to return (most recent first)
            
        Returns:
            List of job statistics dictionaries
        """
        if not self.jobs_file.exists():
            return []
        
        jobs = []
        try:
            with open(self.jobs_file, 'r') as f:
                for line in f:
                    if line.strip():
                        jobs.append(json.loads(line))
        except Exception as e:
            print(f"Warning: Failed to read job history: {e}")
            return []
        
        # Return most recent first
        jobs.reverse()
        
        if limit:
            return jobs[:limit]
        return jobs
    
    def get_job_stats(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get statistics for a specific job.
        
        Args:
            task_id: Task identifier
            
        Returns:
            Job statistics dictionary or None if not found
        """
        jobs = self.get_job_history()
        for job in jobs:
            if job['task_id'] == task_id:
                return job
        return None
    
    def get_summary_statistics(self) -> Dict[str, Any]:
        """
        Get summary statistics for all jobs.
        
        Returns:
            Dictionary with aggregate statistics
        """
        jobs = self.get_job_history()
        
        if not jobs:
            return {
                'total_jobs': 0,
                'successful': 0,
                'failed': 0,
                'success_rate': 0.0,
                'total_cpu_time': 0.0,
                'total_duration': 0.0,
                'by_tool': {},
            }
        
        successful = sum(1 for j in jobs if j['status'] == 'success')
        failed = sum(1 for j in jobs if j['status'] in ['failed', 'error', 'timeout'])
        total_cpu = sum(j['resource_usage']['cpu_total_seconds'] for j in jobs)
        total_duration = sum(j['duration_seconds'] for j in jobs)
        
        # Group by tool
        by_tool = {}
        for job in jobs:
            tool = job['tool']
            if tool not in by_tool:
                by_tool[tool] = {
                    'count': 0,
                    'successful': 0,
                    'failed': 0,
                    'total_duration': 0.0,
                }
            by_tool[tool]['count'] += 1
            if job['status'] == 'success':
                by_tool[tool]['successful'] += 1
            elif job['status'] in ['failed', 'error', 'timeout']:
                by_tool[tool]['failed'] += 1
            by_tool[tool]['total_duration'] += job['duration_seconds']
        
        return {
            'total_jobs': len(jobs),
            'successful': successful,
            'failed': failed,
            'success_rate': round(successful / len(jobs) * 100, 2) if jobs else 0.0,
            'total_cpu_time_seconds': round(total_cpu, 2),
            'total_duration_seconds': round(total_duration, 2),
            'average_duration_seconds': round(total_duration / len(jobs), 2) if jobs else 0.0,
            'by_tool': by_tool,
        }
    
    def track_job(self, task_id: str, tool: str, script: str, params: Optional[Dict[str, Any]] = None):
        """
        Context manager for tracking a job.
        
        Args:
            task_id: Task identifier
            tool: Simulation tool name
            script: Script being executed
            params: Job parameters
            
        Example:
            >>> monitor = JobMonitor()
            >>> with monitor.track_job("task-123", "fenicsx", "poisson.py", {}):
            ...     run_simulation()
        """
        return JobTracker(self, task_id, tool, script, params or {})


class JobTracker:
    """Context manager for job tracking."""
    
    def __init__(
        self,
        monitor: JobMonitor,
        task_id: str,
        tool: str,
        script: str,
        params: Dict[str, Any]
    ):
        self.monitor = monitor
        self.task_id = task_id
        self.tool = tool
        self.script = script
        self.params = params
        self.error = None
        self.status = 'success'
        self.returncode = 0
    
    def __enter__(self):
        self.monitor.start_monitoring(self.task_id, self.tool, self.script, self.params)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.status = 'error'
            self.error = str(exc_val)
            self.returncode = 1
        
        self.monitor.stop_monitoring(
            self.task_id,
            self.status,
            self.returncode,
            self.error
        )
        return False  # Don't suppress exceptions
    
    def set_status(self, status: str, returncode: int = 0, error: Optional[str] = None):
        """Update job status within the context."""
        self.status = status
        self.returncode = returncode
        self.error = error


# Global monitor instance
_global_monitor = None


def get_monitor() -> JobMonitor:
    """
    Get the global job monitor instance.
    
    Returns:
        Global JobMonitor instance
    """
    global _global_monitor
    if _global_monitor is None:
        _global_monitor = JobMonitor()
    return _global_monitor
