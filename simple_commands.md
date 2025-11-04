# 🚀 Einfache Befehle für Modell-Download

## Schritt 1: Virtual Environment aktivieren
```bash
source venv/bin/activate
```

## Schritt 2: Mit Ihrem HF Token anmelden
```bash
huggingface-cli login --token IHR_HUGGINGFACE_TOKEN_HIER
```

## Schritt 3: Modell herunterladen (wählen Sie eines)

### Option A: Kleines Modell (1GB - schnell)
```bash
huggingface-cli download huggingface/Llama-3.2-1B-Instruct-Q4_K_M-GGUF llama-3.2-1b-instruct-q4_k_m.gguf --local-dir models --local-dir-use-symlinks False
```

### Option B: Mittleres Modell (2.4GB - bessere Qualität)
```bash
huggingface-cli download microsoft/Phi-3.5-mini-instruct-gguf Phi-3.5-mini-instruct-Q4_K_M.gguf --local-dir models --local-dir-use-symlinks False
```

## Schritt 4: Config automatisch anpassen
```bash
python update_config.py
```

## Schritt 5: Echte AI testen!
```bash
python npu_chat.py
```

---

## Alternative: Manueller Download-Test

Falls die automatischen Befehle nicht funktionieren, können Sie auch:

1. Ein GGUF-Modell manuell herunterladen (z.B. von https://huggingface.co/models?library=gguf)
2. In den `models/` Ordner kopieren
3. `python update_config.py` ausführen
4. `python npu_chat.py` testen

---

## Aktueller Status ✅

- ✅ System funktioniert im Demo-Modus
- ✅ Alle Bibliotheken installiert
- ✅ Hugging Face CLI verfügbar
- ✅ QNN-Modelle vorhanden (für NPU)
- ⏳ Nur noch GGUF-Modell für CPU needed