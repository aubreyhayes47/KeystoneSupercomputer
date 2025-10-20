#!/usr/bin/env python3
"""
Verification Script for Provenance Integration
===============================================

This script verifies that provenance logging is properly integrated
into the Celery task system and LangGraph workflows.
"""

import sys
import json
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent))

from provenance_logger import get_provenance_logger


def verify_celery_integration():
    """Verify that celery_app.py imports and uses provenance_logger."""
    print("\n" + "=" * 70)
    print("Verifying Celery Integration")
    print("=" * 70)
    
    celery_file = Path(__file__).parent / "celery_app.py"
    
    print("\n1. Checking imports in celery_app.py...")
    with open(celery_file, 'r') as f:
        content = f.read()
    
    if "from provenance_logger import get_provenance_logger" in content:
        print("   ✓ Provenance logger import found")
    else:
        print("   ✗ Missing provenance logger import")
        return False
    
    print("\n2. Checking provenance workflow start...")
    if "prov_logger.start_workflow" in content:
        print("   ✓ Workflow start call found")
    else:
        print("   ✗ Missing workflow start call")
        return False
    
    print("\n3. Checking tool call recording...")
    if "prov_logger.record_tool_call" in content:
        print("   ✓ Tool call recording found")
    else:
        print("   ✗ Missing tool call recording")
        return False
    
    print("\n4. Checking provenance finalization...")
    count = content.count("prov_logger.finalize_workflow")
    if count >= 3:  # Should be called in success, timeout, and error paths
        print(f"   ✓ Workflow finalization found ({count} paths)")
    else:
        print(f"   ✗ Insufficient finalization calls (found {count}, expected 3)")
        return False
    
    print("\n5. Checking provenance file in results...")
    if "'provenance_file'" in content or '"provenance_file"' in content:
        print("   ✓ Provenance file added to results")
    else:
        print("   ✗ Missing provenance file in results")
        return False
    
    print("\n✓ Celery integration verified successfully!")
    return True


def verify_langgraph_integration():
    """Verify that conductor_performer_graph.py integrates provenance."""
    print("\n" + "=" * 70)
    print("Verifying LangGraph Integration")
    print("=" * 70)
    
    graph_file = Path(__file__).parent / "agent" / "conductor_performer_graph.py"
    
    print("\n1. Checking imports in conductor_performer_graph.py...")
    with open(graph_file, 'r') as f:
        content = f.read()
    
    if "from provenance_logger import get_provenance_logger" in content:
        print("   ✓ Provenance logger import found")
    else:
        print("   ✗ Missing provenance logger import")
        return False
    
    print("\n2. Checking execute_workflow provenance tracking...")
    if "prov_logger.start_workflow" in content:
        print("   ✓ Workflow start in execute_workflow")
    else:
        print("   ✗ Missing workflow start")
        return False
    
    print("\n3. Checking agent action recording...")
    if "prov_logger.record_agent_action" in content:
        print("   ✓ Agent action recording found")
    else:
        print("   ✗ Missing agent action recording")
        return False
    
    print("\n4. Checking error handling...")
    if "except Exception" in content and "finalize_workflow" in content:
        print("   ✓ Error handling with provenance finalization")
    else:
        print("   ✗ Missing error handling")
        return False
    
    print("\n5. Checking provenance file in results...")
    if "'provenance_file'" in content or '"provenance_file"' in content:
        print("   ✓ Provenance file added to results")
    else:
        print("   ✗ Missing provenance file in results")
        return False
    
    print("\n✓ LangGraph integration verified successfully!")
    return True


def verify_provenance_storage():
    """Verify provenance directory and file structure."""
    print("\n" + "=" * 70)
    print("Verifying Provenance Storage")
    print("=" * 70)
    
    provenance_dir = Path("/tmp/keystone_provenance")
    
    print("\n1. Checking provenance directory...")
    if provenance_dir.exists():
        print(f"   ✓ Directory exists: {provenance_dir}")
    else:
        print(f"   ℹ Directory will be created on first use: {provenance_dir}")
    
    print("\n2. Checking for existing provenance files...")
    if provenance_dir.exists():
        prov_files = list(provenance_dir.glob("provenance_*.json"))
        if prov_files:
            print(f"   ✓ Found {len(prov_files)} provenance files")
            
            # Verify one file structure
            sample_file = prov_files[0]
            print(f"\n3. Validating sample file: {sample_file.name}")
            
            try:
                with open(sample_file, 'r') as f:
                    prov = json.load(f)
                
                required_fields = [
                    "provenance_version",
                    "workflow_id",
                    "created_at",
                    "status",
                    "user_prompt",
                    "workflow_plan",
                    "tool_calls",
                    "software_versions",
                    "environment",
                    "random_seeds",
                    "execution_timeline"
                ]
                
                missing_fields = []
                for field in required_fields:
                    if field not in prov:
                        missing_fields.append(field)
                
                if not missing_fields:
                    print("   ✓ All required fields present")
                else:
                    print(f"   ✗ Missing fields: {', '.join(missing_fields)}")
                    return False
                
                print(f"   ✓ Provenance version: {prov.get('provenance_version')}")
                print(f"   ✓ Status: {prov.get('status')}")
                print(f"   ✓ Tool calls: {len(prov.get('tool_calls', []))}")
                
            except json.JSONDecodeError:
                print(f"   ✗ Invalid JSON in {sample_file.name}")
                return False
            except Exception as e:
                print(f"   ✗ Error reading file: {e}")
                return False
        else:
            print("   ℹ No provenance files found (expected for fresh install)")
    else:
        print("   ℹ Directory not yet created (expected for fresh install)")
    
    print("\n✓ Storage verification completed!")
    return True


def verify_api_availability():
    """Verify that provenance API is accessible."""
    print("\n" + "=" * 70)
    print("Verifying Provenance API")
    print("=" * 70)
    
    print("\n1. Testing global logger access...")
    try:
        logger = get_provenance_logger()
        print("   ✓ Global logger accessible")
    except Exception as e:
        print(f"   ✗ Error accessing logger: {e}")
        return False
    
    print("\n2. Testing API methods...")
    required_methods = [
        'start_workflow',
        'record_tool_call',
        'record_agent_action',
        'add_input_file',
        'add_output_file',
        'finalize_workflow',
        'get_provenance',
        'list_workflows'
    ]
    
    for method in required_methods:
        if hasattr(logger, method) and callable(getattr(logger, method)):
            print(f"   ✓ {method}")
        else:
            print(f"   ✗ Missing method: {method}")
            return False
    
    print("\n✓ API verification completed!")
    return True


def verify_documentation():
    """Verify that documentation files exist."""
    print("\n" + "=" * 70)
    print("Verifying Documentation")
    print("=" * 70)
    
    repo_root = Path(__file__).parent.parent
    
    print("\n1. Checking PROVENANCE_SCHEMA.md...")
    schema_doc = repo_root / "PROVENANCE_SCHEMA.md"
    if schema_doc.exists():
        size_kb = schema_doc.stat().st_size / 1024
        print(f"   ✓ Found ({size_kb:.1f} KB)")
        
        # Check for key sections
        with open(schema_doc, 'r') as f:
            content = f.read()
        
        key_sections = [
            "## Overview",
            "## Provenance Schema Version",
            "### Field Definitions",
            "## Usage Examples",
            "## API Reference",
            "## Best Practices"
        ]
        
        for section in key_sections:
            if section in content:
                print(f"   ✓ Section: {section}")
            else:
                print(f"   ✗ Missing section: {section}")
    else:
        print("   ✗ PROVENANCE_SCHEMA.md not found")
        return False
    
    print("\n2. Checking example scripts...")
    example_script = Path(__file__).parent / "example_provenance.py"
    if example_script.exists():
        print(f"   ✓ example_provenance.py found")
    else:
        print("   ✗ example_provenance.py not found")
        return False
    
    print("\n3. Checking test files...")
    test_file = Path(__file__).parent / "test_provenance_logger.py"
    if test_file.exists():
        print(f"   ✓ test_provenance_logger.py found")
    else:
        print("   ✗ test_provenance_logger.py not found")
        return False
    
    print("\n4. Checking README.md updates...")
    readme = repo_root / "README.md"
    with open(readme, 'r') as f:
        readme_content = f.read()
    
    if "PROVENANCE_SCHEMA.md" in readme_content:
        print("   ✓ Provenance documentation linked in README")
    else:
        print("   ✗ Missing provenance link in README")
        return False
    
    if "Provenance Logging and Reproducibility" in readme_content:
        print("   ✓ Provenance section in README")
    else:
        print("   ✗ Missing provenance section in README")
        return False
    
    print("\n✓ Documentation verification completed!")
    return True


def main():
    """Run all verification checks."""
    print("\n" + "=" * 70)
    print("PROVENANCE INTEGRATION VERIFICATION")
    print("=" * 70)
    print("\nThis script verifies that provenance logging is properly")
    print("integrated into Keystone Supercomputer.")
    
    results = {
        "Celery Integration": verify_celery_integration(),
        "LangGraph Integration": verify_langgraph_integration(),
        "Provenance Storage": verify_provenance_storage(),
        "API Availability": verify_api_availability(),
        "Documentation": verify_documentation()
    }
    
    # Summary
    print("\n" + "=" * 70)
    print("VERIFICATION SUMMARY")
    print("=" * 70)
    
    for check, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {check}")
    
    all_passed = all(results.values())
    
    if all_passed:
        print("\n" + "=" * 70)
        print("✓ ALL CHECKS PASSED!")
        print("=" * 70)
        print("\nProvenance logging is properly integrated and ready to use.")
        print("\nNext steps:")
        print("  1. Run a simulation to generate provenance files")
        print("  2. Examine provenance.json in /tmp/keystone_provenance/")
        print("  3. Use provenance records for reproducibility")
    else:
        print("\n" + "=" * 70)
        print("✗ SOME CHECKS FAILED")
        print("=" * 70)
        print("\nPlease review the failed checks above.")
    
    print()
    return 0 if all_passed else 1


if __name__ == '__main__':
    sys.exit(main())
