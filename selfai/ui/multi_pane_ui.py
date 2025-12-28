"""
Multi-Pane Terminal UI für parallele Subtask-Streams
====================================================

Zeigt mehrere Subtasks gleichzeitig in separaten Panes an.
Jeder Pane zeigt den Stream-Output eines Subtasks.

Author: SelfAI Team
Date: 2025-01-21
"""

import sys
import threading
import time
import shutil
from collections import deque
from typing import Dict, List, Optional


class SubtaskPane:
    """Repräsentiert einen einzelnen Pane für einen Subtask."""

    def __init__(self, task_id: str, title: str, max_lines: int = 4):
        self.task_id = task_id
        self.title = title
        self.max_lines = max_lines
        self.lines: deque = deque(maxlen=max_lines)
        self.status = "running"  # running, completed, failed
        self.start_time = time.time()
        self.end_time: Optional[float] = None
        self.lock = threading.Lock()

    def add_line(self, text: str):
        """Fügt eine Zeile hinzu (thread-safe)."""
        with self.lock:
            # Verzögerung: max 1 Zeile pro Sekunde für Lesbarkeit
            if len(self.lines) > 0:
                time.sleep(0.3)  # 300ms zwischen Zeilen

            self.lines.append(text)

    def set_status(self, status: str):
        """Setzt Status (running/completed/failed)."""
        with self.lock:
            self.status = status
            if status in ("completed", "failed"):
                self.end_time = time.time()

    def get_duration(self) -> float:
        """Gibt Laufzeit in Sekunden zurück."""
        if self.end_time:
            return self.end_time - self.start_time
        return time.time() - self.start_time

    def render(self, width: int) -> List[str]:
        """
        Rendert Pane als Liste von Zeilen.
        
        Args:
            width: Maximale Breite für den Inhalt (ohne Borders)
            
        Returns:
            List[str]: Zeilen für Ausgabe
        """
        with self.lock:
            output = []

            # Header mit Status
            status_icons = {
                "running": "🔄",
                "completed": "✅",
                "failed": "❌"
            }
            icon = status_icons.get(self.status, "⏳")

            duration = self.get_duration()
            header_text = f"{icon} {self.title} ({self.task_id})"
            
            if self.status != "running":
                header_text += f" - {duration:.1f}s"
                
            # Truncate header safely
            if len(header_text) > width:
                header_text = header_text[:width-1] + "…"
            
            output.append(header_text)

            # Content lines
            for line in self.lines:
                # Remove ANSI codes potentially? For now just raw text
                clean_line = line.replace('\n', ' ').replace('\r', '')
                
                # Truncate content safely
                if len(clean_line) > width:
                    clean_line = clean_line[:width-3] + "..."
                
                output.append("  " + clean_line)

            # Fill empty lines to keep height constant
            while len(output) < self.max_lines + 1:  # +1 for header
                output.append("")

            return output


class MultiPaneUI:
    """
    Multi-Pane Terminal UI für parallele Subtask-Anzeige.
    """

    def __init__(self, pane_height: int = 4):
        self.panes: Dict[str, SubtaskPane] = {}
        self.pane_height = pane_height
        self.render_thread: Optional[threading.Thread] = None
        self.rendering = False
        self.terminal_width = 80
        self._render_lock = threading.Lock()
        
        # Hide cursor initially
        sys.stdout.write("\033[?25l")
        sys.stdout.flush()

        # Detect terminal width
        self._update_terminal_size()

    def _update_terminal_size(self):
        try:
            self.terminal_width = shutil.get_terminal_size().columns
        except Exception:
            self.terminal_width = 80

    def add_pane(self, task_id: str, title: str):
        """Fügt einen neuen Pane hinzu."""
        self.panes[task_id] = SubtaskPane(task_id, title, self.pane_height)

    def update_pane(self, task_id: str, text: str):
        """Fügt Text zu einem Pane hinzu."""
        if task_id in self.panes:
            self.panes[task_id].add_line(text)

    def complete_pane(self, task_id: str):
        """Markiert Pane als completed."""
        if task_id in self.panes:
            self.panes[task_id].set_status("completed")

    def fail_pane(self, task_id: str):
        """Markiert Pane als failed."""
        if task_id in self.panes:
            self.panes[task_id].set_status("failed")

    def render_frame(self):
        """Rendert einen Frame (alle Panes) - statisch."""
        with self._render_lock:
            # Update size just in case user resized terminal
            self._update_terminal_size()
            
            # Safety margin: -2 for borders, -2 for safety
            content_width = max(10, self.terminal_width - 4)
            
            # Calculate total lines (pane content + borders)
            lines_per_pane = self.pane_height + 3  # header + content + top border + separator
            total_lines = len(self.panes) * lines_per_pane + 1  # +1 for final bottom border

            # Move cursor up on subsequent renders
            if hasattr(self, '_first_render') and not self._first_render:
                # Move up
                sys.stdout.write(f"\033[{total_lines}A")
            else:
                self._first_render = False

            # Render all panes in one box
            # Top Border
            print("┌" + "─" * (self.terminal_width - 2) + "┐")

            pane_ids = sorted(self.panes.keys())
            for idx, pane_id in enumerate(pane_ids):
                pane = self.panes[pane_id]
                lines = pane.render(content_width)

                # Content lines
                for line in lines:
                    # Pad to width explicitly to clear old content
                    # Justify left, fill with spaces
                    padded = line.ljust(self.terminal_width - 4)
                    # Enforce hard limit to prevent wrap
                    padded = padded[:self.terminal_width - 4]
                    
                    print("│ " + padded + " │")

                # Separator between panes (not after last)
                if idx < len(pane_ids) - 1:
                    print("├" + "─" * (self.terminal_width - 2) + "┤")

            # Final bottom border
            print("└" + "─" * (self.terminal_width - 2) + "┘")

            sys.stdout.flush()

    def _render_loop(self):
        """Background rendering loop."""
        self._first_render = True

        while self.rendering:
            self.render_frame()
            time.sleep(0.5)  # Refresh every 500ms

    def start_rendering(self):
        """Startet Background-Rendering."""
        if self.rendering:
            return

        self.rendering = True
        # Hide cursor
        sys.stdout.write("\033[?25l")
        
        self.render_thread = threading.Thread(target=self._render_loop, daemon=True)
        self.render_thread.start()

    def stop_rendering(self):
        """Stoppt Background-Rendering."""
        self.rendering = False
        if self.render_thread:
            self.render_thread.join(timeout=1.0)

        # Final render
        self.render_frame()
        
        # Show cursor again
        sys.stdout.write("\033[?25h")
        sys.stdout.flush()

    def all_completed(self) -> bool:
        """Prüft ob alle Panes completed oder failed sind."""
        return all(
            pane.status in ("completed", "failed")
            for pane in self.panes.values()
        )


# Streaming wrapper für Execution Dispatcher
class MultiPaneStreamWrapper:
    """
    Wrapper der Subtask-Output zu Multi-Pane UI routet.
    """

    def __init__(self, multi_pane_ui: MultiPaneUI):
        self.multi_pane = multi_pane_ui

    def route_stream(self, task_id: str, stream_iterator):
        """
        Routet Stream-Output zu entsprechendem Pane.
        """
        buffer = ""

        for chunk in stream_iterator:
            buffer += chunk

            # Split by newlines
            if "\n" in buffer:
                lines = buffer.split("\n")
                buffer = lines[-1]  # Keep last incomplete line

                for line in lines[:-1]:
                    if line.strip():
                        self.multi_pane.update_pane(task_id, line.strip())

        # Add remaining buffer
        if buffer.strip():
            self.multi_pane.update_pane(task_id, buffer.strip())


def demo_multi_pane():
    """Demo der Multi-Pane UI."""
    try:
        ui = MultiPaneUI(pane_height=4)

        # Add panes
        ui.add_pane("S1", "Code Analysis")
        ui.add_pane("S2", "Implementation")
        ui.add_pane("S3", "Testing")

        # Start rendering
        ui.start_rendering()

        # Simulate work
        import random

        tasks = [
            ("S1", ["Analyzing files...", "Loading modules...", "Checking imports...", "Analysis complete!"]),
            ("S2", ["Starting implementation...", "Modifying code...", "Running formatters...", "Done!"]),
            ("S3", ["Running tests...", "Test 1: PASS", "Test 2: PASS", "All tests passed!"]),
        ]

        # Simulate parallel work
        def work(task_id, messages):
            for msg in messages:
                time.sleep(random.uniform(0.5, 2.0))
                ui.update_pane(task_id, msg)
            ui.complete_pane(task_id)

        threads = []
        for task_id, messages in tasks:
            t = threading.Thread(target=work, args=(task_id, messages))
            t.start()
            threads.append(t)

        # Wait for completion
        for t in threads:
            t.join()

        # Stop rendering
        ui.stop_rendering()

        print("\n✅ All subtasks completed!")
        
    except KeyboardInterrupt:
        # Ensure cursor is shown even on Ctrl+C
        sys.stdout.write("\033[?25h")
        sys.stdout.flush()


if __name__ == "__main__":
    demo_multi_pane()