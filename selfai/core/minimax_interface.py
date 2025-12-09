"""MiniMax Cloud API Interface"""
import requests
import logging

logger = logging.getLogger(__name__)

class MinimaxInterface:
    def __init__(self, api_key: str, api_base: str = "https://api.minimax.io/v1",
                 model: str = "openai/MiniMax-M2"):
        self.api_key = api_key
        self.api_base = api_base.rstrip('/')
        self.model = model
        logger.info(f"✅ MiniMax Interface initialisiert: {model}")

    def generate_response(self, system_prompt: str, user_prompt: str,
                         max_tokens: int = 512, temperature: float = 0.7,
                         history=None, **kwargs) -> str:
        """Generiert Antwort via MiniMax API"""
        url = f"{self.api_base}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        # Model String: "MiniMax-M2" (OHNE "openai/" prefix für API Body!)
        model_name = self.model.replace("openai/", "")

        # Messages mit History
        messages = [{"role": "system", "content": system_prompt}]
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": user_prompt})

        data = {
            "model": model_name,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature
        }

        try:
            response = requests.post(url, headers=headers, json=data, timeout=60)
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"❌ MiniMax Fehler: {e}")
            raise

    def stream_generate_response(self, system_prompt: str, user_prompt: str,
                                 max_tokens: int = 512, temperature: float = 0.7,
                                 history=None, **kwargs):
        """Streaming-Antwort"""
        # Vereinfachte Version ohne Streaming vorerst
        response = self.generate_response(system_prompt, user_prompt, max_tokens, temperature, history=history)
        yield response
