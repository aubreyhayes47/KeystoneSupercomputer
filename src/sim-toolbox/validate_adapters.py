#!/usr/bin/env python3
"""
Adapter Validation Script
==========================

Simple validation tests for simulation tool adapters.
Tests basic functionality without requiring Docker images to be built.
"""

import sys
from pathlib import Path


def test_fenicsx_adapter():
    """Test FEniCSx adapter basic functionality."""
    print("Testing FEniCSx Adapter...")
    
    try:
        # Import adapter
        sys.path.insert(0, str(Path(__file__).parent / "fenicsx"))
        from fenicsx_adapter import FEniCSxAdapter
        
        # Test initialization
        adapter = FEniCSxAdapter(
            image_name="test-fenicsx",
            output_dir="/tmp/test_output"
        )
        
        # Test attribute access
        assert adapter.image_name == "test-fenicsx"
        assert adapter.output_dir.name == "test_output"
        
        # Test image check (should return False for non-existent image)
        available = adapter.check_image_available()
        print(f"  ✓ Image check: {available}")
        
        # Test last result before running
        assert adapter.get_last_result() is None
        print(f"  ✓ Initial state check passed")
        
        print("  ✓ FEniCSx adapter validation passed\n")
        return True
        
    except Exception as e:
        print(f"  ✗ FEniCSx adapter validation failed: {e}\n")
        return False


def test_lammps_adapter():
    """Test LAMMPS adapter basic functionality."""
    print("Testing LAMMPS Adapter...")
    
    try:
        # Import adapter
        sys.path.insert(0, str(Path(__file__).parent / "lammps"))
        from lammps_adapter import LAMMPSAdapter
        
        # Test initialization
        adapter = LAMMPSAdapter(
            image_name="test-lammps",
            output_dir="/tmp/test_output"
        )
        
        # Test attribute access
        assert adapter.image_name == "test-lammps"
        assert adapter.output_dir.name == "test_output"
        
        # Test image check
        available = adapter.check_image_available()
        print(f"  ✓ Image check: {available}")
        
        # Test last result
        assert adapter.get_last_result() is None
        print(f"  ✓ Initial state check passed")
        
        print("  ✓ LAMMPS adapter validation passed\n")
        return True
        
    except Exception as e:
        print(f"  ✗ LAMMPS adapter validation failed: {e}\n")
        return False


def test_openfoam_adapter():
    """Test OpenFOAM adapter basic functionality."""
    print("Testing OpenFOAM Adapter...")
    
    try:
        # Import adapter
        sys.path.insert(0, str(Path(__file__).parent / "openfoam"))
        from openfoam_adapter import OpenFOAMAdapter
        
        # Test initialization
        adapter = OpenFOAMAdapter(
            image_name="test-openfoam",
            output_dir="/tmp/test_output"
        )
        
        # Test attribute access
        assert adapter.image_name == "test-openfoam"
        assert adapter.output_dir.name == "test_output"
        
        # Test image check
        available = adapter.check_image_available()
        print(f"  ✓ Image check: {available}")
        
        # Test last result
        assert adapter.get_last_result() is None
        print(f"  ✓ Initial state check passed")
        
        print("  ✓ OpenFOAM adapter validation passed\n")
        return True
        
    except Exception as e:
        print(f"  ✗ OpenFOAM adapter validation failed: {e}\n")
        return False


def test_api_consistency():
    """Test that all adapters have consistent APIs."""
    print("Testing API Consistency...")
    
    try:
        # Import all adapters
        sys.path.insert(0, str(Path(__file__).parent / "fenicsx"))
        sys.path.insert(0, str(Path(__file__).parent / "lammps"))
        sys.path.insert(0, str(Path(__file__).parent / "openfoam"))
        
        from fenicsx_adapter import FEniCSxAdapter
        from lammps_adapter import LAMMPSAdapter
        from openfoam_adapter import OpenFOAMAdapter
        
        adapters = [
            FEniCSxAdapter(output_dir="/tmp/test1"),
            LAMMPSAdapter(output_dir="/tmp/test2"),
            OpenFOAMAdapter(output_dir="/tmp/test3")
        ]
        
        # Check that all adapters have required methods
        required_methods = [
            'check_image_available',
            'build_image',
            'get_last_result',
            'save_result_json',
            'run_simulation'
        ]
        
        for adapter in adapters:
            adapter_name = adapter.__class__.__name__
            for method in required_methods:
                if not hasattr(adapter, method):
                    raise AssertionError(f"{adapter_name} missing method: {method}")
                print(f"  ✓ {adapter_name}.{method} exists")
        
        print("  ✓ API consistency validation passed\n")
        return True
        
    except Exception as e:
        print(f"  ✗ API consistency validation failed: {e}\n")
        return False


def main():
    """Run all validation tests."""
    print("="*60)
    print("Simulation Tool Adapter Validation")
    print("="*60 + "\n")
    
    results = []
    
    # Run individual adapter tests
    results.append(("FEniCSx", test_fenicsx_adapter()))
    results.append(("LAMMPS", test_lammps_adapter()))
    results.append(("OpenFOAM", test_openfoam_adapter()))
    results.append(("API Consistency", test_api_consistency()))
    
    # Print summary
    print("="*60)
    print("Validation Summary")
    print("="*60)
    
    for name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{name}: {status}")
    
    print("="*60)
    
    # Return exit code
    all_passed = all(result[1] for result in results)
    
    if all_passed:
        print("\n✓ All validation tests passed!")
        return 0
    else:
        print("\n✗ Some validation tests failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
