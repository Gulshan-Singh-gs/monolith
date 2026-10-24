"""
core/sdlc/generator.py
SDLC Artifact Generation engine that creates structured, verifiable engineering documentation
within the user-authorized workspace.
"""

import time
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

from core.workspace.engine import SecureWorkspaceEngine
from core.skills.registry import SkillRegistry
from core.skills.models import SkillExecutionRequest

logger = logging.getLogger("SDLCGenerator")


class SDLCArtifactGenerator:
    def __init__(
        self,
        workspace: SecureWorkspaceEngine,
        skill_registry: SkillRegistry
    ):
        self.workspace = workspace
        self.skill_registry = skill_registry

    async def generate_sdlc_pack(
        self,
        product_name: str,
        product_description: str,
        technical_stack: str = "Python, FastAPI, Playwright, Modern Vanilla CSS/HTML"
    ) -> Dict[str, Any]:
        """
        Generates full suite of professional SDLC documentation:
        1. docs/product/PRD.md
        2. docs/architecture/ARCHITECTURE.md
        3. docs/security/THREAT_MODEL.md
        4. docs/testing/TEST_PLAN.md
        5. docs/deployment/DEPLOYMENT_PLAN.md
        """
        results = {
            "product_name": product_name,
            "created_artifacts": [],
            "failed_artifacts": []
        }

        specs = [
            {
                "skill_id": "sdlc_prd_generator",
                "rel_path": "docs/product/PRD.md",
                "prompt": f"Project: {product_name}\nDescription: {product_description}\nStack: {technical_stack}"
            },
            {
                "skill_id": "sdlc_architecture_design",
                "rel_path": "docs/architecture/ARCHITECTURE.md",
                "prompt": f"Project: {product_name}\nDescription: {product_description}\nStack: {technical_stack}"
            },
            {
                "skill_id": "security_threat_model",
                "rel_path": "docs/security/THREAT_MODEL.md",
                "prompt": f"Project: {product_name}\nDescription: {product_description}\nStack: {technical_stack}"
            },
            {
                "skill_id": "qa_test_plan_generator",
                "rel_path": "docs/testing/TEST_PLAN.md",
                "prompt": f"Project: {product_name}\nDescription: {product_description}\nStack: {technical_stack}"
            }
        ]

        for item in specs:
            try:
                res = await self.skill_registry.execute_skill(SkillExecutionRequest(
                    skill_id=item["skill_id"],
                    parameters={"input": item["prompt"]}
                ))
                if res.success and res.output_content:
                    self.workspace.write_file(item["rel_path"], res.output_content)
                    results["created_artifacts"].append(item["rel_path"])
                else:
                    results["failed_artifacts"].append({"path": item["rel_path"], "error": res.error})
            except Exception as e:
                logger.error(f"Failed to generate {item['rel_path']}: {e}")
                results["failed_artifacts"].append({"path": item["rel_path"], "error": str(e)})

        return results
