# Security Assessment & Baseline Verification
**Repository**: Sovereign On-Premise Agentic AI Workbench
**Audit Baseline Date**: October 23, 2026
**Verification Status**: All 10 Initial Vulnerabilities Remediated & Covered by Automated Regression Tests

---

## Remediated Vulnerabilities (V-01 - V-10)

1. **V-01 — Physical Recovery Authorization** (`profile_manager.py`):
   - *Original Weakness*: Password reset occurred simply if `output/.vault/recovery.key` existed on disk without verifying caller possession.
   - *Fix*: Requires `supplied_token`, validates using `secrets.compare_digest`, and rotates the emergency token upon successful reset.
   - *Verification*: `test_security_audit_remediation.py::test_v01_physical_recovery_authorization` (PASSED).

2. **V-02 — Cookie Vault Plaintext Storage** (`cookie_vault.py`):
   - *Original Weakness*: Saved credentials to plaintext JSON and hardcoded mock session cookies.
   - *Fix*: Uses Fernet authenticated encryption (AES-128-CBC + HMAC-SHA256). Isolated key stored in `.vault_key` with strict permissions. Zero hardcoded credentials in production code.
   - *Verification*: `test_security_audit_remediation.py::test_v02_cookie_vault_authenticated_encryption` (PASSED).

3. **V-03 — Workspace Lock Fail-Open** (`server.py`):
   - *Original Weakness*: `except Exception: pass` bypassed lock when storage was unreadable.
   - *Fix*: Returns HTTP 503 (`Security state unavailable. Workspace access temporarily restricted (fail-closed)`).
   - *Verification*: `test_security_audit_remediation.py::test_v03_workspace_lock_fails_closed` (PASSED).

4. **V-04 — Cloud Fallback Data Sovereignty** (`dual_engine_llm.py`):
   - *Original Weakness*: Silent fallback from Ollama to Groq/Gemini when Ollama failed.
   - *Fix*: Cloud fallback strictly forbidden when `target == 'local'` or `air_gap_active=True`. Routes solely to on-premise fallback engine.
   - *Verification*: `test_security_audit_remediation.py::test_v04_local_inference_sovereignty_killswitch` (PASSED).

5. **V-05 — WebSocket Lock Enforcement** (`server.py`):
   - *Original Weakness*: WebSockets `/ws` and `/ws/dictation` bypassed HTTP workspace-lock middleware.
   - *Fix*: Handshake checks workspace lock state; closes unauthorized/locked sockets with code 4423.
   - *Verification*: `test_security_audit_remediation.py::test_v05_websocket_locked_workspace_rejection` (PASSED).

6. **V-06 — Streaming Upload Limit** (`server.py`):
   - *Original Weakness*: File read completely into RAM before checking `MAX_UPLOAD_BYTES`.
   - *Fix*: Chunked streaming reads (1MB chunks) with cumulative byte counter; immediate 413 abort. Unique filenames prevent overwrite attacks.
   - *Verification*: `test_security_audit_remediation.py::test_v06_streaming_upload_size_limit` (PASSED).

7. **V-07 — Multi-Layered Injection & Tool Policy** (`injection_guard.py`):
   - *Original Weakness*: Purely regex-based prompt filtering.
   - *Fix*: Programmatic tool execution allowlist (`PERMITTED_ACTIONS`), authorized domain checks (`ALLOWED_PORTAL_DOMAINS`), and credential DLP filter.
   - *Verification*: `test_security_audit_remediation.py::test_v07_injection_guard_tool_and_dlp_boundaries` (PASSED).

8. **V-08 — Human Approval Action Binding** (`governed_agent.py`):
   - *Original Weakness*: Caller could supply arbitrary `officer_name` without action payload binding.
   - *Fix*: Binds approval to `payload_hash` (SHA-256) verifying action payload immutability between request and approval.
   - *Verification*: `test_security_audit_remediation.py::test_v08_approval_immutable_action_binding` (PASSED).

9. **V-09 — Unlocked Path Boundary Tightening** (`server.py`):
   - *Original Weakness*: Unlocked route list included WebSockets and session management endpoints.
   - *Fix*: Pruned non-bootstrap endpoints from `_UNLOCKED_PATHS`.
   - *Verification*: `test_security_audit_remediation.py::test_v09_unlocked_boundaries_tightened` (PASSED).

10. **V-10 — Pairing PIN Rate Limiting & Lockout** (`lan_security_manager.py`):
    - *Original Weakness*: 6-digit numeric PIN lacked attempt rate limiting.
    - *Fix*: Enforced per-IP sliding-window rate limit (max 5 per 5 min) and destroyed PIN after 3 failed guesses.
    - *Verification*: `test_security_audit_remediation.py::test_v10_pairing_pin_rate_limiting` (PASSED).
