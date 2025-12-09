#!/usr/bin/env python3
"""Minimal SelfAI Test mit MiniMax"""
from config_loader import load_configuration
from selfai.core.minimax_interface import MinimaxInterface

print("╔══════════════════════════════════════════════════╗")
print("║   SelfAI mit MiniMax - Minimal Test             ║")
print("╚══════════════════════════════════════════════════╝\n")

config = load_configuration()
print(f"✅ Config geladen - MiniMax enabled: {config.minimax_config.enabled}")

interface = MinimaxInterface(
    api_key=config.minimax_config.api_key,
    api_base=config.minimax_config.api_base,
    model=config.minimax_config.model
)

print(f"✅ MiniMax Interface bereit\n")
print("─" * 50)

# Interactive Chat Loop
while True:
    try:
        user_input = input("\n💬 Du: ")
        if user_input.lower() in ['quit', 'exit', 'q']:
            print("\n👋 Auf Wiedersehen!")
            break

        print("\n🤖 MiniMax denkt...", end='', flush=True)
        response = interface.generate_response(
            system_prompt="Du bist ein hilfreicher Assistent.",
            user_prompt=user_input,
            max_tokens=512
        )

        print(f"\r🤖 SelfAI: {response}\n")

    except KeyboardInterrupt:
        print("\n\n👋 Auf Wiedersehen!")
        break
    except Exception as e:
        print(f"\n❌ Fehler: {e}")
