# GeminiUI (V2) ist jetzt Standard UI für SelfAI

## Änderung

**Datum**: 2025-01-20

**GeminiUI (V2) ist jetzt die Standard-Benutzeroberfläche für SelfAI.**

Die moderne, strukturierte UI von Gemini ist nun aktiviert, wenn keine Umgebungsvariable gesetzt ist.

---

## Was bedeutet das?

### Vorher (Alt)

```bash
# Standard war TerminalUI (V1)
python selfai/selfai.py
→ TerminalUI (V1) - Original UI mit vielen Farben/Emojis

# GeminiUI brauchte explizite Aktivierung
SELFAI_UI_VARIANT=v2 python selfai/selfai.py
→ GeminiUI (V2) - Moderne strukturierte UI
```

### Jetzt (Neu)

```bash
# Standard ist jetzt GeminiUI (V2)
python selfai/selfai.py
→ GeminiUI (V2) - Moderne strukturierte UI (STANDARD)

# Alte UI braucht explizite Aktivierung
SELFAI_UI_VARIANT=v1 python selfai/selfai.py
→ TerminalUI (V1) - Legacy UI
```

---

## Warum die Änderung?

**GeminiUI (V2) Vorteile:**
- ✅ Klarere visuelle Hierarchie (5 Ebenen)
- ✅ Bessere Lesbarkeit (weniger visuelle Überladung)
- ✅ Konsistente Formatierung (Box-Drawing-Zeichen)
- ✅ Professionelleres Erscheinungsbild
- ✅ Semantische Farbcodierung (Grün=Erfolg, Rot=Fehler)
- ✅ Moderne, strukturierte Layouts

**Design-Philosophie:**
- Struktur über Dekoration
- Klarheit über Farbenreichtum
- Information über Animation

---

## Wie nutze ich die alte UI?

Wenn du die alte TerminalUI (V1) bevorzugst:

```bash
# Option 1: Umgebungsvariable setzen
SELFAI_UI_VARIANT=v1 python selfai/selfai.py

# Option 2: In .bashrc/.zshrc hinzufügen
export SELFAI_UI_VARIANT=v1
```

---

## UI-Vergleich

### GeminiUI (V2) - Jetzt Standard

```
╔══════════════════════════════════════════════════════════════╗
║    🚀  SelfAI NextGen Interface  🚀                         ║
║          Hybrid Intelligence System (NPU & CPU)              ║
╚══════════════════════════════════════════════════════════════╝

═══════════════════════════════════════════════════════════════
 ℹ️  SYSTEM STATUS
═══════════════════════════════════════════════════════════════

ℹ️  Konfiguration geladen.
✅ Agent 'Code Helper' geladen

SelfAI │ MiniMax
·····················
Das ist eine Antwort mit klarer Struktur.

💭 Reasoning Process #1
  │ Hier ist mein Denkprozess...
  │ - Schritt 1
  │ - Schritt 2
```

**Merkmale:**
- Doppellinien für Hauptsektionen (═)
- Einfache Linien für Untersektionen (─)
- Box-Zeichen für Hierarchie (│, ║, └)
- Konsistente Icon-Nutzung
- Klare Trennung von Inhalt und Metadaten

### TerminalUI (V1) - Legacy

```
╔══════════════════════════════════════════════════════════════╗
║                    🚀 SelfAI v2.0 🚀                         ║
║          Hybrid Intelligence System (NPU & CPU)              ║
╚══════════════════════════════════════════════════════════════╝

ℹ️  Konfiguration geladen.
✓ Agent 'Code Helper' geladen

🌊 [SelfAI | MiniMax]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Das ist eine Antwort mit vielen Farben und Effekten.

💭 [Thinking 1]
  Hier ist mein Denkprozess...
  - Schritt 1
  - Schritt 2
```

**Merkmale:**
- Mehr Farben und Emojis
- Animierte Effekte (Typing-Animation)
- Visuelle "Spielereien"
- Weniger strikte Hierarchie

---

## Commands

### UI-Status prüfen

```bash
You: /ui

# Ausgabe zeigt:
# ℹ️  Aktuelles UI: GeminiUI (V2)
# ℹ️  Verfügbare Varianten: v2 (GeminiUI - Standard), v1 (TerminalUI - Legacy)
```

### UI wechseln

```bash
# Alte UI aktivieren
You: /ui v1

# Ausgabe:
# ⚠️  UI-Wechsel erfordert Neustart von SelfAI
# ℹ️  Starte neu mit: SELFAI_UI_VARIANT=v1 python selfai/selfai.py
```

---

## Technische Details

### Geänderte Datei

**`selfai/selfai.py`** (Zeile 1089-1099):

```python
def main():
    # UI Variant Selection: Check environment variable
    # DEFAULT CHANGED: GeminiUI (V2) is now the default
    ui_variant = os.environ.get("SELFAI_UI_VARIANT", "v2").lower()

    if ui_variant == "v1" or ui_variant == "terminal":
        ui = TerminalUI()
        ui_variant_name = "TerminalUI (V1)"
    else:
        # Default: GeminiUI (V2)
        ui = GeminiUI()
        ui_variant_name = "GeminiUI (V2)"
```

**Vorher**: `os.environ.get("SELFAI_UI_VARIANT", "v1")`
**Nachher**: `os.environ.get("SELFAI_UI_VARIANT", "v2")`

### Logik

- **Keine Umgebungsvariable** → GeminiUI (V2) ✅
- **`SELFAI_UI_VARIANT=v1`** → TerminalUI (V1)
- **`SELFAI_UI_VARIANT=v2`** → GeminiUI (V2)
- **`SELFAI_UI_VARIANT=gemini`** → GeminiUI (V2)
- **`SELFAI_UI_VARIANT=terminal`** → TerminalUI (V1)

---

## Feedback & Probleme

### Gefällt dir die neue UI nicht?

**Einfach alte UI aktivieren:**
```bash
SELFAI_UI_VARIANT=v1 python selfai/selfai.py
```

### UI-Metriken

Beide UIs werden weiterhin für A/B-Tests getrackt:

```bash
You: /uimetrics

# Zeigt Vergleich:
# - GeminiUI (V2) Sessions
# - TerminalUI (V1) Sessions
# - Empfehlung basierend auf Nutzung
```

### Probleme melden

Wenn du Probleme mit GeminiUI (V2) findest:
1. Aktiviere vorübergehend V1: `SELFAI_UI_VARIANT=v1`
2. Melde das Problem als GitHub Issue
3. Beschreibe was nicht funktioniert

---

## Zusammenfassung

**Was ändert sich:**
- 🔄 GeminiUI (V2) ist jetzt **Standard**
- 🔄 TerminalUI (V1) ist jetzt **Legacy** (aber weiterhin verfügbar)

**Was bleibt gleich:**
- ✅ Alle Features funktionieren in beiden UIs
- ✅ A/B-Testing weiterhin aktiv
- ✅ Einfacher Wechsel zwischen UIs möglich
- ✅ Metriken-Tracking für beide UIs

**Nächste Schritte:**
1. Teste die neue Standard-UI (GeminiUI V2)
2. Gib Feedback über `/uimetrics`
3. Nutze V1 falls nötig mit `SELFAI_UI_VARIANT=v1`

---

**Viel Spaß mit der neuen Standard-UI!** 🎉
