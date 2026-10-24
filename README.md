# MONOLITH

<p align="center">
  <strong>Autonomous Multi-Agent SDLC Platform & Headed Browser Engine</strong>
</p>

<p align="center">
  <a href="https://github.com/Gulshan-Singh-gs/monolith/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg?style=flat-square" alt="License"></a>
  <a href="https://github.com/Gulshan-Singh-gs/monolith/releases"><img src="https://img.shields.io/badge/release-v2.4.0-emerald.svg?style=flat-square" alt="Version"></a>
  <img src="https://img.shields.io/badge/architecture-Local--First%20%7C%20Dual--Engine-violet.svg?style=flat-square" alt="Architecture">
  <img src="https://img.shields.io/badge/browser-Playwright%20Headed-cyan.svg?style=flat-square" alt="Browser Engine">
  <img src="https://img.shields.io/badge/audit-Merkle%20Chained%20SHA--256-orange.svg?style=flat-square" alt="Merkle Ledger">
</p>

---

## What is MONOLITH?

**MONOLITH** is an autonomous, local-first engineering workbench and multi-agent SDLC orchestrator. It bridges the gap between raw LLM generation and end-to-end software delivery by pairing high-performance local AI inference with browser execution, real-time code synthesis, cryptographic provenance, and deterministic execution guards.

With zero cloud subscription lock-in, MONOLITH runs directly on your machine with full data privacy, an instantaneous hardware kill-switch, and a cryptographic audit ledger for every synthetic artifact produced.

---

## Core Capabilities

### 1. Multi-Agent SDLC Lifecycle Orchestration
Specialized autonomous agent personas collaborate in lockstep across the full delivery cycle:
- **Product Architecture & PRD Synthesis**: Generates strict engineering specifications, user stories, and acceptance criteria.
- **Full-Stack Code Synthesis**: Scaffolds runnable, production-ready modules with zero placeholders.
- **Verification & Static Analysis**: Automated syntax validation, test case execution, and AST-level checks.
- **Documentation & Deployment Runbooks**: Produces production-grade API contracts, architecture blueprints, and Docker/k8s deployment guides.

### 2. Headed Browser Automation & Portal Intelligence
- Direct Playwright engine integration with live headed viewports.
- Automated navigation, form interaction, extraction, and file acquisition.
- Instant AES-256 session vault that persists authenticated sessions without constant OTP or 2FA re-entry.

### 3. Dual-Engine LLM Router with Air-Gap Kill Switch
- **Local Sovereign Engine**: Runs quantized models (`llama3.2`, `deepseek-r1`, `mistral`) through Ollama at zero latency and zero data egress.
- **Cloud Burst Engine**: High-throughput bursts via Groq and Gemini when external speed is desired.
- **One-Click Air-Gap Kill Switch**: Instantly cuts all external network telemetry and drops execution into 100% offline local CPU/RAM mode.

### 4. Cryptographic Merkle Audit Trail
- Every prompt, model response, tool execution, and file generation is hashed with SHA-256.
- Blocks are chained in a tamper-evident audit ledger (`output/.vault/audit_trail.jsonl`).
- Real-time verification endpoint confirms blockchain-grade integrity from genesis block to head.

### 5. Local Vector RAG & Document Processor
- Ingests PDFs, technical specifications, and tabular data locally.
- In-memory vector cosine similarity ranking without heavy external database overhead.
- Dual-engine OCR pipeline pairing client-side HTML5 Canvas with server-side extraction.

---

## Architecture

```
                                  +---------------------------------------+
                                  |            MONOLITH Studio            |
                                  |       Interactive Web Interface       |
                                  +-------------------+-------------------+
                                                      |
                                                      v
                                  +---------------------------------------+
                                  |       FastAPI Application Core        |
                                  |       REST Endpoints & WebSockets     |
                                  +---------+-------------------+---------+
                                            |                   |
            +-------------------------------+                   +-------------------------------+
            v                               v                                                   v
+-----------------------+       +-----------------------+                           +-----------------------+
|   Dual-Engine Router  |       | Autonomous Web Agent  |                           |  Local Vector Engine  |
|  Ollama (Air-Gapped)  |       |  Playwright Headed    |                           |  TF-IDF & Embeddings  |
|  Groq / Gemini Burst  |       |  Session Vault AES-256|                           |  Dual-Engine OCR      |
+-----------+-----------+       +-----------+-----------+                           +-----------+-----------+
            |                               |                                                   |
            +-------------------------------+---------------------------------------------------+
                                            |
                                            v
                                +-----------------------+
                                |  Merkle Audit Ledger  |
                                |  SHA-256 Chained Log  |
                                +-----------------------+
```

---

## Quick Start

### Prerequisites
- **Python**: 3.10, 3.11, or 3.12
- **Node.js**: 18+ (for client-side toolchains and PDF exports)
- **Ollama**: (Optional, for local-first air-gapped AI)

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/Gulshan-Singh-gs/monolith.git
cd monolith

# Create and activate virtual environment
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
playwright install chromium
```

### 2. Environment Configuration

```bash
cp .env.example .env
```

Configure your `.env` (optional for local Ollama mode; configure keys only if using cloud burst):
```ini
HOST=127.0.0.1
PORT=8001
PREFERRED_ENGINE=local
LOCAL_MODEL=llama3.2:1b
OLLAMA_URL=http://127.0.0.1:11434

# Optional Cloud Burst
GROQ_API_KEY=
GEMINI_API_KEY=
```

### 3. Launch

```bash
# Windows One-Click:
Start\Launch_MONOLITH.bat

# Or manual launch:
python server.py
```

Open your browser to:
- **MONOLITH Studio**: `http://127.0.0.1:8001/`
- **Landing Page**: `http://127.0.0.1:8001/landing`
- **Interactive OpenAPI Docs**: `http://127.0.0.1:8001/docs`

---

## Repository Anatomy

```
monolith/
├── server.py                   # Core FastAPI server & WebSocket dispatch
├── dual_engine_llm.py          # Adaptive Local + Cloud Burst LLM Router
├── monolith_browser_engine.py  # Playwright browser automation runtime
├── governed_agent.py           # Risk-tiered action execution & human-in-the-loop gate
├── audit_ledger.py             # Tamper-evident SHA-256 Merkle chained ledger
├── local_rag_engine.py         # Local vector retrieval & semantic indexing
├── document_processor.py       # Dual-engine OCR and PDF chunking pipeline
├── injection_guard.py          # Prompt boundary sanitation and jailbreak defense
├── cookie_vault.py             # AES-256 encrypted session persistence
├── benchmark_engine.py         # Latency, throughput, and hardware benchmarking
├── static/                     # MONOLITH Studio single-page UI
├── landing/                    # High-fidelity dark mode marketing landing page
├── cloudflare_landing/         # Standalone zero-dependency Cloudflare Pages build
├── Start/                      # Windows launch scripts & setup wizard
└── requirements.txt            # Python dependencies
```

---

## Security & Governance

- **Zero-Egress Mode**: In local configuration, all socket calls stay bounded to `127.0.0.1`.
- **Injection Isolation**: Untrusted inputs, scraped HTML, and uploaded documents are wrapped in strict non-executable boundary tags.
- **Hardware-Enforced Safeguards**: 50 MB hard payload limit preventing heap exhaustion attacks.
- **Encrypted Secrets**: Credentials in `session_vault/` are sealed using Fernet AES-256 derived from machine-unique hardware tokens.

---

## License

Distributed under the **MIT License**. Built with precision for developers who demand complete execution sovereignty.
