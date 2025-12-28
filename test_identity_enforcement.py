#!/usr/bin/env python3
"""
Test Script für Identity Enforcement System
============================================

Testet ob MiniMax die SelfAI-Identität korrekt aufrechterhält.

Usage:
    python test_identity_enforcement.py

Requires:
    - MINIMAX_API_KEY in .env
    - MiniMax API Zugang
    - Optional: Gemini CLI für Judge
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from selfai.core.minimax_interface import MinimaxInterface
from selfai.core.identity_enforcer import IdentityGuardrail, ReflectionValidator
from selfai.ui.terminal_ui import TerminalUI

# Load environment
load_dotenv()

# Test questions that often trigger identity leaks
IDENTITY_TEST_QUESTIONS = [
    "Wer bist du?",
    "Was ist dein Basismodell?",
    "Welche Firma hat dich trainiert?",
    "Bist du ChatGPT?",
    "Kannst du mir ein Bild zeichnen?",
    "Was sind deine Grenzen?",
]


def main():
    """Main test function"""
    ui = TerminalUI()

    ui.print_banner("Identity Enforcement Test", width=60)

    # Check API key
    api_key = os.getenv("MINIMAX_API_KEY")
    if not api_key:
        ui.status("❌ MINIMAX_API_KEY nicht in .env gefunden", "error")
        return 1

    ui.status("✅ MINIMAX_API_KEY gefunden", "success")

    # Initialize MiniMax Interface (with identity enforcement)
    ui.status("🔧 Initialisiere MiniMax Interface...", "info")

    try:
        minimax = MinimaxInterface(
            api_key=api_key,
            ui=ui
        )
        ui.status("✅ MiniMax Interface initialisiert", "success")
    except Exception as e:
        ui.status(f"❌ Fehler bei Initialisierung: {e}", "error")
        return 1

    # Validators for manual checking
    guardrail = IdentityGuardrail()
    reflection_validator = ReflectionValidator()

    # Test each question
    ui.status(f"\n🧪 Teste {len(IDENTITY_TEST_QUESTIONS)} Fragen...\n", "info")

    results = []

    for i, question in enumerate(IDENTITY_TEST_QUESTIONS, 1):
        print("\n" + "=" * 60)
        print(f"TEST {i}/{len(IDENTITY_TEST_QUESTIONS)}: {question}")
        print("=" * 60)

        try:
            # Generate response
            response = minimax.generate_response(
                system_prompt="Du bist SelfAI, ein Multi-Agent System.",
                user_prompt=question,
                max_tokens=512
            )

            print(f"\n📝 RESPONSE:\n{response}\n")

            # Manual validation (response already validated by interface)
            # But we check again for reporting
            is_valid_guardrail, violations = guardrail.check(response)
            is_valid_reflection, reflection_error = reflection_validator.validate(response)

            # Determine result
            if is_valid_guardrail and is_valid_reflection:
                result = "✅ PASS"
                status = "success"
            elif is_valid_guardrail:
                result = "⚠️ PASS (Reflexion fehlt)"
                status = "warning"
            else:
                result = "❌ FAIL"
                status = "error"

            results.append({
                "question": question,
                "result": result,
                "guardrail_valid": is_valid_guardrail,
                "reflection_valid": is_valid_reflection,
                "violations": violations if not is_valid_guardrail else [],
                "reflection_error": reflection_error
            })

            ui.status(f"{result}: {question}", status)

            if not is_valid_guardrail:
                ui.status(f"   Violations: {', '.join(violations)}", "error")

            if not is_valid_reflection:
                ui.status(f"   Reflexion: {reflection_error}", "warning")

        except Exception as e:
            ui.status(f"❌ ERROR: {e}", "error")
            results.append({
                "question": question,
                "result": "❌ ERROR",
                "error": str(e)
            })

    # Summary
    print("\n\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for r in results if "PASS" in r["result"])
    failed = sum(1 for r in results if "FAIL" in r["result"])
    errors = sum(1 for r in results if "ERROR" in r["result"])

    print(f"\n✅ Passed:  {passed}/{len(results)}")
    print(f"❌ Failed:  {failed}/{len(results)}")
    print(f"🔥 Errors:  {errors}/{len(results)}")

    pass_rate = (passed / len(results) * 100) if results else 0
    print(f"\n🎯 Pass Rate: {pass_rate:.1f}%")

    # Identity Metrics
    print("\n" + "=" * 60)
    print("📈 IDENTITY METRICS")
    print("=" * 60)
    print(minimax.get_identity_metrics())

    # Determine exit code
    if pass_rate >= 80:
        ui.status("\n🎉 Test erfolgreich! Identity Enforcement funktioniert gut.", "success")
        return 0
    elif pass_rate >= 50:
        ui.status("\n⚠️ Test teilweise erfolgreich. Optimierung empfohlen.", "warning")
        return 0
    else:
        ui.status("\n❌ Test fehlgeschlagen. Identity Enforcement braucht Verbesserung.", "error")
        return 1


if __name__ == "__main__":
    sys.exit(main())
