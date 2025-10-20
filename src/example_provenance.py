#!/usr/bin/env python3
"""
Example: Provenance Logging System
===================================

This script demonstrates how to use the provenance logging system
to track workflow metadata, tool calls, and artifacts.
"""

import sys
import json
from pathlib import Path
import tempfile

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent))

from provenance_logger import ProvenanceLogger, get_provenance_logger


def example_1_basic_workflow():
    """Example 1: Basic workflow with provenance tracking."""
    print("\n" + "=" * 70)
    print("Example 1: Basic Workflow with Provenance Tracking")
    print("=" * 70)
    
    # Use a temporary directory for this example
    with tempfile.TemporaryDirectory() as tmpdir:
        logger = ProvenanceLogger(log_dir=tmpdir)
        
        # Start workflow
        print("\n1. Starting workflow...")
        workflow_id = logger.start_workflow(
            user_prompt="Run FEniCSx Poisson equation solver",
            workflow_plan={
                "tool": "fenicsx",
                "script": "poisson.py",
                "parameters": {"mesh_size": 64}
            },
            metadata={
                "project": "example_simulations",
                "researcher": "demo_user"
            }
        )
        print(f"   Workflow ID: {workflow_id}")
        
        # Record tool call
        print("\n2. Recording tool call...")
        logger.record_tool_call(
            workflow_id=workflow_id,
            tool="fenicsx",
            script="poisson.py",
            parameters={"mesh_size": 64},
            task_id="task-123"
        )
        print("   Tool call recorded")
        
        # Finalize workflow
        print("\n3. Finalizing workflow...")
        provenance_file = logger.finalize_workflow(
            workflow_id=workflow_id,
            status="completed",
            final_result={
                "status": "success",
                "output": "solution.vtk"
            }
        )
        print(f"   Provenance saved to: {provenance_file}")
        
        # Display provenance
        print("\n4. Provenance record:")
        with open(provenance_file, 'r') as f:
            prov = json.load(f)
        
        print(f"   - Workflow ID: {prov['workflow_id']}")
        print(f"   - Status: {prov['status']}")
        print(f"   - Duration: {prov['duration_seconds']:.2f}s")
        print(f"   - Tool calls: {len(prov['tool_calls'])}")
        print(f"   - Software versions: {len(prov['software_versions'])} packages")


def example_2_file_tracking():
    """Example 2: Tracking input and output files."""
    print("\n" + "=" * 70)
    print("Example 2: Input/Output File Tracking")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        logger = ProvenanceLogger(log_dir=tmpdir)
        
        # Create dummy files
        input_file = Path(tmpdir) / "input.mesh"
        output_file = Path(tmpdir) / "output.vtk"
        input_file.write_text("mesh data")
        output_file.write_text("results data")
        
        # Start workflow
        print("\n1. Starting workflow with file tracking...")
        workflow_id = logger.start_workflow(
            user_prompt="Structural analysis with mesh input",
            workflow_plan={"tool": "fenicsx"}
        )
        
        # Add input file
        print("\n2. Adding input file...")
        logger.add_input_file(
            workflow_id=workflow_id,
            filepath=input_file,
            description="FEM mesh definition"
        )
        print(f"   Input file: {input_file.name}")
        
        # Record tool execution
        logger.record_tool_call(
            workflow_id=workflow_id,
            tool="fenicsx",
            parameters={"mesh": str(input_file)}
        )
        
        # Add output file
        print("\n3. Adding output file...")
        logger.add_output_file(
            workflow_id=workflow_id,
            filepath=output_file,
            description="Stress field visualization"
        )
        print(f"   Output file: {output_file.name}")
        
        # Finalize
        provenance_file = logger.finalize_workflow(
            workflow_id=workflow_id,
            status="completed"
        )
        
        # Display file metadata
        print("\n4. File metadata in provenance:")
        with open(provenance_file, 'r') as f:
            prov = json.load(f)
        
        print(f"   Input files: {len(prov['input_files'])}")
        for f in prov['input_files']:
            print(f"     - {f['filename']}: {f['size_bytes']} bytes, SHA256: {f['checksum'][:16]}...")
        
        print(f"   Output files: {len(prov['output_files'])}")
        for f in prov['output_files']:
            print(f"     - {f['filename']}: {f['size_bytes']} bytes, SHA256: {f['checksum'][:16]}...")


def example_3_agent_actions():
    """Example 3: Tracking multi-agent workflow."""
    print("\n" + "=" * 70)
    print("Example 3: Multi-Agent Workflow Tracking")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        logger = ProvenanceLogger(log_dir=tmpdir)
        
        print("\n1. Starting multi-agent workflow...")
        workflow_id = logger.start_workflow(
            user_prompt="Run structural analysis on steel beam",
            workflow_plan={"pattern": "conductor_performer"},
            metadata={"orchestration_type": "langgraph"}
        )
        
        # Simulate conductor agent actions
        print("\n2. Recording conductor actions...")
        logger.record_agent_action(
            workflow_id=workflow_id,
            agent_role="conductor",
            action="analyze_request",
            details={"complexity": "medium"}
        )
        
        logger.record_agent_action(
            workflow_id=workflow_id,
            agent_role="conductor",
            action="create_execution_plan",
            details={"phases": 3}
        )
        
        # Simulate performer agent action
        print("\n3. Recording performer execution...")
        logger.record_agent_action(
            workflow_id=workflow_id,
            agent_role="fenicsx_performer",
            action="execute_simulation",
            details={"tool": "fenicsx"}
        )
        
        logger.record_tool_call(
            workflow_id=workflow_id,
            tool="fenicsx",
            parameters={"material": "steel", "load": 10000}
        )
        
        # Simulate validator agent
        print("\n4. Recording validation...")
        logger.record_agent_action(
            workflow_id=workflow_id,
            agent_role="validator",
            action="validate_results",
            details={"validation_passed": True}
        )
        
        # Finalize
        provenance_file = logger.finalize_workflow(
            workflow_id=workflow_id,
            status="completed",
            final_result={"max_stress": 250.5}
        )
        
        # Display timeline
        print("\n5. Execution timeline:")
        with open(provenance_file, 'r') as f:
            prov = json.load(f)
        
        for event in prov['execution_timeline']:
            event_type = event['event']
            if event_type == 'agent_action':
                role = event['details'].get('agent_role', 'unknown')
                action = event['details'].get('action', 'unknown')
                print(f"   - {event_type}: {role} -> {action}")
            else:
                print(f"   - {event_type}")


def example_4_query_workflows():
    """Example 4: Querying workflow provenance."""
    print("\n" + "=" * 70)
    print("Example 4: Querying Workflow Provenance")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        logger = ProvenanceLogger(log_dir=tmpdir)
        
        # Create multiple workflows
        print("\n1. Creating multiple workflows...")
        
        wf1 = logger.start_workflow("Workflow 1: FEniCSx", {})
        logger.record_tool_call(wf1, "fenicsx", {})
        logger.finalize_workflow(wf1, status="completed")
        print("   - Workflow 1 completed")
        
        wf2 = logger.start_workflow("Workflow 2: LAMMPS", {})
        logger.record_tool_call(wf2, "lammps", {})
        logger.finalize_workflow(wf2, status="failed", error="Out of memory")
        print("   - Workflow 2 failed")
        
        wf3 = logger.start_workflow("Workflow 3: OpenFOAM", {})
        logger.record_tool_call(wf3, "openfoam", {})
        logger.finalize_workflow(wf3, status="completed")
        print("   - Workflow 3 completed")
        
        # Query all workflows
        print("\n2. Querying all workflows...")
        all_workflows = logger.list_workflows()
        print(f"   Total workflows: {len(all_workflows)}")
        
        # Query by status
        print("\n3. Querying completed workflows...")
        completed = logger.list_workflows(status="completed")
        print(f"   Completed: {len(completed)}")
        for wf in completed:
            print(f"     - {wf['workflow_id'][:20]}... : {wf['user_prompt']}")
        
        print("\n4. Querying failed workflows...")
        failed = logger.list_workflows(status="failed")
        print(f"   Failed: {len(failed)}")
        for wf in failed:
            print(f"     - {wf['workflow_id'][:20]}... : {wf['user_prompt']}")


def example_5_reproducibility():
    """Example 5: Using provenance for reproducibility."""
    print("\n" + "=" * 70)
    print("Example 5: Reproducibility Use Case")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        logger = ProvenanceLogger(log_dir=tmpdir)
        
        # Original workflow
        print("\n1. Running original workflow...")
        workflow_id = logger.start_workflow(
            user_prompt="Benchmark simulation",
            workflow_plan={
                "tool": "fenicsx",
                "script": "benchmark.py",
                "parameters": {"mesh_size": 128, "solver": "cg"}
            }
        )
        
        logger.record_tool_call(
            workflow_id=workflow_id,
            tool="fenicsx",
            script="benchmark.py",
            parameters={"mesh_size": 128, "solver": "cg"}
        )
        
        provenance_file = logger.finalize_workflow(
            workflow_id=workflow_id,
            status="completed",
            final_result={"solution_norm": 1.2345}
        )
        
        print(f"   Original workflow: {workflow_id}")
        
        # Load provenance for reproduction
        print("\n2. Loading provenance for reproduction...")
        with open(provenance_file, 'r') as f:
            prov = json.load(f)
        
        print("   Reproduction instructions:")
        print(f"   - Tool: {prov['tool_calls'][0]['tool']}")
        print(f"   - Script: {prov['tool_calls'][0]['script']}")
        print(f"   - Parameters: {prov['tool_calls'][0]['parameters']}")
        print(f"   - Python version: {prov['software_versions']['python'].split()[0]}")
        
        print("\n3. Software environment to recreate:")
        for pkg, version in prov['software_versions'].items():
            if pkg in ['celery', 'redis', 'psutil']:
                print(f"   - {pkg}=={version}")
        
        print("\n4. Random seed to use:")
        if 'python_random_state' in prov['random_seeds']:
            print(f"   - Python random state: {prov['random_seeds']['python_random_state'][:3]}...")


def main():
    """Run all examples."""
    print("\n" + "=" * 70)
    print("PROVENANCE LOGGING SYSTEM - EXAMPLES")
    print("=" * 70)
    print("\nThis script demonstrates the provenance logging capabilities")
    print("of Keystone Supercomputer for reproducibility and audit trails.")
    
    # Run examples
    example_1_basic_workflow()
    example_2_file_tracking()
    example_3_agent_actions()
    example_4_query_workflows()
    example_5_reproducibility()
    
    print("\n" + "=" * 70)
    print("All examples completed!")
    print("=" * 70)
    print("\nFor more information, see:")
    print("  - PROVENANCE_SCHEMA.md - Complete schema documentation")
    print("  - src/provenance_logger.py - API reference")
    print("  - src/test_provenance_logger.py - Unit tests")
    print()


if __name__ == '__main__':
    main()
