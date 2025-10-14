#!/usr/bin/env python3
"""
Minimal OpenFOAM Cavity Flow Example
=====================================
This script demonstrates a basic computational fluid dynamics (CFD) simulation
using OpenFOAM in a reproducible containerized environment.

The classic lid-driven cavity case simulates flow in a square cavity where the
top wall moves with a constant velocity, creating a recirculating flow pattern.

Usage:
    python3 example_cavity.py [--output-dir OUTPUT_DIR]

The simulation will:
1. Copy the cavity tutorial case
2. Generate the mesh with blockMesh
3. Run the icoFoam solver (incompressible laminar flow)
4. Output results to the specified directory (default: /data/output/cavity)
"""

import subprocess
import sys
import os
import shutil
from pathlib import Path
import argparse


def run_command(cmd, cwd=None):
    """Execute a shell command and return the result."""
    print(f"Running: {cmd}")
    result = subprocess.run(
        cmd,
        shell=True,
        cwd=cwd,
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print(f"Error running command: {cmd}")
        print(f"stderr: {result.stderr}")
        sys.exit(1)
    
    print(result.stdout)
    return result


def setup_case(work_dir):
    """Copy and set up the cavity tutorial case."""
    print("Setting up cavity flow case...")
    
    # Source OpenFOAM environment and copy tutorial
    tutorial_src = "/opt/openfoam11/tutorials/incompressible/icoFoam/cavity/cavity"
    
    if not os.path.exists(tutorial_src):
        print(f"Tutorial not found at {tutorial_src}, trying alternate location...")
        tutorial_src = "/opt/openfoam11/tutorials/incompressible/icoFoam/cavity"
    
    if os.path.exists(tutorial_src):
        shutil.copytree(tutorial_src, work_dir / "cavity", dirs_exist_ok=True)
    else:
        print("Could not find OpenFOAM cavity tutorial. Creating basic case structure...")
        os.makedirs(work_dir / "cavity" / "system", exist_ok=True)
        os.makedirs(work_dir / "cavity" / "constant", exist_ok=True)
        os.makedirs(work_dir / "cavity" / "0", exist_ok=True)
        
    print(f"Case directory: {work_dir / 'cavity'}")


def run_simulation(case_dir):
    """Run the OpenFOAM simulation."""
    print("\n" + "="*60)
    print("Starting OpenFOAM Cavity Flow Simulation")
    print("="*60 + "\n")
    
    # Generate mesh
    print("Generating mesh with blockMesh...")
    run_command(
        "source /opt/openfoam11/etc/bashrc && blockMesh",
        cwd=case_dir
    )
    
    # Run solver
    print("\nRunning icoFoam solver...")
    run_command(
        "source /opt/openfoam11/etc/bashrc && icoFoam",
        cwd=case_dir
    )
    
    print("\n" + "="*60)
    print("Simulation completed successfully!")
    print("="*60 + "\n")


def copy_results(case_dir, output_dir):
    """Copy simulation results to output directory."""
    print(f"Copying results to {output_dir}...")
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Copy time directories and logs
    for item in case_dir.iterdir():
        if item.is_dir() and item.name.replace('.', '').replace('-', '').isdigit():
            shutil.copytree(item, output_dir / item.name, dirs_exist_ok=True)
    
    # Copy log files if they exist
    for log_file in case_dir.glob("log.*"):
        shutil.copy2(log_file, output_dir)
    
    print(f"Results saved to: {output_dir}")


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description="Run OpenFOAM cavity flow simulation"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="/data/output/cavity",
        help="Directory for simulation output (default: /data/output/cavity)"
    )
    parser.add_argument(
        "--work-dir",
        type=str,
        default="/workspace/foam-run",
        help="Working directory for simulation (default: /workspace/foam-run)"
    )
    
    args = parser.parse_args()
    
    work_dir = Path(args.work_dir)
    output_dir = Path(args.output_dir)
    
    work_dir.mkdir(parents=True, exist_ok=True)
    
    # Setup the case
    setup_case(work_dir)
    
    case_dir = work_dir / "cavity"
    
    # Run the simulation
    run_simulation(case_dir)
    
    # Copy results to output
    copy_results(case_dir, output_dir)
    
    print("\n✓ OpenFOAM cavity flow simulation completed successfully!")
    print(f"✓ Results available at: {output_dir}")


if __name__ == "__main__":
    main()
