"""
Bash Wrapper Tools für SelfAI
=============================

Einfache Wrapper für Shell-Kommandos (ls, cat, grep), die als Python-Tools
registriert und von MiniMax via CustomAgentLoop aufgerufen werden können.

Diese Tools ermöglichen MiniMax, Dateien zu lesen, zu suchen und zu listen,
ohne dass ein separater API-Server nötig ist.

Latenz pro Tool-Call: ~5-20ms
Komplexität: 1 Datei, 30min Implementierung
"""

import subprocess
import json
from pathlib import Path
from typing import Optional

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def tool_ls(subdir: str = ".", pattern: str = "*", max_results: int = 20) -> str:
    """
    Liste Dateien im Projekt auf (analog zu bash ls / find).

    Args:
        subdir: Unterordner relativ zum Projektroot (Standard: ".")
        pattern: Glob-Muster für Dateien (Standard: "*")
        max_results: Maximale Anzahl der zurückgegebenen Dateien (Standard: 20)

    Returns:
        JSON-String mit Liste der gefundenen Dateien

    Example:
        tool_ls(subdir="selfai", pattern="*.py", max_results=10)
        # Ergebnis: '{"files": ["selfai/selfai.py", "selfai/core/agent.py"], "count": 2}'
    """
    base = PROJECT_ROOT / subdir
    files = []

    try:
        for p in base.rglob(pattern):
            if p.is_file():
                try:
                    rel_path = str(p.relative_to(PROJECT_ROOT))
                    files.append(rel_path)
                except ValueError:
                    files.append(str(p))
                if len(files) >= max_results:
                    break
    except Exception as e:
        return json.dumps(
            {"error": f"Fehler beim Auflisten: {e}", "files": [], "count": 0}
        )

    return json.dumps(
        {"files": files, "count": len(files), "subdir": subdir, "pattern": pattern}
    )


def tool_cat(path: str, max_chars: int = 4000) -> str:
    """
    Lese Datei-Inhalt (analog zu bash cat / head).

    Args:
        path: Pfad zur Datei relativ zum Projektroot
        max_chars: Maximale Anzahl der Zeichen (Standard: 4000)

    Returns:
        JSON-String mit Dateipfad und Inhalt

    Example:
        tool_cat(path="selfai/selfai.py", max_chars=1000)
        # Ergebnis: '{"path": "selfai/selfai.py", "content": "...", "truncated": true}'
    """
    file_path = PROJECT_ROOT / path

    if not file_path.exists():
        return json.dumps(
            {
                "error": f"Datei nicht gefunden: {path}",
                "path": path,
                "content": "",
                "truncated": False,
            }
        )

    if not file_path.is_file():
        return json.dumps(
            {
                "error": f"Pfad ist keine Datei: {path}",
                "path": path,
                "content": "",
                "truncated": False,
            }
        )

    try:
        content = file_path.read_text(encoding="utf-8")
        truncated = len(content) > max_chars
        if truncated:
            content = content[:max_chars]

        return json.dumps(
            {
                "path": path,
                "content": content,
                "truncated": truncated,
                "full_length": len(file_path.read_text(encoding="utf-8"))
                if truncated
                else len(content),
            }
        )
    except Exception as e:
        return json.dumps(
            {
                "error": f"Fehler beim Lesen der Datei: {e}",
                "path": path,
                "content": "",
                "truncated": False,
            }
        )


def tool_grep(
    query: str, pattern: str = "*", max_results: int = 20, context_lines: int = 2
) -> str:
    """
    Suche nach Text in Dateien (analog zu bash grep).

    Args:
        query: Suchbegriff (Groß-/Kleinschreibung wird ignoriert)
        pattern: Glob-Muster für Dateien (Standard: "*")
        max_results: Maximale Anzahl der Treffer (Standard: 20)
        context_lines: Anzahl der Kontext-Zeilen um jeden Treffer (Standard: 2)

    Returns:
        JSON-String mit Liste der Treffer

    Example:
        tool_grep(query="def main", pattern="*.py", max_results=10)
        # Ergebnis: '{"matches": [{"file": "...", "line": 10, "content": "def main():"}], "count": 1}'
    """
    matches = []
    query_lower = query.lower()

    try:
        for p in PROJECT_ROOT.rglob(pattern):
            if not p.is_file():
                continue

            try:
                text = p.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue

            if query_lower not in text.lower():
                continue

            lines = text.splitlines()
            for i, line in enumerate(lines, start=1):
                if query_lower in line.lower():
                    # Kontext sammeln
                    start_line = max(0, i - context_lines - 1)
                    end_line = min(len(lines), i + context_lines)
                    context = lines[start_line:end_line]

                    try:
                        rel_path = str(p.relative_to(PROJECT_ROOT))
                    except ValueError:
                        rel_path = str(p)

                    matches.append(
                        {
                            "file": rel_path,
                            "line": i,
                            "content": line.strip(),
                            "context": context,
                        }
                    )

                    if len(matches) >= max_results:
                        break

            if len(matches) >= max_results:
                break

    except Exception as e:
        return json.dumps(
            {
                "error": f"Fehler bei der Suche: {e}",
                "matches": [],
                "count": 0,
                "query": query,
            }
        )

    return json.dumps(
        {"query": query, "matches": matches, "count": len(matches), "pattern": pattern}
    )


def tool_find(
    subdir: str = ".",
    name_pattern: Optional[str] = None,
    type_filter: Optional[str] = None,
    max_results: int = 20,
) -> str:
    """
    Erweiterte Dateisuche (analog zu bash find).

    Args:
        subdir: Start-Verzeichnis relativ zum Projektroot (Standard: ".")
        name_pattern: Optionaler Name-Filter (z.B. "*.py")
        type_filter: Optionaler Typ-Filter ("f" für Dateien, "d" für Verzeichnisse)
        max_results: Maximale Anzahl der Ergebnisse (Standard: 20)

    Returns:
        JSON-String mit Liste der gefundenen Pfade

    Example:
        tool_find(subdir="selfai", name_pattern="*.py", type_filter="f", max_results=10)
    """
    base = PROJECT_ROOT / subdir
    results = []

    try:
        cmd = ["find", str(base), "-type", type_filter or "f"]

        if name_pattern:
            cmd.extend(["-name", name_pattern])

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

        for line in result.stdout.strip().split("\n"):
            if line and len(results) < max_results:
                try:
                    path = str(Path(line).relative_to(PROJECT_ROOT))
                    results.append(path)
                except ValueError:
                    results.append(line)

    except subprocess.TimeoutExpired:
        return json.dumps({"error": "Timeout bei der Suche", "results": [], "count": 0})
    except Exception as e:
        return json.dumps(
            {"error": f"Fehler bei der Suche: {e}", "results": [], "count": 0}
        )

    return json.dumps(
        {
            "results": results,
            "count": len(results),
            "subdir": subdir,
            "name_pattern": name_pattern,
            "type_filter": type_filter,
        }
    )


def tool_wc(path: Optional[str] = None, pattern: str = "*") -> str:
    """
    Zähle Zeilen, Wörter und Zeichen (analog zu bash wc).

    Args:
        path: Optionaler Dateipfad. Wenn nicht angegeben, werden alle passenden Dateien gezählt.
        pattern: Glob-Muster wenn path=None (Standard: "*")

    Returns:
        JSON-String mit Statistiken

    Example:
        tool_wc(path="selfai/selfai.py")
        # Ergebnis: '{"path": "selfai/selfai.py", "lines": 100, "words": 500, "chars": 3000}'
    """
    if path:
        file_path = PROJECT_ROOT / path
        if not file_path.exists() or not file_path.is_file():
            return json.dumps({"error": "Datei nicht gefunden", "path": path})

        content = file_path.read_text(encoding="utf-8")
        lines = len(content.splitlines())
        words = len(content.split())
        chars = len(content)

        return json.dumps(
            {"path": path, "lines": lines, "words": words, "chars": chars}
        )
    else:
        total_lines = 0
        total_words = 0
        total_chars = 0
        files = []

        for p in PROJECT_ROOT.rglob(pattern):
            if p.is_file():
                try:
                    content = p.read_text(encoding="utf-8")
                    total_lines += len(content.splitlines())
                    total_words += len(content.split())
                    total_chars += len(content)
                    files.append(str(p.relative_to(PROJECT_ROOT)))
                except Exception:
                    continue

        return json.dumps(
            {
                "pattern": pattern,
                "files_count": len(files),
                "total_lines": total_lines,
                "total_words": total_words,
                "total_chars": total_chars,
            }
        )
