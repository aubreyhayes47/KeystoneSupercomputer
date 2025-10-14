#!/usr/bin/env python3
"""
FEniCSx Simulation Adapter
===========================

Python adapter for running FEniCSx simulations in Docker containers.
This adapter provides a standardized interface for:
- Accepting input parameters and custom scripts
- Automating container execution
- Parsing and reporting simulation results
- Enabling LLM-based tool calling and agentic orchestration

Usage:
    from fenicsx_adapter import FEniCSxAdapter
    
    adapter = FEniCSxAdapter(
        image_name="fenicsx-toolbox",
        output_dir="./output"
    )
    
    result = adapter.run_simulation(
        script_path="poisson.py",
        custom_params={"mesh_size": 64}
    )
"""

import subprocess
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
import tempfile
import shutil


class FEniCSxAdapter:
    """Adapter for running FEniCSx simulations in Docker containers."""
    
    def __init__(
        self,
        image_name: str = "fenicsx-toolbox",
        output_dir: str = "./output",
        work_dir: Optional[str] = None
    ):
        """
        Initialize the FEniCSx adapter.
        
        Args:
            image_name: Docker image name for FEniCSx
            output_dir: Directory for simulation outputs
            work_dir: Optional working directory (default: temporary directory)
        """
        self.image_name = image_name
        self.output_dir = Path(output_dir).resolve()
        self.work_dir = Path(work_dir) if work_dir else None
        self.last_result = None
        
        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def run_simulation(
        self,
        script_path: Optional[str] = None,
        script_content: Optional[str] = None,
        custom_params: Optional[Dict[str, Any]] = None,
        docker_args: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Run a FEniCSx simulation in a Docker container.
        
        Args:
            script_path: Path to Python script to run (default: use built-in poisson.py)
            script_content: Python script content as string (alternative to script_path)
            custom_params: Optional dictionary of parameters to pass to script
            docker_args: Additional Docker run arguments
            
        Returns:
            Dictionary containing:
                - success: Whether simulation completed successfully
                - stdout: Standard output from simulation
                - stderr: Standard error from simulation
                - output_files: List of output files generated
                - metadata: Simulation metadata
        """
        use_temp_dir = self.work_dir is None
        work_dir = self.work_dir or Path(tempfile.mkdtemp())
        
        try:
            # Prepare the simulation script
            if script_content:
                script_file = work_dir / "custom_script.py"
                script_file.write_text(script_content)
                script_name = "custom_script.py"
            elif script_path:
                script_file = Path(script_path).resolve()
                script_name = script_file.name
            else:
                # Use default poisson.py from container
                script_file = None
                script_name = "poisson.py"
            
            # Build Docker command
            cmd = ["docker", "run", "--rm"]
            
            # Mount output directory
            cmd.extend(["-v", f"{self.output_dir}:/data"])
            
            # Mount custom script if provided
            if script_file:
                cmd.extend(["-v", f"{script_file}:/app/{script_name}"])
            
            # Add custom Docker arguments
            if docker_args:
                cmd.extend(docker_args)
            
            # Specify image
            cmd.append(self.image_name)
            
            # Specify script to run
            cmd.append(script_name)
            
            # Add custom parameters as command-line arguments
            if custom_params:
                for key, value in custom_params.items():
                    cmd.extend([f"--{key}", str(value)])
            
            print(f"Running FEniCSx simulation...")
            print(f"Command: {' '.join(cmd)}")
            
            # Execute container
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True
            )
            
            # Parse output files
            output_files = self._scan_output_files()
            
            # Extract statistics from stdout if available
            metadata = self._parse_output(result.stdout)
            
            # Prepare result
            simulation_result = {
                "success": result.returncode == 0,
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "output_files": output_files,
                "metadata": metadata,
                "output_dir": str(self.output_dir)
            }
            
            self.last_result = simulation_result
            
            if result.returncode == 0:
                print("✓ Simulation completed successfully!")
                print(f"✓ Output files: {len(output_files)}")
                print(f"✓ Results saved to: {self.output_dir}")
            else:
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
    
    def _parse_output(self, stdout: str) -> Dict[str, Any]:
        """Parse simulation output to extract metadata."""
        metadata = {}
        
        # Extract statistics from output
        for line in stdout.split('\n'):
            if 'Min value:' in line:
                try:
                    metadata['min_value'] = float(line.split(':')[1].strip())
                except (ValueError, IndexError):
                    pass
            elif 'Max value:' in line:
                try:
                    metadata['max_value'] = float(line.split(':')[1].strip())
                except (ValueError, IndexError):
                    pass
            elif 'Mean value:' in line:
                try:
                    metadata['mean_value'] = float(line.split(':')[1].strip())
                except (ValueError, IndexError):
                    pass
            elif 'Mesh created:' in line:
                try:
                    metadata['mesh_cells'] = int(line.split(':')[1].split()[0].strip())
                except (ValueError, IndexError):
                    pass
            elif 'Function space dimension:' in line:
                try:
                    metadata['dof_count'] = int(line.split(':')[1].strip())
                except (ValueError, IndexError):
                    pass
        
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
    
    def build_image(self, dockerfile_dir: str = ".") -> bool:
        """
        Build the Docker image for FEniCSx.
        
        Args:
            dockerfile_dir: Directory containing Dockerfile
            
        Returns:
            True if build succeeded, False otherwise
        """
        try:
            print(f"Building Docker image: {self.image_name}...")
            result = subprocess.run(
                ["docker", "build", "-t", self.image_name, dockerfile_dir],
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
    """Example usage of the FEniCSx adapter."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="FEniCSx Simulation Adapter - Run containerized FEniCS simulations"
    )
    parser.add_argument(
        "--image",
        type=str,
        default="fenicsx-toolbox",
        help="Docker image name (default: fenicsx-toolbox)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="./output",
        help="Output directory for simulation results"
    )
    parser.add_argument(
        "--script",
        type=str,
        help="Path to custom Python script to run"
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
    adapter = FEniCSxAdapter(
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
    result = adapter.run_simulation(script_path=args.script)
    
    # Save result metadata
    adapter.save_result_json()
    
    # Print summary
    print("\n" + "="*60)
    print("Simulation Summary")
    print("="*60)
    print(f"Success: {result['success']}")
    print(f"Output files: {len(result['output_files'])}")
    if result['metadata']:
        print("\nMetadata:")
        for key, value in result['metadata'].items():
            print(f"  {key}: {value}")


if __name__ == "__main__":
    main()
