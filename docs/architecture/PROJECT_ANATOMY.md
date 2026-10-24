# Technical Anatomy: Sovereign On-Premise Agentic AI Workbench

**Classification**: Production-Verified Architecture  
**Execution Environment**: Local-First, Privacy-Governed, Air-Gapped Workstation  
**Authoritative Implementation Roots**:
- Frontend: `static/index.html`, `static/app.js`, `static/styles.css`
- Server & Transport: `server.py`, `core/api/routes.py`
- Local Orchestrator: `core/orchestrator/orchestrator.py`
- Model Gateway & Privacy Engine: `core/gateway/router.py`, `dual_engine_llm.py`
- Workspace Engine: `core/workspace/engine.py`
- Skill Registry & SDLC Generator: `core/skills/registry.py`, `core/sdlc/generator.py`
- Security & HITL Governance: `governed_agent.py`, `lan_security_manager.py`, `cookie_vault.py`

---

## Layer 1: System Overview & Component Hierarchy

```
+-----------------------------------------------------------------------------------+
|               Sovereign Neumorphic User Interface (Vanilla HTML/CSS/JS)           |
|  - Workspace Selector    - SDLC Hero Orchestrator    - Real-Time Activity Console |
|  - Interactive Inquiries - Document Hub              - Content Security Policy    |
+-----------------------------------------+-----------------------------------------+
                                          | REST / WebSockets (Port 8001)
                                          v
+-----------------------------------------------------------------------------------+
|                        FastAPI Gateway & Security Layer                           |
|  - lan_network_security_guard (IP & session token validation)                     |
|  - workspace_lock_guard (Fail-closed ProfileManager check)                        |
|  - CSP Middleware & Safe Origin Filters                                           |
+--------------------+--------------------+--------------------+--------------------+
                     |                    |                    |
                     v                    v                    v
+--------------------+----+ +-------------+------+ +-----------+-------------------+
| SecureWorkspaceEngine   | | SovereignModelGate | | SkillRegistry & SDLC Gen    |
| [core/workspace/engine] | | [core/gateway]     | | [core/skills/ & core/sdlc/] |
| - Canonical Path Bounds | | - LOCAL_ONLY       | | - PRD Generator             |
| - Symlink Defense       | | - HYBRID Routing   | | - Architecture & ADR        |
| - Atomic Writes (.tmp)  | | - Ollama Daemon    | | - Threat Modeling (STRIDE)  |
| - Dangerous CMD Filters | | - Zero Egress Gate | | - QA Test Strategy          |
+--------------------+----+ +-------------+------+ +-----------+-------------------+
                     ^                    ^                    ^
                     |                    |                    |
+--------------------+--------------------+--------------------+--------------------+
|                         Local Orchestrator Agent                                  |
|                      [core/orchestrator/orchestrator.py]                          |
|  - Task Contracts: AgentRole, TaskState (CREATED -> RUNNING -> COMPLETED)        |
|  - Human-in-the-Loop Approval Gating: governed_agent.evaluate_and_gate             |
|  - SHA-256 Payload Binding & Tamper Detection                                     |
+-----------------------------------------------------------------------------------+
```

---

## Layer 2: Runtime Request Flow (End-to-End)

1. **User Action**: User clicks *"Generate Full SDLC Requirements & Architecture"* or enters a natural-language prompt.
2. **Frontend Dispatch**: `static/app.js` posts to `/api/sdlc/generate` or `/api/orchestrator/tasks`.
3. **Network & Lock Security Check**:
   - `lan_network_security_guard` verifies client IP is local host (`127.0.0.1`) or an authenticated LAN device.
   - `workspace_lock_guard` checks `.vault/profile.json`. If locked or state unavailable, fails closed (HTTP 423 / 503).
4. **Local Orchestrator Invocation**:
   - Creates `AgentTaskContract` with ID `TSK-XXXX`.
   - If `requires_approval=True`, transitions to `AWAITING_APPROVAL`, binds the request to SHA-256 hash `payload_hash`, and waits for authorized officer decision.
5. **Model Gateway Inference**:
   - Evaluates `PrivacyMode`. If `LOCAL_ONLY`, forces `is_airgap=True`, routing prompt directly to Ollama daemon (`http://127.0.0.1:11434`) or on-premise synthesizer.
   - Remote cloud fallback is rejected at the gateway boundary.
6. **Workspace Write**:
   - `SecureWorkspaceEngine.write_file` resolves canonical path against authorized root (`C:\Users\Code66\Music\Sovereign_AI_Workbench_Clean`).
   - Ensures no directory traversal escapes (`../`).
   - Writes atomically via `.tmp_write` before replacing target file (`docs/product/PRD.md`).
7. **Telemetry & Audit**:
   - `audit_ledger.record_event` commits an immutable record with timestamp and cryptographic hash.
   - Telemetry emitted to `/ws` updates progress bar and live console in `static/index.html`.

---

## Layer 3: Model Gateway & Sovereignty Routing Policies

| Privacy Mode | Permitted Providers | Fallback Rule | Network Behavior |
|---|---|---|---|
| **`LOCAL_ONLY`** (Default) | Ollama Local Models, On-Premise Synthesizer | Strict Fail-Closed. Never falls back to cloud. | Zero outbound network egress. 100% on-premise execution. |
| **`HYBRID`** | Local Primary; Authorized Google Gemini / OpenRouter | Local first; falls back to cloud only for non-confidential tasks. | Secrets and private profile files redacted. |
| **`CONNECTED`** | Multi-Provider with Credential Isolation | Evaluates provider quotas and latency. | Requires explicit human approval for code publishing. |

---

## Layer 4: Trust Boundaries & Cryptographic Defenses

1. **Localhost Isolation**: The workbench treats `localhost` as a multi-origin environment. Malicious browser tabs cannot invoke APIs without passing origin checks and workspace lock verification.
2. **Path Traversal Defense**: `SecureWorkspaceEngine._resolve_safe_path` resolves candidates canonicalizing all symlinks and checking `candidate.relative_to(root_path)`.
3. **Dangerous Command Policy**: `rm -rf`, `format`, `del /s C:`, and piped shell executions are blocked pre-execution with exit code `-1`.
4. **Physical Token Recovery**: Emergency account recovery uses `secrets.compare_digest` against cryptographically randomized entropy keys, automatically rotating the token upon single use.
5. **Session Vault Encryption**: Browser sessions and API tokens are encrypted at rest using authenticated symmetric Fernet keys (`portal_sessions.enc`).
