"""
core/orchestrator/orchestrator.py
Local Orchestrator Agent coordinating task decomposition, agent delegation,
SDLC planning, and human approval verification with durable persistence and lifecycle gating.
"""

import os
import json
import time
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

from core.interfaces.agent import (
    AgentTaskContract,
    TaskState,
    AgentRole
)
from core.interfaces.model_gateway import PrivacyMode, InferenceRequest
from core.gateway.router import SovereignModelGateway
from core.workspace.engine import SecureWorkspaceEngine
from core.verification.quality_gates import QualityGateEngine
from governed_agent import governed_agent
from audit_ledger import audit_ledger

logger = logging.getLogger("Orchestrator")


class LocalOrchestrator:
    def __init__(
        self,
        workspace: Optional[SecureWorkspaceEngine] = None,
        gateway: Optional[SovereignModelGateway] = None,
        storage_dir: Optional[Path] = None
    ):
        self.workspace = workspace or SecureWorkspaceEngine()
        self.gateway = gateway or SovereignModelGateway()
        self.quality_gates = QualityGateEngine(
            workspace_root=self.workspace.get_root(),
            broker=self.workspace.execution_broker
        )
        self.storage_dir = storage_dir or (Path(__file__).resolve().parent.parent.parent / "output" / ".vault")
        self.tasks_file = self.storage_dir / "orchestrator_tasks.json"
        self._tasks: Dict[str, AgentTaskContract] = {}
        self._load_persisted_tasks()

    def _load_persisted_tasks(self) -> None:
        try:
            if self.tasks_file.exists():
                data = json.loads(self.tasks_file.read_text(encoding="utf-8"))
                for t_dict in data.get("tasks", []):
                    task = AgentTaskContract(**t_dict)
                    self._tasks[task.task_id] = task
        except Exception as e:
            logger.warning(f"Failed to load persisted tasks: {e}")

    def _persist_tasks(self) -> None:
        try:
            self.storage_dir.mkdir(parents=True, exist_ok=True)
            payload = {
                "tasks": [t.model_dump() for t in self._tasks.values()]
            }
            tmp = self.tasks_file.with_suffix(".tmp")
            tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
            tmp.replace(self.tasks_file)
        except Exception as e:
            logger.warning(f"Failed to persist orchestrator tasks: {e}")

    def create_task(
        self,
        role: AgentRole,
        objective: str,
        inputs: Optional[Dict[str, Any]] = None,
        requires_approval: bool = False
    ) -> AgentTaskContract:
        task = AgentTaskContract(
            role=role,
            objective=objective,
            inputs=inputs or {},
            state=TaskState.CREATED,
            requires_human_approval=requires_approval
        )
        self._tasks[task.task_id] = task
        self._persist_tasks()

        audit_ledger.record_event(
            event_type="TASK_CREATED",
            action=f"Created task {task.task_id} [{task.role.value}]: {objective}",
            actor="ORCHESTRATOR",
            risk_level="HIGH" if requires_approval else "LOW",
            details={"task_id": task.task_id, "role": task.role.value}
        )
        return task

    def get_task(self, task_id: str) -> Optional[AgentTaskContract]:
        return self._tasks.get(task_id)

    def list_tasks(self) -> List[AgentTaskContract]:
        return list(self._tasks.values())

    def pause_task(self, task_id: str) -> Optional[AgentTaskContract]:
        task = self._tasks.get(task_id)
        if task and task.state in (TaskState.RUNNING, TaskState.READY, TaskState.AWAITING_APPROVAL):
            task.state = TaskState.PAUSED
            task.updated_at = time.time()
            self._persist_tasks()
        return task

    def resume_task(self, task_id: str) -> Optional[AgentTaskContract]:
        task = self._tasks.get(task_id)
        if task and task.state == TaskState.PAUSED:
            task.state = TaskState.READY
            task.updated_at = time.time()
            self._persist_tasks()
        return task

    def cancel_task(self, task_id: str, reason: str = "Cancelled by user.") -> Optional[AgentTaskContract]:
        task = self._tasks.get(task_id)
        if not task:
            return None
        if task.state == TaskState.AWAITING_APPROVAL:
            approval_id = task.inputs.get("approval_action_id")
            if approval_id:
                governed_agent.cancel_approval(approval_id, reason=reason)
        task.state = TaskState.CANCELLED
        task.error_message = reason
        task.updated_at = time.time()
        self._persist_tasks()

        audit_ledger.record_event(
            event_type="TASK_CANCELLED",
            action=f"Task {task_id} cancelled: {reason}",
            actor="ORCHESTRATOR",
            risk_level="LOW",
            details={"task_id": task_id}
        )
        return task

    async def execute_task(self, task_id: str, timeout_seconds: Optional[float] = None) -> AgentTaskContract:
        task = self._tasks.get(task_id)
        if not task:
            raise ValueError(f"Task '{task_id}' not found.")

        # 1. VALIDATING
        task.state = TaskState.VALIDATING
        task.updated_at = time.time()
        self._persist_tasks()

        if not task.objective or not task.objective.strip():
            task.state = TaskState.FAILED
            task.error_message = "Task objective cannot be empty."
            task.updated_at = time.time()
            self._persist_tasks()
            return task

        # 2. PLANNING
        task.state = TaskState.PLANNING
        task.updated_at = time.time()
        self._persist_tasks()

        # Determine effective approval timeout
        effective_timeout = timeout_seconds or task.inputs.get("timeout_seconds", 300.0)

        # 3. READY
        task.state = TaskState.READY
        task.updated_at = time.time()
        self._persist_tasks()

        # HITL Approval Gate if high-impact or explicitly required
        if task.requires_human_approval:
            task.state = TaskState.AWAITING_APPROVAL
            task.updated_at = time.time()
            self._persist_tasks()

            action_payload = {
                "task_id": task.task_id,
                "role": task.role.value,
                "objective": task.objective
            }

            gate_res = await governed_agent.evaluate_and_gate(
                action_type="agent_task_execution",
                description=f"Execute {task.role.value} for objective: {task.objective}",
                payload=action_payload,
                timeout_seconds=effective_timeout,
                force_approval=True
            )
            task.inputs["approval_action_id"] = gate_res.action_id

            if not gate_res.is_allowed:
                task.state = TaskState.FAILED
                task.error_message = gate_res.decision_reason or "Action rejected by authorized officer."
                task.updated_at = time.time()
                self._persist_tasks()
                return task

            # Revalidate payload immediately before running
            expected_hash = gate_res.compute_payload_hash()
            if gate_res.payload_hash and expected_hash != gate_res.payload_hash:
                task.state = TaskState.FAILED
                task.error_message = "Security check failed: Action payload tampered before execution."
                task.updated_at = time.time()
                self._persist_tasks()
                return task

        # 4. RUNNING
        task.state = TaskState.RUNNING
        task.updated_at = time.time()
        self._persist_tasks()

        try:
            # Plan generation / task synthesis via model gateway
            sys_prompt = f"You are a specialized sovereign {task.role.value} agent. Complete the user objective accurately."
            inf_req = InferenceRequest(
                prompt=task.objective,
                system_prompt=sys_prompt,
                privacy_mode=self.gateway.get_privacy_mode()
            )
            response = await self.gateway.generate(inf_req)

            # 5. VERIFYING
            task.state = TaskState.VERIFYING
            task.updated_at = time.time()
            self._persist_tasks()

            if not response.content or not response.content.strip():
                raise ValueError("Model produced empty response.")

            # Run quality gate verification if code was modified
            modified_files = task.inputs.get("modified_files", [])
            gate_report = None
            if modified_files:
                gate_report = await self.quality_gates.execute_verification_pipeline(
                    modified_files=modified_files,
                    run_full_suite=False
                )

            task.result_data = {
                "response": response.content,
                "model_used": response.model_used,
                "latency_seconds": response.latency_seconds,
                "verification_report": gate_report.model_dump() if gate_report else None
            }

            if gate_report and gate_report.verdict == "FAILED":
                task.state = TaskState.FAILED
                task.error_message = f"Quality gate verification failed: {gate_report.failed_count} check(s) failed."
                task.updated_at = time.time()
                self._persist_tasks()
                return task

            # 6. COMPLETED
            task.state = TaskState.COMPLETED
            task.error_message = None

            audit_ledger.record_event(
                event_type="TASK_COMPLETED",
                action=f"Task {task.task_id} completed successfully",
                actor="ORCHESTRATOR",
                risk_level="LOW",
                details={"task_id": task.task_id, "model_used": response.model_used}
            )
        except Exception as e:
            task.state = TaskState.FAILED
            task.error_message = str(e)
            logger.error(f"Task execution failed: {e}")

            audit_ledger.record_event(
                event_type="TASK_FAILED",
                action=f"Task {task.task_id} failed: {e}",
                actor="ORCHESTRATOR",
                risk_level="MEDIUM",
                details={"task_id": task.task_id, "error": str(e)}
            )

        task.updated_at = time.time()
        self._persist_tasks()
        return task
