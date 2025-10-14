#!/usr/bin/env python3
"""
Example Usage: LAMMPS Adapter
==============================

This script demonstrates how to use the LAMMPS adapter to run
containerized molecular dynamics simulations.
"""

import sys
from pathlib import Path

# Add adapter to path
adapter_dir = Path(__file__).parent
sys.path.insert(0, str(adapter_dir))

from lammps_adapter import LAMMPSAdapter


def example_basic_usage():
    """Example 1: Basic usage with example LAMMPS script."""
    print("="*60)
    print("Example 1: Running LAMMPS Lennard-Jones simulation")
    print("="*60 + "\n")
    
    # Path to example script
    example_script = adapter_dir / "example.lammps"
    
    if not example_script.exists():
        print(f"Example script not found: {example_script}")
        return
    
    # Create adapter
    adapter = LAMMPSAdapter(
        image_name="keystone/lammps:latest",
        output_dir="./output/lammps_basic"
    )
    
    # Check if image is available
    if not adapter.check_image_available():
        print("Docker image not available. Please build it first:")
        print("  cd src/sim-toolbox/lammps")
        print("  docker build -t keystone/lammps:latest .")
        return
    
    # Run simulation
    result = adapter.run_simulation(
        input_script=str(example_script),
        log_file="lammps.log"
    )
    
    # Save results
    adapter.save_result_json()
    
    # Print results
    print("\nResults:")
    print(f"  Success: {result['success']}")
    print(f"  Output files: {result['output_files']}")
    
    if result['thermo_data'] and 'summary' in result['thermo_data']:
        print(f"\nThermodynamic data:")
        summary = result['thermo_data']['summary']
        print(f"  Total steps: {summary.get('total_steps', 'N/A')}")
        print(f"  Loop time: {summary.get('loop_time', 'N/A')} seconds")
        
        if 'final' in summary:
            print(f"\nFinal state:")
            final = summary['final']
            for key in ['Step', 'Temp', 'TotEng', 'Press']:
                if key in final:
                    print(f"    {key}: {final[key]}")


def example_custom_script():
    """Example 2: Running with a custom LAMMPS script."""
    print("\n" + "="*60)
    print("Example 2: Running with custom LAMMPS script")
    print("="*60 + "\n")
    
    # Define a custom LAMMPS script
    custom_script = """# Simple 2D Lennard-Jones gas
units           lj
atom_style      atomic
dimension       2
boundary        p p p

# Create box
lattice         hex 0.7
region          box block 0 20 0 20 -0.1 0.1
create_box      1 box
create_atoms    1 box
mass            1 1.0

# Interactions
pair_style      lj/cut 2.5
pair_coeff      1 1 1.0 1.0 2.5

# Initial conditions
velocity        all create 1.0 87287

# Dynamics
fix             1 all nve
fix             2 all enforce2d

# Output
thermo          50
thermo_style    custom step temp pe ke etotal press

# Run
timestep        0.005
run             500

# Save final state
write_data      /data/output/final_2d.data
"""
    
    # Create adapter
    adapter = LAMMPSAdapter(
        image_name="keystone/lammps:latest",
        output_dir="./output/lammps_custom"
    )
    
    # Run with custom script
    result = adapter.run_simulation(
        script_content=custom_script,
        log_file="custom.log"
    )
    
    if result['success']:
        print(f"\n✓ Custom script executed successfully!")
        print(f"✓ Output files: {result['output_files']}")
        
        if result['thermo_data'] and 'summary' in result['thermo_data']:
            steps = result['thermo_data']['summary'].get('total_steps', 0)
            print(f"✓ Completed {steps} timesteps")


def example_with_parameters():
    """Example 3: Running simulation with additional parameters."""
    print("\n" + "="*60)
    print("Example 3: LAMMPS simulation with additional parameters")
    print("="*60 + "\n")
    
    example_script = adapter_dir / "example.lammps"
    
    if not example_script.exists():
        print(f"Example script not found: {example_script}")
        return
    
    # Create adapter
    adapter = LAMMPSAdapter(
        image_name="keystone/lammps:latest",
        output_dir="./output/lammps_params"
    )
    
    # Run with additional LAMMPS arguments
    result = adapter.run_simulation(
        input_script=str(example_script),
        log_file="detailed.log",
        lammps_args=["-screen", "none"]  # Suppress screen output
    )
    
    if result['success']:
        print(f"\n✓ Simulation with parameters completed!")
        print(f"✓ Check log file at: {result['output_dir']}/detailed.log")


def main():
    """Run all examples."""
    print("LAMMPS Adapter Examples")
    print("=" * 60)
    
    # Example 1: Basic usage
    example_basic_usage()
    
    # Example 2: Custom script
    # example_custom_script()
    
    # Example 3: With parameters
    # example_with_parameters()
    
    print("\n" + "="*60)
    print("Examples completed!")
    print("="*60)


if __name__ == "__main__":
    main()
