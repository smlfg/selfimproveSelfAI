"""MiniMax-Chat-Interface für Merge-Ausgaben."""

from __future__ import annotations

import json
from typing import Dict, Iterator, Optional

import httpx

from selfai.core.think_parser import parse_think_tags, parse_think_tags_streaming


class MergeMinimaxInterface:
    def __init__(
        self,
        base_url: str,
        model: str,
        timeout: float,
        max_tokens: int,
        headers: Optional[Dict[str, str]] = None,
        ui=None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self.max_tokens = max_tokens
        self.headers = headers or {}
        self.generate_url = f"{self.base_url}/chat/completions"
        self.ui = ui  # Optional UI for displaying think tags

    def _stream_request(self, payload: Dict[str, object]) -> Iterator[str]:
        with httpx.Client(timeout=self.timeout) as client:
            with client.stream(
                "POST",
                self.generate_url,
                json=payload,
                headers=self.headers or None,
            ) as response:
                response.raise_for_status()
                buffer = ""
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
                        if parsed.get("error"):
                            raise RuntimeError(parsed["error"])
                        if parsed.get("choices"):
                            choices = parsed.get("choices", [])
                            for choice in choices:
                                if choice.get("delta") and choice["delta"].get("content"):
                                    yield choice["delta"]["content"]

    def stream_chat(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        timeout: float | None = None,
        max_tokens: int | None = None,
    ) -> Iterator[str]:
        # Model String: "MiniMax-M2" (OHNE "openai/" prefix für API Body!)
        model_name = self.model.replace("openai/", "")
        
        messages = [
            {"role": "system", "content": system_prompt.strip()},
            {"role": "user", "content": user_prompt.strip()}
        ]
        
        payload = {
            "model": model_name,
            "messages": messages,
            "stream": True,
            "temperature": 0.2,
            "max_tokens": int(max_tokens or self.max_tokens),
        }
        return self._stream_request(payload)

    def chat(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        timeout: float | None = None,
        max_tokens: int | None = None,
    ) -> str:
        # Model String: "MiniMax-M2" (OHNE "openai/" prefix für API Body!)
        model_name = self.model.replace("openai/", "")
        
        messages = [
            {"role": "system", "content": system_prompt.strip()},
            {"role": "user", "content": user_prompt.strip()}
        ]
        
        payload = {
            "model": model_name,
            "messages": messages,
            "stream": False,
            "temperature": 0.2,
            "max_tokens": int(max_tokens or self.max_tokens),
        }
        with httpx.Client(timeout=timeout or self.timeout) as client:
            response = client.post(
                self.generate_url,
                json=payload,
                headers=self.headers or None,
            )
            response.raise_for_status()
            data = response.json()
            choices = data.get("choices", [])
            if not choices or not choices[0].get("message", {}).get("content"):
                raise RuntimeError("MiniMax lieferte keine Antwort.")

            raw_content = choices[0]["message"]["content"]

            # Parse and display think tags separately
            clean_content, think_contents = parse_think_tags(raw_content)
            if self.ui and think_contents:
                self.ui.show_think_tags(think_contents)

            return clean_content
