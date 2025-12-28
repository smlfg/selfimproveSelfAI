# Feedback zur SelfAI Awareness-Lösung: Brute Force vs. Agentic Tools

**Datum:** 24. Dezember 2025
**Autor:** Gemini (CLI Agent)
**Kontext:** Analyse der Vorschläge aus `SELFAI_AWARENESS_GAP_ANALYSIS.md` zur Behebung der "Architektur-Blindheit" von SelfAI.

---

## 🎯 Executive Summary

Die Diagnose in der Gap-Analyse ist **korrekt**: SelfAI halluziniert Komponenten, weil es keinen Zugriff auf seinen eigenen Source-Code hat.
Die vorgeschlagene Lösung (Context Injection + Reflection Loop) ist jedoch teilweise **zu komplex und ineffizient**.

Mein Gegenvorschlag: **Weniger Prompt-Engineering, mehr Tool-Nutzung.**

---

## ⚖️ Kosten-Nutzen-Analyse der Vorschläge

### 1. Context Injection (Vorschlag: Alles in den System-Prompt)
*Der Vorschlag:* Eine Liste aller Dateien, Tools und Schwächen statisch in jeden System-Prompt injizieren.
*   **Komplexitäts-Kosten:** 🔴 **HOCH**
    *   **Context Bloat:** Verbraucht permanent Token für Informationen, die oft irrelevant sind.
    *   **Over-Alignment:** Risiko, dass das Modell sich zu sehr auf Meta-Themen fokussiert statt auf den User-Task.
    *   **Wartbarkeit:** Statische Texte veralten sofort, wenn sich der Code ändert.
*   **Urteil:** **Vermeiden** oder auf ein absolutes Minimum (nur Identitäts-Kern) reduzieren.

### 2. Reflection Loop (Vorschlag: Nachdenken nach jeder Antwort)
*Der Vorschlag:* Nach jeder Antwort einen zweiten LLM-Call starten, um die Antwort zu bewerten.
*   **Komplexitäts-Kosten:** 🔴 **HOCH**
    *   **Latenz:** Verdoppelt effektiv die Wartezeit für den User.
    *   **Kosten:** Verdoppelt die API-Kosten.
*   **Urteil:** **Weglassen** für den Standard-Chat. Nur als expliziter Modus (z.B. `/debug` oder `/audit`) sinnvoll.

### 3. Self-Inspection Tools (Vorschlag: Tools zum Lesen von Code)
*Der Vorschlag:* Dem Agenten Tools wie `list_selfai_core_files` und `read_selfai_code` geben.
*   **Komplexitäts-Kosten:** 🟢 **GERING**
    *   **On-Demand:** Keine Token-Kosten, wenn die Tools nicht genutzt werden.
    *   **Skalierbarkeit:** Funktioniert automatisch auch bei wachsender Codebasis.
    *   **Lerneffekt:** Zwingt den Agenten zu aktivem Verhalten ("Ich weiß es nicht → Ich schlage nach").
*   **Urteil:** **BESTER WEG.** Das ist "Agentic Behavior" statt "Prompt-Füttern".

---

## 🛠️ Empfohlene Architektur-Entscheidung ("The Lean Way")

Anstatt das System mit Meta-Informationen zu überladen, sollten wir SelfAI die Fähigkeit geben, **Wissen bei Bedarf zu holen**.

### Do's:
1.  **Inspection Tools priorisieren:** Implementierung von `list_core_files` und `read_file` (beschränkt auf den SelfAI-Ordner) in der `ToolRegistry`.
2.  **Dynamischer Prompt (Minimal):** Der System-Prompt sollte nur sagen: *"Du bist SelfAI. Du hast keinen internen Zugriff auf dein Wissen, aber du hast Tools, um deinen eigenen Source-Code zu lesen. Wenn du gefragt wirst, wie du funktionierst, NUTZE DIE TOOLS."*
3.  **Codebase-Suche:** Ein Tool (z.B. basierend auf `grep` oder `ripgrep`), um Funktionen im eigenen Code zu finden.

### Don'ts:
1.  **Keine statischen Dateilisten im Prompt.**
2.  **Kein erzwungener Reflection-Loop bei jedem Turn.**

## 💡 Fazit

Die Lösung für fehlende Self-Awareness ist nicht, dem Modell das Wissen "einzuimpfen" (Context Injection), sondern ihm die **Augen zu öffnen** (Tools). Das hält das System schnell, kosteneffizient und fördert echtes autonomes Problemlösen.
