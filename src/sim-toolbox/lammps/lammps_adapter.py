#!/usr/bin/env python3
"""
LAMMPS Simulation Adapter
==========================

Python adapter for running LAMMPS molecular dynamics simulations in Docker containers.
This adapter provides a standardized interface for:
- Accepting LAMMPS input scripts and parameters
- Automating container execution
- Parsing thermodynamic output and trajectory files
- Enabling LLM-based tool calling and agentic orchestration

Usage:
    from lammps_adapter import LAMMPSAdapter
    
    adapter = LAMMPSAdapter(
        image_name="keystone/lammps:latest",
        output_dir="./output"
    )
    
    result = adapter.run_simulation(
        input_script="example.lammps",
        log_file="lammps.log"
    )
"""

import subprocess
import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
import tempfile
import shutil

# Add parent directory to path for orchestration_base import
sys.path.insert(0, str(Path(__file__).parent.parent))
from orchestration_base import OrchestrationBase, SimulationStatus


class LAMMPSAdapter(OrchestrationBase):
    """Adapter for running LAMMPS simulations in Docker containers."""
    
    def __init__(
        self,
        image_name: str = "keystone/lammps:latest",
        output_dir: str = "./output",
        input_dir: Optional[str] = None,
        work_dir: Optional[str] = None
    ):
        """
        Initialize the LAMMPS adapter.
        
        Args:
            image_name: Docker image name for LAMMPS
            output_dir: Directory for simulation outputs
            input_dir: Optional directory for input files
            work_dir: Optional working directory (default: temporary directory)
        """
        # Initialize orchestration base
        super().__init__(image_name, output_dir)
        
        self.output_dir = Path(output_dir).resolve()
        self.input_dir = Path(input_dir).resolve() if input_dir else None
        self.work_dir = Path(work_dir) if work_dir else None
        self.last_result = None
        
        # Ensure directories exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
        if self.input_dir:
            self.input_dir.mkdir(parents=True, exist_ok=True)
    
    def run_simulation(
        self,
        input_script: Optional[str] = None,
        script_content: Optional[str] = None,
        log_file: str = "lammps.log",
        additional_files: Optional[Dict[str, str]] = None,
        lammps_args: Optional[List[str]] = None,
        docker_args: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Run a LAMMPS simulation in a Docker container.
        
        Args:
            input_script: Path to LAMMPS input script
            script_content: LAMMPS script content as string (alternative to input_script)
            log_file: Name for LAMMPS log file
            additional_files: Dictionary mapping local paths to container paths
            lammps_args: Additional LAMMPS command-line arguments
            docker_args: Additional Docker run arguments
            
        Returns:
            Dictionary containing:
                - success: Whether simulation completed successfully
                - stdout: Standard output from simulation
                - stderr: Standard error from simulation
                - output_files: List of output files generated
                - thermo_data: Parsed thermodynamic data
                - metadata: Simulation metadata
        """
        use_temp_dir = self.work_dir is None
        work_dir = self.work_dir or Path(tempfile.mkdtemp())
        
        # Update status to running
        self._update_status(SimulationStatus.RUNNING)
        
        try:
            # Prepare the input script
            if script_content:
                input_file = work_dir / "input.lammps"
                input_file.write_text(script_content)
                script_path = input_file
            elif input_script:
                script_path = Path(input_script).resolve()
            else:
                raise ValueError("Either input_script or script_content must be provided")
            
            if not script_path.exists():
                raise FileNotFoundError(f"Input script not found: {script_path}")
            
            # Build Docker command
            cmd = ["docker", "run", "--rm"]
            
            # Mount input directory
            if self.input_dir:
                cmd.extend(["-v", f"{self.input_dir}:/data/input"])
            
            # Mount output directory
            cmd.extend(["-v", f"{self.output_dir}:/data/output"])
            
            # Mount the input script
            cmd.extend(["-v", f"{script_path}:/data/input/input.lammps"])
            
            # Mount additional files if provided
            if additional_files:
                for local_path, container_path in additional_files.items():
                    cmd.extend(["-v", f"{local_path}:{container_path}"])
            
            # Add custom Docker arguments
            if docker_args:
                cmd.extend(docker_args)
            
            # Specify image
            cmd.append(self.image_name)
            
            # LAMMPS command
            lammps_cmd = ["lmp", "-in", "/data/input/input.lammps"]
            
            # Add log file argument
            if log_file:
                lammps_cmd.extend(["-log", f"/data/output/{log_file}"])
            
            # Add custom LAMMPS arguments
            if lammps_args:
                lammps_cmd.extend(lammps_args)
            
            # Add LAMMPS command to Docker command
            cmd.extend(lammps_cmd)
            
            print(f"Running LAMMPS simulation...")
            print(f"Command: {' '.join(cmd)}")
            
            # Execute container
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True
            )
            
            # Parse output files
            output_files = self._scan_output_files()
            
            # Parse thermodynamic data from log file
            thermo_data = self._parse_log_file(log_file)
            
            # Extract metadata from output
            metadata = self._parse_metadata(result.stdout, result.stderr)
            
            # Prepare result
            simulation_result = {
                "success": result.returncode == 0,
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "output_files": output_files,
                "thermo_data": thermo_data,
                "metadata": metadata,
                "output_dir": str(self.output_dir)
            }
            
            self.last_result = simulation_result
            
            # Update status based on result
            if result.returncode == 0:
                self._update_status(SimulationStatus.COMPLETED)
                print("✓ Simulation completed successfully!")
                print(f"✓ Output files: {len(output_files)}")
                print(f"✓ Results saved to: {self.output_dir}")
                if thermo_data and 'summary' in thermo_data:
                    print(f"✓ Timesteps completed: {thermo_data['summary'].get('total_steps', 'N/A')}")
            else:
                self._update_status(SimulationStatus.FAILED)
                print("✗ Simulation failed!")
                print(f"Error: {result.stderr}")
            
            return simulation_result
            
        finally:
            # Clean up temporary directory if created
            if use_temp_dir and work_dir.exists():
                shutil.rmtree(work_dir)
    
    def _scan_output_files(self) -> List[str]:
        """Scan output directory for generated files."""
        output_files = []
        if self.output_dir.exists():
            for item in self.output_dir.iterdir():
                if item.is_file():
                    output_files.append(item.name)
        return output_files
    
    def _parse_log_file(self, log_file: str) -> Dict[str, Any]:
        """
        Parse LAMMPS log file to extract thermodynamic data.
        
        Args:
            log_file: Name of the log file
            
        Returns:
            Dictionary with parsed thermodynamic data
        """
        log_path = self.output_dir / log_file
        
        if not log_path.exists():
            return {}
        
        thermo_data = {
            "columns": [],
            "data": [],
            "summary": {}
        }
        
        try:
            with open(log_path, 'r') as f:
                content = f.read()
            
            # Find thermo output sections
            # Look for lines starting with "Step" which indicate column headers
            lines = content.split('\n')
            in_thermo = False
            
            for i, line in enumerate(lines):
                line = line.strip()
                
                # Detect thermo header
                if line.startswith('Step') and not thermo_data['columns']:
                    thermo_data['columns'] = line.split()
                    in_thermo = True
                    continue
                
                # Parse thermo data rows
                if in_thermo and line and not line.startswith('Loop'):
                    # Check if line contains numeric data
                    parts = line.split()
                    try:
                        # Try to convert first element to number
                        float(parts[0])
                        thermo_data['data'].append([float(x) if '.' in x or 'e' in x.lower() else int(x) for x in parts])
                    except (ValueError, IndexError):
                        in_thermo = False
                
                # Look for performance info
                if 'Loop time' in line:
                    try:
                        loop_time = float(re.search(r'Loop time of ([\d.]+)', line).group(1))
                        thermo_data['summary']['loop_time'] = loop_time
                    except (AttributeError, ValueError):
                        pass
            
            # Calculate summary statistics
            if thermo_data['data']:
                thermo_data['summary']['total_steps'] = len(thermo_data['data'])
                
                # Get final values
                if thermo_data['columns'] and thermo_data['data']:
                    final_values = thermo_data['data'][-1]
                    thermo_data['summary']['final'] = dict(zip(thermo_data['columns'], final_values))
        
        except Exception as e:
            print(f"Warning: Error parsing log file: {e}")
        
        return thermo_data
    
    def _parse_metadata(self, stdout: str, stderr: str) -> Dict[str, Any]:
        """Parse simulation output to extract metadata."""
        metadata = {}
        
        # Extract version info
        for line in stdout.split('\n'):
            if 'LAMMPS' in line and 'version' in line.lower():
                metadata['lammps_version'] = line.strip()
                break
        
        # Check for warnings or errors in stderr
        if stderr:
            metadata['has_warnings'] = True
            metadata['stderr_lines'] = len(stderr.split('\n'))
        
        return metadata
    
    def get_last_result(self) -> Optional[Dict[str, Any]]:
        """Get the result from the last simulation run."""
        return self.last_result
    
    def save_result_json(self, filepath: str = "simulation_result.json"):
        """
        Save the last simulation result to a JSON file.
        
        Args:
            filepath: Path to save JSON result
        """
        if self.last_result:
            result_path = self.output_dir / filepath
            with open(result_path, 'w') as f:
                json.dump(self.last_result, f, indent=2)
            print(f"✓ Result metadata saved to: {result_path}")
        else:
            print("No simulation result available to save.")
    
    def check_image_available(self) -> bool:
        """
        Check if the Docker image is available locally.
        
        Returns:
            True if image exists, False otherwise
        """
        try:
            result = subprocess.run(
                ["docker", "image", "inspect", self.image_name],
                capture_output=True
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def build_image(self, dockerfile_dir: str = ".", tag: Optional[str] = None) -> bool:
        """
        Build the Docker image for LAMMPS.
        
        Args:
            dockerfile_dir: Directory containing Dockerfile
            tag: Optional custom tag (default: use self.image_name)
            
        Returns:
            True if build succeeded, False otherwise
        """
        image_tag = tag or self.image_name
        
        try:
            print(f"Building Docker image: {image_tag}...")
            result = subprocess.run(
                ["docker", "build", "-t", image_tag, dockerfile_dir],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print("✓ Docker image built successfully!")
                return True
            else:
                print("✗ Docker image build failed!")
                print(result.stderr)
                return False
        except Exception as e:
            print(f"Error building image: {e}")
            return False
    
    def _get_capabilities(self) -> list:
        """
        Return list of capabilities supported by LAMMPS adapter.
        
        Returns:
            List of capability strings
        """
        return [
            "molecular_dynamics",
            "atomic_simulation",
            "lennard_jones",
            "coulombic_interactions",
            "bond_angle_dihedral",
            "nve_nvt_npt_ensembles",
            "parallel_computing",
            "trajectory_output",
            "thermodynamic_output"
        ]
    
    def _get_version(self) -> Optional[str]:
        """
        Get LAMMPS version from Docker image.
        
        Returns:
            Version string if available, None otherwise
        """
        try:
            result = subprocess.run(
                ["docker", "run", "--rm", self.image_name, 
                 "lmp", "-help"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                # Try to extract version from help output
                for line in result.stdout.split('\n'):
                    if 'LAMMPS' in line and any(char.isdigit() for char in line):
                        return line.strip()
        except Exception:
            pass
        return None


def main():
    """Example usage of the LAMMPS adapter."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="LAMMPS Simulation Adapter - Run containerized LAMMPS simulations"
    )
    parser.add_argument(
        "--image",
        type=str,
        default="keystone/lammps:latest",
        help="Docker image name (default: keystone/lammps:latest)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="./output",
        help="Output directory for simulation results"
    )
    parser.add_argument(
        "--input-script",
        type=str,
        help="Path to LAMMPS input script"
    )
    parser.add_argument(
        "--log-file",
        type=str,
        default="lammps.log",
        help="Name for LAMMPS log file (default: lammps.log)"
    )
    parser.add_argument(
        "--build",
        action="store_true",
        help="Build Docker image before running"
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Only check if Docker image is available"
    )
    
    args = parser.parse_args()
    
    # Create adapter
    adapter = LAMMPSAdapter(
        image_name=args.image,
        output_dir=args.output_dir
    )
    
    # Check image availability
    if args.check:
        available = adapter.check_image_available()
        if available:
            print(f"✓ Docker image '{args.image}' is available")
        else:
            print(f"✗ Docker image '{args.image}' is not available")
            print("  Run with --build to build the image")
        return
    
    # Build image if requested
    if args.build:
        if not adapter.build_image():
            print("Failed to build Docker image. Exiting.")
            return
    
    # Check if image is available
    if not adapter.check_image_available():
        print(f"✗ Docker image '{args.image}' is not available")
        print("  Run with --build to build the image, or build manually:")
        print(f"  docker build -t {args.image} .")
        return
    
    # Run simulation
    if not args.input_script:
        print("Error: --input-script is required to run a simulation")
        print("Use --check to verify image availability or --build to build the image")
        return
    
    result = adapter.run_simulation(
        input_script=args.input_script,
        log_file=args.log_file
    )
    
    # Save result metadata
    adapter.save_result_json()
    
    # Print summary
    print("\n" + "="*60)
    print("Simulation Summary")
    print("="*60)
    print(f"Success: {result['success']}")
    print(f"Output files: {len(result['output_files'])}")
    
    if result['thermo_data'] and 'summary' in result['thermo_data']:
        print("\nThermodynamic Summary:")
        for key, value in result['thermo_data']['summary'].items():
            if key != 'final':
                print(f"  {key}: {value}")
        
        if 'final' in result['thermo_data']['summary']:
            print("\nFinal State:")
            for key, value in result['thermo_data']['summary']['final'].items():
                print(f"  {key}: {value}")


if __name__ == "__main__":
    main()
