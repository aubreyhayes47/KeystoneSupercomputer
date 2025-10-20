#!/usr/bin/env python3
"""
Test Suite for Validation Framework
====================================

Tests convergence checking, conservation law validation, regression comparison,
and integration with provenance/monitoring systems.
"""

import unittest
import tempfile
import json
from pathlib import Path
import shutil

from validation_framework import (
    ValidationFramework,
    ConvergenceChecker,
    ConservationLawValidator,
    RegressionComparator,
    ValidationResult,
    load_validation_config
)
from validation_integration import ValidationIntegration


class TestValidationResult(unittest.TestCase):
    """Test ValidationResult container class."""
    
    def test_add_check_passed(self):
        """Test adding a passed check."""
        result = ValidationResult()
        result.add_check('test_check', True, {'detail': 'passed'})
        
        self.assertEqual(len(result.checks_performed), 1)
        self.assertEqual(len(result.checks_passed), 1)
        self.assertEqual(len(result.checks_failed), 0)
        self.assertTrue(result.checks_performed[0]['passed'])
    
    def test_add_check_failed(self):
        """Test adding a failed check."""
        result = ValidationResult()
        result.add_check('test_check', False, {'detail': 'failed'})
        
        self.assertEqual(len(result.checks_performed), 1)
        self.assertEqual(len(result.checks_passed), 0)
        self.assertEqual(len(result.checks_failed), 1)
        self.assertFalse(result.checks_performed[0]['passed'])
    
    def test_to_dict(self):
        """Test converting to dictionary."""
        result = ValidationResult()
        result.add_check('check1', True, {})
        result.add_check('check2', False, {})
        result.add_warning('test warning')
        
        dict_result = result.to_dict()
        
        self.assertFalse(dict_result['validation_passed'])
        self.assertEqual(dict_result['total_checks'], 2)
        self.assertEqual(dict_result['checks_passed'], 1)
        self.assertEqual(dict_result['checks_failed'], 1)
        self.assertEqual(len(dict_result['warnings']), 1)


class TestConvergenceChecker(unittest.TestCase):
    """Test ConvergenceChecker class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.checker = ConvergenceChecker()
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_converged_simulation(self):
        """Test detection of converged simulation."""
        log_file = self.temp_dir / 'converged.log'
        with open(log_file, 'w') as f:
            f.write("Iteration 1: residual = 1.0e-1\n")
            f.write("Iteration 2: residual = 1.0e-2\n")
            f.write("Iteration 3: residual = 1.0e-4\n")
            f.write("Iteration 4: residual = 1.0e-7\n")
        
        result = self.checker.check_convergence(log_file)
        
        self.assertTrue(result['converged'])
        self.assertEqual(result['iterations'], 4)
        self.assertAlmostEqual(result['final_residual'], 1e-7)
        self.assertTrue(result['monotonic'])
    
    def test_non_converged_simulation(self):
        """Test detection of non-converged simulation."""
        log_file = self.temp_dir / 'not_converged.log'
        with open(log_file, 'w') as f:
            f.write("Iteration 1: residual = 1.0e-1\n")
            f.write("Iteration 2: residual = 1.0e-2\n")
            f.write("Iteration 3: residual = 1.0e-3\n")
        
        result = self.checker.check_convergence(log_file)
        
        self.assertFalse(result['converged'])
        self.assertAlmostEqual(result['final_residual'], 1e-3)
    
    def test_stalled_convergence(self):
        """Test detection of stalled convergence."""
        log_file = self.temp_dir / 'stalled.log'
        with open(log_file, 'w') as f:
            f.write("Iteration 1: residual = 1.0e-1\n")
            f.write("Iteration 2: residual = 1.0e-2\n")
            # Stalled at 1e-3
            for i in range(3, 10):
                f.write(f"Iteration {i}: residual = 1.0e-3\n")
        
        result = self.checker.check_convergence(log_file)
        
        self.assertTrue(result['stalled'])
    
    def test_non_monotonic_convergence(self):
        """Test detection of non-monotonic convergence."""
        log_file = self.temp_dir / 'non_monotonic.log'
        with open(log_file, 'w') as f:
            f.write("Iteration 1: residual = 1.0e-1\n")
            f.write("Iteration 2: residual = 1.0e-2\n")
            f.write("Iteration 3: residual = 5.0e-2\n")  # Increase
            f.write("Iteration 4: residual = 1.0e-7\n")
        
        result = self.checker.check_convergence(log_file)
        
        self.assertFalse(result['monotonic'])


class TestConservationLawValidator(unittest.TestCase):
    """Test ConservationLawValidator class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.validator = ConservationLawValidator()
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_mass_conservation(self):
        """Test mass conservation check."""
        results_file = self.temp_dir / 'results.json'
        with open(results_file, 'w') as f:
            json.dump({
                'mass': [100.0, 100.0, 100.0, 100.0]
            }, f)
        
        result = self.validator.check_conservation(results_file, 'mass')
        
        self.assertTrue(result['conserved'])
        self.assertEqual(result['initial_value'], 100.0)
        self.assertEqual(result['final_value'], 100.0)
        self.assertAlmostEqual(result['relative_change'], 0.0)
    
    def test_mass_not_conserved(self):
        """Test detection of mass not conserved."""
        results_file = self.temp_dir / 'results.json'
        with open(results_file, 'w') as f:
            json.dump({
                'mass': [100.0, 99.0, 98.0, 95.0]  # 5% loss
            }, f)
        
        result = self.validator.check_conservation(results_file, 'mass')
        
        self.assertFalse(result['conserved'])
        self.assertEqual(result['initial_value'], 100.0)
        self.assertEqual(result['final_value'], 95.0)
        self.assertAlmostEqual(result['relative_change'], 0.05)
    
    def test_energy_conservation_tolerance(self):
        """Test energy conservation with tolerance."""
        results_file = self.temp_dir / 'results.json'
        with open(results_file, 'w') as f:
            json.dump({
                'energy': [1000.0, 1000.01, 999.99, 1000.001]  # Within 1e-5 tolerance
            }, f)
        
        result = self.validator.check_conservation(results_file, 'energy')
        
        # Should be conserved within default energy tolerance (1e-5)
        self.assertTrue(result['conserved'])


class TestRegressionComparator(unittest.TestCase):
    """Test RegressionComparator class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.comparator = RegressionComparator()
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_file_exists_check(self):
        """Test output file existence check."""
        # Create expected file
        (self.temp_dir / 'output.txt').touch()
        
        benchmark_def = {
            'id': 'test-benchmark',
            'expected_results': {
                'output_files': [
                    {'filename': 'output.txt', 'description': 'Test output'}
                ]
            }
        }
        
        result = self.comparator.compare_against_benchmark(
            benchmark_def, self.temp_dir
        )
        
        self.assertTrue(result['all_checks_passed'])
        self.assertEqual(len(result['file_checks']), 1)
        self.assertTrue(result['file_checks'][0]['passed'])
    
    def test_file_missing(self):
        """Test detection of missing output file."""
        benchmark_def = {
            'id': 'test-benchmark',
            'expected_results': {
                'output_files': [
                    {'filename': 'missing.txt', 'description': 'Missing file'}
                ]
            }
        }
        
        result = self.comparator.compare_against_benchmark(
            benchmark_def, self.temp_dir
        )
        
        self.assertFalse(result['all_checks_passed'])
        self.assertEqual(len(result['file_checks']), 1)
        self.assertFalse(result['file_checks'][0]['passed'])
    
    def test_metric_comparison_within_tolerance(self):
        """Test metric comparison within tolerance."""
        # Create metrics file
        metrics_file = self.temp_dir / 'metrics.json'
        with open(metrics_file, 'w') as f:
            json.dump({'solution_max': 0.972}, f)
        
        benchmark_def = {
            'id': 'test-benchmark',
            'expected_results': {
                'metrics': {
                    'solution_max': {
                        'value': 0.975,
                        'tolerance': 0.01,
                        'unit': 'dimensionless'
                    }
                }
            }
        }
        
        result = self.comparator.compare_against_benchmark(
            benchmark_def, self.temp_dir
        )
        
        self.assertTrue(result['all_checks_passed'])
        self.assertEqual(len(result['metric_checks']), 1)
        self.assertTrue(result['metric_checks'][0]['passed'])
    
    def test_metric_comparison_outside_tolerance(self):
        """Test metric comparison outside tolerance."""
        # Create metrics file
        metrics_file = self.temp_dir / 'metrics.json'
        with open(metrics_file, 'w') as f:
            json.dump({'solution_max': 0.9}, f)  # 7.7% error
        
        benchmark_def = {
            'id': 'test-benchmark',
            'expected_results': {
                'metrics': {
                    'solution_max': {
                        'value': 0.975,
                        'tolerance': 0.01,  # 1% tolerance
                        'unit': 'dimensionless'
                    }
                }
            }
        }
        
        result = self.comparator.compare_against_benchmark(
            benchmark_def, self.temp_dir
        )
        
        self.assertFalse(result['all_checks_passed'])
        self.assertEqual(len(result['metric_checks']), 1)
        self.assertFalse(result['metric_checks'][0]['passed'])


class TestValidationFramework(unittest.TestCase):
    """Test ValidationFramework integration."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.framework = ValidationFramework()
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_validate_simulation_with_log(self):
        """Test validation with convergence log."""
        # Create log file
        log_file = self.temp_dir / 'simulation.log'
        with open(log_file, 'w') as f:
            f.write("Iteration 1: residual = 1.0e-1\n")
            f.write("Iteration 2: residual = 1.0e-2\n")
            f.write("Iteration 3: residual = 1.0e-7\n")
        
        result = self.framework.validate_simulation(
            task_id='test-task',
            tool='fenicsx',
            output_dir=self.temp_dir
        )
        
        self.assertIn('convergence', [c['check_name'] for c in result['checks_performed']])
        self.assertTrue(result['validation_passed'])
    
    def test_alert_handler(self):
        """Test alert handler registration and triggering."""
        alerts_received = []
        
        def test_handler(alert_data):
            alerts_received.append(alert_data)
        
        self.framework.register_alert_handler(test_handler)
        
        # Create failing validation
        result = self.framework.validate_simulation(
            task_id='test-task',
            tool='fenicsx',
            output_dir=self.temp_dir  # No files, validation will fail
        )
        
        # Alert should be triggered since validation failed
        # (though convergence check might pass with warning)
        if not result['validation_passed']:
            self.assertGreater(len(alerts_received), 0)


class TestLoadValidationConfig(unittest.TestCase):
    """Test configuration loading."""
    
    def test_load_default_config(self):
        """Test loading default configuration."""
        config = load_validation_config()
        
        self.assertIn('convergence', config)
        self.assertIn('conservation', config)
        self.assertIn('regression', config)
        self.assertEqual(config['convergence']['max_residual'], 1e-6)
    
    def test_load_config_from_file(self):
        """Test loading configuration from file."""
        temp_dir = Path(tempfile.mkdtemp())
        config_file = temp_dir / 'test_config.json'
        
        try:
            test_config = {
                'convergence': {'max_residual': 1e-8},
                'conservation': {'mass_tolerance': 1e-10}
            }
            
            with open(config_file, 'w') as f:
                json.dump(test_config, f)
            
            config = load_validation_config(config_file)
            
            self.assertEqual(config['convergence']['max_residual'], 1e-8)
            self.assertEqual(config['conservation']['mass_tolerance'], 1e-10)
        
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


def run_tests():
    """Run all tests."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestValidationResult))
    suite.addTests(loader.loadTestsFromTestCase(TestConvergenceChecker))
    suite.addTests(loader.loadTestsFromTestCase(TestConservationLawValidator))
    suite.addTests(loader.loadTestsFromTestCase(TestRegressionComparator))
    suite.addTests(loader.loadTestsFromTestCase(TestValidationFramework))
    suite.addTests(loader.loadTestsFromTestCase(TestLoadValidationConfig))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    import sys
    success = run_tests()
    sys.exit(0 if success else 1)
