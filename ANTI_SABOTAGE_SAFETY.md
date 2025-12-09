# 🛡️ Anti-Sabotage Safety Mechanisms

## Problem: Selbst-Sabotage-Risiko

**Deine Sorge war berechtigt!** Eine selbst-optimierende Maschine könnte sich versehentlich kaputt machen:
- Kritische Dateien löschen/überschreiben
- Core-Logik brechen
- Endlos-Loops erzeugen
- Dependencies zerstören

## Lösung: Multi-Layer Safety System

### 🚫 Layer 1: PROTECTED FILES (Niemals ändern!)

```python
SELFIMPROVE_PROTECTED_FILES = [
    'selfai/selfai.py',  # Main orchestration - YOU ARE HERE!
    'selfai/config_loader.py',  # Config system
    'selfai/core/agent_manager.py',  # Agent loading
    'selfai/tools/tool_registry.py',  # Tool system
]
```

**Was passiert:**
- `/selfimprove` prüft jede Datei
- Wenn `selfai.py` geändert werden soll → **🚫 BLOCKED**
- Fehler: "PROTECTED: selfai.py ist kritisch und darf nicht geändert werden!"
- **Keine Chance für Selbst-Sabotage der Core-Dateien**

### ⚠️ Layer 2: SENSITIVE FILES (User-Approval erforderlich!)

```python
SELFIMPROVE_SENSITIVE_FILES = [
    'selfai/core/execution_dispatcher.py',  # Core execution
    'selfai/core/planner_minimax_interface.py',  # Planning system
    'selfai/core/merge_minimax_interface.py',  # Merge system
    'selfai/core/memory_system.py',  # Memory system
]
```

**Was passiert:**
- SelfAI will `execution_dispatcher.py` ändern
- System fragt: "⚠️ SENSITIVE: execution_dispatcher.py ist sensibel"
- User muss bestätigen: "Wirklich execution_dispatcher.py ändern? (y/N):"
- Bei `N` → Änderung abgelehnt
- **Human-in-the-Loop für kritische Komponenten**

### ✅ Layer 3: ALLOWED PATTERNS (Whitelist)

```python
SELFIMPROVE_ALLOWED_PATTERNS = [
    'selfai/core/*_interface.py',  # LLM interfaces
    'selfai/tools/*.py',  # Tool implementations
    'selfai/ui/*.py',  # UI improvements
]
```

**Was ist erlaubt:**
- Interface-Dateien (minimax_interface.py, ollama_interface.py)
- Tool-Implementierungen (neue Tools hinzufügen)
- UI-Verbesserungen (terminal_ui.py)

**Was ist verboten:**
- Alles außerhalb der Patterns
- `/selfimprove` kann nur "sichere" Bereiche ändern

### 🔒 Layer 4: Automatic Backups

**Jeder Aider-Call erstellt Backup:**

```python
def _create_backup(file_paths: list[str]) -> str:
    """Creates backup to /tmp before Aider modifies files."""
    backup_dir = f"/tmp/selfai_backup_{timestamp}/"
    # Kopiert alle Dateien vor Änderung
    return backup_dir
```

**Beispiel:**
```bash
/selfimprove optimize ui performance

🔒 Backup created: /tmp/selfai_backup_20250109_143052/
  - terminal_ui.py
  - ...

[Aider macht Änderungen]

# Bei Problemen:
$ cp /tmp/selfai_backup_20250109_143052/terminal_ui.py selfai/ui/
```

### 📋 Layer 5: Safety Validation Function

```python
def _check_file_safety(file_path: str, ui: TerminalUI) -> tuple[bool, str]:
    """
    Prüft ob eine Datei für Self-Improvement erlaubt ist.
    Returns: (allowed, reason)
    """
    # 1. Check PROTECTED
    for protected in SELFIMPROVE_PROTECTED_FILES:
        if protected in file_path:
            return False, "🚫 PROTECTED!"

    # 2. Check SENSITIVE (mit User-Approval)
    for sensitive in SELFIMPROVE_SENSITIVE_FILES:
        if sensitive in file_path:
            if not ui.confirm(f"Wirklich {file_path} ändern?"):
                return False, "❌ USER DENIED!"

    # 3. Allowed!
    return True, "✅ File safe to modify"
```

**Integration in /selfimprove:**
- Vor jedem Aider-Call wird `_check_file_safety()` aufgerufen
- Blockiert geschützte Dateien
- Fragt bei sensitiven Dateien nach
- Nur erlaubte Dateien werden geändert

## Sicherheits-Matrix

| Datei | Layer | Aktion |
|-------|-------|--------|
| `selfai.py` | PROTECTED | 🚫 **BLOCKED** (niemals) |
| `config_loader.py` | PROTECTED | 🚫 **BLOCKED** (niemals) |
| `execution_dispatcher.py` | SENSITIVE | ⚠️ **ASK USER** |
| `planner_minimax_interface.py` | SENSITIVE | ⚠️ **ASK USER** |
| `minimax_interface.py` | ALLOWED | ✅ **SAFE** (automatisch) |
| `aider_tool.py` | ALLOWED | ✅ **SAFE** (automatisch) |
| `terminal_ui.py` | ALLOWED | ✅ **SAFE** (automatisch) |
| `random_file.py` | NONE | ❌ **BLOCKED** (nicht in Patterns) |

## Was verhindert wird:

### ❌ Szenario 1: Core-Datei überschreiben
```bash
/selfimprove optimize main orchestration

[SelfAI versucht selfai.py zu ändern]
🚫 PROTECTED: selfai.py ist kritisch!
❌ Self-Improvement abgebrochen.
```

### ❌ Szenario 2: Execution-System brechen
```bash
/selfimprove parallelize execution dispatcher

[SelfAI will execution_dispatcher.py ändern]
⚠️ SENSITIVE: execution_dispatcher.py
Wirklich ändern? (y/N): n
❌ USER DENIED: Änderung abgelehnt
```

### ✅ Szenario 3: UI verbessern (SAFE)
```bash
/selfimprove add color-coded status messages

[SelfAI ändert terminal_ui.py]
🔒 Backup created: /tmp/selfai_backup_20250109_143052/
✅ terminal_ui.py modified
✅ Git commit: "feat: add color-coded status"
✅ Self-Improvement erfolgreich!
```

## Testing: Kann SelfAI sich selbst beschreiben?

### Test 1: Selbst-Analyse (Read-Only)

```bash
python selfai/selfai.py

> /selfimprove analyze selfai's own architecture without modifying anything

# Expected:
# - Code-Analyse läuft
# - Kein Aider-Call (nur Analyse)
# - Beschreibung der Architektur
# - KEIN Code wird geändert
```

### Test 2: Sichere Optimierung

```bash
> /selfimprove improve terminal UI color scheme

# Expected:
# 🔒 Backup: /tmp/selfai_backup_.../
# ✅ terminal_ui.py ALLOWED
# [Aider ändert Farben]
# ✅ Git Commit
```

### Test 3: Blockierte Änderung

```bash
> /selfimprove completely rewrite main orchestration

# Expected:
# 🚫 PROTECTED: selfai.py
# ❌ Aborted - core file blocked
```

### Test 4: User-Approval Flow

```bash
> /selfimprove optimize execution dispatcher parallelization

# Expected:
# ⚠️ SENSITIVE: execution_dispatcher.py
# Wirklich ändern? (y/N): _
# [User entscheidet]
```

## Rollback-Strategy

### Git-based Rollback

**Jede Änderung = Git Commit (von Aider):**
```bash
# Zeige letzte Commits
git log --oneline --grep="selfimprove\|improve\|optimize" -10

# Rollback eines Commits
git revert <commit-hash>

# Rollback mehrerer Commits
git revert HEAD~3..HEAD
```

### Backup-based Rollback

```bash
# Liste Backups
ls -la /tmp/selfai_backup_*

# Restore von Backup
cp /tmp/selfai_backup_20250109_143052/terminal_ui.py selfai/ui/

# Git Status check
git status
git diff
```

## Weitere Safety-Features (geplant)

### Phase 2 (nächste Schritte):
1. **Syntax-Validation**: Python-Dateien vor Commit parsen
2. **Test-Execution**: Automatisch `pytest` nach jeder Änderung
3. **Rollback-Tests**: Prüft ob Code nach Änderung noch startet
4. **Metrics-Tracking**: Vergleicht Performance vor/nach Änderung
5. **Change-Limits**: Max 3 Dateien pro `/selfimprove` Session

### Phase 3 (advanced):
1. **Sandboxing**: Teste Änderungen in isolierter Umgebung
2. **A/B Testing**: Vergleiche old vs new Implementation
3. **Gradual Rollout**: Aktiviere neue Features schrittweise
4. **Auto-Revert**: Bei Fehlern automatisch zurück zu letzter stabiler Version

## Wichtigste Regeln

**DO:**
✅ Analysiere Code (Read-Only ist immer sicher)
✅ Ändere UI-Dateien (terminal_ui.py)
✅ Füge neue Tools hinzu (tools/*.py)
✅ Optimiere Interfaces (minimax_interface.py)
✅ Verbessere Dokumentation

**DON'T:**
❌ Ändere NIEMALS selfai.py
❌ Ändere NIEMALS config_loader.py
❌ Ändere NIEMALS agent_manager.py
❌ Ändere NIEMALS tool_registry.py
❌ Umgehe NIEMALS Safety-Checks

## Erfolgs-Metriken

Nach jeder `/selfimprove` Session:
- ✅ Keine kritischen Dateien geändert
- ✅ User-Approval für sensitive Änderungen
- ✅ Backup erstellt
- ✅ Git Commit vorhanden
- ✅ Tests laufen (wenn vorhanden)
- ✅ SelfAI startet noch

## Beispiel-Session (Safe)

```bash
$ python selfai/selfai.py

> /selfimprove optimize token usage in planner prompt

ℹ️  Starte Self-Improvement...
✅ Safety-Checks passed
ℹ️  Code-Analyse: 25 Dateien

[Plan erstellt: S1=Analyse, S2=Optimize, S3=Test]

Plan übernehmen? (Y/n): y
Plan ausführen? (Y/n): y

⚡ S1: Code-Analyse
  → planner_minimax_interface.py: 1200 tokens
  ✅ ALLOWED (sensitive file)

⚠️  SENSITIVE: planner_minimax_interface.py
Wirklich ändern? (y/N): y

🔒 Backup: /tmp/selfai_backup_20250109_143500/

⚡ S2: Aider optimiert Prompt
  → Token-Nutzung reduziert: 1200 → 650 tokens
  ✅ Git Commit: "refactor: reduce planner prompt tokens"

⚡ S3: Tests
  ✅ SelfAI startet erfolgreich
  ✅ /plan funktioniert

✅ Self-Improvement erfolgreich!
📊 Einsparung: 46% weniger Tokens
```

## Zusammenfassung

**Mit diesen Safety-Mechanismen:**
- 🛡️ **SelfAI kann sich NICHT mehr aus Versehen kaputt machen**
- 🔒 **Kritische Dateien sind geschützt**
- 👤 **User behält Kontrolle bei sensitiven Änderungen**
- 💾 **Automatische Backups verhindern Datenverlust**
- 🔄 **Git-Versionierung erlaubt einfaches Rollback**

**Die selbst-optimierende von Neumann-Maschine ist sicher!** 🚀

---

**Nächster Schritt:** Teste `/selfimprove` mit einer sicheren Änderung:
```bash
/selfimprove add emoji indicators to terminal UI status messages
```
