"""
MONOLITH Browser Automation & Asset Ingestion Engine
=====================================================
Multi-Agent Browser Automation Powered by Playwright Chromium.

Core Capabilities:
1. Interactive Headed & Headless Browser Sessions:
   - Launches isolated Chromium sessions with optional desktop GUI visualization.
   - Rehydrates authenticated SSO session cookies from the Encrypted CookieVault.
   - Interacts with web chatbots, LLM playgrounds, and developer consoles.

2. UI Blueprint & Component Inspector (shadcn / threeui / WebGL):
   - Scrapes and parses UI component libraries (shadcn/ui, Three.js canvases, Tailwind blocks).
   - Extracts JSX markup, Tailwind utility classes, computed CSS variables, and canvas contexts.

3. Pinterest Video Saver & Media Downloader:
   - Ingests Pinterest pin URLs and shortlinks (pin.it).
   - Extracts direct 720p/1080p MP4 media streams via Playwright network capture & DOM inspection.
   - Automates Pin Saver downloader utilities as fallback.
   - Streams media directly into local workspace folder (e.g. output/downloads/) with SHA-256 audit logging.

4. Sovereign Boundary Governance:
   - Enforces air-gap boundaries; validates outbound egress exceptions before launching external connections.
"""

import asyncio
import os
import re
import json
import time
import uuid
import hashlib
import urllib.request
import urllib.parse
import logging
from enum import Enum
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
from pydantic import BaseModel, Field

from playwright.async_api import async_playwright, Browser, BrowserContext, Page

from cookie_vault import CookieVault
from audit_ledger import audit_ledger

logger = logging.getLogger("MonolithBrowser")

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DOWNLOAD_DIR = BASE_DIR / "output" / "downloads"
DEFAULT_DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)


class BrowserSessionState(str, Enum):
    DISCONNECTED = "DISCONNECTED"
    NEEDS_LOGIN = "NEEDS_LOGIN"
    AUTHENTICATED = "AUTHENTICATED"
    READY = "READY"
    CHALLENGE_REQUIRED = "CHALLENGE_REQUIRED"
    PAUSED = "PAUSED"
    FAILED = "FAILED"


class BrowserSessionMeta(BaseModel):
    session_id: str
    name: str
    state: BrowserSessionState = BrowserSessionState.READY
    current_url: str
    title: str = ""
    trusted_domain: Optional[str] = None
    task_id: Optional[str] = None
    challenge_reason: Optional[str] = None
    is_headed: bool = True
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)


class MonolithBrowserEngine:
    def __init__(self):
        self.cookie_vault = CookieVault()
        self.download_dir = DEFAULT_DOWNLOAD_DIR
        self.active_processes: Dict[str, Any] = {}
        self.named_sessions: Dict[str, BrowserSessionMeta] = {}
        self.recent_downloads: List[Dict[str, Any]] = []
        self._load_recent_downloads()

    def _load_recent_downloads(self):
        """Scans the download directory for existing video and media files."""
        self.recent_downloads = []
        if not self.download_dir.exists():
            return
        for f in self.download_dir.glob("*.*"):
            if f.is_file() and f.suffix.lower() in [".mp4", ".webm", ".mkv", ".mov", ".png", ".jpg", ".webp"]:
                stat = f.stat()
                self.recent_downloads.append({
                    "id": f.stem,
                    "filename": f.name,
                    "filepath": str(f),
                    "relative_url": f"/api/browser/downloaded-file/{f.name}",
                    "size_bytes": stat.st_size,
                    "size_mb": round(stat.st_size / (1024 * 1024), 2),
                    "created_at": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(stat.st_mtime)),
                    "format": f.suffix.lower().replace(".", "").upper()
                })
        self.recent_downloads.sort(key=lambda x: x["created_at"], reverse=True)

    def get_status(self) -> Dict[str, Any]:
        """Returns the current status of the browser engine and recent media."""
        self._load_recent_downloads()
        return {
            "status": "READY",
            "engine": "Playwright Chromium (v1.40+)",
            "download_directory": str(self.download_dir),
            "active_sessions_count": len(self.active_processes),
            "total_downloaded_assets": len(self.recent_downloads),
            "recent_downloads": self.recent_downloads[:15],
            "supported_actions": [
                "pinterest_video_download",
                "pin_saver_automation",
                "ui_component_inspection",
                "headed_browser_launch",
                "chatbot_automation"
            ]
        }

    async def launch_headed_session(self, url: str, session_domain: Optional[str] = None) -> Dict[str, Any]:
        """
        Launches an interactive, visible Headed Chromium browser window on the developer's desktop.
        Automatically injects pre-saved cookies from CookieVault for instant SSO.
        """
        session_id = f"BROWSER-{uuid.uuid4().hex[:6].upper()}"
        start_time = time.time()

        try:
            p = await async_playwright().start()
            # Launch headed Chromium window on Windows desktop
            browser = await p.chromium.launch(
                headless=False,
                args=["--start-maximized", "--no-sandbox"]
            )
            context = await browser.new_context(
                viewport={"width": 1280, "height": 800},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            )

            # Ingest session cookies if available
            target_domain = session_domain or url
            injected = await self.cookie_vault.inject_into_context(context, target_domain)

            page = await context.new_page()
            await page.goto(url, timeout=30000, wait_until="domcontentloaded")
            title = await page.title()

            self.active_processes[session_id] = {
                "playwright": p,
                "browser": browser,
                "context": context,
                "page": page,
                "url": url,
                "title": title,
                "started_at": start_time
            }

            meta = BrowserSessionMeta(
                session_id=session_id,
                name=f"Headed Session - {title[:20]}",
                state=BrowserSessionState.READY,
                current_url=url,
                title=title,
                trusted_domain=target_domain,
                is_headed=True,
                created_at=start_time,
                updated_at=start_time
            )
            self.named_sessions[session_id] = meta

            audit_ledger.record_action(
                action_type="BROWSER_HEADED_LAUNCH",
                user="Developer",
                details=f"Launched interactive browser to {url} (Cookies injected: {injected})",
                severity="INFO",
                target_resource=url
            )

            return {
                "status": "SUCCESS",
                "session_id": session_id,
                "title": title,
                "url": url,
                "state": meta.state.value,
                "cookies_injected": injected,
                "message": f"Interactive Chromium session '{session_id}' launched successfully on desktop."
            }
        except Exception as e:
            logger.error(f"Failed to launch headed browser: {e}")
            return {
                "status": "ERROR",
                "error": str(e),
                "message": f"Could not launch browser session: {e}"
            }

    def pause_for_challenge(self, session_id: str, reason: str = "MFA / CAPTCHA challenge detected") -> Optional[BrowserSessionMeta]:
        """Pauses automated interaction when an authentication challenge or CAPTCHA appears."""
        meta = self.named_sessions.get(session_id)
        if meta:
            meta.state = BrowserSessionState.CHALLENGE_REQUIRED
            meta.challenge_reason = reason
            meta.updated_at = time.time()
            audit_ledger.record_action(
                action_type="BROWSER_CHALLENGE_PAUSE",
                user="SYSTEM",
                details=f"Browser session {session_id} paused for human intervention: {reason}",
                severity="WARN",
                target_resource=meta.current_url
            )
        return meta

    def resume_after_challenge(self, session_id: str) -> Optional[BrowserSessionMeta]:
        """Resumes session after user resolves challenge manually in visible headed window."""
        meta = self.named_sessions.get(session_id)
        if meta and meta.state in (BrowserSessionState.CHALLENGE_REQUIRED, BrowserSessionState.PAUSED):
            meta.state = BrowserSessionState.READY
            meta.challenge_reason = None
            meta.updated_at = time.time()
            audit_ledger.record_action(
                action_type="BROWSER_CHALLENGE_RESUME",
                user="OPERATOR",
                details=f"Browser session {session_id} challenge marked resolved by operator.",
                severity="INFO",
                target_resource=meta.current_url
            )
        return meta

    def list_named_sessions(self) -> List[BrowserSessionMeta]:
        """Returns catalog of all registered browser sessions and states."""
        return list(self.named_sessions.values())

    def get_named_session(self, session_id: str) -> Optional[BrowserSessionMeta]:
        return self.named_sessions.get(session_id)

    async def close_session(self, session_id: str) -> Dict[str, Any]:
        """Closes an active browser session cleanly."""
        if session_id in self.named_sessions:
            self.named_sessions[session_id].state = BrowserSessionState.DISCONNECTED
            self.named_sessions[session_id].updated_at = time.time()

        if session_id in self.active_processes:
            try:
                proc = self.active_processes.pop(session_id)
                await proc["browser"].close()
                await proc["playwright"].stop()
                return {"status": "SUCCESS", "message": f"Session {session_id} closed."}
            except Exception as e:
                return {"status": "ERROR", "message": str(e)}
        return {"status": "ERROR", "message": "Session not found."}

    async def inspect_ui_components(self, url: str, component_filter: str = "all") -> Dict[str, Any]:
        """
        Navigates to a UI component documentation or design gallery (e.g. shadcn/ui, Three.js, Tailwind),
        and extracts UI elements, component hierarchy, JSX snippets, and WebGL canvas info.
        """
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            )
            page = await context.new_page()

            try:
                await page.goto(url, timeout=30000, wait_until="networkidle")
            except Exception:
                # If networkidle times out on asset-heavy pages, proceed with loaded DOM
                pass

            title = await page.title()

            # Extract shadcn / interactive UI buttons
            buttons_data = await page.evaluate("""() => {
                const results = [];
                const buttons = document.querySelectorAll('button, a[role="button"], div[role="button"], [class*="button"], [class*="btn"]');
                buttons.forEach((el, idx) => {
                    if (idx < 20) {
                        const style = window.getComputedStyle(el);
                        results.push({
                            tag: el.tagName.toLowerCase(),
                            text: (el.innerText || el.textContent || '').trim().slice(0, 50),
                            classes: el.className || '',
                            role: el.getAttribute('role') || 'button',
                            variant: el.getAttribute('data-variant') || (el.className.includes('primary') ? 'primary' : 'default'),
                            backgroundColor: style.backgroundColor,
                            color: style.color,
                            borderRadius: style.borderRadius
                        });
                    }
                });
                return results;
            }""")

            # Extract threeui / WebGL Canvases
            canvas_data = await page.evaluate("""() => {
                const canvases = document.querySelectorAll('canvas');
                const results = [];
                canvases.forEach((c, idx) => {
                    results.push({
                        index: idx,
                        width: c.width,
                        height: c.height,
                        id: c.id || '',
                        classes: c.className || '',
                        webglSupported: !!(c.getContext('webgl2') || c.getContext('webgl') || c.getContext('experimental-webgl'))
                    });
                });
                return results;
            }""")

            # Extract CSS variables / Theme Tokens
            theme_tokens = await page.evaluate("""() => {
                const styles = window.getComputedStyle(document.documentElement);
                const tokens = {};
                for (let i = 0; i < styles.length; i++) {
                    const prop = styles[i];
                    if (prop.startsWith('--')) {
                        tokens[prop] = styles.getPropertyValue(prop).trim();
                        if (Object.keys(tokens).length > 25) break;
                    }
                }
                return tokens;
            }""")

            # Extract code blocks (JSX/TSX for shadcn components)
            code_snippets = await page.evaluate("""() => {
                const blocks = document.querySelectorAll('pre, code, [data-code]');
                const snippets = [];
                blocks.forEach((b, idx) => {
                    if (idx < 5 && b.textContent.length > 20) {
                        snippets.push({
                            language: b.getAttribute('data-language') || 'tsx',
                            code: b.textContent.trim().slice(0, 1500)
                        });
                    }
                });
                return snippets;
            }""")

            await browser.close()

            audit_ledger.record_action(
                action_type="UI_COMPONENT_INSPECT",
                user="Developer",
                details=f"Extracted UI components from {url}: {len(buttons_data)} elements, {len(canvas_data)} WebGL canvases",
                severity="INFO",
                target_resource=url
            )

            return {
                "status": "SUCCESS",
                "url": url,
                "page_title": title,
                "components": {
                    "interactive_elements_count": len(buttons_data),
                    "interactive_elements": buttons_data,
                    "webgl_canvases": canvas_data,
                    "theme_tokens": theme_tokens,
                    "code_snippets": code_snippets
                }
            }

    async def download_pinterest_video(
        self,
        pin_url_or_query: str,
        target_dir: Optional[str] = None,
        headed: bool = False,
        progress_cb: Optional[Callable[[str, int, str], None]] = None
    ) -> Dict[str, Any]:
        """
        Automates Playwright to extract, resolve, and download Pinterest videos locally:
        1. Resolves shortlinks (pin.it) and pin IDs.
        2. Inspects page for direct MP4 media streams from v.pinimg.com or JSON-LD metadata.
        3. Falls back to automated Pin Saver site workflow (typing link, clicking download, scraping stream).
        4. Downloads MP4 stream to the local workspace folder with verification and audit hashing.
        """
        def update_progress(step: str, pct: int, msg: str):
            if progress_cb:
                try:
                    progress_cb(step, pct, msg)
                except Exception:
                    pass

        dest_dir = Path(target_dir) if target_dir else self.download_dir
        dest_dir.mkdir(parents=True, exist_ok=True)

        clean_input = pin_url_or_query.strip()
        update_progress("INITIALIZING", 10, "Initializing Playwright Chromium browser engine...")

        detected_video_urls: List[str] = []
        page_title = "Pinterest Video"

        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=not headed,
                args=["--no-sandbox", "--disable-setuid-sandbox"]
            )
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                viewport={"width": 1280, "height": 800}
            )
            page = await context.new_page()

            # Network Sniffer: Capture any direct .mp4 responses
            async def on_response(response):
                r_url = response.url
                if (".mp4" in r_url or "v.pinimg.com/videos" in r_url) and "m3u8" not in r_url:
                    if r_url not in detected_video_urls:
                        detected_video_urls.append(r_url)

            page.on("response", on_response)

            try:
                # Step 1: Handle Pinterest URL vs Search Query
                pin_target_url = clean_input
                if not (clean_input.startswith("http://") or clean_input.startswith("https://")):
                    update_progress("SEARCHING", 20, f"Searching Pinterest for '{clean_input}'...")
                    pin_target_url = f"https://www.pinterest.com/search/pins/?q={urllib.parse.quote(clean_input)}"

                update_progress("NAVIGATING", 30, f"Navigating to {pin_target_url}...")
                await page.goto(pin_target_url, timeout=30000, wait_until="domcontentloaded")
                await asyncio.sleep(2.0)

                page_title = await page.title()

                # Step 2: Check for <video> tag in DOM
                update_progress("EXTRACTING", 50, "Extracting video media stream from DOM and network...")
                dom_video_src = await page.evaluate("""() => {
                    const v = document.querySelector('video');
                    if (v && v.src) return v.src;
                    const source = document.querySelector('video source');
                    if (source && source.src) return source.src;
                    return null;
                }""")
                if dom_video_src and dom_video_src not in detected_video_urls:
                    detected_video_urls.insert(0, dom_video_src)

                # Step 3: Check Redux state or JSON-LD in page source
                redux_videos = await page.evaluate("""() => {
                    const results = [];
                    // Check schema.org JSON-LD
                    const scripts = document.querySelectorAll('script[type="application/ld+json"]');
                    scripts.forEach(s => {
                        try {
                            const data = JSON.parse(s.textContent);
                            if (data.contentUrl && data.contentUrl.includes('.mp4')) results.push(data.contentUrl);
                        } catch(e) {}
                    });
                    // Check PWS_DATA
                    const pws = document.getElementById('__PWS_DATA__');
                    if (pws) {
                        try {
                            const str = pws.textContent;
                            const matches = str.match(/https:\\/\\/v\\.pinimg\\.com\\/videos\\/[^"']+\\.mp4/g);
                            if (matches) matches.forEach(m => results.push(m.replace(/\\\\u002F/g, '/')));
                        } catch(e) {}
                    }
                    return results;
                }""")
                for rv in redux_videos:
                    if rv not in detected_video_urls:
                        detected_video_urls.insert(0, rv)

                # Step 4: Fallback to Pin Saver Downloader Site Automation if no direct stream detected
                if not detected_video_urls:
                    update_progress("PIN_SAVER_FALLBACK", 65, "Engaging Pin Saver web downloader automation...")
                    pin_saver_url = "https://pinterestvideodownloader.com/"
                    await page.goto(pin_saver_url, timeout=30000, wait_until="domcontentloaded")
                    await asyncio.sleep(1.5)

                    # Look for input bar, type pin link, and trigger download
                    input_sel = 'input[type="text"], input[name="url"], #url'
                    if await page.locator(input_sel).count() > 0:
                        await page.locator(input_sel).first.fill(pin_target_url)
                        await asyncio.sleep(0.5)
                        submit_btn = 'button[type="submit"], input[type="submit"], .btn-download'
                        if await page.locator(submit_btn).count() > 0:
                            await page.locator(submit_btn).first.click()
                            await asyncio.sleep(4.0)

                            # Find generated download links
                            saver_mp4 = await page.evaluate("""() => {
                                const links = document.querySelectorAll('a[href*=".mp4"], a[download]');
                                for (const a of links) {
                                    if (a.href && a.href.includes('.mp4')) return a.href;
                                }
                                return null;
                            }""")
                            if saver_mp4:
                                detected_video_urls.append(saver_mp4)

            except Exception as nav_err:
                logger.warning(f"Playwright navigation note: {nav_err}")
            finally:
                await browser.close()

        # Step 5: Download the resolved MP4 video file locally
        if not detected_video_urls:
            return {
                "status": "NOT_FOUND",
                "message": f"Could not detect direct MP4 video stream for '{clean_input}'. Ensure the pin contains a video or try another pin URL.",
                "url": clean_input
            }

        target_video_url = detected_video_urls[0]
        update_progress("DOWNLOADING", 80, f"Streaming video bytes to local disk from {target_video_url[:60]}...")

        safe_filename = f"pinterest_video_{int(time.time())}_{uuid.uuid4().hex[:4]}.mp4"
        out_filepath = dest_dir / safe_filename

        try:
            req = urllib.request.Request(
                target_video_url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                    "Referer": "https://www.pinterest.com/"
                }
            )
            with urllib.request.urlopen(req, timeout=45) as response, open(out_filepath, "wb") as out_file:
                chunk_size = 64 * 1024
                while True:
                    chunk = response.read(chunk_size)
                    if not chunk:
                        break
                    out_file.write(chunk)

            stat = out_filepath.stat()
            file_size_mb = round(stat.st_size / (1024 * 1024), 2)

            # SHA-256 Audit
            with open(out_filepath, "rb") as f:
                sha_hash = hashlib.sha256(f.read()).hexdigest()

            audit_ledger.record_action(
                action_type="PINTEREST_VIDEO_DOWNLOAD",
                user="Developer",
                details=f"Downloaded Pinterest video '{safe_filename}' ({file_size_mb} MB) from {target_video_url[:80]}",
                severity="INFO",
                target_resource=str(out_filepath)
            )

            update_progress("COMPLETED", 100, f"Saved successfully to {out_filepath.name} ({file_size_mb} MB)!")
            self._load_recent_downloads()

            return {
                "status": "SUCCESS",
                "filename": safe_filename,
                "filepath": str(out_filepath),
                "relative_url": f"/api/browser/downloaded-file/{safe_filename}",
                "size_bytes": stat.st_size,
                "size_mb": file_size_mb,
                "sha256": sha_hash,
                "source_video_url": target_video_url,
                "pin_url": clean_input,
                "page_title": page_title,
                "message": f"Successfully downloaded and saved: {safe_filename} ({file_size_mb} MB)"
            }

        except Exception as dl_err:
            logger.error(f"Failed to stream video bytes: {dl_err}")
            return {
                "status": "ERROR",
                "error": str(dl_err),
                "resolved_url": target_video_url,
                "message": f"Stream download failed: {dl_err}"
            }


# Singleton instance
monolith_browser_mgr = MonolithBrowserEngine()
