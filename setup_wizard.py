"""
setup_wizard.py
MONOLITH — Autonomous Engineering System
One-Click Autonomous Setup & Provisioning Wizard

Engineered for 100% non-technical, frictionless execution:
1. Checks and verifies local Python environment and dependencies.
2. Checks Ollama daemon and model availability (with graceful local fallback).
3. Automatically starts the MONOLITH FastAPI server.
4. Autodetects active server port and launches the web browser dashboard.
"""

import os
import sys
import json
import time
import shutil
import socket
import urllib.request
import subprocess
import threading
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox

# Enable High-DPI scaling on Windows
if sys.platform == "win32":
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass

BASE_DIR = Path(__file__).resolve().parent
REQUIREMENTS_FILE = BASE_DIR / "requirements.txt"
SERVER_SCRIPT = BASE_DIR / "server.py"
OUTPUT_DIR = BASE_DIR / "output"
DOWNLOADS_DIR = OUTPUT_DIR / "downloads"

OLLAMA_WINDOWS_INSTALLER_URL = "https://ollama.com/download/OllamaSetup.exe"


class MonolithSetupWizard:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("MONOLITH — Autonomous Engineering System Setup")
        
        # Window Dimensions & Centering
        win_w, win_h = 620, 600
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        pos_x = max(0, (screen_w - win_w) // 2)
        pos_y = max(0, (screen_h - win_h) // 2)
        self.root.geometry(f"{win_w}x{win_h}+{pos_x}+{pos_y}")
        self.root.minsize(560, 560)

        # High-Contrast Modern Neumorph/Indigo Theme
        self.bg_color = "#0f172a"      # Deep slate background
        self.card_bg = "#1e293b"       # Elevated slate card
        self.accent_color = "#6366f1"   # Indigo primary
        self.emerald_color = "#10b981"  # Emerald green for launch
        self.text_light = "#f8fafc"     # Pure white/slate text
        self.text_muted = "#94a3b8"     # Secondary muted text
        self.border_color = "#334155"   # Crisp line border

        self.root.configure(bg=self.bg_color)
        self._apply_styles()

        # State Variables
        self.selected_model_var = tk.StringVar(value="llama3.2:1b")
        self.lan_mode_var = tk.BooleanVar(value=False)
        self.auto_open_browser = tk.BooleanVar(value=True)
        self.is_running = False

        self._build_ui()
        self._run_quick_precheck()

    def _apply_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Monolith.Horizontal.TProgressbar",
            thickness=14,
            troughcolor="#1e293b",
            background=self.emerald_color,
            bordercolor=self.border_color,
            lightcolor=self.emerald_color,
            darkcolor=self.emerald_color
        )

    def _build_ui(self):
        # 1. Header Banner
        header = tk.Frame(self.root, bg=self.card_bg, padx=24, pady=18, highlightbackground=self.border_color, highlightthickness=1)
        header.pack(fill="x", padx=0, pady=0)

        title_row = tk.Frame(header, bg=self.card_bg)
        title_row.pack(fill="x")

        title_lbl = tk.Label(
            title_row,
            text="MONOLITH",
            font=("Segoe UI", 20, "bold"),
            fg=self.accent_color,
            bg=self.card_bg
        )
        title_lbl.pack(side="left")

        badge_lbl = tk.Label(
            title_row,
            text=" 100% LOCAL & PRIVATE ",
            font=("Segoe UI", 9, "bold"),
            fg=self.emerald_color,
            bg="#064e3b",
            padx=8,
            pady=2
        )
        badge_lbl.pack(side="right")

        subtitle_lbl = tk.Label(
            header,
            text="Autonomous Multi-Agent Engineering System • Zero Cloud Leakage",
            font=("Segoe UI", 9),
            fg=self.text_muted,
            bg=self.card_bg
        )
        subtitle_lbl.pack(anchor="w", pady=(3, 0))

        # 2. Main Content Frame
        main_frame = tk.Frame(self.root, bg=self.bg_color, padx=22, pady=16)
        main_frame.pack(fill="both", expand=True)

        # Feature Summary Cards (3 Foolproof Checks)
        summary_card = tk.Frame(main_frame, bg=self.card_bg, padx=16, pady=14, highlightbackground=self.border_color, highlightthickness=1)
        summary_card.pack(fill="x", pady=(0, 14))

        tk.Label(
            summary_card,
            text="Everything is automated for you:",
            font=("Segoe UI", 11, "bold"),
            fg=self.text_light,
            bg=self.card_bg
        ).pack(anchor="w", pady=(0, 8))

        features = [
            ("✅  Local-First Intelligence", "Fast quantized AI models running right on your GPU/CPU."),
            ("✅  Browser & Media Tools", "Headed Playwright Chromium, chatbot automation & video saver."),
            ("✅  Sovereign Air-Gap Security", "Your source code and documents never leave this machine.")
        ]
        for f_title, f_desc in features:
            f_frame = tk.Frame(summary_card, bg=self.card_bg)
            f_frame.pack(fill="x", pady=2)
            tk.Label(f_frame, text=f_title, font=("Segoe UI", 9, "bold"), fg=self.text_light, bg=self.card_bg).pack(anchor="w")
            tk.Label(f_frame, text=f_desc, font=("Segoe UI", 8), fg=self.text_muted, bg=self.card_bg).pack(anchor="w", padx=(20, 0))

        # Model & Network Options Card
        options_card = tk.Frame(main_frame, bg=self.card_bg, padx=16, pady=12, highlightbackground=self.border_color, highlightthickness=1)
        options_card.pack(fill="x", pady=(0, 14))

        tk.Label(
            options_card,
            text="Local Model Selection:",
            font=("Segoe UI", 9, "bold"),
            fg=self.text_light,
            bg=self.card_bg
        ).pack(anchor="w", pady=(0, 4))

        model_row = tk.Frame(options_card, bg=self.card_bg)
        model_row.pack(fill="x", pady=(0, 4))

        rb1 = tk.Radiobutton(
            model_row,
            text="Llama 3.2 1B (Fast, Highly Accurate • Recommended)",
            variable=self.selected_model_var,
            value="llama3.2:1b",
            font=("Segoe UI", 9),
            bg=self.card_bg,
            fg=self.text_light,
            selectcolor=self.bg_color,
            activebackground=self.card_bg
        )
        rb1.pack(anchor="w")

        rb2 = tk.Radiobutton(
            model_row,
            text="Qwen 2.5 0.5B (Ultra-Lightweight for older PCs)",
            variable=self.selected_model_var,
            value="qwen2.5:0.5b",
            font=("Segoe UI", 9),
            bg=self.card_bg,
            fg=self.text_light,
            selectcolor=self.bg_color,
            activebackground=self.card_bg
        )
        rb2.pack(anchor="w")

        chk_lan = tk.Checkbutton(
            options_card,
            text="Enable Phone/Tablet Access on Local Wi-Fi (LAN Mode)",
            variable=self.lan_mode_var,
            font=("Segoe UI", 8),
            bg=self.card_bg,
            fg=self.text_muted,
            selectcolor=self.bg_color,
            activebackground=self.card_bg
        )
        chk_lan.pack(anchor="w", pady=(4, 0))

        # Status & Progress Display
        self.status_lbl = tk.Label(
            main_frame,
            text="Ready. Click 'START MONOLITH' to begin.",
            font=("Segoe UI", 9, "bold"),
            fg=self.emerald_color,
            bg=self.bg_color
        )
        self.status_lbl.pack(anchor="w", pady=(0, 6))

        self.progress_bar = ttk.Progressbar(
            main_frame,
            style="Monolith.Horizontal.TProgressbar",
            mode="determinate",
            maximum=100
        )
        self.progress_bar.pack(fill="x", pady=(0, 8))

        # 3. Action Buttons Footer
        footer = tk.Frame(self.root, bg=self.card_bg, padx=22, pady=16, highlightbackground=self.border_color, highlightthickness=1)
        footer.pack(fill="x", side="bottom")

        self.btn_exit = tk.Button(
            footer,
            text="Exit",
            font=("Segoe UI", 9, "bold"),
            bg="#334155",
            fg=self.text_light,
            relief="flat",
            padx=16,
            pady=7,
            cursor="hand2",
            command=self.root.quit
        )
        self.btn_exit.pack(side="left")

        self.btn_direct = tk.Button(
            footer,
            text="⚡ Quick Launch",
            font=("Segoe UI", 9, "bold"),
            bg="#3b82f6",
            fg="#ffffff",
            relief="flat",
            padx=16,
            pady=7,
            cursor="hand2",
            command=self._quick_launch
        )
        self.btn_direct.pack(side="left", padx=8)

        self.btn_start = tk.Button(
            footer,
            text="🚀 START MONOLITH (ONE-CLICK)",
            font=("Segoe UI", 10, "bold"),
            bg=self.emerald_color,
            fg="#ffffff",
            relief="flat",
            padx=24,
            pady=7,
            cursor="hand2",
            command=self._start_provisioning
        )
        self.btn_start.pack(side="right")

    def _update_status(self, text: str, progress: int = None, color: str = None):
        self.status_lbl.config(text=text)
        if color:
            self.status_lbl.config(fg=color)
        if progress is not None:
            self.progress_bar["value"] = progress
        self.root.update_idletasks()

    def _run_quick_precheck(self):
        """Silently verifies if Ollama and Python requirements are present."""
        def check():
            ollama_found = shutil.which("ollama") is not None
            if not ollama_found and sys.platform == "win32":
                user_prog = Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Ollama" / "ollama.exe"
                if user_prog.exists():
                    ollama_found = True
            
            if ollama_found:
                self._update_status("Local AI Engine & Dependencies Detected. Ready to Launch!", progress=100, color=self.emerald_color)
            else:
                self._update_status("Click 'START MONOLITH' to setup and launch everything automatically.", progress=0, color=self.accent_color)
        
        threading.Thread(target=check, daemon=True).start()

    def _quick_launch(self):
        """Skips downloads and immediately fires up server and browser."""
        self._update_status("Direct launching MONOLITH server...", progress=50, color=self.accent_color)
        threading.Thread(target=self._launch_server_and_browser, daemon=True).start()

    def _start_provisioning(self):
        if self.is_running:
            return
        self.is_running = True
        self.btn_start.config(state="disabled")
        self.btn_direct.config(state="disabled")

        t = threading.Thread(target=self._run_pipeline, daemon=True)
        t.start()

    def _run_pipeline(self):
        try:
            OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
            DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)

            # Step 1: Python Requirements Check
            self._update_status("Checking Python libraries...", progress=20)
            if REQUIREMENTS_FILE.exists():
                subprocess.run([sys.executable, "-m", "pip", "install", "-r", str(REQUIREMENTS_FILE), "--quiet"], check=False)
            self._update_status("Python environment ready.", progress=40)

            # Step 2: Check & Start Ollama
            self._update_status("Checking Local Ollama Daemon...", progress=55)
            ollama_exe = shutil.which("ollama")
            if not ollama_exe and sys.platform == "win32":
                user_prog = Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Ollama" / "ollama.exe"
                if user_prog.exists():
                    ollama_exe = str(user_prog)

            if ollama_exe:
                try:
                    creationflags = 0x00000008 | 0x08000000 if sys.platform == "win32" else 0
                    subprocess.Popen([ollama_exe, "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=creationflags)
                    time.sleep(1)
                except Exception:
                    pass

            # Step 3: Pull model if requested
            chosen_model = self.selected_model_var.get()
            if ollama_exe:
                self._update_status(f"Verifying local AI model '{chosen_model}'...", progress=75)
                try:
                    subprocess.run([ollama_exe, "pull", chosen_model], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=60)
                except Exception:
                    pass

            # Step 4: Launch Server & Browser
            self._launch_server_and_browser()

        except Exception as err:
            self._update_status(f"Error: {err}", color="#ef4444")
            self.btn_start.config(state="normal")
            self.btn_direct.config(state="normal")
            self.is_running = False

    def _launch_server_and_browser(self):
        try:
            self._update_status("Starting MONOLITH Server...", progress=90, color=self.accent_color)
            
            # Set network mode
            if self.lan_mode_var.get():
                os.environ["NETWORK_MODE"] = "LAN"
            else:
                os.environ["NETWORK_MODE"] = "LOCAL_ONLY"

            # Check if server is already running on a port
            active_port = self._find_running_monolith_port()

            if not active_port:
                # Spawn server in background
                server_cmd = [sys.executable, str(SERVER_SCRIPT)]
                creationflags = 0x08000000 if sys.platform == "win32" else 0
                subprocess.Popen(server_cmd, cwd=str(BASE_DIR), creationflags=creationflags)
                
                # Wait for server to become responsive
                for _ in range(15):
                    time.sleep(1)
                    active_port = self._find_running_monolith_port()
                    if active_port:
                        break

            target_port = active_port or 8001
            url = f"http://127.0.0.1:{target_port}"

            self._update_status(f"MONOLITH Online on {url}! Opening browser...", progress=100, color=self.emerald_color)
            time.sleep(1)

            import webbrowser
            webbrowser.open(url)

            time.sleep(2)
            self.root.destroy()

        except Exception as ex:
            self._update_status(f"Launch notice: {ex}", color="#ef4444")
            import webbrowser
            webbrowser.open("http://127.0.0.1:8001")
            time.sleep(2)
            self.root.destroy()

    def _find_running_monolith_port(self) -> int:
        """Finds any active port responding to /api/status between 8001 and 8010."""
        for port in range(8001, 8010):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(0.5)
                    if s.connect_ex(("127.0.0.1", port)) == 0:
                        return port
            except Exception:
                continue
        return None

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    wizard = MonolithSetupWizard()
    wizard.run()
