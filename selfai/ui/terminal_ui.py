import json
import os
import sys
import threading
import time
from itertools import cycle
from typing import Optional

# Terminal UI Module - Rich terminal interface for SelfAI
# Last updated: 2025-12-08


class TerminalUI:
    """Einfache Terminal-UI mit Farben, Banner und Spinner."""

    SPINNER_FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

    def __init__(self) -> None:
        self._spinner_thread: Optional[threading.Thread] = None
        self._spinner_running = False
        self._spinner_message = ""
        self._first_chunk_printed = False
        self._enable_color = self._detect_color_support()
        self._yolo_mode = False  # YOLO mode: auto-accept all prompts
        self._colors = {
            "cyan": "\033[96m",
            "magenta": "\033[95m",
            "green": "\033[92m",
            "yellow": "\033[93m",
            "red": "\033[91m",
            "blue": "\033[94m",
            "bold": "\033[1m",
            "reset": "\033[0m",
        }

    @staticmethod
    def _detect_color_support() -> bool:
        if os.name == "nt":
            try:
                from colorama import init  # type: ignore

                init()
                return True
            except ImportError:
                return False
        return sys.stdout.isatty()

    def colorize(self, text: str, color: str) -> str:
        if not self._enable_color:
            return text
        prefix = self._colors.get(color, "")
        suffix = self._colors["reset"] if prefix else ""
        return f"{prefix}{text}{suffix}"

    def clear(self) -> None:
        os.system("cls" if os.name == "nt" else "clear")

    def banner(self) -> None:
        line = self.colorize(
            "╔══════════════════════════════════════════════════════════════╗",
            "cyan",
        )
        title = self.colorize("🚀  SelfAI Hybrid Chat (NPU & CPU) 🚀", "magenta")
        print(line)
        print(self.colorize("║                                                              ║", "cyan"))
        center = title.center(60)
        print(self.colorize(f"║{center}║", "cyan"))
        print(self.colorize("║                                                              ║", "cyan"))
        print(line.replace("╔", "╚").replace("╗", "╝"))

    def status(self, message: str, level: str = "info") -> None:
        icons = {
            "info": "ℹ️ ",
            "success": "✅ ",
            "warning": "⚠️ ",
            "error": "❌ ",
        }
        colors = {
            "info": "cyan",
            "success": "green",
            "warning": "yellow",
            "error": "red",
        }
        icon = icons.get(level, "")
        color = colors.get(level, "")
        print(f"{icon}{self.colorize(message, color)}")

    def start_spinner(self, message: str) -> None:
        self.stop_spinner()
        self._spinner_running = True
        self._spinner_message = message

        def spin() -> None:
            frames = cycle(self.SPINNER_FRAMES)
            while self._spinner_running:
                frame = next(frames)
                text = f"{self.colorize(frame, 'cyan')} {self._spinner_message}"
                print(f"\r{text}", end="", flush=True)
                time.sleep(0.1)
            # Clear the spinner line when stopping
            print("\r" + " " * (len(self._spinner_message) + 4) + "\r", end="", flush=True)

        self._spinner_thread = threading.Thread(target=spin, daemon=True)
        self._spinner_thread.start()

    def stop_spinner(self, final_message: Optional[str] = None, level: str = "success") -> None:
        if not self._spinner_running:
            return
        self._spinner_running = False
        if self._spinner_thread:
            self._spinner_thread.join()
        if final_message:
            self.status(final_message, level=level)
        self._spinner_thread = None
        self._first_chunk_printed = False

    def stream_prefix(self, backend_label: Optional[str]) -> None:
        backend_text = f"[{backend_label}]" if backend_label else ""
        prefix = self.colorize("SelfAI", "magenta")
        print(f"{prefix} {backend_text}: ", end="", flush=True)
        self._first_chunk_printed = True

    def streaming_chunk(self, chunk: str) -> None:
        if chunk:
            if not self._first_chunk_printed:
                print(chunk, end="", flush=True)
                self._first_chunk_printed = True
            else:
                print(chunk, end="", flush=True)

    def typing_animation(self, text: str, delay: float = 0.02) -> None:
        for char in text:
            print(char, end="", flush=True)
            time.sleep(delay)
        print()

    def list_agents(self, agents, active_key: Optional[str] = None) -> None:
        """Gibt eine formatierte Liste verfügbarer Agenten aus."""
        try:
            agent_list = list(agents.values())
        except AttributeError:
            agent_list = list(agents)

        if not agent_list:
            self.status("Keine Agenten verfügbar.", "warning")
            return

        print(self.colorize("\nVerfügbare Agenten:", "bold"))

        for idx, agent in enumerate(agent_list, start=1):
            is_active = active_key and agent.key == active_key
            marker = self.colorize("➤", "magenta") if is_active else " "
            name_colored = self.colorize(agent.display_name, agent.color)
            categories = ", ".join(agent.memory_categories) or "-"
            print(
                f"{marker} {idx:>2}. {name_colored} "
                f"(Workspace: {agent.workspace_slug}, Memory: {categories})"
            )
            if agent.description:
                print(f"      {self.colorize(agent.description, 'cyan')}")

    def display_final_result(self, content: str, title: str = "Final Result"):
        """Clears the screen and prints the final content block."""
        self.clear()
        self.banner()
        self.status(title, "success")
        print(f"\n{content}")

    def show_plan(self, plan: dict) -> None:
        """Zeigt den vom Planner gelieferten JSON-Plan formatiert an."""
        print(self.colorize("\nGeplanter Ablauf (DPPM):", "bold"))
        formatted = json.dumps(plan, indent=2, ensure_ascii=False)
        print(formatted)

    def enable_yolo_mode(self) -> None:
        """Enable YOLO mode - auto-accept all prompts"""
        self._yolo_mode = True
        self.status("🚀 YOLO MODE ACTIVATED - Auto-accepting all prompts!", "warning")

    def disable_yolo_mode(self) -> None:
        """Disable YOLO mode"""
        self._yolo_mode = False
        self.status("🛑 YOLO MODE DEACTIVATED", "info")

    def is_yolo_mode(self) -> bool:
        """Check if YOLO mode is active"""
        return self._yolo_mode

    def _confirm(self, prompt: str, default_yes: bool = False) -> bool:
        # YOLO mode: always accept
        if self._yolo_mode:
            suffix = "Y/n" if default_yes else "y/N"
            print(self.colorize(f"{prompt} ({suffix}): ", "yellow") + self.colorize("y", "green") + " (YOLO)")
            return True

        suffix = "Y/n" if default_yes else "y/N"
        answer = input(self.colorize(f"{prompt} ({suffix}): ", "yellow")).strip().lower()
        if not answer:
            return default_yes
        return answer in {"y", "yes", "j", "ja"}

    def confirm_plan(self) -> bool:
        """Fragt den Benutzer, ob der Plan ausgeführt/gespeichert werden soll."""
        return self._confirm("Plan übernehmen?", default_yes=False)

    def confirm_execution(self) -> bool:
        return self._confirm("Plan jetzt ausführen?", default_yes=False)

    def confirm(self, message: str, default_yes: bool = False) -> bool:
        """Generische Bestätigung mit Ja/Nein-Abfrage."""
        return self._confirm(message, default_yes=default_yes)

    def choose_option(self, prompt: str, options: list[str], default_index: int | None = None) -> int:
        if not options:
            raise ValueError("Optionsliste darf nicht leer sein")

        # YOLO mode: always choose first option (index 0) or default
        if self._yolo_mode:
            chosen_idx = default_index if default_index is not None else 0
            for idx, option in enumerate(options, start=1):
                marker = " ← YOLO" if idx - 1 == chosen_idx else ""
                print(self.colorize(f"  {idx}. {option}{marker}", "cyan"))
            suffix = f"1-{len(options)}"
            default_hint = f" (Default {default_index + 1})" if default_index is not None else ""
            print(self.colorize(f"{prompt} [{suffix}]{default_hint}: ", "yellow") + self.colorize(f"{chosen_idx + 1}", "green") + " (YOLO)")
            return chosen_idx

        for idx, option in enumerate(options, start=1):
            print(self.colorize(f"  {idx}. {option}", "cyan"))
        while True:
            suffix = f"1-{len(options)}"
            default_hint = f" (Default {default_index + 1})" if default_index is not None else ""
            selection = input(self.colorize(f"{prompt} [{suffix}]{default_hint}: ", "yellow")).strip()
            if not selection and default_index is not None:
                return default_index
            if selection.isdigit():
                chosen = int(selection) - 1
                if 0 <= chosen < len(options):
                    return chosen
            print(self.colorize("Ungültige Auswahl. Bitte erneut versuchen.", "red"))

    def show_available_tools(self, tools: list[dict]) -> None:
        """Zeigt verfügbare Tools in einer übersichtlichen Liste an."""
        if not tools:
            return

        print(self.colorize("\n📦 Verfügbare Tools:", "bold"))
        print(self.colorize("─" * 60, "cyan"))

        # Kategorisiere Tools
        aider_tools = [t for t in tools if "aider" in t["name"].lower()]
        calendar_tools = [t for t in tools if "calendar" in t["name"].lower()]
        project_tools = [t for t in tools if "project" in t["name"].lower()]
        other_tools = [t for t in tools if t not in aider_tools + calendar_tools + project_tools]

        def print_tool_category(category_name: str, tool_list: list[dict]) -> None:
            if not tool_list:
                return
            print(f"\n  {self.colorize(category_name, 'magenta')}:")
            for tool in tool_list:
                name_colored = self.colorize(tool["name"], "cyan")
                desc = tool["description"][:200] + "..." if len(tool["description"]) > 200 else tool["description"]
                print(f"    • {name_colored}")
                print(f"      {desc}")

        print_tool_category("🤖 AI Coding Assistant", aider_tools)
        print_tool_category("📅 Calendar & Events", calendar_tools)
        print_tool_category("📁 Project Management", project_tools)
        print_tool_category("🔧 Other Tools", other_tools)

        print(self.colorize("\n" + "─" * 60, "cyan"))
        print(self.colorize(f"  Gesamt: {len(tools)} Tools verfügbar\n", "green"))

    def show_tool_call(self, tool_name: str, arguments: dict = None) -> None:
        """
        Zeigt einen Tool-Call mit spezialisierten Emojis an.

        Args:
            tool_name: Name des aufgerufenen Tools
            arguments: Optionale Tool-Argumente
        """
        # Tool-spezifische Emojis und Labels
        tool_icons = {
            "list_selfai_files": ("👁️ 📁", "Inspiziere Dateien"),
            "read_selfai_code": ("👁️ 📄", "Lese Code"),
            "search_selfai_code": ("👁️ 🔍", "Durchsuche Code"),
            "run_aider_task": ("🤖", "Aider Task"),
            "run_openhands_task": ("🤖", "OpenHands Task"),
            "list_project_files": ("📁", "Liste Dateien"),
            "read_project_file": ("📄", "Lese Datei"),
            "search_project_files": ("🔍", "Suche Dateien"),
            "get_current_weather": ("🌤️", "Wetter"),
            "find_train_connections": ("🚆", "Bahn"),
            "add_calendar_event": ("📅", "Kalender"),
            "list_calendar_events": ("📅", "Kalender"),
        }

        icon, label = tool_icons.get(tool_name, ("🔧", "Tool"))

        # Basis-Anzeige
        tool_display = self.colorize(f"{icon} {label}: {tool_name}", "cyan")
        print(f"\n{tool_display}", end="")

        # Zeige wichtige Argumente für Self-Inspection Tools
        if arguments:
            if tool_name == "read_selfai_code" and "file_path" in arguments:
                file_name = arguments["file_path"]
                print(self.colorize(f" → {file_name}", "yellow"), end="")
            elif tool_name == "list_selfai_files" and "subdirectory" in arguments:
                subdir = arguments["subdirectory"] or "selfai/"
                print(self.colorize(f" → {subdir}", "yellow"), end="")
            elif tool_name == "search_selfai_code" and "pattern" in arguments:
                pattern = arguments["pattern"]
                print(self.colorize(f" → '{pattern}'", "yellow"), end="")

        print()  # Newline nach Tool-Call

    def show_think_tags(self, think_contents: list[str]) -> None:
        """
        Zeigt <think> tag Inhalte in separater Formatierung an.

        Args:
            think_contents: Liste von extrahierten Denk-Prozess-Inhalten
        """
        if not think_contents:
            return

        for idx, think in enumerate(think_contents, start=1):
            # Dimmed/grey style for thinking process (not main content)
            prefix = self.colorize(f"💭 [Thinking {idx}]", "blue")
            # Clean up whitespace
            think_clean = think.strip()
            # Display with indentation
            print(f"\n{prefix}")
            for line in think_clean.split('\n'):
                print(f"  {self.colorize(line, 'cyan')}")
        print()  # Extra line after all thinks

    def show_help(self) -> None:
        """Zeigt umfassende Hilfe zu allen SelfAI Commands an."""
        help_text = f"""
{self.colorize("┌─────────────────────────────────────────────────────────────────────────┐", "cyan")}
{self.colorize("│ 📖 SelfAI Command Reference                                             │", "magenta")}
{self.colorize("├─────────────────────────────────────────────────────────────────────────┤", "cyan")}
{self.colorize("│                                                                         │", "cyan")}
{self.colorize("│  💬 CHAT                                                                │", "magenta")}
{self.colorize("│     <Nachricht>       Normale Konversation mit aktuellem Agent          │", "cyan")}
{self.colorize("│                                                                         │", "cyan")}
{self.colorize("│  📋 PLANNING                                                            │", "magenta")}
{self.colorize("│     /plan <Ziel>      DPPM Plan erstellen & ausführen                 │", "cyan")}
{self.colorize("│     /planner list      Zeigt verfügbare Planner-Provider               │", "cyan")}
{self.colorize("│     /planner use <Name> Wechselt aktiven Planner                        │", "cyan")}
{self.colorize("│                                                                         │", "cyan")}
{self.colorize("│  💾 MEMORY                                                               │", "magenta")}
{self.colorize("│     /memory            Zeigt alle Memory-Kategorien                   │", "cyan")}
{self.colorize("│     /memory clear       Löscht Konversationen                       │", "cyan")}
{self.colorize("│                         Usage: /memory clear <category> [keep_n]      │", "cyan")}
{self.colorize("│                                                                         │", "cyan")}
{self.colorize("│  🤖 AGENTS                                                               │", "magenta")}
{self.colorize("│     /switch <Agent>     Wechselt aktiven Agent (Name oder Nummer)      │", "cyan")}
{self.colorize("│     /agents            Zeigt alle verfügbaren Agenten               │", "cyan")}
{self.colorize("│                                                                         │", "cyan")}
{self.colorize("│  ⚙️  SYSTEM                                                               │", "magenta")}
{self.colorize("│     /status            Zeigt System-Status & Konfiguration          │", "cyan")}
{self.colorize("│     /tokens            Zeigt/ändert Token-Limits                     │", "cyan")}
{self.colorize("│     /context           Zeigt/ändert Context Window                   │", "cyan")}
{self.colorize("│     /yolo              Aktiviert/Deaktiviert Auto-Accept Modus        │", "cyan")}
{self.colorize("│                                                                         │", "cyan")}
{self.colorize("│  🔧 TOOLS                                                               │", "magenta")}
{self.colorize("│     /toolcreate <name>  Erstellt neues Tool via LLM                   │", "cyan")}
{self.colorize("│     /errorcorrection   Startet Fehler-Analyse & Auto-Fix             │", "cyan")}
{self.colorize("│     /selfimprove <ziel> Startet Selbst-Optimierung                     │", "cyan")}
{self.colorize("│                                                                         │", "cyan")}
{self.colorize("│  ❓ OTHER                                                               │", "magenta")}
{self.colorize("│     /help              Zeigt diese Hilfe                            │", "cyan")}
{self.colorize("│     quit               Beendet SelfAI                               │", "cyan")}
{self.colorize("│                                                                         │", "cyan")}
{self.colorize("└─────────────────────────────────────────────────────────────────────────┘", "cyan")}
"""
        print(help_text)

    def show_status_dashboard(
        self,
        execution_backends: list,
        active_backend_index: int,
        agent_manager,
        memory_system,
        token_limits,
        config
    ) -> None:
        """Zeigt umfassendes System-Status-Dashboard an."""

        # Header
        print(self.colorize("\n┌─────────────────────────────────────────────────────────────────────────┐", "cyan"))
        print(self.colorize("│ 📊 SelfAI System Status                                                 │", "magenta"))
        print(self.colorize("├─────────────────────────────────────────────────────────────────────────┤", "cyan"))
        print(self.colorize("│                                                                         │", "cyan"))

        # 1. LLM Backends
        print(self.colorize("│  🤖 LLM BACKENDS                                                        │", "magenta"))
        for idx, backend in enumerate(execution_backends):
            is_active = idx == active_backend_index
            status_icon = "✅" if is_active else "⚪"
            backend_name = backend.get("name", "unknown")
            backend_type = backend.get("type", "unknown")
            backend_label = backend.get("label", backend_name)

            active_marker = self.colorize(" (aktiv)", "green") if is_active else ""
            type_badge = self.colorize(f"[{backend_type}]", "yellow")
            print(f"│   {status_icon} {backend_label:30s} {type_badge}{active_marker}              │")
        print(self.colorize("│                                                                         │", "cyan"))

        # 2. System Resources (mit psutil)
        try:
            import psutil
            mem = psutil.virtual_memory()
            cpu_percent = psutil.cpu_percent(interval=0.1)
            disk = psutil.disk_usage(".")

            print(self.colorize("│  💻 SYSTEM RESOURCES                                                    │", "magenta"))

            # RAM Bar
            ram_percent = mem.percent
            ram_bar_length = 20
            filled = int(ram_bar_length * ram_percent / 100)
            bar = "█" * filled + "░" * (ram_bar_length - filled)
            bar_color = "red" if ram_percent > 80 else "yellow" if ram_percent > 50 else "green"
            print(f"│   RAM: {self.colorize(bar, bar_color)} {ram_percent:3.0f}%                              │")

            # CPU
            cpu_bar_length = int(cpu_percent / 5)
            cpu_bar = self.colorize("█" * cpu_bar_length + "░" * (20 - cpu_bar_length), "green")
            print(f"│   CPU: {cpu_bar} {cpu_percent:3.0f}%                              │")

            # Disk
            disk_percent = disk.percent
            disk_filled = int(ram_bar_length * disk_percent / 100)
            disk_bar = "█" * disk_filled + "░" * (ram_bar_length - disk_filled)
            disk_color = "red" if disk_percent > 80 else "yellow" if disk_percent > 50 else "green"
            print(f"│   Disk: {self.colorize(disk_bar, disk_color)} {disk_percent:3.0f}%                              │")

            print(self.colorize("│                                                                         │", "cyan"))
        except ImportError:
            print(self.colorize("│   psutil nicht installiert - System-Ressourcen nicht verfügbar         │", "yellow"))
            print(self.colorize("│                                                                         │", "cyan"))
        except Exception:
            print(self.colorize("│   Fehler beim Abruf der System-Ressourcen                              │", "yellow"))
            print(self.colorize("│                                                                         │", "cyan"))

        # 3. Active Agent
        print(self.colorize("│  🤖 ACTIVE AGENT                                                        │", "magenta"))
        if agent_manager and agent_manager.active_agent:
            agent = agent_manager.active_agent
            agent_colored = self.colorize(agent.display_name, agent.color)
            print(f"│   {agent_colored} ({agent.key})                                             │")
            if agent.description:
                desc_short = agent.description[:60] if len(agent.description) > 60 else agent.description
                print(f"│   {desc_short}                                              │")
        else:
            print(f"│   Kein Agent aktiv                                                      │")
        print(self.colorize("│                                                                         │", "cyan"))

        # 4. Memory System
        print(self.colorize("│  💾 MEMORY SYSTEM                                                        │", "magenta"))
        if memory_system:
            try:
                # Categories
                categories = []
                if memory_system.memory_dir.exists():
                    for cat_dir in memory_system.memory_dir.iterdir():
                        if cat_dir.is_dir() and not cat_dir.name.startswith("."):
                            count = len(list(cat_dir.glob("*.txt")))
                            categories.append(f"{cat_dir.name}: {count}")

                if categories:
                    cat_str = ", ".join(categories[:3])
                    print(f"│   Categories: {cat_str}                                      │")
                else:
                    print(f"│   Keine Konversationen gespeichert                                      │")

                # Plans
                if hasattr(memory_system, 'plan_dir') and memory_system.plan_dir.exists():
                    plan_files = list(memory_system.plan_dir.glob("*.json"))
                    print(f"│   Plans: {len(plan_files)} gespeichert                                              │")

                # Context Window
                if hasattr(memory_system, 'context_window_minutes'):
                    print(f"│   Context Window: {memory_system.context_window_minutes} Minuten                                    │")
            except Exception as exc:
                print(f"│   Fehler beim Abruf: {str(exc)[:50]}                              │")
        else:
            print(f"│   Memory System nicht verfügbar                                         │")
        print(self.colorize("│                                                                         │", "cyan"))

        # 5. Configuration
        print(self.colorize("│  ⚙️  CONFIGURATION                                                       │", "magenta"))
        if config:
            # Streaming
            streaming_status = self.colorize("✅ Enabled", "green") if config.system.streaming_enabled else self.colorize("❌ Disabled", "red")
            print(f"│   Streaming: {streaming_status}                                                 │")

            # Agent Mode
            agent_mode_status = self.colorize("✅ Enabled", "green") if config.system.enable_agent_mode else self.colorize("❌ Disabled", "red")
            print(f"│   Agent Mode: {agent_mode_status}                                                │")

            # Planner
            planner_status = self.colorize("✅ Enabled", "green") if config.planner.enabled else self.colorize("❌ Disabled", "red")
            print(f"│   Planner: {planner_status}                                                    │")

            # Merge
            merge_status = self.colorize("✅ Enabled", "green") if config.merge.enabled else self.colorize("❌ Disabled", "red")
            print(f"│   Merge: {merge_status}                                                      │")
        print(self.colorize("│                                                                         │", "cyan"))

        # 6. Token Limits
        print(self.colorize("│  🎯 TOKEN LIMITS                                                        │", "magenta"))
        if token_limits:
            print(f"│   Planner: {token_limits.planner_max_tokens}                                                   │")
            print(f"│   Merge: {token_limits.merge_max_tokens}                                                     │")
            print(f"│   Chat: {token_limits.chat_max_tokens}                                                      │")
        else:
            print(f"│   Token Limits nicht verfügbar                                              │")
        print(self.colorize("│                                                                         │", "cyan"))

        # Footer
        print(self.colorize("└─────────────────────────────────────────────────────────────────────────┘", "cyan"))
