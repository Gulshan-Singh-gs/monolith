# Master Migration Plan: Sovereign Software Engineering Workbench
**Target**: Transform existing Sovereign AI Workbench into a production-grade local-first multi-agent software engineering platform.

---

## Migration Roadmap & Phases

### Phase 0: Baseline & Reconnaissance (COMPLETED)
- Verified repository inventory, test suites, and startup pipeline.
- Established characterization baseline (43 passing tests across security, LAN, governance, dictation, and document processing).
- Rebuilt Graft Context Engine graph (548 symbols, 1318 edges).

### Phase 1: Critical Security Hardening (COMPLETED)
- Eradicated all 10 verified vulnerabilities (V-01 to V-10).
- Encrypted CookieVault at rest via Fernet.
- Hardened WebSockets, uploads, injection defenses, and pairing PIN verification.
- Enforced CSP and sanitized frontend XSS surfaces.

### Phase 2: Core Abstraction & Stable Internal Interfaces (IN PROGRESS)
- **Model Gateway Interface (`interfaces/model_gateway.py`)**: Provider-agnostic interface supporting Ollama, OpenRouter, Gemini, Grok, and local fallback with strict privacy boundary validation.
- **Workspace Engine Interface (`interfaces/workspace.py`)**: Canonical path traversal defense, file ownership, diff tracking, and controlled terminal process execution.
- **Agent Runtime & Task Contracts (`interfaces/agent.py`)**: Typed task schemas, state machine (`CREATED` -> `PLANNING` -> `RUNNING` -> `AWAITING_APPROVAL` -> `COMPLETED`), and role-based tool permissions.

### Phase 3: Workspace Engine Implementation
- Multi-file explorer, patch applicator, git branch/diff inspection, and secure workspace sandboxing.
- Controlled command executor with working-directory confinement and process timeouts.

### Phase 4: Model Gateway & Multi-Provider Adapters
- Plug-in adapters for Ollama, OpenRouter, Google Gemini, and Grok.
- Privacy mode enforcement (`LOCAL_ONLY`, `HYBRID`, `CONNECTED`).

### Phase 5: Multi-Agent Software Development Lifecycle (SDLC) Runtime
- Orchestrator, Planning Agent, Coding Agent, Reviewer Agent, and Testing Agent coordination.
- SDLC artifact generation (`docs/product/`, `docs/architecture/`, `docs/decisions/`).

### Phase 6: Skill System & Project Memory
- Versioned skill registry (`skills/`) with input/output validation.
- Graft-backed incremental RAG and symbol lookup.

### Phase 7: Governed Playwright Browser Integration
- Isolated browser sessions with visible challenge handling (CAPTCHA/MFA pauses).

### Phase 8: Testing & Quality Assurance Engine
- Automated test discovery, execution, diff reviews, and regression verification.

### Phase 9: Deployment Integrations (Cloudflare & GitHub)
- Least-privilege GitHub commits and Cloudflare Pages/Workers preview deployments with verified live URLs.

### Phase 10: Production Hardening & Release Verification
- End-to-end verification and release checklist.
