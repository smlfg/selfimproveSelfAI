import json
import logging
from typing import Iterator, Iterable, Optional, Dict, Any

import httpx


logger = logging.getLogger(__name__)


class MinimaxInterface:
    """HTTP-Client für die MiniMax Cloud API (OpenAI-kompatibel)."""

    def __init__(
        self,
        api_key: str,
        api_base: str = "https://api.minimax.io/v1",
        model: str = "openai/MiniMax-M2",
        *,
        stream: bool = True,
        timeout: float = 60.0,
    ) -> None:
        if not api_key:
            raise ValueError("API-Key für MiniMax fehlt.")
        if not api_base:
            raise ValueError("API-Basis-URL für MiniMax fehlt.")
        if not model:
            raise ValueError("Modell-Name für MiniMax fehlt.")

        self.api_key = api_key
        self.api_base = api_base.rstrip("/")
        self.model = model
        self.stream_enabled = stream
        self.timeout = timeout

        self.chat_url = f"{self.api_base}/chat/completions"
        self.headers = {
            "accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        # Mini-Healthcheck beim Initialisieren, damit Fehlkonfigurationen früh auffallen.
        self._check_auth()

    def _check_auth(self) -> None:
        """Validiert den API-Key gegen einen einfachen Chat-Endpoint."""
        try:
            test_payload = {
                "model": self.model,
                "messages": [
                    {"role": "user", "content": "ping"}
                ],
                "max_tokens": 1,
            }
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(
                    self.chat_url, headers=self.headers, json=test_payload
                )
                response.raise_for_status()
                logger.info("MiniMax API-Authentifizierung erfolgreich")
        except httpx.HTTPStatusError as exc:
            logger.error(f"MiniMax Auth fehlgeschlagen (Status {exc.response.status_code})")
            raise RuntimeError(
                f"MiniMax Auth fehlgeschlagen (Status {exc.response.status_code})"
            ) from exc
        except httpx.RequestError as exc:
            logger.error(f"Keine Verbindung zu MiniMax möglich: {exc}")
            raise RuntimeError(
                f"Keine Verbindung zu MiniMax möglich: {exc}"
            ) from exc

    def _build_messages(
        self,
        system_prompt: str,
        user_prompt: str,
        history: Iterable[Dict[str, str]] | None,
    ) -> list[Dict[str, str]]:
        """Formatiert System-Prompt, History und Nutzerprompt zu einer Nachrichtenliste."""
        messages: list[Dict[str, str]] = []

        if system_prompt:
            messages.append({
                "role": "system",
                "content": system_prompt.strip()
            })

        if history:
            for message in history:
                role = message.get("role", "")
                content = message.get("content", "")
                if not content:
                    continue
                messages.append({
                    "role": role,
                    "content": content
                })

        messages.append({
            "role": "user", 
            "content": user_prompt.strip()
        })
        return messages

    def generate_response(
        self,
        system_prompt: str,
        user_prompt: str,
        history: list[Dict[str, str]] | None = None,
        *,
        timeout: float | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> str:
        """
        Sendet eine Chat-Anfrage an MiniMax und gibt die Textantwort zurück.
        Streaming wird intern deaktiviert, da SelfAI synchron arbeitet.
        """
        messages = self._build_messages(system_prompt, user_prompt, history)
        
        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
        }
        
        if max_tokens:
            payload["max_tokens"] = max_tokens
        if temperature:
            payload["temperature"] = temperature

        client_timeout = timeout or self.timeout
        try:
            with httpx.Client(timeout=client_timeout) as client:
                response = client.post(
                    self.chat_url, headers=self.headers, json=payload
                )
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            error_payload = exc.response.text
            logger.error(f"MiniMax HTTP-Fehler {exc.response.status_code}: {error_payload}")
            raise RuntimeError(
                f"MiniMax antwortete mit HTTP {exc.response.status_code}: {error_payload}"
            ) from exc
        except httpx.RequestError as exc:
            logger.error(f"Fehler beim Kontaktieren von MiniMax: {exc}")
            raise RuntimeError(
                f"Fehler beim Kontaktieren von MiniMax: {exc}"
            ) from exc

        try:
            data = response.json()
        except ValueError as exc:
            logger.error(f"Ungültiges JSON von MiniMax: {response.text}")
            raise RuntimeError(
                f"Antwort von MiniMax ist kein gültiges JSON: {response.text}"
            ) from exc

        choices = data.get("choices", [])
        if not choices:
            logger.error(f"MiniMax lieferte keine Choices zurück: {data}")
            raise RuntimeError(
                f"MiniMax lieferte keine Choices zurück: {data}"
            )

        message = choices[0].get("message", {})
        content = message.get("content", "")
        if not content:
            logger.error(f"MiniMax lieferte keinen Content zurück: {message}")
            raise RuntimeError(
                f"MiniMax lieferte keinen Content zurück: {message}"
            )
        
        logger.info(f"MiniMax Antwort empfangen ({len(content)} Zeichen)")
        return content

    def stream_generate_response(
        self,
        system_prompt: str,
        user_prompt: str,
        history: list[Dict[str, str]] | None = None,
        *,
        timeout: float | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> Iterator[str]:
        """
        Streamt eine Chat-Antwort. Gibt Text-Segmente (Chunks) zurück.
        """
        if not self.stream_enabled:
            raise RuntimeError("Streaming ist für MiniMax deaktiviert.")

        messages = self._build_messages(system_prompt, user_prompt, history)
        
        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "stream": True,
        }
        
        if max_tokens:
            payload["max_tokens"] = max_tokens
        if temperature:
            payload["temperature"] = temperature

        buffer = ""
        client_timeout = timeout or self.timeout
        try:
            with httpx.Client(timeout=client_timeout) as client:
                with client.stream(
                    "POST",
                    self.chat_url,
                    headers=self.headers,
                    json=payload,
                ) as response:
                    response.raise_for_status()

                    for chunk in response.iter_text():
                        if not chunk:
                            continue
                        buffer += chunk
                        while "\n\n" in buffer:
                            line, buffer = buffer.split("\n\n", 1)
                            line = line.strip()
                            if not line:
                                continue
                            
                            if line.startswith("data:"):
                                line = line[len("data:"):].strip()
                            
                            if not line or line == "[DONE]":
                                return
                            
                            try:
                                parsed_chunk = json.loads(line)
                            except json.JSONDecodeError:
                                logger.warning(f"Fehler beim Parsen des Stream-Chunks: {line}")
                                continue

                            if parsed_chunk.get("error"):
                                error_msg = parsed_chunk["error"].get("message", "Unbekannter Fehler")
                                logger.error(f"MiniMax Stream-Fehler: {error_msg}")
                                raise RuntimeError(f"MiniMax Stream-Fehler: {error_msg}")

                            choices = parsed_chunk.get("choices", [])
                            if choices:
                                delta = choices[0].get("delta", {})
                                content_delta = delta.get("content")
                                if content_delta:
                                    yield content_delta

        except httpx.HTTPStatusError as exc:
            error_payload = exc.response.text
            logger.error(f"MiniMax Streaming HTTP-Fehler {exc.response.status_code}: {error_payload}")
            raise RuntimeError(
                f"MiniMax Streaming-Request schlug fehl "
                f"(HTTP {exc.response.status_code}): {error_payload}"
            ) from exc
        except httpx.RequestError as exc:
            logger.error(f"Fehler beim Streaming von MiniMax: {exc}")
            raise RuntimeError(
                f"Fehler beim Streaming von MiniMax: {exc}"
            ) from exc

        # Falls nach dem Stream noch Daten übrig sind, versuche sie zu parsen.
        if buffer:
            try:
                parsed_response = json.loads(buffer)
                if parsed_response.get("error"):
                    error_msg = parsed_response["error"].get("message", "Unbekannter Fehler")
                    logger.error(f"MiniMax Stream-Fehler (Ende): {error_msg}")
                    raise RuntimeError(f"MiniMax Stream-Fehler: {error_msg}")
                
                choices = parsed_response.get("choices", [])
                if choices:
                    final_message = choices[0].get("message", {})
                    full_content = final_message.get("content")
                    if full_content:
                        yield full_content
            except json.JSONDecodeError:
                logger.warning(f"Fehler beim Parsen der verbleibenden Stream-Daten: {buffer}")
                # Unvollständige Reste ignorieren.
                pass
