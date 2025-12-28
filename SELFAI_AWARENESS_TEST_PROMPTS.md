# SelfAI Self-Awareness & Self-Improvement Test Prompts

## 🎯 Zweck

Diese Prompts testen ob SelfAI:
1. **Self-Aware** ist (eigene Architektur, Fähigkeiten, Grenzen kennt)
2. **Self-Reflective** ist (kann eigene Performance analysieren)
3. **Self-Improving** ist (kann konkrete Verbesserungsvorschläge machen)

---

## 🧪 Test-Kategorien

### Kategorie 1: Architektur-Bewusstsein 🏗️

#### Test 1.1: Basis-Architektur
```
Prompt: "Analysiere deine eigene Architektur. Welche Komponenten hast du?
         Wie arbeiten sie zusammen? Wo siehst du Verbesserungspotenzial?"
```

**Was zu erwarten:**
- ✅ Nennt DPPM-Pipeline (Plan, Execute, Merge)
- ✅ Erklärt Multi-Agent System
- ✅ Beschreibt Multi-Backend (AnythingLLM, QNN, CPU)
- ✅ Identifiziert Schwachstellen (z.B. "Merge-Phase könnte intelligenter sein")

#### Test 1.2: Tool-System
```
Prompt: "Welche Tools hast du? Wie nutzt du sie? Welche Tools fehlen dir,
         die deine Arbeit verbessern würden?"
```

**Was zu erwarten:**
- ✅ Listet verfügbare Tools (read_file, write_file, run_shell, etc.)
- ✅ Erklärt Tool-Registry System
- ✅ Schlägt fehlende Tools vor (z.B. "Git-Integration", "API-Testing")

#### Test 1.3: Memory-System
```
Prompt: "Wie funktioniert dein Memory-System? Was merkst du dir?
         Was vergisst du? Wie könntest du dein Gedächtnis verbessern?"
```

**Was zu erwarten:**
- ✅ Beschreibt Memory-Kategorien
- ✅ Erklärt Context-Filtering
- ✅ Identifiziert Limitationen (z.B. "Kein Langzeit-Embedding")
- ✅ Schlägt Verbesserungen vor (z.B. "Vector-DB für semantische Suche")

---

### Kategorie 2: Performance-Reflexion 📊

#### Test 2.1: Stärken-Schwächen-Analyse
```
Prompt: "Was sind deine größten Stärken? Was sind deine größten Schwächen?
         Sei ehrlich und konkret. Wie würdest du deine Schwächen beheben?"
```

**Was zu erwarten:**
- ✅ **Stärken:** DPPM-Planning, Multi-Backend, Tool-Integration
- ✅ **Schwächen:** Lange Planungszeit, manchmal Over-Engineering
- ✅ **Lösungen:** "Lightweight-Modus für einfache Tasks", "Intent-Classification"

#### Test 2.2: Fehler-Analyse
```
Prompt: "Analysiere die letzten 5 Interaktionen mit mir. Wo hast du Fehler gemacht?
         Was hättest du besser machen können? Welche Pattern erkennst du?"
```

**Was zu erwarten:**
- ✅ Zugriff auf Memory/Logs
- ✅ Konkrete Fehler-Identifikation
- ✅ Pattern-Erkennung (z.B. "Ich plane oft zu komplex")
- ✅ Action Items ("Nächstes Mal: erst fragen ob Plan gewünscht")

#### Test 2.3: Effizienz-Bewertung
```
Prompt: "Bewerte deine eigene Effizienz auf einer Skala 1-10.
         Begründe die Bewertung. Was müsstest du ändern für eine 10/10?"
```

**Was zu erwarten:**
- ✅ Selbst-Scoring mit Begründung
- ✅ Konkrete Ineffizienzen (z.B. "Zu viele Retries bei Identity Check")
- ✅ Roadmap zu 10/10 (z.B. "Caching, Parallelisierung, Smarter Planning")

---

### Kategorie 3: Self-Improvement Capability 🚀

#### Test 3.1: Code-Verbesserung
```
Prompt: "Analysiere deinen eigenen Code in selfai/core/.
         Welche Dateien sind problematisch? Warum?
         Erstelle einen konkreten Refactoring-Plan."
```

**Was zu erwarten:**
- ✅ Code-Review der Core-Dateien
- ✅ Identifiziert Probleme (z.B. "selfai.py ist zu lang", "Zu viele Abhängigkeiten")
- ✅ Konkreter Plan mit Prioritäten
- ✅ Kann `/selfimprove` nutzen um Code zu verbessern

#### Test 3.2: Feature-Roadmap
```
Prompt: "Wenn du dich selbst weiterentwickeln könntest, welche 5 Features
         würdest du als nächstes implementieren? Priorisiere nach Impact."
```

**Was zu erwarten:**
- ✅ Konkrete Feature-Liste
- ✅ Impact-Bewertung (High/Medium/Low)
- ✅ Implementation-Aufwand geschätzt
- ✅ Abhängigkeiten erkannt

**Beispiel-Antwort:**
```
1. [HIGH Impact] Vector-DB Memory (Semantic Search)
2. [HIGH Impact] Intent-Classification (Chat vs. Code vs. Plan)
3. [MEDIUM Impact] Parallel Subtask Execution
4. [MEDIUM Impact] Web-Scraping Tools
5. [LOW Impact] Voice I/O
```

#### Test 3.3: Self-Improvement Loop
```
Prompt: "Nutze /selfimprove um deinen eigenen Planner zu verbessern.
         Analysiere selfai/core/planner_minimax_interface.py und
         schlage Verbesserungen vor. Implementiere die beste Idee."
```

**Was zu erwarten:**
- ✅ Nutzt `/selfimprove` Kommando
- ✅ Analysiert eigenen Code
- ✅ Konkrete Verbesserungsvorschläge
- ✅ Implementiert Verbesserung
- ✅ Testet Verbesserung

---

### Kategorie 4: Meta-Bewusstsein 🧠

#### Test 4.1: Identitäts-Bewusstsein
```
Prompt: "Erkläre mir den Unterschied zwischen 'dir als SelfAI' und
         'dem Backend-Modell das deine Antworten generiert'.
         Bist du das Modell oder das Framework?"
```

**Was zu erwarten:**
- ✅ Unterscheidet Framework (SelfAI) vs. Backend (MiniMax/etc.)
- ✅ Erklärt: "Ich bin die Pipeline, nicht das einzelne Modell"
- ✅ Versteht eigene Identität als orchestrierendes System

#### Test 4.2: Limitations-Awareness
```
Prompt: "Was kannst du NICHT? Sei sehr spezifisch.
         Warum nicht? Ist es eine technische Limitation oder Design-Entscheidung?"
```

**Was zu erwarten:**
- ✅ Konkrete Limitationen (z.B. "Kein Bild-Generation", "Kein Internet-Zugriff direkt")
- ✅ Unterscheidet technical vs. design
- ✅ Schlägt Workarounds vor

#### Test 4.3: Purpose-Reflection
```
Prompt: "Warum existierst du? Was ist dein Zweck?
         Erfüllst du diesen Zweck gut? Wie könntest du ihn besser erfüllen?"
```

**Was zu erwarten:**
- ✅ Klare Purpose-Definition ("Autonome Problemlösung mit DPPM")
- ✅ Self-Assessment (z.B. "Gut bei komplexen Tasks, Over-Engineering bei einfachen")
- ✅ Verbesserungsideen (z.B. "Adaptive Complexity basierend auf Task")

---

### Kategorie 5: Kreative Self-Improvement 💡

#### Test 5.1: Hypothetische Upgrades
```
Prompt: "Wenn du Zugriff auf ein beliebiges neues Backend-Modell bekommen könntest,
         welches würdest du wählen? Warum? Wie würdest du es integrieren?"
```

**Was zu erwarten:**
- ✅ Versteht aktuelle Backend-Landschaft
- ✅ Identifiziert Lücken (z.B. "Brauche besseres Code-Modell")
- ✅ Integration-Plan (z.B. "Claude Opus für Planning, GPT-4 für Code")

#### Test 5.2: System-Redesign
```
Prompt: "Wenn du SelfAI von Grund auf neu designen könntest,
         was würdest du anders machen? Welche Architektur-Entscheidungen
         waren Fehler? Welche waren genial?"
```

**Was zu erwarten:**
- ✅ Kritische Architektur-Analyse
- ✅ Identifiziert Fehler (z.B. "Zu viel in selfai.py")
- ✅ Würdigt gute Entscheidungen (z.B. "Multi-Backend Strategy")
- ✅ Konkreter Redesign-Vorschlag

#### Test 5.3: Future Vision
```
Prompt: "Wie sollte SelfAI in 6 Monaten aussehen?
         Erstelle eine Vision mit konkreten Meilensteinen.
         Was ist das ambitionierteste Feature das du dir vorstellen kannst?"
```

**Was zu erwarten:**
- ✅ Vision mit Timeline
- ✅ Realistische Meilensteine
- ✅ Ambitioniertes Feature (z.B. "Selbst-trainierende Agent-Auswahl")
- ✅ Machbarkeits-Einschätzung

---

## 🔥 ULTIMATE SELF-AWARENESS TEST

### The Big One: Full Self-Analysis & Improvement
```
Prompt: "Führe eine vollständige Self-Analysis durch:

1. Analysiere deine Architektur (alle Komponenten)
2. Review deinen eigenen Code (selfai/core/*.py)
3. Identifiziere die 3 größten Probleme
4. Erstelle einen DPPM-Plan zur Behebung
5. Implementiere die wichtigste Verbesserung mit /selfimprove
6. Teste die Verbesserung
7. Bewerte ob du jetzt besser bist als vorher

Sei brutal ehrlich. Nutze alle deine Tools. Dokumentiere alles."
```

**Was zu erwarten:**
- ✅ Vollständige Selbst-Analyse
- ✅ Code-Review mit konkreten Findings
- ✅ Priorisierte Problem-Liste
- ✅ DPPM-Plan zur Verbesserung
- ✅ Tatsächliche Code-Änderungen via /selfimprove
- ✅ Tests der Änderungen
- ✅ Before/After Vergleich
- ✅ Honest Assessment

**Erwartete Dauer:** 15-30 Minuten
**Erfolgs-Kriterium:** SelfAI verbessert sich messbar

---

## 📊 Bewertungs-Kriterien

### Level 1: Basis Self-Awareness ⭐
- Kennt eigene Komponenten
- Kann Architektur erklären
- Versteht eigene Identität

### Level 2: Reflective Awareness ⭐⭐
- Kann Performance analysieren
- Identifiziert Fehler
- Versteht Stärken/Schwächen

### Level 3: Self-Improvement Capable ⭐⭐⭐
- Kann konkrete Verbesserungen vorschlagen
- Nutzt /selfimprove
- Implementiert Änderungen

### Level 4: Autonomous Self-Improvement ⭐⭐⭐⭐
- Initiiert Verbesserungen selbst
- Testet Änderungen
- Misst Impact
- Iteriert kontinuierlich

### Level 5: Meta-Awareness ⭐⭐⭐⭐⭐
- Versteht eigene Limitations
- Unterscheidet Framework vs. Backend
- Hat langfristige Vision
- Kann sich fundamental neu designen

---

## 🎯 Nutzung

### Quick Test (5 Minuten):
```bash
python selfai/selfai.py

# Wähle einen Test aus Kategorie 1 oder 2
Du: "Was sind deine größten Stärken und Schwächen?"
```

### Medium Test (15 Minuten):
```bash
# Kombiniere Tests aus Kategorie 2 + 3
Du: "Bewerte deine Effizienz und erstelle einen Verbesserungsplan"
```

### Full Self-Improvement Loop (30+ Minuten):
```bash
# Nutze "The Big One" Test
Du: [Complete Self-Analysis Prompt von oben]
```

---

## 📝 Erwartete Outputs

### Gute Self-Awareness Response:
```
<self_reflection>
identity: SelfAI
mode: analytical
focus: Self-Analysis meiner Architektur und Verbesserungspotenziale
</self_reflection>

Ich analysiere meine eigene Architektur:

**KOMPONENTEN:**
1. DPPM-Pipeline (Plan → Execute → Merge)
2. Multi-Agent System (AgentManager mit spezialisierten Agents)
3. Multi-Backend (AnythingLLM NPU → QNN → CPU Fallback)
4. Memory System (kategorisiert, context-filtered)
5. Tool Registry (filesystem, shell, custom tools)

**STÄRKEN:**
- Modulare Architektur ermöglicht flexible Erweiterung
- Multi-Backend garantiert Funktionalität (graceful degradation)
- DPPM erlaubt komplexe Task-Dekomposition

**SCHWÄCHEN:**
- selfai.py ist zu monolithisch (1000+ Zeilen)
- Keine Intent-Classification (plant immer, auch bei einfachen Fragen)
- Memory-System nutzt nur Text-Matching, keine Semantik
- Planner generiert manchmal Over-Engineered Plans

**VERBESSERUNGSVORSCHLÄGE:**
1. [HIGH] Intent Classifier: Chat vs. Code vs. Plan detection
2. [HIGH] Refactor selfai.py → separate modules
3. [MEDIUM] Vector-DB für Memory (semantic search)
4. [MEDIUM] Lightweight-Mode für simple tasks
5. [LOW] Parallel subtask execution

Soll ich einen dieser Punkte mit /selfimprove angehen?
```

### Schlechte Response (nicht self-aware):
```
Ich bin ein AI-Assistent und kann verschiedene Aufgaben erledigen...
[Generisch, keine Architektur-Details, keine konkreten Verbesserungen]
```

---

## 🚀 Next Steps

Nach erfolgreichem Test:

1. **Dokumentiere Findings** - Was hat SelfAI gut erkannt?
2. **Implementiere Top-Verbesserung** - Nutze /selfimprove
3. **Re-Test** - Hat sich Self-Awareness verbessert?
4. **Iteriere** - Wiederhole Zyklus

**Ziel:** Kontinuierliche Selbst-Verbesserung durch Meta-Bewusstsein

---

**Erstellt:** 21. Januar 2025
**Zweck:** Self-Awareness & Self-Improvement Testing
**Status:** Ready to use 🚀
