from dataclasses import dataclass, field
from typing import List, Optional
import yaml
from pathlib import Path
from dotenv import load_dotenv
import os

@dataclass
class MinimaxConfig:
    api_key: str
    api_base: str = "https://api.minimax.io/v1"
    model: str = "openai/MiniMax-M2"
    enabled: bool = True

@dataclass
class SystemConfig:
    streaming_enabled: bool = True
    stream_timeout: float = 60.0

@dataclass
class NPUProviderConfig:
    base_url: str = "http://localhost:3001/api/v1"
    workspace_slug: str = "main"
    api_key: str = ""

@dataclass
class CPUFallbackConfig:
    model_path: str = "Phi-3-mini-4k-instruct.Q4_K_M.gguf"
    n_ctx: int = 4096
    n_gpu_layers: int = 0

@dataclass
class ProviderConfig:
    name: str
    type: str
    base_url: str
    model: str
    timeout: float = 180.0
    max_tokens: int = 1024
    api_key_env: Optional[str] = None

@dataclass
class PlannerConfig:
    enabled: bool = False
    execution_timeout: float = 120.0
    providers: List[ProviderConfig] = field(default_factory=list)

@dataclass
class MergeConfig:
    enabled: bool = False
    providers: List[ProviderConfig] = field(default_factory=list)

@dataclass
class AgentConfig:
    default_agent: str = "default"

@dataclass
class AppConfig:
    minimax_config: MinimaxConfig
    system: SystemConfig
    npu_provider: NPUProviderConfig
    cpu_fallback: CPUFallbackConfig
    planner: PlannerConfig
    merge: MergeConfig
    agent_config: AgentConfig

def load_configuration():
    load_dotenv()
    config_path = Path("config.yaml")

    if not config_path.exists():
        # Fallback: create minimal config
        return AppConfig(
            minimax_config=MinimaxConfig(
                api_key=os.getenv("MINIMAX_API_KEY", ""),
                api_base="https://api.minimax.io/v1",
                model="openai/MiniMax-M2",
                enabled=True
            ),
            system=SystemConfig(),
            npu_provider=NPUProviderConfig(),
            cpu_fallback=CPUFallbackConfig(),
            planner=PlannerConfig(),
            merge=MergeConfig(),
            agent_config=AgentConfig()
        )

    with open(config_path) as f:
        data = yaml.safe_load(f) or {}

    # MiniMax Config
    minimax_data = data.get("minimax", {})
    minimax_cfg = MinimaxConfig(
        api_key=os.getenv("MINIMAX_API_KEY", minimax_data.get("api_key", "")),
        api_base=minimax_data.get("api_base", "https://api.minimax.io/v1"),
        model=minimax_data.get("model", "openai/MiniMax-M2"),
        enabled=minimax_data.get("enabled", True)
    )

    # System Config
    system_data = data.get("system", {})
    system_cfg = SystemConfig(
        streaming_enabled=system_data.get("streaming_enabled", True),
        stream_timeout=system_data.get("stream_timeout", 60.0)
    )

    # NPU Provider Config
    npu_data = data.get("npu_provider", {})
    npu_cfg = NPUProviderConfig(
        base_url=npu_data.get("base_url", "http://localhost:3001/api/v1"),
        workspace_slug=npu_data.get("workspace_slug", "main"),
        api_key=os.getenv("API_KEY", npu_data.get("api_key", ""))
    )

    # CPU Fallback Config
    cpu_data = data.get("cpu_fallback", {})
    cpu_cfg = CPUFallbackConfig(
        model_path=cpu_data.get("model_path", "Phi-3-mini-4k-instruct.Q4_K_M.gguf"),
        n_ctx=cpu_data.get("n_ctx", 4096),
        n_gpu_layers=cpu_data.get("n_gpu_layers", 0)
    )

    # Planner Config
    planner_data = data.get("planner", {})
    planner_providers = []
    for p in planner_data.get("providers", []):
        api_key_env = p.get("api_key_env")
        provider = ProviderConfig(
            name=p["name"],
            type=p["type"],
            base_url=p["base_url"],
            model=p["model"],
            timeout=p.get("timeout", 180.0),
            max_tokens=p.get("max_tokens", 1024),
            api_key_env=api_key_env
        )
        planner_providers.append(provider)

    planner_cfg = PlannerConfig(
        enabled=planner_data.get("enabled", False),
        execution_timeout=planner_data.get("execution_timeout", 120.0),
        providers=planner_providers
    )

    # Merge Config
    merge_data = data.get("merge", {})
    merge_providers = []
    for p in merge_data.get("providers", []):
        api_key_env = p.get("api_key_env")
        provider = ProviderConfig(
            name=p["name"],
            type=p["type"],
            base_url=p["base_url"],
            model=p["model"],
            timeout=p.get("timeout", 180.0),
            max_tokens=p.get("max_tokens", 2048),
            api_key_env=api_key_env
        )
        merge_providers.append(provider)

    merge_cfg = MergeConfig(
        enabled=merge_data.get("enabled", False),
        providers=merge_providers
    )

    # Agent Config
    agent_data = data.get("agent_config", {})
    agent_cfg = AgentConfig(
        default_agent=agent_data.get("default_agent", "default")
    )

    return AppConfig(
        minimax_config=minimax_cfg,
        system=system_cfg,
        npu_provider=npu_cfg,
        cpu_fallback=cpu_cfg,
        planner=planner_cfg,
        merge=merge_cfg,
        agent_config=agent_cfg
    )
