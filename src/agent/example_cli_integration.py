#!/usr/bin/env python3
"""
Example: CLI and Agent Integration
====================================

This example demonstrates how the CLI commands can be used alongside
the LLM agent for intelligent workflow orchestration.

The workflow shows:
1. Using CLI commands programmatically
2. Integrating with task_pipeline for monitoring
3. Using the LLM agent to interpret results (if available)
"""

import sys
import json
from pathlib import Path
from click.testing import CliRunner

# Add agent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from cli import cli
from task_pipeline import TaskPipeline


def example_cli_programmatic_usage():
    """Example 1: Using CLI commands programmatically."""
    print("=" * 70)
    print("Example 1: Programmatic CLI Usage")
    print("=" * 70)
    print()
    
    runner = CliRunner()
    
    # Check health
    print("1. Checking worker health...")
    result = runner.invoke(cli, ['health'])
    print(result.output)
    
    if result.exit_code != 0:
        print("Worker not available - skipping task submission")
        return
    
    # List tools
    print("2. Listing available tools...")
    result = runner.invoke(cli, ['list-tools'])
    print(result.output)
    
    # Submit a task
    print("3. Submitting a task...")
    result = runner.invoke(cli, [
        'submit', 
        'fenicsx', 
        'poisson.py',
        '-p', '{"mesh_size": 32}',
        '--no-wait'
    ])
    print(result.output)
    
    if result.exit_code == 0 and 'Task submitted:' in result.output:
        # Extract task ID from output
        for line in result.output.split('\n'):
            if 'Task submitted:' in line:
                task_id = line.split(':')[1].strip()
                print(f"\nTask ID extracted: {task_id}")
                
                # Check status
                print("\n4. Checking task status...")
                result = runner.invoke(cli, ['status', task_id])
                print(result.output)
    
    print()


def example_hybrid_approach():
    """Example 2: Hybrid approach using both CLI and TaskPipeline."""
    print("=" * 70)
    print("Example 2: Hybrid CLI + TaskPipeline Approach")
    print("=" * 70)
    print()
    
    # Use CLI to check health
    runner = CliRunner()
    print("1. Using CLI to check health...")
    result = runner.invoke(cli, ['health'])
    print(result.output)
    
    if result.exit_code != 0:
        print("Worker not available")
        return
    
    # Use TaskPipeline for programmatic control
    print("2. Using TaskPipeline for direct task submission...")
    pipeline = TaskPipeline()
    
    try:
        task_id = pipeline.submit_task(
            tool="fenicsx",
            script="poisson.py",
            params={"mesh_size": 64}
        )
        print(f"   ✓ Task submitted: {task_id}")
        
        # Use CLI to monitor
        print("\n3. Using CLI to monitor task...")
        result = runner.invoke(cli, ['status', task_id, '--monitor'])
        print(result.output)
        
    except Exception as e:
        print(f"   ✗ Task submission failed: {e}")
    
    print()


def example_workflow_orchestration():
    """Example 3: Workflow orchestration example."""
    print("=" * 70)
    print("Example 3: Workflow Orchestration")
    print("=" * 70)
    print()
    
    runner = CliRunner()
    
    # Create a temporary workflow file
    workflow = [
        {
            "tool": "fenicsx",
            "script": "poisson.py",
            "params": {"mesh_size": 16}
        },
        {
            "tool": "lammps",
            "script": "example.lammps",
            "params": {}
        }
    ]
    
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(workflow, f)
        workflow_file = f.name
    
    print("1. Created workflow file:")
    print(json.dumps(workflow, indent=2))
    print()
    
    print("2. Submitting workflow via CLI...")
    result = runner.invoke(cli, [
        'submit-workflow',
        workflow_file,
        '--parallel',
        '--no-wait'
    ])
    print(result.output)
    
    # Extract task IDs if successful
    if result.exit_code == 0 and 'Task' in result.output:
        print("\n3. Workflow submitted successfully!")
        print("   In production, you would now monitor the workflow status.")
    
    # Cleanup
    Path(workflow_file).unlink()
    print()


def example_agent_integration_concept():
    """Example 4: Conceptual agent integration."""
    print("=" * 70)
    print("Example 4: Agent Integration Concept")
    print("=" * 70)
    print()
    
    print("""
    This example shows how an LLM agent could use the CLI for workflow management:
    
    1. User: "Run a FEniCS simulation with mesh size 64"
       Agent: Interprets request and executes:
              python3 cli.py submit fenicsx poisson.py -p '{"mesh_size": 64}' --wait
    
    2. User: "Check the status of my last three jobs"
       Agent: Retrieves task IDs from history and executes:
              python3 cli.py workflow-status task-1 task-2 task-3
    
    3. User: "Run a workflow with FEniCS, LAMMPS, and OpenFOAM in parallel"
       Agent: Creates workflow.json and executes:
              python3 cli.py submit-workflow workflow.json --parallel --wait
    
    4. User: "Cancel the running job"
       Agent: Identifies current task and executes:
              python3 cli.py cancel <task-id>
    
    Benefits:
    - Natural language interface to simulation infrastructure
    - Agent can make intelligent decisions about workflows
    - CLI provides reliable, tested interface
    - Easy to extend with new capabilities
    """)
    print()


def main():
    """Run all examples."""
    print("\n")
    print("#" * 70)
    print("# CLI and Agent Integration Examples")
    print("#" * 70)
    print("\n")
    
    examples = [
        ("Programmatic CLI Usage", example_cli_programmatic_usage),
        ("Hybrid CLI + TaskPipeline", example_hybrid_approach),
        ("Workflow Orchestration", example_workflow_orchestration),
        ("Agent Integration Concept", example_agent_integration_concept),
    ]
    
    print("Available examples:")
    for i, (name, _) in enumerate(examples, 1):
        print(f"  {i}. {name}")
    print()
    
    # Run all examples
    for name, example_func in examples:
        try:
            example_func()
        except Exception as e:
            print(f"Example '{name}' failed: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n")
    print("#" * 70)
    print("# Examples Complete")
    print("#" * 70)
    print("\n")
    print("Note: Most examples will fail without Redis/Celery running.")
    print("To run with real services:")
    print("  docker compose up -d redis celery-worker")
    print()


if __name__ == '__main__':
    main()
