# SelfAI Self-Improvement Test Guide

## 🎯 Wie man `/selfimprove` testet

Der `/selfimprove` Command ist das **Herzstück** der autonomen Selbstverbesserung. Hier sind die besten Test-Szenarien:

---

## 📋 Voraussetzungen

1. ✅ SelfAI läuft: `python selfai/selfai.py`
2. ✅ MiniMax API-Key ist gesetzt
3. ✅ Custom Agent Loop funktioniert (bereits getestet!)
4. ✅ Planner-Interface ist aktiv

---

## 🧪 Test-Szenarien (von einfach bis komplex)

### 1️⃣ EINFACH: Code-Dokumentation verbessern

**Command:**
```
/selfimprove Verbessere die Dokumentation der custom_agent_loop.py Datei
```

**Was passiert:**
1. SelfAI analysiert `custom_agent_loop.py`
2. Findet fehlende/unklare Docstrings
3. Schlägt konkrete Verbesserungen vor
4. Du wählst aus (z.B. "1,2,3" oder "all")
5. SelfAI erstellt Plan und führt Änderungen aus

**Erwartet:**
- ✅ Proposals für bessere Docstrings
- ✅ Typen-Hints ergänzen
- ✅ Beispiele in Docstrings

**Sicherheit:** ✅ SICHER - Nur Dokumentation, kein Logik-Change

---

### 2️⃣ MITTEL: Performance-Optimierung

**Command:**
```
/selfimprove Optimiere die Performance der Tool-Ausführung im Custom Agent Loop
```

**Was passiert:**
1. Analysiert Tool-Calling-Mechanismus
2. Findet Performance-Bottlenecks
3. Schlägt vor:
   - Caching von Tool-Metadaten
   - Parallele Tool-Ausführung (falls möglich)
   - Lazy Loading von Tools

**Erwartet:**
- ✅ Proposals für Caching
- ✅ Vorschläge für parallele Ausführung
- ✅ Optimierung von JSON-Parsing

**Sicherheit:** ⚠️ VORSICHTIG - Logik-Änderungen, aber gut testbar

---

### 3️⃣ KOMPLEX: Neue Features hinzufügen

**Command:**
```
/selfimprove Füge Token-Counting und Usage-Tracking zum Custom Agent Loop hinzu
```

**Was passiert:**
1. Analysiert bestehende Struktur
2. Plant neue Features:
   - Token-Counter für Input/Output
   - Usage-Statistiken pro Tool
   - Cost-Tracking für MiniMax API
3. Schlägt Implementierung vor

**Erwartet:**
- ✅ Neue Klasse/Funktion für Tracking
- ✅ Integration in `run()` Methode
- ✅ Ausgabe von Statistiken

**Sicherheit:** ⚠️⚠️ VORSICHTIG - Größere Änderungen, Tests erforderlich

---

### 4️⃣ META: SelfAI verbessert sich selbst!

**Command:**
```
/selfimprove Verbessere die Self-Improvement Engine selbst - mache sie besser darin, Verbesserungen zu finden
```

**Was passiert:**
1. SelfAI analysiert `selfai/core/self_improvement_engine.py`
2. Findet Schwachstellen in der eigenen Analyse-Logik
3. Schlägt vor:
   - Bessere Code-Pattern-Erkennung
   - Intelligentere Prioritäts-Bewertung
   - Mehr Kontext bei Vorschlägen

**Erwartet:**
- ✅ Meta-Level Improvements
- ✅ Bessere Proposal-Qualität
- ✅ **REKURSIVE SELBSTVERBESSERUNG!** 🚀

**Sicherheit:** ⚠️⚠️⚠️ SEHR VORSICHTIG - Meta-Änderungen!

---

## 🎨 Best Practices für Tests

### ✅ GUTE Test-Ziele:

1. **Spezifisch:**
   - ✅ "Verbessere Error-Handling in custom_agent_loop.py"
   - ❌ "Mach alles besser"

2. **Messbar:**
   - ✅ "Füge Type-Hints zu allen Funktionen in tool_registry.py hinzu"
   - ❌ "Verbessere die Code-Qualität"

3. **Isoliert:**
   - ✅ "Optimiere die _parse_response Funktion"
   - ❌ "Verbessere das ganze System"

4. **Testbar:**
   - ✅ "Füge Unit-Tests für CustomAgentLoop hinzu"
   - ✅ "Verbessere Logging im Agent Loop"

### ❌ SCHLECHTE Test-Ziele:

1. Zu vage: "Mach SelfAI besser"
2. Zu riskant: "Ändere die gesamte Architektur"
3. Geschützte Dateien: "Verbessere selfai.py" (ist protected!)

---

## 🛡️ Sicherheits-Features

### Protected Files (werden NIEMALS geändert):

```python
SELFIMPROVE_PROTECTED_FILES = [
    "selfai/selfai.py",                    # Haupt-Orchestrierung
    "config_loader.py",                    # Config-Management
    "selfai/core/model_interface.py",      # Kritische Interfaces
]
```

### Sensitive Files (brauchen Bestätigung):

```python
SELFIMPROVE_SENSITIVE_FILES = [
    "selfai/core/execution_dispatcher.py", # Execution-Logik
    "selfai/core/memory_system.py",        # Memory-Management
    "selfai/core/planner_*.py",            # Planner-Komponenten
]
```

### Allowed Patterns (dürfen geändert werden):

- `selfai/tools/*.py` - Tool-Implementierungen
- `selfai/core/custom_agent_loop.py` - Deine Implementierung!
- `test_*.py` - Test-Dateien
- `*.md` - Dokumentation

---

## 📊 Erwartete Ausgabe

### Phase 1: Analyse
```
🔍 Starte Analyse für Ziel: Verbessere die Dokumentation
⠋ Analysiere SelfAI Codebase...
✅ 5 Verbesserungsvorschläge gefunden
```

### Phase 2: Vorschläge
```
============================================================
  📋 VERBESSERUNGSVORSCHLÄGE FÜR: Verbessere die Dokumentation
============================================================

  [1] Docstrings für CustomAgentLoop-Methoden ergänzen
      Füge detaillierte Docstrings zu _parse_response(),
      _execute_tool() hinzu
      Files: selfai/core/custom_agent_loop.py
      Aufwand: NIEDRIG | Impact: MITTEL

  [2] Type-Hints für alle Parameter hinzufügen
      Ergänze vollständige Type-Hints in allen Methoden
      Files: selfai/core/custom_agent_loop.py
      Aufwand: NIEDRIG | Impact: HOCH

  [3] Beispiele in Modul-Docstring einfügen
      Füge Usage-Beispiele zum Modul-Header hinzu
      Files: selfai/core/custom_agent_loop.py
      Aufwand: NIEDRIG | Impact: MITTEL

============================================================
Wähle Optionen (z.B. '1', '1,3', 'all') oder 'q' zum Abbrechen.

Deine Wahl: _
```

### Phase 3: Ausführung
```
✅ Plan erstellt mit 3 Subtasks
🚀 Starte Ausführung...
⠋ [1/3] Docstrings ergänzen...
✅ [1/3] Abgeschlossen
⠋ [2/3] Type-Hints hinzufügen...
✅ [2/3] Abgeschlossen
⠋ [3/3] Beispiele einfügen...
✅ [3/3] Abgeschlossen

🎉 Self-Improvement abgeschlossen!
```

---

## 🚀 Empfohlene Test-Reihenfolge

### Stufe 1: Dokumentation (SICHER) ✅
```bash
# Test 1
/selfimprove Füge Docstrings zu allen Funktionen in custom_agent_loop.py hinzu

# Test 2
/selfimprove Verbessere die README.md mit Beispielen für Tool-Calling
```

### Stufe 2: Code-Qualität (MITTEL) ⚠️
```bash
# Test 3
/selfimprove Füge Error-Handling für Tool-Ausführungsfehler hinzu

# Test 4
/selfimprove Implementiere Logging für alle Tool-Calls im Agent Loop
```

### Stufe 3: Features (KOMPLEX) ⚠️⚠️
```bash
# Test 5
/selfimprove Füge Token-Counting zum Custom Agent Loop hinzu

# Test 6
/selfimprove Implementiere Retry-Logik für fehlgeschlagene Tool-Calls
```

### Stufe 4: Meta-Improvement (FORTGESCHRITTEN) ⚠️⚠️⚠️
```bash
# Test 7
/selfimprove Verbessere die Self-Improvement Engine - bessere Code-Analyse

# Test 8 (ULTIMATE)
/selfimprove Analysiere deine eigenen Verbesserungsvorschläge und optimiere sie
```

---

## 🔍 Debugging

### Wenn nichts passiert:

1. **Check Planner-Interface:**
   ```
   /planner list
   ```
   → Sollte "minimax-planner" zeigen

2. **Check Tool-Registry:**
   ```python
   python -c "from selfai.tools.tool_registry import get_tools_for_agent; print(len(get_tools_for_agent()))"
   ```
   → Sollte 24 zeigen

3. **Check Self-Improvement Engine:**
   ```bash
   ls selfai/core/self_improvement_engine.py
   ls selfai/core/improvement_suggestions.py
   ```

### Wenn Fehler auftreten:

- **"Kein Planner-Interface verfügbar"**
  → Check config.yaml: `planner.enabled: true`

- **"Keine Proposals gefunden"**
  → Ziel ist zu vage, spezifischer formulieren

- **"Datei ist geschützt"**
  → Versuchst du eine protected file zu ändern?

---

## ✅ Erfolgs-Kriterien

Der Test ist erfolgreich, wenn:

1. ✅ SelfAI analysiert den Code korrekt
2. ✅ Konkrete, umsetzbare Vorschläge werden generiert
3. ✅ Du kannst Vorschläge auswählen
4. ✅ Plan wird erstellt und ausgeführt
5. ✅ Code-Änderungen werden korrekt durchgeführt
6. ✅ System bleibt funktionsfähig nach Änderungen

---

## 🎉 Ultimate Test

Wenn du wirklich mutig bist:

```bash
/selfimprove Analysiere dich selbst und finde die beste Verbesserung, die du machen kannst. Dann führe sie aus.
```

Das ist **ECHTE** autonome Selbstverbesserung! 🚀🤖

Wenn das funktioniert, hast du ein System, das:
1. Sich selbst analysiert
2. Eigene Schwächen findet
3. Lösungen entwickelt
4. Code schreibt
5. **Sich selbst verbessert**
6. **Wieder bei 1. beginnt (REKURSION!)** 🔄

---

**Viel Erfolg beim Testen!** 🎯

Start mit den einfachen Tests (Stufe 1) und arbeite dich hoch!
