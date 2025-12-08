"""Ollama-basierter Planner für SelfAI."""

from __future__ import annotations

import json
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


class PlannerOllamaInterface:
    """Kommuniziert mit einem Ollama-Endpunkt, um DPPM-Pläne zu generieren."""

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
        self.generate_url = f"{self.base_url}/api/generate"
        self.headers = headers or {}

    def healthcheck(self) -> None:
        """Prüft, ob der Ollama-Server erreichbar ist."""
        try:
            with httpx.Client(timeout=min(5.0, self.timeout)) as client:
                response = client.get(
                    f"{self.base_url}/api/tags",
                    headers=self.headers or None,
                )
                response.raise_for_status()
        except Exception as exc:  # pragma: no cover - defensive
            raise PlannerError(f"Ollama Healthcheck fehlgeschlagen: {exc}") from exc

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
                1. Decompose – zerlege die Aufgabe in so viele Subtasks wie nötig für optimale Parallelisierung.
                2. Parallel Plan – weise parallele Arbeiten über "parallel_group" zu und nutze "depends_on" nur für echte Abhängigkeiten.
                3. Merge – definiere eine konsistente Zusammenführung des globalen Plans.

                PARALLELISIERUNG (WICHTIG für Geschwindigkeit):
                - parallel_group: Niedrigere Zahlen = früher starten
                - Gleiche parallel_group = Tasks laufen GLEICHZEITIG (2-3x schneller!)
                - Beispiel paralleler Plan:
                  {{
                    "subtasks": [
                      {{"id": "S1", "parallel_group": 1, "depends_on": []}},  // Läuft solo
                      {{"id": "S2", "parallel_group": 2, "depends_on": ["S1"]}},  // }
                      {{"id": "S3", "parallel_group": 2, "depends_on": ["S1"]}},  // } Parallel!
                      {{"id": "S4", "parallel_group": 2, "depends_on": ["S1"]}},  // }
                      {{"id": "S5", "parallel_group": 3, "depends_on": ["S2", "S3", "S4"]}}  // Merge
                    ]
                  }}
                - OPTIMIERE für Parallelität: Zerlege Aufgaben so, dass viele parallel laufen können!
                - Nutze depends_on NUR für echte Abhängigkeiten

                BESTE PRAKTIKEN für Task-Dekomposition:
                - Zerlege in UNABHÄNGIGE Subtasks (für Parallelisierung)
                - Jeder Subtask sollte in 1-2 Minuten erledigt sein
                - Bei Listen/Mehrfach-Items: Erstelle parallele Subtasks (z.B. "Test Feature A", "Test Feature B")
                - Vermeide monolithische Subtasks ("Implementiere alles")
                - Nutze frühe parallel_groups für schnelles Feedback

                MERGE-STRATEGIE:
                - Beschreibe WIE die Ergebnisse kombiniert werden (nicht nur "kombiniere")
                - Beispiele: "Aggregiere Test-Ergebnisse zu Gesamt-Report", "Vereinige Code-Module zu Gesamtlösung"
                - Merge sollte auf ALLEN Subtask-Ergebnissen basieren

                Regeln:
                - Gib ausschließlich reines JSON zurück, ohne Markdown, Backticks oder Text vor/nach dem JSON.
                - Jeder String muss eine Zeile bleiben und <= 160 Zeichen haben.
                - Verwende als "agent_key" nur die geladenen Agenten.
                - Verwende als "engine" primär: "minimax" (für LLM-Tasks), "smolagent" (für Tool-Tasks)
                - Legacy-Optionen: "anythingllm", "qnn", "cpu" (nur falls nötig)
                - Erstelle so viele Subtasks wie sinnvoll (typisch 2-8, bei komplexen Aufgaben auch mehr)
                - Bei Aufgaben mit vielen unabhängigen Teilen: Nutze Parallelisierung statt Sequenz!
                - Liefere die finale JSON ausschließlich in der Antwort-Ausgabe (nicht im Thinking-Bereich).
                - Analysiere die Anforderung präzise. Wenn explizite Detailanweisungen (z. B. "letter for letter", "Schritt für Schritt", "einzeln") vorkommen, bilde Subtasks, die diese Vorgaben exakt widerspiegeln.
                - Jeder Subtask muss einen eigenen Mehrwert liefern; vermeide redundante oder identische Ziele.
                - Beende die Ausgabe direkt nach dem JSON mit der Zeichenkette END_OF_PLAN.
                - Wenn die Anforderung mehrdeutig ist, erstelle zuerst einen Klärungs-Subtask (z. B. "Anforderung klären") mit einem passenden Agenten und notiere offene Fragen oder Annahmen.
                - Stelle sicher, dass Subtasks, die auf den Ergebnissen vorangehender Schritte basieren, die entsprechenden IDs in "depends_on" aufführen.
                - Wenn ein Subtask externe Informationen beschaffen, recherchieren, Dateien lesen oder Berechnungen mit Tools durchführen soll, setze "engine" auf "smolagent".
                - Für Subtasks mit "engine": "smolagent" füge das Feld "tools": ["tool_name"] hinzu und nutze ausschließlich folgende Tool-Namen (keine anderen erfinden):
{tool_name_list}
                - Verwende "engine": "minimax" für reine Text- oder Planungsaufgaben ohne Toolzugriff.

                SelfAI Agenten:
                {agent_overview}

                Memory-Zusammenfassung:
                {memory_summary}

            Verfügbare Tools:
            {tools_overview}

                Ziel:
                {goal}

            BEISPIEL-PLAN (parallele Web-Crawler Entwicklung):
            {{
              "subtasks": [
                {{
                  "id": "S1",
                  "title": "Requirements analysieren",
                  "objective": "Liste alle technischen Anforderungen für den Crawler",
                  "agent_key": "code_helfer",
                  "engine": "minimax",
                  "parallel_group": 1,
                  "depends_on": [],
                  "notes": "Definiere: Ziel-Websites, Datenformat, Rate-Limits"
                }},
                {{
                  "id": "S2",
                  "title": "HTTP Client entwickeln",
                  "objective": "Implementiere robuste HTTP-Anfragen mit Error-Handling",
                  "agent_key": "code_helfer",
                  "engine": "minimax",
                  "parallel_group": 2,
                  "depends_on": ["S1"]
                }},
                {{
                  "id": "S3",
                  "title": "HTML Parser entwickeln",
                  "objective": "Implementiere BeautifulSoup Parser für News-Extraktion",
                  "agent_key": "code_helfer",
                  "engine": "minimax",
                  "parallel_group": 2,
                  "depends_on": ["S1"]
                }},
                {{
                  "id": "S4",
                  "title": "Storage Layer entwickeln",
                  "objective": "Implementiere JSON/CSV Export-Funktionalität",
                  "agent_key": "code_helfer",
                  "engine": "minimax",
                  "parallel_group": 2,
                  "depends_on": ["S1"]
                }},
                {{
                  "id": "S5",
                  "title": "Integration & Tests",
                  "objective": "Kombiniere Module und teste End-to-End",
                  "agent_key": "code_helfer",
                  "engine": "minimax",
                  "parallel_group": 3,
                  "depends_on": ["S2", "S3", "S4"],
                  "notes": "Teste mit realen Websites"
                }}
              ],
              "merge": {{
                "strategy": "Kombiniere HTTP Client, Parser und Storage zu vollständigem Crawler mit Tests",
                "steps": [
                  {{
                    "title": "Code-Integration",
                    "description": "Vereinige S2, S3, S4 Module in main.py",
                    "depends_on": ["S5"]
                  }},
                  {{
                    "title": "Dokumentation",
                    "description": "Erstelle README mit Usage-Beispielen und API-Docs",
                    "depends_on": ["S5"]
                  }}
                ]
              }}
            }}

            Beachte: S2, S3, S4 laufen PARALLEL (parallel_group: 2) → 3x schneller als sequentiell!
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
        """Erzeugt einen Plan über den Ollama-Endpunkt."""

        payload = {
            "model": self.model,
            "prompt": self._build_prompt(goal, context),
            "stream": bool(progress_callback),
            "format": "json",
            "options": {
                "temperature": 0.1,
                "num_predict": self.max_tokens,
            },
        }

        raw_response = ""

        try:
            with httpx.Client(timeout=self.timeout) as client:
                if progress_callback:
                    aggregated = ""
                    buffer = ""
                    with client.stream(
                        "POST",
                        self.generate_url,
                        json=payload,
                        headers=self.headers or None,
                    ) as response:
                        response.raise_for_status()
                        for chunk in response.iter_text():
                            if not chunk:
                                continue
                            buffer += chunk
                            while "\n" in buffer:
                                line, buffer = buffer.split("\n", 1)
                                line = line.strip()
                                if not line:
                                    continue
                                if line.startswith("data:"):
                                    line = line[len("data:") :].strip()
                                if not line or line in ("[DONE]", "DONE"):
                                    continue
                                try:
                                    parsed = json.loads(line)
                                except json.JSONDecodeError:
                                    continue

                                if "response" in parsed and parsed["response"]:
                                    part = parsed["response"]
                                    aggregated += part
                                    progress_callback(part)

                                if parsed.get("done"):
                                    if parsed.get("response"):
                                        aggregated += parsed["response"]
                                    raw_response = aggregated or parsed.get("response", "")
                                    return self._parse_plan(raw_response, body_extra=parsed, context=context)
                        raw_response = aggregated
                else:
                    response = client.post(
                        self.generate_url,
                        json=payload,
                        headers=self.headers or None,
                    )
                    response.raise_for_status()
                    body = response.json()
                    raw_response = body.get("response") or body.get("thinking")
                    if not raw_response:
                        raise PlannerError(f"Ollama-Response enthält kein 'response'-Feld: {body}")
                    return self._parse_plan(raw_response, body_extra=body, context=context)
        except httpx.TimeoutException as exc:
            raise PlannerError(
                f"Ollama antwortete nicht innerhalb von {self.timeout} Sekunden."
            ) from exc
        except httpx.HTTPStatusError as exc:
            raise PlannerError(
                f"Ollama HTTP-Fehler {exc.response.status_code}: {exc.response.text}"
            ) from exc
        except httpx.RequestError as exc:
            raise PlannerError(f"Fehler beim Kontaktieren von Ollama: {exc}") from exc

        if not raw_response:
            raise PlannerError("Ollama lieferte keine Daten während des Streams.")

        return self._parse_plan(raw_response, context=context)

    def _parse_plan(
        self,
        raw_response: str,
        body_extra: Dict[str, Any] | None = None,
        context: PlannerContext | None = None,
    ) -> Dict[str, Any]:
        context = context or PlannerContext(agents=[], memory_summary="")

        cleaned = self._strip_code_fences(raw_response)
        if "END_OF_PLAN" in cleaned:
            cleaned = cleaned.split("END_OF_PLAN", 1)[0].strip()
        try:
            plan_data = json.loads(cleaned)
        except json.JSONDecodeError as exc:
            done_reason = None
            if body_extra:
                done_reason = body_extra.get("done_reason")
            hint = f" Done-Reason: {done_reason}" if done_reason else ""
            raise PlannerError(
                f"Planner-Ausgabe ist kein gültiges JSON.{hint} Rohantwort: {cleaned[:300]}"
            ) from exc

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
            setattr(exc, "plan_data", plan_data)
            raise PlannerError(f"Planvalidierung fehlgeschlagen: {exc}") from exc

        return plan_data
