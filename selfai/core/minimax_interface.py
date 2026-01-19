"""MiniMax Cloud API Interface with Identity Enforcement"""
import requests
import logging
import random
from selfai.core.think_parser import parse_think_tags
from selfai.core.identity_enforcer import (
    IDENTITY_CORE,
    REFLECTION_REQUIREMENT,
    IdentityInjector,
    IdentityGuardrail,
    ReflectionValidator,
    IdentityMetrics,
)

logger = logging.getLogger(__name__)

# Configuration
ENABLE_IDENTITY_ENFORCEMENT = True  # Master switch
ENABLE_INJECTION = True              # Identity reminders
ENABLE_GUARDRAILS = True             # Output validation
ENABLE_REFLECTION = False            # XML reflection requirement (OPTIONAL - MiniMax ignoriert oft)
ENABLE_JUDGE = False                 # Gemini Judge (costly, opt-in - NUR für /plan!)
JUDGE_SAMPLE_RATE = 0.1              # 10% sampling

class MinimaxInterface:
    def __init__(self, api_key: str, api_base: str = "https://api.minimax.io/v1",
                 model: str = "MiniMax-M2", ui=None):
        self.api_key = api_key
        self.api_base = api_base.rstrip('/')
        self.model = model
        self.ui = ui  # Optional UI for displaying think tags

        # Identity Enforcement Components
        self.identity_injector = IdentityInjector()
        self.identity_guardrail = IdentityGuardrail()
        self.reflection_validator = ReflectionValidator()
        self.identity_metrics = IdentityMetrics()

        # Optional: Identity Judge (initialized on demand)
        self.identity_judge = None
        if ENABLE_JUDGE:
            try:
                from selfai.core.identity_judge import IdentityJudge
                self.identity_judge = IdentityJudge(ui=ui)
            except Exception as e:
                logger.warning(f"⚠️ Identity Judge nicht verfügbar: {e}")
                if ui:
                    ui.status("⚠️ Identity Judge nicht verfügbar (optional)", "warning")

        logger.info(f"✅ MiniMax Interface initialisiert: {model}")
        if ui and ENABLE_IDENTITY_ENFORCEMENT:
            ui.status("✅ Identity Enforcement aktiviert", "success")

    def generate_response(self, system_prompt: str, user_prompt: str,
                         max_tokens: int = 512, temperature: float = 0.7,
                         history=None, **kwargs) -> str:
        """Generiert Antwort via MiniMax API mit Identity Enforcement"""

        # === PHASE 0: System Prompt Hardening ===
        if ENABLE_IDENTITY_ENFORCEMENT:
            # Prepend IDENTITY_CORE to system prompt
            enhanced_system_prompt = IDENTITY_CORE + "\n\n"

            if ENABLE_REFLECTION:
                enhanced_system_prompt += REFLECTION_REQUIREMENT + "\n\n"

            enhanced_system_prompt += system_prompt
        else:
            enhanced_system_prompt = system_prompt

        # === PHASE 1: Identity Injection ===
        if ENABLE_IDENTITY_ENFORCEMENT and ENABLE_INJECTION:
            enhanced_user_prompt = self.identity_injector.inject(user_prompt)
        else:
            enhanced_user_prompt = user_prompt

        # Retry loop for identity enforcement
        max_retries = 2
        for attempt in range(max_retries + 1):
            # === API Call ===
            url = f"{self.api_base}/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            model_name = self.model.replace("openai/", "")

            # Messages mit History
            messages = [{"role": "system", "content": enhanced_system_prompt}]
            if history:
                messages.extend(history)
            messages.append({"role": "user", "content": enhanced_user_prompt})

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
                raw_content = result["choices"][0]["message"]["content"]

                # Parse and display think tags separately
                clean_content, think_contents = parse_think_tags(raw_content)

                # Display think tags in UI if available
                if self.ui and think_contents:
                    self.ui.show_think_tags(think_contents)

                # === PHASE 2: Reflection Validation ===
                if ENABLE_IDENTITY_ENFORCEMENT and ENABLE_REFLECTION:
                    is_valid_reflection, error_msg = self.reflection_validator.validate(raw_content)

                    if not is_valid_reflection:
                        if self.ui:
                            self.ui.status(
                                f"⚠️ Reflexion ungültig (Attempt {attempt+1}/{max_retries+1}): {error_msg}",
                                "warning"
                            )

                        if attempt < max_retries:
                            logger.warning(f"Reflexion ungültig, retry... ({error_msg})")
                            continue
                        else:
                            logger.error(f"Reflexion nach {max_retries} Retries ungültig")
                            # Accept response anyway, just log

                # === PHASE 3: Guardrail Check ===
                had_leak = False
                was_corrected = False

                if ENABLE_IDENTITY_ENFORCEMENT and ENABLE_GUARDRAILS:
                    is_valid, violations = self.identity_guardrail.check(clean_content)

                    if not is_valid:
                        had_leak = True

                        if self.ui:
                            self.ui.status(
                                f"⚠️ Identity Leak detected (Attempt {attempt+1}/{max_retries+1}): {', '.join(violations)}",
                                "warning"
                            )

                        # Try auto-correction
                        corrected_content = self.identity_guardrail.auto_correct(clean_content)

                        # Re-validate corrected content
                        is_valid_after, _ = self.identity_guardrail.check(corrected_content)

                        if is_valid_after:
                            if self.ui:
                                self.ui.status("✅ Auto-Correction erfolgreich", "success")
                            clean_content = corrected_content
                            was_corrected = True
                        elif attempt < max_retries:
                            # Auto-correction failed, retry generation
                            logger.warning(f"Auto-correction fehlgeschlagen, retry generation...")
                            continue
                        else:
                            # Max retries reached, use corrected version anyway
                            logger.warning(f"Max retries erreicht, nutze korrigierte Version")
                            clean_content = corrected_content
                            was_corrected = True

                # === PHASE 4: Judge Evaluation (Sampling) ===
                judge_score = None
                if (ENABLE_IDENTITY_ENFORCEMENT and ENABLE_JUDGE and
                    self.identity_judge and random.random() < JUDGE_SAMPLE_RATE):

                    try:
                        judge_result = self.identity_judge.evaluate(user_prompt, raw_content)
                        judge_score = judge_result.total_score

                        # Check if retry recommended
                        if judge_result.recommendation == "retry" and attempt < max_retries:
                            if self.ui:
                                self.ui.status(
                                    f"⚠️ Judge empfiehlt Retry (Score: {judge_score:.1f}/10)",
                                    "warning"
                                )
                            continue

                    except Exception as e:
                        logger.warning(f"Judge evaluation fehlgeschlagen: {e}")

                # === Log Metrics ===
                self.identity_metrics.log_response(
                    had_leak=had_leak,
                    was_corrected=was_corrected,
                    retry_count=attempt,
                    judge_score=judge_score
                )

                # Success! Return clean content
                return clean_content

            except Exception as e:
                logger.error(f"❌ MiniMax Fehler: {e}")
                raise

        # Should not reach here, but just in case
        logger.error("Identity enforcement failed nach allen Retries")
        return clean_content  # Return last attempt

    def _call_api_direct(self, system_prompt: str, user_prompt: str,
                        max_tokens: int = 512, temperature: float = 0.7) -> str:
        """
        Direct API call bypassing identity enforcement and tool-calling.
        Use for structured output tasks like JSON generation.
        """
        url = f"{self.api_base}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        model_name = self.model.replace("openai/", "")

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

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
            content = result["choices"][0]["message"]["content"]

            # Remove think tags if present
            clean_content, _ = parse_think_tags(content)
            return clean_content

        except Exception as e:
            logger.error(f"❌ Direct MiniMax API Error: {e}")
            raise

    def stream_generate_response(self, system_prompt: str, user_prompt: str,
                                 max_tokens: int = 512, temperature: float = 0.7,
                                 history=None, **kwargs):
        """Echtes Streaming via MiniMax API."""
        
        # === PHASE 0: System Prompt Hardening ===
        if ENABLE_IDENTITY_ENFORCEMENT:
            enhanced_system_prompt = IDENTITY_CORE + "\n\n"
            if ENABLE_REFLECTION:
                enhanced_system_prompt += REFLECTION_REQUIREMENT + "\n\n"
            enhanced_system_prompt += system_prompt
        else:
            enhanced_system_prompt = system_prompt

        # === PHASE 1: Identity Injection ===
        if ENABLE_IDENTITY_ENFORCEMENT and ENABLE_INJECTION:
            enhanced_user_prompt = self.identity_injector.inject(user_prompt)
        else:
            enhanced_user_prompt = user_prompt

        url = f"{self.api_base}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        model_name = self.model.replace("openai/", "")

        messages = [{"role": "system", "content": enhanced_system_prompt}]
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": enhanced_user_prompt})

        data = {
            "model": model_name,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": True  # Enable API Streaming
        }

        try:
            with requests.post(url, headers=headers, json=data, stream=True, timeout=60) as response:
                response.raise_for_status()
                
                for line in response.iter_lines():
                    if not line:
                        continue
                    
                    decoded_line = line.decode('utf-8').strip()
                    if decoded_line.startswith("data: "):
                        data_str = decoded_line[6:] # Remove "data: " prefix
                        
                        if data_str == "[DONE]":
                            break
                            
                        try:
                            import json
                            chunk_json = json.loads(data_str)
                            delta = chunk_json["choices"][0]["delta"]
                            content = delta.get("content", "")
                            
                            # MiniMax specifics: sometimes content is in other fields or empty
                            if content:
                                yield content
                                
                        except Exception:
                            # Skip malformed chunks
                            continue
                            
        except Exception as e:
            logger.error(f"❌ MiniMax Streaming Fehler: {e}")
            # Fallback to blocking if streaming fails
            yield self.generate_response(system_prompt, user_prompt, max_tokens, temperature, history)

    def get_identity_metrics(self) -> str:
        """
        Gibt Identity Enforcement Metrics zurück.

        Returns:
            Formatierter Metrics-Report
        """
        return self.identity_metrics.report()
