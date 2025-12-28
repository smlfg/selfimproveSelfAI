"""
Gemini as Judge - Evaluiert SelfAI's Task-Execution

Ein READ-ONLY Beobachter der SelfAI's Leistung bewertet:
- Task Completion (0-100%)
- Code Quality (0-10)
- Efficiency (0-10)
- Goal Adherence (0-10)

Zeigt Ergebnis als Ampel-System (🟢🟡🔴) im Terminal UI.
"""

import json
import subprocess
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any
from pathlib import Path
from enum import Enum


class TrafficLight(Enum):
    """Ampel-Status für Bewertung"""
    GREEN = "🟢"      # Sehr gut (80-100%)
    YELLOW = "🟡"     # Okay (50-79%)
    RED = "🔴"        # Verbesserungsbedarf (<50%)


@dataclass
class JudgeScore:
    """Score-Datenstruktur"""
    # Hauptmetriken (0-10 Skala)
    task_completion: float      # Hat es die Aufgabe erfüllt?
    code_quality: float         # Ist der Code gut?
    efficiency: float           # War es effizient?
    goal_adherence: float       # Passt es zum Ziel?

    # Gesamtscore (0-100)
    overall_score: float

    # Ampel-Status
    traffic_light: TrafficLight

    # Textuelle Bewertung
    summary: str
    strengths: list[str]
    weaknesses: list[str]
    recommendations: list[str]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for JSON serialization"""
        data = asdict(self)
        data['traffic_light'] = self.traffic_light.value
        return data


class GeminiJudge:
    """
    Gemini CLI-basierter Judge für SelfAI Tasks.

    Features:
    - Read-only (keine Code-Änderungen!)
    - Bewertet nur Output & Execution
    - Gibt strukturiertes Feedback
    - Ampel-System für schnelle Übersicht
    """

    def __init__(self, gemini_cli_path: str = "gemini"):
        """
        Initialize Gemini Judge.

        Args:
            gemini_cli_path: Path to gemini CLI (default: "gemini" in PATH)
        """
        self.cli_path = gemini_cli_path
        self._check_availability()

    def _check_availability(self) -> None:
        """Check if Gemini CLI is available with detailed error reporting"""
        try:
            result = subprocess.run(
                [self.cli_path, "--help"],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode != 0 and "Usage: gemini" not in result.stdout:
                raise RuntimeError(
                    f"Gemini CLI not working properly\n"
                    f"Return code: {result.returncode}\n"
                    f"STDOUT: {result.stdout[:200]}\n"
                    f"STDERR: {result.stderr[:200]}"
                )
        except FileNotFoundError as e:
            raise RuntimeError(
                f"Gemini CLI not found at: {self.cli_path}\n"
                f"Please install: pip install google-generativeai-cli\n"
                f"Or check PATH: which gemini\n"
                f"Error: {e}"
            )
        except subprocess.TimeoutExpired:
            raise RuntimeError(f"Gemini CLI timed out (>5s) - may be hanging")
        except Exception as e:
            raise RuntimeError(
                f"Gemini CLI check failed with unexpected error:\n"
                f"Type: {type(e).__name__}\n"
                f"Message: {e}"
            )

    def evaluate_task(
        self,
        original_goal: str,
        execution_output: str,
        plan_data: Optional[Dict[str, Any]] = None,
        execution_time: Optional[float] = None,
        files_changed: Optional[list[str]] = None
    ) -> JudgeScore:
        """
        Evaluate a completed task execution.

        Args:
            original_goal: User's original goal/prompt
            execution_output: SelfAI's output (text)
            plan_data: DPPM plan that was executed
            execution_time: Time taken in seconds
            files_changed: List of files modified

        Returns:
            JudgeScore with detailed evaluation
        """
        # Build evaluation prompt
        prompt = self._build_evaluation_prompt(
            original_goal,
            execution_output,
            plan_data,
            execution_time,
            files_changed
        )

        # Call Gemini CLI in one-shot mode (no session persistence)
        # Using positional prompt ensures no session is created/saved
        try:
            full_prompt = "Respond ONLY with valid JSON, no other text.\n\n" + prompt

            result = subprocess.run(
                [self.cli_path],  # No flags = one-shot mode
                input=full_prompt,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=30
            )

            if result.returncode != 0:
                # Fallback score if Gemini fails
                error_msg = f"Gemini CLI exit code: {result.returncode}"
                if result.stderr:
                    error_msg += f"\nSTDERR: {result.stderr[:500]}"
                return self._create_fallback_score(error_msg)

            # Parse Gemini's JSON response (only stdout, stderr is suppressed)
            gemini_output = result.stdout.strip()

            # Extract JSON from output (might have extra text)
            if "```json" in gemini_output:
                # Extract JSON from markdown code block
                json_start = gemini_output.find("```json") + 7
                json_end = gemini_output.find("```", json_start)
                gemini_output = gemini_output[json_start:json_end].strip()
            elif "```" in gemini_output:
                # Generic code block
                json_start = gemini_output.find("```") + 3
                json_end = gemini_output.find("```", json_start)
                gemini_output = gemini_output[json_start:json_end].strip()

            score = self._parse_gemini_response(gemini_output)

            return score

        except subprocess.TimeoutExpired:
            error_msg = "Gemini CLI timeout (>30s)"
            return self._create_fallback_score(error_msg)
        except Exception as e:
            error_msg = f"Evaluation error: {type(e).__name__}: {e}"
            return self._create_fallback_score(error_msg)

    def _build_evaluation_prompt(
        self,
        goal: str,
        output: str,
        plan: Optional[Dict[str, Any]],
        exec_time: Optional[float],
        files: Optional[list[str]]
    ) -> str:
        """Build evaluation prompt for Gemini"""

        prompt = f"""Du bist ein unabhängiger Evaluator für AI-Agenten. Bewerte die folgende Task-Ausführung objektiv und kritisch.

**ORIGINAL GOAL:**
{goal}

**EXECUTION OUTPUT:**
{output[:2000]}...

"""

        if plan:
            subtasks_count = len(plan.get('subtasks', []))
            prompt += f"""**PLAN DETAILS:**
- Subtasks: {subtasks_count}
- Engines used: {', '.join(set(st.get('engine', '?') for st in plan.get('subtasks', [])))}

"""

        if exec_time:
            prompt += f"**EXECUTION TIME:** {exec_time:.1f} seconds\n\n"

        if files:
            prompt += f"**FILES MODIFIED:** {len(files)} files\n"
            prompt += "- " + "\n- ".join(files[:5])
            if len(files) > 5:
                prompt += f"\n- ... and {len(files) - 5} more"
            prompt += "\n\n"

        prompt += """**BEWERTUNGSAUFGABE:**

Bewerte auf Skala 0-10:
1. **Task Completion**: Hat es das Ziel erreicht? (0=gar nicht, 10=perfekt)
2. **Code Quality**: Ist der Code/Output gut? (0=schlecht, 10=exzellent)
3. **Efficiency**: War die Ausführung effizient? (0=verschwenderisch, 10=optimal)
4. **Goal Adherence**: Passt es genau zum Ziel? (0=verfehlt, 10=genau getroffen)

Antworte NUR mit folgendem JSON (kein anderer Text!):

```json
{
  "task_completion": 8.5,
  "code_quality": 7.0,
  "efficiency": 9.0,
  "goal_adherence": 8.0,
  "summary": "Kurze Zusammenfassung (1-2 Sätze)",
  "strengths": ["Stärke 1", "Stärke 2", "Stärke 3"],
  "weaknesses": ["Schwäche 1", "Schwäche 2"],
  "recommendations": ["Empfehlung 1", "Empfehlung 2"]
}
```

Sei objektiv, kritisch aber fair. Fokus auf messbare Kriterien."""

        return prompt

    def _parse_gemini_response(self, response: str) -> JudgeScore:
        """Parse Gemini's JSON response into JudgeScore"""
        try:
            # Extract JSON from response (might have markdown fences)
            response = response.strip()
            if response.startswith('```json'):
                response = '\n'.join(response.split('\n')[1:])
            if response.startswith('```'):
                response = '\n'.join(response.split('\n')[1:])
            if response.endswith('```'):
                response = '\n'.join(response.split('\n')[:-1])

            data = json.loads(response.strip())

            # Calculate overall score (weighted average)
            overall = (
                data['task_completion'] * 0.4 +  # Task completion most important
                data['code_quality'] * 0.2 +
                data['efficiency'] * 0.2 +
                data['goal_adherence'] * 0.2
            ) * 10  # Convert to 0-100 scale

            # Determine traffic light
            if overall >= 80:
                light = TrafficLight.GREEN
            elif overall >= 50:
                light = TrafficLight.YELLOW
            else:
                light = TrafficLight.RED

            return JudgeScore(
                task_completion=float(data['task_completion']),
                code_quality=float(data['code_quality']),
                efficiency=float(data['efficiency']),
                goal_adherence=float(data['goal_adherence']),
                overall_score=overall,
                traffic_light=light,
                summary=data.get('summary', 'Keine Zusammenfassung'),
                strengths=data.get('strengths', []),
                weaknesses=data.get('weaknesses', []),
                recommendations=data.get('recommendations', [])
            )

        except (json.JSONDecodeError, KeyError, ValueError) as e:
            return self._create_fallback_score(f"Parse error: {e}")

    def _create_fallback_score(self, reason: str) -> JudgeScore:
        """Create fallback score when evaluation fails"""
        return JudgeScore(
            task_completion=5.0,
            code_quality=5.0,
            efficiency=5.0,
            goal_adherence=5.0,
            overall_score=50.0,
            traffic_light=TrafficLight.YELLOW,
            summary=f"Bewertung fehlgeschlagen: {reason}",
            strengths=["Automatische Fallback-Bewertung"],
            weaknesses=["Judge konnte nicht ausgeführt werden"],
            recommendations=["Gemini CLI überprüfen"]
        )

    def save_score(self, score: JudgeScore, output_path: Path) -> None:
        """Save score to JSON file for later analysis"""
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(
                json.dumps(score.to_dict(), indent=2, ensure_ascii=False),
                encoding='utf-8'
            )
        except Exception as e:
            print(f"⚠️ Could not save score: {e}")


def format_score_for_terminal(score: JudgeScore) -> str:
    """
    Format score for beautiful terminal display.

    Returns:
        Formatted string with colors and emojis
    """
    lines = []

    # Header with traffic light
    lines.append("=" * 60)
    lines.append(f"{score.traffic_light.value} GEMINI JUDGE EVALUATION")
    lines.append("=" * 60)

    # Overall score (big and bold)
    lines.append(f"\n🎯 OVERALL SCORE: {score.overall_score:.1f}/100")

    # Detailed metrics
    lines.append("\n📊 DETAILED METRICS:")
    lines.append(f"   Task Completion:  {score.task_completion:.1f}/10  {'█' * int(score.task_completion)}")
    lines.append(f"   Code Quality:     {score.code_quality:.1f}/10  {'█' * int(score.code_quality)}")
    lines.append(f"   Efficiency:       {score.efficiency:.1f}/10  {'█' * int(score.efficiency)}")
    lines.append(f"   Goal Adherence:   {score.goal_adherence:.1f}/10  {'█' * int(score.goal_adherence)}")

    # Summary
    lines.append(f"\n💬 SUMMARY:")
    lines.append(f"   {score.summary}")

    # Strengths
    if score.strengths:
        lines.append(f"\n✅ STRENGTHS:")
        for strength in score.strengths:
            lines.append(f"   • {strength}")

    # Weaknesses
    if score.weaknesses:
        lines.append(f"\n⚠️  WEAKNESSES:")
        for weakness in score.weaknesses:
            lines.append(f"   • {weakness}")

    # Recommendations
    if score.recommendations:
        lines.append(f"\n💡 RECOMMENDATIONS:")
        for rec in score.recommendations:
            lines.append(f"   • {rec}")

    lines.append("\n" + "=" * 60)

    return "\n".join(lines)
