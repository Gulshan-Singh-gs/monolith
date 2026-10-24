# Enhancement Skills & Repositories Evaluation

**Assessment Date**: October 24, 2026  
**Project**: Sovereign On-Premise Agentic AI Workbench  
**Environment**: Google Antigravity (Windows x64, Node.js, Python 3.14)  

---

## 1. Candidate Evaluation Matrix

| Candidate | Repository | Focus Area | Antigravity / Windows Compatibility | License | Recommendation & Decision |
|---|---|---|---|---|---|
| **Candidate A: Archify** | [`tt-a1i/archify`](https://github.com/tt-a1i/archify) | Architecture & Sequence Diagrams | **High**: Generates self-contained standalone HTML/SVG/PNG diagrams | MIT / CC | **ADOPT (Primary Architecture Tool)**: Generates verifiable, interactive system anatomy & sequence diagrams directly grounded in actual source files. |
| **Candidate B: UI Skill** | [`lcanady/ui-skill`](https://github.com/lcanady/ui-skill) | Design System & Token Guardrails | **High**: Token patterns and CSS property contracts | MIT | **REFERENCE (Design System Foundation)**: Used to enforce tactile Neumorphic design tokens, elevation levels, and WCAG AA contrast standards without introducing unnecessary frontend framework weight. |
| **Candidate C: Remotion Agent Skills** | [`remotion-dev/skills`](https://github.com/remotion-dev/skills) | Programmatic Video Generation | **Medium**: Requires full React/Remotion toolchain | Apache 2.0 | **REFERENCE (Motion Guidance)**: Avoid migrating to Remotion as requested by user prompt. Retain installed `brag` + `Hyperframes` as the primary video pipeline. |
| **Candidate D: Video Shotcraft** | [`syklayou-glitch/video-shotcraft`](https://github.com/syklayou-glitch/video-shotcraft) | Cinematic Camera & Motion Recipes | **Medium**: Built specifically for Remotion | MIT | **REFERENCE (Choreography & Pacing)**: Adopted camera choreography and kinetic timing principles for Hyperframes scene orchestration. |
| **Candidate E: Playwright** | [`microsoft/playwright`](https://github.com/microsoft/playwright) | Browser Automation & Video Capture | **High**: Native Python & Node support on Windows | Apache 2.0 | **ADOPT (Active Runtime)**: Already integrated in `tender_agent.py` and workbench automation for live browser capture. |

---

## 2. Detailed Technical Findings

### Candidate A: Archify (`tt-a1i/archify`)
- **Actual Functionality**: Takes codebase structure, symbols, and runtime routes, generating interactive, standalone, self-contained HTML architecture and sequence diagrams with zero external runtime dependencies.
- **Measurable Benefit**: Directly solves the requirement for Part 4 ("Build the Project Anatomy") by creating verified System Anatomy maps, Model Routing sequences, Data-Flow diagrams, and Request Lifecycles that link to real files (`core/workspace/engine.py`, `core/gateway/router.py`, `server.py`).
- **Security & Dependency Risk**: Negligible (output is pure client-side HTML/SVG; no daemon or remote telemetry).
- **Decision**: **ADOPT & INTEGRATE**. Used to produce the interactive architectural diagrams in `docs/architecture/`.

### Candidate B: UI Skill (`lcanady/ui-skill`)
- **Actual Functionality**: Standardizes design tokens, surface hierarchies, and motion patterns.
- **Measurable Benefit**: Informs the tactile Neumorphic design token implementation (`--shadow-raised`, `--shadow-inset`, `--bg: #e4e9f2`, `--acc: #3544d6`, `--emerald: #046c4e`), ensuring high contrast and accessibility without UI framework bloat.
- **Decision**: **ADOPT AS DESIGN TOKEN REFERENCE**. Preserved existing Vanilla CSS architecture while enforcing cohesive token variables across the workbench.

### Candidate C: Remotion Agent Skills (`remotion-dev/skills`)
- **Actual Functionality**: Provides AI guidance for writing Remotion React video compositions.
- **Overlap & Risk**: Overlaps with the already installed `brag` skill and `Hyperframes` engine. Replacing Hyperframes with Remotion would violate the non-negotiable preservation requirement ("Do not replace the brag skill with Remotion merely because the repository is available").
- **Decision**: **REJECT AS PRIMARY PIPELINE / RETAIN FOR MOTION LOGIC REFERENCE**.

### Candidate D: Video Shotcraft (`syklayou-glitch/video-shotcraft`)
- **Actual Functionality**: Provides recipe cards for motion graphics and camera transitions.
- **Overlap & Risk**: Remotion-tied dependencies.
- **Decision**: **REFERENCE ONLY**. Used kinetic choreography and typography pacing rules within Hyperframes GSAP timelines.

### Candidate E: Microsoft Playwright (`microsoft/playwright`)
- **Actual Functionality**: Headless and headful browser automation with native screen recording.
- **Decision**: **ACTIVE RUNTIME**. Integrated for live application verification and capturing real workbench footage.
