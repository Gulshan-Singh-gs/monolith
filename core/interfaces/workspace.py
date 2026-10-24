"""
core/interfaces/workspace.py
Abstract contracts for authorized workspace filesystem access, diff generation, and sandboxed command execution.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from pathlib import Path
from pydantic import BaseModel, Field


class WorkspaceFileMeta(BaseModel):
    relative_path: str
    absolute_path: str
    size_bytes: int
    is_dir: bool
    modified_at: float
    sha256_hash: Optional[str] = None


class CommandExecutionResult(BaseModel):
    command: str
    exit_code: int
    stdout: str
    stderr: str
    duration_seconds: float
    timed_out: bool = False


class IWorkspaceEngine(ABC):
    @abstractmethod
    def set_root(self, root_dir: Path) -> bool:
        """Sets and authorizes the workspace root directory."""
        pass

    @abstractmethod
    def get_root(self) -> Path:
        """Returns the authorized canonical workspace root path."""
        pass

    @abstractmethod
    def list_files(self, sub_dir: str = "") -> List[WorkspaceFileMeta]:
        """Lists files within authorized workspace root."""
        pass

    @abstractmethod
    def read_file(self, relative_path: str) -> str:
        """Reads file contents within authorized workspace root, preventing path traversal."""
        pass

    @abstractmethod
    def write_file(self, relative_path: str, content: str) -> bool:
        """Safely writes file contents within authorized workspace root."""
        pass

    @abstractmethod
    async def run_command(
        self,
        command: str,
        timeout_seconds: float = 30.0,
        env_vars: Optional[Dict[str, str]] = None
    ) -> CommandExecutionResult:
        """Executes a permitted terminal command confined strictly to the workspace root."""
        pass
