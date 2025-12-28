"""
Self-Inspection Tools for SelfAI
---------------------------------
Ermöglicht SelfAI, den eigenen Source-Code zu lesen und zu durchsuchen.

**Security**: Zugriff nur auf selfai/**/*.py (Whitelist-Prinzip)

Tools:
1. ListSelfAIFilesTool - Liste alle Python-Dateien im SelfAI Codebase
2. ReadSelfAICodeTool - Lese Source-Code einer spezifischen Datei
3. SearchSelfAICodeTool - Suche nach Pattern/Begriff im Code

Author: Claude Code + User
Date: 2025-01-21
Context: Lösung für Self-Awareness Gap (Gemini's "Lean Way")
"""

from pathlib import Path
import subprocess
from typing import Dict, Any


class ListSelfAIFilesTool:
    """Liste alle Python-Dateien im SelfAI Codebase."""

    @property
    def name(self) -> str:
        return "list_selfai_files"

    @property
    def description(self) -> str:
        return (
            "Liste alle Python-Dateien (.py) im SelfAI Codebase auf. "
            "Nutze dies, um zu sehen welche Komponenten existieren. "
            "Optional: Gib ein Unterverzeichnis an (z.B. 'core', 'tools', 'ui')."
        )

    @property
    def inputs(self) -> Dict[str, Any]:
        return {
            "subdirectory": {
                "type": "string",
                "description": "Optional: Unterverzeichnis (z.B. 'core', 'tools', 'ui'). Leer = alle Dateien.",
                "nullable": True
            }
        }

    def forward(self, subdirectory: str = "") -> str:
        """
        Liste alle .py Dateien im SelfAI Verzeichnis.

        Args:
            subdirectory: Optional subdirectory (z.B. "core")

        Returns:
            Formatierte Liste aller Python-Dateien
        """
        try:
            # Finde SelfAI root (selfai/)
            selfai_root = Path(__file__).parent.parent  # tools/ -> selfai/

            # Bestimme Suchpfad
            if subdirectory:
                search_path = selfai_root / subdirectory
                if not search_path.exists():
                    return f"❌ Fehler: Unterverzeichnis '{subdirectory}' existiert nicht in selfai/"
            else:
                search_path = selfai_root

            # Finde alle .py Dateien
            py_files = sorted(search_path.rglob("*.py"))

            if not py_files:
                return f"Keine Python-Dateien gefunden in: {search_path.relative_to(selfai_root.parent)}"

            # Formatiere Output
            result = f"📁 SelfAI Python Files ({len(py_files)} Dateien)"
            if subdirectory:
                result += f" in '{subdirectory}/':\n\n"
            else:
                result += ":\n\n"

            # Gruppiere nach Verzeichnis
            by_dir = {}
            for f in py_files:
                rel_path = f.relative_to(selfai_root)
                dir_name = str(rel_path.parent) if rel_path.parent != Path(".") else "root"

                if dir_name not in by_dir:
                    by_dir[dir_name] = []
                by_dir[dir_name].append(rel_path.name)

            # Output
            for dir_name in sorted(by_dir.keys()):
                if dir_name == "root":
                    result += "📦 selfai/ (root):\n"
                else:
                    result += f"📦 selfai/{dir_name}/:\n"

                for filename in sorted(by_dir[dir_name]):
                    result += f"   - {filename}\n"
                result += "\n"

            result += f"\n💡 Tipp: Nutze 'read_selfai_code' um eine Datei zu lesen."
            return result

        except Exception as e:
            return f"❌ Fehler beim Auflisten: {str(e)}"


class ReadSelfAICodeTool:
    """Lese Source-Code einer spezifischen SelfAI Datei."""

    @property
    def name(self) -> str:
        return "read_selfai_code"

    @property
    def description(self) -> str:
        return (
            "Lese den vollständigen Source-Code einer SelfAI Python-Datei. "
            "Gib den relativen Pfad zur Datei an (z.B. 'core/execution_dispatcher.py'). "
            "Security: Zugriff nur auf selfai/**/*.py erlaubt."
        )

    @property
    def inputs(self) -> Dict[str, Any]:
        return {
            "file_path": {
                "type": "string",
                "description": "Relativer Pfad zur Datei (z.B. 'core/execution_dispatcher.py' oder 'tools/tool_registry.py')"
            }
        }

    def forward(self, file_path: str) -> str:
        """
        Lese eine Python-Datei aus dem SelfAI Codebase.

        Args:
            file_path: Relativer Pfad zur Datei (z.B. "core/agent.py")

        Returns:
            Dateiinhalt oder Fehlermeldung
        """
        try:
            # Finde SelfAI root
            selfai_root = Path(__file__).parent.parent  # tools/ -> selfai/

            # Konstruiere vollständigen Pfad
            full_path = selfai_root / file_path

            # Security Check 1: Muss innerhalb selfai/ liegen
            try:
                full_path.resolve().relative_to(selfai_root.resolve())
            except ValueError:
                return (
                    f"❌ SECURITY ERROR: Zugriff verweigert!\n"
                    f"Datei muss innerhalb selfai/ liegen.\n"
                    f"Angefragt: {file_path}"
                )

            # Security Check 2: Muss .py Datei sein
            if full_path.suffix != ".py":
                return (
                    f"❌ Fehler: Nur Python-Dateien (.py) erlaubt!\n"
                    f"Angefragt: {file_path}\n"
                    f"Endung: {full_path.suffix}"
                )

            # Check 3: Datei muss existieren
            if not full_path.exists():
                return (
                    f"❌ Fehler: Datei existiert nicht!\n"
                    f"Gesucht: {file_path}\n"
                    f"Vollständiger Pfad: {full_path}\n\n"
                    f"💡 Tipp: Nutze 'list_selfai_files' um verfügbare Dateien zu sehen."
                )

            # Lese Datei
            content = full_path.read_text(encoding="utf-8")

            # Formatiere Output
            rel_path = full_path.relative_to(selfai_root)
            lines = content.count("\n") + 1

            result = (
                f"📄 File: selfai/{rel_path}\n"
                f"📏 Lines: {lines}\n"
                f"{'=' * 60}\n\n"
                f"{content}\n\n"
                f"{'=' * 60}\n"
                f"✅ Ende von selfai/{rel_path}"
            )

            return result

        except Exception as e:
            return f"❌ Fehler beim Lesen: {str(e)}"


class SearchSelfAICodeTool:
    """Suche nach Pattern/Begriff im SelfAI Source-Code."""

    @property
    def name(self) -> str:
        return "search_selfai_code"

    @property
    def description(self) -> str:
        return (
            "Suche nach einem Begriff oder Pattern im gesamten SelfAI Source-Code. "
            "Nutze dies um Funktionen, Klassen oder Konzepte zu finden. "
            "Beispiele: 'class ExecutionDispatcher', 'def plan(', 'DPPM', 'tool_registry'."
        )

    @property
    def inputs(self) -> Dict[str, Any]:
        return {
            "pattern": {
                "type": "string",
                "description": "Suchbegriff oder Pattern (z.B. 'class Agent', 'def execute', 'IDENTITY_CORE')"
            },
            "file_extension": {
                "type": "string",
                "description": "Optional: Datei-Endung (default: 'py')",
                "nullable": True
            }
        }

    def forward(self, pattern: str, file_extension: str = "py") -> str:
        """
        Suche nach Pattern im SelfAI Codebase.

        Args:
            pattern: Suchbegriff (z.B. "class Agent")
            file_extension: Datei-Endung (default: "py")

        Returns:
            Suchergebnisse mit Datei und Zeilennummer
        """
        try:
            # Finde SelfAI root
            selfai_root = Path(__file__).parent.parent

            # Nutze grep für schnelle Suche
            result = subprocess.run(
                [
                    "grep",
                    "-rn",  # recursive + line numbers
                    "--include", f"*.{file_extension}",
                    pattern,
                    str(selfai_root)
                ],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0 and result.stdout:
                # Parse und formatiere Output
                lines = result.stdout.strip().split("\n")

                output = f"🔍 Suchergebnisse für '{pattern}' ({len(lines)} Treffer):\n\n"

                for line in lines[:50]:  # Limitiere auf erste 50 Treffer
                    # Format: /full/path/file.py:123:code
                    if ":" in line:
                        parts = line.split(":", 2)
                        if len(parts) >= 3:
                            file_path = Path(parts[0])
                            line_num = parts[1]
                            code = parts[2]

                            # Relative path
                            try:
                                rel_path = file_path.relative_to(selfai_root)
                                output += f"📍 selfai/{rel_path}:{line_num}\n"
                                output += f"   {code.strip()}\n\n"
                            except ValueError:
                                # Falls Pfad außerhalb selfai/ (sollte nicht passieren)
                                continue

                if len(lines) > 50:
                    output += f"\n⚠️  Nur erste 50 von {len(lines)} Treffern angezeigt.\n"

                output += f"\n💡 Tipp: Nutze 'read_selfai_code' um vollständige Datei zu lesen."
                return output

            else:
                return f"❌ Nichts gefunden für: '{pattern}'\n\n💡 Tipp: Nutze 'list_selfai_files' um verfügbare Dateien zu sehen."

        except subprocess.TimeoutExpired:
            return "❌ Fehler: Suche dauerte zu lange (Timeout nach 10s)"
        except FileNotFoundError:
            return "❌ Fehler: 'grep' command nicht gefunden. Installiere grep oder nutze andere Tools."
        except Exception as e:
            return f"❌ Fehler bei der Suche: {str(e)}"


# Tool instances (für smolagents compatibility)
list_selfai_files_tool = ListSelfAIFilesTool()
read_selfai_code_tool = ReadSelfAICodeTool()
search_selfai_code_tool = SearchSelfAICodeTool()
