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

    def run(self) -> None:
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

        # Execute groups sequentially
        try:
            for group_num in sorted(groups.keys()):
                tasks_in_group = groups[group_num]

                # Check depends_on before starting group
                for task in tasks_in_group:
                    deps = task.get("depends_on", [])
                    for dep_id in deps:
                        if self._get_task_status(dep_id) != "completed":
                            raise ExecutionError(f"Dependency {dep_id} not completed")

                # Execute group in parallel
                if len(tasks_in_group) == 1:
                    # Single task - no threading overhead
                    task = tasks_in_group[0]
                    task_id = task.get("id") or "?"
                    self.ui.status(f"Task {task_id}: {task.get('title', '')}", "info")
                    self._update_task_status(task_id, "running", None)
                    self._run_subtask(task)
                    self._update_task_status(task_id, "completed", None)
                else:
                    # Multiple tasks - parallel execution
                    self.ui.status(f"⚡ Parallel Group {group_num}: {len(tasks_in_group)} Tasks gleichzeitig...", "info")

                    with ThreadPoolExecutor(max_workers=len(tasks_in_group)) as executor:
                        futures = {}
                        for task in tasks_in_group:
                            task_id = task.get("id") or "?"
                            self._update_task_status(task_id, "running", None)
                            future = executor.submit(self._run_subtask, task)
                            futures[future] = task_id

                        # Wait for completion
                        for future in as_completed(futures):
                            task_id = futures[future]
                            try:
                                future.result()
                                self._update_task_status(task_id, "completed", None)
                                self.ui.status(f"✓ Task {task_id} abgeschlossen", "success")
                            except Exception as exc:
                                self._update_task_status(task_id, "failed", str(exc))
                                self.ui.status(f"✗ Task {task_id} fehlgeschlagen: {exc}", "error")
                                # Cancel remaining tasks
                                executor.shutdown(wait=False, cancel_futures=True)
                                raise ExecutionError(f"Parallel task {task_id} failed: {exc}")
        finally:
            self._save_plan()

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

        # Show first 500 chars
        display_text = response.strip()[:500]
        if len(response) > 500:
            display_text += "\n... [weitere Ausgabe in Memory gespeichert]"

        print(display_text)
        self.ui.status(separator + "\n", "info")

    def _run_subtask(self, task: Dict[str, Any]) -> None:
        task_id = task.get("id", "?")
        agent_key = task.get("agent_key")
        engine = task.get("engine")
        objective = task.get("objective", "")

        agent = self.agent_manager.get(agent_key)
        if agent is None:
            raise ExecutionError(f"Agent '{agent_key}' nicht gefunden.")

        context_hint = f"{objective}\n{task.get('notes', '')}".strip()
        history = self.memory_system.load_relevant_context(
            agent,
            context_hint,
            limit=2,
        )
        prompt = f"Subtask {task_id}: {objective}\nNOTES: {task.get('notes', '')}"

        self.ui.status(f"Subtask {task_id} starten ({task.get('title', objective)})", "info")

        # LLM-basierte Engines (nutzen alle _invoke_llm mit verfügbaren Backends)
        if engine in ("minimax", "anythingllm", "qnn", "cpu"):
            response = self._invoke_llm(agent, prompt, history, task_id)
        elif engine == "smolagent":
            response = self._run_smolagent(task, agent, prompt, history, task_id)
        else:
            raise ExecutionError(f"Engine '{engine}' wird noch nicht unterstützt.")

        # Show intermediate result in console
        self._display_subtask_result(task_id, task.get('title', ''), response)

        result_path = self.memory_system.save_conversation(agent, prompt, response)
        if result_path:
            task["result_path"] = str(result_path)
        self.ui.status(f"Subtask {task_id} abgeschlossen.", "success")

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
                    try:
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
                                self.ui.streaming_chunk(chunk)
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
