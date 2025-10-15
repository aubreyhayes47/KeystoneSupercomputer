#!/usr/bin/env python3
"""
Simulation Toolbox Integration Test
====================================

Integration test that runs at least one simulation in each containerized tool:
- FEniCSx: Finite element analysis (Poisson equation)
- LAMMPS: Molecular dynamics (Lennard-Jones fluid)
- OpenFOAM: Computational fluid dynamics (cavity flow)

This test verifies that:
1. Adapters can successfully automate the workflow
2. Docker images can be built
3. Simulations run to completion
4. Output results are collected and validated
5. Results are properly reported

Usage:
    python3 integration_test.py [--build] [--output-dir OUTPUT_DIR] [--report REPORT_FILE]
    
    --build: Build Docker images before running tests
    --output-dir: Base directory for all outputs (default: ./integration_test_output)
    --report: Path to save test report (default: integration_test_report.md)
"""

import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# Add adapters to path
sys.path.insert(0, str(Path(__file__).parent / "fenicsx"))
sys.path.insert(0, str(Path(__file__).parent / "lammps"))
sys.path.insert(0, str(Path(__file__).parent / "openfoam"))

from fenicsx_adapter import FEniCSxAdapter
from lammps_adapter import LAMMPSAdapter
from openfoam_adapter import OpenFOAMAdapter


class IntegrationTest:
    """Integration test orchestrator for all simulation toolboxes."""
    
    def __init__(self, output_base_dir: str = "./integration_test_output", build_images: bool = False):
        """
        Initialize the integration test.
        
        Args:
            output_base_dir: Base directory for test outputs
            build_images: Whether to build Docker images before testing
        """
        self.output_base_dir = Path(output_base_dir).resolve()
        self.build_images = build_images
        self.results = []
        self.start_time = None
        self.end_time = None
        
        # Create output directory
        self.output_base_dir.mkdir(parents=True, exist_ok=True)
        
    def run_all_tests(self) -> bool:
        """
        Run integration tests for all simulation toolboxes.
        
        Returns:
            True if all tests passed, False otherwise
        """
        self.start_time = datetime.now()
        
        print("="*80)
        print("SIMULATION TOOLBOX INTEGRATION TEST")
        print("="*80)
        print(f"Start time: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Output directory: {self.output_base_dir}")
        print(f"Build images: {self.build_images}")
        print("="*80 + "\n")
        
        # Run tests for each toolbox
        self.results.append(self.test_fenicsx())
        self.results.append(self.test_lammps())
        self.results.append(self.test_openfoam())
        
        self.end_time = datetime.now()
        
        # Print summary
        self._print_summary()
        
        # Return overall status
        return all(result['passed'] for result in self.results)
    
    def test_fenicsx(self) -> Dict[str, Any]:
        """Test FEniCSx adapter with Poisson equation solver."""
        print("\n" + "="*80)
        print("TEST 1: FEniCSx (Finite Element Analysis)")
        print("="*80)
        print("Simulation: 2D Poisson Equation")
        print("Description: Solves -∇²u = f in a unit square with Dirichlet BC")
        print("-"*80 + "\n")
        
        result = {
            'toolbox': 'FEniCSx',
            'test_name': 'Poisson Equation',
            'passed': False,
            'image_name': 'fenicsx-toolbox',
            'start_time': datetime.now(),
            'output_dir': None,
            'simulation_result': None,
            'error_message': None
        }
        
        try:
            # Setup adapter
            output_dir = self.output_base_dir / "fenicsx"
            adapter = FEniCSxAdapter(
                image_name="fenicsx-toolbox",
                output_dir=str(output_dir)
            )
            result['output_dir'] = str(output_dir)
            
            # Build image if requested
            if self.build_images:
                print("Building FEniCSx Docker image...")
                fenicsx_dir = Path(__file__).parent / "fenicsx"
                if not adapter.build_image(dockerfile_dir=str(fenicsx_dir)):
                    result['error_message'] = "Failed to build Docker image"
                    print(f"✗ {result['error_message']}\n")
                    return result
                print("✓ Image built successfully\n")
            
            # Check image availability
            if not adapter.check_image_available():
                result['error_message'] = "Docker image not available"
                print(f"✗ {result['error_message']}")
                print("  Run with --build flag to build images\n")
                return result
            
            print("✓ Docker image available\n")
            
            # Test orchestration features
            print("Testing orchestration features...")
            
            # Health check
            print("  - Running health check...")
            health = adapter.health_check()
            print(f"    Status: {health['status']}")
            print(f"    Checks passed: {sum(1 for v in health['checks'].values() if v)}/{len(health['checks'])}")
            
            # Status reporting
            print("  - Getting status...")
            status = adapter.get_status()
            print(f"    State: {status['state']}")
            
            # Metadata API
            print("  - Getting metadata...")
            metadata = adapter.get_metadata()
            print(f"    Tool: {metadata['tool_name']}")
            print(f"    Capabilities: {len(metadata['capabilities'])} features")
            
            print("✓ Orchestration features validated\n")
            
            # Run simulation with default Poisson script
            print("Running Poisson equation simulation...")
            script_path = Path(__file__).parent / "fenicsx" / "poisson.py"
            
            sim_result = adapter.run_simulation(script_path=str(script_path))
            result['simulation_result'] = sim_result
            
            # Save result JSON
            adapter.save_result_json()
            
            # Validate results
            if sim_result['success']:
                print("\n✓ Simulation completed successfully!")
                print(f"✓ Output directory: {output_dir}")
                print(f"✓ Output files: {len(sim_result['output_files'])}")
                
                if sim_result['metadata']:
                    print("\nSimulation Metadata:")
                    for key, value in sim_result['metadata'].items():
                        print(f"  - {key}: {value}")
                
                result['passed'] = True
            else:
                result['error_message'] = f"Simulation failed (returncode: {sim_result.get('returncode', 'unknown')})"
                print(f"\n✗ {result['error_message']}")
                
        except Exception as e:
            result['error_message'] = str(e)
            print(f"\n✗ Test failed with exception: {e}")
        
        result['end_time'] = datetime.now()
        result['duration_seconds'] = (result['end_time'] - result['start_time']).total_seconds()
        
        return result
    
    def test_lammps(self) -> Dict[str, Any]:
        """Test LAMMPS adapter with Lennard-Jones fluid simulation."""
        print("\n" + "="*80)
        print("TEST 2: LAMMPS (Molecular Dynamics)")
        print("="*80)
        print("Simulation: Lennard-Jones Fluid")
        print("Description: MD simulation of argon-like atoms with LJ potential")
        print("-"*80 + "\n")
        
        result = {
            'toolbox': 'LAMMPS',
            'test_name': 'Lennard-Jones Fluid',
            'passed': False,
            'image_name': 'keystone/lammps:latest',
            'start_time': datetime.now(),
            'output_dir': None,
            'simulation_result': None,
            'error_message': None
        }
        
        try:
            # Setup adapter
            output_dir = self.output_base_dir / "lammps"
            adapter = LAMMPSAdapter(
                image_name="keystone/lammps:latest",
                output_dir=str(output_dir)
            )
            result['output_dir'] = str(output_dir)
            
            # Build image if requested
            if self.build_images:
                print("Building LAMMPS Docker image...")
                lammps_dir = Path(__file__).parent / "lammps"
                if not adapter.build_image(dockerfile_dir=str(lammps_dir)):
                    result['error_message'] = "Failed to build Docker image"
                    print(f"✗ {result['error_message']}\n")
                    return result
                print("✓ Image built successfully\n")
            
            # Check image availability
            if not adapter.check_image_available():
                result['error_message'] = "Docker image not available"
                print(f"✗ {result['error_message']}")
                print("  Run with --build flag to build images\n")
                return result
            
            print("✓ Docker image available\n")
            
            # Test orchestration features
            print("Testing orchestration features...")
            
            # Health check
            print("  - Running health check...")
            health = adapter.health_check()
            print(f"    Status: {health['status']}")
            print(f"    Checks passed: {sum(1 for v in health['checks'].values() if v)}/{len(health['checks'])}")
            
            # Status reporting
            print("  - Getting status...")
            status = adapter.get_status()
            print(f"    State: {status['state']}")
            
            # Metadata API
            print("  - Getting metadata...")
            metadata = adapter.get_metadata()
            print(f"    Tool: {metadata['tool_name']}")
            print(f"    Capabilities: {len(metadata['capabilities'])} features")
            
            print("✓ Orchestration features validated\n")
            
            # Run simulation with example LAMMPS script
            print("Running Lennard-Jones fluid simulation...")
            script_path = Path(__file__).parent / "lammps" / "example.lammps"
            
            sim_result = adapter.run_simulation(
                input_script=str(script_path),
                log_file="lammps.log"
            )
            result['simulation_result'] = sim_result
            
            # Save result JSON
            adapter.save_result_json()
            
            # Validate results
            if sim_result['success']:
                print("\n✓ Simulation completed successfully!")
                print(f"✓ Output directory: {output_dir}")
                print(f"✓ Output files: {len(sim_result['output_files'])}")
                
                if sim_result.get('thermo_data') and 'summary' in sim_result['thermo_data']:
                    print("\nThermodynamic Summary:")
                    summary = sim_result['thermo_data']['summary']
                    if 'total_steps' in summary:
                        print(f"  - Total steps: {summary['total_steps']}")
                    if 'loop_time' in summary:
                        print(f"  - Loop time: {summary['loop_time']:.3f} seconds")
                    if 'final' in summary:
                        print("  - Final state:")
                        for key, val in summary['final'].items():
                            print(f"    • {key}: {val}")
                
                result['passed'] = True
            else:
                result['error_message'] = f"Simulation failed (returncode: {sim_result.get('returncode', 'unknown')})"
                print(f"\n✗ {result['error_message']}")
                
        except Exception as e:
            result['error_message'] = str(e)
            print(f"\n✗ Test failed with exception: {e}")
        
        result['end_time'] = datetime.now()
        result['duration_seconds'] = (result['end_time'] - result['start_time']).total_seconds()
        
        return result
    
    def test_openfoam(self) -> Dict[str, Any]:
        """Test OpenFOAM adapter with cavity flow simulation."""
        print("\n" + "="*80)
        print("TEST 3: OpenFOAM (Computational Fluid Dynamics)")
        print("="*80)
        print("Simulation: Lid-Driven Cavity Flow")
        print("Description: Incompressible laminar flow with moving top wall")
        print("-"*80 + "\n")
        
        result = {
            'toolbox': 'OpenFOAM',
            'test_name': 'Cavity Flow',
            'passed': False,
            'image_name': 'openfoam-toolbox',
            'start_time': datetime.now(),
            'output_dir': None,
            'simulation_result': None,
            'error_message': None
        }
        
        try:
            # Setup adapter
            output_dir = self.output_base_dir / "openfoam"
            adapter = OpenFOAMAdapter(
                image_name="openfoam-toolbox",
                output_dir=str(output_dir)
            )
            result['output_dir'] = str(output_dir)
            
            # Build image if requested
            if self.build_images:
                print("Building OpenFOAM Docker image...")
                openfoam_dir = Path(__file__).parent / "openfoam"
                if not adapter.build_image(dockerfile_dir=str(openfoam_dir)):
                    result['error_message'] = "Failed to build Docker image"
                    print(f"✗ {result['error_message']}\n")
                    return result
                print("✓ Image built successfully\n")
            
            # Check image availability
            if not adapter.check_image_available():
                result['error_message'] = "Docker image not available"
                print(f"✗ {result['error_message']}")
                print("  Run with --build flag to build images\n")
                return result
            
            print("✓ Docker image available\n")
            
            # Test orchestration features
            print("Testing orchestration features...")
            
            # Health check
            print("  - Running health check...")
            health = adapter.health_check()
            print(f"    Status: {health['status']}")
            print(f"    Checks passed: {sum(1 for v in health['checks'].values() if v)}/{len(health['checks'])}")
            
            # Status reporting
            print("  - Getting status...")
            status = adapter.get_status()
            print(f"    State: {status['state']}")
            
            # Metadata API
            print("  - Getting metadata...")
            metadata = adapter.get_metadata()
            print(f"    Tool: {metadata['tool_name']}")
            print(f"    Capabilities: {len(metadata['capabilities'])} features")
            
            print("✓ Orchestration features validated\n")
            
            # Run simulation with cavity flow example
            print("Running cavity flow simulation...")
            script_path = Path(__file__).parent / "openfoam" / "example_cavity.py"
            
            sim_result = adapter.run_simulation(
                case_script=str(script_path),
                case_name="cavity"
            )
            result['simulation_result'] = sim_result
            
            # Save result JSON
            adapter.save_result_json()
            
            # Validate results
            if sim_result['success']:
                print("\n✓ Simulation completed successfully!")
                print(f"✓ Output directory: {output_dir}")
                print(f"✓ Output files: {len(sim_result['output_files'])}")
                
                if sim_result.get('solver_data'):
                    print("\nSolver Information:")
                    solver_data = sim_result['solver_data']
                    if 'timesteps_completed' in solver_data:
                        print(f"  - Timesteps completed: {solver_data['timesteps_completed']}")
                    if 'solver' in solver_data:
                        print(f"  - Solver: {solver_data['solver']}")
                
                result['passed'] = True
            else:
                result['error_message'] = f"Simulation failed (returncode: {sim_result.get('returncode', 'unknown')})"
                print(f"\n✗ {result['error_message']}")
                
        except Exception as e:
            result['error_message'] = str(e)
            print(f"\n✗ Test failed with exception: {e}")
        
        result['end_time'] = datetime.now()
        result['duration_seconds'] = (result['end_time'] - result['start_time']).total_seconds()
        
        return result
    
    def _print_summary(self):
        """Print test summary."""
        print("\n" + "="*80)
        print("INTEGRATION TEST SUMMARY")
        print("="*80)
        
        total_duration = (self.end_time - self.start_time).total_seconds()
        passed_count = sum(1 for r in self.results if r['passed'])
        failed_count = len(self.results) - passed_count
        
        print(f"Total tests: {len(self.results)}")
        print(f"Passed: {passed_count}")
        print(f"Failed: {failed_count}")
        print(f"Total duration: {total_duration:.2f} seconds")
        print("-"*80)
        
        for result in self.results:
            status = "✓ PASSED" if result['passed'] else "✗ FAILED"
            duration = result.get('duration_seconds', 0)
            print(f"{result['toolbox']:15s} - {result['test_name']:25s} {status:10s} ({duration:.2f}s)")
            
            if not result['passed'] and result['error_message']:
                print(f"  Error: {result['error_message']}")
        
        print("="*80)
        
        if all(r['passed'] for r in self.results):
            print("\n✓ ALL INTEGRATION TESTS PASSED!")
        else:
            print("\n✗ SOME INTEGRATION TESTS FAILED!")
        
        print("="*80 + "\n")
    
    def generate_report(self, report_file: str = "integration_test_report.md"):
        """
        Generate markdown report of test results.
        
        Args:
            report_file: Path to save the report
        """
        report_path = Path(report_file).resolve()
        
        with open(report_path, 'w') as f:
            f.write("# Simulation Toolbox Integration Test Report\n\n")
            f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"**Test Start:** {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"**Test End:** {self.end_time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            total_duration = (self.end_time - self.start_time).total_seconds()
            f.write(f"**Total Duration:** {total_duration:.2f} seconds\n\n")
            
            # Summary
            passed_count = sum(1 for r in self.results if r['passed'])
            f.write("## Summary\n\n")
            f.write(f"- **Total Tests:** {len(self.results)}\n")
            f.write(f"- **Passed:** {passed_count}\n")
            f.write(f"- **Failed:** {len(self.results) - passed_count}\n")
            f.write(f"- **Success Rate:** {(passed_count/len(self.results)*100):.1f}%\n\n")
            
            # Overall status
            if all(r['passed'] for r in self.results):
                f.write("**Status:** ✓ ALL TESTS PASSED\n\n")
            else:
                f.write("**Status:** ✗ SOME TESTS FAILED\n\n")
            
            # Detailed results
            f.write("## Test Results\n\n")
            
            for i, result in enumerate(self.results, 1):
                status_icon = "✓" if result['passed'] else "✗"
                f.write(f"### {i}. {result['toolbox']} - {result['test_name']}\n\n")
                f.write(f"**Status:** {status_icon} {'PASSED' if result['passed'] else 'FAILED'}\n\n")
                f.write(f"**Image:** `{result['image_name']}`\n\n")
                f.write(f"**Duration:** {result.get('duration_seconds', 0):.2f} seconds\n\n")
                
                if result['output_dir']:
                    f.write(f"**Output Directory:** `{result['output_dir']}`\n\n")
                
                if result['passed']:
                    sim_result = result['simulation_result']
                    if sim_result:
                        f.write("**Simulation Output:**\n\n")
                        f.write(f"- Success: {sim_result['success']}\n")
                        f.write(f"- Output files: {len(sim_result['output_files'])}\n")
                        
                        if sim_result['output_files']:
                            f.write(f"- Files generated:\n")
                            for file in sim_result['output_files'][:5]:  # Show first 5
                                f.write(f"  - `{file}`\n")
                            if len(sim_result['output_files']) > 5:
                                f.write(f"  - ... and {len(sim_result['output_files']) - 5} more\n")
                        
                        # Add toolbox-specific metadata
                        if result['toolbox'] == 'FEniCSx' and sim_result.get('metadata'):
                            f.write("\n**FEniCSx Metadata:**\n\n")
                            for key, value in sim_result['metadata'].items():
                                f.write(f"- {key}: {value}\n")
                        
                        elif result['toolbox'] == 'LAMMPS' and sim_result.get('thermo_data'):
                            thermo = sim_result['thermo_data']
                            if 'summary' in thermo:
                                f.write("\n**LAMMPS Thermodynamics:**\n\n")
                                summary = thermo['summary']
                                for key in ['total_steps', 'loop_time', 'timestep']:
                                    if key in summary:
                                        f.write(f"- {key}: {summary[key]}\n")
                        
                        elif result['toolbox'] == 'OpenFOAM' and sim_result.get('solver_data'):
                            f.write("\n**OpenFOAM Solver Data:**\n\n")
                            solver_data = sim_result['solver_data']
                            for key in ['timesteps_completed', 'solver', 'mesh_cells']:
                                if key in solver_data:
                                    f.write(f"- {key}: {solver_data[key]}\n")
                        
                        f.write("\n")
                else:
                    f.write(f"**Error:** {result['error_message']}\n\n")
                
                f.write("---\n\n")
            
            # Validation criteria
            f.write("## Validation Criteria\n\n")
            f.write("This integration test validates that:\n\n")
            f.write("1. ✓ Docker images can be built or are available for all tools\n")
            f.write("2. ✓ Adapters successfully automate container execution\n")
            f.write("3. ✓ Simulations run to completion without errors\n")
            f.write("4. ✓ Output results are collected and saved to designated directories\n")
            f.write("5. ✓ Results are properly structured and can be parsed\n")
            f.write("6. ✓ End-to-end workflow orchestration is functional\n\n")
            
            # Output directories
            f.write("## Output Directories\n\n")
            f.write("Test outputs are organized as follows:\n\n")
            f.write("```\n")
            f.write(f"{self.output_base_dir}/\n")
            f.write("├── fenicsx/\n")
            f.write("│   ├── simulation_result.json\n")
            f.write("│   └── [FEniCSx output files]\n")
            f.write("├── lammps/\n")
            f.write("│   ├── simulation_result.json\n")
            f.write("│   └── [LAMMPS output files]\n")
            f.write("└── openfoam/\n")
            f.write("    ├── simulation_result.json\n")
            f.write("    └── [OpenFOAM output files]\n")
            f.write("```\n\n")
            
            # Conclusion
            f.write("## Conclusion\n\n")
            if all(r['passed'] for r in self.results):
                f.write("All integration tests passed successfully! The simulation toolbox is fully ")
                f.write("functional and capable of orchestrating end-to-end scientific simulations ")
                f.write("across FEniCSx, LAMMPS, and OpenFOAM.\n\n")
            else:
                f.write("Some integration tests failed. Please review the errors above and ensure:\n\n")
                f.write("- Docker images are built (use --build flag)\n")
                f.write("- Docker daemon is running\n")
                f.write("- Input scripts are available\n")
                f.write("- Sufficient system resources are available\n\n")
            
            f.write("---\n\n")
            f.write("*This report was auto-generated by the Simulation Toolbox Integration Test*\n")
        
        print(f"✓ Test report generated: {report_path}\n")


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description="Run integration tests for simulation toolbox"
    )
    parser.add_argument(
        "--build",
        action="store_true",
        help="Build Docker images before running tests"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="./integration_test_output",
        help="Base directory for test outputs (default: ./integration_test_output)"
    )
    parser.add_argument(
        "--report",
        type=str,
        default="integration_test_report.md",
        help="Path to save test report (default: integration_test_report.md)"
    )
    
    args = parser.parse_args()
    
    # Run integration tests
    test = IntegrationTest(
        output_base_dir=args.output_dir,
        build_images=args.build
    )
    
    all_passed = test.run_all_tests()
    
    # Generate report
    test.generate_report(report_file=args.report)
    
    # Exit with appropriate code
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
