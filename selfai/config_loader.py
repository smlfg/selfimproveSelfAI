import os
import sys
import yaml
from dataclasses import dataclass
from typing import Dict
from dotenv import load_dotenv

@dataclass
class MiniMaxConfig:
    base_url: str
    model: str
    headers: Dict[str, str]

def load_configuration(config_path: str = 'config.yaml') -> MiniMaxConfig:
    """
    Lädt die MiniMax-Konfiguration aus einer YAML-Datei und Umgebungsvariablen.
    """
    load_dotenv()

    # YAML-Konfigurationsdatei laden
    if not os.path.exists(config_path):
        raise FileNotFoundError(
            f"'{config_path}' nicht gefunden. "
            f"Bitte kopieren Sie 'config.yaml.template' nach '{config_path}' und konfigurieren Sie es."
        )

    with open(config_path, 'r') as f:
        try:
            config_data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ValueError(f"Fehler beim Parsen von '{config_path}': {e}")

    if not isinstance(config_data, dict):
        raise ValueError("Konfigurationsdatei enthält keine gültigen Schlüssel/Wert-Paare.")
    
    # MiniMax API-Schlüssel aus Umgebungsvariable laden
    api_key = os.getenv('MINIMAX_API_KEY')
    if not api_key:
        raise ValueError(
            "MINIMAX_API_KEY ist nicht gesetzt. "
            "Bitte setzen Sie es in Ihrer .env-Datei (kopiert von .env.example)."
        )

    # Konfigurationswerte aus YAML laden
    minimax_section = config_data.get('minimax', {})
    base_url = minimax_section.get('base_url', 'https://api.minimax.io/v1')
    model = minimax_section.get('model', 'MiniMax-M2')
    
    # Authorization-Header erstellen
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    # Zusätzliche Header aus der Konfiguration hinzufügen
    custom_headers = minimax_section.get('headers', {})
    headers.update(custom_headers)
    
    return MiniMaxConfig(
        base_url=base_url,
        model=model,
        headers=headers
    )

# --- Beispiel-Nutzung ---
if __name__ == '__main__':
    print("Versuche Konfiguration zu laden...")
    try:
        config = load_configuration()
        print("✔️ Konfiguration erfolgreich geladen!")
        print("\n--- MiniMax-Konfiguration ---")
        print(f"Base URL: {config.base_url}")
        print(f"Modell: {config.model}")
        print("Headers:", {k: v for k, v in config.headers.items() if k != 'Authorization'})
    except (FileNotFoundError, ValueError) as e:
        print(f"❌ FEHLER: {e}")
        sys.exit(1)