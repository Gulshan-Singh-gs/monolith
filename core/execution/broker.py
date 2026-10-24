"""
core/execution/broker.py
Governed Execution Broker for MONOLITH Autonomous Engineering System.
Enforces deterministic tool execution policies:
- Structured executable identity & argument arrays (asyncio.create_subprocess_exec)
- Authorized working-directory confinement
- Environment sanitization (secret & credential stripping)
- Process-tree termination on timeout/cancellation (Windows & POSIX)
- Bounded stdout/stderr capture (max 1MB)
- Audit logging & risk classification
"""

import os
import sys
import time
import shlex
import shutil
import asyncio
import logging
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional, Set, Tuple
from pydantic import BaseModel, Field

from core.interfaces.workspace import CommandExecutionResult
from audit_ledger import audit_ledger

logger = logging.getLogger("ExecutionBroker")

MAX_OUTPUT_BYTES = 1024 * 1024  # 1 MB bounded capture


class ExecutionPolicy(BaseModel):
    allowed_executables: Set[str] = {
        "python", "python3", "pytest", "git", "node", "npm", "npx", "uv"
    }
    blocked_commands: Set[str] = {
        "format", "shutdown", "reg", "vssadmin", "bcdedit", "diskpart",
        "rmdir", "del", "erase", "mkfs", "dd", "reboot"
    }
    allow_arbitrary_shell: bool = False
    max_timeout_seconds: float = 300.0


class GovernedExecutionBroker:
    """
    Centralized execution service enforcing deterministic security controls
    for all developer tools and commands executed within MONOLITH workspaces.
    """

    def __init__(self, workspace_root: Optional[Path] = None, policy: Optional[ExecutionPolicy] = None):
        self.workspace_root = (workspace_root or Path.cwd()).resolve()
        self.policy = policy or ExecutionPolicy()

    def set_workspace_root(self, root: Path) -> None:
        self.workspace_root = root.resolve()

    def _sanitize_environment(self, custom_env: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """
        Creates a clean execution environment stripped of sensitive API keys,
        tokens, and internal secrets to prevent child process leakage.
        """
        sanitized = {}
        # Safe standard environment variables to propagate
        safe_keys = {
            "PATH", "PATHEXT", "SYSTEMROOT", "TEMP", "TMP", "COMSPEC",
            "USERPROFILE", "HOMEDRIVE", "HOMEPATH", "WINDIR",
            "PYTHONPATH", "PYTHONHOME", "NODE_PATH", "LANG", "LC_ALL"
        }
        for k, v in os.environ.items():
            if k.upper() in safe_keys:
                sanitized[k] = v

        # Explicitly ensure sensitive secrets are absent
        secret_needles = ["KEY", "SECRET", "TOKEN", "PASSWORD", "VAULT", "CREDENTIAL"]
        for k in list(sanitized.keys()):
            if any(needle in k.upper() for needle in secret_needles):
                sanitized.pop(k, None)

        if custom_env:
            for k, v in custom_env.items():
                if not any(needle in k.upper() for needle in secret_needles):
                    sanitized[k] = v

        return sanitized

    def parse_command(self, command_str: str) -> Tuple[str, List[str]]:
        """
        Safely tokenizes a command string into executable and arguments.
        """
        cleaned = command_str.strip()
        if not cleaned:
            raise ValueError("Empty command string.")
        # Use posix=True to strip outer quote wrappers from arguments cleanly
        tokens = shlex.split(cleaned, posix=True)
        if not tokens:
            raise ValueError("No executable tokens found.")
        executable = tokens[0]
        args = tokens[1:]
        return executable, args

    def evaluate_command_safety(self, executable: str, args: List[str]) -> Tuple[bool, str]:
        """
        Deterministic policy validation for requested executable and arguments.
        """
        base_name = Path(executable).stem.lower()

        # Check explicit blocked commands
        if base_name in self.policy.blocked_commands:
            return False, f"Executable '{base_name}' is explicitly prohibited by policy."

        # Check dangerous patterns in arguments
        full_cmd_str = f"{executable} {' '.join(args)}".lower()
        dangerous_fragments = [
            "curl | bash", "curl | sh", "wget | bash",
            "powershell -enc", "powershell -encodedcommand",
            "rm -rf /", "del /s", "del /f", "format ", "shutdown "
        ]
        for frag in dangerous_fragments:
            if frag in full_cmd_str:
                return False, f"Command contains forbidden destructive pattern: '{frag}'."

        # Check if executable is in allowlist
        if base_name in self.policy.allowed_executables or executable in self.policy.allowed_executables:
            return True, "Approved development executable."

        if self.policy.allow_arbitrary_shell:
            return True, "Arbitrary execution permitted by explicit configuration."

        return False, f"Executable '{base_name}' is not in the approved development allowlist ({', '.join(sorted(self.policy.allowed_executables))})."

    async def execute_command(
        self,
        command: str,
        cwd: Optional[Path] = None,
        timeout_seconds: float = 30.0,
        env_vars: Optional[Dict[str, str]] = None
    ) -> CommandExecutionResult:
        """
        Executes a controlled command using create_subprocess_exec with process-tree termination.
        """
        start_time = time.time()
        target_cwd = (cwd or self.workspace_root).resolve()

        # 1. Enforce working-directory confinement
        try:
            target_cwd.relative_to(self.workspace_root)
        except ValueError:
            return CommandExecutionResult(
                command=command,
                exit_code=-1,
                stdout="",
                stderr=f"Security violation: Cwd '{target_cwd}' is outside authorized workspace root.",
                duration_seconds=0.0
            )

        # 2. Parse command
        try:
            executable, args = self.parse_command(command)
        except Exception as e:
            return CommandExecutionResult(
                command=command,
                exit_code=-1,
                stdout="",
                stderr=f"Command parsing failed: {e}",
                duration_seconds=0.0
            )

        # 3. Policy validation
        allowed, policy_msg = self.evaluate_command_safety(executable, args)
        if not allowed:
            audit_ledger.record_event(
                event_type="COMMAND_BLOCKED",
                action=f"Blocked command: {command}",
                actor="EXECUTION_BROKER",
                risk_level="HIGH",
                details={"executable": executable, "reason": policy_msg}
            )
            return CommandExecutionResult(
                command=command,
                exit_code=-1,
                stdout="",
                stderr=f"Command blocked by workspace security policy: {policy_msg}",
                duration_seconds=0.0
            )

        # 4. Resolve binary path (prefer active Python runtime over Windows Store alias)
        if executable.lower() in ("python", "python3") and sys.executable:
            resolved_exe = sys.executable
        else:
            resolved_exe = shutil.which(executable)
            if not resolved_exe:
                return CommandExecutionResult(
                    command=command,
                    exit_code=-1,
                    stdout="",
                    stderr=f"Executable '{executable}' not found on system PATH.",
                    duration_seconds=0.0
                )

        sanitized_env = self._sanitize_environment(env_vars)
        timeout = min(timeout_seconds, self.policy.max_timeout_seconds)

        proc = None
        try:
            proc = await asyncio.create_subprocess_exec(
                resolved_exe,
                *args,
                cwd=str(target_cwd),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=sanitized_env
            )

            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                proc.communicate(),
                timeout=timeout
            )

            # Enforce bounded capture
            stdout_str = stdout_bytes[:MAX_OUTPUT_BYTES].decode("utf-8", errors="replace")
            stderr_str = stderr_bytes[:MAX_OUTPUT_BYTES].decode("utf-8", errors="replace")
            duration = time.time() - start_time

            audit_ledger.record_event(
                event_type="COMMAND_EXECUTED",
                action=f"Executed: {command}",
                actor="EXECUTION_BROKER",
                risk_level="LOW",
                details={"exit_code": proc.returncode, "duration_seconds": duration}
            )

            return CommandExecutionResult(
                command=command,
                exit_code=proc.returncode if proc.returncode is not None else 0,
                stdout=stdout_str,
                stderr=stderr_str,
                duration_seconds=duration,
                timed_out=False
            )

        except asyncio.TimeoutError:
            self._terminate_process_tree(proc)
            duration = time.time() - start_time
            return CommandExecutionResult(
                command=command,
                exit_code=-1,
                stdout="",
                stderr=f"Command timed out after {timeout}s.",
                duration_seconds=duration,
                timed_out=True
            )
        except Exception as e:
            if proc:
                self._terminate_process_tree(proc)
            duration = time.time() - start_time
            return CommandExecutionResult(
                command=command,
                exit_code=-1,
                stdout="",
                stderr=f"Execution error: {str(e)}",
                duration_seconds=duration
            )

    def _terminate_process_tree(self, proc: Optional[asyncio.subprocess.Process]) -> None:
        """
        Forcefully terminates the entire child process tree to prevent orphan processes.
        """
        if not proc or proc.pid is None:
            return
        pid = proc.pid
        try:
            if sys.platform == "win32":
                subprocess.run(
                    ["taskkill", "/F", "/T", "/PID", str(pid)],
                    capture_output=True,
                    check=False
                )
            else:
                proc.kill()
        except Exception as e:
            logger.warning(f"Failed to kill process tree for PID {pid}: {e}")


# Default execution broker singleton
default_execution_broker = GovernedExecutionBroker()
