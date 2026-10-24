"""
tests/test_approval_lifecycle.py
Comprehensive regression tests for Human-in-the-Loop approval lifecycle,
persistence, authenticated submission, idempotency, and cancellation.
"""

import os
import json
import asyncio
import tempfile
import shutil
from pathlib import Path
import pytest

from core.interfaces.agent import AgentRole, TaskState, AgentTaskContract
from core.interfaces.model_gateway import PrivacyMode, InferenceRequest, InferenceResponse, IModelProvider
from core.orchestrator.orchestrator import LocalOrchestrator
from core.workspace.engine import SecureWorkspaceEngine
from core.gateway.router import SovereignModelGateway
from governed_agent import GovernedAgentController, AgentActionRequest


class MockLocalProvider(IModelProvider):
    def __init__(self, response_text: str = "Mock synthesis complete."):
        self.response_text = response_text
        self.is_local = True

    def provider_id(self) -> str:
        return "mock_local"

    def is_available(self) -> bool:
        return True

    async def generate(self, request: InferenceRequest) -> InferenceResponse:
        return InferenceResponse(
            content=self.response_text,
            model_used="mock-model",
            provider_used="mock_local",
            is_local=True,
            latency_seconds=0.01,
            token_usage={"tokens": 10}
        )


@pytest.fixture
def test_env():
    from governed_agent import governed_agent
    temp_dir = Path(tempfile.mkdtemp(prefix="sov_approval_test_"))
    vault_dir = temp_dir / "output" / ".vault"
    vault_dir.mkdir(parents=True, exist_ok=True)

    original_storage = governed_agent.storage_dir
    original_pending_file = governed_agent.pending_file
    governed_agent.pending_approvals.clear()
    governed_agent.approval_futures.clear()
    governed_agent.decided_approvals.clear()
    governed_agent.storage_dir = vault_dir
    governed_agent.pending_file = vault_dir / "pending_approvals.json"

    ws = SecureWorkspaceEngine(initial_root=temp_dir)
    mock_provider = MockLocalProvider()
    gw = SovereignModelGateway(
        default_privacy_mode=PrivacyMode.LOCAL_ONLY,
        provider_override=mock_provider
    )
    orch = LocalOrchestrator(workspace=ws, gateway=gw, storage_dir=vault_dir)

    yield {
        "temp_dir": temp_dir,
        "vault_dir": vault_dir,
        "workspace": ws,
        "gateway": gw,
        "orchestrator": orch
    }
    governed_agent.pending_approvals.clear()
    governed_agent.approval_futures.clear()
    governed_agent.decided_approvals.clear()
    governed_agent.storage_dir = original_storage
    governed_agent.pending_file = original_pending_file
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.mark.asyncio
async def test_lifecycle_normal_task_flow(test_env):
    """A task not requiring approval transitions through: CREATED -> VALIDATING -> PLANNING -> READY -> RUNNING -> VERIFYING -> COMPLETED."""
    orch = test_env["orchestrator"]
    task = orch.create_task(
        role=AgentRole.CODING_AGENT,
        objective="Implement a safe string reverse utility",
        requires_approval=False
    )
    assert task.state == TaskState.CREATED

    executed = await orch.execute_task(task.task_id)
    assert executed.state == TaskState.COMPLETED
    assert executed.result_data is not None
    assert "Mock synthesis complete." in executed.result_data["response"]


@pytest.mark.asyncio
async def test_approval_valid_officer_approval(test_env):
    """An approval-gated task awaits decision, and completes upon authenticated approval."""
    orch = test_env["orchestrator"]
    from governed_agent import governed_agent

    task = orch.create_task(
        role=AgentRole.DEPLOYMENT_AGENT,
        objective="Deploy release build to staging",
        requires_approval=True,
        inputs={"timeout_seconds": 10.0}
    )

    async def approve_later():
        action_id = None
        for _ in range(50):
            await asyncio.sleep(0.05)
            pending = governed_agent.list_pending()
            matching = [p for p in pending if p.get("payload", {}).get("task_id") == task.task_id]
            if matching:
                action_id = matching[0]["action_id"]
                break
        assert action_id is not None, "Pending approval action was not registered in time."
        # Authenticated approval
        success = governed_agent.submit_decision(
            action_id=action_id,
            approved=True,
            officer_name="Director Jenkins",
            reason="Verified safe for staging."
        )
        assert success is True

    # Run execution and approval concurrently
    exec_task, _ = await asyncio.gather(
        orch.execute_task(task.task_id),
        approve_later()
    )
    assert exec_task.state == TaskState.COMPLETED
    assert exec_task.result_data is not None


@pytest.mark.asyncio
async def test_approval_rejection_flow(test_env):
    """When an officer rejects the action, task fails closed with the rejection reason."""
    orch = test_env["orchestrator"]
    from governed_agent import governed_agent

    task = orch.create_task(
        role=AgentRole.DEPLOYMENT_AGENT,
        objective="Deploy unverified package to live network",
        requires_approval=True,
        inputs={"timeout_seconds": 10.0}
    )

    async def reject_later():
        action_id = None
        for _ in range(50):
            await asyncio.sleep(0.05)
            pending = governed_agent.list_pending()
            matching = [p for p in pending if p.get("payload", {}).get("task_id") == task.task_id]
            if matching:
                action_id = matching[0]["action_id"]
                break
        assert action_id is not None, "Pending approval action was not registered in time."
        success = governed_agent.submit_decision(
            action_id=action_id,
            approved=False,
            officer_name="Security Auditor",
            reason="Rejected: Unverified checksums."
        )
        assert success is True

    exec_task, _ = await asyncio.gather(
        orch.execute_task(task.task_id),
        reject_later()
    )
    assert exec_task.state == TaskState.FAILED
    assert "Rejected" in exec_task.error_message


@pytest.mark.asyncio
async def test_approval_configurable_timeout_flow(test_env):
    """When no decision is received within the configured timeout, task safely expires and fails closed."""
    orch = test_env["orchestrator"]
    task = orch.create_task(
        role=AgentRole.DEPLOYMENT_AGENT,
        objective="Deploy application",
        requires_approval=True,
        inputs={"timeout_seconds": 0.1}  # Fast test timeout
    )
    exec_task = await orch.execute_task(task.task_id, timeout_seconds=0.1)
    assert exec_task.state == TaskState.FAILED
    assert "timed out" in exec_task.error_message.lower()


@pytest.mark.asyncio
async def test_approval_cancellation_flow(test_env):
    """Cancelling a task cancels its pending approval future and transitions to CANCELLED."""
    orch = test_env["orchestrator"]
    task = orch.create_task(
        role=AgentRole.DEPLOYMENT_AGENT,
        objective="Deploy to prod",
        requires_approval=True,
        inputs={"timeout_seconds": 15.0}
    )

    async def cancel_later():
        await asyncio.sleep(0.05)
        orch.cancel_task(task.task_id, reason="Operator aborted execution")

    exec_task, _ = await asyncio.gather(
        orch.execute_task(task.task_id),
        cancel_later()
    )
    assert exec_task.state in (TaskState.CANCELLED, TaskState.FAILED)


def test_idempotent_duplicate_decisions():
    """Submitting duplicate decisions on the same action ID must be idempotent."""
    ctrl = GovernedAgentController()
    action = AgentActionRequest(
        action_type="portal_write",
        target="http://gem.gov.in",
        payload={"tender_id": 99},
        risk_level="HIGH",
        requires_approval=True
    )
    action.payload_hash = action.compute_payload_hash()
    ctrl.pending_approvals[action.action_id] = action

    loop = asyncio.new_event_loop()
    fut = loop.create_future()
    ctrl.approval_futures[action.action_id] = fut

    # First submission
    res1 = ctrl.submit_decision(
        action_id=action.action_id,
        approved=True,
        officer_name="Officer Alpha"
    )
    assert res1 is True

    # Duplicate submission on same action must be idempotent
    res2 = ctrl.submit_decision(
        action_id=action.action_id,
        approved=True,
        officer_name="Officer Alpha"
    )
    assert res2 is True


def test_unauthenticated_blank_officer_rejected():
    """Decisions without a valid officer identity must be rejected."""
    ctrl = GovernedAgentController()
    action = AgentActionRequest(
        action_type="file_modify",
        payload={"file": "critical.config"},
        risk_level="HIGH",
        requires_approval=True
    )
    action.payload_hash = action.compute_payload_hash()
    ctrl.pending_approvals[action.action_id] = action

    loop = asyncio.new_event_loop()
    fut = loop.create_future()
    ctrl.approval_futures[action.action_id] = fut

    success = ctrl.submit_decision(
        action_id=action.action_id,
        approved=True,
        officer_name="   "  # Blank
    )
    assert success is False
    assert not fut.done()


def test_task_persistence_across_reinstantiation(test_env):
    """Task records persist on disk and survive orchestrator re-instantiation."""
    orch = test_env["orchestrator"]
    vault_dir = test_env["vault_dir"]
    ws = test_env["workspace"]
    gw = test_env["gateway"]

    task = orch.create_task(
        role=AgentRole.SECURITY_AGENT,
        objective="Perform threat model sweep",
        requires_approval=False
    )
    task_id = task.task_id

    # Verify persistent file was written
    assert (vault_dir / "orchestrator_tasks.json").exists()

    # Re-instantiate orchestrator from disk
    new_orch = LocalOrchestrator(workspace=ws, gateway=gw, storage_dir=vault_dir)
    loaded_task = new_orch.get_task(task_id)
    assert loaded_task is not None
    assert loaded_task.task_id == task_id
    assert loaded_task.role == AgentRole.SECURITY_AGENT
    assert loaded_task.objective == "Perform threat model sweep"
