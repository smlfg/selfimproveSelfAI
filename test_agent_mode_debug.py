#!/usr/bin/env python3
"""Debug test to check if Agent Mode is being triggered"""

import sys
from pathlib import Path

# Add to path
sys.path.insert(0, str(Path(__file__).parent))

from config_loader import load_configuration

config = load_configuration()

print("=== AGENT MODE DEBUG ===")
print(f"enable_agent_mode: {getattr(config.system, 'enable_agent_mode', 'NOT SET')}")
print(f"agent_max_steps: {getattr(config.system, 'agent_max_steps', 'NOT SET')}")
print(f"agent_verbose: {getattr(config.system, 'agent_verbose', 'NOT SET')}")
print("========================")
