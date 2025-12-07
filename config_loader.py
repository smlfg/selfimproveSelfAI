import os
import sys
import yaml
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from pathlib import Path
from dotenv import load_dotenv


@dataclass
class MinimaxConfig:
    """MiniMax Cloud API - Primary Backend (ersetzt AnythingLLM/NPU)"""
    api_key: str
    api_base: str = "https://api.minimax.io/v1"
    model: str = "openai/MiniMax-M2"
    enabled: bool = True


@dataclass
class SystemConfig:
    """General system settings"""
    streaming_enabled: bool = True
    stream_timeout: float = 60.0


@dataclass
class CPUFallbackConfig:
    """CPU Fallback mit GGUF"""
    model_path: str = "Phi-3-mini-4k-instruct.Q4_K_M.gguf"
    n_ctx: int = 4096
    n_gpu_layers: int = 0


@dataclass
class ProviderConfig:
    """Generic provider (Planner/Merge)"""
    name: str
    type: str
    base_url: str
    model: str
    timeout: float = 180.0
    max_tokens: int = 1024
    api_key_env: Optional[str] = None


@dataclass
class PlannerConfig:
    """DPPM Planning Phase - KRITISCH!"""
    enabled: bool = False
    execution_timeout: float = 120.0
    providers: List[ProviderConfig] = field(default_factory=list)


@dataclass
class MergeConfig:
    """Merge Phase - Result Synthesis"""
    enabled: bool = False
    providers: List[ProviderConfig] = field(default_factory=list)


@dataclass
class AgentConfig:
    """Agent Management"""
    default_agent: str = "default"


@dataclass
class AppConfig:
    """COMPLETE SelfAI Config - ALLE Features!"""
    minimax_config: MinimaxConfig
    system: SystemConfig
    cpu_fallback: CPUFallbackConfig
    planner: PlannerConfig
    merge: MergeConfig
    agent_config: AgentConfig


def load_configuration(config_path: str = 'config.yaml') -> AppConfig:
    """
    Lädt die vollständige SelfAI-Konfiguration aus einer YAML-Datei und Umgebungsvariablen.
    
    KRITISCH: Gibt AppConfig zurück, nicht nur MiniMaxConfig!
    Enthält ALLE Sub-Configs für DPPM (Distributed Planning Problem Model).
    """
    # .env-Datei für Geheimnisse laden
    load_dotenv()

    # Fallback-Konfiguration wenn config.yaml fehlt
    if not os.path.exists(config_path):
        print(f"Warnung: '{config_path}' nicht gefunden. Verwende Standard-Fallback-Konfiguration.")
        return AppConfig(
            minimax_config=MinimaxConfig(
                api_key=os.getenv("MINIMAX_API_KEY", ""),
                api_base="https://api.minimax.io/v1",
                model="openai/MiniMax-M2",
                enabled=True
            ),
            system=SystemConfig(),
            cpu_fallback=CPUFallbackConfig(),
            planner=PlannerConfig(enabled=False),
            merge=MergeConfig(enabled=False),
            agent_config=AgentConfig()
        )
    
    # YAML-Konfigurationsdatei laden
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

    # Parse sections aus YAML
    minimax_section = config_data.get('minimax', {})
    system_section = config_data.get('system', {})
    cpu_section = config_data.get('cpu_fallback', {})
    planner_section = config_data.get('planner', {})
    merge_section = config_data.get('merge', {})
    agent_section = config_data.get('agent_config', {})
    
    # Provider-Listen aus YAML parsen
    def parse_providers(section_data: dict, section_name: str) -> List[ProviderConfig]:
        providers_data = section_data.get('providers', [])
        if not isinstance(providers_data, list):
            raise ValueError(f"'{section_name}.providers' muss eine Liste sein.")
        
        providers = []
        for i, provider_data in enumerate(providers_data):
            if not isinstance(provider_data, dict):
                raise ValueError(f"'{section_name}.providers[{i}]' muss ein Dictionary sein.")
            
            # API-Schlüssel aus Umgebungsvariable laden wenn api_key_env gesetzt ist
            if 'api_key_env' in provider_data and provider_data['api_key_env']:
                env_key = provider_data['api_key_env']
                provider_data = dict(provider_data)  # Kopie erstellen
                provider_data['api_key'] = os.getenv(env_key, '')
                del provider_data['api_key_env']  # Entfernen da jetzt direkt als api_key
            
            try:
                provider = ProviderConfig(**provider_data)
                providers.append(provider)
            except TypeError as e:
                raise ValueError(f"Fehler beim Parsen von '{section_name}.providers[{i}]': {e}")
        
        return providers

    # AppConfig mit allen Sub-Configs erstellen
    return AppConfig(
        minimax_config=MinimaxConfig(
            api_key=api_key,
            api_base=minimax_section.get('api_base', 'https://api.minimax.io/v1'),
            model=minimax_section.get('model', 'openai/MiniMax-M2'),
            enabled=minimax_section.get('enabled', True)
        ),
        system=SystemConfig(
            streaming_enabled=system_section.get('streaming_enabled', True),
            stream_timeout=system_section.get('stream_timeout', 60.0)
        ),
        cpu_fallback=CPUFallbackConfig(
            model_path=cpu_section.get('model_path', 'Phi-3-mini-4k-instruct.Q4_K_M.gguf'),
            n_ctx=cpu_section.get('n_ctx', 4096),
            n_gpu_layers=cpu_section.get('n_gpu_layers', 0)
        ),
        planner=PlannerConfig(
            enabled=planner_section.get('enabled', False),
            execution_timeout=planner_section.get('execution_timeout', 120.0),
            providers=parse_providers(planner_section, 'planner')
        ),
        merge=MergeConfig(
            enabled=merge_section.get('enabled', False),
            providers=parse_providers(merge_section, 'merge')
        ),
        agent_config=AgentConfig(
            default_agent=agent_section.get('default_agent', 'default')
        )
    )


# --- Beispiel-Nutzung ---
if __name__ == '__main__':
    print("Lade vollständige SelfAI-Konfiguration...")
    try:
        config = load_configuration()
        print("✅ Vollständige SelfAI-Konfiguration erfolgreich geladen!")
        
        print("\n" + "="*50)
        print("🔧 MINIMAX KONFIGURATION")
        print("="*50)
        print(f"API Base: {config.minimax_config.api_base}")
        print(f"Modell: {config.minimax_config.model}")
        print(f"Enabled: {config.minimax_config.enabled}")
        
        print("\n" + "="*50)
        print("⚙️  SYSTEM KONFIGURATION")
        print("="*50)
        print(f"Streaming Enabled: {config.system.streaming_enabled}")
        print(f"Stream Timeout: {config.system.stream_timeout}s")
        
        print("\n" + "="*50)
        print("🖥️  CPU FALLBACK KONFIGURATION")
        print("="*50)
        print(f"Model Path: {config.cpu_fallback.model_path}")
        print(f"Context Length: {config.cpu_fallback.n_ctx}")
        print(f"GPU Layers: {config.cpu_fallback.n_gpu_layers}")
        
        print("\n" + "="*50)
        print("🧠 PLANNER KONFIGURATION (DPPM)")
        print("="*50)
        print(f"Enabled: {config.planner.enabled}")
        print(f"Execution Timeout: {config.planner.execution_timeout}s")
        print(f"Anzahl Provider: {len(config.planner.providers)}")
        for i, provider in enumerate(config.planner.providers):
            print(f"  Provider {i+1}: {provider.name} ({provider.type})")
        
        print("\n" + "="*50)
        print("🔗 MERGE KONFIGURATION")
        print("="*50)
        print(f"Enabled: {config.merge.enabled}")
        print(f"Anzahl Provider: {len(config.merge.providers)}")
        for i, provider in enumerate(config.merge.providers):
            print(f"  Provider {i+1}: {provider.name} ({provider.type})")
        
        print("\n" + "="*50)
        print("🤖 AGENT KONFIGURATION")
        print("="*50)
        print(f"Default Agent: {config.agent_config.default_agent}")
        
    except (FileNotFoundError, ValueError) as e:
        print(f"❌ FEHLER: {e}")
        sys.exit(1)
