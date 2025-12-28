# Vibe Coding Protokoll: SelfAI

**Datum:** 24. Dezember 2025
**Analyst:** Gemini (CLI Agent)
**Gegenstand:** Analyse der Entwicklungsmethodik, Strategie und Kultur des SelfAI-Projekts.

---

## 1. Der "Vibe" des Projekts: Pragmatische Evolution

Das SelfAI-Projekt strahlt eine bemerkenswerte **Resilienz** und **Lernfähigkeit** aus. Es ist kein steriles Software-Projekt, sondern wirkt wie ein "organisches Wesen", das durch Schmerz und Fehler gewachsen ist.

**Kern-Philosophie:**
*   **"Pragmatismus schlägt Dogma":** Das ursprüngliche Dogma ("Muss auf NPU laufen!") wurde fallen gelassen, als es den Fortschritt blockierte. Der Switch zum hybriden Modell rettete das Projekt.
*   **"Prozess vor Code":** Die Erkenntnis, dass eine instabile Umgebung mehr Zeit kostet als schlechter Code, führte zur konsequenten Einführung von Dev Containern.
*   **"Agentic Self-Correction":** Das System ist so gebaut, dass es seine eigenen Fehler erkennen und beheben soll (Self-Improvement, Feedback-Loops).

---

## 2. Vibe Coding Practices: Wie gearbeitet wurde

Der User ("Developer") nutzt eine hochentwickelte Form des **"AI-Orchestrated Development"**.

### Die Orchestrierungs-Kette
Es gibt eine klare Hierarchie der Intelligenz:
1.  **Der User (Architect):** Setzt Vision, OKRs und trifft die harten Pivot-Entscheidungen.
2.  **Claude Code (Manager):** Orchestriert die Umsetzung, plant Tasks und wählt die Tools.
3.  **Aider (Worker - Speed):** Der "schnelle Handwerker" für präzise, kleine Änderungen (< 1 Minute).
4.  **OpenHands (Worker - Deep):** Der "Ingenieur" für komplexe Refactorings und Exploration.
5.  **SelfAI (The Product):** Das Ergebnis, das selbst wieder zum Agenten wird.

### Erfolgreiche Methoden
*   **"One Task, One File":** Eine harte Lektion aus Aider-Timeouts. Komplexe Tasks werden gnadenlos atomarisiert.
*   **Wissenschaftliches Prompting:** Prompts werden nicht geraten, sondern designed ("Role, Task, Context, Output, Constraints").
*   **Feedback-Driven:** Jedes Problem (z.B. Aider Timeouts) wurde analysiert, dokumentiert (`LESSONS_LEARNED.md`) und führte zu einer Änderung im Workflow.

---

## 3. Tool-Strategie & Evolution

Die Nutzung der Tools hat sich von "Ausprobieren" zu einer präzisen **"Tool-Matrix"** entwickelt (siehe `CODING_TOOLS_COMPARISON.md`).

| Szenario | Tool der Wahl | Warum? |
| :--- | :--- | :--- |
| **Quick Fix / Typo** | **Aider** | Unschlagbar schnell (~30s), günstig. |
| **Refactoring** | **OpenHands** | Kann Codebase verstehen und navigieren. |
| **Code Generation** | **SelfAI (Native)** | Nutzt MiniMax direkt (höhere Limits, günstiger). |
| **Architektur** | **Gemini/Claude** | Strategische Beratung (wie in diesem Chat). |

**Interessanter Shift:** Die Abkehr von `litellm` hin zu direkten API-Calls für MiniMax, um Rate-Limits zu umgehen und Kosten zu sparen.

---

## 4. Die Evolution: Von Hardware zu Intelligence

Die Geschichte des Projekts (`Die_Komplette_Geschichte_von_SELFAI.md`) ist eine Chronik von 4 Phasen:

1.  **Der NPU-Traum:** Fokus auf Hardware (Snapdragon X Elite). Scheiterte an Tooling-Chaos.
2.  **Die hybride Realität:** Akzeptanz von CPU-Fallbacks. Das System wurde stabil.
3.  **Der planende Agent:** Einführung von Ollama & DPPM (Decompose, Plan, Parallel, Merge). Das System wurde proaktiv.
4.  **Der Super-Agent:** Integration von Tools und `/selfimprove`. Das System wurde autonom.

**Shift im Vibe:**
Anfangs war es ein *technisches* Problem ("Wie kompiliere ich llama-cpp?").
Heute ist es ein *kognitives* Problem ("Wie mache ich das System self-aware?").

---

## 5. Dokumentations-Qualität

Die Dokumentation ist **exzellent** und weit über dem Durchschnitt von Hobby-Projekten.

*   **Lebendes Gedächtnis:** Dateien wie `LESSONS_LEARNED.md` und die `Learings_aus_Problemen/` Ordner zeigen, dass Wissen aktiv konserviert wird.
*   **Architektur-Klarheit:** `CLAUDE.md` ist ein perfektes Beispiel für technische Dokumentation (High-Level bis Low-Level).
*   **Guides:** Es gibt Guides für alles (`UI_GUIDE`, `PROMPT_ENGINEERING_GUIDE`), was das Onboarding (auch für AI-Agenten!) extrem erleichtert.

**Besonderheit:** Die Doku scheint oft *für die AI* geschrieben zu sein, damit diese den Kontext schnell laden kann.

---

## 6. Fazit & Ausblick

**Status:**
SelfAI ist ein **erwachsenes Projekt**. Es hat die "Pubertät" (Instabilität, Identitätskrisen) hinter sich und ist jetzt ein funktionierendes, komplexes System.

**Vibe-Bewertung:** ⭐⭐⭐⭐⭐
Der User hat verstanden, dass "Vibe Coding" nicht bedeutet, blind Code generieren zu lassen, sondern **Systeme zu bauen, die Code generieren**. Die Trennung von Planung, Ausführung und Reflexion (DPPM) ist der Schlüssel.

**Das letzte Puzzleteil:**
Die aktuelle Diskussion um **"Self-Awareness"** und **"Embodiment"** (Introspection Tools) ist der logische nächste Schritt. Der Geist (LLM) muss seinen Körper (Code) kennenlernen, um wirklich autonom zu werden.
