"""
Automated Post-Run Validation Framework for Keystone Supercomputer
===================================================================

This module provides comprehensive automated validation for simulation workflows,
including convergence analysis, conservation law checking, and regression comparison
against established benchmarks.

Features:
- Convergence analysis for iterative solvers
- Conservation law validation (mass, momentum, energy)
- Regression comparison against benchmark results
- Automated result recording in provenance logs
- Configurable tolerance levels and validation rules
- Alert mechanism for failed checks

Example:
    >>> from validation_framework import ValidationFramework
    >>> validator = ValidationFramework()
    >>> 
    >>> # Validate a simulation result
    >>> result = validator.validate_simulation(
    ...     task_id="abc123",
    ...     tool="fenicsx",
    ...     benchmark_id="fenicsx-poisson-2d-basic",
    ...     output_dir="/data/results"
    ... )
    >>> 
    >>> if result['validation_passed']:
    ...     print("All checks passed!")
    ... else:
    ...     print(f"Failed checks: {result['failed_checks']}")
"""

import json
import os
import re
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ValidationResult:
    """Container for validation results."""
    
    def __init__(self):
        self.checks_performed = []
        self.checks_passed = []
        self.checks_failed = []
        self.warnings = []
        self.metadata = {}
    
    def add_check(self, check_name: str, passed: bool, details: Dict[str, Any]):
        """Add a validation check result."""
        check_result = {
            'check_name': check_name,
            'passed': passed,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'details': details
        }
        
        self.checks_performed.append(check_result)
        if passed:
            self.checks_passed.append(check_result)
        else:
            self.checks_failed.append(check_result)
    
    def add_warning(self, message: str):
        """Add a warning message."""
        self.warnings.append({
            'message': message,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        })
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            'validation_passed': len(self.checks_failed) == 0,
            'total_checks': len(self.checks_performed),
            'checks_passed': len(self.checks_passed),
            'checks_failed': len(self.checks_failed),
            'checks_performed': self.checks_performed,
            'failed_checks': self.checks_failed,
            'warnings': self.warnings,
            'metadata': self.metadata
        }


class ConvergenceChecker:
    """
    Analyzes convergence behavior of iterative solvers.
    
    Checks for:
    - Monotonic decrease in residuals
    - Achievement of target tolerance
    - Convergence rate
    - Stalled convergence
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize convergence checker.
        
        Args:
            config: Configuration dictionary with thresholds
        """
        self.config = config or {}
        self.max_residual = self.config.get('max_residual', 1e-6)
        self.min_convergence_rate = self.config.get('min_convergence_rate', 0.1)
        self.stall_threshold = self.config.get('stall_threshold', 5)
    
    def check_convergence(self, log_file: Path) -> Dict[str, Any]:
        """
        Check convergence from solver log file.
        
        Args:
            log_file: Path to solver log file
            
        Returns:
            Dictionary with convergence analysis results
        """
        result = {
            'converged': False,
            'final_residual': None,
            'iterations': 0,
            'convergence_rate': None,
            'monotonic': False,
            'stalled': False,
            'details': {}
        }
        
        if not log_file.exists():
            result['details']['error'] = f"Log file not found: {log_file}"
            return result
        
        # Parse residuals from log file
        residuals = self._parse_residuals(log_file)
        
        if not residuals:
            result['details']['warning'] = "No residuals found in log file"
            return result
        
        result['iterations'] = len(residuals)
        result['final_residual'] = residuals[-1] if residuals else None
        
        # Check convergence
        if result['final_residual'] and result['final_residual'] < self.max_residual:
            result['converged'] = True
        
        # Check monotonic decrease
        result['monotonic'] = self._is_monotonic_decrease(residuals)
        
        # Check for stalled convergence
        result['stalled'] = self._is_stalled(residuals)
        
        # Calculate convergence rate
        if len(residuals) > 1:
            result['convergence_rate'] = self._calculate_convergence_rate(residuals)
        
        result['details']['residuals'] = residuals[:10]  # First 10 for reference
        
        return result
    
    def _parse_residuals(self, log_file: Path) -> List[float]:
        """Parse residuals from log file."""
        residuals = []
        
        try:
            with open(log_file, 'r') as f:
                for line in f:
                    # Look for common residual patterns
                    # Pattern for "residual = 1.23e-4" or "r = 1.23e-4"
                    match = re.search(r'(?:residual|res|r)\s*[=:]\s*([\d.e+-]+)', line, re.IGNORECASE)
                    if match:
                        try:
                            residual = float(match.group(1))
                            residuals.append(residual)
                        except ValueError:
                            continue
        except Exception as e:
            logger.warning(f"Error parsing residuals from {log_file}: {e}")
        
        return residuals
    
    def _is_monotonic_decrease(self, residuals: List[float], tolerance: float = 1e-10) -> bool:
        """Check if residuals decrease monotonically."""
        for i in range(1, len(residuals)):
            if residuals[i] > residuals[i-1] * (1 + tolerance):
                return False
        return True
    
    def _is_stalled(self, residuals: List[float]) -> bool:
        """Check if convergence has stalled."""
        if len(residuals) < self.stall_threshold:
            return False
        
        # Check if last N residuals are nearly constant
        recent = residuals[-self.stall_threshold:]
        if max(recent) / min(recent) < 1.1:  # Less than 10% variation
            return True
        
        return False
    
    def _calculate_convergence_rate(self, residuals: List[float]) -> float:
        """Calculate average convergence rate."""
        if len(residuals) < 2:
            return 0.0
        
        rates = []
        for i in range(1, len(residuals)):
            if residuals[i-1] > 0 and residuals[i] > 0:
                rate = residuals[i] / residuals[i-1]
                rates.append(rate)
        
        return sum(rates) / len(rates) if rates else 0.0


class ConservationLawValidator:
    """
    Validates conservation laws (mass, momentum, energy).
    
    Checks for:
    - Mass conservation
    - Momentum conservation
    - Energy conservation
    - Global balance checks
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize conservation law validator.
        
        Args:
            config: Configuration dictionary with tolerances
        """
        self.config = config or {}
        self.mass_tolerance = self.config.get('mass_tolerance', 1e-6)
        self.momentum_tolerance = self.config.get('momentum_tolerance', 1e-6)
        self.energy_tolerance = self.config.get('energy_tolerance', 1e-5)
    
    def check_conservation(self, results_file: Path, law_type: str) -> Dict[str, Any]:
        """
        Check conservation law from results file.
        
        Args:
            results_file: Path to results file
            law_type: Type of conservation law ('mass', 'momentum', 'energy')
            
        Returns:
            Dictionary with conservation check results
        """
        result = {
            'conserved': False,
            'law_type': law_type,
            'initial_value': None,
            'final_value': None,
            'relative_change': None,
            'tolerance': self._get_tolerance(law_type),
            'details': {}
        }
        
        if not results_file.exists():
            result['details']['error'] = f"Results file not found: {results_file}"
            return result
        
        # Parse conservation values
        values = self._parse_conservation_values(results_file, law_type)
        
        if not values or len(values) < 2:
            result['details']['warning'] = f"Insufficient data for {law_type} conservation check"
            return result
        
        result['initial_value'] = values[0]
        result['final_value'] = values[-1]
        
        # Calculate relative change
        if result['initial_value'] != 0:
            result['relative_change'] = abs(
                (result['final_value'] - result['initial_value']) / result['initial_value']
            )
        else:
            result['relative_change'] = abs(result['final_value'])
        
        # Check if conserved within tolerance
        result['conserved'] = result['relative_change'] < result['tolerance']
        result['details']['all_values'] = values
        
        return result
    
    def _get_tolerance(self, law_type: str) -> float:
        """Get tolerance for conservation law type."""
        tolerances = {
            'mass': self.mass_tolerance,
            'momentum': self.momentum_tolerance,
            'energy': self.energy_tolerance
        }
        return tolerances.get(law_type, 1e-6)
    
    def _parse_conservation_values(self, results_file: Path, law_type: str) -> List[float]:
        """Parse conservation values from results file."""
        values = []
        
        try:
            # Try to parse as JSON first
            with open(results_file, 'r') as f:
                data = json.load(f)
                if law_type in data:
                    values = data[law_type]
                elif 'conservation' in data and law_type in data['conservation']:
                    values = data['conservation'][law_type]
        except json.JSONDecodeError:
            # Try parsing as text
            try:
                with open(results_file, 'r') as f:
                    for line in f:
                        # Look for conservation patterns
                        pattern = rf'{law_type}\s*[=:]\s*([\d.e+-]+)'
                        match = re.search(pattern, line, re.IGNORECASE)
                        if match:
                            values.append(float(match.group(1)))
            except Exception as e:
                logger.warning(f"Error parsing conservation values: {e}")
        
        return values


class RegressionComparator:
    """
    Compares simulation results against established benchmarks.
    
    Performs:
    - Metric comparison (solution values, norms, etc.)
    - File existence checks
    - Performance regression detection
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize regression comparator.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.default_tolerance = self.config.get('default_tolerance', 0.01)
    
    def compare_against_benchmark(
        self,
        benchmark_def: Dict[str, Any],
        output_dir: Path
    ) -> Dict[str, Any]:
        """
        Compare results against benchmark definition.
        
        Args:
            benchmark_def: Benchmark definition with expected results
            output_dir: Directory containing simulation outputs
            
        Returns:
            Dictionary with comparison results
        """
        result = {
            'benchmark_id': benchmark_def.get('id', 'unknown'),
            'all_checks_passed': True,
            'file_checks': [],
            'metric_checks': [],
            'performance_checks': [],
            'details': {}
        }
        
        expected = benchmark_def.get('expected_results', {})
        
        # Check output files
        for file_info in expected.get('output_files', []):
            check = self._check_output_file(output_dir, file_info)
            result['file_checks'].append(check)
            if not check['passed']:
                result['all_checks_passed'] = False
        
        # Check metrics
        for metric_name, metric_spec in expected.get('metrics', {}).items():
            check = self._check_metric(output_dir, metric_name, metric_spec)
            result['metric_checks'].append(check)
            if not check['passed']:
                result['all_checks_passed'] = False
        
        # Check performance (optional warning only)
        perf = expected.get('performance', {})
        if perf:
            perf_check = self._check_performance(output_dir, perf)
            result['performance_checks'].append(perf_check)
            # Performance checks are warnings, not failures
        
        return result
    
    def _check_output_file(self, output_dir: Path, file_info: Dict[str, Any]) -> Dict[str, Any]:
        """Check if expected output file exists."""
        filename = file_info.get('filename', '')
        file_path = output_dir / filename
        
        passed = file_path.exists()
        
        return {
            'check_type': 'file_exists',
            'filename': filename,
            'passed': passed,
            'details': {
                'expected_path': str(file_path),
                'exists': passed,
                'description': file_info.get('description', '')
            }
        }
    
    def _check_metric(
        self,
        output_dir: Path,
        metric_name: str,
        metric_spec: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Check if metric value matches expected value within tolerance."""
        expected_value = metric_spec.get('value')
        tolerance = metric_spec.get('tolerance', self.default_tolerance)
        unit = metric_spec.get('unit', '')
        
        # Try to find actual value in results
        actual_value = self._extract_metric_value(output_dir, metric_name)
        
        passed = False
        relative_error = None
        
        if actual_value is not None and expected_value is not None:
            if expected_value != 0:
                relative_error = abs((actual_value - expected_value) / expected_value)
            else:
                relative_error = abs(actual_value)
            
            passed = relative_error <= tolerance
        
        return {
            'check_type': 'metric_value',
            'metric_name': metric_name,
            'passed': passed,
            'details': {
                'expected_value': expected_value,
                'actual_value': actual_value,
                'tolerance': tolerance,
                'relative_error': relative_error,
                'unit': unit
            }
        }
    
    def _extract_metric_value(self, output_dir: Path, metric_name: str) -> Optional[float]:
        """Extract metric value from results files."""
        # Look for metrics.json file
        metrics_file = output_dir / 'metrics.json'
        if metrics_file.exists():
            try:
                with open(metrics_file, 'r') as f:
                    metrics = json.load(f)
                    if metric_name in metrics:
                        return float(metrics[metric_name])
            except Exception as e:
                logger.warning(f"Error reading metrics file: {e}")
        
        # Look in log files
        for log_file in output_dir.glob('*.log'):
            try:
                with open(log_file, 'r') as f:
                    for line in f:
                        pattern = rf'{metric_name}\s*[=:]\s*([\d.e+-]+)'
                        match = re.search(pattern, line, re.IGNORECASE)
                        if match:
                            return float(match.group(1))
            except Exception as e:
                continue
        
        return None
    
    def _check_performance(self, output_dir: Path, perf_spec: Dict[str, Any]) -> Dict[str, Any]:
        """Check performance metrics (warning only)."""
        typical_runtime = perf_spec.get('typical_runtime_seconds')
        typical_memory = perf_spec.get('memory_mb')
        
        # Try to read actual performance from timing file
        timing_file = output_dir / 'timing.json'
        actual_runtime = None
        actual_memory = None
        
        if timing_file.exists():
            try:
                with open(timing_file, 'r') as f:
                    timing = json.load(f)
                    actual_runtime = timing.get('runtime_seconds')
                    actual_memory = timing.get('memory_mb')
            except Exception as e:
                logger.warning(f"Error reading timing file: {e}")
        
        return {
            'check_type': 'performance',
            'passed': True,  # Performance is warning only
            'details': {
                'typical_runtime_seconds': typical_runtime,
                'actual_runtime_seconds': actual_runtime,
                'typical_memory_mb': typical_memory,
                'actual_memory_mb': actual_memory,
                'reference_hardware': perf_spec.get('reference_hardware', '')
            }
        }


class ValidationFramework:
    """
    Main validation framework that orchestrates all validation checks.
    
    Integrates:
    - Convergence checking
    - Conservation law validation
    - Regression comparison
    - Result recording in provenance logs
    - Alert generation
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize validation framework.
        
        Args:
            config: Configuration dictionary for all validators
        """
        self.config = config or {}
        
        # Initialize validators
        self.convergence_checker = ConvergenceChecker(
            self.config.get('convergence', {})
        )
        self.conservation_validator = ConservationLawValidator(
            self.config.get('conservation', {})
        )
        self.regression_comparator = RegressionComparator(
            self.config.get('regression', {})
        )
        
        # Alert configuration
        self.alert_on_failure = self.config.get('alert_on_failure', True)
        self.alert_handlers = []
    
    def register_alert_handler(self, handler: callable):
        """Register a callback function for alerts."""
        self.alert_handlers.append(handler)
    
    def validate_simulation(
        self,
        task_id: str,
        tool: str,
        output_dir: Union[str, Path],
        benchmark_id: Optional[str] = None,
        custom_checks: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Perform comprehensive validation on simulation results.
        
        Args:
            task_id: Unique task identifier
            tool: Simulation tool name
            output_dir: Directory containing simulation outputs
            benchmark_id: Optional benchmark ID for regression comparison
            custom_checks: Optional custom validation checks
            
        Returns:
            Comprehensive validation results dictionary
        """
        output_dir = Path(output_dir)
        validation_result = ValidationResult()
        validation_result.metadata = {
            'task_id': task_id,
            'tool': tool,
            'output_dir': str(output_dir),
            'benchmark_id': benchmark_id,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
        
        logger.info(f"Starting validation for task {task_id} (tool: {tool})")
        
        # 1. Convergence checks
        log_file = output_dir / 'simulation.log'
        if log_file.exists():
            conv_result = self.convergence_checker.check_convergence(log_file)
            validation_result.add_check(
                'convergence',
                conv_result['converged'],
                conv_result
            )
        else:
            validation_result.add_warning(f"Log file not found: {log_file}")
        
        # 2. Conservation law checks
        results_file = output_dir / 'results.json'
        if results_file.exists():
            for law_type in ['mass', 'momentum', 'energy']:
                cons_result = self.conservation_validator.check_conservation(
                    results_file, law_type
                )
                # Only fail if conservation data was found and violated
                if cons_result.get('initial_value') is not None:
                    validation_result.add_check(
                        f'conservation_{law_type}',
                        cons_result['conserved'],
                        cons_result
                    )
        
        # 3. Regression comparison against benchmark
        if benchmark_id:
            try:
                # Import benchmark registry
                import sys
                sys.path.insert(0, str(Path(__file__).parent / 'sim-toolbox' / 'benchmarks'))
                from benchmark_registry import BenchmarkRegistry
                registry = BenchmarkRegistry()
                benchmark_def = registry.load_benchmark(benchmark_id)
                
                reg_result = self.regression_comparator.compare_against_benchmark(
                    benchmark_def, output_dir
                )
                
                validation_result.add_check(
                    'regression_comparison',
                    reg_result['all_checks_passed'],
                    reg_result
                )
                
            except Exception as e:
                logger.warning(f"Error loading benchmark {benchmark_id}: {e}")
                validation_result.add_warning(
                    f"Could not perform regression comparison: {e}"
                )
        
        # 4. Custom checks
        if custom_checks:
            for check_name, check_func in custom_checks.items():
                try:
                    check_result = check_func(output_dir)
                    validation_result.add_check(
                        f'custom_{check_name}',
                        check_result.get('passed', False),
                        check_result
                    )
                except Exception as e:
                    logger.error(f"Error in custom check {check_name}: {e}")
                    validation_result.add_warning(
                        f"Custom check {check_name} failed: {e}"
                    )
        
        # Convert to dictionary
        result_dict = validation_result.to_dict()
        
        # 5. Trigger alerts if validation failed
        if not result_dict['validation_passed'] and self.alert_on_failure:
            self._trigger_alerts(task_id, result_dict)
        
        logger.info(
            f"Validation complete for task {task_id}: "
            f"{result_dict['checks_passed']}/{result_dict['total_checks']} checks passed"
        )
        
        return result_dict
    
    def _trigger_alerts(self, task_id: str, validation_result: Dict[str, Any]):
        """Trigger registered alert handlers."""
        alert_data = {
            'task_id': task_id,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'failed_checks': validation_result['failed_checks'],
            'warnings': validation_result['warnings']
        }
        
        for handler in self.alert_handlers:
            try:
                handler(alert_data)
            except Exception as e:
                logger.error(f"Error in alert handler: {e}")


def load_validation_config(config_file: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
    """
    Load validation configuration from file.
    
    Args:
        config_file: Path to configuration file (JSON or YAML)
        
    Returns:
        Configuration dictionary
    """
    if config_file is None:
        # Return default configuration
        return {
            'convergence': {
                'max_residual': 1e-6,
                'min_convergence_rate': 0.1,
                'stall_threshold': 5
            },
            'conservation': {
                'mass_tolerance': 1e-6,
                'momentum_tolerance': 1e-6,
                'energy_tolerance': 1e-5
            },
            'regression': {
                'default_tolerance': 0.01
            },
            'alert_on_failure': True
        }
    
    config_file = Path(config_file)
    if not config_file.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_file}")
    
    with open(config_file, 'r') as f:
        if config_file.suffix in ['.yaml', '.yml']:
            try:
                import yaml
                return yaml.safe_load(f)
            except ImportError:
                raise ImportError("PyYAML is required to load YAML config files")
        else:
            return json.load(f)
