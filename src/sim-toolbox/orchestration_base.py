#!/usr/bin/env python3
"""
Orchestration Base Class for Simulation Adapters
================================================

This module defines the standardized interface for simulation tool orchestration.
All simulation adapters should inherit from OrchestrationBase to ensure they:
- Support health checks
- Provide status reporting
- Expose standardized metadata APIs
- Enable robust workflow management

This interface allows orchestration systems (Celery, Kubernetes, etc.) to
reliably manage and monitor simulation containers.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime
from enum import Enum


class HealthStatus(Enum):
    """Enumeration of health check statuses."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class SimulationStatus(Enum):
    """Enumeration of simulation states."""
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class OrchestrationBase(ABC):
    """
    Base class for simulation adapters with orchestration support.
    
    All simulation adapters (OpenFOAM, LAMMPS, FEniCSx) should inherit from
    this class to ensure they provide consistent orchestration APIs.
    """
    
    def __init__(self, image_name: str, output_dir: str):
        """
        Initialize the orchestration base.
        
        Args:
            image_name: Docker image name for the simulation tool
            output_dir: Directory for simulation outputs
        """
        self.image_name = image_name
        self.output_dir = output_dir
        self._last_health_check = None
        self._current_status = SimulationStatus.IDLE
        self._simulation_metadata = {}
    
    @abstractmethod
    def run_simulation(self, **kwargs) -> Dict[str, Any]:
        """
        Run a simulation with the given parameters.
        
        This method must be implemented by each adapter.
        
        Returns:
            Dictionary containing simulation results
        """
        pass
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform a health check on the simulation tool.
        
        Checks:
        - Docker image availability
        - Container runtime accessibility
        - Output directory writability
        
        Returns:
            Dictionary with health check results:
                - status: HealthStatus enum value
                - timestamp: ISO format timestamp
                - checks: Dict of individual check results
                - message: Human-readable status message
        """
        checks = {}
        overall_status = HealthStatus.HEALTHY
        messages = []
        
        # Check 1: Docker image availability
        try:
            image_available = self.check_image_available()
            checks['image_available'] = image_available
            if not image_available:
                overall_status = HealthStatus.UNHEALTHY
                messages.append(f"Docker image '{self.image_name}' not available")
        except Exception as e:
            checks['image_available'] = False
            overall_status = HealthStatus.UNHEALTHY
            messages.append(f"Failed to check image: {str(e)}")
        
        # Check 2: Docker daemon accessibility
        try:
            import subprocess
            result = subprocess.run(
                ["docker", "info"],
                capture_output=True,
                timeout=5
            )
            docker_accessible = result.returncode == 0
            checks['docker_accessible'] = docker_accessible
            if not docker_accessible:
                overall_status = HealthStatus.UNHEALTHY
                messages.append("Docker daemon not accessible")
        except Exception as e:
            checks['docker_accessible'] = False
            overall_status = HealthStatus.UNHEALTHY
            messages.append(f"Docker daemon check failed: {str(e)}")
        
        # Check 3: Output directory writability
        try:
            from pathlib import Path
            output_path = Path(self.output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            # Test write access
            test_file = output_path / ".health_check"
            test_file.write_text("test")
            test_file.unlink()
            
            checks['output_dir_writable'] = True
        except Exception as e:
            checks['output_dir_writable'] = False
            if overall_status == HealthStatus.HEALTHY:
                overall_status = HealthStatus.DEGRADED
            messages.append(f"Output directory not writable: {str(e)}")
        
        # Prepare result
        result = {
            'status': overall_status.value,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'checks': checks,
            'message': '; '.join(messages) if messages else 'All checks passed',
            'tool': self.__class__.__name__,
            'image': self.image_name
        }
        
        self._last_health_check = result
        return result
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get current status of the simulation adapter.
        
        Returns:
            Dictionary with status information:
                - state: Current simulation state
                - last_result: Last simulation result if available
                - last_health_check: Last health check result if available
                - metadata: Adapter metadata
        """
        return {
            'state': self._current_status.value,
            'last_result': getattr(self, 'last_result', None),
            'last_health_check': self._last_health_check,
            'metadata': self._simulation_metadata,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
    
    def get_metadata(self) -> Dict[str, Any]:
        """
        Get metadata about the simulation tool.
        
        Returns:
            Dictionary with tool metadata:
                - tool_name: Name of the simulation tool
                - image_name: Docker image name
                - capabilities: List of supported features
                - version: Tool version if available
        """
        return {
            'tool_name': self.__class__.__name__.replace('Adapter', ''),
            'image_name': self.image_name,
            'output_dir': str(self.output_dir),
            'capabilities': self._get_capabilities(),
            'version': self._get_version(),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
    
    @abstractmethod
    def _get_capabilities(self) -> list:
        """
        Return list of capabilities supported by this adapter.
        
        Should be implemented by each adapter to describe its features.
        """
        pass
    
    def _get_version(self) -> Optional[str]:
        """
        Get version information for the simulation tool.
        
        Default implementation returns None. Override in subclasses to
        extract version from Docker image or other sources.
        """
        return None
    
    @abstractmethod
    def check_image_available(self) -> bool:
        """
        Check if the Docker image is available locally.
        
        Must be implemented by each adapter.
        
        Returns:
            True if image exists, False otherwise
        """
        pass
    
    def _update_status(self, status: SimulationStatus):
        """Update the current simulation status."""
        self._current_status = status
    
    def _update_metadata(self, metadata: Dict[str, Any]):
        """Update simulation metadata."""
        self._simulation_metadata.update(metadata)
