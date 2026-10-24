"""
core/orchestrator/orchestrator.py
Local Orchestrator Agent coordinating task decomposition, agent delegation,
SDLC planning, and human approval verification.
"""

import time
import logging
from typing import Dict, Any, List, Optional

from core.interfaces.agent import (
    AgentTaskContract,
    TaskState,
    AgentRole
)
from core.interfaces.model_gateway import PrivacyMode, InferenceRequest
from core.gateway.router import SovereignModelGateway
from core.workspace.engine import SecureWorkspaceEngine
from governed_agent import governed_agent

logger = logging.getLogger("Orchestrator")


class LocalOrchestrator:
    def __init__(
        self,
        workspace: Optional[SecureWorkspaceEngine] = None,
        gateway: Optional[SovereignModelGateway] = None
    ):
        self.workspace = workspace or SecureWorkspaceEngine()
        self.gateway = gateway or SovereignModelGateway()
        self._tasks: Dict[str, AgentTaskContract] = {}

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
        return task

    def get_task(self, task_id: str) -> Optional[AgentTaskContract]:
        return self._tasks.get(task_id)

    def list_tasks(self) -> List[AgentTaskContract]:
        return list(self._tasks.values())

    async def execute_task(self, task_id: str) -> AgentTaskContract:
        task = self._tasks.get(task_id)
        if not task:
            raise ValueError(f"Task '{task_id}' not found.")

        task.state = TaskState.RUNNING
        task.updated_at = time.time()

        # HITL Approval Gate if high-impact or explicitly required
        if task.requires_human_approval:
            task.state = TaskState.AWAITING_APPROVAL
            gate_res = await governed_agent.evaluate_and_gate(
                action_type="agent_task_execution",
                description=f"Execute {task.role.value} for objective: {task.objective}",
                payload={"task_id": task.task_id, "role": task.role.value},
                timeout_seconds=0.1,
                force_approval=True
            )
            if not gate_res.is_allowed:
                task.state = TaskState.FAILED
                task.error_message = gate_res.decision_reason or "Action rejected by authorized officer."
                return task
            task.state = TaskState.RUNNING

        try:
            # Plan generation / task synthesis via model gateway
            sys_prompt = f"You are a specialized sovereign {task.role.value} agent. Complete the user objective accurately."
            inf_req = InferenceRequest(
                prompt=task.objective,
                system_prompt=sys_prompt,
                privacy_mode=self.gateway.get_privacy_mode()
            )
            response = await self.gateway.generate(inf_req)

            task.result_data = {
                "response": response.content,
                "model_used": response.model_used,
                "latency_seconds": response.latency_seconds
            }
            task.state = TaskState.COMPLETED
        except Exception as e:
            task.state = TaskState.FAILED
            task.error_message = str(e)
            logger.error(f"Task execution failed: {e}")

        task.updated_at = time.time()
        return task
