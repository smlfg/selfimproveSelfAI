#!/bin/bash
# Einfaches Modell-Setup Skript

echo "🚀 Modell-Setup für NPU/CPU Chat"
echo "=================================="

# Virtual Environment aktivieren
source venv/bin/activate

echo "✅ Virtual Environment aktiviert"

# Überprüfe HF CLI
echo "🔍 Überprüfe Hugging Face CLI..."
if huggingface-cli --help > /dev/null 2>&1; then
    echo "✅ Hugging Face CLI ist verfügbar"
else
    echo "❌ Hugging Face CLI nicht gefunden"
    exit 1
fi

# Models Verzeichnis erstellen
mkdir -p models
echo "✅ Models-Verzeichnis bereit"

echo ""
echo "📋 Nächste Schritte:"
echo "1. Führen Sie aus: huggingface-cli login --token IHR_TOKEN"
echo "2. Dann: huggingface-cli download microsoft/Phi-3.5-mini-instruct-gguf Phi-3.5-mini-instruct-Q4_K_M.gguf --local-dir models --local-dir-use-symlinks False"
echo "3. Warten Sie auf den Download (~2.4GB)"
echo "4. Testen Sie: python npu_chat.py"
echo ""
echo "💡 Kleinere Alternative (nur 1GB):"
echo "   huggingface-cli download huggingface/Llama-3.2-1B-Instruct-Q4_K_M-GGUF llama-3.2-1b-instruct-q4_k_m.gguf --local-dir models --local-dir-use-symlinks False"