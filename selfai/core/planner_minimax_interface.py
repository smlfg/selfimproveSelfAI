"""MiniMax-basierter Planner für SelfAI."""

from __future__ import annotations

import json
import re
import textwrap
from dataclasses import dataclass
from typing import Any, Callable, Dict, Iterable

import httpx

from selfai.core.planner_validator import (
    DEFAULT_ENGINES,
    PlanValidationError,
    validate_plan_structure,
)
from selfai.tools.tool_registry import get_all_tool_schemas


class PlannerError(RuntimeError):
    """Basisklasse für Planner-bezogene Fehler."""


@dataclass
class PlannerContext:
    agents: Iterable[dict]
    memory_summary: str


class PlannerMinimaxInterface:
    """Kommuniziert mit MiniMax Chat Completions API, um DPPM-Pläne zu generieren."""

    def __init__(
        self,
        *,
        base_url: str,
        model: str,
        timeout: float,
        max_tokens: int,
        headers: Dict[str, str] | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self.max_tokens = max_tokens
        self.generate_url = f"{self.base_url}/chat/completions"
        self.headers = headers or {}

    def healthcheck(self) -> None:
        """Prüft, ob die MiniMax API erreichbar ist."""
        try:
            with httpx.Client(timeout=min(5.0, self.timeout)) as client:
                response = client.get(
                    f"{self.base_url}/models",
                    headers=self.headers or None,
                )
                response.raise_for_status()
        except Exception as exc:  # pragma: no cover - defensive
            raise PlannerError(f"MiniMax Healthcheck fehlgeschlagen: {exc}") from exc

    def _build_prompt(self, goal: str, context: PlannerContext) -> str:
        agent_lines = []
        for agent in context.agents:
            agent_lines.append(
                f"- {agent['key']}: {agent.get('display_name', agent['key'])} – {agent.get('description', '').strip() or 'kein Kommentar'}"
            )
        agents_text = "\n".join(agent_lines) if agent_lines else "- Keine Agenten geladen"

        tool_schemas = get_all_tool_schemas()
        if tool_schemas:
            tool_lines = []
            for schema in tool_schemas:
                name = schema.get("name", "unbenannt")
                description = (schema.get("description") or "").strip()
                tool_lines.append(f"- {name}: {description or 'keine Beschreibung'}")
            tools_overview = "\n".join(tool_lines)
        else:
            tools_overview = "- Keine Tools registriert."

        schemas = get_all_tool_schemas()
        if schemas:
            allowed_tool_lines = ["- " + schema.get("name", "") for schema in schemas]
            allowed_tool_lines.append("- final_answer")
            allowed_tool_names = "\n".join(allowed_tool_lines)
        else:
            allowed_tool_names = "- final_answer"

        template = textwrap.dedent(
            """
            Du agierst als DPPM-Planer (Decompose–Parallel Plan–Merge) für SelfAI und erzeugst ausschließlich JSON in folgendem Schema:
            {{
              "subtasks": [
                    {{
                      "id": "S1",
                      "title": "kurzer Titel",
                      "objective": "prägnante Zielbeschreibung (max. 160 Zeichen)",
                      "agent_key": "code_helfer",
                      "engine": "minimax",
                      "parallel_group": 1,
                      "depends_on": [],
                      "notes": "optionale Hinweise (max. 160 Zeichen)"
                    }}
                  ],
                  "merge": {{
                    "strategy": "Kurze Beschreibung der Zusammenführung (max. 160 Zeichen)",
                    "steps": [
                      {{
                        "title": "Schritt",
                        "description": "konkrete Merge-Aktion (max. 160 Zeichen)",
                        "depends_on": ["S1", "S2"]
                      }}
                    ]
                  }}
                }}

                DPPM-Vorgaben:
                1. Decompose – zerlege die Aufgabe in unabhängige Subtasks (typisch 2-8, bei komplexen Aufgaben auch mehr).
                2. Parallel Plan – weise parallele Arbeiten über "parallel_group" zu und nutze "depends_on" nur für echte Abhängigkeiten.
                3. Merge – definiere eine konsistente Zusammenführung des globalen Plans.

                PARALLELISIERUNG (WICHTIG für Geschwindigkeit):
                - parallel_group: Niedrigere Zahlen = früher starten
                - Gleiche parallel_group = Tasks laufen GLEICHZEITIG (2-3x schneller!)
                - Beispiel: S1 (group 1), S2+S3+S4 (group 2, parallel!), S5 (group 3, merge)
                - OPTIMIERE für Parallelität: Zerlege so, dass viele Tasks parallel laufen!
                - Nutze depends_on NUR für echte Abhängigkeiten

                BESTE PRAKTIKEN für Task-Dekomposition:
                - Zerlege in UNABHÄNGIGE Subtasks (für Parallelisierung)
                - Jeder Subtask sollte in 1-2 Minuten erledigt sein
                - Bei Listen/Mehrfach-Items: Erstelle parallele Subtasks ("Test Feature A", "Test Feature B")
                - Vermeide monolithische Subtasks ("Implementiere alles")
                - Nutze frühe parallel_groups für schnelles Feedback

                Regeln:
                - Gib ausschließlich reines JSON zurück, ohne Markdown, Backticks oder Text vor/nach dem JSON.
                - Jeder String muss eine Zeile bleiben und <= 160 Zeichen haben.
                - Verwende als "agent_key" nur die geladenen Agenten.
                - Verwende als "engine" primär: "minimax" (für LLM-Tasks), "smolagent" (für Tool-Tasks). Legacy: "anythingllm", "qnn", "cpu".
                - Liefere die finale JSON ausschließlich in der Antwort-Ausgabe (nicht im Thinking-Bereich).
                - Analysiere die Anforderung präzise. Wenn explizite Detailanweisungen (z. B. "letter for letter", "Schritt für Schritt", "einzeln") vorkommen, bilde Subtasks, die diese Vorgaben exakt widerspiegeln.
                - Jeder Subtask muss einen eigenen Mehrwert liefern; vermeide redundante oder identische Ziele.
                - Die Merge-Strategie muss beschreiben, wie die Ergebnisse zusammengeführt werden (nicht nur "kombiniere alle Outputs").
                - Beende die Ausgabe direkt nach dem JSON mit der Zeichenkette END_OF_PLAN.
                - Wenn die Anforderung mehrdeutig ist, erstelle zuerst einen Klärungs-Subtask (z. B. "Anforderung klären") mit einem passenden Agenten und notiere offene Fragen oder Annahmen.
                - Stelle sicher, dass Subtasks, die auf den Ergebnissen vorangehender Schritte basieren, die entsprechenden IDs in "depends_on" aufführen.
                - Wenn ein Subtask externe Informationen beschaffen, recherchieren, Dateien lesen oder Berechnungen mit Tools durchführen soll, setze "engine" auf "smolagent".
                - Für Subtasks mit "engine": "smolagent" füge das Feld "tools": ["tool_name"] hinzu und nutze ausschließlich folgende Tool-Namen (keine anderen erfinden):
{tool_name_list}
                - Verwende "engine": "minimax" für reine Text- oder Planungsaufgaben ohne Toolzugriff.

                AIDER TOOL BEST PRACTICES (bei run_aider_task/run_aider_architect):
                - Ein Task = Ein File = Eine Änderung! Für mehrere Files: mehrere parallele Subtasks erstellen
                - Konkrete task_description mit Funktionsnamen (z.B. "Add try-except to init_db() in src/db.py")
                - Nur 1 file im "files" Parameter! NIE mehrere Dateien kommasepariert
                - timeout: 180s für einfache Tasks, 240s für komplexe (default 180 ist meist ok)
                - Bevorzuge mehrere kleine parallele Aider-Tasks über einen großen komplexen Task
                - GUTER task: "Add type hints to calculate() function" - SCHLECHTER: "Improve code quality"
                - run_aider_task für Code-Änderungen, run_aider_architect für Design-Fragen ohne Code-Edit
                - Bei komplexen Änderungen: NICHT Aider nutzen, sondern engine: minimax mit detaillierter Beschreibung

                SelfAI Agenten:
                {agent_overview}

                Memory-Zusammenfassung:
                {memory_summary}

            Verfügbare Tools:
            {tools_overview}

                Ziel:
                {goal}
            """
        ).strip()

        return template.format(
            agent_overview=agents_text,
            memory_summary=context.memory_summary or "(kein Memory verfügbar)",
            tools_overview=tools_overview,
            goal=goal.strip(),
            tool_name_list=allowed_tool_names,
        )

    @staticmethod
    def _strip_code_fences(text: str) -> str:
        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned[3:].strip()
            if "\n" in cleaned:
                cleaned = cleaned.split("\n", 1)[1]
            cleaned = cleaned.strip()
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3].strip()
        return cleaned

    def plan(
        self,
        goal: str,
        context: PlannerContext,
        progress_callback: Callable[[str], None] | None = None,
    ) -> Dict[str, Any]:
        """Erzeugt einen Plan über die MiniMax Chat Completions API."""

        # Model String: "MiniMax-M2" (OHNE "openai/" prefix für API Body!)
        model_name = self.model.replace("openai/", "")

        # Prompt erstellen
        prompt_content = self._build_prompt(goal, context)

        # Chat Completions Format
        messages = [
            {"role": "system", "content": "Du bist ein DPPM-Planer für SelfAI. Antworte ausschließlich mit gültigem JSON im spezifizierten Schema."},
            {"role": "user", "content": prompt_content}
        ]

        payload = {
            "model": model_name,
            "messages": messages,
            "max_tokens": self.max_tokens,
            "temperature": 0.1,
            "response_format": {"type": "json_object"}
        }

        raw_response = ""

        try:
            with httpx.Client(timeout=self.timeout) as client:
                if progress_callback:
                    # Vereinfachte Version ohne Streaming vorerst
                    response = client.post(
                        self.generate_url,
                        json=payload,
                        headers=self.headers or None,
                    )
                    response.raise_for_status()
                    body = response.json()
                    raw_response = body.get("choices", [{}])[0].get("message", {}).get("content", "")
                    
                    # Progress callback mit Rohinhalt
                    if raw_response:
                        progress_callback(raw_response)
                    
                    return self._parse_plan(raw_response, body_extra=body, context=context)
                else:
                    response = client.post(
                        self.generate_url,
                        json=payload,
                        headers=self.headers or None,
                    )
                    response.raise_for_status()
                    body = response.json()
                    raw_response = body.get("choices", [{}])[0].get("message", {}).get("content", "")
                    
                    if not raw_response:
                        raise PlannerError(f"MiniMax-Response enthält kein 'content'-Feld: {body}")
                    
                    return self._parse_plan(raw_response, body_extra=body, context=context)
        except httpx.TimeoutException as exc:
            raise PlannerError(
                f"MiniMax antwortete nicht innerhalb von {self.timeout} Sekunden."
            ) from exc
        except httpx.HTTPStatusError as exc:
            raise PlannerError(
                f"MiniMax HTTP-Fehler {exc.response.status_code}: {exc.response.text}"
            ) from exc
        except httpx.RequestError as exc:
            raise PlannerError(f"Fehler beim Kontaktieren von MiniMax: {exc}") from exc

        if not raw_response:
            raise PlannerError("MiniMax lieferte keine Daten.")

        return self._parse_plan(raw_response, context=context)

    def _parse_plan(
        self,
        raw_response: str,
        body_extra: Dict[str, Any] | None = None,
        context: PlannerContext | None = None,
    ) -> Dict[str, Any]:
        context = context or PlannerContext(agents=[], memory_summary="")

        # 1. Strip <think> tags
        cleaned = re.sub(r'<think>.*?</think>', '', raw_response, flags=re.DOTALL)
        cleaned = cleaned.strip()

        # 2. Try JSON parsing first
        try:
            # Strip code fences
            cleaned = self._strip_code_fences(cleaned)
            
            # Check if we still have a plan structure
            if "END_OF_PLAN" in cleaned:
                cleaned = cleaned.split("END_OF_PLAN", 1)[0].strip()
            
            # Try to parse JSON
            plan_data = json.loads(cleaned)
            
            # Validate the JSON structure
            allowed_agents = {agent.get("key") for agent in context.agents if agent.get("key")}
            default_agent = next(iter(allowed_agents), "code_helfer")
            
            for task in plan_data.get("subtasks", []) or []:
                if not isinstance(task.get("agent_key"), str) or not task.get("agent_key"):
                    task["agent_key"] = default_agent
                try:
                    pg_value = int(task.get("parallel_group", 1))
                    if pg_value < 1:
                        task["parallel_group"] = 1
                except (TypeError, ValueError):
                    task["parallel_group"] = 1
                if not isinstance(task.get("notes"), str):
                    task["notes"] = ""
            
            try:
                validate_plan_structure(
                    plan_data,
                    allowed_agent_keys=allowed_agents,
                    allowed_engines=DEFAULT_ENGINES,
                )
            except PlanValidationError as exc:
                # If validation fails, try fallback plan
                pass
            else:
                # JSON parsing and validation successful
                return plan_data
                
        except (json.JSONDecodeError, PlanValidationError, Exception):
            # JSON parsing failed, will try fallback
            pass

        # 3. FALLBACK: Create simple plan from response text
        goal = "Unbekanntes Ziel"
        if hasattr(context, 'memory_summary') and context.memory_summary:
            goal = context.memory_summary[:100] + "..." if len(context.memory_summary) > 100 else context.memory_summary
        
        # Extract potential information from the cleaned response
        response_text = cleaned[:500] if cleaned else "Keine Antwort verfügbar"
        
        # Create fallback plan
        fallback_plan = {
            "subtasks": [
                {
                    "id": "S1",
                    "title": "Anforderungen analysieren",
                    "objective": f"Analysiere die Anforderung: {goal}",
                    "agent_key": "code_helfer",
                    "engine": "minimax",
                    "parallel_group": 1,
                    "depends_on": [],
                    "notes": f"Analysiere Eingabe: {response_text[:100]}"
                },
                {
                    "id": "S2",
                    "title": "Lösung erarbeiten",
                    "objective": f"Erarbeite eine Lösung für: {goal}",
                    "agent_key": "code_helfer",
                    "engine": "minimax",
                    "parallel_group": 2,
                    "depends_on": ["S1"],
                    "notes": f"Basierend auf Analyse: {response_text[:100]}"
                }
            ],
            "merge": {
                "strategy": "Kombiniere Analyse und Lösung",
                "steps": [
                    {
                        "title": "Finale Antwort",
                        "description": "Zusammenführen aller Ergebnisse",
                        "depends_on": ["S2"]
                    }
                ]
            },
            "metadata": {
                "planner_provider": "minimax-planner",
                "planner_model": self.model,
                "goal": goal,
                "fallback": True,
                "reason": "JSON-Parsing fehlgeschlagen, Fallback-Plan erstellt"
            }
        }
        
        return fallback_plan
