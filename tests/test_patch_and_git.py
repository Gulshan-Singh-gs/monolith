"""
tests/test_patch_and_git.py
Test suite for PatchEngine and GitService.
Verifies unified diff generation, parsing, risk classification, workspace confinement,
atomic application, recoverable checkpoints, rollback, and safe Git operations.
"""

import pytest
from pathlib import Path
from core.workspace.patch_engine import PatchEngine
from core.workspace.git_service import GitService, CommitPlan


@pytest.fixture
def temp_patch_workspace(tmp_path):
    ws = tmp_path / "patch_workspace"
    ws.mkdir()
    (ws / "hello.py").write_text("def hello():\n    print('Hello World')\n", encoding="utf-8")
    (ws / "server.py").write_text("# Sensitive server file\nSECRET = 123\n", encoding="utf-8")
    return ws


def test_unified_diff_generation_and_parsing(temp_patch_workspace):
    pe = PatchEngine(workspace_root=temp_patch_workspace)

    orig = "line 1\nline 2\nline 3\n"
    mod = "line 1\nline 2 modified\nline 3\nline 4\n"

    diff = pe.generate_unified_diff("test.txt", orig, mod)
    assert "--- a/test.txt" in diff
    assert "+++ b/test.txt" in diff
    assert "+line 2 modified" in diff

    file_patches = pe.parse_patch(diff)
    assert len(file_patches) == 1
    fp = file_patches[0]
    assert fp.target_file == "test.txt"
    assert fp.additions >= 2
    assert fp.deletions >= 1
    assert len(fp.hunks) == 1


def test_patch_validation_and_risk_classification(temp_patch_workspace):
    pe = PatchEngine(workspace_root=temp_patch_workspace)

    # 1. Normal safe file
    diff_safe = pe.generate_unified_diff(
        "hello.py",
        "def hello():\n    print('Hello World')\n",
        "def hello():\n    print('Hello Sovereign')\n"
    )
    val_safe = pe.validate_patch(diff_safe)
    assert val_safe.is_valid is True
    assert "hello.py" in val_safe.affected_files
    assert val_safe.highest_risk == "LOW"

    # 2. Sensitive server file triggers HIGH risk
    diff_sensitive = pe.generate_unified_diff(
        "server.py",
        "# Sensitive server file\nSECRET = 123\n",
        "# Sensitive server file\nSECRET = 456\n"
    )
    val_sens = pe.validate_patch(diff_sensitive)
    assert val_sens.is_valid is True
    assert val_sens.highest_risk == "HIGH"

    # 3. Path traversal attack in diff header is blocked
    malicious_diff = (
        "--- a/../../etc/passwd\n"
        "+++ b/../../etc/passwd\n"
        "@@ -1,1 +1,1 @@\n"
        "-root:x:0:0\n"
        "+hacked:x:0:0\n"
    )
    val_mal = pe.validate_patch(malicious_diff)
    assert val_mal.is_valid is False
    assert "Security violation" in val_mal.error or "escapes" in val_mal.error


def test_atomic_patch_application_and_rollback(temp_patch_workspace):
    pe = PatchEngine(workspace_root=temp_patch_workspace)

    orig_content = (temp_patch_workspace / "hello.py").read_text(encoding="utf-8")
    mod_content = "def hello():\n    print('Hello Sovereign AI Workbench')\n"

    diff = pe.generate_unified_diff("hello.py", orig_content, mod_content)

    # Apply patch
    apply_res = pe.apply_patch(diff)
    assert apply_res.success is True
    assert apply_res.checkpoint_id is not None
    assert "hello.py" in apply_res.applied_files

    # Verify updated content on disk
    updated_content = (temp_patch_workspace / "hello.py").read_text(encoding="utf-8")
    assert "Hello Sovereign AI Workbench" in updated_content

    # Roll back to pre-patch checkpoint
    rollback_res = pe.rollback_checkpoint(apply_res.checkpoint_id)
    assert rollback_res is True

    # Verify original content restored
    restored_content = (temp_patch_workspace / "hello.py").read_text(encoding="utf-8")
    assert restored_content == orig_content


@pytest.mark.asyncio
async def test_git_service_status_and_commit_plan(temp_patch_workspace):
    gs = GitService(workspace_root=temp_patch_workspace)

    # In a non-git dir, status returns cleanly with is_git_repo=False
    status = await gs.get_status()
    assert status.is_git_repo is False

    # Prepare commit plan requires explicit authorization
    plan = gs.prepare_commit_plan(
        commit_message="feat: add sovereign patch engine",
        files_to_commit=["hello.py"],
        task_id="task_12345"
    )
    assert plan.requires_approval is True
    assert plan.is_approved is False

    # Attempting to commit without authorization must fail
    res = await gs.execute_commit(plan, authorized_by="")
    assert res.success is False
    assert "Authentication required" in res.error
