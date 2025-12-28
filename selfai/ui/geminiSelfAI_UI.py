import json
import os
import sys
import threading
import time
import re
from datetime import datetime
from itertools import cycle
from typing import Optional, List, Dict, Any

# ===============================================================================
# SELF.AI UI COLLECTION
# Available Themes:
# 1. TACTICAL (Default) - High tech, tabular, military HUD
# 2. STARK              - Minimalist bracket notation, instant info
# 3. NEON               - Cyberpunk, emojis, frames
# 4. ZEN                - Monochrome, ample whitespace, no distractions
# 5. OVERLORD           - Max info, timestamps, PIDs, trace-style logging
# ===============================================================================

class BaseUI:
    """Shared functionality for all UIs."""
    
    def __init__(self):
        self._spinner_thread: Optional[threading.Thread] = None
        self._spinner_running = False
        self._spinner_message = ""
        self._yolo_mode = False
        self._enable_color = self._detect_color_support()
        self._pid = os.getpid()

    @staticmethod
    def _detect_color_support() -> bool:
        return sys.stdout.isatty() or os.name == "nt"

    def clear(self) -> None:
        os.system("cls" if os.name == "nt" else "clear")

    def _fmt(self, text: str, color: str) -> str:
        if not self._enable_color: return text
        return f"{color}{text}\033[0m"

    def _clean_text(self, text: str) -> str:
        """Removes common emojis and clutter for cleaner UI."""
        clean = text.replace("⚠️", "").replace("✅", "").replace("ℹ️", "").replace("❌", "")
        clean = clean.replace("🚀", "").replace("📦", "").replace("🤖", "")
        return re.sub(r'\s+', ' ', clean).strip()

    def confirm(self, message: str, default_yes: bool = False) -> bool:
        if self._yolo_mode: return True
        suffix = "Y/n" if default_yes else "y/N"
        res = input(f"{message} [{suffix}]: ").strip().lower()
        if not res: return default_yes
        return res in ("y", "yes")

    def enable_yolo_mode(self) -> None:
        self._yolo_mode = True
        print(f"\n\033[91m!!! SAFETY OVERRIDE ENGAGED (YOLO) !!!\033[0m")
        
    def disable_yolo_mode(self) -> None:
        self._yolo_mode = False
        print("Safety Protocols Restored.")

    def is_yolo_mode(self) -> bool:
        return self._yolo_mode
    
    def colorize(self, text: str, color: str) -> str:
        c_map = {
            "cyan": "\033[96m", "magenta": "\033[95m", "green": "\033[92m", 
            "yellow": "\033[93m", "red": "\033[91m", "blue": "\033[94m", 
            "bold": "\033[1m", "reset": "\033[0m"
        }
        return f"{c_map.get(color.lower(), '')}{text}\033[0m"

# ===============================================================================
# 1. TACTICAL UI (The "Soldier" Choice)
# ===============================================================================

class TacticalUI(BaseUI):
    C_FRAME = "\033[96m"    # Cyan
    C_TEXT = "\033[97m"     # White
    C_DIM = "\033[90m"      # Grey
    C_CMD = "\033[95m"      # Magenta
    C_OK = "\033[92m"       # Green
    C_WARN = "\033[93m"     # Yellow
    C_ERR = "\033[91m"      # Red
    RESET = "\033[0m"
    BOLD = "\033[1m"
    
    SPINNER_FRAMES = ["⣾", "⣽", "⣻", "⢿", "⡿", "⣟", "⣯", "⣷"]

    def banner(self) -> None:
        self.clear()
        ts = datetime.now().strftime("%H:%M:%S")
        os_name = sys.platform.upper()
        print(f"{self.C_FRAME}┌── SYSTEM READY ─────────────────────────────┐{self.RESET}")
        print(f"{self.C_FRAME}│{self.RESET} {self.BOLD}SELF.AI TACTICAL{self.RESET} | {os_name:<10} | {ts:<8} {self.C_FRAME}│{self.RESET}")
        print(f"{self.C_FRAME}└─────────────────────────────────────────────┘{self.RESET}")
        print()

    def section_header(self, title: str, icon_key: str = ""):
        print(f"\n{self.C_FRAME}:: {title.upper()} ::{self.RESET}")

    def status(self, message: str, level: str = "info") -> None:
        markers = {"info": "ℹ", "success": "✔", "warning": "⚠", "error": "✖"}
        c_map = {"info": self.C_TEXT, "success": self.C_OK, "warning": self.C_WARN, "error": self.C_ERR}
        mark = markers.get(level, "ℹ")
        col = c_map.get(level, self.C_TEXT)
        clean_msg = self._clean_text(message)
        print(f"{self.C_FRAME}{mark}{self.RESET} {self._fmt(clean_msg, col)}")

    def start_spinner(self, message: str) -> None:
        self.stop_spinner()
        self._spinner_running = True
        self._spinner_message = message
        def spin():
            frames = cycle(self.SPINNER_FRAMES)
            while self._spinner_running:
                print(f"\r{self.C_FRAME}{next(frames)}{self.RESET} {self.C_DIM}{self._spinner_message}{self.RESET}", end="")
                time.sleep(0.1)
            print("\r" + " " * (len(self._spinner_message) + 5) + "\r", end="")
        self._spinner_thread = threading.Thread(target=spin, daemon=True)
        self._spinner_thread.start()

    def stop_spinner(self, final_message: Optional[str] = None, level: str = "success") -> None:
        if not self._spinner_running: return
        self._spinner_running = False
        if self._spinner_thread: self._spinner_thread.join()
        print("\r", end="")
        if final_message: self.status(final_message, level)
        self._spinner_thread = None

    def stream_prefix(self, backend_label: Optional[str]) -> None:
        print()
        src = backend_label if backend_label else "CORE"
        print(f"{self.C_FRAME}[{src}]{self.RESET} >> ", end="", flush=True)

    def streaming_chunk(self, chunk: str) -> None:
        print(chunk, end="", flush=True)

    def show_think_tags(self, think_contents: List[str]) -> None:
        if not think_contents: return
        for think in think_contents:
            print(f"\n{self.C_DIM}┌─ internal_monologue ────────────────────────{self.RESET}")
            for line in think.strip().split('\n'):
                print(f"{self.C_DIM}│ {line}{self.RESET}")
            print(f"{self.C_DIM}└──────────────────────────────────────────────{self.RESET}")

    def show_plan(self, plan: dict) -> None:
        self.section_header("EXECUTION SEQUENCE")
        for line in json.dumps(plan, indent=2).split('\n'):
            print(f" {self.C_TEXT}{line}{self.RESET}")

    def list_agents(self, agents, active_key: Optional[str] = None) -> None:
        try: l = list(agents.values())
        except: l = list(agents)
        self.section_header("AGENTS")
        for ag in l:
            active = f" {self.C_OK}[ACTIVE]{self.RESET}" if (active_key and ag.key == active_key) else ""
            print(f" {self.C_CMD}• {ag.display_name:<15}{self.RESET} {active}")

    def show_available_tools(self, tools: List[Dict]) -> None:
        self.section_header("TOOLS")
        for t in tools:
            desc = t["description"].split(".")[0][:50]
            print(f"  {self.C_CMD}{t['name']:<25}{self.RESET} {self.C_DIM}{desc}{self.RESET}")

    def confirm(self, message: str, default_yes: bool = False) -> bool:
        if self._yolo_mode: return True
        prompt = f"{self.C_WARN}? {message}{self.RESET} "
        choice = "Y/n" if default_yes else "y/N"
        res = input(f"{prompt}[{choice}]: ").strip().lower()
        return res in ("y", "yes") if res else default_yes

    def confirm_plan(self) -> bool: return self.confirm("Authorize Plan?", True)
    def confirm_execution(self) -> bool: return self.confirm("Execute?", True)

    def choose_option(self, prompt: str, options: List[str], default_index: Optional[int] = None) -> int:
        if self._yolo_mode: return default_index if default_index is not None else 0
        print()
        for i, o in enumerate(options, 1):
            print(f" {self.C_FRAME}{i}.{self.RESET} {o}")
        
        default_display = f"[{default_index+1}]" if default_index is not None else ""
        res = input(f"\n{self.C_WARN}?? {prompt}{self.RESET} {default_display}: ").strip()
        
        if not res: return default_index if default_index is not None else 0
        if res.isdigit():
            val = int(res) - 1
            if 0 <= val < len(options): return val
        return self.choose_option(prompt, options, default_index)
        
    def typing_animation(self, text: str, delay: float = 0.01) -> None:
        for char in text:
            print(char, end="", flush=True)
            time.sleep(delay)
        print()

# ===============================================================================
# 2. STARK UI (The "Minimalist" Choice)
# ===============================================================================

class StarkUI(BaseUI):
    C_SYS = "\033[96m"   # Cyan
    C_TXT = "\033[97m"   # White
    C_SUB = "\033[90m"   # Dim
    C_ALT = "\033[93m"   # Amber
    RESET = "\033[0m"
    SPINNER_FRAMES = ["|", "/", "-", "\"]

    def banner(self) -> None:
        self.clear()
        print(f"{self.C_SYS}// SELF.AI INTERFACE V2{self.RESET}")
        print(f"{self.C_SUB}>> INITIALIZING...{self.RESET}\n")

    def section_header(self, title: str, icon_key: str = ""):
        print(f"\n{self.C_SYS}[{title.upper()}]{self.RESET}")

    def status(self, message: str, level: str = "info") -> None:
        tag = level.upper()[:4]
        c_tag = self.C_SYS
        if level == "success": c_tag = "\033[92m"
        if level == "warning": c_tag = self.C_ALT
        if level == "error": c_tag = "\033[91m"
        clean = self._clean_text(message)
        print(f"[{self._fmt(tag, c_tag)}] {self.C_TXT}{clean}{self.RESET}")

    def start_spinner(self, message: str) -> None:
        self.stop_spinner()
        self._spinner_running = True
        self._spinner_message = message
        def spin():
            frames = cycle(self.SPINNER_FRAMES)
            while self._spinner_running:
                print(f"\r{self.C_SYS}{next(frames)}{self.RESET} {self.C_SUB}{self._spinner_message}{self.RESET}", end="")
                time.sleep(0.08)
            print("\r" + " " * (len(self._spinner_message) + 5) + "\r", end="")
        self._spinner_thread = threading.Thread(target=spin, daemon=True)
        self._spinner_thread.start()

    def stop_spinner(self, final_message: Optional[str] = None, level: str = "success") -> None:
        if not self._spinner_running: return
        self._spinner_running = False
        if self._spinner_thread: self._spinner_thread.join()
        print("\r", end="")
        if final_message: self.status(final_message, level)
        self._spinner_thread = None

    def stream_prefix(self, backend_label: Optional[str]) -> None:
        print()
        src = backend_label if backend_label else "AI"
        print(f"{self.C_SYS}{src}:{self.RESET} ", end="", flush=True)

    def streaming_chunk(self, chunk: str) -> None:
        print(chunk, end="", flush=True)

    def show_think_tags(self, think_contents: List[str]) -> None:
        if not think_contents: return
        for think in think_contents:
            print(f"\n{self.C_SUB}>> reasoning_stream{self.RESET}")
            for line in think.strip().split('\n'):
                print(f"{self.C_SUB}   | {line}{self.RESET}")

    def show_plan(self, plan: dict) -> None:
        self.section_header("PLAN")
        print(json.dumps(plan, indent=2))

    def list_agents(self, agents, active_key: Optional[str] = None) -> None:
        try: l = list(agents.values())
        except: l = list(agents)
        self.section_header("AGENTS")
        for i, ag in enumerate(l, 1):
            act = "*" if (active_key and ag.key == active_key) else " "
            print(f" {i:02d} {act} {ag.display_name}")

    def show_available_tools(self, tools: List[Dict]) -> None:
        self.section_header("TOOLS")
        for t in tools:
            print(f" > {t['name']}")

    def confirm(self, message: str, default_yes: bool = False) -> bool:
        if self._yolo_mode: return True
        opt = "[Y/n]" if default_yes else "[y/N]"
        res = input(f"{self.C_ALT}? {message}{self.RESET} {self.C_SUB}{opt}{self.RESET} ").strip().lower()
        if not res: return default_yes
        return res in ("y", "yes")

    def confirm_plan(self) -> bool: return self.confirm("Authorize?", True)
    def confirm_execution(self) -> bool: return self.confirm("Start?", True)

    def choose_option(self, prompt: str, options: List[str], default_index: Optional[int] = None) -> int:
        if self._yolo_mode: return default_index if default_index is not None else 0
        print()
        for i, o in enumerate(options, 1):
            print(f" [{i}] {o}")
        
        default_display = f"[{default_index+1}]" if default_index is not None else ""
        res = input(f"\n{self.C_ALT}?? {prompt}{self.RESET} {default_display}: ").strip()
        
        if not res: return default_index if default_index is not None else 0
        if res.isdigit():
            val = int(res) - 1
            if 0 <= val < len(options): return val
        return self.choose_option(prompt, options, default_index)

    def typing_animation(self, text: str, delay: float = 0.01) -> None:
        print(text)

# ===============================================================================
# 3. NEON UI (The "Cyberpunk" Choice)
# ===============================================================================

class NeonUI(BaseUI):
    C_HEAD = "\033[1;95m"   # Bold Magenta
    C_SUB = "\033[1;94m"    # Bold Blue
    C_TXT = "\033[0m"       # Reset
    C_ACC = "\033[96m"      # Cyan
    SPINNER_FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

    def banner(self) -> None:
        self.clear()
        line = "\033[96m═" * 60 + "\033[0m"
        print(f"\033[95m╔{line}╗\033[0m")
        print(f"\033[95m║       🚀 SELF.AI CYBERPUNK EDITION 🚀       ║\033[0m")
        print(f"\033[95m╚{line}╝\033[0m\n")

    def section_header(self, title: str, icon_key: str = ""):
        print(f"\n{self.C_HEAD}══ {title} ══{self.C_TXT}")

    def status(self, message: str, level: str = "info") -> None:
        icons = {"info": "ℹ️ ", "success": "✅", "warning": "⚠️ ", "error": "❌"}
        print(f"{icons.get(level, '')} {message}")

    def start_spinner(self, message: str) -> None:
        self.stop_spinner()
        self._spinner_running = True
        self._spinner_message = message
        def spin():
            frames = cycle(self.SPINNER_FRAMES)
            while self._spinner_running:
                print(f"\r{self.C_ACC}{next(frames)}{self.C_TXT} {self._spinner_message}", end="")
                time.sleep(0.1)
            print("\r" + " " * (len(self._spinner_message) + 5) + "\r", end="")
        self._spinner_thread = threading.Thread(target=spin, daemon=True)
        self._spinner_thread.start()

    def stop_spinner(self, final_message: Optional[str] = None, level: str = "success") -> None:
        if not self._spinner_running: return
        self._spinner_running = False
        if self._spinner_thread: self._spinner_thread.join()
        print("\r", end="")
        if final_message: self.status(final_message, level)
        self._spinner_thread = None

    def stream_prefix(self, backend_label: Optional[str]) -> None:
        print(f"\n{self.C_HEAD}SelfAI [{backend_label or 'Bot'}]:{self.C_TXT} ", end="", flush=True)

    def streaming_chunk(self, chunk: str) -> None:
        print(chunk, end="", flush=True)

    def show_think_tags(self, think_contents: List[str]) -> None:
        if not think_contents: return
        for think in think_contents:
            print(f"\n{self.C_SUB}💭 Thinking:{self.C_TXT}")
            for line in think.strip().split('\n'):
                print(f"  \033[90m{line}\033[0m")

    def show_plan(self, plan: dict) -> None:
        self.section_header("📋 Execution Plan")
        print(json.dumps(plan, indent=2))

    def list_agents(self, agents, active_key: Optional[str] = None) -> None:
        try: l = list(agents.values())
        except: l = list(agents)
        self.section_header("🤖 Agents")
        for ag in l:
            mark = "➤" if (active_key and ag.key == active_key) else " "
            print(f" {mark} {self.C_ACC}{ag.display_name}{self.C_TXT}")

    def show_available_tools(self, tools: List[Dict]) -> None:
        self.section_header("📦 Toolkit")
        for t in tools:
            print(f" • {self.C_ACC}{t['name']}{self.C_TXT}: {t['description'][:60]}...")

    def confirm(self, message: str, default_yes: bool = False) -> bool:
        if self._yolo_mode: return True
        return super().confirm(message, default_yes)

    def confirm_plan(self) -> bool: return self.confirm("Run plan?", True)
    def confirm_execution(self) -> bool: return self.confirm("Engage?", True)

    def choose_option(self, prompt: str, options: List[str], default_index: Optional[int] = None) -> int:
        if self._yolo_mode: return default_index if default_index is not None else 0
        print()
        for i, o in enumerate(options, 1):
            print(f" {self.C_ACC}{i}.{self.C_TXT} {o}")
        
        default_display = f"[{default_index+1}]" if default_index is not None else ""
        res = input(f"\n{self.C_HEAD}❓ {prompt}{self.C_TXT} {default_display}: ").strip()
        
        if not res: return default_index if default_index is not None else 0
        if res.isdigit():
            val = int(res) - 1
            if 0 <= val < len(options): return val
        return self.choose_option(prompt, options, default_index)

    def typing_animation(self, text: str, delay: float = 0.02) -> None:
        for char in text:
            print(char, end="", flush=True)
            time.sleep(delay)
        print()

# ===============================================================================
# 4. ZEN UI (The "Monochrome" Choice)
# ===============================================================================

class ZenUI(BaseUI):
    C_FOCUS = "\033[97m"  # Bright White
    C_SUB = "\033[90m"    # Dark Grey
    RESET = "\033[0m"
    
    SPINNER_FRAMES = [" .  ", "  . ", "   ."] # Calm breathing

    def banner(self) -> None:
        self.clear()
        print(f"\n   s e l f . a i   \n")

    def section_header(self, title: str, icon_key: str = ""):
        print(f"\n   --- {title.lower()} ---")

    def status(self, message: str, level: str = "info") -> None:
        clean = self._clean_text(message)
        marker = "*"
        if level == "success": marker = "+"
        if level == "warning": marker = "!"
        if level == "error": marker = "x"
        print(f" {marker} {clean}")

    def start_spinner(self, message: str) -> None:
        self.stop_spinner()
        self._spinner_running = True
        self._spinner_message = message
        def spin():
            frames = cycle(self.SPINNER_FRAMES)
            while self._spinner_running:
                print(f"\r{self.C_SUB}{next(frames)} {self._spinner_message}{self.RESET}", end="")
                time.sleep(0.2) # Slower breathing
            print("\r" + " " * (len(self._spinner_message) + 10) + "\r", end="")
        self._spinner_thread = threading.Thread(target=spin, daemon=True)
        self._spinner_thread.start()

    def stop_spinner(self, final_message: Optional[str] = None, level: str = "success") -> None:
        if not self._spinner_running: return
        self._spinner_running = False
        if self._spinner_thread: self._spinner_thread.join()
        print("\r", end="")
        if final_message: self.status(final_message, level)
        self._spinner_thread = None

    def stream_prefix(self, backend_label: Optional[str]) -> None:
        print()
        print(f" > ", end="", flush=True)

    def streaming_chunk(self, chunk: str) -> None:
        print(chunk, end="", flush=True)

    def show_think_tags(self, think_contents: List[str]) -> None:
        if not think_contents: return
        for think in think_contents:
            print()
            for line in think.strip().split('\n'):
                print(f"   {self.C_SUB}{line}{self.RESET}")

    def show_plan(self, plan: dict) -> None:
        self.section_header("plan")
        print(json.dumps(plan, indent=2))

    def list_agents(self, agents, active_key: Optional[str] = None) -> None:
        try: l = list(agents.values())
        except: l = list(agents)
        self.section_header("agents")
        for ag in l:
            act = "(active)" if (active_key and ag.key == active_key) else ""
            print(f"   {ag.display_name.lower()} {act}")

    def show_available_tools(self, tools: List[Dict]) -> None:
        self.section_header("tools")
        for t in tools:
            print(f"   {t['name']}")

    def confirm(self, message: str, default_yes: bool = False) -> bool:
        if self._yolo_mode: return True
        return super().confirm(message.lower(), default_yes)

    def confirm_plan(self) -> bool: return self.confirm("proceed?", True)
    def confirm_execution(self) -> bool: return self.confirm("execute?", True)

    def choose_option(self, prompt: str, options: List[str], default_index: Optional[int] = None) -> int:
        if self._yolo_mode: return default_index if default_index is not None else 0
        print()
        for i, o in enumerate(options, 1):
            print(f"   {i} {o}")
        
        default_display = f"[{default_index+1}]" if default_index is not None else ""
        res = input(f"\n   ? {prompt.lower()} {default_display}: ").strip()
        
        if not res: return default_index if default_index is not None else 0
        if res.isdigit():
            val = int(res) - 1
            if 0 <= val < len(options): return val
        return self.choose_option(prompt, options, default_index)

    def typing_animation(self, text: str, delay: float = 0.02) -> None:
        for char in text:
            print(char, end="", flush=True)
            time.sleep(delay)
        print()

# ===============================================================================
# 5. OVERLORD UI (Max Info, Metrics, Trace)
# ===============================================================================

class OverlordUI(BaseUI):
    C_LOG = "\033[32m"      # Terminal Green
    C_HEAD = "\033[1;32m"   # Bold Green
    C_WARN = "\033[33m"     # Amber
    C_ERR = "\033[31m"      # Red
    C_META = "\033[90m"     # Grey
    RESET = "\033[0m"
    
    def _ts(self):
        return datetime.now().strftime("%H:%M:%S.%f")[:-3]

    def banner(self) -> None:
        self.clear()
        print(f"{self.C_HEAD}KERNEL_INIT_SEQUENCE_STARTED_{self.RESET}")
        print(f"{self.C_META}PID: {self._pid} | SESSION: {hex(id(self))} | TTY: {sys.stdout.isatty()}{self.RESET}")
        print(f"{self.C_LOG}[{self._ts()}] [SYS] MOUNTING_INTERFACES... OK{self.RESET}")
        print(f"{self.C_LOG}[{self._ts()}] [SYS] LOADING_UI_OVERLORD... OK{self.RESET}")
        print("-" * 80)

    def section_header(self, title: str, icon_key: str = ""):
        print(f"\n{self.C_HEAD}>>> BLOCK_START: {title.upper()} <<<{self.RESET}")

    def status(self, message: str, level: str = "info") -> None:
        col = self.C_LOG
        if level == "warning": col = self.C_WARN
        if level == "error": col = self.C_ERR
        
        # Format: [TIME] [PID] [LEVEL] MESSAGE
        print(f"{self.C_META}[{self._ts()}] [{self._pid}] [{level.upper():<4}]{self.RESET} {col}{message}{self.RESET}")

    def start_spinner(self, message: str) -> None:
        self.stop_spinner()
        self._spinner_running = True
        self._spinner_message = message
        def spin():
            # Hex frames
            frames = cycle(["0x00", "0x33", "0x66", "0x99", "0xCC", "0xFF"])
            while self._spinner_running:
                print(f"\r{self.C_META}[{self._ts()}] [PROC] {next(frames)} > {self._spinner_message.upper()}...{self.RESET}", end="")
                time.sleep(0.1)
            print("\r" + " " * (len(self._spinner_message) + 30) + "\r", end="")
        self._spinner_thread = threading.Thread(target=spin, daemon=True)
        self._spinner_thread.start()

    def stop_spinner(self, final_message: Optional[str] = None, level: str = "success") -> None:
        if not self._spinner_running: return
        self._spinner_running = False
        if self._spinner_thread: self._spinner_thread.join()
        print("\r", end="")
        if final_message: self.status(final_message, level)
        self._spinner_thread = None

    def stream_prefix(self, backend_label: Optional[str]) -> None:
        print()
        src = backend_label.upper() if backend_label else "CORE"
        print(f"{self.C_HEAD}[STREAM_OPEN] SOURCE:{src}{self.RESET}\n", end="", flush=True)

    def streaming_chunk(self, chunk: str) -> None:
        print(chunk, end="", flush=True)

    def show_think_tags(self, think_contents: List[str]) -> None:
        if not think_contents: return
        for think in think_contents:
            print(f"\n{self.C_META}--- TRACE_BLOCK_START ---"{self.RESET})
            for line in think.strip().split('\n'):
                print(f"{self.C_META}[THINK] {line}{self.RESET}")
            print(f"{self.C_META}--- TRACE_BLOCK_END ---"{self.RESET})

    def show_plan(self, plan: dict) -> None:
        self.section_header("DPPM_EXECUTION_PROTOCOL")
        # Raw dump
        print(f"{self.C_LOG}{json.dumps(plan, indent=4)}{self.RESET}")

    def list_agents(self, agents, active_key: Optional[str] = None) -> None:
        try: l = list(agents.values())
        except: l = list(agents)
        self.section_header("REGISTERED_AGENTS")
        print(f"{self.C_META}{'ID':<4} | {'NAME':<20} | {'STATUS':<10} | {'MEMORY'}{self.RESET}")
        print(f"{self.C_META}-{'-'*50}{self.RESET}")
        for i, ag in enumerate(l, 1):
            stat = "ACTIVE" if (active_key and ag.key == active_key) else "IDLE"
            col = self.C_LOG if stat == "ACTIVE" else self.C_META
            print(f"{col}{i:04d} | {ag.display_name:<20} | {stat:<10} | {ag.memory_categories}{self.RESET}")

    def show_available_tools(self, tools: List[Dict]) -> None:
        self.section_header("MODULE_REGISTRY")
        print(f"{self.C_META}COUNT: {len(tools)} MODULES{self.RESET}")
        for t in tools:
            print(f"{self.C_LOG}[MOD] {t['name']:<25} :: {t['description'][:50]}{self.RESET}")

    def confirm(self, message: str, default_yes: bool = False) -> bool:
        if self._yolo_mode: return True
        opt = "YES/no" if default_yes else "yes/NO"
        res = input(f"{self.C_WARN}[INTERRUPT] {message.upper()} <{opt}>: {self.RESET}").strip().lower()
        if not res: return default_yes
        return res in ("y", "yes")

    def confirm_plan(self) -> bool: return self.confirm("AUTHORIZE_PROTOCOL_EXECUTION", True)
    def confirm_execution(self) -> bool: return self.confirm("INITIATE_PROCESS", True)

    def choose_option(self, prompt: str, options: List[str], default_index: Optional[int] = None) -> int:
        if self._yolo_mode: return default_index if default_index is not None else 0
        print(f"\n{self.C_HEAD}--- SELECTION_REQUIRED ---"{self.RESET})
        for i, o in enumerate(options, 1):
            print(f"[{i:02d}] {o}")
        
        default_display = f"[{default_index+1}]" if default_index is not None else ""
        res = input(f"{self.C_WARN}>> {prompt.upper()} {default_display}: {self.RESET}").strip()
        
        if not res: return default_index if default_index is not None else 0
        if res.isdigit():
            val = int(res) - 1
            if 0 <= val < len(options): return val
        return self.choose_option(prompt, options, default_index)
    
    def typing_animation(self, text: str, delay: float = 0.01) -> None:
        print(text) # Max speed, no animation


# ===============================================================================
# FACTORY / EXPORT
# ===============================================================================

UI_THEMES = {
    "TACTICAL": TacticalUI,
    "STARK": StarkUI,
    "NEON": NeonUI,
    "ZEN": ZenUI,
    "OVERLORD": OverlordUI
}

def get_ui_class(theme_name: str = "TACTICAL"):
    """Returns the UI Class (not instance) based on name."""
    return UI_THEMES.get(theme_name.upper(), TacticalUI)

# Default export
GeminiUI = TacticalUI