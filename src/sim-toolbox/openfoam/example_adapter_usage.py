#!/usr/bin/env python3
"""
Example Usage: OpenFOAM Adapter
================================

This script demonstrates how to use the OpenFOAM adapter to run
containerized CFD simulations.
"""

import sys
from pathlib import Path

# Add adapter to path
adapter_dir = Path(__file__).parent
sys.path.insert(0, str(adapter_dir))

from openfoam_adapter import OpenFOAMAdapter


def example_basic_usage():
    """Example 1: Basic usage with cavity flow example."""
    print("="*60)
    print("Example 1: Running OpenFOAM cavity flow simulation")
    print("="*60 + "\n")
    
    # Create adapter
    adapter = OpenFOAMAdapter(
        image_name="openfoam-toolbox",
        output_dir="./output/openfoam_basic"
    )
    
    # Check if image is available
    if not adapter.check_image_available():
        print("Docker image not available. Please build it first:")
        print("  cd src/sim-toolbox/openfoam")
        print("  docker build -t openfoam-toolbox .")
        return
    
    # Run simulation using the example_cavity.py script
    result = adapter.run_simulation(
        case_name="cavity"
    )
    
    # Save results
    adapter.save_result_json()
    
    # Print results
    print("\nResults:")
    print(f"  Success: {result['success']}")
    print(f"  Output files: {len(result['output_files'])}")
    
    if result['solver_data']:
        print(f"\nSolver statistics:")
        print(f"  Timesteps: {result['solver_data'].get('timesteps_completed', 0)}")
        if result['solver_data'].get('residuals'):
            print(f"  Residuals tracked: {len(result['solver_data']['residuals'])}")


def example_custom_case_script():
    """Example 2: Running with a custom case setup script."""
    print("\n" + "="*60)
    print("Example 2: Running with custom case script")
    print("="*60 + "\n")
    
    # Use the existing example_cavity.py script
    case_script = adapter_dir / "example_cavity.py"
    
    if not case_script.exists():
        print(f"Case script not found: {case_script}")
        return
    
    # Create adapter
    adapter = OpenFOAMAdapter(
        image_name="openfoam-toolbox",
        output_dir="./output/openfoam_custom"
    )
    
    # Run with explicit script path
    result = adapter.run_simulation(
        case_script=str(case_script),
        case_name="custom_cavity",
        script_args=["--output-dir", "/data/output/custom_cavity"]
    )
    
    if result['success']:
        print(f"\n✓ Custom case executed successfully!")
        print(f"✓ Case name: {result['case_name']}")
        print(f"✓ Output directory: {result['output_dir']}")


def example_direct_case():
    """Example 3: Running an existing OpenFOAM case directory (if available)."""
    print("\n" + "="*60)
    print("Example 3: Running existing OpenFOAM case directory")
    print("="*60 + "\n")
    
    # This example would work with an existing OpenFOAM case
    # For demonstration, we'll show the pattern
    
    print("This example requires an existing OpenFOAM case directory.")
    print("Pattern:")
    print("""
    adapter = OpenFOAMAdapter(
        image_name="openfoam-toolbox",
        output_dir="./output/openfoam_direct"
    )
    
    result = adapter.run_case_direct(
        case_dir="/path/to/openfoam/case",
        solver="icoFoam",
        mesh_command="blockMesh"
    )
    """)


def example_with_monitoring():
    """Example 4: Running simulation and monitoring progress."""
    print("\n" + "="*60)
    print("Example 4: Running with detailed monitoring")
    print("="*60 + "\n")
    
    # Create adapter
    adapter = OpenFOAMAdapter(
        image_name="openfoam-toolbox",
        output_dir="./output/openfoam_monitoring"
    )
    
    print("Running simulation...")
    result = adapter.run_simulation(case_name="cavity")
    
    # Access detailed results
    if result['success']:
        print("\n✓ Simulation completed!")
        
        # Print solver convergence info
        if result['solver_data']:
            solver_data = result['solver_data']
            print(f"\nSolver convergence:")
            print(f"  Timesteps: {solver_data['timesteps'][:5]}..." if len(solver_data['timesteps']) > 5 else f"  Timesteps: {solver_data['timesteps']}")
            
            # Show some residual data
            if solver_data['residuals']:
                print(f"\nSample residuals:")
                for res in solver_data['residuals'][:3]:
                    print(f"  {res['field']}: {res['initial']:.2e} → {res['final']:.2e}")
        
        # Show metadata
        if result['metadata']:
            print(f"\nMetadata:")
            for key, value in result['metadata'].items():
                print(f"  {key}: {value}")
    else:
        print("\n✗ Simulation failed!")
        print(f"Return code: {result['returncode']}")


def main():
    """Run all examples."""
    print("OpenFOAM Adapter Examples")
    print("=" * 60)
    
    # Example 1: Basic usage
    example_basic_usage()
    
    # Example 2: Custom case script
    # example_custom_case_script()
    
    # Example 3: Direct case (pattern only)
    # example_direct_case()
    
    # Example 4: With monitoring
    # example_with_monitoring()
    
    print("\n" + "="*60)
    print("Examples completed!")
    print("="*60)


if __name__ == "__main__":
    main()
