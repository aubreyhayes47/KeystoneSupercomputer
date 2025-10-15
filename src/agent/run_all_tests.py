#!/usr/bin/env python3
"""
Test runner for all workflow orchestration tests.

Runs unit tests and optionally integration tests.
"""

import sys
import subprocess
from pathlib import Path


def run_test(test_file: str, description: str) -> bool:
    """
    Run a test file and return success status.
    
    Args:
        test_file: Path to test file
        description: Description of the test
        
    Returns:
        True if test passed, False otherwise
    """
    print("\n" + "=" * 70)
    print(f"Running: {description}")
    print("=" * 70)
    print(f"File: {test_file}")
    print()
    
    result = subprocess.run(
        [sys.executable, test_file],
        capture_output=False,
        text=True
    )
    
    success = result.returncode == 0
    
    if success:
        print(f"\n✓ {description} PASSED")
    else:
        print(f"\n✗ {description} FAILED")
    
    return success


def main():
    """Main test runner."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Run workflow orchestration tests"
    )
    parser.add_argument(
        "--integration",
        action="store_true",
        help="Run integration tests (requires Docker Compose services)"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run all tests including integration tests"
    )
    
    args = parser.parse_args()
    
    # Get test directory
    test_dir = Path(__file__).parent
    
    print("\n" + "=" * 70)
    print("WORKFLOW ORCHESTRATION TEST SUITE")
    print("=" * 70)
    print()
    
    results = []
    
    # Always run unit tests
    print("Running Unit Tests...")
    print("-" * 70)
    
    unit_tests = [
        (test_dir / "test_workflow_orchestration.py", "Workflow Orchestration Unit Tests"),
        (test_dir / "test_task_pipeline.py", "Task Pipeline Unit Tests"),
        (test_dir / "test_cli.py", "CLI Unit Tests"),
        (test_dir.parent / "test_job_monitor.py", "Job Monitor Unit Tests"),
    ]
    
    for test_file, description in unit_tests:
        if test_file.exists():
            results.append((description, run_test(str(test_file), description)))
        else:
            print(f"\n⚠ Warning: Test file not found: {test_file}")
            results.append((description, False))
    
    # Run integration tests if requested
    if args.integration or args.all:
        print("\n" + "=" * 70)
        print("Running Integration Tests...")
        print("-" * 70)
        print()
        print("NOTE: Integration tests require Docker Compose services:")
        print("  docker compose up -d redis celery-worker")
        print()
        
        integration_tests = [
            (test_dir / "test_agentic_workflow_integration.py", "Agentic Workflow Integration Tests"),
        ]
        
        for test_file, description in integration_tests:
            if test_file.exists():
                results.append((description, run_test(str(test_file), description)))
            else:
                print(f"\n⚠ Warning: Test file not found: {test_file}")
                results.append((description, False))
    
    # Print summary
    print("\n" + "=" * 70)
    print("TEST SUITE SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for description, success in results:
        status = "✓ PASSED" if success else "✗ FAILED"
        print(f"{description:45s} {status}")
    
    print("-" * 70)
    print(f"Total: {passed}/{total} test suites passed")
    print("=" * 70)
    
    if passed == total:
        print("\n✓ ALL TESTS PASSED!\n")
        return 0
    else:
        print(f"\n✗ {total - passed} TEST SUITE(S) FAILED!\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
