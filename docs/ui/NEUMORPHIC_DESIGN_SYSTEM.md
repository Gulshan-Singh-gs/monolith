# Neumorphic UI Design System & Architecture

**Project**: Sovereign On-Premise Agentic AI Workbench  
**Style**: Tactile, High-Contrast Neumorphism (Soft UI)  

---

## 1. Design Tokens & Surface Variables

```css
:root {
  --bg: #e4e9f2;
  --bg-card: #e4e9f2;
  --shadow-dark: #c8cfdc;
  --shadow-light: #ffffff;
  
  /* Elevation Surfaces */
  --shadow-raised: 12px 12px 24px var(--shadow-dark), -12px -12px 24px var(--shadow-light);
  --shadow-raised-sm: 6px 6px 14px var(--shadow-dark), -6px -6px 14px var(--shadow-light);
  --shadow-inset: inset 5px 5px 10px var(--shadow-dark), inset -5px -5px 10px var(--shadow-light);
  --shadow-inset-deep: inset 8px 8px 16px var(--shadow-dark), inset -8px -8px 16px var(--shadow-light);
  
  /* Radii */
  --r-pill: 999px;
  --r-card: 26px;
  --r-tile: 18px;
  --r-input: 14px;
  
  /* Accents & Status Indicators */
  --acc: #3544d6;        /* Electric Sovereign Indigo */
  --acc-hover: #2937b8;
  --emerald: #046c4e;    /* Verified / Air-Gap Green */
  --amber: #b45309;      /* Attention / Warning */
  --rose: #be123c;       /* Blocked / Danger */
  --ink: #1e2438;        /* High-contrast body text */
  --mut: #474f68;        /* Slate muted labels */
  --line: #b9c0d4;
}
```

---

## 2. Refined Components

1. **Top Navigation Bar**: Floating Neumorphic pill housing the server connection dot, air-gap boundary badge, settings launcher, and workspace root selector.
2. **Action Hero Bar**: Raised dual-tone card highlighting the autonomous multi-agent SDLC orchestrator.
3. **Workspace Modal**: Tactile dialog with inset path input for canonical folder authorization.
4. **Console & Telemetry**: Deep inset well with terminal text and color-coded status pills.
5. **Interactive Inquiry Items**: Raised Neumorphic list items that elevate on hover and trigger automated agent workflows.
