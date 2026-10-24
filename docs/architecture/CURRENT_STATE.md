# Current Architecture & Runtime State
**Product**: Sovereign On-Premise Agentic AI Workbench (SIH PSC26117)
**Evaluation Date**: October 23, 2026
**Framework**: FastAPI (Python 3.14+), Uvicorn, Playwright, Fernet Crypto, HTML5/CSS3/ES6 Vanilla JS

---

## 1. Application Architecture & Entry Points

- **Primary Entry Point**: `server.py`
  - Binds to `0.0.0.0:8001` (controlled via `lan_security_manager.py`).
  - Routes serving Web UI:
    - `/` -> `static/index.html` (Workbench application UI)
    - `/deck` -> `presentation/index.html` (Executive slide deck)
    - `/landing` -> `landing/index.html` (Product landing page)
  - Real-time Transports:
    - `/ws` -> Real-time bidirectional telemetry streaming and heartbeat (`ConnectionManager`)
    - `/ws/dictation` -> Real-time binary PCM microphone audio dictation streaming
  - Middleware Pipeline (strictly ordered):
    1. `security_headers_middleware`: Enforces CSP (`default-src 'self' ...`), X-Frame-Options, and nosniff.
    2. `CORSMiddleware`: RFC1918 & loopback regex-restricted origins.
    3. `lan_network_security_guard`: Rejects public subnets; enforces pairing token validation for remote clients.
    4. `workspace_lock_guard`: Fail-closed evaluation of workspace lock state.

## 2. Component Subsystems Inventory

1. **DualEngineLLM (`dual_engine_llm.py`)**:
   - Provider Router supporting:
     - Local Sovereign Ollama (`http://127.0.0.1:11434` / `llama3.2:1b` / `llama-3.3-70b`)
     - On-premise Deterministic Fallback Synthesizer (`_generate_sovereign_local_ai`)
     - Cloud evaluation tiers (Groq Cloud API & Google Gemini API)
   - Strict Sovereignty Policy: When `target == 'local'` or `air_gap_active=True`, all external network calls are prohibited.

2. **Cookie Vault (`cookie_vault.py`)**:
   - Encrypted portal session storage using Fernet authenticated symmetric encryption.
   - Master key isolated in `session_vault/.vault_key` or `SOVEREIGN_VAULT_KEY` environment variable.
   - Zero hardcoded mock credentials in production path.

3. **Governed Agent Controller (`governed_agent.py`)**:
   - Human-in-the-Loop (HITL) gate for high-risk actions (`portal_write`, `submit_bid`, `cloud_burst`, `file_modify`).
   - Cryptographic `payload_hash` verification preventing tampering between request pause and user authorization.

4. **Prompt Injection Guard (`injection_guard.py`)**:
   - Multi-layered defense: pattern neutralizing, XML demarcated framing, programmatic tool allowlists (`PERMITTED_ACTIONS`), domain allowlists (`ALLOWED_PORTAL_DOMAINS`), and secret credential DLP filters.

5. **Local RAG & Memory Engine (`local_rag_engine.py`)**:
   - Multi-format ingestion (PDF, DOCX, CSV, TXT).
   - Integration with Graft Context Engine for token-efficient symbol analysis.

6. **Audio & Dictation Subsystem (`dictation_engine.py`)**:
   - 100% on-premise local speech transcription via Vosk / Whisper with VAD streaming.

---

## 3. Verified Execution Status

- **Automated Regression Suite**: 43 passed, 0 failed.
- **Security Baseline**: All 10 vulnerabilities (V-01 through V-10) remediated and validated under `test_security_audit_remediation.py`.
