# Parallel UI - Quick Start

## 🚀 In 3 Schritten zur Parallel UI

### 1️⃣ Installation (falls noch nicht gemacht)
```bash
pip install -r requirements-ui.txt
```

### 2️⃣ Aktivieren
```bash
export SELFAI_PARALLEL_UI=true
```

### 3️⃣ SelfAI starten und /plan nutzen
```bash
python selfai/selfai.py

Du: /plan Wer bist du und was sind deine Fähigkeiten?
```

---

## 🎨 Was du sehen wirst

**Vorher:**
```
💭 Thinking...
Response...
💭 Thinking 2...
Response 2...
```

**Nachher:**
```
╭─ Task 1 ─────╮╭─ Task 2 ─────╮╭─ Task 3 ─────╮
│ 💭 THINKING:  ││ 💭 THINKING:  ││ 💭 THINKING:  │
│   [cyan...]   ││   [cyan...]   ││   [cyan...]   │
│               ││               ││               │
│ 💬 RESPONSE:  ││ 💬 RESPONSE:  ││ 💬 RESPONSE:  │
│   [white...]  ││   [white...]  ││   [white...]  │
╰───────────────╯╰───────────────╯╰───────────────╯
```

**ALLE TASKS PARALLEL SICHTBAR!**

---

## ⚙️ Permanent aktivieren

```bash
# In ~/.bashrc oder ~/.zshrc:
echo 'export SELFAI_PARALLEL_UI=true' >> ~/.bashrc
source ~/.bashrc
```

---

## 🔧 Deaktivieren

```bash
# Temporary:
SELFAI_PARALLEL_UI=false python selfai/selfai.py

# Permanent:
# Entferne die Zeile aus ~/.bashrc
```

---

## 🐛 Troubleshooting

### Rich not installed?
```bash
pip install -r requirements-ui.txt
```

### Layout sieht kaputt aus?
```bash
# Terminal zu klein! Mindestens 80 Spalten nötig
# Check:
echo "Spalten: $(tput cols)"

# Resize Terminal oder deaktiviere Parallel UI:
export SELFAI_PARALLEL_UI=false
```

### Parallel UI aktiviert sich nicht?
```bash
# Check Status:
python -c "
from selfai.ui.ui_adapter import get_ui_info
import json
print(json.dumps(get_ui_info(), indent=2))
"

# Sollte zeigen:
# {
#   "parallel_available": true,
#   "parallel_enabled": true,
#   "active_ui": "ParallelStreamUI"
# }
```

---

## 📖 Mehr Info

- **Vollständige Dokumentation:** `PARALLEL_UI_GUIDE.md`
- **Implementation Details:** `PARALLEL_UI_IMPLEMENTATION.md`
- **Test Script:** `python test_parallel_ui.py`

---

**That's it! Viel Spaß mit der Parallel UI! 🎉**
