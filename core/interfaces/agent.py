"""
core/interfaces/agent.py
Typed task contracts, execution states, and role definitions for multi-agent software engineering.
"""

from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
import uuid
import time


class TaskState(str, Enum):
    CREATED = "CREATED"
    VALIDATING = "VALIDATING"
    PLANNING = "PLANNING"
    READY = "READY"
    RUNNING = "RUNNING"
    VERIFYING = "VERIFYING"
    AWAITING_APPROVAL = "AWAITING_APPROVAL"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    PAUSED = "PAUSED"
    CANCELLED = "CANCELLED"


class AgentRole(str, Enum):
    ORCHESTRATOR = "ORCHESTRATOR"
    REQUIREMENTS_ANALYST = "REQUIREMENTS_ANALYST"
    ARCHITECT = "ARCHITECT"
    IMPLEMENTATION_PLANNER = "IMPLEMENTATION_PLANNER"
    CODING_AGENT = "CODING_AGENT"
    CODE_REVIEWER = "CODE_REVIEWER"
    TESTING_AGENT = "TESTING_AGENT"
    SECURITY_AGENT = "SECURITY_AGENT"
    DEPLOYMENT_AGENT = "DEPLOYMENT_AGENT"


class AgentTaskContract(BaseModel):
    task_id: str = Field(default_factory=lambda: f"TASK-{uuid.uuid4().hex[:8].upper()}")
    parent_task_id: Optional[str] = None
    role: AgentRole
    objective: str
    inputs: Dict[str, Any] = Field(default_factory=dict)
    expected_outputs: List[str] = Field(default_factory=list)
    authorized_tools: List[str] = Field(default_factory=list)
    state: TaskState = TaskState.CREATED
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)
    result_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    requires_human_approval: bool = False
