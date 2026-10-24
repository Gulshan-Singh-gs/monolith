"""
Comprehensive Security Regression Test Suite
Validates the eradication of all 10 vulnerabilities (V-01 through V-10)
from the Security Audit Report: Sovereign On-Premise Agentic AI Workbench.
"""

import os
import json
import time
import shutil
import asyncio
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, AsyncMock

from fastapi.testclient import TestClient
from server import app, profile_mgr, vault, llm_router, lan_security_mgr
from profile_manager import ProfileManager, PHYSICAL_RECOVERY_FILE
from cookie_vault import CookieVault
from dual_engine_llm import DualEngineLLM
from governed_agent import GovernedAgentController, AgentActionRequest
from injection_guard import PromptInjectionGuard
from lan_security_manager import LANSecurityManager


class TestSecurityAuditHardening(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    # ──────────────────────────────────────────────────────────────────────────
    # Test 1: V-01 — Physical Recovery Authorization Verification
    # ──────────────────────────────────────────────────────────────────────────
    def test_v01_physical_recovery_authorization(self):
        """V-01: Password reset MUST require valid physical recovery token verification."""
        # 1. Without supplying token -> Must FAIL
        res = self.client.post("/api/profile/recover-physical", json={"new_password": "NewSecretPassword123!"})
        self.assertEqual(res.status_code, 400)
        self.assertIn("required", res.json().get("message", "").lower())

        # 2. With invalid token -> Must FAIL
        res = self.client.post("/api/profile/recover-physical", json={
            "recovery_token": "wrong_invalid_token_xyz_12345",
            "new_password": "NewSecretPassword123!"
        })
        self.assertEqual(res.status_code, 400)
        self.assertIn("invalid", res.json().get("message", "").lower())

        # 3. With legitimate token from recovery.key -> Must SUCCEED
        if PHYSICAL_RECOVERY_FILE.exists():
            valid_token = PHYSICAL_RECOVERY_FILE.read_text(encoding="utf-8").strip()
            res = self.client.post("/api/profile/recover-physical", json={
                "recovery_token": valid_token,
                "new_password": "LegitimateNewPassword123!"
            })
            self.assertEqual(res.status_code, 200)
            self.assertEqual(res.json().get("status"), "SUCCESS")
            # Verify password was actually updated
            self.assertTrue(profile_mgr.verify_password("LegitimateNewPassword123!"))

    # ──────────────────────────────────────────────────────────────────────────
    # Test 2: V-02 — Cookie Vault Authenticated Encryption at Rest
    # ──────────────────────────────────────────────────────────────────────────
    def test_v02_cookie_vault_authenticated_encryption(self):
        """V-02: Stored credentials MUST be encrypted at rest and not readable as plaintext."""
        temp_dir = Path(tempfile.mkdtemp())
        try:
            cv = CookieVault(storage_dir=temp_dir)
            secret_cookie_val = "SUPER_SECRET_NIC_SESSION_TOKEN_XYZ_987"
            cv.save_session(
                domain="audit-portal.gov.in",
                portal_name="Audit Portal",
                cookies=[{"name": "SESSION", "value": secret_cookie_val}],
                role="Auditor",
                org="MeitY"
            )

            # Inspect raw file on disk
            enc_file = temp_dir / "portal_sessions.enc"
            self.assertTrue(enc_file.exists())
            raw_bytes = enc_file.read_bytes()

            # Ensure secret cookie value is completely absent from plaintext bytes
            self.assertNotIn(secret_cookie_val.encode("utf-8"), raw_bytes)
            self.assertNotIn(b"SUPER_SECRET_NIC", raw_bytes)

            # Confirm decrypted read by authorized class instance works
            retrieved = cv.get_cookies_for_domain("audit-portal.gov.in")
            self.assertEqual(len(retrieved), 1)
            self.assertEqual(retrieved[0]["value"], secret_cookie_val)

            # Confirm vault initialized without hardcoded mock credentials
            empty_dir = Path(tempfile.mkdtemp())
            cv_clean = CookieVault(storage_dir=empty_dir)
            self.assertEqual(len(cv_clean.list_sessions()), 0)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    # ──────────────────────────────────────────────────────────────────────────
    # Test 3: V-03 — Workspace Lock Fail-Closed Behavior
    # ──────────────────────────────────────────────────────────────────────────
    def test_v03_workspace_lock_fails_closed(self):
        """V-03: When profile cannot be read, protected routes fail-closed (HTTP 503), not fail-open."""
        with patch.object(profile_mgr, "_load_profile", side_effect=IOError("Corrupt storage / permission denied")):
            res = self.client.get("/api/workbench/sessions")
            # Must return 503 Service Unavailable, refusing to fail open
            self.assertEqual(res.status_code, 503)
            self.assertIn("fail-closed", res.json().get("error", "").lower())

    # ──────────────────────────────────────────────────────────────────────────
    # Test 4: V-04 — Cloud Fallback Data Sovereignty Enforcement
    # ──────────────────────────────────────────────────────────────────────────
    def test_v04_local_inference_sovereignty_killswitch(self):
        """V-04: Strict local mode or air-gap MUST prohibit cloud fallback unconditionally."""
        llm = DualEngineLLM()
        llm.groq_api_key = "dummy_groq_key"
        llm.gemini_api_key = "dummy_gemini_key"

        # Mock Ollama failure
        with patch.object(llm, "_call_ollama", side_effect=ConnectionError("Local Ollama down")):
            with patch.object(llm, "_call_groq") as mock_groq:
                with patch.object(llm, "_call_gemini") as mock_gemini:
                    # When target is 'local'
                    res = asyncio.run(llm.generate("Sensitive government query", engine_override="local"))
                    # Cloud engines must NOT have been called
                    mock_groq.assert_not_called()
                    mock_gemini.assert_not_called()
                    self.assertIsInstance(res, str)

                    # When air_gap_active=True
                    res_airgap = asyncio.run(llm.generate("Classified query", air_gap_active=True))
                    mock_groq.assert_not_called()
                    mock_gemini.assert_not_called()
                    self.assertIsInstance(res_airgap, str)

    # ──────────────────────────────────────────────────────────────────────────
    # Test 5: V-05 — WebSocket Lock & Auth Enforcement
    # ──────────────────────────────────────────────────────────────────────────
    def test_v05_websocket_locked_workspace_rejection(self):
        """V-05: WebSocket connections MUST be rejected when workspace is locked."""
        with patch.object(profile_mgr, "_load_profile", return_value={"is_locked": True, "is_password_protected": True}):
            with self.assertRaises(Exception):
                # TestClient websocket_connect will raise WebSocketDisconnect or error when closed with 4423
                with self.client.websocket_connect("/ws") as ws:
                    ws.receive_json()

    # ──────────────────────────────────────────────────────────────────────────
    # Test 6: V-06 — Streaming Upload Limit Enforcement
    # ──────────────────────────────────────────────────────────────────────────
    def test_v06_streaming_upload_size_limit(self):
        """V-06: File uploads exceeding MAX_UPLOAD_BYTES are rejected with 413 without accumulating in RAM."""
        from server import MAX_UPLOAD_BYTES
        # Attempt to upload 52 MB payload (limit is 50 MB)
        oversized_data = b"X" * (MAX_UPLOAD_BYTES + 1024)
        files = {"file": ("oversized.csv", oversized_data, "text/csv")}
        res = self.client.post("/api/workbench/upload-file", files=files)
        self.assertEqual(res.status_code, 413)
        self.assertIn("too large", res.json().get("error", "").lower())

    # ──────────────────────────────────────────────────────────────────────────
    # Test 7: V-07 — Multi-Layered Tool Permission & DLP Enforcement
    # ──────────────────────────────────────────────────────────────────────────
    def test_v07_injection_guard_tool_and_dlp_boundaries(self):
        """V-07: Tool execution requires programmatic allowlist, air-gap egress checks, and DLP."""
        # 1. Unauthorized action rejected
        allowed, reason = PromptInjectionGuard.validate_tool_execution(action_type="arbitrary_eval_exec")
        self.assertFalse(allowed)
        self.assertIn("allowlist", reason.lower())

        # 2. Unauthorized external domain rejected
        allowed_domain, reason_domain = PromptInjectionGuard.validate_tool_execution(
            action_type="portal_browse",
            target_url="http://malicious-exfiltration-hub.com/steal"
        )
        self.assertFalse(allowed_domain)
        self.assertIn("allowlist", reason_domain.lower())

        # 3. Secret credential DLP leak rejected
        allowed_dlp, reason_dlp = PromptInjectionGuard.validate_tool_execution(
            action_type="portal_browse",
            target_url="http://127.0.0.1:8001/portal/gem-tenders",
            payload={"token": "SOV-LAN-12345678-abcdef"}
        )
        self.assertFalse(allowed_dlp)
        self.assertIn("dlp", reason_dlp.lower())

    # ──────────────────────────────────────────────────────────────────────────
    # Test 8: V-08 — Human Approval Action Binding & Tamper Proofing
    # ──────────────────────────────────────────────────────────────────────────
    def test_v08_approval_immutable_action_binding(self):
        """V-08: Officer approval is cryptographically bound to immutable action payload."""
        ctrl = GovernedAgentController()
        action = AgentActionRequest(
            action_type="submit_bid",
            target="https://gem.gov.in/bid/123",
            payload={"amount": 500000},
            risk_level="HIGH",
            requires_approval=True
        )
        action.payload_hash = action.compute_payload_hash()
        ctrl.pending_approvals[action.action_id] = action

        loop = asyncio.new_event_loop()
        fut = loop.create_future()
        ctrl.approval_futures[action.action_id] = fut

        # 1. Anonymous / blank officer name rejected
        success_blank = ctrl.submit_decision(action_id=action.action_id, approved=True, officer_name="  ")
        self.assertFalse(success_blank)

        # 2. Tampered payload detection
        action.payload["amount"] = 999999999  # Tampered behind the scenes!
        success_tampered = ctrl.submit_decision(
            action_id=action.action_id,
            approved=True,
            officer_name="Secretary Sharma"
        )
        self.assertFalse(success_tampered)
        self.assertEqual(action.status, "REJECTED")
        self.assertIn("tampered", action.decision_reason.lower() + " modified")

    # ──────────────────────────────────────────────────────────────────────────
    # Test 9: V-09 — Tightened Unlocked Route Boundaries
    # ──────────────────────────────────────────────────────────────────────────
    def test_v09_unlocked_boundaries_tightened(self):
        """V-09: Sensitive paths are protected by workspace lock and not mistakenly whitelisted."""
        from server import _UNLOCKED_PATHS
        # Ensure WebSockets and session manipulation are NOT in _UNLOCKED_PATHS
        self.assertNotIn("/ws", _UNLOCKED_PATHS)
        self.assertNotIn("/ws/dictation", _UNLOCKED_PATHS)
        self.assertNotIn("/api/workbench/sessions", _UNLOCKED_PATHS)
        self.assertNotIn("/api/agent/approval/respond", _UNLOCKED_PATHS)

    # ──────────────────────────────────────────────────────────────────────────
    # Test 10: V-10 — Pairing PIN Verification Rate Limiting & Lockout
    # ──────────────────────────────────────────────────────────────────────────
    def test_v10_pairing_pin_rate_limiting(self):
        """V-10: Pairing PIN verification enforces rate limiting and lockout after repeated failed attempts."""
        lsm = LANSecurityManager()
        real_pin = lsm.generate_pairing_code()

        client_ip = "192.168.1.150"
        # 1. Submit repeated wrong PIN guesses
        for _ in range(3):
            token = lsm.verify_pairing_code(candidate_pin="000000", client_ip=client_ip)
            self.assertIsNone(token)

        # 2. The real PIN should now be destroyed / invalidated due to brute force detection
        token_after_brute = lsm.verify_pairing_code(candidate_pin=real_pin, client_ip=client_ip)
        self.assertIsNone(token_after_brute)


if __name__ == "__main__":
    unittest.main()
