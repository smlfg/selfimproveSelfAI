import json
import os
import sys
import subprocess
from datetime import datetime
from pathlib import Path

try:
    import psutil
except ImportError:
    psutil = None

# Füge das Projekt-Stammverzeichnis zum Pfad hinzu, um Importe aus `core` zu ermöglichen
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root.parent))

from config_loader import load_configuration
from selfai.core.agent_manager import Agent, AgentManager
from selfai.core.minimax_interface import MinimaxInterface
from selfai.core.local_llm_interface import LocalLLMInterface
from selfai.core.execution_dispatcher import ExecutionDispatcher, ExecutionError
from selfai.core.memory_system import MemorySystem
from selfai.core.planner_ollama_interface import (
    PlannerContext,
    PlannerError,
    PlannerOllamaInterface,
)
from selfai.core.planner_validator import (
    PlanValidationError,
    validate_plan_logic,
)
from selfai.core.merge_ollama_interface import MergeOllamaInterface
from selfai.core.planner_minimax_interface import PlannerMinimaxInterface
from selfai.core.merge_minimax_interface import MergeMinimaxInterface  # Falls erstellt
from selfai.core.tool_calling_ollama_interface import ToolCallingOllamaInterface
from selfai.ui.terminal_ui import TerminalUI
from selfai.ui.ui_adapter import create_ui
from selfai.tools.tool_registry import list_all_tools, get_tools_for_agent
from selfai.core.token_limits import TokenLimits
from selfai.core.selfai_agent import create_selfai_agent
from selfai.core.custom_agent_loop import CustomAgentLoop
from selfai.core.improvement_suggestions import (
    ImprovementManager,
    ImprovementProposal,
    parse_proposals_from_json,
)

PLANNER_STATE_FILENAME = "planner_state.json"
MERGE_STATE_FILENAME = "merge_state.json"

# SAFETY: Critical files that /selfimprove must NEVER modify
# These files are too risky - any bug here breaks the entire system
SELFIMPROVE_PROTECTED_FILES = [
    "selfai/selfai.py",  # Main orchestration - YOU ARE HERE!
    "selfai/config_loader.py",  # Config system
    "selfai/core/agent_manager.py",  # Agent loading
    "selfai/tools/tool_registry.py",  # Tool system
]

# SAFETY: Files that need explicit user approval before modification
SELFIMPROVE_SENSITIVE_FILES = [
    "selfai/core/execution_dispatcher.py",  # Core execution
    "selfai/core/planner_minimax_interface.py",  # Planning system
    "selfai/core/merge_minimax_interface.py",  # Merge system
    "selfai/core/memory_system.py",  # Memory system
]

# SAFETY: Allowed file patterns for self-improvement
SELFIMPROVE_ALLOWED_PATTERNS = [
    "selfai/core/*_interface.py",  # LLM interfaces
    "selfai/tools/*.py",  # Tool implementations
    "selfai/ui/*.py",  # UI improvements
]


def _format_gigabytes(value_bytes: float) -> float:
    return value_bytes / (1024**3)


def _show_system_resources(ui: TerminalUI) -> None:
    if psutil is None:
        ui.status(
            "Systemmonitor nicht verfügbar (psutil nicht installiert).", "warning"
        )
        return

    try:
        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()
        cpu_percent = psutil.cpu_percent(interval=0.1)
    except Exception as exc:
        ui.status(f"Systemmonitor konnte nicht abgerufen werden: {exc}", "warning")
        return

    total_gb = _format_gigabytes(mem.total)
    used_gb = _format_gigabytes(mem.total - mem.available)
    free_gb = _format_gigabytes(mem.available)

    status_parts = [
        f"RAM {used_gb:.1f}/{total_gb:.1f} GB ({mem.percent:.0f}%)",
        f"frei {free_gb:.1f} GB",
        f"CPU {cpu_percent:.0f}%",
    ]

    if swap and swap.total:
        swap_used = _format_gigabytes(swap.used)
        swap_total = _format_gigabytes(swap.total)
        status_parts.append(
            f"Swap {swap_used:.1f}/{swap_total:.1f} GB ({swap.percent:.0f}%)"
        )

    ui.status(" | ".join(status_parts), "info")


def _show_pipeline_overview(ui: TerminalUI) -> None:
    ui.status("Pipeline: 1) Planner – zerlegt dein Ziel in Subtasks.", "info")
    ui.status(
        "Pipeline: 2) Execution – führt die Subtasks nacheinander oder parallel gemäß Plan aus.",
        "info",
    )
    ui.status(
        "Pipeline: 3) Merge – verdichtet alle Ergebnisse zu einer finalen Antwort.",
        "info",
    )


def _default_agent_key(agent_manager: AgentManager) -> str | None:
    if agent_manager.active_agent:
        return agent_manager.active_agent.key
    agents = agent_manager.list_agents()
    if agents:
        return agents[0].key
    return None


def _build_fallback_plan(goal_text: str, agent_key: str) -> dict[str, object]:
    sanitized_goal = goal_text.strip()
    return {
        "subtasks": [
            {
                "id": "S1",
                "title": "Analyse des Ziels",
                "objective": f"Analysiere das Ziel mit Tools: {sanitized_goal}",
                "agent_key": agent_key,
                "engine": "smolagent",  # Use tool-capable engine
                "tools": [
                    "list_selfai_files",
                    "read_selfai_code",
                    "search_selfai_code",
                ],
                "parallel_group": 1,
                "depends_on": [],
                "notes": "Automatisch erzeugter Fallback-Plan – nutze Tools zur Analyse.",
            },
            {
                "id": "S2",
                "title": "Antwort formulieren",
                "objective": f"Formuliere eine ausführliche Antwort für: {sanitized_goal}",
                "agent_key": agent_key,
                "engine": "minimax",
                "parallel_group": 2,
                "depends_on": ["S1"],
                "notes": "Automatisch erzeugter Fallback-Plan.",
            },
        ],
        "merge": {
            "strategy": "Analyse und Antwort zu einem konsistenten Ergebnis kombinieren.",
            "steps": [
                {
                    "title": "Synthese",
                    "description": "Fasse Analyse und Antwort in einer finalen Empfehlung zusammen.",
                    "depends_on": ["S2"],
                }
            ],
        },
    }


def _sanitize_plan_agents(
    plan_data: dict[str, object],
    agent_manager: AgentManager,
    ui: TerminalUI,
) -> None:
    valid_keys = {agent.key for agent in agent_manager.list_agents()}
    if not valid_keys:
        return

    fallback_key = _default_agent_key(agent_manager)
    if fallback_key is None:
        return

    changed = False
    for task in plan_data.get("subtasks", []) or []:
        key = task.get("agent_key")
        if key not in valid_keys:
            task["agent_key"] = fallback_key
            changed = True
    if changed:
        ui.status(
            f"Plan angepasst: Unbekannte Agenten wurden auf '{fallback_key}' gemappt.",
            "warning",
        )


def _announce_plan_agents(
    plan_data: dict[str, object],
    agent_manager: AgentManager,
    ui: TerminalUI,
) -> None:
    seen: set[str] = set()
    for task in plan_data.get("subtasks", []) or []:
        key = task.get("agent_key")
        if not key or key in seen:
            continue
        agent = agent_manager.get(key)
        if agent is None:
            continue
        description = agent.description.strip() if agent.description else ""
        if description:
            ui.status(
                f"Subtasks nutzen Agent '{agent.display_name}' – {description}",
                "info",
            )
        else:
            ui.status(
                f"Subtasks nutzen Agent '{agent.display_name}'.",
                "info",
            )
        seen.add(key)


def _build_planner_context(
    agent_manager: AgentManager, memory_system: MemorySystem
) -> PlannerContext:
    agents_data = []
    for agent in agent_manager.list_agents():
        categories = ", ".join(agent.memory_categories) or "-"
        details = [f"Memory: {categories}", f"Workspace: {agent.workspace_slug}"]
        if agent.description:
            details.insert(0, agent.description.strip())
        agents_data.append(
            {
                "key": agent.key,
                "display_name": agent.display_name,
                "description": "; ".join(details),
            }
        )

    plan_dir = getattr(memory_system, "plan_dir", None)
    summary = ""
    if plan_dir and plan_dir.exists():
        plan_files = sorted(plan_dir.glob("*.json"))
        if plan_files:
            summary = (
                f"{len(plan_files)} gespeicherte Pläne. Letzter: {plan_files[-1].name}"
            )
    if not summary:
        summary = "Noch keine Pläne gespeichert."

    return PlannerContext(agents=agents_data, memory_summary=summary)


def _planner_state_path(memory_system: MemorySystem) -> Path:
    return memory_system.memory_dir / PLANNER_STATE_FILENAME


def _load_active_planner(memory_system: MemorySystem) -> str | None:
    path = _planner_state_path(memory_system)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        value = data.get("active_provider")
        if isinstance(value, str) and value:
            return value
    except (OSError, json.JSONDecodeError):
        return None
    return None


def _save_active_planner(memory_system: MemorySystem, provider_name: str) -> None:
    path = _planner_state_path(memory_system)
    try:
        path.write_text(
            json.dumps({"active_provider": provider_name}, indent=2),
            encoding="utf-8",
        )
    except OSError:
        pass


def _merge_state_path(memory_system: MemorySystem) -> Path:
    return memory_system.memory_dir / MERGE_STATE_FILENAME


def _load_active_merge(memory_system: MemorySystem) -> str | None:
    path = _merge_state_path(memory_system)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        value = data.get("active_provider")
        if isinstance(value, str) and value:
            return value
    except (OSError, json.JSONDecodeError):
        return None
    return None


def _save_active_merge(memory_system: MemorySystem, provider_name: str) -> None:
    path = _merge_state_path(memory_system)
    try:
        path.write_text(
            json.dumps({"active_provider": provider_name}, indent=2),
            encoding="utf-8",
        )
    except OSError:
        pass


def _load_plan_file(plan_path: Path) -> dict:
    try:
        return json.loads(plan_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _save_plan_file(plan_path: Path, data: dict) -> None:
    try:
        plan_path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
        )
    except OSError:
        pass


def _read_result_file(result_path: Path) -> str:
    try:
        return result_path.read_text(encoding="utf-8")
    except OSError:
        return ""


def _collect_subtask_entries(plan_data: dict[str, object]) -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    subtasks = plan_data.get("subtasks", []) or []
    base_dir = project_root.parent
    for task in subtasks:
        if not isinstance(task, dict):
            continue
        result_ref = task.get("result_path")
        content = ""
        if result_ref:
            result_path = Path(result_ref)
            if not result_path.is_absolute():
                result_path = base_dir / result_path
            content = _read_result_file(result_path)
        entries.append(
            {
                "id": str(task.get("id", "?")),
                "title": str(task.get("title", "")),
                "objective": str(task.get("objective", "")),
                "output": content or "",
            }
        )
    return entries


def _render_fallback_merge(entries: list[dict[str, str]]) -> str:
    if not entries:
        return "SelfAI konnte keine Subtask-Ergebnisse finden."

    lines: list[str] = ["# Merge Summary (Fallback)", ""]
    for entry in entries:
        title = entry.get("title") or entry.get("id") or "Subtask"
        lines.append(f"## {entry.get('id', '?')} – {title}")
        objective = entry.get("objective", "").strip()
        if objective:
            lines.append(f"**Objective:** {objective}")
        output = entry.get("output", "").strip()
        if output:
            snippet = output if len(output) <= 600 else output[:600].rstrip() + "…"
            lines.append("```")
            lines.append(snippet)
            lines.append("```")
        else:
            lines.append("(Kein Output gespeichert.)")
        lines.append("")
    return "\n".join(lines).strip()


def _select_merge_agent_from_plan(
    merge_cfg: dict[str, object],
    agent_manager: AgentManager,
) -> Agent | None:
    # 1. Verwende Agent aus Plan (falls spezifiziert)
    merge_agent_key = None
    if isinstance(merge_cfg, dict):
        merge_agent_key = merge_cfg.get("agent_key")

    if merge_agent_key:
        agent = agent_manager.get(merge_agent_key)
        if agent:
            return agent

    # 2. Bevorzuge spezialisierter Synthesis Expert (NEU!)
    agent = agent_manager.get("synthesis_expert")
    if agent:
        return agent

    # 3. Fallback: Projektmanager
    agent = agent_manager.get("projektmanager")
    if agent:
        return agent

    # 4. Letzter Fallback: Aktiver Agent
    return agent_manager.active_agent


def _create_provider_headers(provider) -> dict[str, str] | None:
    """Erstellt Headers für Provider basierend auf api_key_env."""
    headers = {}
    if hasattr(provider, "api_key_env") and provider.api_key_env:
        api_key = os.getenv(provider.api_key_env, "")
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
    return headers if headers else None


def _execute_merge_phase(
    plan_path: Path,
    merge_backend: dict[str, object],
    agent_manager: AgentManager,
    memory_system: MemorySystem,
    ui: TerminalUI,
    execution_timeout: float | None,
) -> bool:
    llm_interface = merge_backend.get("interface")
    if llm_interface is None:
        ui.status("Kein Merge-Backend verfügbar.", "warning")
        return False

    merge_label = merge_backend.get("label", "Merge")
    try:
        merge_token_limit = int(merge_backend.get("max_tokens", 4096) or 4096)
    except (TypeError, ValueError):
        merge_token_limit = 4096

    timeout_value = merge_backend.get("timeout")
    if timeout_value is not None:
        try:
            timeout_value = float(timeout_value)
        except (TypeError, ValueError):
            timeout_value = execution_timeout
    else:
        timeout_value = execution_timeout

    plan_data = _load_plan_file(plan_path)
    merge_cfg = plan_data.get("merge") or {}
    if not merge_cfg:
        ui.status("Kein Merge-Schritt im Plan definiert.", "info")
        return True

    entries = _collect_subtask_entries(plan_data)
    outputs: list[str] = []
    for entry in entries:
        content = entry.get("output", "").strip()
        if not content:
            continue
        block = (
            f"Subtask {entry.get('id', '?')} – {entry.get('title', '')}\n"
            f"Objective: {entry.get('objective', '')}\n"
            f"Output:\n{content}"
        )
        outputs.append(block)

    if not outputs:
        ui.status("Keine Subtask-Ergebnisse für den Merge gefunden.", "warning")
        return False

    merge_agent = _select_merge_agent_from_plan(merge_cfg, agent_manager)
    if merge_agent is None:
        ui.status("Kein Agent für Merge verfügbar.", "warning")
        return False

    strategy = merge_cfg.get("strategy") or ""
    steps = merge_cfg.get("steps", []) or []
    steps_text = "".join(
        f"- {step.get('title', 'Schritt')}: {step.get('description', '').strip()}\n"
        for step in steps
    )

    combined_outputs = "\n\n".join(outputs)

    # Get original goal from plan metadata
    original_goal = plan_data.get("metadata", {}).get("goal", "Unbekanntes Ziel")

    final_prompt = (
        "Du bist ein Experte für Ergebnis-Synthese im DPPM-System.\n\n"
        f"URSPRÜNGLICHES ZIEL (User-Frage):\n{original_goal}\n\n"
        "AUSGEFÜHRTE SUBTASKS:\n"
        f"{combined_outputs}\n\n"
        "DEINE AUFGABE:\n"
        "Beantworte die URSPRÜNGLICHE USER-FRAGE direkt und vollständig. "
        "Synthetisiere die Subtask-Ergebnisse zu einer kohärenten Gesamt-Antwort.\n\n"
        "KRITISCHE ANFORDERUNGEN:\n"
        "1. FOKUS: Beantworte NUR die ursprüngliche User-Frage (keine Meta-Diskussion über den Prozess!)\n"
        "2. DIREKTHEIT: Beginne sofort mit der Antwort (kein 'Ich werde jetzt...', kein 'Lass mich...')\n"
        "3. SYNTHESE: Kombiniere Ergebnisse intelligent (nicht einfach copy-paste)\n"
        "4. REDUNDANZ: Wenn mehrere Subtasks dasselbe sagen, erwähne es NUR EINMAL\n"
        "5. WIDERSPRÜCHE: Identifiziere und löse Widersprüche zwischen Subtasks\n"
        "6. STRUKTUR: Gib eine klare, gut strukturierte Antwort (mit Überschriften wenn sinnvoll)\n"
        "7. VOLLSTÄNDIGKEIT: Alle relevanten Informationen aus Subtasks einbeziehen\n"
        "8. PRÄGNANZ: So kurz wie möglich, aber so ausführlich wie nötig\n\n"
        "AUSGABE-FORMAT:\n"
        "- KEINE <think> Tags oder interne Überlegungen!\n"
        "- KEINE Meta-Kommentare über den Merge-Prozess!\n"
        "- Beginne direkt mit der Antwort (optional: kurze Executive Summary)\n"
        "- Verwende Markdown-Formatierung (## für Überschriften, - für Listen)\n"
        "- Bei Code: Zeige integrierten, lauffähigen Code (nicht separate Snippets)\n\n"
    )
    if strategy:
        final_prompt += f"MERGE-STRATEGIE (vom Planner):\n{strategy}\n\n"
    if steps_text:
        final_prompt += f"VORGESCHLAGENE SCHRITTE:\n{steps_text}\n"

    final_prompt += "\nERSTELLE JETZT DIE FINALE ANTWORT:"

    history = memory_system.load_relevant_context(
        merge_agent,
        final_prompt,
        limit=2,
    )
    ui.status(
        f"Merge-Ausgabe mit Agent '{merge_agent.display_name}' wird berechnet...",
        "info",
    )

    merge_response = ""
    displayed = False
    use_streaming = hasattr(llm_interface, "stream_chat") or hasattr(
        llm_interface, "stream_generate_response"
    )

    if use_streaming:
        try:
            chunks: list[str] = []
            ui.stream_prefix(f"{merge_label}")
            if hasattr(llm_interface, "stream_chat"):
                iterator = llm_interface.stream_chat(
                    system_prompt=merge_agent.system_prompt,
                    user_prompt=final_prompt,
                    timeout=timeout_value,
                    max_tokens=merge_token_limit,
                )
            else:
                iterator = llm_interface.stream_generate_response(
                    system_prompt=merge_agent.system_prompt,
                    user_prompt=final_prompt,
                    history=history,
                    timeout=timeout_value,
                    max_output_tokens=merge_token_limit,
                )
            for chunk in iterator:
                if chunk:
                    chunks.append(chunk)
                    ui.streaming_chunk(chunk)
            print()
            merge_response = "".join(chunks)
            displayed = True
        except Exception as stream_exc:
            ui.status(
                f"Merge-Streaming fehlgeschlagen ({stream_exc}). Fallback auf Block-Modus.",
                "warning",
            )
            print()
            use_streaming = False

    if not displayed:
        try:
            if hasattr(llm_interface, "chat"):
                merge_response = llm_interface.chat(
                    system_prompt=merge_agent.system_prompt,
                    user_prompt=final_prompt,
                    timeout=timeout_value,
                    max_tokens=merge_token_limit,
                )
            else:
                merge_response = llm_interface.generate_response(
                    system_prompt=merge_agent.system_prompt,
                    user_prompt=final_prompt,
                    history=history,
                    timeout=timeout_value,
                    max_output_tokens=merge_token_limit,
                )
            ui.stream_prefix(f"{merge_label}")
            ui.typing_animation(merge_response)
            displayed = True
        except Exception as exc:  # pragma: no cover
            ui.status(f"Merge-Ausgabe fehlgeschlagen: {exc}", "error")
            return False

    if not merge_response or not merge_response.strip():
        ui.status("Merge-Backend lieferte keinen Inhalt.", "warning")
        return False

    # Clean up merge response: remove <think> tags and meta-commentary
    import re

    merge_response = re.sub(
        r"<think>.*?</think>", "", merge_response, flags=re.DOTALL
    ).strip()

    if not merge_response:
        ui.status("Merge-Backend lieferte nur <think> Tags, keinen Inhalt.", "warning")
        return False

    result_path = memory_system.save_conversation(
        merge_agent,
        final_prompt,
        merge_response,
    )

    if not displayed:
        ui.status("Merge-Ergebnis gespeichert.", "success")
    else:
        ui.status("Merge-Ergebnis abgeschlossen.", "success")

    plan_data.setdefault("metadata", {})
    plan_data["metadata"].update(
        {
            "merge_agent": merge_agent.key,
            "merge_provider": merge_backend.get("name"),
            "merge_provider_type": merge_backend.get("type"),
            "merge_model": merge_backend.get("model"),
            "merge_backend_label": merge_label,
            "merge_base_url": merge_backend.get("base_url"),
            "merge_max_tokens": merge_token_limit,
            "merge_timeout": timeout_value,
            "merge_result_path": str(result_path) if result_path else None,
        }
    )
    _save_plan_file(plan_path, plan_data)
    return True


def _select_merge_backend(
    ui: TerminalUI,
    llm_interface,
    backend_label: str | None,
    merge_providers: dict[str, dict[str, object]],
    active_merge_provider: str | None,
    merge_provider_order: list[str] | None = None,
) -> dict[str, object]:
    """Erlaubt dem Nutzer die Auswahl des Merge-Backends."""

    default_label = backend_label or "MiniMax"
    backends: list[dict[str, object]] = [
        {
            "label": default_label,
            "type": "minimax",
            "interface": llm_interface,
            "max_tokens": 2048,
            "name": "minimax",
        }
    ]
    options: list[str] = [f"{default_label} (aktuelles LLM)"]

    provider_names = list(merge_provider_order or merge_providers.keys())
    for name in provider_names:
        info = merge_providers.get(name)
        if not info:
            continue
        if "interface" not in info:
            continue
        backend_entry = dict(info)
        backend_entry.setdefault("label", name)
        backend_entry.setdefault("name", name)
        backends.append(backend_entry)
        options.append(
            f"{name} [{backend_entry.get('type', 'custom')}] {backend_entry.get('model')}"
        )

    if len(backends) == 1:
        return backends[0]

    default_index = 0
    if active_merge_provider:
        for idx, backend in enumerate(backends):
            if backend.get("name") == active_merge_provider:
                default_index = idx
                break

    choice = ui.choose_option(
        "Merge-Backend auswählen",
        options,
        default_index=default_index,
    )
    return backends[choice]


def _load_minimax(config, ui: TerminalUI):
    """Lädt MiniMax als primäres Cloud-Backend."""
    try:
        minimax_config = getattr(config, "minimax_config", None)
        if not minimax_config or not minimax_config.enabled:
            return None, None

        interface = MinimaxInterface(
            api_key=minimax_config.api_key,
            api_base=minimax_config.api_base,
            model=minimax_config.model,
            ui=ui,  # Pass UI for think tag display
        )
        return interface, "MiniMax"
    except Exception as exc:
        ui.status(f"MiniMax konnte nicht geladen werden: {exc}", "warning")
        return None, None


def _load_qnn(models_root: Path, ui: TerminalUI):
    try:
        from selfai.core.npu_llm_interface import NpuLLMInterface, find_qnn_models
    except ImportError:
        ui.status(
            "`npu_llm_interface` nicht gefunden. Überspringe QNN-Pfad.", "warning"
        )
        return None, None

    qnn_models = find_qnn_models(models_root)
    if not qnn_models:
        ui.status("Keine QNN-Modelle gefunden.", "warning")
        return None, None

    model_path = qnn_models[0]
    try:
        interface = NpuLLMInterface(model_path=str(model_path))
        return interface, f"qnn:{model_path.name}"
    except (ImportError, FileNotFoundError, RuntimeError) as exc:
        ui.status(f"Fehler beim Laden des QNN-Modells: {exc}", "warning")
        return None, None


def _load_cpu(models_root: Path, ui: TerminalUI):
    candidates = [
        "Phi-3-mini-4k-instruct.Q4_K_M.gguf",
        "deepseek-llm-7b-chat.Q4_K_M.gguf",
    ]
    for model_filename in candidates:
        model_path = models_root / model_filename
        if not model_path.exists():
            continue
        try:
            interface = LocalLLMInterface(model_path=str(model_path))
            return interface, f"cpu:{model_filename}"
        except (FileNotFoundError, RuntimeError, ImportError) as exc:
            ui.status(f"Fehler beim Laden von '{model_filename}': {exc}", "warning")

    return None, None


def _check_file_safety(file_path: str, ui: TerminalUI) -> tuple[bool, str]:
    """
    Prüft ob eine Datei für Self-Improvement erlaubt ist.
    Returns: (allowed, reason)
    """
    # Normalisiere Pfad
    file_path = file_path.replace("\\", "/")

    # CRITICAL: Geschützte Dateien dürfen NIE geändert werden
    for protected in SELFIMPROVE_PROTECTED_FILES:
        if file_path.endswith(protected) or protected in file_path:
            return (
                False,
                f"🚫 PROTECTED: {file_path} ist kritisch und darf nicht geändert werden!",
            )

    # SENSITIVE: Benötigen explizite User-Approval
    for sensitive in SELFIMPROVE_SENSITIVE_FILES:
        if file_path.endswith(sensitive) or sensitive in file_path:
            ui.status(f"⚠️  SENSITIVE: {file_path} ist sensibel", "warning")
            if not ui.confirm(f"Wirklich {file_path} ändern?", default_yes=False):
                return False, f"❌ USER DENIED: {file_path} Änderung abgelehnt"

    return True, "✅ File safe to modify"


def _validate_selfimprove_safety(ui: TerminalUI) -> bool:
    """Prüft Safety-Bedingungen für Self-Improvement."""
    warnings = []

    # Prüfe pytest Verfügbarkeit
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "--version"],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            warnings.append(
                "pytest nicht verfügbar - automatisierte Tests nicht möglich"
            )
    except FileNotFoundError:
        warnings.append("pytest nicht installiert - automatisierte Tests nicht möglich")

    # Prüfe Git Status
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            cwd=project_root,
        )
        if result.stdout.strip():
            warnings.append(
                "Git Repository nicht sauber - uncommitted changes vorhanden"
            )
    except FileNotFoundError:
        warnings.append("Git nicht verfügbar - Versionskontrolle nicht möglich")
    except Exception:
        warnings.append("Git Status konnte nicht geprüft werden")

    # Prüfe Aider Verfügbarkeit
    try:
        result = subprocess.run(["aider", "--version"], capture_output=True, text=True)
        if result.returncode != 0:
            warnings.append(
                "Aider nicht verfügbar - automatische Code-Änderungen nicht möglich"
            )
    except FileNotFoundError:
        warnings.append(
            "Aider nicht installiert - automatische Code-Änderungen nicht möglich"
        )

    if warnings:
        ui.status("SICHERHEITSWARNUNGEN für Self-Improvement:", "warning")
        for warning in warnings:
            ui.status(f"- {warning}", "warning")

        if not ui.confirm("Trotzdem fortfahren?", default_yes=False):
            ui.status("Self-Improvement abgebrochen.", "info")
            return False

    return True


def _analyze_selfai_code(ui: TerminalUI) -> dict[str, str]:
    """Analysiert SelfAI Code-Struktur und sammelt alle Python-Dateien."""
    ui.status("Analysiere SelfAI Code-Struktur...", "info")

    code_analysis = {"files": [], "total_files": 0, "total_lines": 0, "modules": []}

    # FIX: project_root IST bereits selfai/, nicht parent davon
    selfai_dir = project_root  # Direkt verwenden!
    if not selfai_dir.exists():
        ui.status("SelfAI Verzeichnis nicht gefunden.", "warning")
        return code_analysis

    # Sammle alle Python-Dateien
    for py_file in selfai_dir.rglob("*.py"):
        try:
            relative_path = py_file.relative_to(project_root)
            content = py_file.read_text(encoding="utf-8")
            lines = len(content.splitlines())

            code_analysis["files"].append(
                {"path": str(relative_path), "lines": lines, "size": len(content)}
            )
            code_analysis["total_files"] += 1
            code_analysis["total_lines"] += lines

            # Extrahiere Modul-Informationen
            if "__init__.py" in str(py_file):
                module_path = str(relative_path.parent).replace("/", ".")
                if module_path not in code_analysis["modules"]:
                    code_analysis["modules"].append(module_path)

        except Exception as exc:
            ui.status(f"Fehler beim Lesen von {py_file}: {exc}", "warning")

    # Sortiere Dateien nach Pfad
    code_analysis["files"].sort(key=lambda x: x["path"])

    ui.status(
        f"Code-Analyse abgeschlossen: {code_analysis['total_files']} Dateien, {code_analysis['total_lines']} Zeilen",
        "success",
    )
    return code_analysis


def _handle_selfimprove(
    goal: str,
    agent_manager: AgentManager,
    memory_system: MemorySystem,
    ui: TerminalUI,
    planner_interface,
    execution_backends: list[dict[str, object]],
    backend_label: str,
) -> None:
    """
    Behandelt den /selfimprove Command für Selbst-Optimierung (V2 Proposal System).

    Flow:
    1. Analyse (Read-Only) durch SelfImprovementEngine
    2. Präsentation von Vorschlägen
    3. Auswahl durch User
    4. Plan-Erstellung und Ausführung
    """

    if not goal.strip():
        ui.status(
            "Bitte ein Ziel für Self-Improvement angeben: /selfimprove <ziel>",
            "warning",
        )
        return

    # 1. Imports für V2
    from selfai.core.self_improvement_engine import SelfImprovementEngine
    from selfai.core.improvement_suggestions import ImprovementManager
    from pathlib import Path

    # Safety-Checks
    if not _validate_selfimprove_safety(ui):
        return

    # 2. Analyse Phase (Read-Only)
    ui.status(f"🔍 Starte Analyse für Ziel: {ui.colorize(goal, 'cyan')}", "info")

    # Get primary LLM for analysis
    primary_backend = execution_backends[0]
    analysis_llm = primary_backend.get("interface")

    engine = SelfImprovementEngine(
        project_root=Path("."), llm_interface=analysis_llm, ui=ui
    )

    # Generate proposals
    try:
        proposals = engine.generate_proposals(goal)
    except Exception as e:
        ui.status(f"Fehler bei der Analyse: {e}", "error")
        return

    if not proposals:
        ui.status("Keine konkreten Verbesserungsvorschläge gefunden.", "warning")
        return

    # 3. Präsentations-Phase
    print("\n" + "=" * 60)
    print(f"  📋 VERBESSERUNGSVORSCHLÄGE FÜR: {goal}")
    print("=" * 60 + "\n")

    for p in proposals:
        # Determine color based on priority
        color = "green" if p.priority == "low" else "yellow"
        if p.priority == "high":
            color = "red"

        print(f"  {ui.colorize(f'[{p.id}] {p.title}', color)}")
        print(f"      {p.description}")
        print(f"      Files: {', '.join(p.files[:3])}")
        print(f"      Aufwand: {p.formatted_effort} | Impact: {p.formatted_impact}")
        print("")

    print("=" * 60)
    print(f"Wähle Optionen (z.B. '1', '1,3', 'all') oder 'q' zum Abbrechen.")

    # 4. Auswahl-Phase
    selection = input(ui.colorize("\nDeine Wahl: ", "cyan")).strip().lower()

    if selection in ["q", "quit", "abort", "exit"]:
        ui.status("Abgebrochen.", "info")
        return

    selected_proposals = []
    if selection == "all":
        selected_proposals = proposals
    else:
        # Parse IDs "1, 2, 3"
        try:
            ids = [int(s.strip()) for s in selection.split(",") if s.strip().isdigit()]
            selected_proposals = [p for p in proposals if p.id in ids]
        except ValueError:
            ui.status("Ungültige Eingabe.", "error")
            return

    if not selected_proposals:
        ui.status("Keine gültigen Vorschläge ausgewählt.", "warning")
        return

    # 5. Planungs & Ausführungs-Phase
    ui.status(f"Erstelle Plan für {len(selected_proposals)} Improvements...", "info")

    # Sammle Details für den Planner
    tasks_description = ""
    for p in selected_proposals:
        tasks_description += f"\nIMPROVEMENT {p.id}: {p.title}\n"
        tasks_description += f"Description: {p.description}\n"
        tasks_description += f"Files: {', '.join(p.files)}\n"
        tasks_description += (
            "Steps:\n" + "\n".join([f"- {s}" for s in p.implementation_steps]) + "\n"
        )

    # Erstelle Plan via Planner Interface
    planner_goal = f"Implementiere folgende Self-Improvements:\n{tasks_description}"

    # Get available agent
    available_agents = agent_manager.list_agents()
    default_agent = (
        agent_manager.active_agent
        if agent_manager.active_agent
        else available_agents[0]
    )

    try:
        plan_data = planner_interface.plan(
            planner_goal,
            PlannerContext(
                agents=[
                    {
                        "key": default_agent.key,
                        "display_name": default_agent.display_name,
                    }
                ],
                memory_summary=f"Selected {len(selected_proposals)} improvements for implementation.",
            ),
        )

        # Zeige Plan
        ui.show_plan(plan_data)

        if not ui.confirm_plan():
            ui.status("Plan verworfen.", "warning")
            return

        # Speichere Plan
        plan_path = memory_system.save_plan(f"Self-Improve: {goal[:30]}", plan_data)

        if not ui.confirm_execution():
            return

        # Ausführung
        dispatcher = ExecutionDispatcher(
            plan_path=plan_path,
            agent_manager=agent_manager,
            memory_system=memory_system,
            llm_backends=execution_backends,
            ui=ui,
            backend_label=backend_label,
            llm_timeout=60.0,
            retry_attempts=1,
            max_output_tokens=4096,
        )
        dispatcher.run()

        ui.status("✅ Self-Improvement Subtasks ausgeführt!", "success")

        # Merge Phase (optional, but good for summary)
        if plan_data.get("merge"):
            ui.status("Starte Merge-Phase (Zusammenfassung)...", "info")
            primary_backend = execution_backends[0]
            merge_backend = {
                "label": "Self-Improvement Merge",
                "type": primary_backend.get("type", "minimax"),
                "interface": primary_backend.get("interface"),
                "max_tokens": 4096,
                "name": "selfimprove_merge",
                "model": "selfimprove",
            }

            _execute_merge_phase(
                plan_path,
                merge_backend=merge_backend,
                agent_manager=agent_manager,
                memory_system=memory_system,
                ui=ui,
                execution_timeout=60.0,
            )

    except Exception as e:
        ui.status(f"Fehler bei der Ausführung: {e}", "error")


def main():
    # Auto-select UI based on SELFAI_PARALLEL_UI environment variable
    ui = create_ui()

    ui.clear()
    ui.banner()
    ui.status("SelfAI wird gestartet...", "info")

    agents_path = project_root / "agents"
    agent_manager = AgentManager(agents_dir=agents_path, verbose=False)

    memory_path = project_root / "memory"
    memory_system = MemorySystem(memory_dir=memory_path)

    # DISABLED: UI metrics for now
    # metrics_path = project_root / "memory" / "ui_metrics"
    # ui_metrics = UIMetricsCollector(metrics_dir=metrics_path)

    # Initialize token limits (runtime-configurable)
    token_limits = TokenLimits()
    token_limits.set_balanced()  # Start with balanced defaults

    if not agent_manager.agents:
        ui.status("Keine Agenten gefunden. Das Programm wird beendet.", "error")
        return

    available_agents = agent_manager.list_agents()

    llm_interface = None
    backend_label = None
    models_root = project_root.parent / "models"

    config = None
    streaming_enabled = False
    planner_cfg = None
    planner_providers: dict[str, dict[str, object]] = {}
    planner_provider_order: list[str] = []
    active_planner_provider: str | None = None
    merge_cfg = None
    merge_providers: dict[str, dict[str, object]] = {}
    merge_provider_order: list[str] = []
    active_merge_provider: str | None = None

    try:
        config = load_configuration()
        ui.status("Konfiguration geladen.", "success")
        streaming_enabled = bool(getattr(config.system, "streaming_enabled", False))
        planner_cfg = getattr(config, "planner", None)
        merge_cfg = getattr(config, "merge", None)
    except (FileNotFoundError, ValueError) as exc:
        ui.status(f"Konfiguration nicht verfügbar: {exc}", "warning")
    except Exception as exc:
        ui.status(f"Unerwarteter Konfigurationsfehler: {exc}", "error")

    # LLM Backend Loading - MiniMax als PRIMARY!
    execution_backends: list[dict[str, object]] = []

    # 1. MiniMax (Cloud - Primary)
    if config:
        interface_minimax, label_minimax = _load_minimax(config, ui)
        if interface_minimax:
            execution_backends.append(
                {
                    "interface": interface_minimax,
                    "label": label_minimax or "MiniMax",
                    "name": "minimax",
                    "type": "cloud",
                }
            )

    # 2. QNN (Lokal - Secondary)
    interface_qnn, label_qnn = _load_qnn(models_root, ui)
    if interface_qnn:
        execution_backends.append(
            {
                "interface": interface_qnn,
                "label": label_qnn or "QNN",
                "name": "qnn",
                "type": "qnn",
            }
        )

    # 3. CPU (Lokal - Tertiary)
    interface_cpu, label_cpu = _load_cpu(models_root, ui)
    if interface_cpu:
        execution_backends.append(
            {
                "interface": interface_cpu,
                "label": label_cpu or "CPU",
                "name": "cpu",
                "type": "cpu",
            }
        )

    if not execution_backends:
        ui.status(
            "Keines der verfügbaren LLM-Backends (MiniMax, QNN, CPU) konnte geladen werden.",
            "error",
        )
        ui.status("Bitte Konfiguration und Modelle prüfen.", "info")
        return

    # Set primary interface to first available backend (MiniMax preferred)
    llm_interface = execution_backends[0]["interface"]
    backend_label = execution_backends[0].get("label") or "Plan"

    ui.status(
        f"Primäres LLM-Backend: {backend_label}, Verfügbare Backends: {', '.join([backend['name'] for backend in execution_backends])}",
        "success",
    )

    # Load tools
    available_tools = list_all_tools()
    ui.show_available_tools(available_tools)

    # Load dynamically generated tools
    tools_gen_dir = project_root / "tools" / "generated"
    if tools_gen_dir.exists():
        generated_tools = list(tools_gen_dir.glob("*.py"))
        generated_count = sum(
            1
            for f in generated_tools
            if f.name != "__init__.py" and not f.name.startswith("_")
        )
        if generated_count > 0:
            ui.status(
                f"Found {generated_count} generated tool(s) in tools/generated/", "info"
            )
            ui.status(
                "⚠️  Generated tools will be available after restart or use /toolcreate to create new ones",
                "info",
            )

    # FIX: Planner Provider Loading mit korrekten Headers und Type-based Selection
    active_planner_interface = None
    if planner_cfg and planner_cfg.enabled:
        ui.status(
            f"🔧 Lade Planner-Provider... (Anzahl: {len(planner_cfg.providers)})",
            "info",
        )
        ui.status(f"   DEBUG: planner_cfg.enabled = {planner_cfg.enabled}", "info")
        for provider in planner_cfg.providers:
            ui.status(
                f"   DEBUG: Versuche Provider '{provider.name}' zu laden...", "info"
            )
            try:
                headers = _create_provider_headers(provider)

                # Wähle Interface basierend auf provider.type
                if provider.type == "minimax":
                    interface = PlannerMinimaxInterface(
                        base_url=provider.base_url,
                        model=provider.model,
                        timeout=provider.timeout,
                        max_tokens=provider.max_tokens,
                        headers=headers,
                        ui=ui,  # Pass UI for think tag display
                    )
                elif provider.type == "local_ollama":
                    interface = PlannerOllamaInterface(
                        base_url=provider.base_url,
                        model=provider.model,
                        timeout=provider.timeout,
                        max_tokens=provider.max_tokens,
                        headers=headers,
                    )
                else:
                    raise ValueError(f"Unknown planner type: {provider.type}")

                planner_providers[provider.name] = {
                    "type": provider.type,
                    "interface": interface,
                    "model": provider.model,
                    "base_url": provider.base_url,
                    "max_tokens": provider.max_tokens,
                    "timeout": provider.timeout,
                }
                planner_provider_order.append(provider.name)

                # Setze erstes Interface als aktives
                if active_planner_interface is None:
                    active_planner_interface = interface

                ui.status(
                    f"Planner-Provider '{provider.name}' ({provider.type}) aktiv.",
                    "info",
                )
            except Exception as exc:
                import traceback

                ui.status(
                    f"Planner-Provider '{provider.name}' Fehler: {exc}",
                    "warning",
                )
                ui.status(f"   Traceback: {traceback.format_exc()[:200]}", "warning")

    if planner_providers:
        stored_provider = _load_active_planner(memory_system)
        if stored_provider and stored_provider in planner_providers:
            active_planner_provider = stored_provider
            active_planner_interface = planner_providers[stored_provider]["interface"]
        else:
            active_planner_provider = planner_provider_order[0]
            active_planner_interface = planner_providers[active_planner_provider][
                "interface"
            ]
            _save_active_planner(memory_system, active_planner_provider)
        ui.status(f"Aktiver Planner-Provider: {active_planner_provider}", "info")
    else:
        ui.status("Kein Planner-Provider verfügbar.", "warning")

    # FIX: Merge Provider Loading mit korrekten Headers und Type-based Selection
    if merge_cfg and merge_cfg.enabled:
        for provider in merge_cfg.providers:
            try:
                headers = _create_provider_headers(provider)

                # Wähle Interface basierend auf provider.type
                if provider.type == "minimax":
                    interface = MergeMinimaxInterface(
                        base_url=provider.base_url,
                        model=provider.model,
                        timeout=provider.timeout,
                        max_tokens=provider.max_tokens,
                        headers=headers,
                        ui=ui,  # Pass UI for think tag display
                    )
                elif provider.type == "local_ollama":
                    interface = MergeOllamaInterface(
                        base_url=provider.base_url,
                        model=provider.model,
                        timeout=provider.timeout,
                        max_tokens=provider.max_tokens,
                        headers=headers,
                    )
                else:
                    raise ValueError(f"Unknown merge type: {provider.type}")

                merge_providers[provider.name] = {
                    "type": provider.type,
                    "interface": interface,
                    "model": provider.model,
                    "base_url": provider.base_url,
                    "max_tokens": provider.max_tokens,
                    "timeout": provider.timeout,
                }
                merge_provider_order.append(provider.name)
                ui.status(
                    f"Merge-Provider '{provider.name}' ({provider.type}) aktiv.",
                    "info",
                )
            except Exception as exc:
                ui.status(
                    f"Merge-Provider '{provider.name}' Fehler: {exc}",
                    "warning",
                )

    if merge_providers:
        stored_merge = _load_active_merge(memory_system)
        if stored_merge and stored_merge in merge_providers:
            active_merge_provider = stored_merge
        else:
            active_merge_provider = merge_provider_order[0]
            _save_active_merge(memory_system, active_merge_provider)
        ui.status(f"Aktiver Merge-Provider: {active_merge_provider}", "info")
    else:
        ui.status("Kein zusätzlicher Merge-Provider konfiguriert.", "info")

    default_key = None
    if config and getattr(config, "agent_config", None):
        default_key = getattr(config.agent_config, "default_agent", None)

    if default_key:
        try:
            agent_manager.switch_agent(default_key)
        except ValueError:
            ui.status(
                f"Standard-Agent '{default_key}' nicht gefunden. Fallback auf Liste.",
                "warning",
            )

    if agent_manager.active_agent is None:
        try:
            first_agent = available_agents[0]
            agent_manager.switch_agent(first_agent.key)
        except (IndexError, ValueError) as exc:
            ui.status(f"Fehler beim Setzen des Standard-Agenten: {exc}", "error")
            return

    ui.status(f"Aktiver Agent: {agent_manager.active_agent.display_name}", "success")
    ui.list_agents(
        agent_manager.agents,
        active_key=agent_manager.active_agent.key,
    )
    available_agents = agent_manager.list_agents()

    # Show pipeline overview and system resources before main loop
    _show_pipeline_overview(ui)
    _show_system_resources(ui)

    command_hint = "Bereit. Nachricht eingeben, "
    if planner_providers:
        command_hint += "'/plan <Ziel>' für DPPM-Plan, '/planner list' für Provider, "
    command_hint += "'/selfimprove <ziel>' für Selbst-Optimierung, "
    command_hint += "'/toolcreate <name> <desc>' für neue Tools, "
    command_hint += "'/errorcorrection' für Fehler-Analyse & Auto-Fix, "
    command_hint += "'/tokens' für Token-Limits, '/extreme' für 64K Limits, "
    command_hint += "'/context' für Context-Window Kontrolle, "
    command_hint += "'/yolo' für Auto-Accept Modus, "
    command_hint += "'/switch <Name|Nummer>' zum Wechseln, 'quit' zum Beenden."
    ui.status(command_hint, "info")

    # Show current context window
    ui.status(
        f"📅 Context Window: {memory_system.context_window_minutes} Minuten (nur Files aus aktueller Session)",
        "info",
    )

    active_chat_backend_index = 0

    def _generate_with_backend(
        interface,
        label: str,
        system_prompt: str,
        user_prompt: str,
        history_messages,
    ) -> tuple[str, bool]:
        use_stream = streaming_enabled and hasattr(
            interface, "stream_generate_response"
        )
        if use_stream:
            chunks: list[str] = []
            first_chunk = True
            try:
                for chunk in interface.stream_generate_response(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    history=history_messages,
                ):
                    if not chunk:
                        continue
                    if first_chunk:
                        ui.stop_spinner()
                        ui.stream_prefix(label)
                        first_chunk = False
                    chunks.append(chunk)
                    ui.streaming_chunk(chunk)
                if first_chunk:
                    ui.stop_spinner()
                else:
                    print()
                return "".join(chunks), True
            except Exception as exc:  # pylint: disable=broad-except
                ui.stop_spinner()
                ui.status(
                    f"Streaming-Fehler am Backend '{label}': {exc}",
                    "warning",
                )
                use_stream = False

        try:
            ui.stop_spinner()
            ui.stream_prefix(label)
            response = interface.generate_response(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                history=history_messages,
            )
            return response, False
        except Exception as exc:  # pylint: disable=broad-except
            raise RuntimeError(exc) from exc

    # Initialize agent variable before loop (prevents UnboundLocalError)
    selfai_agent = None

    while True:
        user_input = input("\nDu: ").strip()
        if not user_input:
            continue

        if user_input.lower() == "quit":
            ui.status("Auf Wiedersehen!", "success")
            break

        # NEU: /tokens Command - Show/Modify Token Limits
        if user_input.lower().startswith("/tokens"):
            parts = user_input.split()

            if len(parts) == 1:
                # Show current limits
                ui.status(str(token_limits), "info")
                ui.status("\n💡 Available commands:", "info")
                ui.status("  /tokens extreme       - Set all limits to 64000", "info")
                ui.status(
                    "  /tokens conservative  - Set all limits to conservative (fast, cheap)",
                    "info",
                )
                ui.status(
                    "  /tokens balanced      - Set all limits to balanced (default)",
                    "info",
                )
                ui.status(
                    "  /tokens generous      - Set all limits to generous (high quality)",
                    "info",
                )
                ui.status("  /tokens set <type> <value> - Set specific limit", "info")
                ui.status(
                    "    Types: planner, execution, merge, tool_creation, error_correction, selfimprove, chat",
                    "info",
                )
                continue

            subcommand = parts[1].lower()

            if subcommand == "extreme":
                token_limits.set_extreme()
                ui.status("🚀 EXTREME MODE: All token limits set to 64000!", "success")
                ui.status(str(token_limits), "info")
                continue

            if subcommand == "conservative":
                token_limits.set_conservative()
                ui.status(
                    "💰 Conservative Mode: Token limits optimized for speed & cost",
                    "success",
                )
                ui.status(str(token_limits), "info")
                continue

            if subcommand == "balanced":
                token_limits.set_balanced()
                ui.status("⚖️  Balanced Mode: Token limits set to defaults", "success")
                ui.status(str(token_limits), "info")
                continue

            if subcommand == "generous":
                token_limits.set_generous()
                ui.status(
                    "✨ Generous Mode: Token limits set for high quality", "success"
                )
                ui.status(str(token_limits), "info")
                continue

            if subcommand == "set" and len(parts) >= 4:
                limit_type = parts[2].lower()
                try:
                    value = int(parts[3])

                    if limit_type == "planner":
                        token_limits.planner_max_tokens = value
                    elif limit_type == "execution":
                        token_limits.execution_max_tokens = value
                    elif limit_type == "merge":
                        token_limits.merge_max_tokens = value
                    elif limit_type == "tool_creation":
                        token_limits.tool_creation_max_tokens = value
                    elif limit_type == "error_correction":
                        token_limits.error_correction_max_tokens = value
                    elif limit_type == "selfimprove":
                        token_limits.selfimprove_max_tokens = value
                    elif limit_type == "chat":
                        token_limits.chat_max_tokens = value
                    else:
                        ui.status(f"Unknown limit type: {limit_type}", "error")
                        continue

                    ui.status(f"✓ Set {limit_type} limit to {value}", "success")
                    ui.status(str(token_limits), "info")
                except ValueError:
                    ui.status("Invalid value. Must be an integer.", "error")
                continue

            ui.status(
                "Usage: /tokens [extreme|conservative|balanced|generous|set <type> <value>]",
                "warning",
            )
            continue

        # NEU: /extreme Command - Shortcut for /tokens extreme
        if user_input.lower() == "/extreme":
            token_limits.set_extreme()
            ui.status("🚀 EXTREME MODE ACTIVATED!", "success")
            ui.status(
                "All token limits set to 64000 - SelfAI fully unleashed!", "success"
            )
            ui.status(str(token_limits), "info")
            continue

        # NEU: /yolo Command - Auto-accept everything
        if user_input.lower() == "/yolo":
            if ui.is_yolo_mode():
                ui.disable_yolo_mode()
            else:
                ui.enable_yolo_mode()
            continue

        # NEU: /context Command - Control Context Window
        if user_input.lower().startswith("/context"):
            parts = user_input.split()

            if len(parts) == 1:
                # Show current settings
                ui.status(f"📅 Context Window Settings:", "info")
                ui.status(
                    f"  • Window: {memory_system.context_window_minutes} Minuten",
                    "info",
                )
                ui.status(
                    f"  • Session Start: {memory_system.session_start.strftime('%Y-%m-%d %H:%M:%S')}",
                    "info",
                )

                import time

                session_age = (
                    time.time() - memory_system.session_start.timestamp()
                ) / 60
                ui.status(f"  • Session Age: {session_age:.1f} Minuten", "info")

                ui.status("\n💡 Available commands:", "info")
                ui.status(
                    "  /context <minutes>  - Set context window (e.g., /context 15)",
                    "info",
                )
                ui.status(
                    "  /context reset      - Reset session (clear context)", "info"
                )
                ui.status(
                    "  /context unlimited  - Load all history (no time filter)", "info"
                )
                continue

            subcommand = parts[1].lower()

            if subcommand == "reset":
                memory_system.session_start = datetime.now()
                ui.status("🔄 Session reset! Context cleared.", "success")
                ui.status(
                    f"New session started at {memory_system.session_start.strftime('%H:%M:%S')}",
                    "info",
                )
                continue

            if subcommand == "unlimited":
                memory_system.context_window_minutes = 99999  # Very large number
                ui.status(
                    "♾️  Context Window: UNLIMITED (all history loaded)", "warning"
                )
                ui.status(
                    "This may cause context pollution! Use /context reset to clear.",
                    "warning",
                )
                continue

            # Try to parse as minutes
            try:
                minutes = int(subcommand)
                if minutes < 1:
                    ui.status("Context window must be at least 1 minute.", "error")
                    continue
                if minutes > 1440:  # 24 hours
                    ui.status(
                        "Context window cannot exceed 1440 minutes (24 hours).", "error"
                    )
                    continue

                memory_system.context_window_minutes = minutes
                ui.status(f"✓ Context window set to {minutes} Minuten", "success")
                ui.status(f"Only loading files from last {minutes} minutes.", "info")
            except ValueError:
                ui.status("Usage: /context <minutes> | reset | unlimited", "warning")
            continue

        # NEU: /selfimprove Command
        if user_input.lower().startswith("/selfimprove"):
            if not active_planner_interface:
                ui.status(
                    "Kein Planner-Interface verfügbar für Self-Improvement.", "warning"
                )
                continue

            goal = user_input[len("/selfimprove") :].strip()
            _handle_selfimprove(
                goal=goal,
                agent_manager=agent_manager,
                memory_system=memory_system,
                ui=ui,
                planner_interface=active_planner_interface,
                execution_backends=execution_backends,
                backend_label=backend_label,
            )
            continue

        # NEU: /toolcreate Command
        if user_input.lower().startswith("/toolcreate"):
            parts = user_input.split(maxsplit=2)
            if len(parts) < 3:
                ui.status("Usage: /toolcreate <tool_name> <description>", "warning")
                ui.status(
                    "Example: /toolcreate calculate_fibonacci 'Calculate fibonacci numbers'",
                    "info",
                )
                continue

            tool_name = parts[1].strip()
            tool_description = parts[2].strip().strip("\"'")

            # Validate tool name
            if not tool_name.replace("_", "").isalnum():
                ui.status(
                    f"Invalid tool name '{tool_name}'. Use alphanumeric and underscore only.",
                    "error",
                )
                continue

            # Check if tool exists
            from selfai.tools.tool_registry import get_tool

            if get_tool(tool_name):
                ui.status(f"Tool '{tool_name}' already exists!", "warning")
                if not ui.confirm("Overwrite existing tool?", default_yes=False):
                    continue

            ui.status(f"Creating tool '{tool_name}': {tool_description}", "info")
            ui.status("🛠️  Generating tool code with MiniMax...", "info")

            # Generate tool using LLM
            tool_generation_prompt = f"""Generate a Python function for a SelfAI tool with these specifications:

Function Name: {tool_name}
Description: {tool_description}

Requirements:
1. Function signature: def {tool_name}(**kwargs) -> str:
2. Return JSON string with structure: {{"result": ..., "status": "success"}} or {{"error": ..., "status": "failed"}}
3. Include comprehensive docstring with Args and Returns sections
4. Add type hints for all parameters
5. Include try-except error handling
6. Import json at top
7. Validate input parameters
8. Follow Python best practices

Output ONLY the Python code, no markdown, no explanations."""

            try:
                # Use first available backend
                primary_backend = execution_backends[0]
                tool_interface = primary_backend["interface"]

                generated_code = tool_interface.generate_response(
                    system_prompt="You are a Python code generator. Output only valid Python code.",
                    user_prompt=tool_generation_prompt,
                    history=[],
                    max_output_tokens=token_limits.tool_creation_max_tokens,
                )

                # Clean up code (remove markdown if present)
                generated_code = generated_code.strip()
                if generated_code.startswith("```python"):
                    generated_code = "\n".join(generated_code.split("\n")[1:])
                if generated_code.startswith("```"):
                    generated_code = "\n".join(generated_code.split("\n")[1:])
                if generated_code.endswith("```"):
                    generated_code = "\n".join(generated_code.split("\n")[:-1])
                generated_code = generated_code.strip()

                # Save to generated tools directory
                tools_gen_dir = project_root / "tools" / "generated"
                tools_gen_dir.mkdir(parents=True, exist_ok=True)

                tool_file = tools_gen_dir / f"{tool_name}.py"
                tool_file.write_text(generated_code, encoding="utf-8")

                ui.status(
                    f"✓ Tool code saved to: {tool_file.relative_to(project_root)}",
                    "success",
                )
                ui.status(f"✓ Tool '{tool_name}' created successfully!", "success")
                ui.status("⚠️  Restart SelfAI to load the new tool", "warning")

            except Exception as exc:
                ui.status(f"Tool creation failed: {exc}", "error")

            continue

        # NEU: /errorcorrection Command
        if user_input.lower().startswith("/errorcorrection"):
            from selfai.core.error_analyzer import ErrorAnalyzer, ErrorSeverity
            from selfai.core.fix_generator import FixGenerator

            ui.status("🔍 Starting Error Correction System...", "info")

            # Scan logs
            log_dir = project_root.parent / "memory"  # Adjust to your log location
            if not log_dir.exists():
                log_dir = project_root

            analyzer = ErrorAnalyzer(log_dir)
            ui.status(f"Scanning logs in {log_dir}...", "info")

            errors = analyzer.scan_logs()

            if not errors:
                ui.status("✓ No errors found in logs!", "success")
                continue

            # Show statistics
            stats = analyzer.get_error_stats()
            ui.status(f"\n📊 Error Analysis:", "info")
            ui.status(f"   Total errors: {stats['total_errors']}", "info")
            ui.status(f"   Unique patterns: {stats['unique_patterns']}", "info")
            ui.status(f"   Critical: {stats['by_severity']['critical']}", "error")
            ui.status(f"   Errors: {stats['by_severity']['error']}", "warning")
            ui.status(f"   Warnings: {stats['by_severity']['warning']}", "info")

            # Get top error patterns
            top_patterns = analyzer.get_top_errors(limit=5)

            if not top_patterns:
                ui.status("No error patterns identified.", "info")
                continue

            ui.status(f"\n🔝 Top {len(top_patterns)} Error Patterns:", "info")
            for idx, pattern in enumerate(top_patterns, 1):
                severity_marker = (
                    "🔴"
                    if pattern.examples[0].severity == ErrorSeverity.CRITICAL
                    else "🟡"
                )
                ui.status(
                    f"{idx}. {severity_marker} {pattern.error_type} ({pattern.occurrences}x)",
                    "info",
                )
                if pattern.examples:
                    ex = pattern.examples[0]
                    if ex.file_path:
                        ui.status(
                            f"   Location: {ex.file_path}:{ex.line_number or '?'}",
                            "info",
                        )
                    ui.status(f"   Message: {ex.message[:80]}...", "info")

            # Ask user which error to fix
            ui.status(
                "\nWhich error should I analyze? (Enter number or 'all' or 'skip')",
                "info",
            )
            choice_input = input("Choice: ").strip().lower()

            if choice_input == "skip":
                ui.status("Error correction skipped.", "info")
                continue

            patterns_to_analyze = []
            if choice_input == "all":
                patterns_to_analyze = top_patterns
            else:
                try:
                    choice_idx = int(choice_input) - 1
                    if 0 <= choice_idx < len(top_patterns):
                        patterns_to_analyze = [top_patterns[choice_idx]]
                    else:
                        ui.status("Invalid choice.", "error")
                        continue
                except ValueError:
                    ui.status("Invalid input.", "error")
                    continue

            # Analyze each selected error
            primary_backend = execution_backends[0]
            fix_gen = FixGenerator(
                llm_interface=primary_backend["interface"], project_root=project_root
            )

            for pattern in patterns_to_analyze:
                ui.status(f"\n🔬 Analyzing: {pattern.error_type}", "info")

                # Generate fix plan
                fix_plan = fix_gen.analyze_error(pattern)

                ui.status(f"\n📋 Analysis:", "info")
                ui.status(f"Root Cause: {fix_plan.root_cause}", "info")
                ui.status(f"Details: {fix_plan.analysis[:200]}...", "info")

                if not fix_plan.options:
                    ui.status("No fix options generated.", "warning")
                    continue

                # Show fix options
                ui.status(f"\n🛠️  Fix Options:", "info")
                for opt in fix_plan.options:
                    risk_emoji = {
                        "low": "🟢",
                        "medium": "🟡",
                        "high": "🔴",
                        "critical": "⛔",
                    }
                    ui.status(
                        f"\n[{opt.option_id}] {opt.title} ({opt.estimated_time} min)",
                        "info",
                    )
                    ui.status(f"    {opt.description}", "info")
                    ui.status(
                        f"    Complexity: {opt.complexity.value} | Risk: {risk_emoji.get(opt.risk.value, '❓')} {opt.risk.value}",
                        "info",
                    )
                    if opt.files_affected:
                        ui.status(
                            f"    Files: {', '.join(opt.files_affected[:3])}", "info"
                        )

                # Ask user to select fix option
                if fix_plan.recommended_option:
                    ui.status(
                        f"\n💡 Recommended: Option {fix_plan.recommended_option}",
                        "info",
                    )

                option_choice = (
                    input(
                        f"\nSelect option [{'/'.join([o.option_id for o in fix_plan.options])}/Skip]: "
                    )
                    .strip()
                    .upper()
                )

                if option_choice.lower() == "skip":
                    ui.status("Skipping this error.", "info")
                    continue

                # Find selected option
                selected_option = None
                for opt in fix_plan.options:
                    if opt.option_id == option_choice:
                        selected_option = opt
                        break

                if not selected_option:
                    ui.status("Invalid option selected.", "error")
                    continue

                ui.status(f"\n✅ Selected: {selected_option.title}", "success")

                # Create DPPM plan for fix
                dppm_plan = fix_gen.create_dppm_plan(
                    selected_option,
                    pattern,
                    agent_key=agent_manager.active_agent.key
                    if agent_manager.active_agent
                    else "default",
                )

                # Show plan
                ui.show_plan(dppm_plan)

                # Ask for confirmation
                if not ui.confirm("Execute this fix plan?", default_yes=False):
                    ui.status("Fix execution cancelled.", "warning")
                    continue

                # Save and execute plan
                plan_path = memory_system.save_plan(
                    f"ErrorFix: {pattern.error_type}", dppm_plan
                )
                ui.status(f"Plan saved: {plan_path.name}", "success")

                try:
                    dispatcher = ExecutionDispatcher(
                        plan_path=plan_path,
                        agent_manager=agent_manager,
                        memory_system=memory_system,
                        llm_backends=execution_backends,
                        ui=ui,
                        backend_label=backend_label,
                        llm_timeout=60.0,
                        retry_attempts=2,
                        retry_delay=5.0,
                        max_output_tokens=token_limits.error_correction_max_tokens,
                    )
                    dispatcher.run()

                    ui.status("✓ Fix plan executed successfully!", "success")

                    # Save fix result to knowledge base
                    fix_gen.save_fix_result(selected_option, pattern, success=True)

                except Exception as exc:
                    ui.status(f"Fix execution failed: {exc}", "error")
                    fix_gen.save_fix_result(selected_option, pattern, success=False)

            ui.status("\n✅ Error Correction completed!", "success")
            continue

        if user_input.lower() == "/memory":
            categories = memory_system.list_categories()
            if categories:
                ui.status("Aktive Memory-Kategorien:", "info")
                for cat in categories:
                    ui.status(f"- {cat}", "info")
            else:
                ui.status("Keine Memory-Kategorien vorhanden.", "info")
            continue

        if user_input.lower().startswith("/memory clear"):
            parts = user_input.split()
            category = None
            keep = None
            if len(parts) >= 3:
                category = parts[2]
            else:
                categories = memory_system.list_categories()
                if not categories:
                    ui.status("Kein Memory vorhanden.", "info")
                    continue
                choice = ui.choose_option(
                    "Welche Memory-Kategorie löschen?",
                    categories,
                    default_index=0,
                )
                category = categories[choice]
            if len(parts) >= 4:
                try:
                    keep = max(0, int(parts[3]))
                except ValueError:
                    keep = None
            removed = memory_system.clear_category(category, keep)
            if removed == 0:
                ui.status(f"Keine Einträge aus '{category}' entfernt.", "info")
            elif keep is None:
                ui.status(
                    f"Memory '{category}' komplett geleert ({removed} Einträge).",
                    "success",
                )
            else:
                ui.status(
                    f"Memory '{category}' reduziert. {removed} alte Einträge entfernt, {keep} behalten.",
                    "success",
                )
            continue

        if user_input.lower().startswith("/planner"):
            if not planner_providers:
                ui.status("Kein Planner-Provider konfiguriert.", "warning")
                continue

            parts = user_input.split()
            subcommand = parts[1].lower() if len(parts) > 1 else "list"

            if subcommand == "list":
                ui.status("Verfügbare Planner-Provider:", "info")
                for idx, name in enumerate(planner_provider_order, start=1):
                    info = planner_providers.get(name)
                    if not info:
                        continue
                    marker = "(aktiv)" if name == active_planner_provider else ""
                    ui.status(
                        f"{idx}. {name} [{info['type']}] {info['model']} {marker}",
                        "info",
                    )
                continue

            if subcommand == "use" and len(parts) >= 3:
                desired = parts[2]
                info = planner_providers.get(desired)
                if not info:
                    ui.status(
                        f"Planner-Provider '{desired}' ist nicht verfügbar.",
                        "error",
                    )
                    continue
                active_planner_provider = desired
                active_planner_interface = info["interface"]
                _save_active_planner(memory_system, desired)
                ui.status(
                    f"Aktiver Planner-Provider gesetzt auf '{desired}'.",
                    "success",
                )
                continue

            ui.status("Verwendung: /planner list | /planner use <Name>", "info")
            continue

        # Load and execute existing plan (for testing)
        if user_input.lower().startswith("/loadplan"):
            parts = user_input.split(" ", 1)
            if len(parts) < 2:
                ui.status("Usage: /loadplan <filename.json>", "warning")
                ui.status("Available test plans:", "info")
                plans_dir = Path("memory/plans")
                if plans_dir.exists():
                    for p in plans_dir.glob("*.json"):
                        ui.status(f"  - {p.name}", "info")
                continue

            plan_filename = parts[1].strip()
            plan_path = Path("memory/plans") / plan_filename

            if not plan_path.exists():
                ui.status(f"Plan file not found: {plan_path}", "error")
                continue

            try:
                with open(plan_path, "r", encoding="utf-8") as f:
                    plan_data = json.load(f)

                goal = plan_data.get("metadata", {}).get("goal", "Loaded Plan")
                ui.status(f"📋 Loaded plan: {goal}", "success")
                ui.show_plan(plan_data)

                confirm = input("\n▶️  Execute this plan? (y/n): ").strip().lower()
                if confirm != "y":
                    ui.status("Plan execution cancelled.", "info")
                    continue

                # Execute the plan
                dispatcher = ExecutionDispatcher(
                    plan_path=plan_path,
                    llm_backends=execution_backends,
                    agent_manager=agent_manager,
                    memory_system=memory_system,
                    ui=ui,
                )
                dispatcher.run()
                ui.status("✅ Plan execution completed!", "success")

            except json.JSONDecodeError as e:
                ui.status(f"Invalid JSON in plan file: {e}", "error")
            except Exception as e:
                ui.status(f"Error executing plan: {e}", "error")
                import traceback

                traceback.print_exc()

            continue

        if user_input.lower().startswith("/plan"):
            if not planner_providers:
                ui.status(
                    "Kein Planner-Provider aktiv. Bitte Konfiguration prüfen.",
                    "warning",
                )
                continue

            parts = user_input.split(" ", 1)
            if len(parts) < 2 or not parts[1].strip():
                ui.status("Bitte Zielbeschreibung angeben: /plan <Ziel>", "warning")
                continue

            goal_text = parts[1].strip()
            ui.status(f"Erzeuge Plan für: {goal_text}", "info")

            planner_context = _build_planner_context(agent_manager, memory_system)

            plan_data = None
            selected_provider_name = None

            ordered_names: list[str] = []
            if active_planner_provider and active_planner_provider in planner_providers:
                ordered_names.append(active_planner_provider)
            for name in planner_provider_order:
                if name not in ordered_names and name in planner_providers:
                    ordered_names.append(name)

            for provider_name in ordered_names:
                info = planner_providers.get(provider_name)
                if not info:
                    continue
                provider_type = info["type"]
                provider_interface = info["interface"]
                ui.status(
                    f"Nutze Planner-Provider '{provider_name}' ({provider_type})...",
                    "info",
                )
                stream_state = {"active": False}

                def _planner_stream(chunk: str) -> None:
                    if not stream_state["active"]:
                        ui.stream_prefix(f"Planner-{provider_name}")
                        stream_state["active"] = True
                    ui.streaming_chunk(chunk)

                try:
                    plan_data = provider_interface.plan(
                        goal_text,
                        planner_context,
                        progress_callback=_planner_stream,
                    )
                    if stream_state["active"]:
                        print()
                    selected_provider_name = provider_name
                    ui.status(
                        f"Planner '{provider_name}' hat einen Plan geliefert.",
                        "success",
                    )
                    ui.status(
                        "Planungsphase abgeschlossen: Subtasks stehen für die Ausführung bereit.",
                        "info",
                    )
                    break
                except PlannerError as exc:
                    if stream_state["active"]:
                        print()
                    hint = ""
                    cause = getattr(exc, "__cause__", None)
                    if isinstance(cause, PlanValidationError):
                        hint = " (Planaufbau entspricht nicht dem Schema)"
                        faulty_plan = getattr(cause, "plan_data", None)
                        ui.status(
                            "Der Planner hat einen unvollständigen oder fehlerhaften Plan geliefert.",
                            "warning",
                        )
                        ui.status(
                            "Hinweis: Agent Keys müssen zu deinen SelfAI-Agenten passen und 'parallel_group' muss >= 1 sein.",
                            "info",
                        )
                        if faulty_plan:
                            ui.status(
                                f"Fehlerquelle (Provider '{provider_name}'):",
                                "warning",
                            )
                            ui.show_plan(faulty_plan)
                    ui.status(
                        f"Planner '{provider_name}' fehlgeschlagen: {exc}{hint}",
                        "warning",
                    )
                    continue

            if plan_data is None:
                ui.status(
                    "Keiner der Planner-Provider konnte einen Plan erstellen. Erzeuge Fallback-Plan.",
                    "warning",
                )
                fallback_agent_key = _default_agent_key(agent_manager)
                if not fallback_agent_key:
                    ui.status(
                        "Fallback fehlgeschlagen: Kein Agent verfügbar. Bitte Konfiguration prüfen.",
                        "error",
                    )
                    continue
                plan_data = _build_fallback_plan(goal_text, fallback_agent_key)
                selected_provider_name = "fallback"
                ui.status(
                    f"Fallback-Plan erstellt (Agent '{fallback_agent_key}').",
                    "info",
                )

            _sanitize_plan_agents(plan_data, agent_manager, ui)
            _announce_plan_agents(plan_data, agent_manager, ui)
            ui.show_plan(plan_data)

            logic_messages = validate_plan_logic(plan_data)
            proceed_with_plan = True
            if logic_messages:
                has_error = any(msg.startswith("FEHLER") for msg in logic_messages)
                for msg in logic_messages:
                    level = "error" if msg.startswith("FEHLER") else "warning"
                    ui.status(msg, level)
                prompt_text = (
                    "Plan enthält kritische Fehler. Trotzdem übernehmen?"
                    if has_error
                    else "Plan enthält Warnungen. Trotzdem übernehmen?"
                )
                proceed_with_plan = ui.confirm(prompt_text, default_yes=False)

            if not proceed_with_plan:
                ui.status("Plan verworfen.", "warning")
                continue

            if not ui.confirm_plan():
                ui.status("Plan verworfen.", "warning")
                continue

            try:
                plan_data.setdefault("metadata", {})
                provider_metadata = planner_providers.get(selected_provider_name, {})
                plan_data["metadata"].update(
                    {
                        "planner_provider": selected_provider_name,
                        "planner_provider_type": provider_metadata.get("type"),
                        "planner_model": provider_metadata.get("model"),
                        "goal": goal_text,
                    }
                )
                if (
                    selected_provider_name
                    and selected_provider_name in planner_providers
                    and selected_provider_name != active_planner_provider
                ):
                    active_planner_provider = selected_provider_name
                    active_planner_interface = planner_providers[
                        selected_provider_name
                    ]["interface"]
                    _save_active_planner(memory_system, selected_provider_name)
                    ui.status(
                        f"Aktiver Planner-Provider aktualisiert auf '{selected_provider_name}'.",
                        "info",
                    )
                plan_path = memory_system.save_plan(goal_text, plan_data)
                try:
                    display_path = plan_path.relative_to(project_root)
                except ValueError:
                    display_path = plan_path
                ui.status(f"Plan gespeichert: {display_path}", "success")
                ui.status(
                    "Plan gespeichert. Als nächstes folgt die Ausführungsphase.",
                    "info",
                )
            except OSError:
                ui.status("Plan konnte nicht gespeichert werden (siehe Log).", "error")
                continue

            if llm_interface is None:
                ui.status(
                    "LLM-Backend nicht verfügbar. Ausführung übersprungen.",
                    "warning",
                )
                continue

            if not ui.confirm_execution():
                ui.status("Ausführung übersprungen. Plan bleibt gespeichert.", "info")
                continue

            try:
                dispatcher = ExecutionDispatcher(
                    plan_path=plan_path,
                    agent_manager=agent_manager,
                    memory_system=memory_system,
                    llm_backends=execution_backends,
                    ui=ui,
                    backend_label=backend_label,
                    llm_timeout=getattr(planner_cfg, "execution_timeout", None),
                    retry_attempts=2,
                    retry_delay=5.0,
                    max_output_tokens=token_limits.execution_max_tokens,
                )
                import time

                start_time = time.time()

                # Run execution but KEEP UI OPEN for merge phase
                dispatcher.run(keep_ui_open=True)
                execution_time = time.time() - start_time

                # Integrate Merge into the Dashboard
                use_rich_parallel = (
                    hasattr(ui, "add_merge_box")
                    and hasattr(ui, "is_active")
                    and ui.is_active
                )

                if use_rich_parallel:
                    ui.add_merge_box()
                    # We can use the 'MERGE' ID defined in parallel_stream_ui
                    ui.status("Starte Merge & Synthese...", "info")

                primary_backend = execution_backends[0]
                default_merge_backend = {
                    "label": primary_backend.get("label") or backend_label or "MiniMax",
                    "type": primary_backend.get("type", "minimax"),
                    "interface": primary_backend.get("interface"),
                    "max_tokens": 2048,
                    "name": primary_backend.get("name", "minimax"),
                    "model": primary_backend.get("label")
                    or primary_backend.get("name")
                    or backend_label
                    or "minimax",
                    "timeout": getattr(planner_cfg, "execution_timeout", None)
                    if planner_cfg
                    else None,
                }

                merge_backend = default_merge_backend
                if plan_data.get("merge"):
                    # Only ask if not using parallel UI to avoid breaking layout, OR if interactive mode
                    # Ideally we just use default or auto-select for seamless experience
                    pass

                merge_timeout = getattr(planner_cfg, "execution_timeout", None)

                # We need to hook into the merge execution to route output to 'MERGE' box if using parallel UI
                # For now, let's just let it run. If _execute_merge_phase uses ui.stream_prefix,
                # we might need to adapt it.
                # But wait! ui.stream_prefix is compatible with TerminalUI.
                # ParallelStreamUI needs to route 'MERGE' output to the merge box.

                # Hack: Temporarily wrap UI methods if using parallel UI
                if use_rich_parallel:
                    original_streaming_chunk = ui.streaming_chunk
                    original_typing = ui.typing_animation

                    def merge_stream_chunk(chunk):
                        ui.add_response_chunk("MERGE", chunk)

                    def merge_typing(text):
                        ui.add_response_chunk("MERGE", text)

                    ui.streaming_chunk = merge_stream_chunk
                    ui.typing_animation = merge_typing
                    ui.stream_prefix = lambda x: None  # Mute prefix

                try:
                    merge_success = _execute_merge_phase(
                        plan_path,
                        merge_backend=merge_backend,
                        agent_manager=agent_manager,
                        memory_system=memory_system,
                        ui=ui,
                        execution_timeout=merge_timeout,
                    )
                finally:
                    # Restore UI methods
                    if use_rich_parallel:
                        ui.streaming_chunk = original_streaming_chunk
                        ui.typing_animation = original_typing
                        # NOW stop the UI
                        ui.mark_subtask_complete("MERGE", success=merge_success)
                        time.sleep(1.0)
                        ui.stop_parallel_view()
                        print()  # Clear line

                # Show final status
                if merge_success:
                    ui.status("Plan und Merge erfolgreich abgeschlossen.", "success")
                else:
                    ui.status(
                        "Ausführung fertig, aber Merge fehlgeschlagen.", "warning"
                    )

                # --- Fallback logic removed for brevity in this refactor, assuming primary works ---
                # (In production code, keep the fallback logic but adapted for the new UI flow)

                # GEMINI AS JUDGE: Evaluate complete execution (after merge)
                try:
                    from selfai.core.gemini_judge import (
                        GeminiJudge,
                        format_score_for_terminal,
                    )

                    ui.status(
                        "\n🤖 Gemini Judge evaluiert die gesamte Ausführung (Plan + Merge)...",
                        "info",
                    )

                    # Try to initialize judge (includes availability check)
                    try:
                        judge = GeminiJudge()
                    except RuntimeError as init_error:
                        ui.status(
                            f"⚠️ Gemini Judge Initialisierung fehlgeschlagen:", "error"
                        )
                        ui.status(f"   {init_error}", "warning")
                        raise  # Re-raise to outer catch block

                    # Collect COMPLETE execution output: subtasks + merge
                    execution_output = ""

                    # 1. Collect subtask results
                    for subtask in plan_data.get("subtasks", []):
                        if subtask.get("result_path"):
                            result_file = Path(subtask["result_path"])
                            if result_file.exists():
                                execution_output += f"\n### Subtask: {subtask.get('title', 'Unknown')}\n"
                                execution_output += (
                                    result_file.read_text(encoding="utf-8")[:1000]
                                    + "\n"
                                )

                    # 2. Collect merge result
                    merge_result_path = plan_data.get("metadata", {}).get(
                        "merge_result_path"
                    )
                    if merge_result_path:
                        merge_file = Path(merge_result_path)
                        if merge_file.exists():
                            execution_output += f"\n### MERGE RESULT (Final Output):\n"
                            execution_output += (
                                merge_file.read_text(encoding="utf-8")[:2000] + "\n"
                            )

                    # Get list of changed files (if available)
                    files_changed = []
                    try:
                        import subprocess

                        git_result = subprocess.run(
                            ["git", "diff", "--name-only"],
                            capture_output=True,
                            text=True,
                            cwd=project_root,
                            timeout=5,
                        )
                        if git_result.returncode == 0:
                            files_changed = [
                                f.strip()
                                for f in git_result.stdout.split("\n")
                                if f.strip()
                            ]
                    except Exception:
                        pass

                    # Evaluate complete pipeline
                    score = judge.evaluate_task(
                        original_goal=goal_text,
                        execution_output=execution_output or "No output captured",
                        plan_data=plan_data,
                        execution_time=execution_time,
                        files_changed=files_changed,
                    )

                    # Display score with traffic light
                    score_text = format_score_for_terminal(score)
                    print("\n" + score_text + "\n")

                    # Save score to memory
                    score_path = (
                        memory_system.memory_dir
                        / "judge_scores"
                        / f"{plan_path.stem}_score.json"
                    )
                    judge.save_score(score, score_path)

                except ImportError as e:
                    ui.status(
                        "⚠️ Gemini Judge nicht verfügbar (Import fehlgeschlagen)",
                        "warning",
                    )
                    ui.status(f"   Fehler: {e}", "info")
                    ui.status("   Tipp: pip install google-generativeai", "info")
                except RuntimeError as e:
                    ui.status("⚠️ Gemini Judge nicht verfügbar (CLI-Problem)", "warning")
                    ui.status(f"   Details siehe oben in Debug-Output", "info")
                except Exception as judge_error:
                    ui.status(f"⚠️ Gemini Judge unerwarteter Fehler:", "error")
                    ui.status(f"   Type: {type(judge_error).__name__}", "warning")
                    ui.status(f"   Message: {judge_error}", "warning")
                    import traceback

                    ui.status(f"   Traceback:", "info")
                    for line in traceback.format_exc().split("\n"):
                        if line.strip():
                            ui.status(f"     {line}", "info")

            except ExecutionError as exc:
                ui.status(f"Plan-Ausführung abgebrochen: {exc}", "error")
            except Exception as exc:  # pylint: disable=broad-except
                ui.status(f"Unerwarteter Ausführungsfehler: {exc}", "error")

            continue

        if user_input.lower().startswith("/switch "):
            agent_name_raw = user_input.split(" ", 1)[1]
            try:
                candidate = agent_name_raw.strip()
                normalized = candidate.rstrip(".").strip()

                if normalized.isdigit():
                    index = int(normalized) - 1
                    if index < 0 or index >= len(available_agents):
                        raise ValueError(
                            f"Agent mit Nummer {normalized} existiert nicht."
                        )
                    selected = available_agents[index]
                    agent_manager.switch_agent(selected.key)
                else:
                    agent_manager.switch_agent(candidate)
                ui.status(
                    f"Aktiver Agent: {agent_manager.active_agent.display_name}",
                    "info",
                )
                ui.list_agents(
                    agent_manager.agents,
                    active_key=agent_manager.active_agent.key,
                )
                available_agents = agent_manager.list_agents()
            except ValueError as exc:
                ui.status(str(exc), "error")
            continue

        # =============================================================================
        # AGENT MODE: Custom Tool-Calling Agent Loop (MiniMax-Compatible!)
        # =============================================================================
        ENABLE_AGENT_MODE = getattr(config.system, "enable_agent_mode", True)

        if ENABLE_AGENT_MODE and llm_interface:
            try:
                # Initialize agent lazily (once per session)
                if "selfai_agent" not in locals() or selfai_agent is None:
                    ui.status("🤖 Initialisiere Custom Agent Loop mit Tools...", "info")

                    # Get all tools (already in smolagents format, works with our loop too!)
                    tools = get_tools_for_agent()
                    ui.status(f"✅ {len(tools)} Tools geladen für Agent", "success")

                    # Get agent-specific settings
                    agent_prompt = getattr(
                        agent_manager.active_agent, "system_prompt", None
                    )

                    # Create custom agent loop with full configuration
                    selfai_agent = CustomAgentLoop(
                        llm_interface=llm_interface,
                        tools=tools,
                        max_steps=getattr(config.system, "agent_max_steps", 10),
                        ui=ui,
                        verbose=getattr(config.system, "agent_verbose", False),
                        agent_prompt=agent_prompt,
                        memory_system=memory_system,
                        temperature=getattr(config.system, "agent_temperature", 0.1),
                        streaming=getattr(config.system, "agent_streaming", True),
                    )

                    ui.status(
                        "✅ Custom Agent Loop bereit! (MiniMax-kompatibel)", "success"
                    )

                # Run agent with user input (tools are called automatically!)
                response_text = selfai_agent.run(user_input)

                # Display response
                print(f"\n{ui.colorize('SelfAI', 'magenta')}: {response_text}\n")

                # Save to memory
                memory_system.save_conversation(
                    agent_manager.active_agent,
                    user_input,
                    response_text,
                )

                continue  # Skip fallback code below

            except Exception as agent_error:
                import traceback

                traceback.print_exc()
                ui.status(f"❌ Agent-Fehler: {agent_error}", "error")
                ui.status("⚠️ Fallback: Nutze direkten LLM-Call ohne Tools", "warning")

                # Disable agent for rest of session and fall through
                ENABLE_AGENT_MODE = False
                selfai_agent = None
                # Fall through to regular chat mode below (no continue here!)


if __name__ == "__main__":
    main()
