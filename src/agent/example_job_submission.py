"""
Example: Agent Job Submission using Celery
Demonstrates how to submit simulation tasks to the job queue and retrieve results.
"""

from celery_app import run_simulation_task, health_check_task, list_simulations_task
import time


def main():
    """
    Example workflow showing agent job submission and result retrieval.
    """
    
    print("=" * 70)
    print("Keystone Supercomputer - Celery Job Queue Example")
    print("=" * 70)
    print()
    
    # 1. Health check
    print("1. Checking Celery worker health...")
    health_task = health_check_task.delay()
    health_result = health_task.get(timeout=10)
    print(f"   Status: {health_result['status']}")
    print(f"   Message: {health_result['message']}")
    print()
    
    # 2. List available simulations
    print("2. Listing available simulation tools...")
    list_task = list_simulations_task.delay()
    simulations = list_task.get(timeout=10)
    for tool, info in simulations['tools'].items():
        print(f"   - {tool}: {info['description']}")
        print(f"     Scripts: {', '.join(info['scripts'])}")
    print()
    
    # 3. Submit a FEniCSx simulation task
    print("3. Submitting FEniCSx simulation task...")
    sim_task = run_simulation_task.delay(
        tool="fenicsx",
        script="poisson.py",
        params={"mesh_size": 64}
    )
    print(f"   Task ID: {sim_task.id}")
    print(f"   Task State: {sim_task.state}")
    print()
    
    # 4. Monitor task progress
    print("4. Monitoring task progress...")
    while not sim_task.ready():
        if sim_task.state == 'RUNNING':
            meta = sim_task.info
            if isinstance(meta, dict) and 'progress' in meta:
                print(f"   Progress: {meta['progress']}%")
        time.sleep(2)
    
    # 5. Retrieve results
    print()
    print("5. Task completed! Retrieving results...")
    result = sim_task.get(timeout=30)
    print(f"   Status: {result['status']}")
    print(f"   Tool: {result['tool']}")
    print(f"   Script: {result['script']}")
    print(f"   Return Code: {result['returncode']}")
    
    if result.get('stdout'):
        print(f"   Output (last 500 chars):")
        print(f"   {result['stdout'][-500:]}")
    
    if result['status'] == 'success':
        print()
        print("   ✓ Simulation completed successfully!")
    else:
        print()
        print(f"   ✗ Simulation failed: {result.get('error', 'Unknown error')}")
    
    print()
    print("=" * 70)
    print("Example workflow completed")
    print("=" * 70)


if __name__ == '__main__':
    main()
