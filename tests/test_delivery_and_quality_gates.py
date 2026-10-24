"""
tests/test_delivery_and_quality_gates.py
Test suite for QualityGateEngine and DeliveryEngine.
Verifies project stack detection, secret leak scanning, quality gate execution,
deployment approval gating, and release verification.
"""

import pytest
from pathlib import Path
from core.verification.quality_gates import QualityGateEngine, CheckStatus
from core.deployment.delivery_engine import (
    DeliveryEngine,
    DeploymentTarget,
    DeploymentEnvironment,
    DeploymentPlan
)


def test_quality_gate_project_detection_and_secrets(temp_workspace):
    qg = QualityGateEngine(workspace_root=temp_workspace)

    # 1. Project profile detection
    profile = qg.detect_project_profile()
    assert profile.has_python is True

    # 2. Secret scanning on clean workspace
    clean_check = qg.scan_for_secrets(["main.py", "README.md"])
    assert clean_check.status == CheckStatus.PASSED

    # 3. Secret scanning on file with hardcoded private key
    leak_file = temp_workspace / "leak.py"
    leak_file.write_text("API_KEY = 'ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890'\n", encoding="utf-8")

    leak_check = qg.scan_for_secrets(["leak.py"])
    assert leak_check.status == CheckStatus.FAILED
    assert "potential secret exposure" in leak_check.output_summary.lower()


@pytest.mark.asyncio
async def test_delivery_engine_approval_and_gating(temp_workspace):
    delivery = DeliveryEngine(workspace_root=temp_workspace)

    # Create dummy build directory
    build_dir = temp_workspace / "static"
    build_dir.mkdir(exist_ok=True)
    (build_dir / "index.html").write_text("<h1>MONOLITH Workbench</h1>", encoding="utf-8")

    # 1. Prepare deployment plan
    plan = delivery.prepare_deployment_plan(
        target=DeploymentTarget.CLOUDFLARE_PAGES,
        project_name="monolith-preview",
        build_dir="static",
        environment=DeploymentEnvironment.PREVIEW
    )
    assert plan.requires_approval is True
    assert plan.is_approved is False

    # 2. Unapproved execution fails closed
    unapproved_res = await delivery.execute_deployment(plan.plan_id, authorized_by="Alice")
    assert unapproved_res.success is False
    assert "Explicit authenticated operator approval required" in unapproved_res.error

    # 3. Approve plan by authorized officer
    approved_plan = delivery.approve_deployment_plan(plan.plan_id, authorized_by="SecurityLead")
    assert approved_plan.is_approved is True
    assert approved_plan.approved_by == "SecurityLead"

    # 4. Execute deployment with approval
    res = await delivery.execute_deployment(plan.plan_id, authorized_by="SecurityLead")
    assert res.success is True
    assert res.deployed_url is not None
    assert "pages.dev" in res.deployed_url
