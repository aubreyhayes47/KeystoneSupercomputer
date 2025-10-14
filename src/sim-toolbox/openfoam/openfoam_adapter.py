#!/usr/bin/env python3
"""
OpenFOAM Simulation Adapter
============================

Python adapter for running OpenFOAM CFD simulations in Docker containers.
This adapter provides a standardized interface for:
- Accepting OpenFOAM case parameters and custom scripts
- Automating container execution
- Parsing solver logs and field data
- Enabling LLM-based tool calling and agentic orchestration

Usage:
    from openfoam_adapter import OpenFOAMAdapter
    
    adapter = OpenFOAMAdapter(
        image_name="openfoam-toolbox",
        output_dir="./output"
    )
    
    result = adapter.run_simulation(
        case_script="example_cavity.py",
        case_name="cavity"
    )
"""

import subprocess
import json
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Any
import tempfile
import shutil


class OpenFOAMAdapter:
    """Adapter for running OpenFOAM simulations in Docker containers."""
    
    def __init__(
        self,
        image_name: str = "openfoam-toolbox",
        output_dir: str = "./output",
        input_dir: Optional[str] = None,
        work_dir: Optional[str] = None
    ):
        """
        Initialize the OpenFOAM adapter.
        
        Args:
            image_name: Docker image name for OpenFOAM
            output_dir: Directory for simulation outputs
            input_dir: Optional directory for input files
            work_dir: Optional working directory (default: temporary directory)
        """
        self.image_name = image_name
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
        case_script: Optional[str] = None,
        script_content: Optional[str] = None,
        case_name: str = "cavity",
        script_args: Optional[List[str]] = None,
        docker_args: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Run an OpenFOAM simulation in a Docker container.
        
        Args:
            case_script: Path to Python script that sets up and runs the case
            script_content: Script content as string (alternative to case_script)
            case_name: Name of the OpenFOAM case
            script_args: Additional arguments to pass to the case script
            docker_args: Additional Docker run arguments
            
        Returns:
            Dictionary containing:
                - success: Whether simulation completed successfully
                - stdout: Standard output from simulation
                - stderr: Standard error from simulation
                - output_files: List of output files generated
                - solver_data: Parsed solver convergence data
                - metadata: Simulation metadata
        """
        use_temp_dir = self.work_dir is None
        work_dir = self.work_dir or Path(tempfile.mkdtemp())
        
        try:
            # Prepare the case script
            if script_content:
                script_file = work_dir / "case_script.py"
                script_file.write_text(script_content)
                script_path = script_file
                script_name = "case_script.py"
            elif case_script:
                script_path = Path(case_script).resolve()
                script_name = script_path.name
            else:
                # Use default example_cavity.py from container
                script_path = None
                script_name = "example_cavity.py"
            
            # Build Docker command
            cmd = ["docker", "run", "--rm"]
            
            # Mount input directory if provided
            if self.input_dir:
                cmd.extend(["-v", f"{self.input_dir}:/data/input"])
            
            # Mount output directory
            cmd.extend(["-v", f"{self.output_dir}:/data/output"])
            
            # Mount custom script if provided
            if script_path and script_path.exists():
                cmd.extend(["-v", f"{script_path}:/workspace/{script_name}"])
            
            # Add custom Docker arguments
            if docker_args:
                cmd.extend(docker_args)
            
            # Specify image
            cmd.append(self.image_name)
            
            # Build command to run inside container
            # Source OpenFOAM environment and run Python script
            container_cmd = f"source /opt/openfoam11/etc/bashrc && python3 /workspace/{script_name}"
            
            # Add script arguments
            if script_args:
                container_cmd += " " + " ".join(script_args)
            else:
                # Default arguments
                container_cmd += f" --output-dir /data/output/{case_name}"
            
            # Add to Docker command
            cmd.extend(["/bin/bash", "-c", container_cmd])
            
            print(f"Running OpenFOAM simulation...")
            print(f"Command: {' '.join(cmd)}")
            
            # Execute container
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True
            )
            
            # Parse output files
            output_files = self._scan_output_files()
            
            # Parse solver data from output
            solver_data = self._parse_solver_output(result.stdout)
            
            # Extract metadata
            metadata = self._parse_metadata(result.stdout, result.stderr)
            
            # Prepare result
            simulation_result = {
                "success": result.returncode == 0,
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "output_files": output_files,
                "solver_data": solver_data,
                "metadata": metadata,
                "output_dir": str(self.output_dir),
                "case_name": case_name
            }
            
            self.last_result = simulation_result
            
            if result.returncode == 0:
                print("✓ Simulation completed successfully!")
                print(f"✓ Output files: {len(output_files)}")
                print(f"✓ Results saved to: {self.output_dir}")
                if solver_data.get('timesteps_completed'):
                    print(f"✓ Timesteps completed: {solver_data['timesteps_completed']}")
            else:
                print("✗ Simulation failed!")
                print(f"Error: {result.stderr}")
            
            return simulation_result
            
        finally:
            # Clean up temporary directory if created
            if use_temp_dir and work_dir.exists():
                shutil.rmtree(work_dir)
    
    def run_case_direct(
        self,
        case_dir: str,
        solver: str = "icoFoam",
        mesh_command: str = "blockMesh",
        additional_commands: Optional[List[str]] = None,
        docker_args: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Run an OpenFOAM case directly by mounting the case directory.
        
        Args:
            case_dir: Path to OpenFOAM case directory
            solver: OpenFOAM solver to use
            mesh_command: Command to generate mesh (e.g., blockMesh, snappyHexMesh)
            additional_commands: List of additional OpenFOAM commands to run
            docker_args: Additional Docker run arguments
            
        Returns:
            Dictionary containing simulation results
        """
        case_path = Path(case_dir).resolve()
        
        if not case_path.exists():
            raise FileNotFoundError(f"Case directory not found: {case_path}")
        
        # Build Docker command
        cmd = ["docker", "run", "--rm"]
        
        # Mount case directory
        cmd.extend(["-v", f"{case_path}:/case"])
        
        # Mount output directory
        cmd.extend(["-v", f"{self.output_dir}:/data/output"])
        
        # Add custom Docker arguments
        if docker_args:
            cmd.extend(docker_args)
        
        # Specify image
        cmd.append(self.image_name)
        
        # Build commands to run
        commands = [
            "source /opt/openfoam11/etc/bashrc",
            "cd /case"
        ]
        
        # Add mesh generation
        if mesh_command:
            commands.append(mesh_command)
        
        # Add additional commands
        if additional_commands:
            commands.extend(additional_commands)
        
        # Add solver
        commands.append(solver)
        
        # Copy results
        commands.append("cp -r * /data/output/ 2>/dev/null || true")
        
        container_cmd = " && ".join(commands)
        cmd.extend(["/bin/bash", "-c", container_cmd])
        
        print(f"Running OpenFOAM case: {case_dir}")
        print(f"Solver: {solver}")
        
        # Execute container
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True
        )
        
        # Parse output files
        output_files = self._scan_output_files()
        
        # Parse solver data
        solver_data = self._parse_solver_output(result.stdout)
        
        # Extract metadata
        metadata = self._parse_metadata(result.stdout, result.stderr)
        metadata['solver'] = solver
        metadata['mesh_command'] = mesh_command
        
        # Prepare result
        simulation_result = {
            "success": result.returncode == 0,
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "output_files": output_files,
            "solver_data": solver_data,
            "metadata": metadata,
            "output_dir": str(self.output_dir),
            "case_dir": str(case_path)
        }
        
        self.last_result = simulation_result
        return simulation_result
    
    def _scan_output_files(self) -> List[str]:
        """Scan output directory for generated files."""
        output_files = []
        if self.output_dir.exists():
            for item in self.output_dir.rglob('*'):
                if item.is_file():
                    rel_path = item.relative_to(self.output_dir)
                    output_files.append(str(rel_path))
        return output_files
    
    def _parse_solver_output(self, stdout: str) -> Dict[str, Any]:
        """
        Parse OpenFOAM solver output to extract convergence data.
        
        Args:
            stdout: Standard output from simulation
            
        Returns:
            Dictionary with parsed solver data
        """
        solver_data = {
            "timesteps": [],
            "residuals": [],
            "timesteps_completed": 0
        }
        
        try:
            lines = stdout.split('\n')
            
            for line in lines:
                # Look for timestep markers (e.g., "Time = 0.1")
                time_match = re.search(r'Time\s*=\s*([\d.e+-]+)', line)
                if time_match:
                    solver_data['timesteps'].append(float(time_match.group(1)))
                
                # Look for residual information
                # Example: "Solving for Ux, Initial residual = 1, Final residual = 0.001"
                residual_match = re.search(
                    r'Solving for (\w+),.*Initial residual = ([\d.e+-]+).*Final residual = ([\d.e+-]+)',
                    line
                )
                if residual_match:
                    solver_data['residuals'].append({
                        'field': residual_match.group(1),
                        'initial': float(residual_match.group(2)),
                        'final': float(residual_match.group(3))
                    })
            
            solver_data['timesteps_completed'] = len(solver_data['timesteps'])
            
        except Exception as e:
            print(f"Warning: Error parsing solver output: {e}")
        
        return solver_data
    
    def _parse_metadata(self, stdout: str, stderr: str) -> Dict[str, Any]:
        """Parse simulation output to extract metadata."""
        metadata = {}
        
        # Look for case setup info
        for line in stdout.split('\n'):
            if 'Case directory:' in line:
                metadata['case_directory'] = line.split(':')[1].strip()
            elif 'mesh with' in line.lower() and 'cells' in line.lower():
                try:
                    # Extract cell count
                    match = re.search(r'(\d+)\s+cells', line, re.IGNORECASE)
                    if match:
                        metadata['mesh_cells'] = int(match.group(1))
                except (ValueError, AttributeError):
                    pass
        
        # Check for completion marker
        if 'completed successfully' in stdout.lower():
            metadata['completed_successfully'] = True
        
        # Check for warnings or errors
        if stderr:
            metadata['has_stderr'] = True
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
        Build the Docker image for OpenFOAM.
        
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


def main():
    """Example usage of the OpenFOAM adapter."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="OpenFOAM Simulation Adapter - Run containerized OpenFOAM simulations"
    )
    parser.add_argument(
        "--image",
        type=str,
        default="openfoam-toolbox",
        help="Docker image name (default: openfoam-toolbox)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="./output",
        help="Output directory for simulation results"
    )
    parser.add_argument(
        "--case-script",
        type=str,
        help="Path to Python script that sets up and runs the case"
    )
    parser.add_argument(
        "--case-name",
        type=str,
        default="cavity",
        help="Name of the OpenFOAM case (default: cavity)"
    )
    parser.add_argument(
        "--case-dir",
        type=str,
        help="Path to existing OpenFOAM case directory (alternative to case-script)"
    )
    parser.add_argument(
        "--solver",
        type=str,
        default="icoFoam",
        help="OpenFOAM solver to use (default: icoFoam, only with --case-dir)"
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
    adapter = OpenFOAMAdapter(
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
    if args.case_dir:
        # Run existing case directory
        result = adapter.run_case_direct(
            case_dir=args.case_dir,
            solver=args.solver
        )
    else:
        # Run using case script
        result = adapter.run_simulation(
            case_script=args.case_script,
            case_name=args.case_name
        )
    
    # Save result metadata
    adapter.save_result_json()
    
    # Print summary
    print("\n" + "="*60)
    print("Simulation Summary")
    print("="*60)
    print(f"Success: {result['success']}")
    print(f"Output files: {len(result['output_files'])}")
    
    if result['solver_data']:
        print("\nSolver Statistics:")
        print(f"  Timesteps completed: {result['solver_data'].get('timesteps_completed', 0)}")
        if result['solver_data'].get('residuals'):
            print(f"  Residual entries: {len(result['solver_data']['residuals'])}")
    
    if result['metadata']:
        print("\nMetadata:")
        for key, value in result['metadata'].items():
            print(f"  {key}: {value}")


if __name__ == "__main__":
    main()
