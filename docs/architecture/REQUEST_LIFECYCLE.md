# Request Lifecycle & Security Verification Flow

**Workbench**: Sovereign On-Premise Agentic AI Workbench  
**Lifecycle Stages**: Ingestion, Authentication, Gating, Routing, Execution, Verification, and Audit  

---

## 1. Lifecycle State Machine

```
[ CREATED ] 
     │
     ▼
[ VALIDATING ] ──► (Verify Client IP & Workspace Lock State)
     │
     ▼
[ PLANNING ] ──► (Decompose user goal into subtasks)
     │
     ▼
[ READY ] ──► (Check Tool Authorization & Security Clearances)
     │
     ▼
[ RUNNING ] ──► (Execute with Model Gateway or Controlled CLI)
     │
     ▼
[ VERIFYING ] ──► (Grounded Evidence & Path Traversal Verification)
     │
     ├──► Requires HITL? ──► [ AWAITING_APPROVAL ] ──► (Officer Decision)
     │                                                     │
     ▼                                                     ▼
[ COMPLETED ] ◄────────────────────────────────────────────┘
     │
     └──► If Error: [ FAILED ] (With Actionable Diagnostic Log)
```

---

## 2. Protected Execution Contracts

| Component | Responsibility | Bound Method / Function | Security Guarantee |
|---|---|---|---|
| **Lock Guard** | Fail-Closed Profile Guard | `server.workspace_lock_guard` | Rejects access with HTTP 503 if profile state is unreadable. |
| **Path Defense** | Canonical Resolution | `SecureWorkspaceEngine._resolve_safe_path` | Rejects any path outside `root_path` via `ValueError` -> `PermissionError`. |
| **Air-Gap Policy** | Zero Cloud Inference | `SovereignModelGateway.generate` | Enforces `is_airgap=True` in `LOCAL_ONLY` mode. |
| **HITL Gate** | Consequential Action Guard | `governed_agent.evaluate_and_gate` | High-risk actions require SHA-256 payload authorization by an officer. |
