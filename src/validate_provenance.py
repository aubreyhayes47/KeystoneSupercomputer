#!/usr/bin/env python3
"""
Provenance Validation Command-Line Tool
========================================

This tool validates provenance JSON files for completeness and correctness.
It can validate individual files or batch-validate all provenance files in a directory.

Usage:
    # Validate a single file
    python3 validate_provenance.py provenance_abc123.json
    
    # Validate all files in a directory
    python3 validate_provenance.py /tmp/keystone_provenance/
    
    # Validate with non-strict mode (warnings don't fail validation)
    python3 validate_provenance.py --non-strict provenance_abc123.json
    
    # Show detailed output
    python3 validate_provenance.py --verbose provenance_abc123.json
"""

import sys
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any

# Add src directory to path if running as standalone script
if __name__ == '__main__':
    sys.path.insert(0, str(Path(__file__).parent))

from provenance_logger import validate_provenance_file


def format_validation_result(result: Dict[str, Any], verbose: bool = False) -> str:
    """
    Format validation result for display.
    
    Args:
        result: Validation result dictionary
        verbose: If True, show all details
        
    Returns:
        Formatted string
    """
    lines = []
    
    # Header
    filepath = result.get("filepath", "unknown")
    lines.append(f"\nFile: {filepath}")
    lines.append("=" * 70)
    
    # Status
    if result["valid"]:
        lines.append("✓ VALID")
    else:
        lines.append("✗ INVALID")
    
    # Version
    version = result.get("version", "unknown")
    lines.append(f"Schema version: {version}")
    
    # Errors
    if result["errors"]:
        lines.append(f"\nErrors ({len(result['errors'])}):")
        for error in result["errors"]:
            lines.append(f"  ✗ {error}")
    
    # Warnings
    if result["warnings"]:
        lines.append(f"\nWarnings ({len(result['warnings'])}):")
        if verbose:
            for warning in result["warnings"]:
                lines.append(f"  ⚠ {warning}")
        else:
            lines.append(f"  ⚠ {len(result['warnings'])} warning(s) (use --verbose to see details)")
    
    # Summary for valid files
    if result["valid"] and not verbose:
        lines.append("\n✓ All required fields present and valid")
    
    return "\n".join(lines)


def validate_directory(
    directory: Path,
    strict: bool = True,
    verbose: bool = False
) -> Dict[str, Any]:
    """
    Validate all provenance files in a directory.
    
    Args:
        directory: Directory containing provenance files
        strict: If True, treat warnings as errors
        verbose: If True, show detailed output
        
    Returns:
        Summary dictionary with validation results
    """
    if not directory.is_dir():
        print(f"Error: {directory} is not a directory")
        return {"valid_count": 0, "invalid_count": 0, "total": 0}
    
    # Find all provenance JSON files
    provenance_files = list(directory.glob("provenance_*.json"))
    
    if not provenance_files:
        print(f"No provenance files found in {directory}")
        return {"valid_count": 0, "invalid_count": 0, "total": 0}
    
    print(f"\nValidating {len(provenance_files)} provenance file(s)...")
    print("=" * 70)
    
    valid_count = 0
    invalid_count = 0
    results = []
    
    for filepath in sorted(provenance_files):
        result = validate_provenance_file(filepath, strict=strict)
        results.append(result)
        
        if result["valid"]:
            valid_count += 1
            if verbose:
                print(format_validation_result(result, verbose=verbose))
        else:
            invalid_count += 1
            print(format_validation_result(result, verbose=verbose))
    
    # Summary
    print("\n" + "=" * 70)
    print("VALIDATION SUMMARY")
    print("=" * 70)
    print(f"Total files:   {len(provenance_files)}")
    print(f"Valid:         {valid_count}")
    print(f"Invalid:       {invalid_count}")
    
    if invalid_count > 0:
        print(f"\n⚠ {invalid_count} file(s) failed validation")
        return {"valid_count": valid_count, "invalid_count": invalid_count, "total": len(provenance_files), "success": False}
    else:
        print("\n✓ All files passed validation!")
        return {"valid_count": valid_count, "invalid_count": invalid_count, "total": len(provenance_files), "success": True}


def validate_file(
    filepath: Path,
    strict: bool = True,
    verbose: bool = False
) -> Dict[str, Any]:
    """
    Validate a single provenance file.
    
    Args:
        filepath: Path to provenance file
        strict: If True, treat warnings as errors
        verbose: If True, show detailed output
        
    Returns:
        Validation result dictionary
    """
    result = validate_provenance_file(filepath, strict=strict)
    print(format_validation_result(result, verbose=verbose))
    return result


def main():
    """Main entry point for command-line tool."""
    parser = argparse.ArgumentParser(
        description="Validate provenance JSON files for completeness and correctness",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Validate a single file
  %(prog)s provenance_abc123.json
  
  # Validate all files in a directory
  %(prog)s /tmp/keystone_provenance/
  
  # Non-strict mode (warnings don't fail validation)
  %(prog)s --non-strict provenance_abc123.json
  
  # Show detailed output
  %(prog)s --verbose provenance_abc123.json
  
  # Combine options
  %(prog)s --non-strict --verbose /tmp/keystone_provenance/
        """
    )
    
    parser.add_argument(
        "path",
        help="Path to provenance file or directory containing provenance files"
    )
    
    parser.add_argument(
        "--non-strict",
        action="store_true",
        help="Non-strict mode: warnings don't fail validation"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed output including all warnings"
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version="Provenance Validation Tool 1.0.0"
    )
    
    args = parser.parse_args()
    
    # Convert path to Path object
    path = Path(args.path)
    strict = not args.non_strict
    
    # Check if path exists
    if not path.exists():
        print(f"Error: Path does not exist: {path}")
        sys.exit(1)
    
    # Validate file or directory
    try:
        if path.is_dir():
            summary = validate_directory(path, strict=strict, verbose=args.verbose)
            sys.exit(0 if summary.get("success", False) else 1)
        else:
            result = validate_file(path, strict=strict, verbose=args.verbose)
            sys.exit(0 if result["valid"] else 1)
    except KeyboardInterrupt:
        print("\n\nValidation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nError during validation: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
