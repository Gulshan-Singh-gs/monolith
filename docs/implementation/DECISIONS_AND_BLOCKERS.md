# Architectural Decisions & Blockers Log (ADR)
## MONOLITH — Autonomous Engineering System

**Last Updated**: October 24, 2026  
**Document Status**: All Identified Blockers Remediated & Verified  

---

### Architectural Decisions (ADRs)

#### ADR-001: Strict Enumeration Parsing with Rejection Over Silent Fallback
* **Context**: `core/api/routes.py` parsed incoming `req.role` by converting it to lowercase and passing it to `AgentRole`, which caused valid uppercase enum values (`CODING_AGENT`, `TESTING_AGENT`) to raise `ValueError`. The exception handler silently caught the error and assigned `AgentRole.ORCHESTRATOR`.
* **Decision**: All API models validate enum inputs case-insensitively using normalized string lookup (`AgentRole.from_string()`). If an invalid role is provided, the API fails fast and rejects the request with HTTP 400 Bad Request and an explicit list of permissible roles. Silent conversion to `ORCHESTRATOR` is abolished.
* **Status**: **IMPLEMENTED & VERIFIED** (`tests/test_agent_roles.py`).

#### ADR-002: Durable Task Lifecycle & Deterministic Approval Gating
* **Context**: `core/orchestrator/orchestrator.py` retained tasks in a volatile in-memory dictionary and passed a hardcoded `timeout_seconds=0.1` to the approval gate. Approvals in `governed_agent.py` accepted unverified `officer_name` strings without session validation.
* **Decision**:
  1. Implement persistent task storage in `.vault/orchestrator_tasks.json` and `.vault/pending_approvals.json` with atomic updates.
  2. Implement comprehensive lifecycle states: `CREATED`, `VALIDATING`, `PLANNING`, `READY`, `RUNNING`, `VERIFYING`, `AWAITING_APPROVAL`, `PAUSED`, `COMPLETED`, `FAILED`, `CANCELLED`.
  3. Bind approvals immutably to task ID, action ID, action payload hash (SHA-256), risk level, and policy version.
  4. Authenticate approval decisions against active session cookies, LAN authentication, and operator profile.
  5. Configurable and bounded timeouts with explicit timeout records; duplicate approval submissions are idempotent.
* **Status**: **IMPLEMENTED & VERIFIED** (`tests/test_approval_lifecycle.py`).

#### ADR-003: Governed Execution Broker Replacing Shell Blacklist
* **Context**: `core/workspace/engine.py` executed commands using `asyncio.create_subprocess_shell` with a simple blacklist regex (`rm -rf`, `del /s`, `format`, `shutdown`, `curl | bash`). Blacklists are fundamentally bypassable (e.g., encoded strings, variable substitutions, relative paths, PowerShell cmdlets).
* **Decision**: Replace shell execution with `GovernedExecutionBroker`. Allowlisted development tools (`git`, `python`, `pytest`, `npm`, `node`) execute via `asyncio.create_subprocess_exec` with explicit argument arrays, preventing shell interpolation. Arbitrary shell access is classified as `HIGH` risk requiring explicit human approval. Enforce process tree termination (`taskkill /F /T` on Windows), working directory confinement, environment sanitization (stripping API keys and session tokens), and output buffer bounding (1MB max).
* **Status**: **IMPLEMENTED & VERIFIED** (`tests/test_execution_broker.py`).

#### ADR-004: Decoupled Multi-Provider Gateway & Explicit Local Mocking
* **Context**: `dual_engine_llm.py` coupled Groq and xAI Grok, and tests hung attempting to connect to external endpoints or an unstarted local Ollama daemon.
* **Decision**:
  1. Separate provider adapters for Ollama, OpenRouter, Google Gemini, Groq, and xAI Grok under `core/gateway/providers/`.
  2. Implement an offline, deterministic mock provider for unit tests and local evaluation.
  3. Enforce `LOCAL_ONLY` privacy mode at the gateway root: zero outbound network connections are attempted when local mode or kill-switch is active. Fast 1.5s probe failover prevents uninstalled models or offline daemons from hanging callers.
  4. Any local model unavailability produces an explicit failure or deterministic on-premise fallback, never a silent cloud burst.
* **Status**: **IMPLEMENTED & VERIFIED** (`tests/test_model_registry_and_providers.py`).

#### ADR-005: Clean Tracking of Tests in Version Control & CI Matrix
* **Context**: `.gitignore` contained `tests/` and `test_*.py`, preventing regression tests from being committed to the repository.
* **Decision**: Modify `.gitignore` to track `tests/` and all test modules. Ignore only runtime test caches (`.pytest_cache/`, `test-results/`, `htmlcov/`, `.coverage`). Establish `.github/workflows/ci.yml` matrix testing across Ubuntu and Windows.
* **Status**: **IMPLEMENTED & VERIFIED** (`.gitignore`, `.github/workflows/ci.yml`).

#### ADR-006: Unified Patch Engine & Checkpointed Rollback
* **Context**: Direct file write APIs overwrote existing workspace files without diff review or rollback capabilities.
* **Decision**: Implement `WorkspacePatchEngine` providing unified diff generation, diff parsing, path confinement validation, risk assessment (`LOW`/`MEDIUM`/`HIGH`/`CRITICAL`), atomic patch application, and automatic snapshotting in `.vault/checkpoints/` with one-click rollback.
* **Status**: **IMPLEMENTED & VERIFIED** (`tests/test_patch_and_git.py`).

#### ADR-007: Automated Quality Gates & Deployment Delivery Engine
* **Context**: The orchestrator treated LLM responses as proof that software development was complete without running tests or verifying outputs.
* **Decision**: Implement `QualityGateEngine` and `DeliveryEngine`. Discover project profiles (Python, Node, Rust, Go), scan for hardcoded secrets, execute linters and test suites, capture bounded diagnostic output, and gate Cloudflare Pages and GitHub Pages deployments behind authorized approvals.
* **Status**: **IMPLEMENTED & VERIFIED** (`tests/test_delivery_and_quality_gates.py`).

---

### Remediated Blockers Log

| Blocker ID | Description | Severity | Status | Verification Evidence |
|---|---|:---:|:---:|---|
| **BLK-001** | `core/api/routes.py` never mounted in `server.py` | CRITICAL | **RESOLVED** | Mounted `app.include_router(core_router)`. Verified via `test_fastapi_workspace_and_core_endpoints`. |
| **BLK-002** | `test_*.py` and `tests/` ignored by `.gitignore` | CRITICAL | **RESOLVED** | Removed ignores in `.gitignore`. 8 test files now tracked. |
| **BLK-003** | Silent role conversion to `ORCHESTRATOR` | HIGH | **RESOLVED** | Implemented `AgentRole.from_string()` and HTTP 400 validation. Verified via `test_agent_roles.py`. |
| **BLK-004** | 0.1s hardcoded approval timeout & unauthenticated approvals | HIGH | **RESOLVED** | Implemented durable 7-stage lifecycle, session auth, hash binding in `core/orchestrator/orchestrator.py` and `governed_agent.py`. Verified via `test_approval_lifecycle.py`. |
| **BLK-005** | Shell blacklist security vulnerability | HIGH | **RESOLVED** | Implemented `GovernedExecutionBroker` in `core/execution/broker.py`. Verified via `test_execution_broker.py`. |
| **BLK-006** | Ollama connection delays during offline unit tests | MEDIUM | **RESOLVED** | Implemented 1.5s fast probe timeout and local fallback synthesis. Verified via `test_model_registry_and_providers.py`. |
| **BLK-007** | Frontend disconnected from `core/` APIs | MEDIUM | **RESOLVED** | Implemented `static/monolith_studio.js` and wired UI modals in `static/index.html`. |
| **BLK-008** | In-memory singleton test crosstalk in approval lifecycle | MEDIUM | **RESOLVED** | Isolated `governed_agent.storage_dir` in pytest fixture and matched approvals by `task_id`. Verified via `test_approval_lifecycle.py` (8/8 passed). |
