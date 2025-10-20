#!/usr/bin/env python3
"""
Benchmark Registry Manager for sim-toolbox
===========================================

This module provides functionality to manage, validate, and execute benchmark
cases for all supported simulators in sim-toolbox (FEniCSx, LAMMPS, OpenFOAM).

Features:
- Load and validate benchmark definitions against JSON schema
- List available benchmarks by simulator, category, or difficulty
- Execute benchmarks and validate results
- Add new benchmarks to the registry
- Generate benchmark reports

Usage:
    from benchmark_registry import BenchmarkRegistry
    
    registry = BenchmarkRegistry()
    benchmarks = registry.list_benchmarks(simulator="fenicsx")
    result = registry.run_benchmark("fenicsx-poisson-2d-basic")
"""

import json
import hashlib
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import jsonschema


class BenchmarkRegistry:
    """
    Manages the benchmark registry for simulation tools.
    
    Provides methods to list, validate, execute, and manage benchmark cases
    for FEniCSx, LAMMPS, and OpenFOAM simulators.
    """
    
    def __init__(self, registry_dir: Optional[str] = None):
        """
        Initialize the benchmark registry.
        
        Args:
            registry_dir: Path to benchmark registry directory 
                         (default: src/sim-toolbox/benchmarks)
        """
        if registry_dir:
            self.registry_dir = Path(registry_dir)
        else:
            # Default to benchmarks directory relative to this file
            self.registry_dir = Path(__file__).parent
        
        self.schema_path = self.registry_dir / "benchmark_schema.json"
        self.schema = self._load_schema()
        self._benchmark_cache = {}
    
    def _load_schema(self) -> Dict[str, Any]:
        """Load the benchmark JSON schema."""
        if not self.schema_path.exists():
            raise FileNotFoundError(f"Schema not found: {self.schema_path}")
        
        with open(self.schema_path, 'r') as f:
            return json.load(f)
    
    def _compute_checksum(self, file_path: Path) -> str:
        """Compute SHA256 checksum of a file."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def _find_benchmark_files(self) -> List[Path]:
        """Find all benchmark JSON files in the registry."""
        benchmark_files = []
        for simulator_dir in ['fenicsx', 'lammps', 'openfoam']:
            sim_path = self.registry_dir / simulator_dir
            if sim_path.exists():
                benchmark_files.extend(sim_path.glob("*.json"))
        return benchmark_files
    
    def load_benchmark(self, benchmark_id: str) -> Dict[str, Any]:
        """
        Load a benchmark definition by ID.
        
        Args:
            benchmark_id: Unique identifier of the benchmark
            
        Returns:
            Benchmark definition dictionary
            
        Raises:
            FileNotFoundError: If benchmark is not found
            jsonschema.ValidationError: If benchmark is invalid
        """
        # Check cache first
        if benchmark_id in self._benchmark_cache:
            return self._benchmark_cache[benchmark_id]
        
        # Search for benchmark file
        for bench_file in self._find_benchmark_files():
            with open(bench_file, 'r') as f:
                benchmark = json.load(f)
                if benchmark.get('id') == benchmark_id:
                    # Validate against schema
                    jsonschema.validate(instance=benchmark, schema=self.schema)
                    self._benchmark_cache[benchmark_id] = benchmark
                    return benchmark
        
        raise FileNotFoundError(f"Benchmark not found: {benchmark_id}")
    
    def list_benchmarks(
        self,
        simulator: Optional[str] = None,
        category: Optional[str] = None,
        difficulty: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        List benchmarks matching specified criteria.
        
        Args:
            simulator: Filter by simulator (fenicsx, lammps, openfoam)
            category: Filter by category
            difficulty: Filter by difficulty level
            tags: Filter by tags (any matching tag)
            
        Returns:
            List of benchmark summaries
        """
        benchmarks = []
        
        for bench_file in self._find_benchmark_files():
            try:
                with open(bench_file, 'r') as f:
                    benchmark = json.load(f)
                
                # Apply filters
                if simulator and benchmark.get('simulator') != simulator:
                    continue
                if category and benchmark.get('category') != category:
                    continue
                if difficulty and benchmark.get('difficulty') != difficulty:
                    continue
                if tags:
                    bench_tags = set(benchmark.get('tags', []))
                    if not bench_tags.intersection(set(tags)):
                        continue
                
                # Add summary info
                benchmarks.append({
                    'id': benchmark['id'],
                    'name': benchmark['name'],
                    'simulator': benchmark['simulator'],
                    'category': benchmark['category'],
                    'difficulty': benchmark['difficulty'],
                    'description': benchmark['description'][:100] + '...' 
                        if len(benchmark['description']) > 100 else benchmark['description'],
                    'file': str(bench_file.relative_to(self.registry_dir))
                })
            except (json.JSONDecodeError, KeyError) as e:
                print(f"Warning: Error loading {bench_file}: {e}")
                continue
        
        return benchmarks
    
    def validate_benchmark(self, benchmark_id: str) -> Dict[str, Any]:
        """
        Validate a benchmark definition.
        
        Args:
            benchmark_id: Benchmark ID to validate
            
        Returns:
            Validation result with status and any errors
        """
        result = {
            'benchmark_id': benchmark_id,
            'valid': False,
            'errors': [],
            'warnings': []
        }
        
        try:
            benchmark = self.load_benchmark(benchmark_id)
            
            # Schema validation is done in load_benchmark
            result['valid'] = True
            
            # Additional validation checks
            # Check if input files exist
            for input_file in benchmark.get('input_files', []):
                file_path = self.registry_dir / input_file.get('path', '')
                if not file_path.exists():
                    result['warnings'].append(
                        f"Input file not found: {input_file['filename']} at {file_path}"
                    )
            
            # Check if validation script exists (if specified)
            validation_script = benchmark.get('validation_criteria', {}).get('validation_script')
            if validation_script:
                script_path = self.registry_dir / benchmark['simulator'] / validation_script
                if not script_path.exists():
                    result['warnings'].append(
                        f"Validation script not found: {validation_script}"
                    )
        
        except FileNotFoundError as e:
            result['errors'].append(str(e))
        except jsonschema.ValidationError as e:
            result['errors'].append(f"Schema validation error: {e.message}")
        except Exception as e:
            result['errors'].append(f"Unexpected error: {str(e)}")
        
        return result
    
    def validate_all_benchmarks(self) -> Dict[str, Any]:
        """
        Validate all benchmarks in the registry.
        
        Returns:
            Summary of validation results
        """
        results = {
            'total': 0,
            'valid': 0,
            'invalid': 0,
            'benchmarks': []
        }
        
        for bench_file in self._find_benchmark_files():
            try:
                with open(bench_file, 'r') as f:
                    benchmark = json.load(f)
                    benchmark_id = benchmark.get('id', 'unknown')
                
                results['total'] += 1
                validation = self.validate_benchmark(benchmark_id)
                
                if validation['valid']:
                    results['valid'] += 1
                else:
                    results['invalid'] += 1
                
                results['benchmarks'].append(validation)
            except Exception as e:
                results['total'] += 1
                results['invalid'] += 1
                results['benchmarks'].append({
                    'file': str(bench_file),
                    'valid': False,
                    'errors': [str(e)]
                })
        
        return results
    
    def get_benchmark_info(self, benchmark_id: str) -> Dict[str, Any]:
        """
        Get detailed information about a benchmark.
        
        Args:
            benchmark_id: Benchmark ID
            
        Returns:
            Complete benchmark definition
        """
        return self.load_benchmark(benchmark_id)
    
    def add_benchmark(
        self,
        benchmark_def: Dict[str, Any],
        validate: bool = True
    ) -> Dict[str, Any]:
        """
        Add a new benchmark to the registry.
        
        Args:
            benchmark_def: Benchmark definition dictionary
            validate: Whether to validate before adding (default: True)
            
        Returns:
            Result with status and file path
        """
        result = {
            'success': False,
            'benchmark_id': benchmark_def.get('id', 'unknown'),
            'file_path': None,
            'errors': []
        }
        
        try:
            # Validate against schema
            if validate:
                jsonschema.validate(instance=benchmark_def, schema=self.schema)
            
            # Determine file path
            simulator = benchmark_def['simulator']
            benchmark_id = benchmark_def['id']
            file_path = self.registry_dir / simulator / f"{benchmark_id.replace(f'{simulator}-', '')}.json"
            
            # Check if already exists
            if file_path.exists():
                result['errors'].append(f"Benchmark already exists: {file_path}")
                return result
            
            # Write benchmark file
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, 'w') as f:
                json.dump(benchmark_def, f, indent=2)
            
            result['success'] = True
            result['file_path'] = str(file_path)
            
        except jsonschema.ValidationError as e:
            result['errors'].append(f"Validation error: {e.message}")
        except Exception as e:
            result['errors'].append(f"Error adding benchmark: {str(e)}")
        
        return result
    
    def generate_report(self, output_file: Optional[str] = None) -> str:
        """
        Generate a markdown report of all benchmarks.
        
        Args:
            output_file: Optional file path to save the report
            
        Returns:
            Markdown report as string
        """
        benchmarks = self.list_benchmarks()
        
        # Group by simulator
        by_simulator = {}
        for bench in benchmarks:
            sim = bench['simulator']
            if sim not in by_simulator:
                by_simulator[sim] = []
            by_simulator[sim].append(bench)
        
        # Generate report
        lines = [
            "# Benchmark Registry Report",
            "",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            f"**Total Benchmarks:** {len(benchmarks)}",
            ""
        ]
        
        for simulator, benches in sorted(by_simulator.items()):
            lines.append(f"## {simulator.upper()}")
            lines.append("")
            lines.append(f"**Count:** {len(benches)}")
            lines.append("")
            lines.append("| ID | Name | Category | Difficulty |")
            lines.append("|---|---|---|---|")
            
            for bench in sorted(benches, key=lambda x: x['id']):
                lines.append(
                    f"| `{bench['id']}` | {bench['name']} | "
                    f"{bench['category']} | {bench['difficulty']} |"
                )
            
            lines.append("")
        
        report = "\n".join(lines)
        
        if output_file:
            with open(output_file, 'w') as f:
                f.write(report)
        
        return report
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the benchmark registry.
        
        Returns:
            Dictionary with registry statistics
        """
        benchmarks = self.list_benchmarks()
        
        stats = {
            'total_benchmarks': len(benchmarks),
            'by_simulator': {},
            'by_category': {},
            'by_difficulty': {}
        }
        
        for bench in benchmarks:
            # Count by simulator
            sim = bench['simulator']
            stats['by_simulator'][sim] = stats['by_simulator'].get(sim, 0) + 1
            
            # Count by category
            cat = bench['category']
            stats['by_category'][cat] = stats['by_category'].get(cat, 0) + 1
            
            # Count by difficulty
            diff = bench['difficulty']
            stats['by_difficulty'][diff] = stats['by_difficulty'].get(diff, 0) + 1
        
        return stats


def main():
    """Command-line interface for benchmark registry."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Benchmark Registry Manager for sim-toolbox"
    )
    parser.add_argument(
        'command',
        choices=['list', 'info', 'validate', 'validate-all', 'report', 'stats'],
        help="Command to execute"
    )
    parser.add_argument(
        '--benchmark-id',
        help="Benchmark ID (required for info and validate commands)"
    )
    parser.add_argument(
        '--simulator',
        choices=['fenicsx', 'lammps', 'openfoam'],
        help="Filter by simulator"
    )
    parser.add_argument(
        '--category',
        help="Filter by category"
    )
    parser.add_argument(
        '--difficulty',
        choices=['beginner', 'intermediate', 'advanced', 'expert'],
        help="Filter by difficulty"
    )
    parser.add_argument(
        '--output',
        help="Output file path for report"
    )
    
    args = parser.parse_args()
    
    registry = BenchmarkRegistry()
    
    if args.command == 'list':
        benchmarks = registry.list_benchmarks(
            simulator=args.simulator,
            category=args.category,
            difficulty=args.difficulty
        )
        
        print(f"\nFound {len(benchmarks)} benchmark(s):\n")
        for bench in benchmarks:
            print(f"  {bench['id']}")
            print(f"    Name: {bench['name']}")
            print(f"    Simulator: {bench['simulator']}")
            print(f"    Category: {bench['category']}")
            print(f"    Difficulty: {bench['difficulty']}")
            print(f"    Description: {bench['description']}")
            print()
    
    elif args.command == 'info':
        if not args.benchmark_id:
            print("Error: --benchmark-id required for 'info' command")
            return 1
        
        benchmark = registry.get_benchmark_info(args.benchmark_id)
        print(json.dumps(benchmark, indent=2))
    
    elif args.command == 'validate':
        if not args.benchmark_id:
            print("Error: --benchmark-id required for 'validate' command")
            return 1
        
        result = registry.validate_benchmark(args.benchmark_id)
        print(f"\nValidation result for {result['benchmark_id']}:")
        print(f"  Valid: {result['valid']}")
        
        if result['errors']:
            print(f"  Errors:")
            for error in result['errors']:
                print(f"    - {error}")
        
        if result['warnings']:
            print(f"  Warnings:")
            for warning in result['warnings']:
                print(f"    - {warning}")
        
        return 0 if result['valid'] else 1
    
    elif args.command == 'validate-all':
        results = registry.validate_all_benchmarks()
        print(f"\nValidation Summary:")
        print(f"  Total: {results['total']}")
        print(f"  Valid: {results['valid']}")
        print(f"  Invalid: {results['invalid']}")
        
        if results['invalid'] > 0:
            print(f"\nInvalid benchmarks:")
            for bench in results['benchmarks']:
                if not bench['valid']:
                    print(f"  {bench.get('benchmark_id', bench.get('file', 'unknown'))}:")
                    for error in bench['errors']:
                        print(f"    - {error}")
        
        return 0 if results['invalid'] == 0 else 1
    
    elif args.command == 'report':
        report = registry.generate_report(output_file=args.output)
        if args.output:
            print(f"Report saved to: {args.output}")
        else:
            print(report)
    
    elif args.command == 'stats':
        stats = registry.get_statistics()
        print("\nBenchmark Registry Statistics:")
        print(f"  Total Benchmarks: {stats['total_benchmarks']}")
        
        print(f"\n  By Simulator:")
        for sim, count in sorted(stats['by_simulator'].items()):
            print(f"    {sim}: {count}")
        
        print(f"\n  By Category:")
        for cat, count in sorted(stats['by_category'].items()):
            print(f"    {cat}: {count}")
        
        print(f"\n  By Difficulty:")
        for diff, count in sorted(stats['by_difficulty'].items()):
            print(f"    {diff}: {count}")
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
