#!/usr/bin/env python3
"""
Example: Automated Post-Run Validation
=======================================

This example demonstrates the automated validation framework for
simulation workflows, including convergence checking, conservation
law validation, and regression comparison.
"""

import json
import tempfile
from pathlib import Path
import shutil

from validation_framework import ValidationFramework, load_validation_config
from validation_integration import get_validation_integration, validate_task


def example_1_basic_validation():
    """Example 1: Basic validation with convergence check."""
    print("\n" + "="*60)
    print("Example 1: Basic Validation with Convergence Check")
    print("="*60)
    
    # Create temporary output directory
    temp_dir = Path(tempfile.mkdtemp())
    
    try:
        # Simulate a converged run with log file
        log_file = temp_dir / 'simulation.log'
        with open(log_file, 'w') as f:
            f.write("Starting simulation...\n")
            f.write("Iteration 1: residual = 1.0e-1\n")
            f.write("Iteration 2: residual = 1.0e-2\n")
            f.write("Iteration 3: residual = 1.0e-4\n")
            f.write("Iteration 4: residual = 1.0e-7\n")
            f.write("Convergence achieved!\n")
        
        # Run validation
        validator = ValidationFramework()
        result = validator.validate_simulation(
            task_id='example-1',
            tool='fenicsx',
            output_dir=temp_dir
        )
        
        # Print results
        print(f"\nValidation Status: {'✓ PASSED' if result['validation_passed'] else '✗ FAILED'}")
        print(f"Total Checks: {result['total_checks']}")
        print(f"Passed: {result['checks_passed']}")
        print(f"Failed: {result['checks_failed']}")
        
        print("\nCheck Details:")
        for check in result['checks_performed']:
            status = '✓' if check['passed'] else '✗'
            print(f"  {status} {check['check_name']}")
            if 'converged' in check['details']:
                conv = check['details']
                print(f"    - Converged: {conv['converged']}")
                print(f"    - Iterations: {conv['iterations']}")
                print(f"    - Final residual: {conv['final_residual']:.2e}")
    
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def example_2_conservation_laws():
    """Example 2: Conservation law validation."""
    print("\n" + "="*60)
    print("Example 2: Conservation Law Validation")
    print("="*60)
    
    temp_dir = Path(tempfile.mkdtemp())
    
    try:
        # Create results file with conservation data
        results_file = temp_dir / 'results.json'
        results_data = {
            'mass': [100.0, 100.0, 100.0, 100.0],  # Perfectly conserved
            'momentum': [50.0, 49.99, 50.01, 50.0],  # Nearly conserved
            'energy': [1000.0, 1000.01, 999.99, 1000.0]  # Within tolerance
        }
        
        with open(results_file, 'w') as f:
            json.dump(results_data, f)
        
        # Run validation
        validator = ValidationFramework()
        result = validator.validate_simulation(
            task_id='example-2',
            tool='lammps',
            output_dir=temp_dir
        )
        
        print(f"\nValidation Status: {'✓ PASSED' if result['validation_passed'] else '✗ FAILED'}")
        
        print("\nConservation Law Checks:")
        for check in result['checks_performed']:
            if check['check_name'].startswith('conservation_'):
                law_type = check['check_name'].replace('conservation_', '')
                status = '✓' if check['passed'] else '✗'
                details = check['details']
                
                print(f"  {status} {law_type.upper()}")
                print(f"    - Initial: {details['initial_value']}")
                print(f"    - Final: {details['final_value']}")
                print(f"    - Change: {details['relative_change']:.2e}")
                print(f"    - Tolerance: {details['tolerance']:.2e}")
    
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def example_3_regression_comparison():
    """Example 3: Regression comparison against benchmark."""
    print("\n" + "="*60)
    print("Example 3: Regression Comparison Against Benchmark")
    print("="*60)
    
    temp_dir = Path(tempfile.mkdtemp())
    
    try:
        # Create output files
        (temp_dir / 'solution.dat').touch()
        
        # Create metrics file
        metrics_file = temp_dir / 'metrics.json'
        metrics_data = {
            'solution_max': 0.975,
            'solution_min': 0.0,
            'solution_mean': 0.042
        }
        
        with open(metrics_file, 'w') as f:
            json.dump(metrics_data, f)
        
        # Define benchmark (normally loaded from registry)
        benchmark_def = {
            'id': 'example-benchmark',
            'expected_results': {
                'output_files': [
                    {'filename': 'solution.dat', 'description': 'Solution file'}
                ],
                'metrics': {
                    'solution_max': {
                        'value': 0.975,
                        'tolerance': 0.01,
                        'unit': 'dimensionless'
                    },
                    'solution_mean': {
                        'value': 0.042,
                        'tolerance': 0.01,
                        'unit': 'dimensionless'
                    }
                }
            }
        }
        
        # Run regression comparison
        from validation_framework import RegressionComparator
        comparator = RegressionComparator()
        result = comparator.compare_against_benchmark(benchmark_def, temp_dir)
        
        print(f"\nRegression Comparison: {'✓ PASSED' if result['all_checks_passed'] else '✗ FAILED'}")
        
        print("\nFile Checks:")
        for check in result['file_checks']:
            status = '✓' if check['passed'] else '✗'
            print(f"  {status} {check['filename']}")
        
        print("\nMetric Checks:")
        for check in result['metric_checks']:
            status = '✓' if check['passed'] else '✗'
            details = check['details']
            print(f"  {status} {check['metric_name']}")
            print(f"    - Expected: {details['expected_value']}")
            print(f"    - Actual: {details['actual_value']}")
            if details['relative_error'] is not None:
                print(f"    - Error: {details['relative_error']:.2%}")
    
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def example_4_custom_validation():
    """Example 4: Custom validation checks."""
    print("\n" + "="*60)
    print("Example 4: Custom Validation Checks")
    print("="*60)
    
    temp_dir = Path(tempfile.mkdtemp())
    
    try:
        # Create custom metric file
        custom_file = temp_dir / 'custom_metric.txt'
        with open(custom_file, 'w') as f:
            f.write('0.95')
        
        # Define custom check
        def check_custom_metric(output_dir):
            """Custom validation check."""
            metric_file = output_dir / 'custom_metric.txt'
            
            if not metric_file.exists():
                return {'passed': False, 'reason': 'Metric file missing'}
            
            with open(metric_file, 'r') as f:
                value = float(f.read().strip())
            
            # Check against threshold
            passed = 0.9 <= value <= 1.1
            
            return {
                'passed': passed,
                'value': value,
                'threshold': [0.9, 1.1],
                'details': f'Custom metric value: {value}'
            }
        
        # Run validation with custom check
        validator = ValidationFramework()
        result = validator.validate_simulation(
            task_id='example-4',
            tool='custom',
            output_dir=temp_dir,
            custom_checks={'metric_check': check_custom_metric}
        )
        
        print(f"\nValidation Status: {'✓ PASSED' if result['validation_passed'] else '✗ FAILED'}")
        
        print("\nCustom Checks:")
        for check in result['checks_performed']:
            if 'custom_' in check['check_name']:
                status = '✓' if check['passed'] else '✗'
                print(f"  {status} {check['check_name']}")
                print(f"    - Details: {check['details']}")
    
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def example_5_validation_integration():
    """Example 5: Integration with provenance and monitoring."""
    print("\n" + "="*60)
    print("Example 5: Validation Integration with Provenance")
    print("="*60)
    
    temp_dir = Path(tempfile.mkdtemp())
    
    try:
        # Create simulation output
        log_file = temp_dir / 'simulation.log'
        with open(log_file, 'w') as f:
            f.write("Iteration 1: residual = 1.0e-1\n")
            f.write("Iteration 2: residual = 1.0e-7\n")
        
        # Use integrated validation
        result = validate_task(
            task_id='example-5',
            tool='fenicsx',
            output_dir=temp_dir,
            workflow_id='workflow-123'
        )
        
        print(f"\nValidation Status: {'✓ PASSED' if result['validation_passed'] else '✗ FAILED'}")
        print(f"\nValidation result saved to: /tmp/keystone_validation/results/validation_example-5.json")
        print("Provenance updated with validation events")
        
        # Query validation history
        integration = get_validation_integration()
        history = integration.get_validation_history(limit=5)
        
        print(f"\nRecent Validations: {len(history)}")
        for v in history[:3]:
            task_id = v['metadata']['task_id']
            passed = v['validation_passed']
            status = "✓" if passed else "✗"
            print(f"  {status} {task_id}")
    
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def example_6_validation_statistics():
    """Example 6: Validation statistics and monitoring."""
    print("\n" + "="*60)
    print("Example 6: Validation Statistics")
    print("="*60)
    
    integration = get_validation_integration()
    stats = integration.get_validation_statistics()
    
    print(f"\nTotal Validations: {stats['total_validations']}")
    print(f"Passed: {stats['passed']}")
    print(f"Failed: {stats['failed']}")
    print(f"Success Rate: {stats['success_rate']:.1%}")
    
    if stats['by_tool']:
        print("\nBy Tool:")
        for tool, tool_stats in stats['by_tool'].items():
            total = tool_stats['passed'] + tool_stats['failed']
            rate = tool_stats['passed'] / total if total > 0 else 0
            print(f"  {tool}: {tool_stats['passed']}/{total} ({rate:.1%})")
    
    if stats['common_failures']:
        print("\nCommon Failures:")
        for check_name, count in sorted(
            stats['common_failures'].items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]:
            print(f"  {check_name}: {count} times")


def example_7_alert_handlers():
    """Example 7: Custom alert handlers."""
    print("\n" + "="*60)
    print("Example 7: Custom Alert Handlers")
    print("="*60)
    
    temp_dir = Path(tempfile.mkdtemp())
    alerts_received = []
    
    try:
        # Define custom alert handler
        def custom_alert_handler(alert_data):
            """Custom alert handler that stores alerts."""
            alerts_received.append(alert_data)
            print(f"\n⚠️  ALERT: Task {alert_data['task_id']} validation failed!")
            print(f"   Failed checks: {len(alert_data['failed_checks'])}")
        
        # Register handler
        validator = ValidationFramework()
        validator.register_alert_handler(custom_alert_handler)
        
        # Create a scenario that will fail validation
        # (no log file, so convergence check will warn)
        result = validator.validate_simulation(
            task_id='example-7',
            tool='fenicsx',
            output_dir=temp_dir
        )
        
        print(f"\nValidation Status: {'✓ PASSED' if result['validation_passed'] else '✗ FAILED'}")
        print(f"Alerts received: {len(alerts_received)}")
    
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def main():
    """Run all examples."""
    print("\n" + "="*60)
    print("Automated Post-Run Validation Framework Examples")
    print("="*60)
    
    examples = [
        example_1_basic_validation,
        example_2_conservation_laws,
        example_3_regression_comparison,
        example_4_custom_validation,
        example_5_validation_integration,
        example_6_validation_statistics,
        example_7_alert_handlers
    ]
    
    for example in examples:
        try:
            example()
        except Exception as e:
            print(f"\n❌ Error in {example.__name__}: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*60)
    print("Examples Complete!")
    print("="*60)
    print("\nFor more information, see:")
    print("  - VALIDATION_GUIDE.md - Complete validation documentation")
    print("  - src/test_validation_framework.py - Comprehensive test suite")
    print("  - src/validation_config.json - Configuration options")
    print()


if __name__ == '__main__':
    main()
