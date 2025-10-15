#!/usr/bin/env python3
"""
Benchmark Module for Keystone Supercomputer
============================================

This module provides standardized benchmarks for simulation tools on both CPU
and GPU/NPU hardware. It records and compares performance metrics for reproducibility.

Features:
- Run standardized benchmarks on each simulation tool
- Compare CPU vs GPU/NPU performance
- Record detailed performance metrics (execution time, CPU, memory, GPU usage)
- Store results for reproducibility and comparison
- Generate benchmark reports

Usage:
    from benchmark import BenchmarkRunner
    
    runner = BenchmarkRunner()
    results = runner.run_benchmark("fenicsx", "poisson.py", device="cpu")
    runner.save_results()
"""

import json
import time
import subprocess
import psutil
import os
import sys
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path
import tempfile

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from job_monitor import JobMonitor


class BenchmarkConfig:
    """Configuration for benchmark runs."""
    
    # Standard benchmark parameters for each tool
    BENCHMARKS = {
        'fenicsx': {
            'script': 'poisson.py',
            'params': {
                'mesh_size': 64,
            },
            'description': 'Poisson equation solver with 64x64 mesh',
        },
        'lammps': {
            'script': 'example.lammps',
            'params': {},
            'description': 'Molecular dynamics simulation',
        },
        'openfoam': {
            'script': 'example_cavity.py',
            'params': {},
            'description': 'Cavity flow CFD simulation',
        },
    }
    
    # Device configurations
    DEVICES = {
        'cpu': {
            'description': 'CPU-only execution',
            'docker_args': [],
            'env': {},
        },
        'gpu': {
            'description': 'NVIDIA GPU acceleration',
            'docker_args': ['--gpus', 'all'],
            'env': {'CUDA_VISIBLE_DEVICES': '0'},
        },
        'intel-gpu': {
            'description': 'Intel GPU/NPU acceleration',
            'docker_args': ['--device', '/dev/dri:/dev/dri'],
            'env': {'ZE_AFFINITY_MASK': '0'},
        },
    }


class BenchmarkRunner:
    """
    Run and record standardized benchmarks for simulation tools.
    
    This class manages benchmark execution, performance monitoring, and
    result storage for reproducibility and comparison.
    
    Example:
        >>> runner = BenchmarkRunner()
        >>> # Run CPU benchmark
        >>> cpu_result = runner.run_benchmark("fenicsx", device="cpu")
        >>> # Run GPU benchmark
        >>> gpu_result = runner.run_benchmark("fenicsx", device="gpu")
        >>> # Compare results
        >>> comparison = runner.compare_results(cpu_result['id'], gpu_result['id'])
        >>> # Save all results
        >>> runner.save_results()
    """
    
    def __init__(self, results_dir: Optional[str] = None):
        """
        Initialize the benchmark runner.
        
        Args:
            results_dir: Directory to store benchmark results (default: /tmp/keystone_benchmarks)
        """
        self.results_dir = Path(results_dir) if results_dir else Path("/tmp/keystone_benchmarks")
        self.results_dir.mkdir(parents=True, exist_ok=True)
        self.results_file = self.results_dir / "benchmark_results.jsonl"
        self.monitor = JobMonitor(log_dir=str(self.results_dir / "job_logs"))
        self.results = []
    
    def run_benchmark(
        self,
        tool: str,
        device: str = "cpu",
        custom_params: Optional[Dict[str, Any]] = None,
        runs: int = 3
    ) -> Dict[str, Any]:
        """
        Run a standardized benchmark for a simulation tool.
        
        Args:
            tool: Simulation tool name (fenicsx, lammps, openfoam)
            device: Device type (cpu, gpu, intel-gpu)
            custom_params: Optional custom parameters (overrides defaults)
            runs: Number of benchmark runs to average (default: 3)
            
        Returns:
            Dictionary with benchmark results including:
            - id: Unique benchmark ID
            - tool: Tool name
            - device: Device type
            - runs: Number of runs
            - metrics: Performance metrics
            - system_info: System information
            
        Example:
            >>> runner = BenchmarkRunner()
            >>> result = runner.run_benchmark("fenicsx", device="cpu", runs=5)
            >>> print(f"Average time: {result['metrics']['avg_duration_seconds']}s")
        """
        # Validate inputs
        if tool not in BenchmarkConfig.BENCHMARKS:
            raise ValueError(f"Unknown tool: {tool}. Available: {list(BenchmarkConfig.BENCHMARKS.keys())}")
        
        if device not in BenchmarkConfig.DEVICES:
            raise ValueError(f"Unknown device: {device}. Available: {list(BenchmarkConfig.DEVICES.keys())}")
        
        # Get benchmark configuration
        bench_config = BenchmarkConfig.BENCHMARKS[tool]
        device_config = BenchmarkConfig.DEVICES[device]
        
        # Prepare parameters
        params = bench_config['params'].copy()
        if custom_params:
            params.update(custom_params)
        
        # Generate unique benchmark ID
        benchmark_id = f"{tool}-{device}-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"
        
        print(f"\n{'='*70}")
        print(f"Running Benchmark: {benchmark_id}")
        print(f"{'='*70}")
        print(f"Tool: {tool}")
        print(f"Device: {device} - {device_config['description']}")
        print(f"Script: {bench_config['script']}")
        print(f"Parameters: {params}")
        print(f"Runs: {runs}")
        print(f"{'='*70}\n")
        
        # Collect system information
        system_info = self._collect_system_info(device)
        
        # Run multiple benchmark iterations
        run_results = []
        for run_num in range(1, runs + 1):
            print(f"Run {run_num}/{runs}...")
            run_result = self._run_single_benchmark(
                tool,
                bench_config['script'],
                params,
                device_config,
                benchmark_id,
                run_num
            )
            run_results.append(run_result)
            
            # Brief pause between runs
            if run_num < runs:
                time.sleep(2)
        
        # Aggregate results
        metrics = self._aggregate_metrics(run_results)
        
        # Prepare final benchmark result
        benchmark_result = {
            'id': benchmark_id,
            'timestamp': datetime.utcnow().isoformat(),
            'tool': tool,
            'device': device,
            'script': bench_config['script'],
            'description': bench_config['description'],
            'params': params,
            'runs': runs,
            'metrics': metrics,
            'system_info': system_info,
            'run_results': run_results,
        }
        
        # Store result
        self.results.append(benchmark_result)
        self._write_result(benchmark_result)
        
        # Print summary
        self._print_benchmark_summary(benchmark_result)
        
        return benchmark_result
    
    def _run_single_benchmark(
        self,
        tool: str,
        script: str,
        params: Dict[str, Any],
        device_config: Dict[str, Any],
        benchmark_id: str,
        run_num: int
    ) -> Dict[str, Any]:
        """Run a single benchmark iteration."""
        task_id = f"{benchmark_id}-run-{run_num}"
        
        # Start monitoring
        self.monitor.start_monitoring(task_id, tool, script, params)
        
        start_time = time.time()
        
        try:
            # Build docker command
            cmd = ['docker', 'compose', 'run', '--rm']
            
            # Add device-specific arguments
            if device_config.get('docker_args'):
                cmd.extend(device_config['docker_args'])
            
            # Specify tool and script
            cmd.extend([tool, script])
            
            # Prepare environment
            env = os.environ.copy()
            env.update(device_config.get('env', {}))
            for key, value in params.items():
                env[f'SIM_{key.upper()}'] = str(value)
            
            # Execute benchmark
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                env=env,
                timeout=600  # 10 minute timeout
            )
            
            end_time = time.time()
            duration = end_time - start_time
            
            # Determine status
            status = 'success' if result.returncode == 0 else 'failed'
            error = result.stderr if result.returncode != 0 else None
            
            # Stop monitoring
            job_stats = self.monitor.stop_monitoring(
                task_id,
                status=status,
                returncode=result.returncode,
                error=error
            )
            
            # Prepare run result
            run_result = {
                'run_num': run_num,
                'status': status,
                'returncode': result.returncode,
                'duration_seconds': round(duration, 3),
                'cpu_user_seconds': job_stats.get('resource_usage', {}).get('cpu_user_seconds', 0),
                'cpu_system_seconds': job_stats.get('resource_usage', {}).get('cpu_system_seconds', 0),
                'cpu_total_seconds': job_stats.get('resource_usage', {}).get('cpu_total_seconds', 0),
                'memory_peak_mb': job_stats.get('resource_usage', {}).get('memory_peak_mb', 0),
                'error': error,
            }
            
            return run_result
            
        except subprocess.TimeoutExpired:
            self.monitor.stop_monitoring(
                task_id,
                status='timeout',
                returncode=-1,
                error='Benchmark timed out'
            )
            return {
                'run_num': run_num,
                'status': 'timeout',
                'returncode': -1,
                'duration_seconds': 600.0,
                'error': 'Benchmark timed out',
            }
        except Exception as e:
            self.monitor.stop_monitoring(
                task_id,
                status='error',
                returncode=-1,
                error=str(e)
            )
            return {
                'run_num': run_num,
                'status': 'error',
                'returncode': -1,
                'duration_seconds': 0.0,
                'error': str(e),
            }
    
    def _aggregate_metrics(self, run_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregate metrics from multiple runs."""
        successful_runs = [r for r in run_results if r['status'] == 'success']
        
        if not successful_runs:
            return {
                'successful_runs': 0,
                'failed_runs': len(run_results),
                'success_rate': 0.0,
            }
        
        durations = [r['duration_seconds'] for r in successful_runs]
        cpu_times = [r.get('cpu_total_seconds', 0) for r in successful_runs]
        memory_peaks = [r.get('memory_peak_mb', 0) for r in successful_runs]
        
        metrics = {
            'successful_runs': len(successful_runs),
            'failed_runs': len(run_results) - len(successful_runs),
            'success_rate': round(len(successful_runs) / len(run_results) * 100, 2),
            'avg_duration_seconds': round(sum(durations) / len(durations), 3),
            'min_duration_seconds': round(min(durations), 3),
            'max_duration_seconds': round(max(durations), 3),
            'avg_cpu_seconds': round(sum(cpu_times) / len(cpu_times), 3),
            'avg_memory_mb': round(sum(memory_peaks) / len(memory_peaks), 2),
            'max_memory_mb': round(max(memory_peaks), 2),
        }
        
        # Calculate standard deviation for duration
        if len(durations) > 1:
            mean_duration = metrics['avg_duration_seconds']
            variance = sum((d - mean_duration) ** 2 for d in durations) / len(durations)
            metrics['std_duration_seconds'] = round(variance ** 0.5, 3)
        else:
            metrics['std_duration_seconds'] = 0.0
        
        return metrics
    
    def _collect_system_info(self, device: str) -> Dict[str, Any]:
        """Collect system information for reproducibility."""
        info = {
            'hostname': os.uname().nodename,
            'os': f"{os.uname().sysname} {os.uname().release}",
            'cpu_count': psutil.cpu_count(logical=False),
            'cpu_count_logical': psutil.cpu_count(logical=True),
            'memory_total_gb': round(psutil.virtual_memory().total / (1024**3), 2),
            'device': device,
        }
        
        # Get CPU model
        try:
            with open('/proc/cpuinfo', 'r') as f:
                for line in f:
                    if 'model name' in line:
                        info['cpu_model'] = line.split(':')[1].strip()
                        break
        except Exception:
            pass
        
        # Get GPU info if applicable
        if device == 'gpu':
            try:
                result = subprocess.run(
                    ['nvidia-smi', '--query-gpu=name,driver_version,memory.total',
                     '--format=csv,noheader'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0 and result.stdout:
                    gpu_data = result.stdout.strip().split(',')
                    info['gpu_name'] = gpu_data[0].strip()
                    info['gpu_driver'] = gpu_data[1].strip()
                    info['gpu_memory_mb'] = gpu_data[2].strip()
            except Exception:
                pass
        
        elif device == 'intel-gpu':
            try:
                result = subprocess.run(
                    ['clinfo'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    info['intel_gpu_available'] = 'Intel' in result.stdout
            except Exception:
                pass
        
        return info
    
    def _write_result(self, result: Dict[str, Any]) -> None:
        """Write benchmark result to file."""
        try:
            with open(self.results_file, 'a') as f:
                f.write(json.dumps(result) + '\n')
        except Exception as e:
            print(f"Warning: Failed to write benchmark result: {e}")
    
    def _print_benchmark_summary(self, result: Dict[str, Any]) -> None:
        """Print a summary of benchmark results."""
        metrics = result['metrics']
        
        print(f"\n{'='*70}")
        print(f"Benchmark Results: {result['id']}")
        print(f"{'='*70}")
        print(f"Tool: {result['tool']}")
        print(f"Device: {result['device']}")
        print(f"Success Rate: {metrics['success_rate']}% ({metrics['successful_runs']}/{result['runs']} runs)")
        print(f"\nPerformance Metrics:")
        print(f"  Average Duration: {metrics['avg_duration_seconds']}s")
        print(f"  Min Duration: {metrics['min_duration_seconds']}s")
        print(f"  Max Duration: {metrics['max_duration_seconds']}s")
        if metrics.get('std_duration_seconds'):
            print(f"  Std Deviation: {metrics['std_duration_seconds']}s")
        print(f"  Average CPU Time: {metrics['avg_cpu_seconds']}s")
        print(f"  Average Memory: {metrics['avg_memory_mb']} MB")
        print(f"  Peak Memory: {metrics['max_memory_mb']} MB")
        print(f"{'='*70}\n")
    
    def load_results(self) -> List[Dict[str, Any]]:
        """
        Load all benchmark results from file.
        
        Returns:
            List of benchmark result dictionaries
        """
        if not self.results_file.exists():
            return []
        
        results = []
        try:
            with open(self.results_file, 'r') as f:
                for line in f:
                    if line.strip():
                        results.append(json.loads(line))
        except Exception as e:
            print(f"Warning: Failed to load benchmark results: {e}")
            return []
        
        self.results = results
        return results
    
    def compare_results(
        self,
        baseline_id: str,
        comparison_id: str
    ) -> Dict[str, Any]:
        """
        Compare two benchmark results.
        
        Args:
            baseline_id: Benchmark ID for baseline
            comparison_id: Benchmark ID to compare against baseline
            
        Returns:
            Dictionary with comparison metrics including speedup
            
        Example:
            >>> comparison = runner.compare_results("fenicsx-cpu-...", "fenicsx-gpu-...")
            >>> print(f"Speedup: {comparison['speedup']}x")
        """
        # Load all results if not already loaded
        if not self.results:
            self.load_results()
        
        # Find the benchmarks
        baseline = None
        comparison = None
        
        for result in self.results:
            if result['id'] == baseline_id:
                baseline = result
            if result['id'] == comparison_id:
                comparison = result
        
        if not baseline:
            raise ValueError(f"Baseline benchmark not found: {baseline_id}")
        if not comparison:
            raise ValueError(f"Comparison benchmark not found: {comparison_id}")
        
        # Calculate comparison metrics
        baseline_duration = baseline['metrics']['avg_duration_seconds']
        comparison_duration = comparison['metrics']['avg_duration_seconds']
        
        speedup = baseline_duration / comparison_duration if comparison_duration > 0 else 0
        time_saved = baseline_duration - comparison_duration
        percent_change = ((comparison_duration - baseline_duration) / baseline_duration * 100) if baseline_duration > 0 else 0
        
        comparison_result = {
            'baseline_id': baseline_id,
            'comparison_id': comparison_id,
            'baseline_device': baseline['device'],
            'comparison_device': comparison['device'],
            'baseline_duration': baseline_duration,
            'comparison_duration': comparison_duration,
            'speedup': round(speedup, 2),
            'time_saved_seconds': round(time_saved, 3),
            'percent_change': round(percent_change, 2),
            'baseline_memory_mb': baseline['metrics']['avg_memory_mb'],
            'comparison_memory_mb': comparison['metrics']['avg_memory_mb'],
        }
        
        # Print comparison
        print(f"\n{'='*70}")
        print(f"Benchmark Comparison")
        print(f"{'='*70}")
        print(f"Baseline: {baseline_id}")
        print(f"  Device: {baseline['device']}")
        print(f"  Duration: {baseline_duration}s")
        print(f"  Memory: {baseline['metrics']['avg_memory_mb']} MB")
        print(f"\nComparison: {comparison_id}")
        print(f"  Device: {comparison['device']}")
        print(f"  Duration: {comparison_duration}s")
        print(f"  Memory: {comparison['metrics']['avg_memory_mb']} MB")
        print(f"\nResults:")
        print(f"  Speedup: {comparison_result['speedup']}x")
        print(f"  Time Saved: {comparison_result['time_saved_seconds']}s")
        print(f"  Performance Change: {comparison_result['percent_change']:+.2f}%")
        print(f"{'='*70}\n")
        
        return comparison_result
    
    def generate_report(self, output_file: Optional[str] = None) -> str:
        """
        Generate a markdown report of all benchmark results.
        
        Args:
            output_file: Optional file path to save report
            
        Returns:
            Markdown report as string
        """
        # Load all results
        if not self.results:
            self.load_results()
        
        if not self.results:
            return "No benchmark results available."
        
        # Group results by tool
        by_tool = {}
        for result in self.results:
            tool = result['tool']
            if tool not in by_tool:
                by_tool[tool] = []
            by_tool[tool].append(result)
        
        # Generate report
        report_lines = [
            "# Keystone Supercomputer Benchmark Results",
            "",
            f"Generated: {datetime.utcnow().isoformat()}",
            "",
            "## Overview",
            "",
            f"Total Benchmarks: {len(self.results)}",
            f"Tools Tested: {', '.join(by_tool.keys())}",
            "",
        ]
        
        # Add results for each tool
        for tool, tool_results in by_tool.items():
            report_lines.extend([
                f"## {tool.upper()}",
                "",
            ])
            
            for result in tool_results:
                metrics = result['metrics']
                report_lines.extend([
                    f"### {result['id']}",
                    "",
                    f"**Configuration:**",
                    f"- Device: {result['device']}",
                    f"- Script: {result['script']}",
                    f"- Description: {result['description']}",
                    f"- Parameters: `{json.dumps(result['params'])}`",
                    f"- Runs: {result['runs']}",
                    "",
                    f"**Performance Metrics:**",
                    f"- Success Rate: {metrics['success_rate']}%",
                    f"- Average Duration: {metrics['avg_duration_seconds']}s",
                    f"- Min/Max Duration: {metrics['min_duration_seconds']}s / {metrics['max_duration_seconds']}s",
                    f"- Average CPU Time: {metrics['avg_cpu_seconds']}s",
                    f"- Average Memory: {metrics['avg_memory_mb']} MB",
                    f"- Peak Memory: {metrics['max_memory_mb']} MB",
                    "",
                    f"**System Information:**",
                ])
                
                for key, value in result['system_info'].items():
                    report_lines.append(f"- {key}: {value}")
                
                report_lines.append("")
        
        report = "\n".join(report_lines)
        
        # Save to file if requested
        if output_file:
            output_path = Path(output_file)
            output_path.write_text(report)
            print(f"✓ Report saved to: {output_path}")
        
        return report
    
    def save_results(self, output_file: Optional[str] = None) -> None:
        """
        Save all benchmark results to a JSON file.
        
        Args:
            output_file: Optional file path (default: benchmark_results_summary.json)
        """
        if not output_file:
            output_file = str(self.results_dir / "benchmark_results_summary.json")
        
        output_path = Path(output_file)
        
        # Load all results if not loaded
        if not self.results:
            self.load_results()
        
        # Save as JSON
        with open(output_path, 'w') as f:
            json.dump({
                'timestamp': datetime.utcnow().isoformat(),
                'total_benchmarks': len(self.results),
                'results': self.results,
            }, f, indent=2)
        
        print(f"✓ Results saved to: {output_path}")


def main():
    """Command-line interface for benchmark runner."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Keystone Supercomputer Benchmark Runner"
    )
    parser.add_argument(
        '--tool',
        type=str,
        choices=['fenicsx', 'lammps', 'openfoam', 'all'],
        default='all',
        help='Simulation tool to benchmark'
    )
    parser.add_argument(
        '--device',
        type=str,
        choices=['cpu', 'gpu', 'intel-gpu', 'all'],
        default='cpu',
        help='Device type for benchmark'
    )
    parser.add_argument(
        '--runs',
        type=int,
        default=3,
        help='Number of benchmark runs (default: 3)'
    )
    parser.add_argument(
        '--compare',
        type=str,
        nargs=2,
        metavar=('BASELINE_ID', 'COMPARISON_ID'),
        help='Compare two benchmark results'
    )
    parser.add_argument(
        '--report',
        action='store_true',
        help='Generate benchmark report'
    )
    parser.add_argument(
        '--results-dir',
        type=str,
        help='Directory for benchmark results'
    )
    
    args = parser.parse_args()
    
    # Create runner
    runner = BenchmarkRunner(results_dir=args.results_dir)
    
    # Handle comparison mode
    if args.compare:
        runner.load_results()
        runner.compare_results(args.compare[0], args.compare[1])
        return
    
    # Handle report generation
    if args.report:
        report = runner.generate_report(
            output_file=str(runner.results_dir / "BENCHMARK_REPORT.md")
        )
        print(report)
        return
    
    # Run benchmarks
    tools = ['fenicsx', 'lammps', 'openfoam'] if args.tool == 'all' else [args.tool]
    devices = ['cpu', 'gpu', 'intel-gpu'] if args.device == 'all' else [args.device]
    
    for tool in tools:
        for device in devices:
            try:
                runner.run_benchmark(tool, device=device, runs=args.runs)
            except Exception as e:
                print(f"✗ Benchmark failed for {tool} on {device}: {e}")
    
    # Generate summary
    runner.save_results()
    print("\n✓ All benchmarks completed!")
    print(f"✓ Results saved to: {runner.results_dir}")


if __name__ == '__main__':
    main()
