#!/usr/bin/env python3
"""
Example demonstrating orchestration features in simulation adapters.

This example shows how to:
1. Check adapter health before running simulations
2. Monitor simulation status
3. Query adapter metadata and capabilities
4. Handle errors gracefully with health checks
"""

import sys
from pathlib import Path

# Add adapters to path
sys.path.insert(0, str(Path(__file__).parent / "fenicsx"))

from fenicsx_adapter import FEniCSxAdapter


def print_section(title):
    """Print a formatted section header."""
    print(f"\n{'='*70}")
    print(f"{title}")
    print(f"{'='*70}\n")


def main():
    """Demonstrate orchestration features."""
    print_section("Simulation Adapter Orchestration Example")
    
    # Initialize adapter
    print("1. Initializing FEniCSx adapter...")
    adapter = FEniCSxAdapter(
        image_name="fenicsx-toolbox",
        output_dir="./orchestration_example_output"
    )
    print("   ✓ Adapter initialized\n")
    
    # Get metadata
    print_section("2. Querying Adapter Metadata")
    metadata = adapter.get_metadata()
    print(f"Tool Name: {metadata['tool_name']}")
    print(f"Image: {metadata['image_name']}")
    print(f"Output Directory: {metadata['output_dir']}")
    print(f"\nCapabilities ({len(metadata['capabilities'])} total):")
    for cap in metadata['capabilities']:
        print(f"  • {cap}")
    if metadata['version']:
        print(f"\nVersion: {metadata['version']}")
    
    # Perform health check
    print_section("3. Performing Health Check")
    health = adapter.health_check()
    print(f"Overall Status: {health['status'].upper()}")
    print(f"Timestamp: {health['timestamp']}")
    print(f"\nIndividual Checks:")
    for check_name, check_result in health['checks'].items():
        status_icon = "✓" if check_result else "✗"
        print(f"  {status_icon} {check_name}: {check_result}")
    print(f"\nMessage: {health['message']}")
    
    # Check if healthy
    if health['status'] != 'healthy':
        print(f"\n⚠ Adapter is not healthy: {health['message']}")
        print("   Cannot proceed with simulation.")
        print("\n   Common solutions:")
        if not health['checks'].get('image_available', False):
            print("   - Build the Docker image:")
            print(f"     cd {Path(__file__).parent / 'fenicsx'}")
            print("     docker build -t fenicsx-toolbox .")
        if not health['checks'].get('docker_accessible', False):
            print("   - Ensure Docker daemon is running:")
            print("     sudo systemctl start docker")
        return 1
    
    # Get initial status
    print_section("4. Checking Initial Status")
    status = adapter.get_status()
    print(f"State: {status['state']}")
    print(f"Last Result: {status['last_result']}")
    print(f"Timestamp: {status['timestamp']}")
    
    # Run simulation (commented out - requires Docker image)
    print_section("5. Running Simulation (Commented Out)")
    print("To run a simulation, uncomment the following code:")
    print("""
    print("Running Poisson equation simulation...")
    result = adapter.run_simulation()
    
    # Check final status
    final_status = adapter.get_status()
    print(f"\\nFinal State: {final_status['state']}")
    print(f"Success: {result['success']}")
    print(f"Output files: {len(result['output_files'])}")
    
    # Save results
    adapter.save_result_json()
    print(f"Results saved to: {adapter.output_dir}")
    """)
    
    print_section("Summary")
    print("This example demonstrated:")
    print("  ✓ Querying adapter metadata and capabilities")
    print("  ✓ Performing comprehensive health checks")
    print("  ✓ Checking adapter status")
    print("  ✓ Handling health check failures gracefully")
    print("\nThese orchestration features enable:")
    print("  • Robust error handling in production")
    print("  • Integration with orchestration platforms")
    print("  • Automated health monitoring")
    print("  • Service discovery and capability checking")
    
    print_section("Next Steps")
    print("1. Build the Docker images for all adapters")
    print("2. Run the orchestration test suite:")
    print("   python3 test_orchestration.py")
    print("3. Run the full integration test:")
    print("   python3 integration_test.py --build")
    print("4. See ORCHESTRATION.md for integration examples\n")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
