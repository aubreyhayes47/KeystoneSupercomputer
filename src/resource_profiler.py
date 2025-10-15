"""
Resource Profiler for Keystone Supercomputer
=============================================

This module provides comprehensive resource profiling for containerized simulations,
including CPU, memory, GPU, I/O, and container-level metrics.

Features:
- CPU usage tracking (user, system, total)
- Memory usage tracking (RSS, VMS, available)
- GPU utilization and memory (NVIDIA, Intel)
- I/O statistics (read/write operations and bytes)
- Container-level resource metrics (Docker stats)
- Network I/O tracking
"""

import psutil
import subprocess
import json
import time
import threading
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class ResourceProfiler:
    """
    Comprehensive resource profiler for simulation containers.
    
    Tracks:
    - CPU usage over time
    - Memory consumption
    - GPU utilization (if available)
    - I/O statistics
    - Container resource metrics
    
    Example:
        >>> profiler = ResourceProfiler()
        >>> profiler.start_profiling("container-name")
        >>> # Run simulation
        >>> profile = profiler.stop_profiling()
    """
    
    def __init__(self):
        """Initialize the resource profiler."""
        self._profiling = False
        self._profile_thread = None
        self._metrics = []
        self._initial_io = None
        self._container_name = None
        self._start_time = None
        
    def start_profiling(self, container_name: Optional[str] = None) -> None:
        """
        Start resource profiling.
        
        Args:
            container_name: Docker container name to monitor (optional)
        """
        if self._profiling:
            logger.warning("Profiling already in progress")
            return
            
        self._profiling = True
        self._container_name = container_name
        self._start_time = time.time()
        self._metrics = []
        
        # Get initial I/O counters
        try:
            self._initial_io = psutil.disk_io_counters()
        except Exception as e:
            logger.warning(f"Could not get initial I/O counters: {e}")
            self._initial_io = None
        
        # Start monitoring thread
        self._profile_thread = threading.Thread(target=self._profile_loop, daemon=True)
        self._profile_thread.start()
        
    def stop_profiling(self) -> Dict[str, Any]:
        """
        Stop profiling and return collected metrics.
        
        Returns:
            Dictionary with comprehensive resource usage statistics
        """
        if not self._profiling:
            logger.warning("Profiling is not active")
            return {}
            
        self._profiling = False
        if self._profile_thread:
            self._profile_thread.join(timeout=2.0)
        
        end_time = time.time()
        duration = end_time - self._start_time
        
        # Compute statistics from collected metrics
        profile = self._compute_statistics(duration)
        
        # Add final I/O statistics
        profile['io_stats'] = self._get_io_statistics()
        
        # Add container metrics if available
        if self._container_name:
            profile['container_stats'] = self._get_container_stats()
        
        # Add GPU metrics if available
        profile['gpu_stats'] = self._get_gpu_statistics()
        
        return profile
    
    def _profile_loop(self) -> None:
        """Background thread that collects metrics periodically."""
        while self._profiling:
            try:
                metrics = self._collect_metrics()
                self._metrics.append(metrics)
            except Exception as e:
                logger.warning(f"Error collecting metrics: {e}")
            
            # Sample every 0.5 seconds
            time.sleep(0.5)
    
    def _collect_metrics(self) -> Dict[str, Any]:
        """Collect current resource metrics."""
        metrics = {
            'timestamp': time.time(),
        }
        
        # CPU metrics
        try:
            metrics['cpu_percent'] = psutil.cpu_percent(interval=0.1)
            metrics['cpu_count'] = psutil.cpu_count()
        except Exception as e:
            logger.warning(f"Could not get CPU metrics: {e}")
        
        # Memory metrics
        try:
            mem = psutil.virtual_memory()
            metrics['memory_percent'] = mem.percent
            metrics['memory_used_mb'] = mem.used / (1024 * 1024)
            metrics['memory_available_mb'] = mem.available / (1024 * 1024)
        except Exception as e:
            logger.warning(f"Could not get memory metrics: {e}")
        
        # Process-level metrics
        try:
            process = psutil.Process()
            metrics['process_cpu_percent'] = process.cpu_percent()
            mem_info = process.memory_info()
            metrics['process_memory_mb'] = mem_info.rss / (1024 * 1024)
        except Exception as e:
            logger.warning(f"Could not get process metrics: {e}")
        
        return metrics
    
    def _compute_statistics(self, duration: float) -> Dict[str, Any]:
        """
        Compute aggregate statistics from collected metrics.
        
        Args:
            duration: Total profiling duration in seconds
            
        Returns:
            Dictionary with statistical summary
        """
        if not self._metrics:
            return {
                'duration_seconds': duration,
                'samples_collected': 0,
            }
        
        # Extract time series
        cpu_percentages = [m.get('cpu_percent', 0) for m in self._metrics if 'cpu_percent' in m]
        memory_used = [m.get('memory_used_mb', 0) for m in self._metrics if 'memory_used_mb' in m]
        process_cpu = [m.get('process_cpu_percent', 0) for m in self._metrics if 'process_cpu_percent' in m]
        process_memory = [m.get('process_memory_mb', 0) for m in self._metrics if 'process_memory_mb' in m]
        
        # Compute statistics
        stats = {
            'duration_seconds': round(duration, 2),
            'samples_collected': len(self._metrics),
            'sampling_interval_seconds': 0.5,
        }
        
        if cpu_percentages:
            stats['cpu'] = {
                'mean_percent': round(sum(cpu_percentages) / len(cpu_percentages), 2),
                'max_percent': round(max(cpu_percentages), 2),
                'min_percent': round(min(cpu_percentages), 2),
            }
        
        if memory_used:
            stats['memory'] = {
                'mean_used_mb': round(sum(memory_used) / len(memory_used), 2),
                'max_used_mb': round(max(memory_used), 2),
                'min_used_mb': round(min(memory_used), 2),
            }
        
        if process_cpu:
            stats['process_cpu'] = {
                'mean_percent': round(sum(process_cpu) / len(process_cpu), 2),
                'max_percent': round(max(process_cpu), 2),
            }
        
        if process_memory:
            stats['process_memory'] = {
                'mean_mb': round(sum(process_memory) / len(process_memory), 2),
                'max_mb': round(max(process_memory), 2),
                'min_mb': round(min(process_memory), 2),
            }
        
        return stats
    
    def _get_io_statistics(self) -> Dict[str, Any]:
        """
        Get I/O statistics since profiling started.
        
        Returns:
            Dictionary with I/O metrics
        """
        try:
            if self._initial_io is None:
                return {}
            
            current_io = psutil.disk_io_counters()
            
            read_bytes = current_io.read_bytes - self._initial_io.read_bytes
            write_bytes = current_io.write_bytes - self._initial_io.write_bytes
            read_count = current_io.read_count - self._initial_io.read_count
            write_count = current_io.write_count - self._initial_io.write_count
            
            return {
                'read_mb': round(read_bytes / (1024 * 1024), 2),
                'write_mb': round(write_bytes / (1024 * 1024), 2),
                'read_count': read_count,
                'write_count': write_count,
                'total_io_mb': round((read_bytes + write_bytes) / (1024 * 1024), 2),
            }
        except Exception as e:
            logger.warning(f"Could not get I/O statistics: {e}")
            return {}
    
    def _get_container_stats(self) -> Dict[str, Any]:
        """
        Get Docker container statistics.
        
        Returns:
            Dictionary with container metrics
        """
        if not self._container_name:
            return {}
        
        try:
            # Use docker stats to get container metrics
            cmd = [
                'docker', 'stats', self._container_name,
                '--no-stream', '--format', '{{json .}}'
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0 and result.stdout.strip():
                stats = json.loads(result.stdout.strip())
                
                # Parse CPU percentage (remove % sign)
                cpu_percent = stats.get('CPUPerc', '0%').rstrip('%')
                mem_usage = stats.get('MemUsage', '0B / 0B')
                
                return {
                    'cpu_percent': cpu_percent,
                    'memory_usage': mem_usage,
                    'memory_percent': stats.get('MemPerc', '0%').rstrip('%'),
                    'net_io': stats.get('NetIO', '0B / 0B'),
                    'block_io': stats.get('BlockIO', '0B / 0B'),
                }
        except subprocess.TimeoutExpired:
            logger.warning("Docker stats command timed out")
        except Exception as e:
            logger.warning(f"Could not get container stats: {e}")
        
        return {}
    
    def _get_gpu_statistics(self) -> Dict[str, Any]:
        """
        Get GPU utilization statistics.
        
        Supports:
        - NVIDIA GPUs (via nvidia-smi)
        - Intel GPUs (via intel_gpu_top)
        
        Returns:
            Dictionary with GPU metrics
        """
        gpu_stats = {}
        
        # Try NVIDIA GPU
        nvidia_stats = self._get_nvidia_gpu_stats()
        if nvidia_stats:
            gpu_stats['nvidia'] = nvidia_stats
        
        # Try Intel GPU
        intel_stats = self._get_intel_gpu_stats()
        if intel_stats:
            gpu_stats['intel'] = intel_stats
        
        return gpu_stats
    
    def _get_nvidia_gpu_stats(self) -> Optional[Dict[str, Any]]:
        """Get NVIDIA GPU statistics using nvidia-smi."""
        try:
            cmd = [
                'nvidia-smi',
                '--query-gpu=utilization.gpu,utilization.memory,memory.used,memory.total,temperature.gpu',
                '--format=csv,noheader,nounits'
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0 and result.stdout.strip():
                values = result.stdout.strip().split(',')
                if len(values) >= 5:
                    return {
                        'gpu_utilization_percent': float(values[0].strip()),
                        'memory_utilization_percent': float(values[1].strip()),
                        'memory_used_mb': float(values[2].strip()),
                        'memory_total_mb': float(values[3].strip()),
                        'temperature_celsius': float(values[4].strip()),
                    }
        except (subprocess.TimeoutExpired, FileNotFoundError, ValueError) as e:
            logger.debug(f"NVIDIA GPU not available or error: {e}")
        
        return None
    
    def _get_intel_gpu_stats(self) -> Optional[Dict[str, Any]]:
        """Get Intel GPU statistics using intel_gpu_top."""
        try:
            # intel_gpu_top requires special setup, so we check if it's available
            cmd = ['intel_gpu_top', '-J', '-s', '100']
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=2)
            
            if result.returncode == 0 and result.stdout.strip():
                stats = json.loads(result.stdout)
                
                # Extract relevant metrics
                engines = stats.get('engines', {})
                render = engines.get('Render/3D', {})
                
                return {
                    'render_busy_percent': render.get('busy', 0),
                    'available': True,
                }
        except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError) as e:
            logger.debug(f"Intel GPU not available or error: {e}")
        
        return None


class ContainerResourceMonitor:
    """
    Monitor Docker container resources during simulation execution.
    
    This class provides container-specific resource tracking using Docker APIs
    and stats commands.
    """
    
    def __init__(self, container_name: str):
        """
        Initialize container monitor.
        
        Args:
            container_name: Name of the Docker container to monitor
        """
        self.container_name = container_name
        self.profiler = ResourceProfiler()
    
    def get_container_info(self) -> Dict[str, Any]:
        """
        Get container information and configuration.
        
        Returns:
            Dictionary with container details
        """
        try:
            cmd = ['docker', 'inspect', self.container_name]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0 and result.stdout.strip():
                info = json.loads(result.stdout)
                if info:
                    container = info[0]
                    config = container.get('Config', {})
                    host_config = container.get('HostConfig', {})
                    
                    return {
                        'image': config.get('Image'),
                        'created': container.get('Created'),
                        'state': container.get('State', {}).get('Status'),
                        'cpu_shares': host_config.get('CpuShares'),
                        'memory_limit': host_config.get('Memory'),
                        'memory_swap': host_config.get('MemorySwap'),
                    }
        except Exception as e:
            logger.warning(f"Could not get container info: {e}")
        
        return {}
    
    def start_monitoring(self) -> None:
        """Start monitoring container resources."""
        self.profiler.start_profiling(self.container_name)
    
    def stop_monitoring(self) -> Dict[str, Any]:
        """
        Stop monitoring and return comprehensive profile.
        
        Returns:
            Dictionary with container resource usage
        """
        profile = self.profiler.stop_profiling()
        profile['container_info'] = self.get_container_info()
        return profile


# Singleton instance for global access
_global_profiler = None


def get_profiler() -> ResourceProfiler:
    """
    Get the global resource profiler instance.
    
    Returns:
        Global ResourceProfiler instance
    """
    global _global_profiler
    if _global_profiler is None:
        _global_profiler = ResourceProfiler()
    return _global_profiler
