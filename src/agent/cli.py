import click
import json
import time
import sys
from typing import Optional
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent_state import AgentState
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage
from task_pipeline import TaskPipeline
from job_monitor import get_monitor

llm = ChatOllama(
    model="llama3:8b",  # Change to the model you have pulled in Ollama
    base_url="http://127.0.0.1:11434"
)

@click.group()
def cli():
    """Keystone Supercomputer CLI - Submit and monitor simulation workflows."""
    pass

@cli.command()
@click.argument('message')
def ask(message):
    """Send a message to the agent and receive a response."""
    state = AgentState(
        messages=[HumanMessage(content=message)],
        simulation_params={},
        artifact_paths=[]
    )
    click.echo(f"User: {message}")
    # Get LLM response
    response = llm.invoke(message)
    click.echo(f"Agent: {response.content}")

@cli.command()
def health():
    """Check the health of the Celery worker."""
    pipeline = TaskPipeline()
    try:
        result = pipeline.health_check()
        click.echo(click.style("✓ Worker is healthy", fg='green'))
        click.echo(f"Status: {result.get('status', 'unknown')}")
        click.echo(f"Message: {result.get('message', '')}")
    except Exception as e:
        click.echo(click.style(f"✗ Health check failed: {e}", fg='red'))
        raise click.Abort()

@cli.command(name='list-tools')
def list_tools():
    """List available simulation tools and scripts."""
    pipeline = TaskPipeline()
    try:
        simulations = pipeline.list_available_simulations()
        click.echo(click.style("Available Simulation Tools:", fg='blue', bold=True))
        for tool, info in simulations.get('tools', {}).items():
            click.echo(f"\n{click.style(tool, fg='cyan', bold=True)}:")
            click.echo(f"  Description: {info.get('description', 'N/A')}")
            if 'scripts' in info:
                click.echo(f"  Scripts: {', '.join(info['scripts'])}")
    except Exception as e:
        click.echo(click.style(f"✗ Failed to list tools: {e}", fg='red'))
        raise click.Abort()

@cli.command()
@click.argument('tool')
@click.argument('script')
@click.option('--params', '-p', help='JSON string of parameters', default='{}')
@click.option('--wait/--no-wait', default=False, help='Wait for task to complete')
@click.option('--timeout', '-t', type=int, default=300, help='Timeout in seconds (default: 300)')
def submit(tool, script, params, wait, timeout):
    """Submit a simulation task.
    
    Examples:
        cli.py submit fenicsx poisson.py
        cli.py submit fenicsx poisson.py -p '{"mesh_size": 64}' --wait
        cli.py submit lammps example.lammps --wait --timeout 600
    """
    pipeline = TaskPipeline()
    
    # Parse params
    try:
        params_dict = json.loads(params)
    except json.JSONDecodeError as e:
        click.echo(click.style(f"✗ Invalid JSON in params: {e}", fg='red'))
        raise click.Abort()
    
    # Submit task
    try:
        click.echo(f"Submitting {tool} simulation: {script}")
        if params_dict:
            click.echo(f"Parameters: {params_dict}")
        
        task_id = pipeline.submit_task(tool, script, params_dict)
        click.echo(click.style(f"✓ Task submitted: {task_id}", fg='green'))
        
        if wait:
            click.echo(f"Waiting for task to complete (timeout: {timeout}s)...")
            with click.progressbar(length=100, label='Progress') as bar:
                def progress_callback(status):
                    if status.get('state') == 'RUNNING' and 'progress' in status:
                        bar.update(status['progress'] - bar.pos)
                
                start_time = time.time()
                while True:
                    status = pipeline.get_task_status(task_id)
                    if status.get('ready'):
                        bar.update(100 - bar.pos)
                        break
                    progress_callback(status)
                    
                    if time.time() - start_time > timeout:
                        click.echo(click.style(f"\n✗ Task timed out after {timeout}s", fg='red'))
                        raise click.Abort()
                    
                    time.sleep(2)
            
            # Get final result
            result = pipeline.wait_for_task(task_id, timeout=5)
            click.echo(f"\n{click.style('Task completed!', fg='green', bold=True)}")
            click.echo(f"Status: {result.get('status', 'unknown')}")
            if result.get('status') == 'success':
                click.echo(click.style("✓ Simulation completed successfully", fg='green'))
                if 'artifacts' in result:
                    click.echo(f"Artifacts: {result['artifacts']}")
            else:
                click.echo(click.style(f"✗ Simulation failed: {result.get('error', 'Unknown error')}", fg='red'))
        else:
            click.echo(f"\nUse 'cli.py status {task_id}' to check the status")
            
    except Exception as e:
        click.echo(click.style(f"✗ Task submission failed: {e}", fg='red'))
        raise click.Abort()

@cli.command()
@click.argument('task_id')
@click.option('--monitor', '-m', is_flag=True, help='Monitor task until completion')
@click.option('--interval', '-i', type=int, default=2, help='Polling interval in seconds (default: 2)')
def status(task_id, monitor, interval):
    """Check the status of a task.
    
    Examples:
        cli.py status abc123-task-id
        cli.py status abc123-task-id --monitor
        cli.py status abc123-task-id -m -i 5
    """
    pipeline = TaskPipeline()
    
    try:
        if monitor:
            click.echo(f"Monitoring task {task_id}...")
            click.echo("Press Ctrl+C to stop monitoring\n")
            
            def progress_callback(status):
                state = status.get('state', 'UNKNOWN')
                ready = status.get('ready', False)
                
                # Color based on state
                if state == 'SUCCESS':
                    state_str = click.style(state, fg='green')
                elif state == 'FAILURE':
                    state_str = click.style(state, fg='red')
                elif state == 'RUNNING':
                    state_str = click.style(state, fg='yellow')
                else:
                    state_str = click.style(state, fg='blue')
                
                click.echo(f"[{time.strftime('%H:%M:%S')}] State: {state_str}, Ready: {ready}")
                
                if state == 'RUNNING' and 'progress' in status:
                    click.echo(f"  Progress: {status['progress']}%")
            
            try:
                pipeline.monitor_task(task_id, callback=progress_callback, poll_interval=interval)
                
                # Get final result
                final_status = pipeline.get_task_status(task_id)
                if final_status.get('successful'):
                    click.echo(click.style("\n✓ Task completed successfully!", fg='green', bold=True))
                    if 'result' in final_status:
                        result = final_status['result']
                        if 'artifacts' in result:
                            click.echo(f"Artifacts: {result['artifacts']}")
                else:
                    click.echo(click.style("\n✗ Task failed!", fg='red', bold=True))
                    if 'error' in final_status:
                        click.echo(f"Error: {final_status['error']}")
            except KeyboardInterrupt:
                click.echo("\n\nMonitoring stopped by user")
        else:
            status = pipeline.get_task_status(task_id)
            click.echo(f"Task ID: {task_id}")
            click.echo(f"State: {status.get('state', 'UNKNOWN')}")
            click.echo(f"Ready: {status.get('ready', False)}")
            
            if status.get('ready'):
                click.echo(f"Successful: {status.get('successful', False)}")
                if 'result' in status:
                    click.echo(f"Result: {json.dumps(status['result'], indent=2)}")
                if 'error' in status:
                    click.echo(f"Error: {status['error']}")
            elif status.get('state') == 'RUNNING':
                if 'progress' in status:
                    click.echo(f"Progress: {status['progress']}%")
                if 'tool' in status:
                    click.echo(f"Tool: {status['tool']}")
                if 'script' in status:
                    click.echo(f"Script: {status['script']}")
                    
    except Exception as e:
        click.echo(click.style(f"✗ Failed to get status: {e}", fg='red'))
        raise click.Abort()

@cli.command()
@click.argument('task_id')
def cancel(task_id):
    """Cancel a running or pending task.
    
    Example:
        cli.py cancel abc123-task-id
    """
    pipeline = TaskPipeline()
    
    try:
        click.echo(f"Cancelling task {task_id}...")
        if pipeline.cancel_task(task_id):
            click.echo(click.style("✓ Task cancelled successfully", fg='green'))
        else:
            click.echo(click.style("✗ Failed to cancel task", fg='red'))
    except Exception as e:
        click.echo(click.style(f"✗ Cancellation failed: {e}", fg='red'))
        raise click.Abort()

@cli.command(name='submit-workflow')
@click.argument('workflow_file', type=click.Path(exists=True))
@click.option('--sequential/--parallel', default=True, help='Run tasks sequentially or in parallel')
@click.option('--wait/--no-wait', default=False, help='Wait for workflow to complete')
@click.option('--timeout', '-t', type=int, default=600, help='Timeout in seconds (default: 600)')
def submit_workflow(workflow_file, sequential, wait, timeout):
    """Submit a workflow from a JSON file.
    
    The workflow file should be a JSON array of tasks, each with:
    - tool: The simulation tool name
    - script: The script filename
    - params: Optional parameters dictionary
    
    Example workflow.json:
    [
        {"tool": "fenicsx", "script": "poisson.py", "params": {"mesh_size": 32}},
        {"tool": "lammps", "script": "example.lammps", "params": {}}
    ]
    
    Usage:
        cli.py submit-workflow workflow.json
        cli.py submit-workflow workflow.json --parallel --wait
    """
    pipeline = TaskPipeline()
    
    # Load workflow
    try:
        with open(workflow_file, 'r') as f:
            tasks = json.load(f)
    except json.JSONDecodeError as e:
        click.echo(click.style(f"✗ Invalid JSON in workflow file: {e}", fg='red'))
        raise click.Abort()
    except Exception as e:
        click.echo(click.style(f"✗ Failed to read workflow file: {e}", fg='red'))
        raise click.Abort()
    
    if not isinstance(tasks, list):
        click.echo(click.style("✗ Workflow file must contain a JSON array of tasks", fg='red'))
        raise click.Abort()
    
    # Submit workflow
    try:
        mode = "sequential" if sequential else "parallel"
        click.echo(f"Submitting workflow with {len(tasks)} tasks ({mode})...")
        
        task_ids = pipeline.submit_workflow(tasks, sequential=sequential)
        
        click.echo(click.style(f"✓ Workflow submitted: {len(task_ids)} tasks", fg='green'))
        for i, task_id in enumerate(task_ids, 1):
            click.echo(f"  Task {i}: {task_id}")
        
        if wait:
            click.echo(f"\nWaiting for workflow to complete (timeout: {timeout}s)...")
            
            def workflow_callback(status):
                completed = status['completed']
                total = status['total']
                running = status['running']
                failed = status['failed']
                click.echo(f"Progress: {completed}/{total} completed, {running} running, {failed} failed")
            
            try:
                final_status = pipeline.wait_for_workflow(
                    task_ids,
                    timeout=timeout,
                    callback=workflow_callback,
                    poll_interval=5
                )
                
                click.echo(click.style(f"\n✓ Workflow completed!", fg='green', bold=True))
                click.echo(f"Total tasks: {final_status['total']}")
                click.echo(f"Completed: {final_status['completed']}")
                click.echo(f"Failed: {final_status['failed']}")
                
                if final_status['failed'] > 0:
                    click.echo(click.style(f"\n⚠ {final_status['failed']} task(s) failed", fg='yellow'))
                    
            except TimeoutError:
                click.echo(click.style(f"\n✗ Workflow timed out after {timeout}s", fg='red'))
                # Show current status
                status = pipeline.get_workflow_status(task_ids)
                click.echo(f"Current progress: {status['completed']}/{status['total']} completed")
        else:
            click.echo(f"\nUse 'cli.py workflow-status' to check workflow status")
            click.echo("Task IDs:")
            for task_id in task_ids:
                click.echo(f"  {task_id}")
            
    except Exception as e:
        click.echo(click.style(f"✗ Workflow submission failed: {e}", fg='red'))
        raise click.Abort()

@cli.command(name='workflow-status')
@click.argument('task_ids', nargs=-1, required=True)
def workflow_status(task_ids):
    """Check the status of multiple tasks in a workflow.
    
    Example:
        cli.py workflow-status task-id-1 task-id-2 task-id-3
    """
    pipeline = TaskPipeline()
    
    try:
        status = pipeline.get_workflow_status(list(task_ids))
        
        click.echo(click.style("Workflow Status:", fg='blue', bold=True))
        click.echo(f"Total tasks: {status['total']}")
        click.echo(f"Completed: {status['completed']}")
        click.echo(f"Failed: {status['failed']}")
        click.echo(f"Running: {status['running']}")
        click.echo(f"Pending: {status['pending']}")
        click.echo(f"All complete: {status['all_complete']}")
        
        click.echo(f"\n{click.style('Individual Task Status:', fg='blue', bold=True)}")
        for task_id, task_status in status['tasks'].items():
            state = task_status.get('state', 'UNKNOWN')
            ready = task_status.get('ready', False)
            
            # Truncate task ID for display
            short_id = task_id[:12] + '...' if len(task_id) > 15 else task_id
            
            if state == 'SUCCESS':
                state_str = click.style(state, fg='green')
            elif state == 'FAILURE':
                state_str = click.style(state, fg='red')
            elif state == 'RUNNING':
                state_str = click.style(state, fg='yellow')
            else:
                state_str = click.style(state, fg='blue')
            
            click.echo(f"  {short_id}: {state_str} (Ready: {ready})")
            
    except Exception as e:
        click.echo(click.style(f"✗ Failed to get workflow status: {e}", fg='red'))
        raise click.Abort()

@cli.command(name='job-history')
@click.option('--limit', '-l', type=int, default=10, help='Number of jobs to show (default: 10)')
@click.option('--tool', '-t', help='Filter by tool name')
@click.option('--status', '-s', help='Filter by status (success, failed, timeout, error)')
def job_history(limit, tool, status):
    """Display job execution history with resource usage.
    
    Examples:
        cli.py job-history
        cli.py job-history --limit 20
        cli.py job-history --tool fenicsx
        cli.py job-history --status failed
    """
    monitor = get_monitor()
    
    try:
        jobs = monitor.get_job_history(limit=None)  # Get all, filter manually
        
        # Apply filters
        if tool:
            jobs = [j for j in jobs if j['tool'] == tool]
        if status:
            jobs = [j for j in jobs if j['status'] == status]
        
        # Apply limit after filtering
        jobs = jobs[:limit]
        
        if not jobs:
            click.echo(click.style("No job history found", fg='yellow'))
            return
        
        click.echo(click.style(f"\nJob History (showing {len(jobs)} jobs):", fg='blue', bold=True))
        click.echo()
        
        for i, job in enumerate(jobs, 1):
            # Status with color
            status_str = job['status']
            if status_str == 'success':
                status_color = 'green'
            elif status_str in ['failed', 'error']:
                status_color = 'red'
            elif status_str == 'timeout':
                status_color = 'yellow'
            else:
                status_color = 'blue'
            
            status_display = click.style(status_str.upper(), fg=status_color, bold=True)
            
            # Truncate task ID
            short_id = job['task_id'][:12] + '...' if len(job['task_id']) > 15 else job['task_id']
            
            click.echo(f"{click.style(f'{i}.', bold=True)} Task: {short_id}")
            click.echo(f"   Tool: {job['tool']}, Script: {job['script']}")
            click.echo(f"   Status: {status_display}")
            click.echo(f"   Started: {job['start_time']}")
            click.echo(f"   Duration: {job['duration_seconds']}s")
            
            resource = job.get('resource_usage', {})
            if resource:
                click.echo(f"   CPU Time: {resource.get('cpu_total_seconds', 0)}s " +
                          f"(user: {resource.get('cpu_user_seconds', 0)}s, " +
                          f"system: {resource.get('cpu_system_seconds', 0)}s)")
                click.echo(f"   Memory Peak: {resource.get('memory_peak_mb', 0)} MB")
            
            if job.get('error'):
                click.echo(f"   {click.style('Error:', fg='red')} {job['error'][:100]}...")
            
            click.echo()
            
    except Exception as e:
        click.echo(click.style(f"✗ Failed to get job history: {e}", fg='red'))
        raise click.Abort()

@cli.command(name='job-stats')
def job_stats():
    """Display aggregate statistics for all jobs.
    
    Example:
        cli.py job-stats
    """
    monitor = get_monitor()
    
    try:
        stats = monitor.get_summary_statistics()
        
        if stats['total_jobs'] == 0:
            click.echo(click.style("No jobs recorded yet", fg='yellow'))
            return
        
        click.echo(click.style("\nJob Statistics Summary:", fg='blue', bold=True))
        click.echo()
        
        # Overall stats
        click.echo(click.style("Overall:", bold=True))
        click.echo(f"  Total Jobs: {stats['total_jobs']}")
        click.echo(f"  Successful: {click.style(str(stats['successful']), fg='green')} " +
                  f"({stats['success_rate']}%)")
        click.echo(f"  Failed: {click.style(str(stats['failed']), fg='red')}")
        click.echo(f"  Success Rate: {stats['success_rate']}%")
        click.echo()
        
        # Resource usage
        click.echo(click.style("Resource Usage:", bold=True))
        click.echo(f"  Total CPU Time: {stats['total_cpu_time_seconds']}s")
        click.echo(f"  Total Duration: {stats['total_duration_seconds']}s")
        click.echo(f"  Average Duration: {stats['average_duration_seconds']}s")
        click.echo()
        
        # By tool
        if stats['by_tool']:
            click.echo(click.style("By Tool:", bold=True))
            for tool_name, tool_stats in stats['by_tool'].items():
                success_rate = round(tool_stats['successful'] / tool_stats['count'] * 100, 2) if tool_stats['count'] > 0 else 0
                click.echo(f"  {click.style(tool_name, fg='cyan')}:")
                click.echo(f"    Jobs: {tool_stats['count']}")
                click.echo(f"    Successful: {click.style(str(tool_stats['successful']), fg='green')} ({success_rate}%)")
                click.echo(f"    Failed: {click.style(str(tool_stats['failed']), fg='red')}")
                click.echo(f"    Total Duration: {tool_stats['total_duration']}s")
            
    except Exception as e:
        click.echo(click.style(f"✗ Failed to get job statistics: {e}", fg='red'))
        raise click.Abort()

@cli.command(name='job-details')
@click.argument('task_id')
def job_details(task_id):
    """Show detailed information for a specific job.
    
    Example:
        cli.py job-details abc123-task-id
    """
    monitor = get_monitor()
    
    try:
        job = monitor.get_job_stats(task_id)
        
        if not job:
            click.echo(click.style(f"Job {task_id} not found in history", fg='yellow'))
            return
        
        # Status with color
        status_str = job['status']
        if status_str == 'success':
            status_color = 'green'
        elif status_str in ['failed', 'error']:
            status_color = 'red'
        elif status_str == 'timeout':
            status_color = 'yellow'
        else:
            status_color = 'blue'
        
        status_display = click.style(status_str.upper(), fg=status_color, bold=True)
        
        click.echo(click.style(f"\nJob Details: {task_id}", fg='blue', bold=True))
        click.echo()
        
        click.echo(click.style("Basic Information:", bold=True))
        click.echo(f"  Tool: {job['tool']}")
        click.echo(f"  Script: {job['script']}")
        click.echo(f"  Status: {status_display}")
        click.echo(f"  Return Code: {job.get('returncode', 'N/A')}")
        click.echo()
        
        click.echo(click.style("Timing:", bold=True))
        click.echo(f"  Started: {job['start_time']}")
        click.echo(f"  Ended: {job['end_time']}")
        click.echo(f"  Duration: {job['duration_seconds']}s")
        click.echo()
        
        if job.get('params'):
            click.echo(click.style("Parameters:", bold=True))
            click.echo(f"  {json.dumps(job['params'], indent=2)}")
            click.echo()
        
        resource = job.get('resource_usage', {})
        if resource:
            click.echo(click.style("Resource Usage:", bold=True))
            click.echo(f"  CPU User Time: {resource.get('cpu_user_seconds', 0)}s")
            click.echo(f"  CPU System Time: {resource.get('cpu_system_seconds', 0)}s")
            click.echo(f"  CPU Total Time: {resource.get('cpu_total_seconds', 0)}s")
            click.echo(f"  Memory Peak: {resource.get('memory_peak_mb', 0)} MB")
            click.echo()
        
        if job.get('error'):
            click.echo(click.style("Error Details:", bold=True, fg='red'))
            click.echo(f"  {job['error']}")
            click.echo()
            
    except Exception as e:
        click.echo(click.style(f"✗ Failed to get job details: {e}", fg='red'))
        raise click.Abort()

if __name__ == '__main__':
    cli()
