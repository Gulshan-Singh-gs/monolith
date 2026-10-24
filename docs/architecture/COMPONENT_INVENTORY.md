# Component Inventory & Interface Registry

| Component | Primary File | Key Classes / Functions | Interface Responsibilities | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Server Engine** | `server.py` | `FastAPI app`, `ws_manager`, `workspace_lock_guard` | Routing, API contracts, WebSockets, HTTP middleware pipeline | Production-Ready (Hardened) |
| **Model Router** | `dual_engine_llm.py` | `DualEngineLLM`, `parse_markdown_to_modular_blocks` | Multi-engine LLM routing (Ollama, Groq, Gemini, Local Fallback) | Verified Local Sovereignty |
| **Session Vault** | `cookie_vault.py` | `CookieVault` | Authenticated Fernet encrypted portal credential persistence | Verified Encrypted at Rest |
| **Profile Manager** | `profile_manager.py` | `ProfileManager` | Password hashing, PBKDF2 salt, physical recovery verification | Verified Cryptographic Binding |
| **LAN Security** | `lan_security_manager.py` | `LANSecurityManager`, `PairingCodeInfo` | Subnet filtering, pairing PIN rate-limiting, session token HMAC | Verified Rate-Limited |
| **Governance Engine** | `governed_agent.py` | `GovernedAgentController`, `AgentActionRequest` | Risk classification, pause-for-approval futures, payload hash binding | Verified Tamper-Resistant |
| **Injection Defense** | `injection_guard.py` | `PromptInjectionGuard` | Pattern detection, XML boundaries, tool allowlists, DLP filter | Verified Layered Defense |
| **Local RAG Engine** | `local_rag_engine.py` | `LocalRAGEngine` | Incremental folder indexing, secret redaction, Graft AST symbol lookup | Active / Operational |
| **Audit Ledger** | `audit_ledger.py` | `AuditLedger`, `AuditEvent` | SHA-256 hash-chained immutable audit log with secret redaction | Operational |
| **Benchmark Engine** | `benchmark_engine.py` | `SovereignBenchmarkEngine` | Local LLM latency, throughput, and citation accuracy evaluator | Operational |
| **Tender Agent** | `tender_agent.py` | `TenderAgent` | Browser-based portal automation via Playwright | Operational (Simulated/Live) |
| **Document Processor**| `document_processor.py` | `DocumentProcessor` | CSV, DOCX, PDF, and Image local text extraction | Operational |
| **Dictation Engine** | `dictation_engine.py` | `DictationManager`, `LanguageRegistry` | Real-time on-premise audio transcription with VAD | Operational |
| **Frontend UI** | `static/app.js` | UI Controller | Single-page Neumorphic interface, WebSocket client, Chat controller | Hardened against XSS |
