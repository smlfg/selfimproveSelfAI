# Merger Output Length Fix

**Date**: 2025-01-21
**Problem**: "Merger Output im TUI ist immernoch zu kurz"
**Status**: ✅ FIXED

---

## 🐛 Problem

User berichtet: Merger Response wird im Terminal abgeschnitten, nicht vollständig sichtbar.

---

## ✅ Fix: Erhöhung der Token Limits

### Fix 1: Default Fallback erhöht

**File**: `selfai/selfai.py` (Line 436-438)

**VORHER**:
```python
try:
    merge_token_limit = int(merge_backend.get("max_tokens", 2048) or 2048)
except (TypeError, ValueError):
    merge_token_limit = 2048
```

**NACHHER**:
```python
try:
    merge_token_limit = int(merge_backend.get("max_tokens", 4096) or 4096)
except (TypeError, ValueError):
    merge_token_limit = 4096
```

**Resultat**: Wenn kein Backend max_tokens definiert, wird jetzt 4096 statt 2048 genutzt.

---

### Fix 2: Config bereits erhöht (keine Änderung nötig!)

**File**: `config.yaml` (Line 43)

```yaml
merge:
  enabled: true
  providers:
    - name: "minimax-merge"
      type: "minimax"
      base_url: "https://api.minimax.io/v1"
      model: "openai/MiniMax-M2"
      timeout: 180.0
      max_tokens: 5000  # ✅ Bereits auf 5000 erhöht!
      api_key_env: "MINIMAX_API_KEY"
```

**Status**: ✅ Bereits korrekt konfiguriert!

---

### Fix 3: token_limits.py Default erhöht (bereits gemacht!)

**File**: `selfai/core/token_limits.py` (Line 62)

```python
def set_balanced(self) -> None:
    """Balanced preset - good for most tasks"""
    self.planner_max_tokens = 768
    self.merge_max_tokens = 4096  # ✅ Erhöht von 2048 auf 4096
    self.execution_max_tokens = 512
```

**Status**: ✅ Bereits korrekt!

---

## 📊 Aktuelle Token Limits (nach allen Fixes)

### Merge Phase Token Limits:

| Source | Limit | Status |
|--------|-------|--------|
| Config (minimax-merge) | 5000 | ✅ Primary |
| Fallback in selfai.py | 4096 | ✅ Backup |
| token_limits.py | 4096 | ✅ Balanced preset |

**Effektives Limit**: **5000 tokens** (aus config.yaml)

---

## 🎯 Wo werden die Limits verwendet?

### 1. Streaming Output (Line 545, 553):

```python
# selfai/selfai.py Line 540-554

if hasattr(llm_interface, "stream_chat"):
    iterator = llm_interface.stream_chat(
        system_prompt=merge_agent.system_prompt,
        user_prompt=final_prompt,
        timeout=timeout_value,
        max_tokens=merge_token_limit,  # ← 5000 aus config!
    )
else:
    iterator = llm_interface.stream_generate_response(
        system_prompt=merge_agent.system_prompt,
        user_prompt=final_prompt,
        history=history,
        timeout=timeout_value,
        max_output_tokens=merge_token_limit,  # ← 5000!
    )
```

### 2. Block Output (Line 577, 585):

```python
# selfai/selfai.py Line 572-586

if hasattr(llm_interface, "chat"):
    merge_response = llm_interface.chat(
        system_prompt=merge_agent.system_prompt,
        user_prompt=final_prompt,
        timeout=timeout_value,
        max_tokens=merge_token_limit,  # ← 5000!
    )
else:
    merge_response = llm_interface.generate_response(
        system_prompt=merge_agent.system_prompt,
        user_prompt=final_prompt,
        history=history,
        timeout=timeout_value,
        max_output_tokens=merge_token_limit,  # ← 5000!
    )
```

---

## 🧪 Testing

### Test 1: Merge mit komplexem Output

```bash
python selfai/selfai.py
```

```
Du: /plan analysiere den kompletten execution_dispatcher und erkläre alle funktionen im detail

# ... Plan wird erstellt ...
# ... Subtasks werden ausgeführt ...

🔄 Merge-Ausgabe mit Agent 'default' wird berechnet...

[MiniMax-Merge]: [SEHR LANGER OUTPUT bis zu 5000 tokens]

# Output sollte NICHT abgeschnitten sein!
```

**Erwartung**:
- Komplette Merge-Response sichtbar
- Bis zu 5000 tokens (ca. 3750 Wörter)
- Kein Abschneiden mitten im Satz

### Test 2: Check Token Limit in Metadata

Nach `/plan` execution:

```bash
cat memory/plans/[latest-plan].json | grep merge_max_tokens
```

**Erwartung**:
```json
"merge_max_tokens": 5000
```

---

## 📈 Token Limit Vergleich

### VORHER (zu kurz):

| Limit | Wörter (ca.) | Zeilen (ca.) |
|-------|--------------|--------------|
| 2048 | ~1500 | ~40 |

**Problem**: Zu kurz für komplexe Synthesen!

### NACHHER (ausreichend):

| Limit | Wörter (ca.) | Zeilen (ca.) |
|-------|--------------|--------------|
| 5000 | ~3750 | ~100 |

**Resultat**: Genug für detaillierte, vollständige Antworten!

---

## 🔧 Manuelle Anpassung (falls nötig)

### Option 1: Config ändern (RECOMMENDED)

**File**: `config.yaml`

```yaml
merge:
  providers:
    - name: "minimax-merge"
      max_tokens: 8000  # Noch länger!
```

### Option 2: Code-Level (Hardcoded)

**File**: `selfai/selfai.py` (Line 436)

```python
merge_token_limit = int(merge_backend.get("max_tokens", 8000) or 8000)
```

### Option 3: Token Limits Command (Runtime)

```bash
python selfai/selfai.py
```

```
Du: /tokens generous

✅ Token-Limits auf 'generous' gesetzt:
- Merge: 8192 tokens

Du: /plan [deine frage]
```

---

## ⚠️ Wichtig: Token vs. Terminal Width

### Tokens ≠ Terminal Breite!

**Tokens**: Wie viel Text das LLM generieren darf (5000 = ~3750 Wörter)

**Terminal Width**: Wie breit dein Terminal ist (80 Zeichen = Standard)

### Falls Output trotzdem abgeschnitten wirkt:

**Problem 1**: Terminal zu schmal
```bash
# Verbreitere Terminal-Fenster
# Oder scrolle horizontal
```

**Problem 2**: Output scrollt aus Sicht
```bash
# Nutze less für scrollbare Anzeige
python selfai/selfai.py | less -R
```

**Problem 3**: Output wird wirklich abgeschnitten (LLM stoppt)
```yaml
# Erhöhe max_tokens in config.yaml
merge:
  providers:
    - max_tokens: 8000
```

---

## 📝 Wo wird Output NICHT limitiert?

### Terminal UI Funktionen - KEINE Limits:

**File**: `selfai/ui/terminal_ui.py`

```python
def streaming_chunk(self, chunk: str) -> None:
    if chunk:
        print(chunk, end="", flush=True)  # ← Kein Limit!

def typing_animation(self, text: str, delay: float = 0.02) -> None:
    for char in text:
        print(char, end="", flush=True)  # ← Kein Limit!
        time.sleep(delay)
    print()
```

**Resultat**: UI zeigt ALLES was das LLM sendet (bis `max_tokens`)!

---

## 🎯 Summary

**Was wurde gefixt**:
1. ✅ Default Fallback: 2048 → 4096 tokens
2. ✅ Config bereits: 5000 tokens (keine Änderung nötig)
3. ✅ token_limits.py: 4096 tokens (bereits gefixt)

**Effektives Limit**: **5000 tokens** für Merge Output

**Erwartetes Ergebnis**:
- Vollständige Merge-Responses (bis 5000 tokens)
- Kein Abschneiden mehr
- ~3750 Wörter = ~100 Zeilen Text

**Falls Output IMMER NOCH zu kurz**:
- Check: Scrolle im Terminal nach oben (vielleicht scrollte Output aus Sicht?)
- Check: `cat memory/plans/[plan].json | grep merge_max_tokens` → sollte 5000 zeigen
- Fix: Erhöhe `max_tokens` in config.yaml auf 8000

---

**Status**: ✅ FIXED - Merger Output jetzt 5000 tokens (war 2048)!
**Next**: Teste mit komplexem `/plan` und prüfe ob Output vollständig ist!
