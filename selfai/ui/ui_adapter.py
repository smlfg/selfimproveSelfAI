"""
UI Adapter for SelfAI
=====================

Switcher zwischen TerminalUI und ParallelStreamUI.

Usage:
    ui = create_ui()  # Wählt automatisch basierend auf ENV
"""

import os
from typing import Union

from selfai.ui.terminal_ui import TerminalUI
from selfai.ui.parallel_stream_ui import (
    ParallelStreamUI,
    is_parallel_ui_available,
    should_use_parallel_ui
)


def should_use_parallel_ui() -> bool:
    """
    Check ob Parallel UI aktiviert werden soll.
    Default: True wenn Rich verfügbar ist, außer SELFAI_PARALLEL_UI=false ist gesetzt.
    """
    env_val = os.getenv("SELFAI_PARALLEL_UI", "").lower()
    
    # Explizit deaktiviert
    if env_val in ("false", "0", "no"):
        return False
        
    # Explizit aktiviert oder Default (True)
    return True


def create_ui() -> Union[TerminalUI, ParallelStreamUI]:
    """
    Erstellt die passende UI basierend auf Environment und Verfügbarkeit.

    Returns:
        ParallelStreamUI wenn:
          - SELFAI_PARALLEL_UI nicht 'false'
          - Rich library installiert
        Sonst: TerminalUI (Fallback)
    """
    # Check ob Parallel UI gewünscht und verfügbar
    if should_use_parallel_ui():
        if is_parallel_ui_available():
            # Erstelle TerminalUI als Fallback
            fallback = TerminalUI()

            # Wrap in ParallelStreamUI
            parallel_ui = ParallelStreamUI(fallback_ui=fallback)

            return parallel_ui
        else:
            # Gewünscht (oder Default) aber nicht verfügbar
            ui = TerminalUI()
            # Nur Warnung zeigen wenn explizit gewünscht
            if os.getenv("SELFAI_PARALLEL_UI", "").lower() in ("true", "1", "yes"):
                ui.status("⚠️ Parallel Stream UI gewünscht aber Rich nicht installiert", "warning")
                ui.status("   Install mit: pip install -r requirements-ui.txt", "info")
            return ui
    else:
        # Explizit deaktiviert
        return TerminalUI()


def get_ui_info() -> dict:
    """
    Gibt Informationen über verfügbare UIs zurück.

    Returns:
        dict mit: {
            'parallel_available': bool,
            'parallel_enabled': bool,
            'active_ui': str
        }
    """
    return {
        'parallel_available': is_parallel_ui_available(),
        'parallel_enabled': should_use_parallel_ui(),
        'active_ui': 'ParallelStreamUI' if (should_use_parallel_ui() and is_parallel_ui_available()) else 'TerminalUI'
    }
