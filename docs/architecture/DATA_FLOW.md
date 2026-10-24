# Data Flow & Boundary Isolation Architecture

**System**: Sovereign On-Premise Agentic AI Workbench  
**Focus**: Privacy Boundary Enforcement, RAG Vector Indexing, and Atomic Disk I/O  

---

## 1. Zero-Cloud Data Flow (`LOCAL_ONLY` Mode)

```
[ User Input / Project Files ]
               │
               ▼
[ Secure Workspace Boundary ] ──(Path Traversal Check: candidate.relative_to(root))
               │
               ▼
[ Local RAG Engine / Tokenizer ] ──(In-Memory Chunking & Local Embeddings)
               │
               ▼
[ Sovereign Model Gateway ]
               │
      Is Air-Gap Active? (LOCAL_ONLY)
         ├── YES: ──► [ Local Ollama Engine (127.0.0.1:11434) ]
         │                     │
         │                     ▼
         │            [ Quantized Inference Output ]
         │
         └── NO (Rejected): Cloud Providers (Gemini / OpenRouter) Blocked
               │
               ▼
[ Atomic Disk Persistence ] ──(Write to .tmp_write -> Atomic File Replace)
               │
               ▼
[ Cryptographic Audit Ledger ] ──(SHA-256 Chained Hash Verification)
```

---

## 2. Ingestion & RAG Memory Pipeline

1. **Document Loading**: Supports `.py`, `.js`, `.md`, `.txt`, `.json`, `.pdf`, `.docx`.
2. **Path Sanitization**: Files are verified against authorized root boundaries.
3. **Chunking & Indexing**: Split into sliding token windows with source path metadata.
4. **Vector Retrieval**: Local cosine similarity matches relevant context.
5. **Prompt Synthesis**: Minimal, redacted context is passed to the local LLM to minimize token consumption and avoid context saturation.
