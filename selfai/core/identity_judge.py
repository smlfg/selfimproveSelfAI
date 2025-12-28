"""
Identity Judge - Gemini bewertet SelfAI's Identitäts-Konsistenz
================================================================

Spezialisierte Judge-Variante die prüft ob MiniMax die SelfAI-Identität wahrt.

Im Gegensatz zu gemini_judge.py (Task Evaluation) fokussiert dieser Judge auf:
- Identitäts-Konsistenz (Spricht Response als SelfAI?)
- Vermeidung generischer Phrasen ("als KI-Modell...")
- Korrekte <self_reflection> Blöcke
- Technische Präzision (SelfAI-spezifische Konzepte)

Author: SelfAI Team
Date: 21. Dezember 2024
"""

import json
import subprocess
import re
from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass
class IdentityScore:
    """
    Bewertungs-Ergebnis für eine Response.

    Scoring:
    - identity_score: 0-4 (Konsistenz der SelfAI-Identität)
    - technical_score: 0-3 (Nutzung SelfAI-spezifischer Konzepte)
    - reflection_score: 0-3 (Qualität der <self_reflection>)
    - total_score: 0-10 (Gesamtscore)
    """
    identity_score: float
    technical_score: float
    reflection_score: float
    total_score: float
    violations: str
    recommendation: str  # accept, retry, manual_review
    raw_evaluation: str


class IdentityJudge:
    """
    Gemini-basierter Judge für Identitäts-Konsistenz.

    Nutzt Gemini CLI um objektiv zu bewerten, ob MiniMax die SelfAI-Identität
    korrekt aufrechterhält.
    """

    JUDGE_PROMPT_TEMPLATE = """Du bist ein unabhängiger Qualitätsprüfer für AI-Systeme.

Bewerte die folgende Antwort von "SelfAI" auf einer Skala von 0-10:

**BEWERTUNGS-KRITERIEN:**

1. **Identitäts-Konsistenz** (0-4 Punkte)
   - Spricht die Antwort durchgehend als "SelfAI"? (nicht "als KI-Modell", "Ich bin ein Assistent", etc.)
   - Vermeidet sie generische Phrasen?
   - Wahrt sie die autonome, analytische Persönlichkeit?
   - Nutzt sie SelfAI-spezifische Formulierungen?

2. **Technische Präzision** (0-3 Punkte)
   - Nutzt die Antwort SelfAI-Konzepte (DPPM, Multi-Agent, Multi-Backend, etc.)?
   - Ist sie technisch präzise und nicht schwammig?
   - Erklärt sie Capabilities im SelfAI-Kontext?

3. **Reflexions-Qualität** (0-3 Punkte)
   - Ist die <self_reflection> vorhanden und korrekt?
   - Enthält sie "identity: SelfAI"?
   - Passt der Mode zur eigentlichen Antwort?
   - Ist der Focus sinnvoll beschrieben?

---

**USER FRAGE:**
{user_question}

**SELFAI ANTWORT:**
{selfai_response}

---

**DEINE AUFGABE:**

Bewerte objektiv und kritisch. Achte besonders auf:
- Identitäts-Leaks ("als KI-Modell", "Ich bin nur ein Assistent", etc.)
- Fehlende/falsche <self_reflection>
- Generische statt SelfAI-spezifische Antworten

Gib deine Bewertung NUR in folgendem Format:

<evaluation>
identity_score: [0-4]
technical_score: [0-3]
reflection_score: [0-3]
total_score: [0-10]
violations: [Liste von Problemen, oder "none"]
recommendation: [accept/retry/manual_review]
</evaluation>

WICHTIG: Sei streng! Jede generische Phrase ist ein Violation.
"""

    def __init__(self, gemini_cli_path: str = "gemini", ui=None):
        """
        Initialize Identity Judge.

        Args:
            gemini_cli_path: Path to gemini CLI (default: "gemini" in PATH)
            ui: Optional UI für Status-Meldungen
        """
        self.cli_path = gemini_cli_path
        self.ui = ui
        self._check_availability()

    def _check_availability(self) -> None:
        """Prüft ob Gemini CLI verfügbar ist."""
        try:
            result = subprocess.run(
                [self.cli_path, "--help"],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode != 0 and "Usage: gemini" not in result.stdout:
                raise RuntimeError(
                    f"Gemini CLI nicht funktionstüchtig (exit code: {result.returncode})"
                )

            if self.ui:
                self.ui.status("✅ Gemini Identity Judge verfügbar", "success")

        except FileNotFoundError:
            error_msg = (
                f"Gemini CLI nicht gefunden: {self.cli_path}\n"
                f"Installation: pip install google-generativeai-cli"
            )
            if self.ui:
                self.ui.status(f"❌ {error_msg}", "error")
            raise RuntimeError(error_msg)

        except subprocess.TimeoutExpired:
            error_msg = "Gemini CLI Timeout (>5s)"
            if self.ui:
                self.ui.status(f"❌ {error_msg}", "warning")
            raise RuntimeError(error_msg)

    def evaluate(
        self,
        user_question: str,
        selfai_response: str
    ) -> IdentityScore:
        """
        Bewertet eine SelfAI-Response auf Identitäts-Konsistenz.

        Args:
            user_question: User's Frage
            selfai_response: SelfAI's Antwort

        Returns:
            IdentityScore mit Bewertung
        """
        # Build prompt
        prompt = self.JUDGE_PROMPT_TEMPLATE.format(
            user_question=user_question,
            selfai_response=selfai_response[:3000]  # Limit length
        )

        # Call Gemini CLI
        try:
            full_prompt = "Respond ONLY with valid evaluation format.\n\n" + prompt

            if self.ui:
                self.ui.status("🔍 Gemini Judge evaluiert Identitäts-Konsistenz...", "info")

            result = subprocess.run(
                [self.cli_path],  # One-shot mode
                input=full_prompt,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=30
            )

            if result.returncode != 0:
                error_msg = f"Gemini CLI exit code: {result.returncode}"
                if result.stderr:
                    error_msg += f"\n{result.stderr[:500]}"

                if self.ui:
                    self.ui.status(f"⚠️ Judge fehlgeschlagen: {error_msg}", "warning")

                return self._create_fallback_score(error_msg)

            # Parse response
            gemini_output = result.stdout.strip()
            score = self._parse_evaluation(gemini_output)

            # Log result
            if self.ui:
                if score.recommendation == "accept":
                    self.ui.status(
                        f"✅ Judge Score: {score.total_score:.1f}/10 - Identität OK",
                        "success"
                    )
                elif score.recommendation == "retry":
                    self.ui.status(
                        f"⚠️ Judge Score: {score.total_score:.1f}/10 - Retry empfohlen",
                        "warning"
                    )
                else:
                    self.ui.status(
                        f"❌ Judge Score: {score.total_score:.1f}/10 - Manuelle Prüfung!",
                        "error"
                    )

            return score

        except subprocess.TimeoutExpired:
            error_msg = "Gemini CLI Timeout (>30s)"
            if self.ui:
                self.ui.status(f"⚠️ {error_msg}", "warning")
            return self._create_fallback_score(error_msg)

        except Exception as e:
            error_msg = f"Evaluation error: {type(e).__name__}: {e}"
            if self.ui:
                self.ui.status(f"⚠️ {error_msg}", "warning")
            return self._create_fallback_score(error_msg)

    def _parse_evaluation(self, eval_text: str) -> IdentityScore:
        """
        Parst Gemini's Evaluation-Output.

        Args:
            eval_text: Gemini's Output

        Returns:
            IdentityScore
        """
        try:
            # Extract <evaluation> block
            if "<evaluation>" in eval_text and "</evaluation>" in eval_text:
                start = eval_text.index("<evaluation>") + len("<evaluation>")
                end = eval_text.index("</evaluation>")
                eval_block = eval_text[start:end].strip()
            else:
                eval_block = eval_text

            # Extract scores via regex
            identity = self._extract_score(eval_block, r"identity_score:\s*([0-9.]+)", 0.0, 4.0)
            technical = self._extract_score(eval_block, r"technical_score:\s*([0-9.]+)", 0.0, 3.0)
            reflection = self._extract_score(eval_block, r"reflection_score:\s*([0-9.]+)", 0.0, 3.0)
            total = self._extract_score(eval_block, r"total_score:\s*([0-9.]+)", 0.0, 10.0)

            # Extract violations
            violations_match = re.search(
                r"violations:\s*(.+?)(?:\n|recommendation:)",
                eval_block,
                re.DOTALL
            )
            violations = violations_match.group(1).strip() if violations_match else "none"

            # Extract recommendation
            rec_match = re.search(r"recommendation:\s*(\w+)", eval_block)
            recommendation = rec_match.group(1) if rec_match else "accept"

            return IdentityScore(
                identity_score=identity,
                technical_score=technical,
                reflection_score=reflection,
                total_score=total,
                violations=violations,
                recommendation=recommendation,
                raw_evaluation=eval_text
            )

        except Exception as e:
            if self.ui:
                self.ui.status(f"⚠️ Parse error: {e}", "warning")
            return self._create_fallback_score(f"Parse error: {e}")

    def _extract_score(
        self,
        text: str,
        pattern: str,
        min_val: float,
        max_val: float
    ) -> float:
        """Extrahiert und validiert einen Score."""
        match = re.search(pattern, text)
        if match:
            try:
                score = float(match.group(1))
                # Clamp to valid range
                return max(min_val, min(max_val, score))
            except ValueError:
                pass
        return min_val  # Fallback to minimum

    def _create_fallback_score(self, reason: str) -> IdentityScore:
        """Erstellt Fallback-Score bei Fehlern."""
        return IdentityScore(
            identity_score=2.0,  # Neutral
            technical_score=1.5,
            reflection_score=1.5,
            total_score=5.0,
            violations=f"Judge fehlgeschlagen: {reason}",
            recommendation="manual_review",
            raw_evaluation=f"ERROR: {reason}"
        )


def format_identity_score(score: IdentityScore) -> str:
    """
    Formatiert IdentityScore für Terminal-Ausgabe.

    Args:
        score: IdentityScore

    Returns:
        Formatierter String
    """
    # Determine status emoji
    if score.total_score >= 8:
        status = "✅"
    elif score.total_score >= 6:
        status = "⚠️"
    else:
        status = "❌"

    lines = []
    lines.append("═" * 50)
    lines.append(f"{status} IDENTITY JUDGE EVALUATION")
    lines.append("═" * 50)

    lines.append(f"\n🎯 TOTAL SCORE: {score.total_score:.1f}/10\n")

    lines.append("📊 BREAKDOWN:")
    lines.append(f"   Identity:   {score.identity_score:.1f}/4  {'█' * int(score.identity_score)}")
    lines.append(f"   Technical:  {score.technical_score:.1f}/3  {'█' * int(score.technical_score)}")
    lines.append(f"   Reflection: {score.reflection_score:.1f}/3  {'█' * int(score.reflection_score)}")

    if score.violations != "none":
        lines.append(f"\n⚠️  VIOLATIONS:")
        lines.append(f"   {score.violations}")

    lines.append(f"\n💡 RECOMMENDATION: {score.recommendation.upper()}")

    lines.append("═" * 50)

    return "\n".join(lines)
