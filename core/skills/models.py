"""
core/skills/models.py
Typed schemas and data models for the Sovereign Workbench Skill Registry.
"""

from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class SkillRiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SkillCategory(str, Enum):
    PRODUCT_PLANNING = "product_planning"
    ARCHITECTURE = "architecture"
    FRONTEND = "frontend"
    BACKEND = "backend"
    TESTING_QA = "testing_qa"
    SECURITY_PRIVACY = "security_privacy"
    DEVOPS_DEPLOYMENT = "devops_deployment"
    RESEARCH = "research"


class SkillDefinition(BaseModel):
    id: str
    name: str
    description: str
    category: SkillCategory
    version: str = "1.0.0"
    risk_level: SkillRiskLevel = SkillRiskLevel.LOW
    requires_approval: bool = False
    authorized_tools: List[str] = Field(default_factory=list)
    system_prompt_template: str
    expected_outputs: List[str] = Field(default_factory=list)


class SkillExecutionRequest(BaseModel):
    skill_id: str
    workspace_context: Optional[str] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)
    privacy_mode_override: Optional[str] = None


class SkillExecutionResult(BaseModel):
    skill_id: str
    success: bool
    output_content: str
    artifacts_created: List[str] = Field(default_factory=list)
    execution_time_seconds: float = 0.0
    error: Optional[str] = None
