"""
core/workspace/engine.py
Production-ready Workspace Engine implementing safe canonical path resolution,
symlink escape defense, diff inspection, and bounded terminal execution.
"""

import os
import re
import time
import asyncio
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional

from core.interfaces.workspace import (
    IWorkspaceEngine,
    WorkspaceFileMeta,
    CommandExecutionResult
)
from core.execution.broker import GovernedExecutionBroker


class SecureWorkspaceEngine(IWorkspaceEngine):
    def __init__(self, initial_root: Optional[Path] = None):
        self.root_path: Path = (initial_root or Path.cwd()).resolve()
        self.execution_broker = GovernedExecutionBroker(workspace_root=self.root_path)

    def set_root(self, root_dir: Path) -> bool:
        resolved = Path(root_dir).resolve()
        if not resolved.exists() or not resolved.is_dir():
            return False
        self.root_path = resolved
        self.execution_broker.set_workspace_root(self.root_path)
        return True

    def get_root(self) -> Path:
        return self.root_path

    def _resolve_safe_path(self, relative_path: str) -> Path:
        """
        Canonical path resolution preventing directory traversal and symlink escapes.
        Raises PermissionError if path resolves outside the authorized workspace root.
        """
        cleaned = relative_path.strip()
        path_obj = Path(cleaned)

        if path_obj.is_absolute() or cleaned.startswith(("/", "\\")):
            candidate = path_obj.resolve()
        else:
            candidate = (self.root_path / cleaned).resolve()

        # Verify candidate is strictly inside self.root_path
        try:
            candidate.relative_to(self.root_path)
        except ValueError:
            raise PermissionError(f"Access denied: Path '{relative_path}' escapes authorized workspace root.")
        return candidate

    def list_files(self, sub_dir: str = "") -> List[WorkspaceFileMeta]:
        target_dir = self._resolve_safe_path(sub_dir) if sub_dir else self.root_path
        if not target_dir.is_dir():
            return []

        results: List[WorkspaceFileMeta] = []
        ignored_names = {".git", ".vault", "__pycache__", "node_modules", ".pytest_cache", ".venv", "graft"}

        for root, dirs, files in os.walk(target_dir):
            dirs[:] = [d for d in dirs if d not in ignored_names and not d.startswith(".")]
            for f in files:
                p = Path(root) / f
                try:
                    rel_p = str(p.relative_to(self.root_path)).replace("\\", "/")
                    stat = p.stat()
                    results.append(WorkspaceFileMeta(
                        relative_path=rel_p,
                        absolute_path=str(p),
                        size_bytes=stat.st_size,
                        is_dir=False,
                        modified_at=stat.st_mtime
                    ))
                except Exception:
                    continue
        return results

    def read_file(self, relative_path: str) -> str:
        safe_path = self._resolve_safe_path(relative_path)
        if not safe_path.exists() or not safe_path.is_file():
            raise FileNotFoundError(f"File '{relative_path}' not found in workspace.")
        return safe_path.read_text(encoding="utf-8", errors="replace")

    def write_file(self, relative_path: str, content: str) -> bool:
        safe_path = self._resolve_safe_path(relative_path)
        safe_path.parent.mkdir(parents=True, exist_ok=True)
        # Atomic write via temp file
        temp_file = safe_path.with_suffix(".tmp_write")
        temp_file.write_text(content, encoding="utf-8")
        temp_file.replace(safe_path)
        return True

    async def run_command(
        self,
        command: str,
        timeout_seconds: float = 30.0,
        env_vars: Optional[Dict[str, str]] = None
    ) -> CommandExecutionResult:
        """
        Executes a controlled command strictly inside the workspace root
        via the GovernedExecutionBroker with process-tree cleanup and policy enforcement.
        """
        return await self.execution_broker.execute_command(
            command=command,
            cwd=self.root_path,
            timeout_seconds=timeout_seconds,
            env_vars=env_vars
        )
