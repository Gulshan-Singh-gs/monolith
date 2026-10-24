# Component Interactions: Sovereign On-Premise Agentic AI Workbench

**Scope**: Production-verified inter-module communication patterns and event contracts.

---

## 1. Interaction Diagram: Orchestrator to Workspace & Model Gateway

```mermaid
sequenceDiagram
    autonumber
    actor User as User / Developer
    participant UI as Neumorphic UI (static/app.js)
    participant API as FastAPI Router (core/api/routes.py)
    participant SEC as Security Guards (lan & lock)
    participant ORCH as Local Orchestrator (core/orchestrator/)
    participant GATE as Model Gateway (core/gateway/router.py)
    participant OLLAMA as Local Ollama Daemon
    participant WS as Secure Workspace Engine (core/workspace/)
    participant AUDIT as Audit Ledger (audit_ledger.py)

    User->>UI: Select Task / Input Prompt
    UI->>API: POST /api/orchestrator/tasks or /api/sdlc/generate
    API->>SEC: Validate Client IP & Workspace Lock
    alt Locked or Unauthorized
        SEC-->>UI: 423 Locked / 401 Unauthorized
    else Authorized
        SEC->>ORCH: Create & Schedule Task (AgentTaskContract)
        ORCH->>GATE: Request Inference (InferenceRequest, PrivacyMode=LOCAL_ONLY)
        GATE->>OLLAMA: POST http://127.0.0.1:11434/api/generate
        OLLAMA-->>GATE: Return Quantized Model Output
        GATE-->>ORCH: InferenceResponse (is_local=True, tokens, latency)
        ORCH->>WS: write_file(rel_path, content)
        WS->>WS: Canonicalize Path & Check Traversal Boundaries
        WS->>WS: Atomic Write via .tmp_write
        WS-->>ORCH: Confirm Write
        ORCH->>AUDIT: Commit Event (SHA-256 hash, timestamp, actor)
        ORCH-->>API: Task Completed Contract
        API-->>UI: Return Result JSON
        UI->>User: Display Artifacts & Telemetry
    end
```

---

## 2. HITL Governance & Cryptographic Approval Gate

```mermaid
sequenceDiagram
    autonumber
    participant Agent as Coding / Deployment Agent
    participant Gate as Governed Agent Gate (governed_agent.py)
    participant Officer as Authorized Officer
    participant Execution as Controlled Execution Layer

    Agent->>Gate: evaluate_and_gate(action_type="deploy", payload)
    Gate->>Gate: Compute SHA-256 payload_hash
    Gate->>Gate: Classify Risk: HIGH
    Gate-->>Officer: Trigger Approval Request (AWAITING_APPROVAL)
    alt Officer Rejects / Times Out
        Gate-->>Agent: Action Denied (is_allowed=False, Safe Fallback)
    else Officer Signs Off
        Officer->>Gate: submit_decision(decision="APPROVED", payload_hash)
        Gate->>Gate: Validate Hash Integrity & Officer Credentials
        Gate->>Execution: Execute Authorized Action
        Execution-->>Agent: Action Completed Successfully
    end
```
