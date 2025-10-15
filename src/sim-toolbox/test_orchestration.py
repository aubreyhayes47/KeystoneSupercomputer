#!/usr/bin/env python3
"""
Test suite for orchestration features in simulation adapters.

Tests health checks, status reporting, and metadata APIs for:
- OpenFOAM adapter
- LAMMPS adapter  
- FEniCSx adapter
"""

import sys
from pathlib import Path
import json
import tempfile
import shutil

# Add adapters to path
sim_toolbox = Path(__file__).parent
sys.path.insert(0, str(sim_toolbox / "openfoam"))
sys.path.insert(0, str(sim_toolbox / "lammps"))
sys.path.insert(0, str(sim_toolbox / "fenicsx"))

from openfoam_adapter import OpenFOAMAdapter
from lammps_adapter import LAMMPSAdapter
from fenicsx_adapter import FEniCSxAdapter


def test_adapter_orchestration(adapter_class, adapter_name, **kwargs):
    """
    Test orchestration features for a given adapter.
    
    Args:
        adapter_class: Adapter class to test
        adapter_name: Name of adapter for reporting
        **kwargs: Additional arguments for adapter initialization
    """
    print(f"\n{'='*70}")
    print(f"Testing {adapter_name} Orchestration Features")
    print(f"{'='*70}")
    
    # Create temporary output directory
    temp_dir = Path(tempfile.mkdtemp())
    
    try:
        # Initialize adapter
        print(f"\n1. Initializing {adapter_name} adapter...")
        adapter = adapter_class(output_dir=str(temp_dir), **kwargs)
        print(f"   ✓ Adapter initialized")
        
        # Test health check
        print(f"\n2. Testing health check...")
        health = adapter.health_check()
        print(f"   Status: {health['status']}")
        print(f"   Timestamp: {health['timestamp']}")
        print(f"   Tool: {health['tool']}")
        print(f"   Image: {health['image']}")
        print(f"   Checks:")
        for check_name, check_result in health['checks'].items():
            status_icon = "✓" if check_result else "✗"
            print(f"     {status_icon} {check_name}: {check_result}")
        print(f"   Message: {health['message']}")
        
        # Validate health check structure
        assert 'status' in health, "Health check missing 'status'"
        assert 'timestamp' in health, "Health check missing 'timestamp'"
        assert 'checks' in health, "Health check missing 'checks'"
        assert 'message' in health, "Health check missing 'message'"
        print(f"   ✓ Health check structure valid")
        
        # Test status reporting
        print(f"\n3. Testing status reporting...")
        status = adapter.get_status()
        print(f"   State: {status['state']}")
        print(f"   Timestamp: {status['timestamp']}")
        print(f"   Last result: {status['last_result']}")
        print(f"   Last health check available: {status['last_health_check'] is not None}")
        
        # Validate status structure
        assert 'state' in status, "Status missing 'state'"
        assert 'timestamp' in status, "Status missing 'timestamp'"
        assert 'last_result' in status, "Status missing 'last_result'"
        assert 'metadata' in status, "Status missing 'metadata'"
        print(f"   ✓ Status structure valid")
        
        # Test metadata API
        print(f"\n4. Testing metadata API...")
        metadata = adapter.get_metadata()
        print(f"   Tool name: {metadata['tool_name']}")
        print(f"   Image name: {metadata['image_name']}")
        print(f"   Output dir: {metadata['output_dir']}")
        print(f"   Timestamp: {metadata['timestamp']}")
        print(f"   Capabilities: {len(metadata['capabilities'])} features")
        for cap in metadata['capabilities'][:3]:
            print(f"     - {cap}")
        if len(metadata['capabilities']) > 3:
            print(f"     - ... and {len(metadata['capabilities']) - 3} more")
        if metadata.get('version'):
            print(f"   Version: {metadata['version']}")
        
        # Validate metadata structure
        assert 'tool_name' in metadata, "Metadata missing 'tool_name'"
        assert 'image_name' in metadata, "Metadata missing 'image_name'"
        assert 'capabilities' in metadata, "Metadata missing 'capabilities'"
        assert isinstance(metadata['capabilities'], list), "Capabilities should be a list"
        assert len(metadata['capabilities']) > 0, "Capabilities list should not be empty"
        print(f"   ✓ Metadata structure valid")
        
        # Test JSON serialization
        print(f"\n5. Testing JSON serialization...")
        health_json = json.dumps(health, indent=2)
        status_json = json.dumps(status, indent=2, default=str)
        metadata_json = json.dumps(metadata, indent=2)
        print(f"   ✓ Health check serializable ({len(health_json)} bytes)")
        print(f"   ✓ Status serializable ({len(status_json)} bytes)")
        print(f"   ✓ Metadata serializable ({len(metadata_json)} bytes)")
        
        print(f"\n{'='*70}")
        print(f"✓ All {adapter_name} orchestration tests passed!")
        print(f"{'='*70}")
        
        return True
        
    except Exception as e:
        print(f"\n{'='*70}")
        print(f"✗ {adapter_name} orchestration test failed!")
        print(f"Error: {e}")
        print(f"{'='*70}")
        return False
        
    finally:
        # Clean up temporary directory
        if temp_dir.exists():
            shutil.rmtree(temp_dir)


def main():
    """Run orchestration tests for all adapters."""
    print("\n" + "="*70)
    print("SIMULATION ADAPTER ORCHESTRATION TEST SUITE")
    print("="*70)
    print("\nThis test validates orchestration features:")
    print("  - Health checks")
    print("  - Status reporting")
    print("  - Metadata APIs")
    print("  - JSON serialization")
    print("\n" + "="*70)
    
    results = []
    
    # Test OpenFOAM adapter
    results.append(("OpenFOAM", test_adapter_orchestration(
        OpenFOAMAdapter, 
        "OpenFOAM",
        image_name="openfoam-toolbox"
    )))
    
    # Test LAMMPS adapter
    results.append(("LAMMPS", test_adapter_orchestration(
        LAMMPSAdapter,
        "LAMMPS",
        image_name="keystone/lammps:latest"
    )))
    
    # Test FEniCSx adapter
    results.append(("FEniCSx", test_adapter_orchestration(
        FEniCSxAdapter,
        "FEniCSx",
        image_name="fenicsx-toolbox"
    )))
    
    # Print summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{name:15s} {status}")
    
    print(f"\nTotal: {passed}/{total} adapters passed orchestration tests")
    
    if passed == total:
        print("\n✓ ALL ORCHESTRATION TESTS PASSED!")
        print("="*70 + "\n")
        return 0
    else:
        print("\n✗ SOME ORCHESTRATION TESTS FAILED!")
        print("="*70 + "\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
