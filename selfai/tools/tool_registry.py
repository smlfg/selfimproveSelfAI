from __future__ import annotations

import json
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from datetime import datetime
from typing import Any, Callable, Dict, List
from uuid import uuid4

try:
    from smolagents.tools import Tool as SmolTool  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    SmolTool = None  # type: ignore

from selfai.tools.aider_tool import run_aider_task, run_aider_architect
from selfai.tools.openhands_tool import (
    run_openhands_task,
    run_openhands_architect,
    compare_coding_tools
)
from selfai.tools.introspection_tools import (
    ListSelfAIFilesTool,
    ReadSelfAICodeTool,
    SearchSelfAICodeTool,
)


@dataclass
class RegisteredTool:
    """
    Wrapper around a plain Python callable that exposes metadata and lazily
    constructs a `smolagents` Tool instance when required.
    """

    name: str
    func: Callable[..., Any]
    schema: Dict[str, Any]
    description: str = ""
    output_type: str = "string"
    _smol_tool: Any = field(default=None, init=False, repr=False)

    def run(self, **kwargs: Any) -> Any:
        """Execute the underlying Python function."""
        return self.func(**kwargs)

    def to_smol_tool(self) -> Any:
        """
        Convert this tool into a `smolagents.tools.Tool` instance.

        Returns:
            Tool: A smolagents-compatible tool instance.

        Raises:
            ImportError: If smolagents is not installed.
        """
        if SmolTool is None:
            raise ImportError(
                "smolagents is not installed. Install it to enable tool execution."
            )
        if self._smol_tool is not None:
            return self._smol_tool

        schema = self.schema or {}
        tool_name = self.name
        tool_description = schema.get("description") or self.description or tool_name
        parameters = schema.get("parameters", {})
        properties = parameters.get("properties", {}) if isinstance(parameters, dict) else {}

        func = self.func
        tool_output_type = self.output_type or "string"

        class _SmolTool(SmolTool):  # type: ignore[misc]
            name: str = tool_name
            description: str = tool_description
            inputs: dict[str, dict[str, Any]] = properties
            output_type: str = tool_output_type
            skip_forward_signature_validation = True

            def forward(self, *args: Any, **kwargs: Any) -> Any:
                if args and kwargs:
                    raise TypeError(
                        f"Tool '{tool_name}' expects keyword arguments, got positional and keyword arguments."
                    )
                if args:
                    return func(*args)
                return func(**kwargs)

        self._smol_tool = _SmolTool()
        return self._smol_tool


# --- Tool Definitions ---

def get_current_weather(location: str, unit: str = "celsius") -> str:
    """
    Return a dummy weather report.

    Args:
        location: City and optional region, e.g. "San Francisco, CA".
        unit: Temperature unit, either "celsius" or "fahrenheit".

    Returns:
        JSON-formatted weather payload with `location`, `temperature`, and `unit`.
    """
    if "tokyo" in location.lower():
        return json.dumps({"location": "Tokyo", "temperature": "10", "unit": unit})
    if "san francisco" in location.lower():
        return json.dumps({"location": "San Francisco", "temperature": "72", "unit": unit})
    if "paris" in location.lower():
        return json.dumps({"location": "Paris", "temperature": "22", "unit": unit})
    return json.dumps({"location": location, "temperature": "unknown", "unit": unit})


PROJECT_ROOT = Path(__file__).resolve().parents[2]
TRAIN_DATA_PATH = PROJECT_ROOT / "data" / "train_connections.json"
CALENDAR_PATH = PROJECT_ROOT / "data" / "calendar_events.json"


@lru_cache(maxsize=1)
def _load_train_data() -> list[dict[str, Any]]:
    if not TRAIN_DATA_PATH.is_file():
        return []
    try:
        return json.loads(TRAIN_DATA_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []


def find_train_connections(
    origin: str,
    destination: str,
    date: str | None = None,
    max_results: int = 3,
) -> str:
    """
    Lookup sample train connections between two stations.

    Args:
        origin: Abfahrtsbahnhof (z.B. "Mainz Hbf").
        destination: Zielbahnhof (z.B. "Worms Hbf").
        date: Optionales Datum im Format YYYY-MM-DD zur Filterung.
        max_results: Anzahl der zurückzugebenden Verbindungen (1-5 empfohlen).

    Returns:
        JSON string with keys ``matches`` (list) and ``count``.
    """
    data = _load_train_data()
    if not data:
        return json.dumps(
            {
                "matches": [],
                "count": 0,
                "note": "Keine Fahrplandaten im lokalen Datensatz gefunden.",
            }
        )

    origin_lower = origin.strip().lower()
    destination_lower = destination.strip().lower()
    date_filtered = date.strip() if isinstance(date, str) and date.strip() else None

    matches: list[dict[str, Any]] = []
    limit = max(1, int(max_results))

    for entry in data:
        if entry.get("origin", "").lower() != origin_lower:
            continue
        if entry.get("destination", "").lower() != destination_lower:
            continue
        if date_filtered and entry.get("date") != date_filtered:
            continue
        matches.append(entry)
        if len(matches) >= limit:
            break

    return json.dumps({"matches": matches, "count": len(matches)})

def _resolve_project_path(relative_path: str) -> Path:
    candidate = (PROJECT_ROOT / (relative_path or ".")).resolve()
    project_root_resolved = PROJECT_ROOT.resolve()
    if project_root_resolved == candidate or project_root_resolved in candidate.parents:
        return candidate
    raise ValueError("Pfad liegt außerhalb des Projektverzeichnisses.")


def list_project_files(
    subdir: str = ".",
    pattern: str = "*",
    max_results: int = 20,
) -> str:
    try:
        base_dir = _resolve_project_path(subdir)
    except ValueError as exc:
        return json.dumps({"error": str(exc), "files": [], "count": 0})

    limit = max(1, int(max_results or 20))
    files: list[str] = []
    for path in base_dir.rglob(pattern or "*"):
        if not path.is_file():
            continue
        if len(files) >= limit:
            break
        try:
            files.append(str(path.relative_to(PROJECT_ROOT)))
        except ValueError:
            continue

    return json.dumps({"files": files, "count": len(files)})


def read_project_file(
    path: str,
    max_chars: int = 4000,
    strip: bool = False,
) -> str:
    try:
        file_path = _resolve_project_path(path)
    except ValueError as exc:
        return json.dumps({"error": str(exc), "content": ""})

    if not file_path.is_file():
        return json.dumps({"error": "Datei wurde nicht gefunden.", "content": ""})

    try:
        content = file_path.read_text(encoding="utf-8")
    except OSError as exc:
        return json.dumps({"error": f"Datei konnte nicht gelesen werden: {exc}", "content": ""})

    limit = max(1, int(max_chars or 4000))
    snippet = content[:limit]
    if strip:
        snippet = snippet.strip()

    return json.dumps(
        {"path": str(file_path.relative_to(PROJECT_ROOT)), "content": snippet, "truncated": len(content) > limit}
    )


def search_project_files(
    query: str,
    pattern: str = "*.md",
    max_results: int = 20,
) -> str:
    if not query:
        return json.dumps({"error": "Leerer Suchbegriff.", "matches": [], "count": 0})

    results: list[dict[str, Any]] = []
    limit = max(1, int(max_results or 20))
    lowered_query = query.lower()

    for path in PROJECT_ROOT.rglob(pattern or "*"):
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue

        if lowered_query not in text.lower():
            continue

        lines = []
        for index, line in enumerate(text.splitlines(), start=1):
            if lowered_query in line.lower():
                lines.append({"line": index, "text": line.strip()})
                if len(lines) >= 3:
                    break

        try:
            relative = str(path.relative_to(PROJECT_ROOT))
        except ValueError:
            relative = str(path)

        results.append({"file": relative, "matches": lines})
        if len(results) >= limit:
            break

    return json.dumps({"matches": results, "count": len(results)})


@lru_cache(maxsize=1)
def _load_calendar_events() -> list[dict[str, Any]]:
    if not CALENDAR_PATH.is_file():
        return []
    try:
        return json.loads(CALENDAR_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []


def _save_calendar_events(events: list[dict[str, Any]]) -> None:
    try:
        CALENDAR_PATH.write_text(
            json.dumps(events, indent=2, ensure_ascii=False), encoding="utf-8"
        )
    except OSError:
        pass


def _normalize_date(value: str | None) -> str | None:
    if not value:
        return None
    raw = value.strip()
    if not raw:
        return None
    candidates = ["%Y-%m-%d", "%d.%m.%Y", "%d.%m.%y", "%d.%m."]
    for fmt in candidates:
        try:
            parsed = datetime.strptime(raw, fmt)
            if fmt == "%d.%m.":
                parsed = parsed.replace(year=datetime.now().year)
            return parsed.strftime("%Y-%m-%d")
        except ValueError:
            continue
    return raw  # fallback – besser als gar nichts


def _normalize_time(value: str | None) -> str | None:
    if not value:
        return None
    raw = value.strip()
    if not raw:
        return None
    for fmt in ("%H:%M", "%H.%M", "%H%M"):
        try:
            return datetime.strptime(raw, fmt).strftime("%H:%M")
        except ValueError:
            continue
    return raw


def add_calendar_event(
    title: str,
    date: str,
    start_time: str | None = None,
    end_time: str | None = None,
    location: str | None = None,
    notes: str | None = None,
) -> str:
    events = _load_calendar_events().copy()
    normalized_date = _normalize_date(date)
    normalized_start = _normalize_time(start_time)
    normalized_end = _normalize_time(end_time)

    event = {
        "id": uuid4().hex,
        "title": title.strip() if title else "(ohne Titel)",
        "date": normalized_date,
        "start_time": normalized_start,
        "end_time": normalized_end,
        "location": (location or "").strip() or None,
        "notes": (notes or "").strip() or None,
        "created_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
    }

    events.append(event)
    _save_calendar_events(events)
    _load_calendar_events.cache_clear()

    return json.dumps({"status": "added", "event": event})


def list_calendar_events(
    date: str | None = None,
    limit: int | None = None,
    include_past: bool = True,
) -> str:
    events = _load_calendar_events()
    target_date = _normalize_date(date) if date else None

    include = include_past
    if isinstance(include_past, str):
        include = include_past.strip().lower() not in {"false", "0", "nein", "no"}

    limit_int: int | None = None
    if limit is not None:
        try:
            limit_int = max(1, int(limit))
        except (TypeError, ValueError):
            limit_int = None

    filtered: list[dict[str, Any]] = []
    today_iso = datetime.utcnow().strftime("%Y-%m-%d")

    for event in events:
        event_date = event.get("date")
        if target_date and event_date != target_date:
            continue
        if not include and event_date and event_date < today_iso:
            continue
        filtered.append(event)
        if limit_int and len(filtered) >= limit_int:
            break

    return json.dumps({"events": filtered, "count": len(filtered)})


# --- Tool Registry ---

_TOOL_REGISTRY: Dict[str, RegisteredTool] = {}


def register_tool(tool: RegisteredTool) -> None:
    """Register a tool in the central registry."""
    _TOOL_REGISTRY[tool.name] = tool


register_tool(
    RegisteredTool(
        name="get_current_weather",
        func=get_current_weather,
        schema={
            "name": "get_current_weather",
            "description": "Get the current weather in a given location.",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "City and region, e.g. 'San Francisco, CA'.",
                    },
                    "unit": {
                        "type": "string",
                        "enum": ["celsius", "fahrenheit"],
                        "description": "Temperature unit.",
                    },
                },
                "required": ["location"],
            },
        },
        output_type="string",
    )
)

register_tool(
    RegisteredTool(
        name="find_train_connections",
        func=find_train_connections,
        schema={
            "name": "find_train_connections",
            "description": "Liefert Beispiel-Bahnverbindungen zwischen zwei Stationen aus einem lokalen Datensatz.",
            "parameters": {
                "type": "object",
                "properties": {
                    "origin": {
                        "type": "string",
                        "description": "Startbahnhof, z. B. 'Mainz Hbf'.",
                    },
                    "destination": {
                        "type": "string",
                        "description": "Zielbahnhof, z. B. 'Worms Hbf'.",
                    },
                    "date": {
                        "type": "string",
                        "description": "Optionales Datum im Format YYYY-MM-DD.",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximale Anzahl an Verbindungen (Standard 3).",
                    },
                },
                "required": ["origin", "destination"],
            },
        },
        output_type="string",
    )
)

register_tool(
    RegisteredTool(
        name="add_calendar_event",
        func=add_calendar_event,
        schema={
            "name": "add_calendar_event",
            "description": "Speichert einen neuen Kalendereintrag im lokalen SelfAI-Kalender.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Titel oder Anlass, z. B. 'Geburtstag Max'.",
                    },
                    "date": {
                        "type": "string",
                        "description": "Datum (preferiert YYYY-MM-DD, dd.mm oder dd.mm.).",
                    },
                    "start_time": {
                        "type": "string",
                        "description": "Optionale Startzeit (HH:MM).",
                    },
                    "end_time": {
                        "type": "string",
                        "description": "Optionale Endzeit (HH:MM).",
                    },
                    "location": {
                        "type": "string",
                        "description": "Ort oder Treffpunkt.",
                    },
                    "notes": {
                        "type": "string",
                        "description": "Zusätzliche Notizen oder Hinweise.",
                    },
                },
                "required": ["title", "date"],
            },
        },
        output_type="string",
    )
)

register_tool(
    RegisteredTool(
        name="list_calendar_events",
        func=list_calendar_events,
        schema={
            "name": "list_calendar_events",
            "description": "Listet lokale Kalendereinträge für ein Datum oder Zeitfenster.",
            "parameters": {
                "type": "object",
                "properties": {
                    "date": {
                        "type": "string",
                        "description": "Optionales Datum (YYYY-MM-DD oder dd.mm).",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximale Anzahl der zurückgegebenen Einträge.",
                    },
                    "include_past": {
                        "type": "boolean",
                        "description": "Vergangene Einträge einschließen (Standard: true).",
                    },
                },
            },
        },
        output_type="string",
    )
)

register_tool(
    RegisteredTool(
        name="list_project_files",
        func=list_project_files,
        schema={
            "name": "list_project_files",
            "description": "Listet Dateien innerhalb des Projekts anhand eines Musters.",
            "parameters": {
                "type": "object",
                "properties": {
                    "subdir": {
                        "type": "string",
                        "description": "Optionaler Unterordner relativ zum Projektroot.",
                    },
                    "pattern": {
                        "type": "string",
                        "description": "Glob-Muster, z. B. '*.py'.",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximale Anzahl der aufzulistenden Dateien.",
                    },
                },
            },
        },
        output_type="string",
    )
)

register_tool(
    RegisteredTool(
        name="read_project_file",
        func=read_project_file,
        schema={
            "name": "read_project_file",
            "description": "Liest den Beginn einer Textdatei aus dem Projekt (UTF-8).",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Pfad relativ zum Projektroot.",
                    },
                    "max_chars": {
                        "type": "integer",
                        "description": "Maximale Anzahl der Zeichen, Standard 4000.",
                    },
                    "strip": {
                        "type": "boolean",
                        "description": "Vor Ausgabe führende/abschließende Leerzeichen entfernen.",
                    },
                },
                "required": ["path"],
            },
        },
        output_type="string",
    )
)

register_tool(
    RegisteredTool(
        name="search_project_files",
        func=search_project_files,
        schema={
            "name": "search_project_files",
            "description": "Durchsucht Projektdateien nach einem Suchbegriff und gibt Trefferzeilen zurück.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Suchbegriff (Groß-/Kleinschreibung wird ignoriert).",
                    },
                    "pattern": {
                        "type": "string",
                        "description": "Dateimuster, z. B. '*.md'.",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximale Anzahl der Dateien im Ergebnis.",
                    },
                },
                "required": ["query"],
            },
        },
        output_type="string",
    )
)

register_tool(
    RegisteredTool(
        name="find_train_connections",
        func=find_train_connections,
        schema={
            "name": "find_train_connections",
            "description": "Liefert Beispiel-Bahnverbindungen zwischen zwei Stationen aus einem lokalen Datensatz.",
            "parameters": {
                "type": "object",
                "properties": {
                    "origin": {
                        "type": "string",
                        "description": "Startbahnhof, z. B. 'Mainz Hbf'.",
                    },
                    "destination": {
                        "type": "string",
                        "description": "Zielbahnhof, z. B. 'Worms Hbf'.",
                    },
                    "date": {
                        "type": "string",
                        "description": "Optionales Datum im Format YYYY-MM-DD.",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximale Anzahl an Verbindungen (Standard 3).",
                    },
                },
                "required": ["origin", "destination"],
            },
        },
        output_type="string",
    )
)
# --- Aider AI Coding Assistant Tools ---

register_tool(
    RegisteredTool(
        name="run_aider_task",
        func=run_aider_task,
        schema={
            "name": "run_aider_task",
            "description": "Execute an AI-powered coding task using Aider with MiniMax. Can edit files, add features, fix bugs, refactor code, etc.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_description": {
                        "type": "string",
                        "description": "Detailed description of the coding task (e.g., 'Add error handling to parse_config function in src/config.py')",
                    },
                    "files": {
                        "type": "string",
                        "description": "Comma-separated list of file paths to edit (e.g., 'src/main.py,tests/test_main.py'). Leave empty for Aider to decide.",
                    },
                    "model": {
                        "type": "string",
                        "description": "LLM model to use (default: openai/MiniMax-M2)",
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "Maximum execution time in seconds (default: 180)",
                    },
                },
                "required": ["task_description"],
            },
        },
        output_type="string",
    )
)

register_tool(
    RegisteredTool(
        name="run_aider_architect",
        func=run_aider_architect,
        schema={
            "name": "run_aider_architect",
            "description": "Consult Aider in architect mode for code design advice (read-only, no file edits). Get recommendations on architecture, design patterns, best practices.",
            "parameters": {
                "type": "object",
                "properties": {
                    "design_question": {
                        "type": "string",
                        "description": "Architectural question or design problem (e.g., 'How should I structure a REST API with authentication?')",
                    },
                    "context_files": {
                        "type": "string",
                        "description": "Comma-separated list of files for context (optional, e.g., 'src/api.py,src/models.py')",
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "Maximum execution time in seconds (default: 120)",
                    },
                },
                "required": ["design_question"],
            },
        },
        output_type="string",
    )
)

# --- OpenHands AI Coding Assistant Tools ---

register_tool(
    RegisteredTool(
        name="run_openhands_task",
        func=run_openhands_task,
        schema={
            "name": "run_openhands_task",
            "description": "Execute autonomous coding task using OpenHands (formerly OpenDevin). Better than Aider for complex multi-file tasks, system-level changes, and autonomous debugging. Can explore codebase independently.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_description": {
                        "type": "string",
                        "description": "Detailed description of the coding task (e.g., 'Implement user authentication system with JWT tokens')",
                    },
                    "files": {
                        "type": "string",
                        "description": "Comma-separated list of files to focus on (optional, e.g., 'src/auth.py,tests/test_auth.py'). OpenHands can discover files autonomously if not specified.",
                    },
                    "model": {
                        "type": "string",
                        "description": "LLM model to use (default: openai/MiniMax-M2, alternatives: anthropic/claude-3-5-sonnet-20241022)",
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "Maximum execution time in seconds (default: 300)",
                    },
                    "max_iterations": {
                        "type": "integer",
                        "description": "Max agent iterations for task completion (default: 10)",
                    },
                },
                "required": ["task_description"],
            },
        },
        output_type="string",
    )
)

register_tool(
    RegisteredTool(
        name="run_openhands_architect",
        func=run_openhands_architect,
        schema={
            "name": "run_openhands_architect",
            "description": "Consult OpenHands for architectural analysis and design recommendations (read-only). Better than Aider architect for system-level architecture and comprehensive codebase analysis.",
            "parameters": {
                "type": "object",
                "properties": {
                    "design_question": {
                        "type": "string",
                        "description": "Architectural question or design problem (e.g., 'How should I design the microservices architecture?')",
                    },
                    "context_files": {
                        "type": "string",
                        "description": "Comma-separated list of files for context (optional, e.g., 'src/api/,src/models/')",
                    },
                    "model": {
                        "type": "string",
                        "description": "LLM model (default: anthropic/claude-3-5-sonnet-20241022 - best for architecture)",
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "Maximum execution time in seconds (default: 180)",
                    },
                },
                "required": ["design_question"],
            },
        },
        output_type="string",
    )
)

register_tool(
    RegisteredTool(
        name="compare_coding_tools",
        func=compare_coding_tools,
        schema={
            "name": "compare_coding_tools",
            "description": "Intelligently recommend whether to use Aider or OpenHands for a coding task based on complexity and requirements. Helps choose the most efficient tool.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_description": {
                        "type": "string",
                        "description": "Description of the coding task to be performed",
                    },
                    "complexity": {
                        "type": "string",
                        "description": "Estimated task complexity: 'simple', 'medium', or 'complex' (default: 'medium')",
                    },
                },
                "required": ["task_description"],
            },
        },
        output_type="string",
    )
)

# --- Self-Inspection Tools (Introspection) ---

# Register introspection tools as smolagents-compatible
list_selfai_files_tool_instance = ListSelfAIFilesTool()
read_selfai_code_tool_instance = ReadSelfAICodeTool()
search_selfai_code_tool_instance = SearchSelfAICodeTool()

register_tool(
    RegisteredTool(
        name="list_selfai_files",
        func=list_selfai_files_tool_instance.forward,
        schema={
            "name": "list_selfai_files",
            "description": list_selfai_files_tool_instance.description,
            "parameters": {
                "type": "object",
                "properties": list_selfai_files_tool_instance.inputs,
            },
        },
        output_type="string",
    )
)

register_tool(
    RegisteredTool(
        name="read_selfai_code",
        func=read_selfai_code_tool_instance.forward,
        schema={
            "name": "read_selfai_code",
            "description": read_selfai_code_tool_instance.description,
            "parameters": {
                "type": "object",
                "properties": read_selfai_code_tool_instance.inputs,
                "required": ["file_path"],
            },
        },
        output_type="string",
    )
)

register_tool(
    RegisteredTool(
        name="search_selfai_code",
        func=search_selfai_code_tool_instance.forward,
        schema={
            "name": "search_selfai_code",
            "description": search_selfai_code_tool_instance.description,
            "parameters": {
                "type": "object",
                "properties": search_selfai_code_tool_instance.inputs,
                "required": ["pattern"],
            },
        },
        output_type="string",
    )
)


# --- Accessor Functions ---

def get_tool(tool_name: str) -> RegisteredTool | None:
    """Retrieve a tool by name."""
    return _TOOL_REGISTRY.get(tool_name)


def get_all_tool_schemas() -> List[Dict[str, Any]]:
    """Return the JSON schemas of all registered tools."""
    return [tool.schema for tool in _TOOL_REGISTRY.values()]


def list_all_tools() -> List[Dict[str, str]]:
    """Return a list of all registered tools with name and description."""
    tools = []
    for tool in _TOOL_REGISTRY.values():
        tools.append({
            "name": tool.name,
            "description": tool.schema.get("description", "No description available")
        })
    return sorted(tools, key=lambda x: x["name"])


def get_tools_for_agent() -> List[Any]:
    """
    Get all registered tools converted to smolagents format.

    Returns:
        List of smolagents Tool instances ready for ToolCallingAgent

    Raises:
        ImportError: If smolagents is not installed
    """
    smol_tools = []
    for tool in _TOOL_REGISTRY.values():
        try:
            smol_tool = tool.to_smol_tool()
            smol_tools.append(smol_tool)
        except Exception as e:
            # Log but don't fail - skip problematic tools
            print(f"Warning: Could not convert tool '{tool.name}' to smolagents format: {e}")
            continue

    return smol_tools
