"""
tests/test_agent_roles.py
Comprehensive regression tests for AgentRole parsing and validation.
Verifies that:
1. All documented AgentRole enum values are accepted case-insensitively and with underscores/hyphens.
2. Invalid roles are rejected with clear HTTP 400 validation errors, never silently defaulting to ORCHESTRATOR.
3. Tasks reach the intended agent role.
"""

import pytest
from fastapi.testclient import TestClient
from core.interfaces.agent import AgentRole
from server import app


class TestAgentRoleValidation:
    @pytest.fixture(autouse=True)
    def setup_client(self):
        self.client = TestClient(app)

    def test_all_supported_roles_parse_case_insensitively(self):
        """Every supported role must resolve to its corresponding AgentRole enum."""
        supported_roles = [
            ("ORCHESTRATOR", AgentRole.ORCHESTRATOR),
            ("orchestrator", AgentRole.ORCHESTRATOR),
            ("REQUIREMENTS_ANALYST", AgentRole.REQUIREMENTS_ANALYST),
            ("requirements_analyst", AgentRole.REQUIREMENTS_ANALYST),
            ("requirements-analyst", AgentRole.REQUIREMENTS_ANALYST),
            ("ARCHITECT", AgentRole.ARCHITECT),
            ("architect", AgentRole.ARCHITECT),
            ("IMPLEMENTATION_PLANNER", AgentRole.IMPLEMENTATION_PLANNER),
            ("implementation_planner", AgentRole.IMPLEMENTATION_PLANNER),
            ("CODING_AGENT", AgentRole.CODING_AGENT),
            ("coding_agent", AgentRole.CODING_AGENT),
            ("coding-agent", AgentRole.CODING_AGENT),
            ("CODE_REVIEWER", AgentRole.CODE_REVIEWER),
            ("code_reviewer", AgentRole.CODE_REVIEWER),
            ("TESTING_AGENT", AgentRole.TESTING_AGENT),
            ("testing_agent", AgentRole.TESTING_AGENT),
            ("SECURITY_AGENT", AgentRole.SECURITY_AGENT),
            ("security_agent", AgentRole.SECURITY_AGENT),
            ("DEPLOYMENT_AGENT", AgentRole.DEPLOYMENT_AGENT),
            ("deployment_agent", AgentRole.DEPLOYMENT_AGENT),
        ]
        for role_str, expected_enum in supported_roles:
            parsed = AgentRole.from_string(role_str)
            assert parsed == expected_enum, f"Failed to parse '{role_str}' into {expected_enum}"

    def test_invalid_roles_raise_value_error(self):
        """Invalid or maliciously formed role strings must raise ValueError."""
        invalid_inputs = [
            "hacker", "admin", "root", "unauthorized_role",
            "super_agent", "sudo", "", "   ", "orchestrator_fake"
        ]
        for invalid in invalid_inputs:
            with pytest.raises(ValueError) as excinfo:
                AgentRole.from_string(invalid)
            assert "Permissible roles" in str(excinfo.value) or "Invalid role" in str(excinfo.value)

    def test_api_accepts_valid_roles_and_creates_task(self):
        """API /api/orchestrator/tasks must create a task with the intended role."""
        test_cases = [
            ("coding_agent", "CODING_AGENT"),
            ("SECURITY_AGENT", "SECURITY_AGENT"),
            ("requirements-analyst", "REQUIREMENTS_ANALYST"),
            ("testing_agent", "TESTING_AGENT"),
            ("deployment_agent", "DEPLOYMENT_AGENT")
        ]
        for role_input, expected_stored_role in test_cases:
            resp = self.client.post("/api/orchestrator/tasks", json={
                "role": role_input,
                "objective": f"Test task for {role_input}",
                "requires_approval": False
            })
            assert resp.status_code == 200, f"Expected 200 for role '{role_input}', got {resp.status_code}: {resp.text}"
            data = resp.json()
            assert data["role"] == expected_stored_role, (
                f"Expected role {expected_stored_role}, but got {data['role']}. Role must not silently default!"
            )

    def test_api_rejects_invalid_role_with_http_400(self):
        """API /api/orchestrator/tasks must reject invalid roles with HTTP 400."""
        invalid_roles = ["invalid_role_xyz", "hacker", "system_admin", ""]
        for invalid in invalid_roles:
            resp = self.client.post("/api/orchestrator/tasks", json={
                "role": invalid,
                "objective": "Unauthorized attempt",
                "requires_approval": False
            })
            assert resp.status_code == 400, (
                f"Expected HTTP 400 for invalid role '{invalid}', but got {resp.status_code}: {resp.text}"
            )
            data = resp.json()
            assert "Permissible roles" in data.get("detail", "") or "Invalid role" in data.get("detail", "")
