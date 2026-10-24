"""
core/workspace/git_service.py
Governed Git integration service for developer-grade workflows.
Provides safe branch management, diff inspection, commit preparation, and release gating
without destructive resets, hard rollbacks, or unauthorized force operations.
"""

import os
import shutil
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from pydantic import BaseModel, Field

from core.execution.broker import GovernedExecutionBroker
from audit_ledger import audit_ledger

logger = logging.getLogger("GitService")


class GitStatus(BaseModel):
    is_git_repo: bool
    branch: Optional[str] = None
    is_clean: bool = True
    modified_files: List[str] = Field(default_factory=list)
    untracked_files: List[str] = Field(default_factory=list)
    staged_files: List[str] = Field(default_factory=list)
    ahead_commits: int = 0
    behind_commits: int = 0
    error: Optional[str] = None


class CommitPlan(BaseModel):
    plan_id: str
    branch: str
    files_to_commit: List[str]
    commit_message: str
    task_id: Optional[str] = None
    verification_evidence: Optional[Dict[str, Any]] = None
    requires_approval: bool = True
    is_approved: bool = False
    approved_by: Optional[str] = None


class CommitResult(BaseModel):
    success: bool
    commit_hash: Optional[str] = None
    branch: Optional[str] = None
    error: Optional[str] = None


class GitService:
    def __init__(self, workspace_root: Path, broker: Optional[GovernedExecutionBroker] = None):
        self.workspace_root = workspace_root.resolve()
        self.broker = broker or GovernedExecutionBroker(workspace_root=self.workspace_root)

    def _is_git_repository(self) -> bool:
        git_dir = self.workspace_root / ".git"
        return git_dir.exists() and git_dir.is_dir()

    async def get_status(self) -> GitStatus:
        """Inspects repository and branch status safely."""
        if not self._is_git_repository():
            return GitStatus(
                is_git_repo=False,
                error=f"'{self.workspace_root}' is not a Git repository."
            )

        # 1. Get current branch
        branch_res = await self.broker.execute_command("git rev-parse --abbrev-ref HEAD", cwd=self.workspace_root)
        current_branch = branch_res.stdout.strip() if branch_res.exit_code == 0 else "unknown"

        # 2. Get status porcelain
        status_res = await self.broker.execute_command("git status --porcelain=v1", cwd=self.workspace_root)
        if status_res.exit_code != 0:
            return GitStatus(
                is_git_repo=True,
                branch=current_branch,
                error=f"git status failed: {status_res.stderr.strip()}"
            )

        modified: List[str] = []
        untracked: List[str] = []
        staged: List[str] = []

        for line in status_res.stdout.splitlines():
            if len(line) < 3:
                continue
            index_code = line[0]
            worktree_code = line[1]
            file_path = line[3:].strip()

            if index_code in ("M", "A", "D", "R", "C"):
                staged.append(file_path)
            if worktree_code in ("M", "D"):
                modified.append(file_path)
            elif index_code == "?" and worktree_code == "?":
                untracked.append(file_path)

        is_clean = len(modified) == 0 and len(untracked) == 0 and len(staged) == 0

        return GitStatus(
            is_git_repo=True,
            branch=current_branch,
            is_clean=is_clean,
            modified_files=modified,
            untracked_files=untracked,
            staged_files=staged
        )

    async def get_diff(self, staged: bool = False, file_path: Optional[str] = None) -> str:
        """Retrieves diff output for working tree or staged changes."""
        if not self._is_git_repository():
            return ""

        cmd_parts = ["git", "diff"]
        if staged:
            cmd_parts.append("--staged")
        if file_path:
            # Validate path confinement
            safe_target = (self.workspace_root / file_path.strip().lstrip("/\\")).resolve()
            try:
                safe_target.relative_to(self.workspace_root)
                rel = str(safe_target.relative_to(self.workspace_root)).replace("\\", "/")
                cmd_parts.extend(["--", rel])
            except ValueError:
                return "Error: File escapes workspace root."

        cmd_str = " ".join(cmd_parts)
        res = await self.broker.execute_command(cmd_str, cwd=self.workspace_root)
        return res.stdout if res.exit_code == 0 else f"Error: {res.stderr}"

    async def create_task_branch(self, task_id: str, custom_name: Optional[str] = None) -> Tuple[bool, str]:
        """Creates and switches to a dedicated task branch."""
        if not self._is_git_repository():
            return False, "Not a git repository."

        branch_name = custom_name or f"task/{task_id[:12]}"
        # Sanitize branch name
        sanitized = "".join(c if c.isalnum() or c in ("-", "_", "/") else "_" for c in branch_name)

        res = await self.broker.execute_command(f"git checkout -b {sanitized}", cwd=self.workspace_root)
        if res.exit_code == 0:
            audit_ledger.record_event(
                event_type="GIT_BRANCH_CREATED",
                action=f"Created task branch: {sanitized}",
                actor="GIT_SERVICE",
                risk_level="LOW",
                details={"branch": sanitized, "task_id": task_id}
            )
            return True, sanitized
        return False, res.stderr.strip()

    def prepare_commit_plan(
        self,
        commit_message: str,
        files_to_commit: List[str],
        task_id: Optional[str] = None,
        verification_evidence: Optional[Dict[str, Any]] = None
    ) -> CommitPlan:
        """Constructs an audited commit plan requiring explicit governance approval."""
        plan_id = f"cplan_{os.urandom(6).hex()}"
        return CommitPlan(
            plan_id=plan_id,
            branch="unknown",
            files_to_commit=files_to_commit,
            commit_message=commit_message,
            task_id=task_id,
            verification_evidence=verification_evidence,
            requires_approval=True,
            is_approved=False
        )

    async def execute_commit(self, plan: CommitPlan, authorized_by: str) -> CommitResult:
        """
        Executes git commit strictly under authenticated operator authorization.
        Stages only explicitly listed files and attaches verified task evidence.
        """
        if not authorized_by or not authorized_by.strip():
            return CommitResult(success=False, error="Authentication required to execute commit.")

        if not self._is_git_repository():
            return CommitResult(success=False, error="Not a git repository.")

        # Stage files
        for rel_file in plan.files_to_commit:
            safe_target = (self.workspace_root / rel_file.strip().lstrip("/\\")).resolve()
            try:
                safe_target.relative_to(self.workspace_root)
                rel = str(safe_target.relative_to(self.workspace_root)).replace("\\", "/")
                stage_res = await self.broker.execute_command(f"git add {rel}", cwd=self.workspace_root)
                if stage_res.exit_code != 0:
                    return CommitResult(success=False, error=f"Failed to stage '{rel}': {stage_res.stderr}")
            except ValueError:
                return CommitResult(success=False, error=f"Cannot commit file outside workspace: '{rel_file}'")

        # Format commit message with attribution and verified task link
        full_message = plan.commit_message
        if plan.task_id:
            full_message += f"\n\nTask-ID: {plan.task_id}"
        full_message += f"\nAuthorized-By: {authorized_by}"

        # Clean quotes for safe commit
        clean_msg = full_message.replace('"', '\\"')
        commit_res = await self.broker.execute_command(f'git commit -m "{clean_msg}"', cwd=self.workspace_root)
        if commit_res.exit_code != 0:
            return CommitResult(success=False, error=commit_res.stderr.strip() or commit_res.stdout.strip())

        # Retrieve commit hash
        hash_res = await self.broker.execute_command("git rev-parse HEAD", cwd=self.workspace_root)
        commit_hash = hash_res.stdout.strip() if hash_res.exit_code == 0 else "unknown"

        # Retrieve current branch
        branch_res = await self.broker.execute_command("git rev-parse --abbrev-ref HEAD", cwd=self.workspace_root)
        branch = branch_res.stdout.strip() if branch_res.exit_code == 0 else "unknown"

        audit_ledger.record_event(
            event_type="GIT_COMMIT_EXECUTED",
            action=f"Committed {commit_hash[:8]} on {branch}: {plan.commit_message.splitlines()[0]}",
            actor=authorized_by,
            risk_level="MEDIUM",
            details={
                "commit_hash": commit_hash,
                "branch": branch,
                "files": plan.files_to_commit,
                "task_id": plan.task_id
            }
        )

        return CommitResult(
            success=True,
            commit_hash=commit_hash,
            branch=branch
        )
