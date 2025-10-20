"""
Validation Integration for Keystone Supercomputer
==================================================

This module integrates the validation framework with the task pipeline,
provenance logging, and job monitoring systems.

Features:
- Automatic post-run validation
- Result recording in provenance logs
- Integration with job monitoring
- Alert mechanism for failed checks
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Union
from datetime import datetime

from validation_framework import ValidationFramework, load_validation_config
from provenance_logger import get_provenance_logger
from job_monitor import get_monitor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ValidationIntegration:
    """
    Integrates validation framework with existing Keystone systems.
    
    Provides hooks for automatic post-run validation, result recording,
    and alert generation.
    """
    
    def __init__(self, config_file: Optional[Union[str, Path]] = None):
        """
        Initialize validation integration.
        
        Args:
            config_file: Optional path to validation configuration file
        """
        self.config = load_validation_config(config_file)
        self.validator = ValidationFramework(self.config)
        self.prov_logger = get_provenance_logger()
        self.job_monitor = get_monitor()
        
        # Register default alert handlers
        self._register_default_alert_handlers()
    
    def _register_default_alert_handlers(self):
        """Register default alert handlers."""
        # Console alert handler
        def console_alert(alert_data):
            task_id = alert_data['task_id']
            failed_checks = alert_data['failed_checks']
            logger.warning(
                f"VALIDATION ALERT for task {task_id}: "
                f"{len(failed_checks)} check(s) failed"
            )
            for check in failed_checks:
                logger.warning(f"  - {check['check_name']}: {check['details']}")
        
        self.validator.register_alert_handler(console_alert)
        
        # File-based alert handler
        def file_alert(alert_data):
            alerts_dir = Path("/tmp/keystone_validation/alerts")
            alerts_dir.mkdir(parents=True, exist_ok=True)
            
            alert_file = alerts_dir / f"alert_{alert_data['task_id']}.json"
            with open(alert_file, 'w') as f:
                json.dump(alert_data, f, indent=2)
        
        self.validator.register_alert_handler(file_alert)
    
    def validate_task_result(
        self,
        task_id: str,
        tool: str,
        output_dir: Union[str, Path],
        benchmark_id: Optional[str] = None,
        workflow_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Validate task results and integrate with provenance/monitoring.
        
        Args:
            task_id: Unique task identifier
            tool: Simulation tool name
            output_dir: Directory containing simulation outputs
            benchmark_id: Optional benchmark ID for regression comparison
            workflow_id: Optional workflow ID for provenance tracking
            
        Returns:
            Validation results dictionary
        """
        logger.info(f"Validating task {task_id} results...")
        
        # Perform validation
        validation_result = self.validator.validate_simulation(
            task_id=task_id,
            tool=tool,
            output_dir=output_dir,
            benchmark_id=benchmark_id
        )
        
        # Record validation results in provenance log
        if workflow_id:
            self._record_validation_in_provenance(workflow_id, validation_result)
        
        # Save validation results to file
        self._save_validation_results(task_id, validation_result)
        
        return validation_result
    
    def _record_validation_in_provenance(
        self,
        workflow_id: str,
        validation_result: Dict[str, Any]
    ):
        """Record validation results in provenance log."""
        try:
            # Add validation event to timeline
            self.prov_logger.add_event(
                workflow_id=workflow_id,
                event_type="validation",
                event_data={
                    'validation_passed': validation_result['validation_passed'],
                    'checks_passed': validation_result['checks_passed'],
                    'checks_failed': validation_result['checks_failed'],
                    'total_checks': validation_result['total_checks'],
                    'failed_checks': validation_result['failed_checks'],
                    'warnings': validation_result['warnings']
                }
            )
            
            # Record validation metadata
            validation_metadata = {
                'validation_performed': True,
                'validation_timestamp': datetime.utcnow().isoformat() + 'Z',
                'validation_passed': validation_result['validation_passed'],
                'validation_summary': {
                    'total_checks': validation_result['total_checks'],
                    'checks_passed': validation_result['checks_passed'],
                    'checks_failed': validation_result['checks_failed']
                }
            }
            
            self.prov_logger.update_metadata(workflow_id, validation_metadata)
            
            logger.info(f"Validation results recorded in provenance for workflow {workflow_id}")
            
        except Exception as e:
            logger.error(f"Error recording validation in provenance: {e}")
    
    def _save_validation_results(self, task_id: str, validation_result: Dict[str, Any]):
        """Save validation results to file."""
        results_dir = Path("/tmp/keystone_validation/results")
        results_dir.mkdir(parents=True, exist_ok=True)
        
        result_file = results_dir / f"validation_{task_id}.json"
        
        try:
            with open(result_file, 'w') as f:
                json.dump(validation_result, f, indent=2)
            logger.info(f"Validation results saved to {result_file}")
        except Exception as e:
            logger.error(f"Error saving validation results: {e}")
    
    def get_validation_history(
        self,
        tool: Optional[str] = None,
        passed_only: bool = False,
        failed_only: bool = False,
        limit: int = 100
    ) -> list:
        """
        Retrieve validation history.
        
        Args:
            tool: Filter by tool name
            passed_only: Only return passed validations
            failed_only: Only return failed validations
            limit: Maximum number of results
            
        Returns:
            List of validation results
        """
        results_dir = Path("/tmp/keystone_validation/results")
        
        if not results_dir.exists():
            return []
        
        validations = []
        
        for result_file in sorted(results_dir.glob("validation_*.json"), reverse=True):
            if len(validations) >= limit:
                break
            
            try:
                with open(result_file, 'r') as f:
                    validation = json.load(f)
                
                # Apply filters
                if tool and validation.get('metadata', {}).get('tool') != tool:
                    continue
                
                if passed_only and not validation.get('validation_passed'):
                    continue
                
                if failed_only and validation.get('validation_passed'):
                    continue
                
                validations.append(validation)
                
            except Exception as e:
                logger.warning(f"Error reading validation file {result_file}: {e}")
                continue
        
        return validations
    
    def get_validation_statistics(self) -> Dict[str, Any]:
        """
        Get aggregate validation statistics.
        
        Returns:
            Dictionary with validation statistics
        """
        validations = self.get_validation_history(limit=1000)
        
        stats = {
            'total_validations': len(validations),
            'passed': 0,
            'failed': 0,
            'by_tool': {},
            'common_failures': {},
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
        
        for validation in validations:
            # Count passed/failed
            if validation.get('validation_passed'):
                stats['passed'] += 1
            else:
                stats['failed'] += 1
            
            # Count by tool
            tool = validation.get('metadata', {}).get('tool', 'unknown')
            if tool not in stats['by_tool']:
                stats['by_tool'][tool] = {'passed': 0, 'failed': 0}
            
            if validation.get('validation_passed'):
                stats['by_tool'][tool]['passed'] += 1
            else:
                stats['by_tool'][tool]['failed'] += 1
            
            # Track common failures
            for failed_check in validation.get('failed_checks', []):
                check_name = failed_check.get('check_name', 'unknown')
                stats['common_failures'][check_name] = \
                    stats['common_failures'].get(check_name, 0) + 1
        
        # Calculate success rate
        if stats['total_validations'] > 0:
            stats['success_rate'] = stats['passed'] / stats['total_validations']
        else:
            stats['success_rate'] = 0.0
        
        return stats


# Global validation integration instance
_validation_integration_instance = None


def get_validation_integration(config_file: Optional[Union[str, Path]] = None) -> ValidationIntegration:
    """
    Get the global validation integration instance.
    
    Args:
        config_file: Optional path to validation configuration file
        
    Returns:
        ValidationIntegration instance
    """
    global _validation_integration_instance
    if _validation_integration_instance is None:
        _validation_integration_instance = ValidationIntegration(config_file)
    return _validation_integration_instance


def validate_task(
    task_id: str,
    tool: str,
    output_dir: Union[str, Path],
    benchmark_id: Optional[str] = None,
    workflow_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Convenience function to validate a task using the global integration instance.
    
    Args:
        task_id: Unique task identifier
        tool: Simulation tool name
        output_dir: Directory containing simulation outputs
        benchmark_id: Optional benchmark ID for regression comparison
        workflow_id: Optional workflow ID for provenance tracking
        
    Returns:
        Validation results dictionary
    """
    integration = get_validation_integration()
    return integration.validate_task_result(
        task_id=task_id,
        tool=tool,
        output_dir=output_dir,
        benchmark_id=benchmark_id,
        workflow_id=workflow_id
    )
