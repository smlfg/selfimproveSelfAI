"""
Parallel Streaming UI for SelfAI
=================================

Optional Layer für simultane Multi-Subtask Ausgabe mit Rich Library.

Features:
- Parallele Subtask-Panels nebeneinander
- Thinking (cyan, dim) vs Response (white, bright) farblich getrennt
- Live-Updates während Streaming
- Graceful Fallback zu TerminalUI wenn Rich nicht verfügbar

Aktivierung:
    export SELFAI_PARALLEL_UI=true
    python selfai/selfai.py
"""

import threading
import time
from typing import Optional, Dict, List
from dataclasses import dataclass, field

# Optional Rich imports - graceful fallback
try:
    from rich.console import Console
    from rich.live import Live
    from rich.panel import Panel
    from rich.layout import Layout
    from rich.text import Text
    from rich.table import Table
    from rich.markup import escape
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


@dataclass
class SubtaskStream:
    """Holds rolling streaming content for one subtask."""
    subtask_id: str
    title: str
    
    # Separate rolling buffers for thinking vs response
    thinking_lines: List[str] = field(default_factory=list)
    response_lines: List[str] = field(default_factory=list)
    
    # Limits
    max_thinking_lines: int = 4   # Keep thinking concise
    max_response_lines: int = 15  # Give response more space
    
    status: str = "pending"
    current_line_buffer: str = "" 
    buffer_skip_escape: bool = False

    def add_chunk(self, chunk: str, style: str = "white", skip_escape: bool = False):
        """Adds text chunk to the appropriate buffer."""
        from rich.markup import escape
        
        self.current_line_buffer += chunk
        self.buffer_skip_escape = skip_escape
        
        if "\n" in self.current_line_buffer:
            parts = self.current_line_buffer.split("\n")
            
            # Identify target list based on status
            target_list = self.thinking_lines if self.status == "thinking" else self.response_lines
            limit = self.max_thinking_lines if self.status == "thinking" else self.max_response_lines
            
            for part in parts[:-1]:
                content = part if skip_escape else escape(part)
                formatted_line = f"[{style}]{content}[/]"
                target_list.append(formatted_line)
            
            self.current_line_buffer = parts[-1]
            
            # Trim target list
            if len(target_list) > limit:
                # Modifying list in place
                del target_list[:len(target_list) - limit]

    def show_think_tags(self, think_contents: List[str]):
        """Suppress direct printing of think tags in dashboard mode."""
        # Route to status instead of breaking layout
        for think in think_contents:
            summary = think[:50].replace("\n", " ") + "..."
            self.status(f"💭 Internal Monologue processed: {summary}", "info")


class ParallelStreamUI:
    """
    Multi-Panel UI für parallele Subtask-Ausgabe (Rolling Stream).
    """

    def __init__(self, fallback_ui=None):
        self.fallback_ui = fallback_ui
        self.enabled = RICH_AVAILABLE

        if not self.enabled and fallback_ui is None:
            raise RuntimeError("ParallelStreamUI requires either Rich or fallback_ui")

        self.console = Console() if RICH_AVAILABLE else None
        self.layout = Layout() if RICH_AVAILABLE else None
        self.live = None

        self.subtasks: Dict[str, SubtaskStream] = {}
        self.task_ids: List[str] = []
        # Direct mapping for layouts to avoid lookup errors
        self.task_layout_map: Dict[str, Layout] = {} 
        self.lock = threading.Lock()
        
        self.status_log: List[str] = []
        self.header_text = ""
        self.is_active = False
        
        # Rendering state for smoothing
        self.needs_redraw = False
        self.render_thread = None

    def start_parallel_view(self, plan_goal: str, subtasks_info: List[Dict]):
        """
        Startet parallele Ansicht für Plan-Ausführung.

        Args:
            plan_goal: Das ursprüngliche Ziel des Plans
            subtasks_info: Liste von Dicts mit {id, title, agent_key}
        """
        if not self.enabled:
            # Fallback: Normale Ausgabe
            self.fallback_ui.status(f"📋 Plan: {plan_goal}", "info")
            self.fallback_ui.status(f"   {len(subtasks_info)} Subtasks werden ausgeführt", "info")
            return

        # Setup subtask streams
        with self.lock:
            self.subtasks.clear()
            self.task_ids = []
            for info in subtasks_info:
                tid = info["id"]
                self.task_ids.append(tid)
                self.subtasks[tid] = SubtaskStream(
                    subtask_id=tid,
                    title=info.get("title", f"Subtask {tid}")
                )

        # Setup layout
        self._setup_layout(plan_goal, len(subtasks_info))

        # Start live display
        self.is_active = True
        self.live = Live(self.layout, console=self.console, refresh_per_second=12, screen=False)
        self.live.start()
        
        # Start background updater
        self.render_thread = threading.Thread(target=self._render_loop, daemon=True)
        self.render_thread.start()

    def _render_loop(self):
        """Background loop to update panel content at fixed rate (smoothing)."""
        while self.is_active:
            if self.needs_redraw:
                with self.lock:
                    for tid in self.task_ids:
                        self._update_subtask_panel(tid)
                    self._update_footer()
                self.needs_redraw = False
            time.sleep(0.05) # ~20 FPS check rate

    def _setup_layout(self, goal: str, num_subtasks: int):
        """Erstellt das Layout: Vertikale Stapelung für maximale Lesbarkeit (Full Width)."""
        # Header
        header = f"🚀 EXECUTION: {goal}"

        # Main layout structure
        # Header, Tasks, Merge (initially invisible/small), Footer
        self.layout.split_column(
            Layout(name="header", size=3),
            Layout(name="tasks"),
            Layout(name="merge", visible=False), # Placeholder for merge
            Layout(name="footer", size=3),
        )

        # Vertical Stack Strategy
        # Use ratio=1 so tasks share the full vertical space equally!
        # No fixed size = auto resize based on terminal height
        self.task_layout_map.clear()
        task_layouts = []
        for tid in self.task_ids:
            layout = Layout(name=f"task_{tid}", ratio=1)
            self.task_layout_map[tid] = layout
            task_layouts.append(layout)
            
        self.layout["tasks"].split_column(*task_layouts)
        
        # Set header
        self.header_text = header
        self._update_header()
        self._update_footer()

    def add_merge_box(self):
        """Activates the dedicated Merge/Synthesis box."""
        if not self.enabled:
            return

        with self.lock:
            tid = "MERGE"
            self.task_ids.append(tid)
            self.subtasks[tid] = SubtaskStream(
                subtask_id=tid,
                title="Synthese & Zusammenfassung",
                status="thinking"
            )
            
            # Activate the pre-reserved merge layout
            merge_layout = self.layout["merge"]
            merge_layout.visible = True
            merge_layout.size = 12 # Set fixed height
            
            # Create a child layout for content to match structure
            # content_layout = Layout(name=f"task_{tid}")
            # merge_layout.update(content_layout)
            
            # Store reference
            self.task_layout_map[tid] = merge_layout
            
            # Trigger update
            self.needs_redraw = True

    def _update_header(self):
        """Aktualisiert Header-Panel."""
        header_table = Table.grid(expand=True)
        header_table.add_column(justify="center")
        header_table.add_row(f"[bold magenta]{self.header_text}[/]")
        self.layout["header"].update(Panel(header_table, style="bold magenta"))

    def _update_footer(self):
        """Aktualisiert Footer-Panel mit dem letzten Status-Log."""
        if not self.status_log:
            msg = "System Ready."
        else:
            msg = self.status_log[-1]
        
        footer_table = Table.grid(expand=True)
        footer_table.add_column(justify="left")
        footer_table.add_row(f"[bold yellow] STATUS: [/][white]{msg}[/]")
        self.layout["footer"].update(Panel(footer_table, style="bold yellow"))

    def status(self, message: str, level: str = "info"):
        """Status-Meldung im Dashboard oder Fallback."""
        if not self.enabled:
            if self.fallback_ui:
                self.fallback_ui.status(message, level)
            return

        if self.is_active:
            with self.lock:
                # Clean message from ANSI
                import re
                clean_msg = re.sub(r'\033\[[0-9;]*[mK]', '', message)
                self.status_log.append(clean_msg)
                if len(self.status_log) > 20:
                    self.status_log.pop(0)
                self.needs_redraw = True # Trigger background update
        else:
            if self.fallback_ui:
                self.fallback_ui.status(message, level)

    def add_thinking_chunk(self, subtask_id: str, chunk: str, skip_escape: bool = False):
        """Fügt einen Thinking-Chunk hinzu (Rolling Stream)."""
        if not self.enabled or not self.is_active:
            if self.fallback_ui:
                self.fallback_ui.status(f"💭 [{subtask_id}] {chunk}", "info")
            return

        with self.lock:
            if subtask_id in self.subtasks:
                self.subtasks[subtask_id].add_chunk(chunk, style="dim cyan", skip_escape=skip_escape)
                self.subtasks[subtask_id].status = "thinking"
                self.needs_redraw = True

    def add_response_chunk(self, subtask_id: str, chunk: str, skip_escape: bool = False):
        """Fügt einen Response-Chunk hinzu (Rolling Stream)."""
        if not self.enabled or not self.is_active:
            return

        with self.lock:
            if subtask_id in self.subtasks:
                self.subtasks[subtask_id].add_chunk(chunk, style="bright_white", skip_escape=skip_escape)
                self.subtasks[subtask_id].status = "responding"
                self.needs_redraw = True

    def mark_subtask_complete(self, subtask_id: str, success: bool = True):
        """Markiert Subtask als fertig."""
        if not self.enabled or not self.is_active:
            if self.fallback_ui:
                icon = "✅" if success else "❌"
                self.fallback_ui.status(f"{icon} Subtask {subtask_id} completed", "success" if success else "error")
            return

        with self.lock:
            if subtask_id in self.subtasks:
                self.subtasks[subtask_id].status = "completed" if success else "failed"
                if self.subtasks[subtask_id].current_line_buffer:
                    self.subtasks[subtask_id].add_chunk("\n", style="white") 
                self.needs_redraw = True

    def _update_subtask_panel(self, subtask_id: str):
        """Aktualisiert das Panel eines Subtasks (Rolling Lines)."""
        subtask = self.subtasks[subtask_id]
        from rich.markup import escape

        status_icons = {
            "pending": "⏳",
            "thinking": "💭",
            "responding": "💬",
            "completed": "✅",
            "failed": "❌"
        }
        icon = status_icons.get(subtask.status, "•")
        
        border_style = {
            "pending": "dim blue",
            "thinking": "cyan",
            "responding": "bright_blue",
            "completed": "green",
            "failed": "red"
        }.get(subtask.status, "blue")

        # Combine thinking and response for display
        text_parts = []
        
        if subtask.thinking_lines:
            text_parts.append("[dim]💭 Thinking:[/]")
            text_parts.extend(subtask.thinking_lines)
            if subtask.response_lines:
                text_parts.append("[dim]────────────────────────────────[/]") # Separator
        
        if subtask.response_lines:
            text_parts.extend(subtask.response_lines)
            
        text_content = "\n".join(text_parts)
        
        if not text_content and not subtask.current_line_buffer and subtask.status == "pending":
            text_content = "[dim]Waiting to start...[/]"
            
        if subtask.current_line_buffer:
            style = "dim cyan" if subtask.status == "thinking" else "bright_white"
            display_buffer = subtask.current_line_buffer if subtask.buffer_skip_escape else escape(subtask.current_line_buffer)
            
            # If switching from thinking to response in buffer, add separator visually
            if subtask.status == "responding" and not subtask.response_lines and subtask.thinking_lines:
                 text_content += "\n[dim]────────────────────────────────[/]"
                 
            text_content += f"\n[{style}]{display_buffer} █[/]"
        elif subtask.status in ("thinking", "responding"):
             text_content += "\n[dim]█[/]"

        # Dynamic height calculation
        # We rely on Layout(ratio=1) to handle the size, so we don't set fixed height here.
        # But we ensure expand=True fills the layout slot.

        panel = Panel(
            text_content,
            title=f"{icon} [bold]{subtask.title}[/]",
            title_align="left",
            border_style=border_style,
            padding=(0, 1),
            expand=True
        )

        # Update layout - Direct access via map
        if subtask_id in self.task_layout_map:
            self.task_layout_map[subtask_id].update(panel)

    def show_think_tags(self, think_contents: List[str]):
        """Suppress direct printing of think tags in dashboard mode."""
        if not self.enabled or not self.is_active:
            if self.fallback_ui:
                self.fallback_ui.show_think_tags(think_contents)
            return

        # Route to status instead of breaking layout
        for think in think_contents:
            summary = think[:60].replace("\n", " ") + "..."
            self.status(f"💭 Internal Monologue processed: {summary}", "info")

    def stop_parallel_view(self):
        """Beendet die parallele Ansicht."""
        if self.live:
            self.live.stop()
            self.is_active = False
            self.live = None

        with self.lock:
            self.subtasks.clear()

    def display_final_result(self, content: str, title: str = "Final Result"):
        """Stops the live view and prints the final content block."""
        if self.is_active:
            self.stop_parallel_view()

        if not self.console:
            # Should not happen if self.enabled is true, but as a safeguard
            if self.fallback_ui:
                self.fallback_ui.display_final_result(content, title)
            return

        # Use the console to clear and print for a clean slate.
        self.console.clear()

        # Reuse fallback UI's banner for consistency
        if self.fallback_ui and hasattr(self.fallback_ui, "banner"):
            self.fallback_ui.banner()

        # Print a title for the final result
        from rich.panel import Panel
        from rich.text import Text
        from rich.markdown import Markdown

        self.console.print(
            Panel(
                Text(title, justify="center", style="bold green"),
                border_style="green",
            )
        )

        # Use rich's print to handle markdown and formatting
        self.console.print(
            Panel(
                Markdown(content, style="bright_white"),
                border_style="dim",  # Use a subtle border
                title="Full Response",
                title_align="left",
            )
        )

    # === Compatibility Methods für TerminalUI Interface ===

    def start_spinner(self, message: str):
        if self.fallback_ui:
            self.fallback_ui.start_spinner(message)

    def stop_spinner(self, final_message: str = None, level: str = "success"):
        if self.fallback_ui:
            self.fallback_ui.stop_spinner(final_message, level)

    def __getattr__(self, name):
        if self.fallback_ui:
            return getattr(self.fallback_ui, name)
        raise AttributeError(f"ParallelStreamUI has no attribute '{name}'")


def is_parallel_ui_available() -> bool:
    return RICH_AVAILABLE


def should_use_parallel_ui() -> bool:
    import os
    env_val = os.getenv("SELFAI_PARALLEL_UI", "").lower()
    if env_val in ("false", "0", "no"):
        return False
    return True