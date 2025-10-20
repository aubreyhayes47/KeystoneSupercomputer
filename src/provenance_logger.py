"""
Provenance Logging System for Keystone Supercomputer
=====================================================

This module provides automated provenance tracking for all simulation runs,
ensuring reproducibility and audit capability.

Features:
- Comprehensive metadata capture (user prompt, workflow plan, tool calls, parameters)
- Software and library version tracking
- Runtime environment variable capture
- Random seed tracking
- Input/output file linking
- Complete workflow provenance chain
- Reproducibility-focused schema

Example:
    >>> from provenance_logger import ProvenanceLogger
    >>> logger = ProvenanceLogger()
    >>> 
    >>> # Start tracking a workflow
    >>> prov_id = logger.start_workflow(
    ...     user_prompt="Run FEA on steel beam",
    ...     workflow_plan={"tool": "fenicsx", "script": "poisson.py"}
    ... )
    >>> 
    >>> # Record tool execution
    >>> logger.record_tool_call(prov_id, tool="fenicsx", parameters={"mesh_size": 64})
    >>> 
    >>> # Finalize and save
    >>> logger.finalize_workflow(prov_id, output_files=["results.vtk"])
"""

import json
import os
import sys
import time
import platform
import hashlib
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
from pathlib import Path
import threading


class ProvenanceLogger:
    """
    Automated provenance logging for simulation workflows.
    
    This class captures comprehensive metadata for every simulation run,
    including workflow plans, tool calls, environment state, and artifact links.
    """
    
    def __init__(self, log_dir: Optional[str] = None):
        """
        Initialize the provenance logger.
        
        Args:
            log_dir: Directory to store provenance files (default: /tmp/keystone_provenance)
        """
        self.log_dir = Path(log_dir) if log_dir else Path("/tmp/keystone_provenance")
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self._active_workflows = {}
        self._lock = threading.Lock()
        
    def start_workflow(
        self,
        user_prompt: str,
        workflow_plan: Optional[Dict[str, Any]] = None,
        workflow_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Start tracking a new workflow execution.
        
        Args:
            user_prompt: Original user request or prompt
            workflow_plan: Planned execution strategy
            workflow_id: Optional unique identifier (generated if not provided)
            metadata: Additional metadata to include
            
        Returns:
            Unique workflow identifier (provenance ID)
        """
        if workflow_id is None:
            workflow_id = self._generate_workflow_id(user_prompt)
        
        # Initialize provenance record
        provenance = {
            "provenance_version": "1.0.0",
            "workflow_id": workflow_id,
            "created_at": datetime.utcnow().isoformat() + "Z",
            "user_prompt": user_prompt,
            "workflow_plan": workflow_plan or {},
            "tool_calls": [],
            "software_versions": self._capture_software_versions(),
            "environment": self._capture_environment(),
            "random_seeds": self._capture_random_seeds(),
            "input_files": [],
            "output_files": [],
            "execution_timeline": [
                {
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "event": "workflow_started",
                    "details": {}
                }
            ],
            "status": "running",
            "metadata": metadata or {}
        }
        
        with self._lock:
            self._active_workflows[workflow_id] = provenance
            
        return workflow_id
    
    def record_tool_call(
        self,
        workflow_id: str,
        tool: str,
        parameters: Dict[str, Any],
        script: Optional[str] = None,
        task_id: Optional[str] = None
    ) -> None:
        """
        Record a tool call as part of the workflow.
        
        Args:
            workflow_id: Workflow identifier
            tool: Tool name (fenicsx, lammps, openfoam, etc.)
            parameters: Tool parameters
            script: Script being executed
            task_id: Optional task identifier
        """
        tool_call = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "tool": tool,
            "script": script,
            "parameters": parameters,
            "task_id": task_id
        }
        
        with self._lock:
            if workflow_id in self._active_workflows:
                self._active_workflows[workflow_id]["tool_calls"].append(tool_call)
                self._active_workflows[workflow_id]["execution_timeline"].append({
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "event": "tool_call",
                    "details": {"tool": tool, "task_id": task_id}
                })
    
    def record_agent_action(
        self,
        workflow_id: str,
        agent_role: str,
        action: str,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Record an agent action in the workflow.
        
        Args:
            workflow_id: Workflow identifier
            agent_role: Role of the agent (conductor, performer, validator)
            action: Action performed
            details: Additional details about the action
        """
        event = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "event": "agent_action",
            "details": {
                "agent_role": agent_role,
                "action": action,
                **(details or {})
            }
        }
        
        with self._lock:
            if workflow_id in self._active_workflows:
                self._active_workflows[workflow_id]["execution_timeline"].append(event)
    
    def add_input_file(
        self,
        workflow_id: str,
        filepath: Union[str, Path],
        description: Optional[str] = None
    ) -> None:
        """
        Link an input file to the workflow provenance.
        
        Args:
            workflow_id: Workflow identifier
            filepath: Path to input file
            description: Optional description of the file
        """
        filepath = Path(filepath)
        
        file_info = {
            "path": str(filepath.absolute()),
            "filename": filepath.name,
            "description": description,
            "added_at": datetime.utcnow().isoformat() + "Z"
        }
        
        # Add checksum if file exists
        if filepath.exists():
            file_info["checksum"] = self._calculate_checksum(filepath)
            file_info["size_bytes"] = filepath.stat().st_size
        
        with self._lock:
            if workflow_id in self._active_workflows:
                self._active_workflows[workflow_id]["input_files"].append(file_info)
    
    def add_output_file(
        self,
        workflow_id: str,
        filepath: Union[str, Path],
        description: Optional[str] = None
    ) -> None:
        """
        Link an output file to the workflow provenance.
        
        Args:
            workflow_id: Workflow identifier
            filepath: Path to output file
            description: Optional description of the file
        """
        filepath = Path(filepath)
        
        file_info = {
            "path": str(filepath.absolute()),
            "filename": filepath.name,
            "description": description,
            "created_at": datetime.utcnow().isoformat() + "Z"
        }
        
        # Add checksum if file exists
        if filepath.exists():
            file_info["checksum"] = self._calculate_checksum(filepath)
            file_info["size_bytes"] = filepath.stat().st_size
        
        with self._lock:
            if workflow_id in self._active_workflows:
                self._active_workflows[workflow_id]["output_files"].append(file_info)
    
    def finalize_workflow(
        self,
        workflow_id: str,
        status: str = "completed",
        final_result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ) -> Path:
        """
        Finalize workflow tracking and save provenance.json.
        
        Args:
            workflow_id: Workflow identifier
            status: Final status (completed, failed, timeout)
            final_result: Final workflow result
            error: Error message if failed
            
        Returns:
            Path to saved provenance.json file
        """
        with self._lock:
            if workflow_id not in self._active_workflows:
                raise ValueError(f"Workflow {workflow_id} not found in active workflows")
            
            provenance = self._active_workflows[workflow_id]
            provenance["status"] = status
            provenance["completed_at"] = datetime.utcnow().isoformat() + "Z"
            
            if final_result:
                provenance["final_result"] = final_result
            
            if error:
                provenance["error"] = error
            
            # Add final timeline event
            provenance["execution_timeline"].append({
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "event": "workflow_completed",
                "details": {"status": status}
            })
            
            # Calculate duration
            start_time = datetime.fromisoformat(provenance["created_at"].replace("Z", ""))
            end_time = datetime.fromisoformat(provenance["completed_at"].replace("Z", ""))
            provenance["duration_seconds"] = (end_time - start_time).total_seconds()
            
            # Save to file
            provenance_file = self.log_dir / f"provenance_{workflow_id}.json"
            with open(provenance_file, 'w') as f:
                json.dump(provenance, f, indent=2)
            
            # Remove from active workflows
            del self._active_workflows[workflow_id]
            
        return provenance_file
    
    def get_provenance(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve provenance record for a workflow.
        
        Args:
            workflow_id: Workflow identifier
            
        Returns:
            Provenance dictionary or None if not found
        """
        # Check active workflows first
        with self._lock:
            if workflow_id in self._active_workflows:
                return self._active_workflows[workflow_id].copy()
        
        # Check saved files
        provenance_file = self.log_dir / f"provenance_{workflow_id}.json"
        if provenance_file.exists():
            with open(provenance_file, 'r') as f:
                return json.load(f)
        
        return None
    
    def list_workflows(
        self,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        List workflow provenance records.
        
        Args:
            status: Filter by status (completed, failed, running)
            limit: Maximum number of records to return
            
        Returns:
            List of provenance summaries
        """
        workflows = []
        
        # Get all provenance files
        for provenance_file in sorted(self.log_dir.glob("provenance_*.json"), reverse=True):
            if len(workflows) >= limit:
                break
            
            try:
                with open(provenance_file, 'r') as f:
                    prov = json.load(f)
                    
                if status is None or prov.get("status") == status:
                    workflows.append({
                        "workflow_id": prov["workflow_id"],
                        "created_at": prov["created_at"],
                        "status": prov["status"],
                        "user_prompt": prov["user_prompt"],
                        "tool_calls_count": len(prov.get("tool_calls", []))
                    })
            except Exception:
                continue
        
        return workflows
    
    def _generate_workflow_id(self, user_prompt: str) -> str:
        """Generate a unique workflow identifier."""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
        prompt_hash = hashlib.md5(user_prompt.encode()).hexdigest()[:8]
        return f"{timestamp}_{prompt_hash}"
    
    def _capture_software_versions(self) -> Dict[str, str]:
        """Capture versions of key software components."""
        versions = {
            "python": sys.version,
            "platform": platform.platform(),
        }
        
        # Try to capture package versions
        try:
            import celery
            versions["celery"] = celery.__version__
        except ImportError:
            pass
        
        try:
            import redis
            versions["redis"] = redis.__version__
        except ImportError:
            pass
        
        try:
            import psutil
            versions["psutil"] = psutil.__version__
        except ImportError:
            pass
        
        try:
            from langchain_core import __version__ as langchain_version
            versions["langchain_core"] = langchain_version
        except ImportError:
            pass
        
        try:
            from langgraph import __version__ as langgraph_version
            versions["langgraph"] = langgraph_version
        except ImportError:
            pass
        
        return versions
    
    def _capture_environment(self) -> Dict[str, Any]:
        """Capture runtime environment variables and system information."""
        env = {
            "hostname": platform.node(),
            "processor": platform.processor(),
            "python_executable": sys.executable,
            "working_directory": os.getcwd(),
            "user": os.getenv("USER", "unknown"),
            "environment_variables": {}
        }
        
        # Capture relevant environment variables (not secrets)
        safe_env_vars = [
            "CELERY_BROKER_URL", "CELERY_RESULT_BACKEND",
            "PATH", "PYTHONPATH",
            "OMP_NUM_THREADS", "MPI_NUM_PROCESSES",
            "CUDA_VISIBLE_DEVICES"
        ]
        
        for var in safe_env_vars:
            value = os.getenv(var)
            if value:
                # Redact sensitive parts of URLs
                if "URL" in var or "BACKEND" in var:
                    env["environment_variables"][var] = self._redact_url(value)
                else:
                    env["environment_variables"][var] = value
        
        return env
    
    def _capture_random_seeds(self) -> Dict[str, Any]:
        """Capture random seeds for reproducibility."""
        import random
        
        seeds = {}
        
        try:
            # Python random state
            state = random.getstate()
            # state[1] is a tuple, convert first 10 values to list
            seeds["python_random_state"] = list(state[1][:10])
        except Exception:
            pass
        
        # Try to capture numpy random state if available
        try:
            import numpy as np
            seeds["numpy_random_state_type"] = str(type(np.random.get_state()[0]))
        except ImportError:
            pass
        except Exception:
            pass
        
        return seeds
    
    def _calculate_checksum(self, filepath: Path) -> str:
        """Calculate SHA256 checksum of a file."""
        sha256_hash = hashlib.sha256()
        with open(filepath, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def _redact_url(self, url: str) -> str:
        """Redact sensitive information from URLs."""
        # Simple redaction: hide password if present
        if "@" in url:
            parts = url.split("@")
            if "://" in parts[0]:
                protocol_user = parts[0].split("://")
                if ":" in protocol_user[1]:
                    protocol, userpass = protocol_user[0], protocol_user[1]
                    user = userpass.split(":")[0]
                    return f"{protocol}://{user}:***@{parts[1]}"
        return url


# Global singleton instance
_global_logger: Optional[ProvenanceLogger] = None
_global_logger_lock = threading.Lock()


def get_provenance_logger() -> ProvenanceLogger:
    """
    Get the global provenance logger instance.
    
    Returns:
        Global ProvenanceLogger instance
    """
    global _global_logger
    
    if _global_logger is None:
        with _global_logger_lock:
            if _global_logger is None:
                _global_logger = ProvenanceLogger()
    
    return _global_logger
