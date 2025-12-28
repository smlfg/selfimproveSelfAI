"""Dispatcher, der geplante Subtasks nacheinander ausführt."""

from __future__ import annotations

import json
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, Iterable, Optional


class ExecutionError(RuntimeError):
    """Signalisiert Fehler während der Subtask-Ausführung."""


class ExecutionDispatcher:
    """Führt Subtasks aus einem Planner-Plan sequentiell aus."""

    def __init__(
        self,
        *,
        plan_path: Path,
        agent_manager,
        memory_system,
        llm_backends: list[dict[str, object]],
        ui,
        backend_label: Optional[str] = None,
        llm_timeout: float | None = None,
        retry_attempts: int = 2,
        retry_delay: float = 5.0,
        max_output_tokens: int | None = None,
    ) -> None:
        if not llm_backends:
            raise ValueError("Keine LLM-Backends verfügbar.")

        self.plan_path = plan_path
        self.agent_manager = agent_manager
        self.memory_system = memory_system
        self.llm_backends = llm_backends
        self.ui = ui
        self.llm_timeout = llm_timeout

        self.retry_attempts = max(0, retry_attempts)
        self.retry_delay = max(0.0, retry_delay)
        self.max_output_tokens = max_output_tokens

        self.plan_data = self._load_plan(plan_path)
        self.subtasks = self.plan_data.get("subtasks", [])
        self.merge = self.plan_data.get("merge", {})

        self.default_backend_label = backend_label or "Plan"
        self.current_backend_name = ""
        self._set_backend(0, announce=False)

    def _set_backend(self, index: int, announce: bool = True) -> None:
        backend = self.llm_backends[index]
        self.active_backend_index = index
        self.llm_interface = backend.get("interface")
        label = backend.get("label") or backend.get("name") or self.default_backend_label
        self.backend_label = label
        self.current_backend_name = backend.get("name") or label
        if announce:
            self.ui.status(
                f"Wechsle auf LLM-Backend '{self.backend_label}'.",
                "warning",
            )

    def _load_plan(self, plan_path: Path) -> Dict[str, Any]:
        try:
            content = plan_path.read_text(encoding="utf-8")
            return json.loads(content)
        except OSError as exc:
            raise ExecutionError(f"Plan-Datei konnte nicht gelesen werden: {exc}")
        except json.JSONDecodeError as exc:
            raise ExecutionError(f"Plan-Datei enthält ungültiges JSON: {exc}")

    def run(self, keep_ui_open: bool = False) -> None:
        """Führt Subtasks parallel nach parallel_group aus."""

        self.ui.status(
            f"Ausführungsphase gestartet ({len(self.subtasks)} Subtasks).",
            "info",
        )
        self._ensure_status_fields()

        # Group tasks by parallel_group
        groups = defaultdict(list)
        for task in self.subtasks:
            pg = task.get("parallel_group", 1)
            groups[pg].append(task)

        # Initialize Persistent Parallel UI if available
        use_rich_parallel = hasattr(self.ui, 'start_parallel_view')
        if use_rich_parallel:
            subtasks_info = [
                {
                    "id": task.get("id", "?"),
                    "title": task.get("title", f"Task {task.get('id', '?')}"),
                    "agent_key": task.get("agent_key", "default")
                }
                for task in self.subtasks
            ]
            header_goal = self.plan_data.get("metadata", {}).get("goal", "SelfAI Mission")
            self.ui.start_parallel_view(plan_goal=header_goal, subtasks_info=subtasks_info)

        # Initialize Multi-Pane UI (only if Rich not active)
        multi_pane_ui = None
        has_parallel_tasks = any(len(tasks) > 1 for tasks in groups.values())
        if has_parallel_tasks and not use_rich_parallel:
            try:
                from selfai.ui.multi_pane_ui import MultiPaneUI
                multi_pane_ui = MultiPaneUI(pane_height=4)
                for task in self.subtasks:
                    task_id = task.get("id", "?")
                    multi_pane_ui.add_pane(task_id, task.get("title", f"Task {task_id}"))
                self.multi_pane_ui = multi_pane_ui
                self.ui.status("🖥️  Multi-Pane UI aktiviert", "info")
            except Exception:
                multi_pane_ui = None

        # Execute groups sequentially
        try:
            for group_num in sorted(groups.keys()):
                tasks_in_group = groups[group_num]

                # Check depends_on
                for task in tasks_in_group:
                    deps = task.get("depends_on", [])
                    for dep_id in deps:
                        if self._get_task_status(dep_id) != "completed":
                            raise ExecutionError(f"Dependency {dep_id} not completed")

                self.ui.status(f"Starte Gruppe {group_num} ({len(tasks_in_group)} Tasks)...", "info")

                if multi_pane_ui:
                    multi_pane_ui.start_rendering()

                # Add objectives to boxes immediately
                if use_rich_parallel:
                    for task in tasks_in_group:
                        task_id = task.get("id") or "?"
                        objective = task.get("objective", "")
                        if objective:
                            self.ui.add_response_chunk(task_id, f"[bold yellow]Ziel: {objective}[/]\n\n", skip_escape=True)

                with ThreadPoolExecutor(max_workers=len(tasks_in_group)) as executor:
                    futures = {}
                    for task in tasks_in_group:
                        task_id = task.get("id") or "?"
                        self._update_task_status(task_id, "running", None)
                        future = executor.submit(self._run_subtask, task)
                        futures[future] = task

                    results = {}
                    for future in as_completed(futures):
                        task = futures[future]
                        task_id = task.get("id") or "?"
                        try:
                            response = future.result()
                            results[task_id] = (task, response)
                            self._update_task_status(task_id, "completed", None)
                            if use_rich_parallel:
                                self.ui.mark_subtask_complete(task_id, success=True)
                        except Exception as exc:
                            self._update_task_status(task_id, "failed", str(exc))
                            if use_rich_parallel:
                                self.ui.mark_subtask_complete(task_id, success=False)
                            executor.shutdown(wait=False, cancel_futures=True)
                            raise ExecutionError(f"Task {task_id} failed: {exc}")

                # Sequential results summary - REMOVED during execution to avoid clutter
                # Results are still saved in the 'results' dict for merge phase
                # Only log simple completion markers in the footer
                for task in tasks_in_group:
                    task_id = task.get("id", "")
                    self.ui.status(f"✓ {task_id} fertig.", "success")

            if multi_pane_ui and multi_pane_ui.all_completed() and not keep_ui_open:
                time.sleep(0.5)
                multi_pane_ui.stop_rendering()

            if use_rich_parallel and not keep_ui_open:
                self.ui.status("Alle Gruppen erfolgreich abgeschlossen.", "success")
                time.sleep(0.5)
                self.ui.stop_parallel_view()

        finally:
            self._save_plan()

        if not keep_ui_open:
            self.ui.status("Ausführungsphase abgeschlossen.", "success")

    def _ensure_status_fields(self) -> None:
        for task in self.subtasks:
            task.setdefault("status", "pending")
            task.setdefault("result_path", None)
            task.setdefault("error", None)
        self._save_plan()

    def _update_task_status(self, task_id: str, status: str, error: str | None) -> None:
        for task in self.subtasks:
            if task.get("id") == task_id:
                task["status"] = status
                task["error"] = error
                break
        self._save_plan()

    def _get_task_status(self, task_id: str) -> str | None:
        """Get status of a task by ID."""
        for task in self.subtasks:
            if task.get("id") == task_id:
                return task.get("status")
        return None

    def _save_plan(self) -> None:
        try:
            self.plan_path.write_text(
                json.dumps(self.plan_data, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        except OSError as exc:
            raise ExecutionError(f"Plan konnte nicht aktualisiert werden: {exc}")

    def _display_subtask_result(self, task_id: str, title: str, response: str) -> None:
        """Zeigt Subtask-Ergebnis in der Konsole an."""
        separator = "─" * 60
        self.ui.status(f"\n{separator}", "info")
        self.ui.status(f"📊 Subtask {task_id}: {title}", "info")
        self.ui.status(separator, "info")

        # Show first 2000 chars (increased from 500)
        display_text = response.strip()[:2000]
        if len(response) > 2000:
            display_text += "\n... [weitere Ausgabe in Memory gespeichert]"

        print(display_text)
        self.ui.status(separator + "\n", "info")

    def _run_subtask(self, task: Dict[str, Any]) -> str:
        task_id = task.get("id", "?")
        agent_key = task.get("agent_key")
        engine = task.get("engine")
        objective = task.get("objective", "")

        agent = self.agent_manager.get(agent_key)
        if agent is None:
            # Fallback: Try 'default' or active agent instead of crashing
            fallback_key = "default"
            agent = self.agent_manager.get(fallback_key)
            if agent is None and self.agent_manager.agents:
                 # Last resort: first available agent
                 agent = list(self.agent_manager.agents.values())[0]
            
            if agent:
                self.ui.status(f"⚠️ Agent '{agent_key}' nicht gefunden. Nutze Fallback: '{agent.key}'", "warning")
            else:
                raise ExecutionError(f"Agent '{agent_key}' nicht gefunden und kein Fallback verfügbar.")

        context_hint = f"{objective}\n{task.get('notes', '')}".strip()
        history = self.memory_system.load_relevant_context(
            agent,
            context_hint,
            limit=2,
        )
        prompt = f"Subtask {task_id}: {objective}\nNOTES: {task.get('notes', '')}"

        self.ui.status(f"Subtask {task_id} starten ({task.get('title', objective)})", "info")

        try:
            # LLM-basierte Engines (nutzen alle _invoke_llm mit verfügbaren Backends)
            if engine in ("minimax", "anythingllm", "qnn", "cpu"):
                response = self._invoke_llm(agent, prompt, history, task_id)
            elif engine == "smolagent":
                response = self._run_smolagent(task, agent, prompt, history, task_id)
            else:
                raise ExecutionError(f"Engine '{engine}' wird noch nicht unterstützt.")

            result_path = self.memory_system.save_conversation(agent, prompt, response)
            if result_path:
                task["result_path"] = str(result_path)

            # Mark pane as completed in Multi-Pane UI
            if hasattr(self, 'multi_pane_ui') and self.multi_pane_ui is not None:
                self.multi_pane_ui.complete_pane(task_id)

            self.ui.status(f"Subtask {task_id} abgeschlossen.", "success")

            return response
        except Exception as exc:
            # Mark pane as failed in Multi-Pane UI
            if hasattr(self, 'multi_pane_ui') and self.multi_pane_ui is not None:
                self.multi_pane_ui.fail_pane(task_id)
            raise

    def _run_smolagent(
        self,
        task: dict[str, Any],
        agent,
        prompt_text: str,
        history: Iterable[dict[str, str]] | None,
        task_id: str,
    ) -> str:
        try:
            from selfai.core.smolagents_runner import SmolAgentError, SmolAgentRunner
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise ExecutionError(
                "Smolagents ist nicht installiert. Bitte `pip install smolagents` ausführen, um Tool-Subtasks zu nutzen."
            ) from exc

        tool_names = []
        raw_tools = task.get("tools")
        if isinstance(raw_tools, list):
            tool_names = [str(name) for name in raw_tools if isinstance(name, str) and name.strip()]

        max_steps = None
        if isinstance(task.get("max_steps"), int):
            max_steps = max(1, int(task["max_steps"]))

        runner = SmolAgentRunner(
            self.llm_backends,
            default_tools=tool_names or None,
            max_steps=max_steps or 12,
            ui=self.ui,
        )

        try:
            run_result = runner.run(
                task=prompt_text,
                system_prompt=agent.system_prompt,
                history=history,
                tool_names=tool_names or None,
                max_steps=max_steps,
                return_full_result=True,
                task_id=task_id, # Pass task_id here
            )
        except SmolAgentError as exc:
            raise ExecutionError(f"SmolAgent Fehler: {exc}") from exc

        if hasattr(run_result, "dict"):
            result_dict = run_result.dict()
            final_output = result_dict.get("output")
            details = json.dumps(result_dict, indent=2, ensure_ascii=False)
        else:
            final_output = run_result
            details = ""

        output_parts = []
        if isinstance(final_output, str):
            output_parts.append(final_output)
        elif final_output is not None:
            output_parts.append(str(final_output))

        if details:
            output_parts.append(f"[SmolAgent Run Details]\n{details}")

        combined = "\n\n".join(part for part in output_parts if part).strip()
        return combined or "Smolagent lieferte keine Ausgabe."

    def _invoke_llm(
        self,
        agent,
        prompt: str,
        history: Iterable[dict],
        task_id: str,
    ) -> str:
        last_error: Optional[ExecutionError] = None
        preferred_order = [self.active_backend_index] + [
            idx for idx in range(len(self.llm_backends)) if idx != self.active_backend_index
        ]
        for index in preferred_order:
            if index != self.active_backend_index:
                self._set_backend(index)
            try:
                return self._call_llm_backend(agent, prompt, history, task_id)
            except ExecutionError as exc:
                last_error = exc
                continue
        raise last_error if last_error else ExecutionError("Keine LLM-Backends verfügbar.")

    def _call_llm_backend(
        self,
        agent,
        prompt: str,
        history: Iterable[dict],
        task_id: str,
    ) -> str:
        use_streaming = hasattr(self.llm_interface, "stream_generate_response")
        last_exception: Optional[Exception] = None

        for attempt in range(self.retry_attempts + 1):
            try:
                if use_streaming:
                    chunks: list[str] = []
                    label = f"{self.backend_label}-S{task_id}"
                    use_parallel_ui = hasattr(self.ui, 'add_thinking_chunk')
                    use_multi_pane = hasattr(self, 'multi_pane_ui') and self.multi_pane_ui is not None

                    # Think tag parsing state
                    in_think_tag = False
                    think_buffer = ""

                    try:
                        if not use_parallel_ui and not use_multi_pane:
                            self.ui.stream_prefix(label)

                        for chunk in self.llm_interface.stream_generate_response(
                            system_prompt=agent.system_prompt,
                            user_prompt=prompt,
                            history=history,
                            timeout=self.llm_timeout,
                            max_output_tokens=self.max_output_tokens,
                        ):
                            if chunk:
                                chunks.append(chunk)

                                # Route to Multi-Pane UI
                                if use_multi_pane:
                                    # Parse think tags and route to multi-pane
                                    for char in chunk:
                                        think_buffer += char

                                        # Check for opening tag
                                        if not in_think_tag and think_buffer.endswith('<think>'):
                                            in_think_tag = True
                                            think_buffer = ""
                                            continue

                                        # Check for closing tag
                                        if in_think_tag and think_buffer.endswith('</think>'):
                                            in_think_tag = False
                                            think_buffer = ""
                                            continue

                                        # Send to multi-pane (non-thinking content)
                                        if not in_think_tag:
                                            if not think_buffer.startswith('<'):
                                                # Accumulate line buffer and send complete lines
                                                if char == '\n' or len(think_buffer) > 60:
                                                    self.multi_pane_ui.update_pane(task_id, think_buffer.strip())
                                                    think_buffer = ""
                                            elif len(think_buffer) > 10:
                                                # Not a think tag, send accumulated
                                                if '\n' in think_buffer:
                                                    lines = think_buffer.split('\n')
                                                    for line in lines[:-1]:
                                                        if line.strip():
                                                            self.multi_pane_ui.update_pane(task_id, line.strip())
                                                    think_buffer = lines[-1]

                                # Route to Parallel UI (old system)
                                elif use_parallel_ui:
                                    # Parse think tags on the fly
                                    for char in chunk:
                                        think_buffer += char

                                        # Check for opening tag
                                        if not in_think_tag and think_buffer.endswith('<think>'):
                                            in_think_tag = True
                                            think_buffer = ""
                                            continue

                                        # Check for closing tag
                                        if in_think_tag and think_buffer.endswith('</think>'):
                                            in_think_tag = False
                                            # Remove </think> from buffer
                                            thinking_content = think_buffer[:-8]
                                            if thinking_content:
                                                self.ui.add_thinking_chunk(task_id, thinking_content)
                                            think_buffer = ""
                                            continue

                                        # Send to appropriate stream
                                        if in_think_tag:
                                            # Accumulate in buffer for thinking
                                            pass
                                        else:
                                            # Send to response stream (but not if it's part of <think>)
                                            if not think_buffer.startswith('<'):
                                                self.ui.add_response_chunk(task_id, char)
                                                think_buffer = ""
                                            elif len(think_buffer) > 10:
                                                # Not a think tag, send accumulated
                                                self.ui.add_response_chunk(task_id, think_buffer)
                                                think_buffer = ""
                                else:
                                    # Standard streaming output
                                    self.ui.streaming_chunk(chunk)

                        # Flush remaining buffer to multi-pane
                        if use_multi_pane and think_buffer.strip():
                            self.multi_pane_ui.update_pane(task_id, think_buffer.strip())

                        if not use_parallel_ui and not use_multi_pane:
                            print()
                        return "".join(chunks)
                    except Exception as stream_exc:
                        self.ui.status(
                            f"Subtask {task_id}: Streaming fehlgeschlagen ({stream_exc}). Fallback auf Block-Modus.",
                            "warning",
                        )
                        print()
                        use_streaming = False
                        last_exception = stream_exc

                response = self.llm_interface.generate_response(
                    agent.system_prompt,
                    prompt,
                    history=history,
                    timeout=self.llm_timeout,
                    max_output_tokens=self.max_output_tokens,
                )
                label = f"{self.backend_label}-S{task_id}"
                self.ui.stream_prefix(label)
                self.ui.typing_animation(response)
                return response
            except Exception as exc:
                last_exception = exc
                if attempt < self.retry_attempts:
                    self.ui.status(
                        f"Subtask {task_id}: Fehler beim LLM-Aufruf ({exc}). Versuche erneut in {self.retry_delay}s...",
                        "warning",
                    )
                    time.sleep(self.retry_delay)
                    continue
                raise ExecutionError(
                    f"Subtask {task_id}: LLM-Backend '{self.backend_label}' fehlgeschlagen ({exc})."
                ) from exc

        raise ExecutionError(
            f"Subtask {task_id}: LLM-Backend '{self.backend_label}' fehlgeschlagen ({last_exception})."
        )
