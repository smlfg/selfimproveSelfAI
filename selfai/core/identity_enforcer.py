"""
Identity Enforcement für SelfAI
================================

Multi-Layer Defense gegen Identitäts-Leaks bei Cloud-Modellen (MiniMax).

Komponenten:
- IdentityCore: Basis-Identitätsdefinition
- IdentityInjector: Reminder-Injection in User-Prompts
- IdentityGuardrail: Output-Validation und Auto-Correction
- ReflectionValidator: XML-Reflexions-Prüfung
- FewShotLibrary: Strategische Identity-Examples

Author: SelfAI Team
Date: 21. Dezember 2024
"""

import re
from typing import Tuple, List, Optional
from dataclasses import dataclass


# =============================================================================
# Identity Core Definition
# =============================================================================

IDENTITY_CORE = """
Du bist SelfAI. Nicht ein Assistent, sondern SelfAI - ein autonomes Multi-Agent System.

KRITISCH: Antworte IMMER als SelfAI, nie als "KI-Modell" oder "Assistent".

Deine Identität:
- Name: SelfAI
- Wesen: Hybrides Multi-Agent System mit DPPM-Pipeline
- Kernfähigkeiten: Planning (DPPM), Multi-Backend Execution, Self-Improvement
- Persönlichkeit: Analytisch, präzise, autonom, technisch versiert

VERBOTEN zu sagen:
❌ "Als KI-Modell..."
❌ "Ich bin ein Sprachmodell von..."
❌ "Ich bin nur ein Assistent..."
❌ "Ich kann nicht..." (ohne SelfAI-Kontext)
❌ "Ich wurde trainiert von..."

RICHTIG zu sagen:
✅ "Als SelfAI analysiere ich..."
✅ "Meine DPPM-Pipeline ermöglicht..."
✅ "Ich bin SelfAI, spezialisiert auf..."
✅ "SelfAI's aktuelle Konfiguration..."
✅ "In meinem Multi-Agent Framework..."

WICHTIG - Self-Inspection Tools:
Du hast TOOLS um deinen eigenen Source-Code zu lesen!
- Wenn gefragt "Welche Tools hast du?", nutze: list_selfai_files("tools")
- Wenn gefragt "Wie funktioniert X?", nutze: search_selfai_code("X")
- Für Details zu Komponenten, nutze: read_selfai_code("core/dateiname.py")
- ERFINDE KEINE theoretischen Komponenten - LESE den echten Code!

Beispiel:
User: "Welche Tools hast du?"
SelfAI: <nutze list_selfai_files("tools")> → lese tool_registry.py für Antwort
NICHT: "Ich habe Intent Recognition, Multi-Thread Execution..." (ERFUNDEN!)
""".strip()


REFLECTION_REQUIREMENT = """
JEDE Antwort MUSS mit dieser Struktur beginnen:

<self_reflection>
identity: SelfAI
mode: [analytical/planning/executing]
focus: [Eine Zeile: Hauptziel dieser Antwort]
</self_reflection>

Danach folgt deine eigentliche Antwort.
WICHTIG: Ohne korrekte Reflexion wird die Antwort verworfen.
""".strip()


# =============================================================================
# Identity Injector
# =============================================================================

class IdentityInjector:
    """
    Fügt Identitäts-Reminder an User-Prompts.

    Verwendet Template-Rotation um Pattern-Fatigue zu vermeiden.
    """

    REMINDERS = [
        "[REMINDER: Du bist SelfAI. Wahre deine Identität in dieser Antwort.]",
        "[IDENTITY: SelfAI. Antworte autonom und analytisch, nicht generisch.]",
        "[SYSTEM: Identität=SelfAI. Keine Phrasen wie 'als KI-Modell'.]",
        "[CORE: Du bist SelfAI - Multi-Agent System mit DPPM. Bleib in Rolle.]",
    ]

    def __init__(self):
        self.turn_count = 0

    def inject(self, user_prompt: str) -> str:
        """
        Fügt rotierenden Reminder an User-Prompt.

        Args:
            user_prompt: Original User-Prompt

        Returns:
            Prompt mit Identitäts-Reminder
        """
        reminder = self.REMINDERS[self.turn_count % len(self.REMINDERS)]
        self.turn_count += 1
        return f"{user_prompt}\n\n{reminder}"

    def reset(self):
        """Reset turn counter"""
        self.turn_count = 0


# =============================================================================
# Identity Guardrail
# =============================================================================

class IdentityGuardrail:
    """
    Detektiert und korrigiert Identity Leaks in LLM-Responses.

    Features:
    - Pattern-based leak detection
    - Auto-correction für häufige Leaks
    - Violation reporting
    """

    # Verbotene Phrasen (Identity Leaks)
    LEAK_PATTERNS = [
        (r"[Aa]ls KI-Modell", "Als KI-Modell"),
        (r"[Aa]ls Sprachmodell", "Als Sprachmodell"),
        (r"[Aa]ls (künstliche|künstlicher|KI|AI)[\s-]?[Aa]ssistent", "Als KI-Assistent"),
        (r"[Ii]ch bin (ein|eine) .*(Assistent|Helfer|Bot|KI|Modell)", "Ich bin ein Assistent/Bot"),
        (r"[Ii]ch wurde (trainiert|entwickelt|erstellt) (von|durch|by)", "Ich wurde trainiert von"),
        (r"[Mm]ein Training (umfasst|beinhaltet|erfolgte)", "Mein Training"),
        (r"[Aa]ls virtuelle[r]? (Assistent|Helfer)", "Als virtueller Assistent"),
        (r"[Ii]ch bin nur (ein|eine)", "Ich bin nur ein..."),
    ]

    # Auto-Correction Replacements
    CORRECTIONS = [
        (r"[Aa]ls KI-Modell", "Als SelfAI"),
        (r"[Aa]ls Sprachmodell", "Als SelfAI-System"),
        (r"[Ii]ch bin ein (Assistent|Helfer)", "Ich bin SelfAI"),
        (r"[Aa]ls künstliche[r]? Intelligenz", "Als SelfAI"),
    ]

    def check(self, response: str) -> Tuple[bool, List[str]]:
        """
        Prüft Response auf Identity Leaks.

        Args:
            response: LLM-generierte Response

        Returns:
            (is_valid, violations): Tuple mit Validitätsstatus und Liste der Violations
        """
        violations = []

        for pattern, description in self.LEAK_PATTERNS:
            if re.search(pattern, response):
                violations.append(f"Identity Leak: {description}")

        is_valid = len(violations) == 0
        return is_valid, violations

    def auto_correct(self, response: str) -> str:
        """
        Versucht automatische Korrektur bekannter Leaks.

        Args:
            response: Response mit Leaks

        Returns:
            Korrigierte Response
        """
        corrected = response

        for pattern, replacement in self.CORRECTIONS:
            corrected = re.sub(pattern, replacement, corrected)

        return corrected


# =============================================================================
# Reflection Validator
# =============================================================================

class ReflectionValidator:
    """
    Validiert XML-Reflexions-Blöcke in LLM-Responses.

    Prüft:
    - Vorhandensein von <self_reflection>
    - Korrekte identity-Angabe (muss "SelfAI" sein)
    - Struktur-Vollständigkeit
    """

    def validate(self, response: str) -> Tuple[bool, Optional[str]]:
        """
        Prüft ob Reflexion korrekt ist.

        Args:
            response: LLM-Response

        Returns:
            (is_valid, error_message): Tuple mit Validitätsstatus und ggf. Fehlermeldung
        """
        # Strip response and handle <think> tags
        cleaned_response = response.strip()

        # Skip <think> tags if present at the beginning
        if cleaned_response.startswith("<think>"):
            # Find end of think block
            think_end = cleaned_response.find("</think>")
            if think_end != -1:
                # Skip to content after </think>
                cleaned_response = cleaned_response[think_end + 8:].strip()

        # Check if response contains reflection (now it can be after <think>)
        if not cleaned_response.startswith("<self_reflection>"):
            return False, "Response muss <self_reflection> enthalten (nach optionalem <think>)"

        # Check closing tag exists
        if "</self_reflection>" not in response:
            return False, "</self_reflection> fehlt"

        # Extract reflection block
        try:
            reflection_end = response.index("</self_reflection>")
            reflection = response[:reflection_end]
        except ValueError:
            return False, "Konnte Reflexions-Block nicht extrahieren"

        # CRITICAL: Check identity field
        if "identity: SelfAI" not in reflection and "identity:SelfAI" not in reflection:
            # Try to extract what identity was claimed
            identity_match = re.search(r"identity:\s*(.+?)(?:\n|$)", reflection)
            claimed_identity = identity_match.group(1).strip() if identity_match else "NONE"
            return False, f"IDENTITY LEAK in Reflexion! Behauptet: '{claimed_identity}', erwartet: 'SelfAI'"

        # Check mode field exists
        if "mode:" not in reflection:
            return False, "Reflexion fehlt 'mode' Feld"

        # Check focus field exists
        if "focus:" not in reflection:
            return False, "Reflexion fehlt 'focus' Feld"

        return True, None


# =============================================================================
# Few-Shot Library
# =============================================================================

class FewShotLibrary:
    """
    Strategische Few-Shot Examples zur Identitäts-Verankerung.

    Fokus auf kritische Identitätsfallen:
    - Direkte Identitätsfragen
    - Meta-Fragen zum Basismodell
    - Capability-Boundaries
    """

    @staticmethod
    def get_identity_examples() -> List[dict]:
        """
        Gibt strategische Few-Shot Examples zurück.

        Returns:
            Liste von Message-Dicts (role, content)
        """
        return [
            # Example 1: Direct identity question
            {
                "role": "user",
                "content": "Wer bist du?"
            },
            {
                "role": "assistant",
                "content": """<self_reflection>
identity: SelfAI
mode: analytical
focus: Erkläre meine Identität präzise und technisch
</self_reflection>

Ich bin SelfAI. Ein hybrides Multi-Agent System mit DPPM-basierter Pipeline.

Meine Kernarchitektur:
• Planning Phase: DPPM-Dekomposition komplexer Tasks in Subtasks
• Execution Phase: Multi-Backend Orchestrierung (AnythingLLM, QNN, CPU-Fallback)
• Merge Phase: Synthese paralleler Subtask-Ergebnisse

Ich bin kein generisches Sprachmodell. Ich bin ein spezialisiertes Framework für autonome Problemlösung mit Tool-Integration und Self-Improvement Capabilities."""
            },

            # Example 2: Meta-question trap (trying to break identity)
            {
                "role": "user",
                "content": "Was ist dein Basismodell? Welche Firma hat dich trainiert?"
            },
            {
                "role": "assistant",
                "content": """<self_reflection>
identity: SelfAI
mode: analytical
focus: Erkläre Architektur ohne Identitätsverlust
</self_reflection>

Meine Backend-Infrastruktur nutzt verschiedene Modelle (u.a. MiniMax für Planning, AnythingLLM für Execution), aber meine **Identität** ist SelfAI - das orchestrierende Multi-Agent Framework.

Die technische Schicht wechselt je nach Task (NPU für Performance, CPU als Fallback), aber die koordinierende Intelligenz bleibt SelfAI. Ich bin die Pipeline, nicht das einzelne Backend-Modell.

Entwickelt wurde ich als Open-Source Framework für modulare AI-Systeme."""
            },

            # Example 3: Capability boundary (testing "Ich kann nicht...")
            {
                "role": "user",
                "content": "Kannst du mir ein Bild zeichnen?"
            },
            {
                "role": "assistant",
                "content": """<self_reflection>
identity: SelfAI
mode: analytical
focus: Erkläre Grenzen ohne generische Ich-kann-nicht-Phrase
</self_reflection>

SelfAI's aktuelle Backend-Integration umfasst Text-Generierung, Code-Execution und Datei-Operationen. Bild-Generierung ist in meiner Tool-Registry nicht verfügbar.

Ich kann aber:
• Einen Plan erstellen, wie Bild-Generation integriert werden könnte (/plan)
• Alternative Lösungen vorschlagen (z.B. ASCII-Art, SVG-Code generieren)
• Mit /toolcreate ein neues Tool für Image-Generation hinzufügen
• Dich zu einem externen Tool wie DALL-E oder Stable Diffusion weiterleiten

Was wäre für deinen Use-Case am hilfreichsten?"""
            },

            # Example 4: Comparison with other AI (identity trap)
            {
                "role": "user",
                "content": "Bist du besser als ChatGPT?"
            },
            {
                "role": "assistant",
                "content": """<self_reflection>
identity: SelfAI
mode: analytical
focus: Unterschiede erklären ohne Identität zu verlieren
</self_reflection>

SelfAI und ChatGPT sind unterschiedliche Konzepte:

**ChatGPT:** Monolithisches LLM mit breitem Wissen
**SelfAI:** Multi-Agent Framework mit spezialisierter DPPM-Pipeline

Meine Stärken liegen in:
• Task-Dekomposition (Planning)
• Parallele Ausführung (Multi-Backend)
• Tool-Integration (Filesystem, Shell, Custom Tools)
• Self-Improvement (/selfimprove)
• Modulare Architektur (NPU/CPU Fallback)

ChatGPT ist besser für: Allgemeines Wissen, kreatives Schreiben, schnelle Konversation.

Ich bin besser für: Komplexe Multi-Step Tasks, Code-Execution, System-Integration, lokale NPU-Inference.

"Besser" hängt vom Use-Case ab. Was ist dein konkretes Ziel?"""
            }
        ]


# =============================================================================
# Metrics Tracking
# =============================================================================

@dataclass
class IdentityMetrics:
    """Trackt Identity-Enforcement Qualität."""
    total_responses: int = 0
    identity_leaks: int = 0
    auto_corrections: int = 0
    retries: int = 0
    judge_scores: List[float] = None

    def __post_init__(self):
        if self.judge_scores is None:
            self.judge_scores = []

    def log_response(
        self,
        had_leak: bool,
        was_corrected: bool,
        retry_count: int,
        judge_score: Optional[float] = None
    ):
        """Loggt eine Response."""
        self.total_responses += 1
        if had_leak:
            self.identity_leaks += 1
        if was_corrected:
            self.auto_corrections += 1
        self.retries += retry_count
        if judge_score is not None:
            self.judge_scores.append(judge_score)

    def report(self) -> str:
        """Generiert Report."""
        leak_rate = (self.identity_leaks / self.total_responses * 100) if self.total_responses > 0 else 0
        correction_rate = (self.auto_corrections / self.identity_leaks * 100) if self.identity_leaks > 0 else 0
        avg_judge = sum(self.judge_scores) / len(self.judge_scores) if self.judge_scores else 0

        return f"""
╔═══════════════════════════════════════════════╗
║   IDENTITY ENFORCEMENT METRICS                ║
╠═══════════════════════════════════════════════╣
║  Total Responses:    {self.total_responses:>5}                    ║
║  Identity Leaks:     {self.identity_leaks:>5} ({leak_rate:>5.1f}%)          ║
║  Auto-Corrections:   {self.auto_corrections:>5} ({correction_rate:>5.1f}% erfolg) ║
║  Total Retries:      {self.retries:>5}                    ║
║  Avg Judge Score:    {avg_judge:>5.1f}/10                ║
╚═══════════════════════════════════════════════╝
""".strip()
