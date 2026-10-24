/**
 * MONOLITH — Autonomous Engineering System
 * Interactive Landing Page Controller
 *
 * Powers interactive simulators:
 * 1. Multi-Agent SDLC Pipeline Generator
 * 2. Playwright Browser Automation & Pinterest Media Ingestion
 * 3. Sovereign Air-Gap Boundary & Kill Switch
 * 4. Cryptographic SHA-256 Merkle Ledger
 * 5. Developer Velocity & ROI Calculator
 * 6. FAQ Accordion & Smooth Navigation
 */

document.addEventListener('DOMContentLoaded', () => {
  initTheme();
  initHeroSineWave();
  initMonolithLiquidTypography();
  initAirgapSimulator();
  initLedgerSimulator();
  initSdlcSimulator();
  initBrowserAutomationSimulator();
  initVelocityCalculator();
  initTerminalTabs();
  initFaqAccordion();
  initSmoothScroll();
  initMobileNavigation();
  initScrollSpy();
});

/* ====================================================================
   1. THEME TOGGLE (Dark / Light Sovereign Modes)
   ==================================================================== */
function initTheme() {
  const toggleBtn = document.getElementById('themeToggleBtn');
  if (!toggleBtn) return;

  const savedTheme = localStorage.getItem('monolith_theme') || 'dark';
  document.documentElement.setAttribute('data-theme', savedTheme);
  updateThemeIcon(savedTheme);

  toggleBtn.addEventListener('click', () => {
    const currentTheme = document.documentElement.getAttribute('data-theme') || 'dark';
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('monolith_theme', newTheme);
    updateThemeIcon(newTheme);
    showToast(`Switched to ${newTheme.toUpperCase()} theme`);
  });
}

function updateThemeIcon(theme) {
  const icon = document.getElementById('themeIcon');
  if (!icon) return;
  if (theme === 'light') {
    icon.innerHTML = `<path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path>`;
  } else {
    icon.innerHTML = `
      <circle cx="12" cy="12" r="5"></circle>
      <line x1="12" y1="1" x2="12" y2="3"></line>
      <line x1="12" y1="21" x2="12" y2="23"></line>
      <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line>
      <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line>
      <line x1="1" y1="12" x2="3" y2="12"></line>
      <line x1="21" y1="12" x2="23" y2="12"></line>
      <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line>
      <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line>
    `;
  }
}

/* ====================================================================
   2. SOVEREIGN AIR-GAP & PHYSICAL KILL SWITCH SIMULATOR
   ==================================================================== */
function initAirgapSimulator() {
  const switchInput = document.getElementById('airgapToggle');
  const statusBadge = document.getElementById('airgapStatusBadge');
  const routeDisplay = document.getElementById('activeRouteDisplay');
  const latencyDisplay = document.getElementById('telemetryLatency');
  const costDisplay = document.getElementById('telemetryCost');
  const leakDisplay = document.getElementById('telemetryLeak');
  const emergencyKillBtn = document.getElementById('emergencyKillBtn');

  if (!switchInput) return;

  function setAirgapState(isAirgapped) {
    if (isAirgapped) {
      switchInput.checked = false;
      statusBadge.textContent = 'AIR-GAP BOUNDARY ENFORCED';
      statusBadge.style.background = 'rgba(16, 185, 129, 0.2)';
      statusBadge.style.color = 'var(--accent-emerald-light)';
      statusBadge.style.borderColor = 'var(--accent-emerald)';

      routeDisplay.textContent = 'Ollama Local Daemon (llama3.2:1b on Local GPU)';
      routeDisplay.style.color = 'var(--accent-emerald-light)';

      latencyDisplay.textContent = '14 ms (Zero Round-Trip)';
      costDisplay.textContent = '$0.00 / token (Free)';
      leakDisplay.textContent = '0.000 Bytes (100% On-Premise)';
      leakDisplay.style.color = 'var(--accent-emerald-light)';
    } else {
      switchInput.checked = true;
      statusBadge.textContent = 'EGRESS PERMITTED (AUTHORIZED)';
      statusBadge.style.background = 'rgba(99, 102, 241, 0.2)';
      statusBadge.style.color = 'var(--accent-primary-light)';
      statusBadge.style.borderColor = 'var(--accent-primary)';

      routeDisplay.textContent = 'Dual-Engine Cloud Router (Authenticated Tunnel)';
      routeDisplay.style.color = 'var(--accent-primary-light)';

      latencyDisplay.textContent = '420 ms (Cloud Round-Trip)';
      costDisplay.textContent = '$0.003 / 1k tokens';
      leakDisplay.textContent = 'Encrypted Egress to Authorized Provider';
      leakDisplay.style.color = 'var(--accent-saffron-light)';
    }
  }

  switchInput.addEventListener('change', () => {
    setAirgapState(!switchInput.checked);
    if (!switchInput.checked) {
      showToast('Boundary Enforced: 100% Air-Gapped Local Model');
    } else {
      showToast('Egress Permitted for Browser Automation / Cloud LLM');
    }
  });

  if (emergencyKillBtn) {
    emergencyKillBtn.addEventListener('click', () => {
      setAirgapState(true);
      showToast('AIR-GAP KILL SWITCH TRIPPED: All external egress severed!');
    });
  }
}

/* ====================================================================
   3. CRYPTOGRAPHIC MERKLE LEDGER SIMULATOR
   ==================================================================== */
function initLedgerSimulator() {
  const verifyBtn = document.getElementById('verifyLedgerBtn');
  const tamperBtn = document.getElementById('tamperLedgerBtn');
  const resetBtn = document.getElementById('resetLedgerBtn');
  const ledgerStatus = document.getElementById('ledgerStatusBadge');
  const blocks = document.querySelectorAll('.ledger-block');

  if (!verifyBtn) return;

  verifyBtn.addEventListener('click', () => {
    verifyBtn.disabled = true;
    verifyBtn.textContent = 'Recalculating SHA-256 Hashes...';
    ledgerStatus.textContent = 'Computing Chain Proofs...';

    let delay = 0;
    blocks.forEach((block) => {
      setTimeout(() => {
        block.classList.remove('tampered');
        block.classList.add('verified');
        const hashElem = block.querySelector('.curr-hash');
        if (hashElem) hashElem.style.color = 'var(--accent-emerald-light)';
      }, delay);
      delay += 200;
    });

    setTimeout(() => {
      verifyBtn.disabled = false;
      verifyBtn.textContent = 'Re-Verify Cryptographic Chain';
      ledgerStatus.textContent = 'CHAIN INTEGRITY 100% VERIFIED';
      ledgerStatus.style.background = 'rgba(16, 185, 129, 0.2)';
      ledgerStatus.style.color = 'var(--accent-emerald-light)';
      ledgerStatus.style.borderColor = 'var(--accent-emerald)';
      showToast('Ledger audit proof: 4/4 blocks cryptographically intact!');
    }, delay + 150);
  });

  if (tamperBtn) {
    tamperBtn.addEventListener('click', () => {
      const block2 = document.getElementById('ledgerBlock2');
      if (block2) {
        block2.classList.remove('verified');
        block2.classList.add('tampered');
        const actionElem = block2.querySelector('.block-action');
        if (actionElem) actionElem.textContent = 'Code modification: Rogue actor injected unauthorized payload';
        const currHash = block2.querySelector('.curr-hash');
        if (currHash) {
          currHash.textContent = 'e4b02e9a... [HASH MISMATCH ERROR]';
          currHash.style.color = '#ef4444';
        }
      }

      const block3 = document.getElementById('ledgerBlock3');
      if (block3) {
        block3.classList.remove('verified');
        block3.classList.add('tampered');
      }

      ledgerStatus.textContent = 'CHAIN INTEGRITY COMPROMISED (TAMPER DETECTED)';
      ledgerStatus.style.background = 'rgba(239, 68, 68, 0.2)';
      ledgerStatus.style.color = '#f87171';
      ledgerStatus.style.borderColor = '#ef4444';

      showToast('ALERT: Tamper detected at Block #02! Cryptographic chain severed!');
    });
  }

  if (resetBtn) {
    resetBtn.addEventListener('click', () => {
      blocks.forEach(block => {
        block.classList.remove('tampered');
        block.classList.remove('verified');
      });
      const block2 = document.getElementById('ledgerBlock2');
      if (block2) {
        const actionElem = block2.querySelector('.block-action');
        if (actionElem) actionElem.textContent = 'Generated Architecture ADR: ADR-004 Microservices Decoupling';
        const currHash = block2.querySelector('.curr-hash');
        if (currHash) {
          currHash.textContent = '8a41bc91...f088';
          currHash.style.color = 'var(--text-primary)';
        }
      }
      ledgerStatus.textContent = 'Ready for Verification';
      ledgerStatus.style.background = 'rgba(99, 102, 241, 0.15)';
      ledgerStatus.style.color = 'var(--accent-primary-light)';
      ledgerStatus.style.borderColor = 'rgba(99, 102, 241, 0.3)';
      showToast('Ledger baseline restored.');
    });
  }
}

/* ====================================================================
   4. MULTI-AGENT SDLC PIPELINE SIMULATOR
   ==================================================================== */
function initSdlcSimulator() {
  const sampleBtns = document.querySelectorAll('.sample-sdlc-btn');
  const titleDisplay = document.getElementById('sdlcSimTitle');
  const matrixContainer = document.getElementById('sdlcMatrixBody');

  const sampleData = {
    sample1: {
      title: 'FinTech Payment Orchestrator & Multi-Rail Clearing Engine',
      rows: [
        { agent: 'Requirements Analyst', artifact: '01_BRD.md', detail: 'Sub-second idempotency, PCI-DSS Level 1 compliance, ISO 20022 messaging', status: 'VERIFIED' },
        { agent: 'Architecture Strategist', artifact: '11_ADR_Pipelining.md', detail: 'Event-driven Saga pattern with transactional outbox over Kafka', status: 'VERIFIED' },
        { agent: 'Code Reviewer & Linter', artifact: 'payment_router.py', detail: 'AST analyzed: 0 cyclomatic complexity violations, strict typing enforced', status: 'VERIFIED' },
        { agent: 'QA Test Synthesizer', artifact: 'test_payment_suite.py', detail: 'Synthesized 48 unit & boundary condition tests with 99.2% branch coverage', status: 'VERIFIED' },
        { agent: 'DevSecOps Specialist', artifact: '12_Threat_Model.md', detail: 'STRIDE model generated: Replay attack & race condition defenses validated', status: 'HARDENED' }
      ]
    },
    sample2: {
      title: 'Real-Time Robotics Telemetry & Drone Fleet Controller',
      rows: [
        { agent: 'Requirements Analyst', artifact: '02_PRD.md', detail: 'Deterministic 50Hz control loop, fail-safe geofencing, MAVLink v2 telemetry', status: 'VERIFIED' },
        { agent: 'Architecture Strategist', artifact: '05_Architecture.md', detail: 'Zero-copy shared memory IPC with WebAssembly edge runtime', status: 'VERIFIED' },
        { agent: 'Code Reviewer & Linter', artifact: 'telemetry_stream.py', detail: 'Zero memory leaks detected; memory-bounded circular ring buffer verified', status: 'VERIFIED' },
        { agent: 'QA Test Synthesizer', artifact: 'test_telemetry.py', detail: 'Hardware-in-the-loop mock tests synthesized with packet loss simulation', status: 'VERIFIED' },
        { agent: 'DevSecOps Specialist', artifact: '12_Security_Policy.md', detail: 'ECDSA telemetry signing and anti-spoofing verification implemented', status: 'HARDENED' }
      ]
    },
    sample3: {
      title: 'High-Concurrency Distributed Vector Search Database',
      rows: [
        { agent: 'Requirements Analyst', artifact: '06_TRD.md', detail: 'HNSW indexing, p99 search latency < 5ms for 10M 1536-dim vectors', status: 'VERIFIED' },
        { agent: 'Architecture Strategist', artifact: '07_Detailed_Design.md', detail: 'SIMD-accelerated AVX-512 distance calculation with tiered caching', status: 'VERIFIED' },
        { agent: 'Code Reviewer & Linter', artifact: 'hnsw_index.py', detail: 'Cache locality validated; lock-free concurrent read data structures verified', status: 'VERIFIED' },
        { agent: 'QA Test Synthesizer', artifact: 'test_vector_perf.py', detail: 'Recall@10 benchmarked at 98.7% across 1,000 concurrent query workers', status: 'VERIFIED' },
        { agent: 'DevSecOps Specialist', artifact: '12_Audit_Ledger.md', detail: 'Cryptographic SHA-256 access logs for all multi-tenant query operations', status: 'HARDENED' }
      ]
    }
  };

  sampleBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      sampleBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');

      const sampleKey = btn.getAttribute('data-sample');
      const data = sampleData[sampleKey];
      if (!data) return;

      if (titleDisplay) titleDisplay.textContent = data.title;
      if (matrixContainer) {
        matrixContainer.innerHTML = data.rows.map(row => `
          <tr>
            <td><strong style="color: var(--accent-primary-light);">${row.agent}</strong></td>
            <td><span class="brand-badge font-mono" style="font-size: 11px;">${row.artifact}</span></td>
            <td>${row.detail}</td>
            <td><span class="tag-monolith" style="color: var(--accent-emerald-light); font-weight: 700; font-size: 10px;">${row.status}</span></td>
          </tr>
        `).join('');
      }

      showToast(`Loaded Blueprint: ${data.title.split('—')[0]}`);
    });
  });
}

/* ====================================================================
   5. PLAYWRIGHT BROWSER & PINTEREST INGESTION SIMULATOR
   ==================================================================== */
function initBrowserAutomationSimulator() {
  const btnRun = document.getElementById('btnSimulateBrowser');
  const simProgress = document.getElementById('browserSimProgress');
  const simProgressFill = document.getElementById('browserSimProgressFill');
  const simStatus = document.getElementById('browserSimStatus');
  const simResult = document.getElementById('browserSimResult');

  if (!btnRun) return;

  btnRun.addEventListener('click', () => {
    btnRun.disabled = true;
    if (simProgress) simProgress.style.display = 'block';
    if (simResult) simResult.style.display = 'none';

    const steps = [
      { pct: 20, msg: 'Spawning isolated Playwright Chromium instance...' },
      { pct: 45, msg: 'Rehydrating CookieVault SSO credentials (Zero OTP prompt)...' },
      { pct: 70, msg: 'Sniffing direct 1080p MP4 media stream from DOM & network frames...' },
      { pct: 90, msg: 'Streaming MP4 video bytes to local output/downloads/ with SHA-256 verification...' },
      { pct: 100, msg: 'Download complete! 3.84 MB ingested into sovereign workspace.' }
    ];

    let stepIdx = 0;
    const interval = setInterval(() => {
      if (stepIdx < steps.length) {
        const s = steps[stepIdx];
        if (simProgressFill) simProgressFill.style.width = `${s.pct}%`;
        if (simStatus) simStatus.textContent = s.msg;
        stepIdx++;
      } else {
        clearInterval(interval);
        btnRun.disabled = false;
        if (simResult) simResult.style.display = 'block';
        showToast('Browser Ingestion Complete: Media asset saved to output/downloads/');
      }
    }, 400);
  });
}

/* ====================================================================
   6. DEVELOPER VELOCITY & ROI CALCULATOR
   ==================================================================== */
/* ====================================================================
   6. DEVELOPER VELOCITY & ROI CALCULATOR (ENTERPRISE SOVEREIGN)
   ==================================================================== */
function initVelocityCalculator() {
  const devsInput = document.getElementById('devsSlider');
  const prsInput = document.getElementById('prsSlider');
  const rateInput = document.getElementById('rateSlider');
  const complexityInput = document.getElementById('complexitySlider');

  const devsVal = document.getElementById('devsVal');
  const prsVal = document.getElementById('prsVal');
  const rateVal = document.getElementById('rateVal');
  const complexityVal = document.getElementById('complexityVal');

  const annualValueResult = document.getElementById('annualValueResult');
  const hoursSavedYearResult = document.getElementById('hoursSavedYearResult');
  const annualCloudSavedResult = document.getElementById('annualCloudSavedResult');
  const monthlyHoursSavedEl = document.getElementById('monthlyHoursSaved');
  const equivalentEngineersEl = document.getElementById('equivalentEngineers');
  const monthlyCloudSavedEl = document.getElementById('monthlyCloudSaved');
  const velocityMultiplierEl = document.getElementById('velocityMultiplier');

  const presetBtns = document.querySelectorAll('.roi-preset-btn');
  const currencySelector = document.getElementById('currencySelector');
  const currBtns = document.querySelectorAll('.curr-btn');
  const cloudRadios = document.querySelectorAll('input[name="cloudAiBaseline"]');
  const copyBtn = document.getElementById('copyRoiSummaryBtn');

  if (!devsInput || !prsInput) return;

  // Currencies Configuration & Exchange Conversion
  const currencies = {
    USD: { symbol: '$', rate: 1.0 },
    EUR: { symbol: '€', rate: 0.92 },
    GBP: { symbol: '£', rate: 0.79 },
    INR: { symbol: '₹', rate: 84.0 }
  };
  let currentCurrency = 'USD';

  // Team Archetype Presets
  const presets = {
    startup: { devs: 5, prs: 25, rate: 65, complexity: 20 },
    scaleup: { devs: 25, prs: 110, rate: 80, complexity: 85 },
    enterprise: { devs: 75, prs: 350, rate: 95, complexity: 400 },
    defense: { devs: 150, prs: 800, rate: 125, complexity: 850 }
  };

  function formatMoney(amountUSD) {
    const curr = currencies[currentCurrency] || currencies.USD;
    const converted = Math.round(amountUSD * curr.rate);
    return `${curr.symbol}${converted.toLocaleString()}`;
  }

  function updateSliderFill(slider) {
    const min = parseFloat(slider.min) || 0;
    const max = parseFloat(slider.max) || 100;
    const val = parseFloat(slider.value) || 0;
    const pct = ((val - min) / (max - min)) * 100;
    const isLight = document.documentElement.getAttribute('data-theme') === 'light';
    const trackBg = isLight ? '#e2e8f0' : 'rgba(255, 255, 255, 0.12)';
    slider.style.background = `linear-gradient(to right, var(--accent-primary) 0%, var(--accent-primary) ${pct}%, ${trackBg} ${pct}%, ${trackBg} 100%)`;
  }

  // Smooth number easing animation
  const activeAnimations = new Map();
  function animateValue(el, target, prefix = '', suffix = '', isCurrency = false) {
    if (!el) return;
    const start = el._currentVal || 0;
    el._currentVal = target;
    const duration = 400;
    const startTime = performance.now();

    if (activeAnimations.has(el)) {
      cancelAnimationFrame(activeAnimations.get(el));
    }

    function step(now) {
      const elapsed = Math.min((now - startTime) / duration, 1);
      const ease = 1 - Math.pow(1 - elapsed, 3);
      const current = Math.round(start + (target - start) * ease);

      if (isCurrency) {
        el.textContent = `${formatMoney(current)}${suffix}`;
      } else {
        el.textContent = `${prefix}${current.toLocaleString()}${suffix}`;
      }

      if (elapsed < 1) {
        const id = requestAnimationFrame(step);
        activeAnimations.set(el, id);
      } else {
        activeAnimations.delete(el);
      }
    }
    const id = requestAnimationFrame(step);
    activeAnimations.set(el, id);
  }

  let latestCalculation = {};

  function calculateVelocity() {
    const devs = parseInt(devsInput.value, 10);
    const prs = parseInt(prsInput.value, 10);
    const rate = rateInput ? parseInt(rateInput.value, 10) : 75;
    const complexityK = complexityInput ? parseInt(complexityInput.value, 10) : 45;

    // Update Slider Value Badges
    if (devsVal) devsVal.textContent = devs;
    if (prsVal) prsVal.textContent = `${prs} PRs`;
    if (rateVal) rateVal.textContent = `${formatMoney(rate)} / hr`;
    if (complexityVal) complexityVal.textContent = `${complexityK >= 1000 ? (complexityK / 1000).toFixed(1) + 'M' : complexityK + 'k'} LOC`;

    [devsInput, prsInput, rateInput, complexityInput].forEach(s => {
      if (s) updateSliderFill(s);
    });

    // Check Cloud Baseline Selection
    let cloudTier = 'standard';
    cloudRadios.forEach(r => {
      if (r.checked) cloudTier = r.value;
      const parentLabel = r.closest('.comp-radio-label');
      if (parentLabel) {
        if (r.checked) parentLabel.classList.add('active');
        else parentLabel.classList.remove('active');
      }
    });

    // Mathematical Formulation:
    // Traditional SDLC: ~14.0 hrs per PR
    // MONOLITH automated multi-agent: ~0.5 hrs per PR
    const hoursSavedPerPr = 13.5;
    const complexityFactor = 1 + Math.min(complexityK / 500, 1.8);
    const monthlyHoursSaved = Math.round(prs * hoursSavedPerPr * complexityFactor);
    const annualHoursSaved = monthlyHoursSaved * 12;

    const monthlyValueGenerated = monthlyHoursSaved * rate;
    const annualValueGenerated = monthlyValueGenerated * 12;

    // Equivalent full-time developers added (160 working hrs/month)
    const equivalentDevs = (monthlyHoursSaved / 160).toFixed(1);

    // Cloud SaaS bills averted
    let monthlyCloudAverted = 0;
    if (cloudTier === 'standard') {
      monthlyCloudAverted = devs * 60 + Math.round(prs * 6);
    } else if (cloudTier === 'enterprise') {
      monthlyCloudAverted = devs * 120 + Math.round(prs * 14);
    }
    const annualCloudAverted = monthlyCloudAverted * 12;

    const totalAnnualImpact = annualValueGenerated + annualCloudAverted;
    const velocityMultiplier = (14.0 / 0.5).toFixed(1);

    latestCalculation = {
      devs,
      prs,
      rate,
      complexityK,
      monthlyHoursSaved,
      annualHoursSaved,
      monthlyValueGenerated,
      annualValueGenerated,
      annualCloudAverted,
      totalAnnualImpact,
      equivalentDevs,
      velocityMultiplier
    };

    // Animate Output Metrics
    if (annualValueResult) animateValue(annualValueResult, totalAnnualImpact, '', '', true);
    if (hoursSavedYearResult) animateValue(hoursSavedYearResult, annualHoursSaved, '', '');
    if (annualCloudSavedResult) animateValue(annualCloudSavedResult, annualCloudAverted, '', '', true);
    if (monthlyHoursSavedEl) animateValue(monthlyHoursSavedEl, monthlyHoursSaved, '', ' hrs');
    if (monthlyCloudSavedEl) animateValue(monthlyCloudSavedEl, monthlyCloudAverted, '', ' / mo', true);
    if (equivalentEngineersEl) equivalentEngineersEl.textContent = `+${equivalentDevs} Devs`;
    if (velocityMultiplierEl) velocityMultiplierEl.textContent = `${velocityMultiplier}x Faster`;
  }

  // Slider Event Listeners
  [devsInput, prsInput, rateInput, complexityInput].forEach(slider => {
    if (slider) slider.addEventListener('input', calculateVelocity);
  });

  // Cloud AI Baseline Radios
  cloudRadios.forEach(radio => {
    radio.addEventListener('change', calculateVelocity);
  });

  // Currency Switcher
  currBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      currBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      currentCurrency = btn.getAttribute('data-currency') || 'USD';
      calculateVelocity();
      showToast(`Switched currency to ${currentCurrency}`);
    });
  });

  // Preset Buttons
  presetBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      presetBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const presetKey = btn.getAttribute('data-preset');
      const p = presets[presetKey];
      if (p) {
        if (devsInput) devsInput.value = p.devs;
        if (prsInput) prsInput.value = p.prs;
        if (rateInput) rateInput.value = p.rate;
        if (complexityInput) complexityInput.value = p.complexity;
        calculateVelocity();
        showToast(`Loaded ${presetKey.toUpperCase()} archetype configuration`);
      }
    });
  });

  // Copy Executive ROI Summary to Clipboard
  if (copyBtn) {
    copyBtn.addEventListener('click', async () => {
      const summary = [
        `=======================================================`,
        `MONOLITH AES — EXECUTIVE ROI & VELOCITY AUDIT BRIEFING`,
        `=======================================================`,
        `Engineering Team Scale: ${latestCalculation.devs} Developers`,
        `Monthly Pull Requests: ${latestCalculation.prs} Features / PRs`,
        `Codebase Monorepo Scale: ${latestCalculation.complexityK}k LOC`,
        `Loaded Engineering Rate: ${formatMoney(latestCalculation.rate)} / hr`,
        `-------------------------------------------------------`,
        `Annual Total Economic Impact: ${formatMoney(latestCalculation.totalAnnualImpact)}`,
        `Annual Engineering Hours Reclaimed: ${latestCalculation.annualHoursSaved?.toLocaleString()} hours`,
        `Equivalent Headcount Added (Recruit-Free): +${latestCalculation.equivalentDevs} Full-Time Engineers`,
        `Cloud AI Subscription Bills Eliminated: ${formatMoney(latestCalculation.annualCloudAverted)} / year`,
        `Spec-to-Ship Cycle Acceleration: ${latestCalculation.velocityMultiplier}x Faster`,
        `-------------------------------------------------------`,
        `Data Sovereignty: 100% On-Premise &bull; Air-Gapped &bull; $0 Token Cost`,
        `MONOLITH Systems: https://monolith.ai-workbench.local`,
        `=======================================================`
      ].join('\n');

      try {
        await navigator.clipboard.writeText(summary);
        showToast('Executive ROI Briefing copied to clipboard!');
      } catch (err) {
        showToast('ROI Summary formatted successfully.');
      }
    });
  }

  calculateVelocity();
}


/* ====================================================================
   8. TERMINAL TAB SWITCHER
   ==================================================================== */
function initTerminalTabs() {
  const tabBtns = document.querySelectorAll('.sim-tab-btn');
  const tabContents = document.querySelectorAll('.sim-tab-content');

  tabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      tabBtns.forEach(b => b.classList.remove('active'));
      tabContents.forEach(c => c.classList.remove('active'));

      btn.classList.add('active');
      const tabId = btn.getAttribute('data-tab');
      const targetContent = document.getElementById(`tab-${tabId}`);
      if (targetContent) targetContent.classList.add('active');
    });
  });
}

/* ====================================================================
   9. TECHNICAL FAQ ACCORDION
   ==================================================================== */
function initFaqAccordion() {
  const faqItems = document.querySelectorAll('.faq-item');

  faqItems.forEach(item => {
    const question = item.querySelector('.faq-question');
    if (!question) return;

    question.addEventListener('click', () => {
      const isOpen = item.classList.contains('active');
      faqItems.forEach(i => i.classList.remove('active'));
      if (!isOpen) item.classList.add('active');
    });
  });
}

/* ====================================================================
   10. SMOOTH SCROLLING
   ==================================================================== */
function initSmoothScroll() {
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function(e) {
      const targetId = this.getAttribute('href');
      if (targetId === '#') return;
      const target = document.querySelector(targetId);
      if (target) {
        e.preventDefault();
        target.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    });
  });
}

/* ====================================================================
   11. MOBILE NAVIGATION DRAWER
   ==================================================================== */
function initMobileNavigation() {
  const toggleBtn = document.getElementById('mobileNavToggle');
  const drawer = document.getElementById('mobileNavDrawer');
  const icon = document.getElementById('mobileMenuIcon');

  if (!toggleBtn || !drawer) return;

  function setDrawerOpen(isOpen) {
    if (isOpen) {
      drawer.classList.add('open');
      if (icon) {
        icon.innerHTML = `
          <line x1="18" y1="6" x2="6" y2="18"></line>
          <line x1="6" y1="6" x2="18" y2="18"></line>
        `;
      }
    } else {
      drawer.classList.remove('open');
      if (icon) {
        icon.innerHTML = `
          <line x1="3" y1="12" x2="21" y2="12"></line>
          <line x1="3" y1="6" x2="21" y2="6"></line>
          <line x1="3" y1="18" x2="21" y2="18"></line>
        `;
      }
    }
  }

  toggleBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    const isOpen = drawer.classList.contains('open');
    setDrawerOpen(!isOpen);
  });

  drawer.querySelectorAll('a').forEach(link => {
    link.addEventListener('click', () => {
      setDrawerOpen(false);
    });
  });

  document.addEventListener('click', (e) => {
    if (drawer.classList.contains('open') && !drawer.contains(e.target) && !toggleBtn.contains(e.target)) {
      setDrawerOpen(false);
    }
  });
}

/* ====================================================================
   12. ACTIVE NAVIGATION SCROLLSPY
   ==================================================================== */
function initScrollSpy() {
  const sections = Array.from(document.querySelectorAll('section[id]'));
  const navLinks = Array.from(document.querySelectorAll('.nav-links a, .mobile-nav-drawer a'));

  if (!sections.length || !navLinks.length) return;

  function setActiveLink(id) {
    navLinks.forEach(link => {
      if (link.getAttribute('href') === `#${id}`) {
        link.classList.add('active');
      } else if (link.getAttribute('href')?.startsWith('#')) {
        link.classList.remove('active');
      }
    });
  }

  function updateActiveSection() {
    const scrollPosition = window.scrollY + 120; // 120px offset for sticky navbar + breathing room

    // If near the very top of the page, highlight the first section (Overview)
    if (window.scrollY < 200 && sections.length > 0) {
      setActiveLink(sections[0].getAttribute('id'));
      return;
    }

    // Check if user has scrolled near bottom of page
    if ((window.innerHeight + window.scrollY) >= document.documentElement.scrollHeight - 50) {
      const lastSection = sections[sections.length - 1];
      if (lastSection) {
        setActiveLink(lastSection.getAttribute('id'));
        return;
      }
    }

    let currentSectionId = sections[0].getAttribute('id');
    for (let i = 0; i < sections.length; i++) {
      const section = sections[i];
      const sectionTop = section.offsetTop;
      if (scrollPosition >= sectionTop) {
        currentSectionId = section.getAttribute('id');
      }
    }

    setActiveLink(currentSectionId);
  }

  // Initial call on load
  updateActiveSection();

  // Throttled scroll listener
  let ticking = false;
  window.addEventListener('scroll', () => {
    if (!ticking) {
      window.requestAnimationFrame(() => {
        updateActiveSection();
        ticking = false;
      });
      ticking = true;
    }
  }, { passive: true });
}

/* ====================================================================
   UTILITY: TOAST NOTIFICATIONS
   ==================================================================== */
function showToast(message) {
  let toast = document.getElementById('monolithToast');
  if (!toast) {
    toast = document.createElement('div');
    toast.id = 'monolithToast';
    toast.style.cssText = `
      position: fixed;
      bottom: 24px;
      right: 24px;
      background: var(--bg-surface-elevated, #17223d);
      color: var(--text-primary, #ffffff);
      border: 1px solid var(--border-medium, rgba(255,255,255,0.15));
      box-shadow: 0 10px 30px rgba(0,0,0,0.5);
      border-radius: 9999px;
      padding: 10px 20px;
      font-size: 13px;
      font-weight: 600;
      z-index: 10000;
      display: flex;
      align-items: center;
      gap: 8px;
      transform: translateY(100px);
      opacity: 0;
      transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
    `;
    document.body.appendChild(toast);
  }

  toast.innerHTML = `<span style="color: var(--accent-primary-light, #818cf8); font-size: 16px; line-height: 1;">&bull;</span> ${message}`;
  toast.style.transform = 'translateY(0)';
  toast.style.opacity = '1';

  clearTimeout(toast._timeout);
  toast._timeout = setTimeout(() => {
    toast.style.transform = 'translateY(100px)';
    toast.style.opacity = '0';
  }, 2600);
}

/* ====================================================================
   7. CHROMATIC ABERRATION WEBGL SINE WAVE (Three.js Hero Background)
   Original reference: Yuki (@Web_yuki1027 on CodePen - GLSL Sample027)
   ==================================================================== */
function initHeroSineWave() {
  const canvas = document.getElementById('hero-chromatic-canvas');
  const heroSection = document.querySelector('.hero-section');
  if (!canvas || !heroSection) return;

  const vertexShader = `
    attribute vec3 position;
    void main() {
      gl_Position = vec4(position, 1.0);
    }
  `;

  const fragmentShader = `
    precision highp float;
    uniform vec2 resolution;
    uniform float time;
    uniform float xScale;
    uniform float yScale;
    uniform float distortion;

    void main() {
      vec2 p = (gl_FragCoord.xy * 2.0 - resolution) / min(resolution.x, resolution.y);
      
      float d = length(p) * distortion;
      
      float rx = p.x * (1.0 + d);
      float gx = p.x;
      float bx = p.x * (1.0 - d);

      float r = 0.05 / abs(p.y + sin((rx + time) * xScale) * yScale);
      float g = 0.05 / abs(p.y + sin((gx + time) * xScale) * yScale);
      float b = 0.05 / abs(p.y + sin((bx + time) * xScale) * yScale);
      
      gl_FragColor = vec4(r, g, b, 1.0);
    }
  `;

  let isIntersecting = true;
  let animId = null;

  function getHeroSize() {
    const rect = heroSection.getBoundingClientRect();
    const width = Math.max(rect.width, 320);
    const height = Math.max(rect.height, 300);
    return { width, height };
  }

  // Interactive mouse/touch dynamics
  const params = {
    xScale: 1.0,
    yScale: 0.5,
    distortion: 0.05,
    targetXScale: 1.0,
    targetYScale: 0.5,
    targetDistortion: 0.05,
    time: 0.0
  };

  heroSection.addEventListener('mousemove', (e) => {
    const rect = heroSection.getBoundingClientRect();
    const nx = ((e.clientX - rect.left) / rect.width) * 2 - 1;
    const ny = ((e.clientY - rect.top) / rect.height) * 2 - 1;
    params.targetDistortion = 0.045 + Math.hypot(nx, ny) * 0.035;
    params.targetXScale = 1.0 + nx * 0.25;
    params.targetYScale = 0.5 + Math.abs(ny) * 0.25;
  }, { passive: true });

  heroSection.addEventListener('mouseleave', () => {
    params.targetDistortion = 0.05;
    params.targetXScale = 1.0;
    params.targetYScale = 0.5;
  });

  if (typeof THREE !== 'undefined') {
    initThreeJsMode();
  } else {
    initNativeWebGlMode();
  }

  function initThreeJsMode() {
    const initialSize = getHeroSize();
    const dpr = Math.min(window.devicePixelRatio || 1, 2);

    const renderer = new THREE.WebGLRenderer({
      canvas: canvas,
      alpha: true,
      antialias: false,
      powerPreference: 'high-performance'
    });
    renderer.setPixelRatio(dpr);
    renderer.setClearColor(0x000000, 0);
    renderer.setSize(initialSize.width, initialSize.height, false);

    const scene = new THREE.Scene();
    const camera = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);

    const uniforms = {
      resolution: { value: new THREE.Vector2(initialSize.width * dpr, initialSize.height * dpr) },
      time: { value: 0.0 },
      xScale: { value: params.xScale },
      yScale: { value: params.yScale },
      distortion: { value: params.distortion }
    };

    const geometry = new THREE.BufferGeometry();
    const positions = new Float32Array([
      -1, -1, 0,
       1, -1, 0,
      -1,  1, 0,
       1, -1, 0,
      -1,  1, 0,
       1,  1, 0
    ]);
    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));

    const material = new THREE.RawShaderMaterial({
      vertexShader: vertexShader,
      fragmentShader: fragmentShader,
      uniforms: uniforms,
      side: THREE.DoubleSide,
      transparent: true,
      depthWrite: false,
      depthTest: false
    });

    const mesh = new THREE.Mesh(geometry, material);
    scene.add(mesh);

    function onResize() {
      const { width, height } = getHeroSize();
      const currentDpr = Math.min(window.devicePixelRatio || 1, 2);
      renderer.setPixelRatio(currentDpr);
      renderer.setSize(width, height, false);
      uniforms.resolution.value.set(width * currentDpr, height * currentDpr);
    }

    window.addEventListener('resize', onResize, { passive: true });

    let lastTime = performance.now();
    function animate(currentTime) {
      if (!isIntersecting) {
        animId = null;
        return;
      }
      animId = requestAnimationFrame(animate);

      const delta = Math.min((currentTime - lastTime) / 1000, 0.1);
      lastTime = currentTime;

      params.time += delta * 0.9;
      uniforms.time.value = params.time;

      params.distortion += (params.targetDistortion - params.distortion) * 0.06;
      params.xScale += (params.targetXScale - params.xScale) * 0.06;
      params.yScale += (params.targetYScale - params.yScale) * 0.06;

      uniforms.distortion.value = params.distortion;
      uniforms.xScale.value = params.xScale;
      uniforms.yScale.value = params.yScale;

      renderer.render(scene, camera);
    }

    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        isIntersecting = entry.isIntersecting;
        if (isIntersecting && !animId) {
          lastTime = performance.now();
          animId = requestAnimationFrame(animate);
        }
      });
    }, { threshold: 0.05 });

    observer.observe(heroSection);
    animId = requestAnimationFrame(animate);
  }

  function initNativeWebGlMode() {
    const gl = canvas.getContext('webgl', { alpha: true, antialias: false, powerPreference: 'high-performance' });
    if (!gl) return;

    function createShader(type, src) {
      const s = gl.createShader(type);
      gl.shaderSource(s, src);
      gl.compileShader(s);
      return s;
    }

    const vShader = createShader(gl.VERTEX_SHADER, vertexShader);
    const fShader = createShader(gl.FRAGMENT_SHADER, fragmentShader);
    const program = gl.createProgram();
    gl.attachShader(program, vShader);
    gl.attachShader(program, fShader);
    gl.linkProgram(program);
    gl.useProgram(program);

    const posBuffer = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, posBuffer);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([
      -1, -1,
       1, -1,
      -1,  1,
       1,  1
    ]), gl.STATIC_DRAW);

    const posLoc = gl.getAttribLocation(program, 'position');
    gl.enableVertexAttribArray(posLoc);
    gl.vertexAttribPointer(posLoc, 2, gl.FLOAT, false, 0, 0);

    const uRes = gl.getUniformLocation(program, 'resolution');
    const uTime = gl.getUniformLocation(program, 'time');
    const uXScale = gl.getUniformLocation(program, 'xScale');
    const uYScale = gl.getUniformLocation(program, 'yScale');
    const uDist = gl.getUniformLocation(program, 'distortion');

    function onResize() {
      const { width, height } = getHeroSize();
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      canvas.width = Math.floor(width * dpr);
      canvas.height = Math.floor(height * dpr);
      gl.viewport(0, 0, canvas.width, canvas.height);
    }
    window.addEventListener('resize', onResize, { passive: true });
    onResize();

    let lastTime = performance.now();
    function animate(currentTime) {
      if (!isIntersecting) {
        animId = null;
        return;
      }
      animId = requestAnimationFrame(animate);

      const delta = Math.min((currentTime - lastTime) / 1000, 0.1);
      lastTime = currentTime;

      params.time += delta * 0.9;
      params.distortion += (params.targetDistortion - params.distortion) * 0.06;
      params.xScale += (params.targetXScale - params.xScale) * 0.06;
      params.yScale += (params.targetYScale - params.yScale) * 0.06;

      gl.uniform2f(uRes, canvas.width, canvas.height);
      gl.uniform1f(uTime, params.time);
      gl.uniform1f(uXScale, params.xScale);
      gl.uniform1f(uYScale, params.yScale);
      gl.uniform1f(uDist, params.distortion);

      gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
    }

    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        isIntersecting = entry.isIntersecting;
        if (isIntersecting && !animId) {
          lastTime = performance.now();
          animId = requestAnimationFrame(animate);
        }
      });
    }, { threshold: 0.05 });

    observer.observe(heroSection);
    animId = requestAnimationFrame(animate);
  }
}

/* ====================================================================
   8. WEBGL LIQUID DISTORTION TYPOGRAPHY MASK ("MONOLITH")
   Original reference: Robin Delaporte (@robin-dela on CodePen - KKPYoBq)
   Flowmap fluid simulation + chromatic aberration vector cutout
   ==================================================================== */
function initMonolithLiquidTypography() {
  const container = document.getElementById('monolithLiquidTypoWrap');
  const canvas = document.getElementById('monolith-liquid-canvas');
  if (!container || !canvas) return;

  if (typeof THREE === 'undefined') {
    return;
  }

  let textCanvas = null;
  let textTexture = null;

  function renderTextMask() {
    const rect = container.getBoundingClientRect();
    const w = Math.max(Math.floor(rect.width * 2), 1600);
    const h = Math.max(Math.floor(rect.height * 2), 320);

    if (!textCanvas) {
      textCanvas = document.createElement('canvas');
    }
    textCanvas.width = w;
    textCanvas.height = h;

    const ctx = textCanvas.getContext('2d');
    ctx.clearRect(0, 0, w, h);

    const fontSize = Math.floor(h * 0.70);
    ctx.font = `900 ${fontSize}px 'Orbitron', 'Inter', system-ui, sans-serif`;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';

    // Letter-spaced vector cutout mask
    const text = 'MONOLITH';
    
    // Draw solid mask base (white = opaque in cutout shader)
    ctx.fillStyle = '#ffffff';
    ctx.fillText(text, w / 2, h / 2);

    // Subtle edge highlight stroke
    ctx.lineWidth = Math.max(2, Math.floor(h * 0.015));
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.45)';
    ctx.strokeText(text, w / 2, h / 2);

    if (textTexture) {
      textTexture.needsUpdate = true;
    }
  }

  renderTextMask();
  textTexture = new THREE.CanvasTexture(textCanvas);
  textTexture.minFilter = THREE.LinearFilter;
  textTexture.magFilter = THREE.LinearFilter;

  // Re-render once web fonts are fully loaded
  if (document.fonts && document.fonts.ready) {
    document.fonts.ready.then(() => {
      renderTextMask();
    });
  }

  const dpr = Math.min(window.devicePixelRatio || 1, 2);
  const renderer = new THREE.WebGLRenderer({
    canvas: canvas,
    alpha: true,
    antialias: true,
    powerPreference: 'high-performance'
  });
  renderer.setPixelRatio(dpr);
  renderer.setSize(container.clientWidth, container.clientHeight, false);

  // Ping-Pong Flowmap Simulation (128x128 FBOs)
  const flowSize = 128;
  const targetOptions = {
    minFilter: THREE.LinearFilter,
    magFilter: THREE.LinearFilter,
    depthBuffer: false
  };
  if (renderer.capabilities.isWebGL2 || renderer.extensions.has('OES_texture_half_float')) {
    targetOptions.type = THREE.HalfFloatType;
  }

  let flowA = new THREE.WebGLRenderTarget(flowSize, flowSize, targetOptions);
  let flowB = flowA.clone();
  let currentFlow = flowA;
  let nextFlow = flowB;

  const flowVertex = `
    varying vec2 vUv;
    void main() {
      vUv = uv;
      gl_Position = vec4(position, 1.0);
    }
  `;

  const flowFragment = `
    precision highp float;
    uniform sampler2D tPrevFlow;
    uniform vec2 uMouse;
    uniform vec2 uVelocity;
    uniform float uFalloff;
    uniform float uDissipation;
    uniform float uAspect;
    varying vec2 vUv;

    void main() {
      vec4 prev = texture2D(tPrevFlow, vUv) * uDissipation;
      vec2 cursor = vUv - uMouse;
      cursor.x *= uAspect;
      float dist = length(cursor);
      float stamp = smoothstep(uFalloff, 0.0, dist);
      vec2 vel = uVelocity * vec2(1.0, -1.0);
      vec3 force = vec3(vel, length(vel));
      vec3 result = mix(prev.rgb, force, stamp * min(1.0, length(vel) * 12.0));
      gl_FragColor = vec4(result, 1.0);
    }
  `;

  const flowScene = new THREE.Scene();
  const flowCamera = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);
  const flowUniforms = {
    tPrevFlow: { value: currentFlow.texture },
    uMouse: { value: new THREE.Vector2(-1, -1) },
    uVelocity: { value: new THREE.Vector2(0, 0) },
    uFalloff: { value: 0.18 },
    uDissipation: { value: 0.95 },
    uAspect: { value: container.clientWidth / container.clientHeight }
  };

  const quadGeom = new THREE.PlaneGeometry(2, 2);
  const flowMat = new THREE.ShaderMaterial({
    vertexShader: flowVertex,
    fragmentShader: flowFragment,
    uniforms: flowUniforms,
    depthTest: false,
    depthWrite: false
  });
  flowScene.add(new THREE.Mesh(quadGeom, flowMat));

  // Liquid Typography Output Mesh
  const displayVertex = `
    varying vec2 vUv;
    void main() {
      vUv = uv;
      gl_Position = vec4(position, 1.0);
    }
  `;

  const displayFragment = `
    precision highp float;
    uniform sampler2D tTextMask;
    uniform sampler2D tFlow;
    uniform float uTime;
    varying vec2 vUv;

    vec3 getLiquidColor(vec2 uv, float time, vec2 flow) {
      vec2 distortedUv = uv + flow * 0.45;
      float wave1 = sin(distortedUv.x * 6.0 + time * 1.8 + flow.x * 4.0);
      float wave2 = cos(distortedUv.y * 6.0 - time * 1.4 + flow.y * 4.0);
      float wave3 = sin((distortedUv.x + distortedUv.y) * 4.0 + time * 1.0);
      
      vec3 colIndigo = vec3(0.388, 0.400, 0.945);
      vec3 colCyan   = vec3(0.024, 0.714, 0.831);
      vec3 colPurple = vec3(0.545, 0.361, 0.965);
      vec3 colWhite  = vec3(1.0, 1.0, 1.0);
      
      float t = 0.5 + 0.5 * sin(wave1 + wave2 + wave3);
      vec3 base = mix(colIndigo, colCyan, t);
      base = mix(base, colPurple, 0.5 + 0.5 * wave2);
      
      float specular = pow(clamp(0.5 + 0.5 * (wave1 * wave2 + length(flow) * 2.5), 0.0, 1.0), 3.5);
      base += colWhite * specular * 0.85;
      return base;
    }

    void main() {
      vec3 flow = texture2D(tFlow, vUv).rgb;
      vec2 flowOffset = flow.xy * 0.20;

      // Chromatic Aberration RGB split on the text mask
      float maskR = texture2D(tTextMask, vUv - flowOffset * 1.25).r;
      float maskG = texture2D(tTextMask, vUv - flowOffset).g;
      float maskB = texture2D(tTextMask, vUv - flowOffset * 0.75).b;
      float maskA = max(maskR, max(maskG, maskB));

      vec3 liquid = getLiquidColor(vUv, uTime, flow.xy);
      liquid.r += maskR * 0.25;
      liquid.b += maskB * 0.25;

      float flowIntensity = clamp(length(flow.xy) * 12.0, 0.0, 1.0);
      vec3 idleColor = vec3(0.96, 0.98, 1.0);
      vec3 finalColor = mix(idleColor, liquid, 0.35 + 0.65 * flowIntensity);

      gl_FragColor = vec4(finalColor, maskA);
    }
  `;

  const displayScene = new THREE.Scene();
  const displayCamera = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);
  const displayUniforms = {
    tTextMask: { value: textTexture },
    tFlow: { value: currentFlow.texture },
    uTime: { value: 0 }
  };

  const displayMat = new THREE.ShaderMaterial({
    vertexShader: displayVertex,
    fragmentShader: displayFragment,
    uniforms: displayUniforms,
    transparent: true,
    depthTest: false,
    depthWrite: false
  });
  displayScene.add(new THREE.Mesh(quadGeom, displayMat));

  // Pointer velocity tracking
  const mouse = new THREE.Vector2(-1, -1);
  const velocity = new THREE.Vector2(0, 0);
  const targetVelocity = new THREE.Vector2(0, 0);
  const lastMouse = new THREE.Vector2(-1, -1);
  let lastTime = performance.now();

  function onPointerMove(clientX, clientY) {
    const rect = container.getBoundingClientRect();
    const x = (clientX - rect.left) / rect.width;
    const y = (clientY - rect.top) / rect.height;
    mouse.set(x, 1.0 - y);

    const now = performance.now();
    const dt = Math.max(16, now - lastTime);
    lastTime = now;

    if (lastMouse.x >= 0) {
      targetVelocity.set((x - lastMouse.x) / (dt * 0.04), (y - lastMouse.y) / (dt * 0.04));
    }
    lastMouse.set(x, y);
  }

  container.addEventListener('mousemove', (e) => {
    onPointerMove(e.clientX, e.clientY);
  }, { passive: true });

  container.addEventListener('mouseleave', () => {
    mouse.set(-1, -1);
    targetVelocity.set(0, 0);
    lastMouse.set(-1, -1);
  });

  container.addEventListener('touchmove', (e) => {
    if (e.touches && e.touches[0]) {
      onPointerMove(e.touches[0].clientX, e.touches[0].clientY);
    }
  }, { passive: true });

  container.addEventListener('touchend', () => {
    mouse.set(-1, -1);
    targetVelocity.set(0, 0);
    lastMouse.set(-1, -1);
  });

  function onResize() {
    const w = container.clientWidth;
    const h = container.clientHeight;
    if (w <= 0 || h <= 0) return;
    const currentDpr = Math.min(window.devicePixelRatio || 1, 2);
    renderer.setPixelRatio(currentDpr);
    renderer.setSize(w, h, false);
    flowUniforms.uAspect.value = w / h;
    renderTextMask();
  }

  window.addEventListener('resize', onResize, { passive: true });

  // Ambient fluid ripple simulation for subtle idle breathing
  let time = 0;
  let isIntersecting = true;
  let animId = null;

  function animate() {
    if (!isIntersecting) {
      animId = null;
      return;
    }
    animId = requestAnimationFrame(animate);
    time += 0.016;

    velocity.lerp(targetVelocity, 0.25);
    targetVelocity.multiplyScalar(0.90);

    // Subtle gentle ambient ripple when mouse is idle
    if (mouse.x < 0) {
      const ambientX = 0.5 + Math.sin(time * 0.8) * 0.35;
      const ambientY = 0.5 + Math.cos(time * 1.1) * 0.25;
      flowUniforms.uMouse.value.set(ambientX, ambientY);
      flowUniforms.uVelocity.value.set(Math.cos(time * 1.5) * 0.08, Math.sin(time * 1.2) * 0.08);
    } else {
      flowUniforms.uMouse.value.copy(mouse);
      flowUniforms.uVelocity.value.copy(velocity);
    }

    flowUniforms.tPrevFlow.value = currentFlow.texture;

    // Render flowmap to nextFlow
    renderer.setRenderTarget(nextFlow);
    renderer.render(flowScene, flowCamera);
    renderer.setRenderTarget(null);

    // Swap ping-pong targets
    const temp = currentFlow;
    currentFlow = nextFlow;
    nextFlow = temp;

    // Render final liquid typography composite
    displayUniforms.tFlow.value = currentFlow.texture;
    displayUniforms.uTime.value = time;
    renderer.render(displayScene, displayCamera);
  }

  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      isIntersecting = entry.isIntersecting;
      if (isIntersecting && !animId) {
        lastTime = performance.now();
        animId = requestAnimationFrame(animate);
      }
    });
  }, { threshold: 0.05 });

  observer.observe(container);
  animId = requestAnimationFrame(animate);
}
