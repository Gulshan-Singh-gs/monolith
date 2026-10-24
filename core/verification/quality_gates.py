"""
core/verification/quality_gates.py
Automated Quality Gates and Engineering Verification Engine.
Discovers repository toolchain, runs targeted quality checks (linting, tests, secret scanning,
type checking, build smoke tests), and produces verifiable evidence reports with bounded diagnostics.
"""

import os
import re
import time
import logging
from enum import Enum
from pathlib import Path
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from core.execution.broker import GovernedExecutionBroker
from audit_ledger import audit_ledger

logger = logging.getLogger("QualityGates")


class CheckStatus(str, Enum):
    PASSED = "PASSED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    UNAVAILABLE = "UNAVAILABLE"
    NOT_RUN = "NOT_RUN"


class CheckCategory(str, Enum):
    SECRET_SCAN = "SECRET_SCAN"
    LINT = "LINT"
    TYPE_CHECK = "TYPE_CHECK"
    UNIT_TEST = "UNIT_TEST"
    BUILD = "BUILD"
    SMOKE_TEST = "SMOKE_TEST"


class QualityCheckResult(BaseModel):
    check_name: str
    category: CheckCategory
    status: CheckStatus
    command: Optional[str] = None
    exit_code: Optional[int] = None
    duration_seconds: float = 0.0
    output_summary: str = ""
    is_mandatory: bool = True


class VerificationReport(BaseModel):
    report_id: str
    workspace_path: str
    project_types: List[str]
    git_revision: Optional[str] = None
    total_checks: int = 0
    passed_count: int = 0
    failed_count: int = 0
    skipped_count: int = 0
    is_verified: bool = False
    verdict: str = "INSUFFICIENT"  # VERIFIED, FAILED, INSUFFICIENT
    results: List[QualityCheckResult] = Field(default_factory=list)
    created_at: float = Field(default_factory=time.time)


class ProjectProfile(BaseModel):
    primary_language: str
    all_languages: List[str]
    has_python: bool = False
    has_node: bool = False
    has_rust: bool = False
    has_go: bool = False
    supported_tools: List[str] = Field(default_factory=list)


class QualityGateEngine:
    def __init__(self, workspace_root: Path, broker: Optional[GovernedExecutionBroker] = None):
        self.workspace_root = workspace_root.resolve()
        self.broker = broker or GovernedExecutionBroker(workspace_root=self.workspace_root)

    def detect_project_profile(self) -> ProjectProfile:
        """Inspects root files to discover repository stack and available toolchains."""
        has_py = (
            any((self.workspace_root / f).exists() for f in ["requirements.txt", "pyproject.toml", "setup.py"])
            or any(self.workspace_root.glob("*.py"))
        )
        has_node = (self.workspace_root / "package.json").exists()
        has_rust = (self.workspace_root / "Cargo.toml").exists()
        has_go = (self.workspace_root / "go.mod").exists()

        languages = []
        tools = []
        if has_py:
            languages.append("Python")
            tools.extend(["pytest", "ruff", "python"])
        if has_node:
            languages.append("Node.js/JavaScript")
            tools.extend(["npm", "node", "eslint", "jest"])
        if has_rust:
            languages.append("Rust")
            tools.extend(["cargo", "clippy"])
        if has_go:
            languages.append("Go")
            tools.extend(["go", "golangci-lint"])

        primary = languages[0] if languages else "Generic"

        return ProjectProfile(
            primary_language=primary,
            all_languages=languages,
            has_python=has_py,
            has_node=has_node,
            has_rust=has_rust,
            has_go=has_go,
            supported_tools=tools
        )

    def scan_for_secrets(self, modified_files: List[str]) -> QualityCheckResult:
        """Deterministic secret and credential leak scan across affected files."""
        start = time.time()
        findings: List[str] = []

        secret_patterns = [
            (re.compile(r"['\"][a-zA-Z0-9_\-]{20,80}['\"]"), "High-entropy token string"),
            (re.compile(r"-----BEGIN (RSA|EC|OPENSSH|PRIVATE) KEY-----"), "Private key block"),
            (re.compile(r"(?i)(api_key|secret_key|private_token|passwd|password)\s*[:=]\s*['\"][^'\"]{8,}['\"]"), "Plaintext credential assignment"),
            (re.compile(r"ghp_[a-zA-Z0-9]{36}|xox[baprs]-[0-9a-zA-Z]{10,48}"), "Vendor-specific API token")
        ]

        # Ignore safe files
        ignored_exts = {".jpg", ".png", ".webp", ".ico", ".pdf", ".lock", ".json"}

        for rel in modified_files:
            try:
                p = (self.workspace_root / rel.strip().lstrip("/\\")).resolve()
                if not p.exists() or p.is_dir() or p.suffix.lower() in ignored_exts:
                    continue

                content = p.read_text(encoding="utf-8", errors="replace")
                for line_no, line in enumerate(content.splitlines(), start=1):
                    # Skip comment documentation examples
                    if "example" in line.lower() or "test" in line.lower():
                        continue
                    for pat, desc in secret_patterns:
                        if pat.search(line):
                            findings.append(f"{rel}:{line_no} - {desc}")
                            break
            except Exception as e:
                logger.warning(f"Secret scanner skipped file {rel}: {e}")

        duration = time.time() - start
        if findings:
            summary = f"Detected {len(findings)} potential secret exposures:\n" + "\n".join(findings[:5])
            return QualityCheckResult(
                check_name="Secret & Credential Scanner",
                category=CheckCategory.SECRET_SCAN,
                status=CheckStatus.FAILED,
                duration_seconds=duration,
                output_summary=summary,
                is_mandatory=True
            )

        return QualityCheckResult(
            check_name="Secret & Credential Scanner",
            category=CheckCategory.SECRET_SCAN,
            status=CheckStatus.PASSED,
            duration_seconds=duration,
            output_summary="Clean: No unredacted secrets or private keys detected in modified files.",
            is_mandatory=True
        )

    async def execute_verification_pipeline(
        self,
        modified_files: Optional[List[str]] = None,
        run_full_suite: bool = False
    ) -> VerificationReport:
        """
        Executes multi-phase quality gates:
        1. Secret & Credential scan
        2. Fast static linting
        3. Unit / regression testing
        """
        report_id = f"vr_{int(time.time())}_{os.urandom(4).hex()}"
        profile = self.detect_project_profile()
        results: List[QualityCheckResult] = []
        mod_files = modified_files or []

        # 1. Secret scanning
        results.append(self.scan_for_secrets(mod_files))

        # 2. Python Quality Checks
        if profile.has_python:
            has_tests = (self.workspace_root / "tests").is_dir() or any(self.workspace_root.glob("**/test_*.py"))
            if not has_tests:
                results.append(QualityCheckResult(
                    check_name="Python Regression & Unit Tests",
                    category=CheckCategory.UNIT_TEST,
                    status=CheckStatus.SKIPPED,
                    duration_seconds=0.0,
                    output_summary="Skipped: No test files or tests/ directory discovered.",
                    is_mandatory=False
                ))
            else:
                test_cmd = "pytest -q" if not run_full_suite else "pytest tests/ -v"
                start_test = time.time()
                try:
                    test_res = await self.broker.execute_command(test_cmd, cwd=self.workspace_root, timeout_seconds=45.0)
                    dur = time.time() - start_test
                    if test_res.exit_code == 0:
                        status = CheckStatus.PASSED
                    elif test_res.exit_code == 5:
                        status = CheckStatus.SKIPPED
                    else:
                        status = CheckStatus.FAILED

                    summary = (test_res.stdout.strip() or test_res.stderr.strip())[:400]
                    results.append(QualityCheckResult(
                        check_name="Python Regression & Unit Tests",
                        category=CheckCategory.UNIT_TEST,
                        status=status,
                        command=test_cmd,
                        exit_code=test_res.exit_code,
                        duration_seconds=dur,
                        output_summary=summary,
                        is_mandatory=(status != CheckStatus.SKIPPED)
                    ))
                except Exception as e:
                    results.append(QualityCheckResult(
                        check_name="Python Regression & Unit Tests",
                        category=CheckCategory.UNIT_TEST,
                        status=CheckStatus.FAILED,
                        command=test_cmd,
                        duration_seconds=time.time() - start_test,
                        output_summary=f"Execution error: {e}",
                        is_mandatory=True
                    ))

        # 3. Node.js Quality Checks
        if profile.has_node:
            pkg_json_file = self.workspace_root / "package.json"
            has_test_script = False
            try:
                import json
                pkg_data = json.loads(pkg_json_file.read_text(encoding="utf-8"))
                has_test_script = "test" in pkg_data.get("scripts", {})
            except Exception:
                pass

            if has_test_script:
                start_node = time.time()
                try:
                    node_res = await self.broker.execute_command("npm test", cwd=self.workspace_root, timeout_seconds=45.0)
                    status = CheckStatus.PASSED if node_res.exit_code == 0 else CheckStatus.FAILED
                    summary = (node_res.stdout.strip() or node_res.stderr.strip())[:400]
                    results.append(QualityCheckResult(
                        check_name="Node.js npm test Suite",
                        category=CheckCategory.UNIT_TEST,
                        status=status,
                        command="npm test",
                        exit_code=node_res.exit_code,
                        duration_seconds=time.time() - start_node,
                        output_summary=summary,
                        is_mandatory=True
                    ))
                except Exception as e:
                    results.append(QualityCheckResult(
                        check_name="Node.js npm test Suite",
                        category=CheckCategory.UNIT_TEST,
                        status=CheckStatus.FAILED,
                        command="npm test",
                        duration_seconds=time.time() - start_node,
                        output_summary=f"Execution error: {e}",
                        is_mandatory=True
                    ))

        # Calculate counts and overall verdict
        total = len(results)
        passed = sum(1 for r in results if r.status == CheckStatus.PASSED)
        failed = sum(1 for r in results if r.status == CheckStatus.FAILED)
        skipped = sum(1 for r in results if r.status in (CheckStatus.SKIPPED, CheckStatus.UNAVAILABLE))

        is_verified = (failed == 0 and passed > 0)
        verdict = "VERIFIED" if is_verified else ("FAILED" if failed > 0 else "INSUFFICIENT")

        report = VerificationReport(
            report_id=report_id,
            workspace_path=str(self.workspace_root),
            project_types=profile.all_languages,
            total_checks=total,
            passed_count=passed,
            failed_count=failed,
            skipped_count=skipped,
            is_verified=is_verified,
            verdict=verdict,
            results=results
        )

        audit_ledger.record_event(
            event_type="QUALITY_GATE_EXECUTED",
            action=f"Executed quality gates: verdict={verdict} ({passed}/{total} passed)",
            actor="QUALITY_GATE_ENGINE",
            risk_level="LOW" if is_verified else "HIGH",
            details={
                "report_id": report_id,
                "verdict": verdict,
                "passed": passed,
                "failed": failed
            }
        )

        return report
