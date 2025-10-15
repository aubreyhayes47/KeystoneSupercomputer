"""
Celery Application for Keystone Supercomputer
Handles background job queuing for simulation tasks using Redis as broker.
"""

from celery import Celery
import os
import subprocess
import json
import logging
from typing import Dict, Any, Optional
from job_monitor import get_monitor

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Celery app
celery_app = Celery(
    'keystone',
    broker=os.getenv('CELERY_BROKER_URL', 'redis://redis:6379/0'),
    backend=os.getenv('CELERY_RESULT_BACKEND', 'redis://redis:6379/0')
)

# Celery configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour timeout
    task_soft_time_limit=3300,  # 55 minutes soft timeout
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=50,
)


@celery_app.task(name='run_simulation', bind=True)
def run_simulation_task(
    self,
    tool: str,
    script: str,
    params: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Execute a simulation task using Docker.
    
    Args:
        tool: Simulation tool name (fenicsx, lammps, openfoam)
        script: Script filename to execute
        params: Optional parameters for the simulation
    
    Returns:
        Dictionary with task results including status, output, artifacts, and resource usage
    """
    if params is None:
        params = {}
    
    # Get monitor and start tracking
    monitor = get_monitor()
    task_id = self.request.id
    
    logger.info(f"Starting job {task_id}: tool={tool}, script={script}, params={params}")
    
    # Update task state to RUNNING
    self.update_state(
        state='RUNNING',
        meta={'tool': tool, 'script': script, 'progress': 0}
    )
    
    # Start monitoring
    container_name = f"keystone-{tool}"
    monitor.start_monitoring(task_id, tool, script, params, container_name=container_name)
    
    try:
        # Build docker command
        container_name = f"keystone-{tool}"
        cmd = [
            'docker', 'compose', 'run', '--rm',
            tool, script
        ]
        
        # Add parameters as environment variables if provided
        env = os.environ.copy()
        for key, value in params.items():
            env[f'SIM_{key.upper()}'] = str(value)
        
        # Execute simulation
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            env=env,
            timeout=3000  # 50 minutes
        )
        
        # Update progress
        self.update_state(
            state='RUNNING',
            meta={'tool': tool, 'script': script, 'progress': 100}
        )
        
        # Determine status
        status = 'success' if result.returncode == 0 else 'failed'
        
        # Stop monitoring and record outcome
        job_stats = monitor.stop_monitoring(
            task_id,
            status=status,
            returncode=result.returncode,
            error=result.stderr if result.returncode != 0 else None
        )
        
        # Log outcome
        if status == 'success':
            logger.info(f"Job {task_id} completed successfully - Duration: {job_stats.get('duration_seconds', 0)}s, "
                       f"CPU: {job_stats.get('resource_usage', {}).get('cpu_total_seconds', 0)}s")
        else:
            logger.error(f"Job {task_id} failed with return code {result.returncode} - "
                        f"Duration: {job_stats.get('duration_seconds', 0)}s")
        
        # Prepare result
        task_result = {
            'status': status,
            'tool': tool,
            'script': script,
            'params': params,
            'returncode': result.returncode,
            'stdout': result.stdout[-1000:] if len(result.stdout) > 1000 else result.stdout,
            'stderr': result.stderr[-1000:] if len(result.stderr) > 1000 else result.stderr,
            'artifacts': [],
            'resource_usage': job_stats.get('resource_usage', {}),
            'duration_seconds': job_stats.get('duration_seconds', 0),
        }
        
        return task_result
        
    except subprocess.TimeoutExpired:
        logger.warning(f"Job {task_id} timed out")
        monitor.stop_monitoring(
            task_id,
            status='timeout',
            returncode=-1,
            error='Task exceeded time limit'
        )
        return {
            'status': 'timeout',
            'tool': tool,
            'script': script,
            'params': params,
            'error': 'Task exceeded time limit'
        }
    except Exception as e:
        logger.exception(f"Job {task_id} encountered an error: {e}")
        monitor.stop_monitoring(
            task_id,
            status='error',
            returncode=-1,
            error=str(e)
        )
        return {
            'status': 'error',
            'tool': tool,
            'script': script,
            'params': params,
            'error': str(e)
        }


@celery_app.task(name='health_check')
def health_check_task() -> Dict[str, str]:
    """
    Simple health check task to verify Celery worker is functioning.
    
    Returns:
        Dictionary with health status
    """
    return {
        'status': 'healthy',
        'worker': 'operational',
        'message': 'Celery worker is running and processing tasks'
    }


@celery_app.task(name='list_simulations')
def list_simulations_task() -> Dict[str, Any]:
    """
    List available simulation tools and scripts.
    
    Returns:
        Dictionary with available tools and their scripts
    """
    tools = {
        'fenicsx': {
            'description': 'Finite Element Method simulations',
            'scripts': ['poisson.py']
        },
        'lammps': {
            'description': 'Molecular Dynamics simulations',
            'scripts': ['example.lammps']
        },
        'openfoam': {
            'description': 'Computational Fluid Dynamics simulations',
            'scripts': ['example_cavity.py']
        }
    }
    
    return {
        'status': 'success',
        'tools': tools
    }


if __name__ == '__main__':
    # Run worker with: celery -A celery_app worker --loglevel=info
    celery_app.start()
