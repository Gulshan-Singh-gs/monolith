"""
core/skills/registry.py
Skill Registry maintaining versioned, governed software engineering skills.
"""

import time
import logging
from typing import Dict, List, Optional

from core.skills.models import (
    SkillDefinition,
    SkillCategory,
    SkillRiskLevel,
    SkillExecutionRequest,
    SkillExecutionResult
)
from core.interfaces.model_gateway import InferenceRequest, PrivacyMode
from core.gateway.router import SovereignModelGateway
from core.workspace.engine import SecureWorkspaceEngine
from governed_agent import governed_agent

logger = logging.getLogger("SkillRegistry")


class SkillRegistry:
    def __init__(
        self,
        gateway: Optional[SovereignModelGateway] = None,
        workspace: Optional[SecureWorkspaceEngine] = None
    ):
        self.gateway = gateway or SovereignModelGateway()
        self.workspace = workspace or SecureWorkspaceEngine()
        self._skills: Dict[str, SkillDefinition] = {}
        self._register_builtin_skills()

    def register(self, skill: SkillDefinition) -> None:
        self._skills[skill.id] = skill
        logger.info(f"Registered skill: {skill.id} ({skill.name})")

    def get_skill(self, skill_id: str) -> Optional[SkillDefinition]:
        return self._skills.get(skill_id)

    def list_skills(self, category: Optional[SkillCategory] = None) -> List[SkillDefinition]:
        if category:
            return [s for s in self._skills.values() if s.category == category]
        return list(self._skills.values())

    def _register_builtin_skills(self) -> None:
        # 1. PRD Generation
        self.register(SkillDefinition(
            id="sdlc_prd_generator",
            name="Product Requirements Document Generator",
            description="Analyzes user product requirements and outputs a structured PRD with personas, acceptance criteria, and constraints.",
            category=SkillCategory.PRODUCT_PLANNING,
            risk_level=SkillRiskLevel.LOW,
            requires_approval=False,
            authorized_tools=["read_file"],
            system_prompt_template=(
                "You are an expert Principal Product Architect. Given the user's project requirements, generate a thorough "
                "Product Requirements Document (PRD) in Markdown. Include Executive Summary, User Personas, Functional Requirements, "
                "Non-Functional Requirements, and Acceptance Criteria."
            ),
            expected_outputs=["PRD.md"]
        ))

        # 2. Architecture & Decision Record (ADR)
        self.register(SkillDefinition(
            id="sdlc_architecture_design",
            name="System Architecture & ADR Designer",
            description="Produces technical architecture specifications, data models, component boundaries, and Architecture Decision Records.",
            category=SkillCategory.ARCHITECTURE,
            risk_level=SkillRiskLevel.LOW,
            requires_approval=False,
            authorized_tools=["read_file", "list_files"],
            system_prompt_template=(
                "You are a Chief Software Architect. Given the project description and existing files, generate a complete "
                "Technical Architecture Specification and Architecture Decision Record (ADR). Specify system boundaries, "
                "data flow, API contracts, and technology trade-offs."
            ),
            expected_outputs=["ARCHITECTURE.md", "ADR_001.md"]
        ))

        # 3. Security Threat Model
        self.register(SkillDefinition(
            id="security_threat_model",
            name="STRIDE Threat Model & Security Evaluation",
            description="Performs STRIDE threat modeling, trust boundary evaluation, and input validation analysis.",
            category=SkillCategory.SECURITY_PRIVACY,
            risk_level=SkillRiskLevel.MEDIUM,
            requires_approval=False,
            authorized_tools=["read_file", "list_files"],
            system_prompt_template=(
                "You are a Senior Application Security Engineer. Evaluate the project architecture against OWASP and STRIDE threat models. "
                "Identify trust boundaries, secret exposure risks, injection surfaces, and provide actionable remediation guidelines."
            ),
            expected_outputs=["THREAT_MODEL.md"]
        ))

        # 4. QA & Test Plan Generator
        self.register(SkillDefinition(
            id="qa_test_plan_generator",
            name="QA Test Strategy & Test Plan Designer",
            description="Formulates unit, integration, boundary, and regression test suites with pytest execution strategy.",
            category=SkillCategory.TESTING_QA,
            risk_level=SkillRiskLevel.LOW,
            requires_approval=False,
            authorized_tools=["read_file", "list_files"],
            system_prompt_template=(
                "You are a Lead Quality Assurance Engineer. Develop a comprehensive Test Strategy and Test Plan for this project. "
                "Outline unit tests, integration tests, security regression tests, and end-to-end verification steps."
            ),
            expected_outputs=["TEST_PLAN.md"]
        ))

        # 5. Secure Code Reviewer
        self.register(SkillDefinition(
            id="code_review_audit",
            name="Independent Code Review & Diff Inspector",
            description="Independently evaluates code diffs for security weaknesses, performance bottlenecks, and style compliance.",
            category=SkillCategory.BACKEND,
            risk_level=SkillRiskLevel.LOW,
            requires_approval=False,
            authorized_tools=["read_file"],
            system_prompt_template=(
                "You are a Principal Software Quality and Security Reviewer. Inspect the provided code or diff. "
                "Report bugs, edge cases, security vulnerabilities, and code smell, and suggest idiomatic improvements."
            ),
            expected_outputs=["CODE_REVIEW.md"]
        ))

        # 6. Cloudflare & GitHub Deployment Planner
        self.register(SkillDefinition(
            id="devops_deployment_preparer",
            name="Cloudflare & GitHub Deployment Preparer",
            description="Prepares wrangler.toml / GitHub release workflow, performs pre-deployment secret scanning, and outlines rollback steps.",
            category=SkillCategory.DEVOPS_DEPLOYMENT,
            risk_level=SkillRiskLevel.HIGH,
            requires_approval=True,
            authorized_tools=["read_file", "list_files"],
            system_prompt_template=(
                "You are a DevSecOps and Release Engineer. Prepare the production release configuration for Cloudflare Pages/Workers "
                "and GitHub. Validate environment variables, check for secret leakage, and define automated smoke test and rollback plans."
            ),
            expected_outputs=["DEPLOYMENT_PLAN.md"]
        ))

    async def execute_skill(self, request: SkillExecutionRequest) -> SkillExecutionResult:
        skill = self._skills.get(request.skill_id)
        if not skill:
            return SkillExecutionResult(
                skill_id=request.skill_id,
                success=False,
                output_content="",
                error=f"Skill '{request.skill_id}' not found in registry."
            )

        start_time = time.time()

        # Gate check for HIGH or CRITICAL risk skills
        if skill.requires_approval or skill.risk_level in (SkillRiskLevel.HIGH, SkillRiskLevel.CRITICAL):
            gate_res = await governed_agent.evaluate_and_gate(
                action_type=f"skill_execution_{skill.id}",
                description=f"Execute privileged skill: {skill.name}",
                payload={"skill_id": skill.id, "parameters": request.parameters}
            )
            if not gate_res.is_allowed:
                return SkillExecutionResult(
                    skill_id=skill.id,
                    success=False,
                    output_content="",
                    execution_time_seconds=time.time() - start_time,
                    error="Skill execution blocked: Denied by authorized governance officer."
                )

        try:
            user_input = request.parameters.get("input", "") or "Execute standard analysis for current workspace."
            context_snippet = f"\n\nWorkspace Context:\n{request.workspace_context}" if request.workspace_context else ""
            full_prompt = f"{user_input}{context_snippet}"

            inf_req = InferenceRequest(
                prompt=full_prompt,
                system_prompt=skill.system_prompt_template,
                privacy_mode=self.gateway.get_privacy_mode()
            )

            res = await self.gateway.generate(inf_req)
            duration = time.time() - start_time

            return SkillExecutionResult(
                skill_id=skill.id,
                success=True,
                output_content=res.content,
                artifacts_created=skill.expected_outputs,
                execution_time_seconds=duration
            )
        except Exception as e:
            logger.error(f"Error executing skill {skill.id}: {e}")
            return SkillExecutionResult(
                skill_id=skill.id,
                success=False,
                output_content="",
                execution_time_seconds=time.time() - start_time,
                error=str(e)
            )
