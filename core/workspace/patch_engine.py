"""
core/workspace/patch_engine.py
Production-grade Patch-First Editing Pipeline.
Provides unified diff generation, parsing, risk classification, workspace confinement validation,
atomic application, recoverable checkpoint snapshots, and rollback capabilities.
"""

import os
import re
import time
import json
import difflib
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from pydantic import BaseModel, Field

logger = logging.getLogger("PatchEngine")


class PatchHunk(BaseModel):
    header: str
    old_start: int
    old_length: int
    new_start: int
    new_length: int
    lines: List[str]


class FilePatch(BaseModel):
    source_file: str
    target_file: str
    hunks: List[PatchHunk] = Field(default_factory=list)
    additions: int = 0
    deletions: int = 0
    is_new_file: bool = False
    is_deleted_file: bool = False
    risk_level: str = "LOW"  # LOW, MEDIUM, HIGH, CRITICAL


class PatchValidationResult(BaseModel):
    is_valid: bool
    affected_files: List[str] = Field(default_factory=list)
    highest_risk: str = "LOW"
    error: Optional[str] = None
    file_patches: List[FilePatch] = Field(default_factory=list)


class CheckpointMeta(BaseModel):
    checkpoint_id: str
    created_at: float
    affected_files: List[str]
    snapshot_dir: str


class PatchApplyResult(BaseModel):
    success: bool
    checkpoint_id: Optional[str] = None
    applied_files: List[str] = Field(default_factory=list)
    error: Optional[str] = None


class PatchEngine:
    def __init__(self, workspace_root: Path, checkpoints_dir: Optional[Path] = None):
        self.workspace_root = workspace_root.resolve()
        self.checkpoints_dir = (
            checkpoints_dir or (self.workspace_root / "output" / ".vault" / "checkpoints")
        ).resolve()
        self.checkpoints_dir.mkdir(parents=True, exist_ok=True)

    def _resolve_safe_path(self, rel_path: str) -> Path:
        """Confines path resolution strictly inside workspace root."""
        cleaned = rel_path.strip().lstrip("/\\")
        candidate = (self.workspace_root / cleaned).resolve()
        try:
            candidate.relative_to(self.workspace_root)
        except ValueError:
            raise PermissionError(f"Path '{rel_path}' escapes workspace root '{self.workspace_root}'")
        return candidate

    def generate_unified_diff(
        self,
        rel_path: str,
        original_content: str,
        modified_content: str
    ) -> str:
        """Generates standard unified diff format for a given relative path."""
        orig_lines = original_content.splitlines(keepends=True)
        mod_lines = modified_content.splitlines(keepends=True)

        diff_lines = list(difflib.unified_diff(
            orig_lines,
            mod_lines,
            fromfile=f"a/{rel_path}",
            tofile=f"b/{rel_path}"
        ))
        return "".join(diff_lines)

    def parse_patch(self, patch_text: str) -> List[FilePatch]:
        """Parses a unified diff string into structured FilePatch objects."""
        file_patches: List[FilePatch] = []
        current_patch: Optional[FilePatch] = None
        current_hunk: Optional[PatchHunk] = None

        lines = patch_text.splitlines()
        i = 0
        while i < len(lines):
            line = lines[i]

            # Detect file headers
            if line.startswith("--- "):
                src_path = line[4:].strip()
                if src_path.startswith("a/"):
                    src_path = src_path[2:]
                i += 1
                if i < len(lines) and lines[i].startswith("+++ "):
                    dst_path = lines[i][4:].strip()
                    if dst_path.startswith("b/"):
                        dst_path = dst_path[2:]

                    current_patch = FilePatch(
                        source_file=src_path,
                        target_file=dst_path,
                        is_new_file=(src_path == "/dev/null"),
                        is_deleted_file=(dst_path == "/dev/null")
                    )
                    file_patches.append(current_patch)
                    current_hunk = None
                    i += 1
                    continue

            # Detect hunk header @@ -old_start,old_len +new_start,new_len @@
            if line.startswith("@@ ") and current_patch is not None:
                match = re.match(r"^@@\s+-(\d+)(?:,(\d+))?\s+\+(\d+)(?:,(\d+))?\s+@@", line)
                if match:
                    old_start = int(match.group(1))
                    old_len = int(match.group(2)) if match.group(2) else 1
                    new_start = int(match.group(3))
                    new_len = int(match.group(4)) if match.group(4) else 1

                    current_hunk = PatchHunk(
                        header=line,
                        old_start=old_start,
                        old_length=old_len,
                        new_start=new_start,
                        new_length=new_len,
                        lines=[]
                    )
                    current_patch.hunks.append(current_hunk)
                    i += 1
                    continue

            if current_hunk is not None and current_patch is not None:
                if line.startswith("+"):
                    current_patch.additions += 1
                    current_hunk.lines.append(line)
                elif line.startswith("-"):
                    current_patch.deletions += 1
                    current_hunk.lines.append(line)
                elif line.startswith(" ") or line == "":
                    current_hunk.lines.append(line)

            i += 1

        # Classify risk for each file patch
        for fp in file_patches:
            fp.risk_level = self._classify_patch_risk(fp)

        return file_patches

    def _classify_patch_risk(self, fp: FilePatch) -> str:
        """Classifies risk level based on modified files and diff contents."""
        path_lower = fp.target_file.lower()
        # High risk files: security, credentials, server entry points, configs
        sensitive_patterns = [
            ".env", "vault", "security", "auth", "token", "key",
            "server.py", "dockerfile", "settings", "broker", "profile"
        ]
        if any(pat in path_lower for pat in sensitive_patterns):
            return "HIGH"

        if fp.is_deleted_file:
            return "MEDIUM"

        total_churn = fp.additions + fp.deletions
        if total_churn > 250:
            return "MEDIUM"

        return "LOW"

    def validate_patch(self, patch_text: str) -> PatchValidationResult:
        """Validates that all paths in the patch strictly reside within workspace."""
        if not patch_text or not patch_text.strip():
            return PatchValidationResult(
                is_valid=False,
                error="Patch text is empty."
            )

        try:
            file_patches = self.parse_patch(patch_text)
            if not file_patches:
                return PatchValidationResult(
                    is_valid=False,
                    error="No valid file patch chunks found in diff."
                )

            affected = []
            highest_risk = "LOW"
            risk_ranks = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}

            for fp in file_patches:
                target = fp.target_file
                if target == "/dev/null":
                    target = fp.source_file

                # Path boundary confinement validation
                try:
                    self._resolve_safe_path(target)
                except PermissionError as pe:
                    return PatchValidationResult(
                        is_valid=False,
                        error=f"Security violation: {pe}"
                    )

                affected.append(target)
                if risk_ranks.get(fp.risk_level, 1) > risk_ranks.get(highest_risk, 1):
                    highest_risk = fp.risk_level

            return PatchValidationResult(
                is_valid=True,
                affected_files=affected,
                highest_risk=highest_risk,
                file_patches=file_patches
            )
        except Exception as e:
            return PatchValidationResult(
                is_valid=False,
                error=f"Patch parsing failure: {e}"
            )

    def create_checkpoint(self, rel_paths: List[str]) -> CheckpointMeta:
        """
        Takes a snapshot of targeted files prior to patch application.
        Allows instant 1-click rollback if testing or verification fails.
        """
        checkpoint_id = f"chk_{int(time.time())}_{os.urandom(4).hex()}"
        snapshot_dir = self.checkpoints_dir / checkpoint_id
        snapshot_dir.mkdir(parents=True, exist_ok=True)

        affected: List[str] = []
        for rel in rel_paths:
            try:
                safe_file = self._resolve_safe_path(rel)
                if safe_file.exists() and safe_file.is_file():
                    target_backup = snapshot_dir / rel
                    target_backup.parent.mkdir(parents=True, exist_ok=True)
                    target_backup.write_bytes(safe_file.read_bytes())
                    affected.append(rel)
            except Exception as e:
                logger.warning(f"Failed to snapshot '{rel}' for checkpoint {checkpoint_id}: {e}")

        meta = CheckpointMeta(
            checkpoint_id=checkpoint_id,
            created_at=time.time(),
            affected_files=affected,
            snapshot_dir=str(snapshot_dir)
        )

        meta_file = snapshot_dir / "meta.json"
        meta_file.write_text(meta.model_dump_json(indent=2), encoding="utf-8")
        return meta

    def apply_patch(self, patch_text: str) -> PatchApplyResult:
        """
        Applies validated patch to workspace files atomically with checkpoint snapshotting.
        """
        validation = self.validate_patch(patch_text)
        if not validation.is_valid:
            return PatchApplyResult(
                success=False,
                error=validation.error or "Patch validation failed."
            )

        # Snapshot files before making modifications
        checkpoint = self.create_checkpoint(validation.affected_files)

        applied: List[str] = []
        try:
            for fp in validation.file_patches:
                target_path = self._resolve_safe_path(fp.target_file)

                if fp.is_deleted_file:
                    if target_path.exists():
                        target_path.unlink()
                        applied.append(fp.target_file)
                    continue

                original_content = ""
                if target_path.exists():
                    original_content = target_path.read_text(encoding="utf-8", errors="replace")

                new_content = self._apply_hunks_to_content(original_content, fp.hunks)

                # Atomic write via temp file
                target_path.parent.mkdir(parents=True, exist_ok=True)
                temp_file = target_path.with_suffix(".tmp_patch")
                temp_file.write_text(new_content, encoding="utf-8")
                temp_file.replace(target_path)
                applied.append(fp.target_file)

            return PatchApplyResult(
                success=True,
                checkpoint_id=checkpoint.checkpoint_id,
                applied_files=applied
            )
        except Exception as e:
            logger.error(f"Patch application failed: {e}. Rolling back...")
            self.rollback_checkpoint(checkpoint.checkpoint_id)
            return PatchApplyResult(
                success=False,
                checkpoint_id=checkpoint.checkpoint_id,
                error=f"Application failed and rolled back: {e}"
            )

    def _apply_hunks_to_content(self, original_content: str, hunks: List[PatchHunk]) -> str:
        """Applies hunks to content line by line."""
        if not hunks:
            return original_content

        orig_lines = original_content.splitlines(keepends=True)
        out_lines: List[str] = []
        orig_idx = 0

        for hunk in hunks:
            # Hunk line numbers are 1-based
            hunk_old_start = hunk.old_start - 1 if hunk.old_start > 0 else 0

            # Copy unchanged lines leading up to this hunk
            while orig_idx < hunk_old_start and orig_idx < len(orig_lines):
                out_lines.append(orig_lines[orig_idx])
                orig_idx += 1

            for h_line in hunk.lines:
                if h_line.startswith("+"):
                    line_to_add = h_line[1:]
                    if not line_to_add.endswith("\n"):
                        line_to_add += "\n"
                    out_lines.append(line_to_add)
                elif h_line.startswith("-"):
                    orig_idx += 1
                elif h_line.startswith(" "):
                    line_to_keep = orig_lines[orig_idx] if orig_idx < len(orig_lines) else h_line[1:] + "\n"
                    out_lines.append(line_to_keep)
                    orig_idx += 1

        # Copy any remaining lines after final hunk
        while orig_idx < len(orig_lines):
            out_lines.append(orig_lines[orig_idx])
            orig_idx += 1

        return "".join(out_lines)

    def rollback_checkpoint(self, checkpoint_id: str) -> bool:
        """Reverts workspace files to their exact state captured in checkpoint."""
        snapshot_dir = self.checkpoints_dir / checkpoint_id
        if not snapshot_dir.exists():
            logger.error(f"Checkpoint '{checkpoint_id}' not found.")
            return False

        meta_file = snapshot_dir / "meta.json"
        if not meta_file.exists():
            return False

        try:
            meta = CheckpointMeta(**json.loads(meta_file.read_text(encoding="utf-8")))
            for rel in meta.affected_files:
                backup_file = snapshot_dir / rel
                target_file = self._resolve_safe_path(rel)
                if backup_file.exists():
                    target_file.parent.mkdir(parents=True, exist_ok=True)
                    target_file.write_bytes(backup_file.read_bytes())
                elif target_file.exists():
                    # If it didn't exist in backup, it was a newly created file
                    target_file.unlink()
            logger.info(f"Successfully rolled back checkpoint {checkpoint_id}")
            return True
        except Exception as e:
            logger.error(f"Error executing rollback for {checkpoint_id}: {e}")
            return False
