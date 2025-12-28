#!/usr/bin/env python3
"""
Gemini Judge Diagnostic Tool

Testet alle Aspekte des Gemini Judge Systems und gibt detaillierte Fehlerberichte.

Usage:
    python scripts/diagnose_gemini_judge.py
"""

import subprocess
import sys
from pathlib import Path


def print_section(title: str):
    """Print section header"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def check_gemini_cli_installed():
    """Check if gemini CLI is in PATH"""
    print_section("1. Checking if 'gemini' is in PATH")

    try:
        result = subprocess.run(
            ["which", "gemini"],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode == 0:
            gemini_path = result.stdout.strip()
            print(f"✅ Found: {gemini_path}")
            return gemini_path
        else:
            print("❌ 'gemini' NOT found in PATH")
            print("\n💡 Installation:")
            print("   Option 1: pip install google-generativeai-cli")
            print("   Option 2: npm install -g @google/generative-ai-cli")
            print("\n   Then check: which gemini")
            return None

    except FileNotFoundError:
        print("❌ 'which' command not found (Windows?)")
        print("   Try: where gemini")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def check_gemini_cli_version(gemini_path: str):
    """Check gemini CLI version and help"""
    print_section("2. Checking 'gemini --help'")

    try:
        result = subprocess.run(
            [gemini_path, "--help"],
            capture_output=True,
            text=True,
            timeout=5
        )

        print(f"Return code: {result.returncode}")
        print(f"\nSTDOUT ({len(result.stdout)} chars):")
        print("-" * 40)
        print(result.stdout[:500])
        if len(result.stdout) > 500:
            print(f"... (truncated, total {len(result.stdout)} chars)")

        print(f"\nSTDERR ({len(result.stderr)} chars):")
        print("-" * 40)
        if result.stderr:
            print(result.stderr[:500])
            if len(result.stderr) > 500:
                print(f"... (truncated, total {len(result.stderr)} chars)")
        else:
            print("(empty)")

        if result.returncode == 0 or "Usage: gemini" in result.stdout:
            print("\n✅ Gemini CLI responds correctly")
            return True
        else:
            print("\n❌ Gemini CLI not responding correctly")
            return False

    except subprocess.TimeoutExpired:
        print("❌ Gemini CLI timed out (>5s)")
        print("   This may indicate it's hanging or waiting for input")
        return False
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {e}")
        return False


def test_gemini_one_shot(gemini_path: str):
    """Test gemini in one-shot mode (piping input)"""
    print_section("3. Testing one-shot mode (piped input)")

    test_prompt = "Say 'Hello World' and nothing else."

    try:
        print(f"Input: {test_prompt}")
        print("Running: echo '{prompt}' | gemini")

        result = subprocess.run(
            [gemini_path],
            input=test_prompt,
            capture_output=True,
            text=True,
            timeout=30
        )

        print(f"\nReturn code: {result.returncode}")
        print(f"\nSTDOUT ({len(result.stdout)} chars):")
        print("-" * 40)
        print(result.stdout[:500])
        if len(result.stdout) > 500:
            print(f"... (truncated, total {len(result.stdout)} chars)")

        print(f"\nSTDERR ({len(result.stderr)} chars):")
        print("-" * 40)
        if result.stderr:
            print(result.stderr[:500])
            if len(result.stderr) > 500:
                print(f"... (truncated, total {len(result.stderr)} chars)")
        else:
            print("(empty)")

        if result.returncode == 0 and result.stdout.strip():
            print("\n✅ Gemini responded in one-shot mode")
            return True
        else:
            print("\n❌ Gemini did not respond correctly")
            if result.returncode != 0:
                print(f"   Exit code: {result.returncode}")
            if not result.stdout.strip():
                print("   STDOUT is empty!")
            return False

    except subprocess.TimeoutExpired:
        print("❌ Gemini timed out (>30s)")
        print("   Possible issues:")
        print("   - Gemini waiting for API key")
        print("   - Gemini in interactive mode (not accepting piped input)")
        print("   - Network issues")
        return False
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {e}")
        import traceback
        print("\nTraceback:")
        print(traceback.format_exc())
        return False


def test_gemini_json_response(gemini_path: str):
    """Test if gemini can return JSON"""
    print_section("4. Testing JSON response format")

    test_prompt = """Respond ONLY with valid JSON, no other text.

{
  "test": "success",
  "message": "This is a test"
}
"""

    try:
        print("Requesting JSON response...")

        result = subprocess.run(
            [gemini_path],
            input=test_prompt,
            capture_output=True,
            text=True,
            timeout=30
        )

        print(f"\nReturn code: {result.returncode}")
        print(f"\nSTDOUT ({len(result.stdout)} chars):")
        print("-" * 40)
        print(result.stdout)

        if result.returncode == 0:
            # Try to parse JSON
            import json
            output = result.stdout.strip()

            # Remove markdown code fences if present
            if "```json" in output:
                json_start = output.find("```json") + 7
                json_end = output.find("```", json_start)
                output = output[json_start:json_end].strip()
            elif "```" in output:
                json_start = output.find("```") + 3
                json_end = output.find("```", json_start)
                output = output[json_start:json_end].strip()

            try:
                data = json.loads(output)
                print("\n✅ Valid JSON received!")
                print(f"   Parsed: {data}")
                return True
            except json.JSONDecodeError as e:
                print(f"\n❌ Invalid JSON: {e}")
                print("   This may work anyway if Gemini uses markdown code fences")
                return False
        else:
            print("\n❌ Gemini failed to respond")
            return False

    except subprocess.TimeoutExpired:
        print("❌ Gemini timed out (>30s)")
        return False
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {e}")
        return False


def check_api_key():
    """Check if Gemini API key is configured"""
    print_section("5. Checking API Key Configuration")

    import os

    # Common environment variable names
    env_vars = [
        "GEMINI_API_KEY",
        "GOOGLE_API_KEY",
        "GOOGLE_GEMINI_API_KEY",
        "GENAI_API_KEY"
    ]

    found_keys = []
    for var in env_vars:
        if os.getenv(var):
            found_keys.append(var)
            value = os.getenv(var)
            masked = value[:8] + "..." + value[-4:] if len(value) > 12 else "***"
            print(f"✅ {var}: {masked}")

    if not found_keys:
        print("⚠️  No API key environment variables found")
        print("   Common names: GEMINI_API_KEY, GOOGLE_API_KEY")
        print("\n💡 Get API key:")
        print("   https://makersuite.google.com/app/apikey")
        print("\n   Then set: export GEMINI_API_KEY='your-key-here'")

    # Check config files
    config_paths = [
        Path.home() / ".gemini" / "config.json",
        Path.home() / ".config" / "gemini" / "config.json",
    ]

    print("\nChecking config files:")
    for path in config_paths:
        if path.exists():
            print(f"✅ Found: {path}")
            try:
                import json
                data = json.loads(path.read_text())
                if "apiKey" in data or "api_key" in data:
                    print("   ✅ Config contains API key")
                else:
                    print("   ⚠️  Config exists but no API key found")
            except Exception as e:
                print(f"   ⚠️  Could not parse: {e}")
        else:
            print(f"❌ Not found: {path}")


def test_gemini_judge_import():
    """Test if GeminiJudge can be imported"""
    print_section("6. Testing GeminiJudge Import")

    try:
        # Add project root to path
        project_root = Path(__file__).parent.parent
        sys.path.insert(0, str(project_root))

        from selfai.core.gemini_judge import GeminiJudge, format_score_for_terminal

        print("✅ Import successful")

        # Try to instantiate (will run availability check)
        print("\nTrying to instantiate GeminiJudge()...")
        try:
            judge = GeminiJudge()
            print("✅ GeminiJudge initialized successfully!")
            return True
        except RuntimeError as e:
            print(f"❌ GeminiJudge initialization failed:")
            print(f"   {e}")
            return False

    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {type(e).__name__}: {e}")
        import traceback
        print("\nTraceback:")
        print(traceback.format_exc())
        return False


def main():
    """Run all diagnostic checks"""
    print("\n" + "🔍" * 30)
    print("  GEMINI JUDGE DIAGNOSTIC TOOL")
    print("🔍" * 30)

    results = {}

    # Check 1: Is gemini in PATH?
    gemini_path = check_gemini_cli_installed()
    results["cli_installed"] = gemini_path is not None

    if not gemini_path:
        print("\n" + "=" * 60)
        print("⛔ CANNOT CONTINUE - Gemini CLI not found")
        print("=" * 60)
        print("\nPlease install gemini CLI and re-run this diagnostic.")
        sys.exit(1)

    # Check 2: Does --help work?
    results["cli_works"] = check_gemini_cli_version(gemini_path)

    # Check 3: Does one-shot mode work?
    results["oneshot_works"] = test_gemini_one_shot(gemini_path)

    # Check 4: Can it return JSON?
    results["json_works"] = test_gemini_json_response(gemini_path)

    # Check 5: API key configured?
    check_api_key()  # Informational only

    # Check 6: Can we import GeminiJudge?
    results["import_works"] = test_gemini_judge_import()

    # Summary
    print_section("SUMMARY")
    print("\nTest Results:")
    for test, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status}  {test}")

    all_passed = all(results.values())

    print("\n" + "=" * 60)
    if all_passed:
        print("✅ ALL TESTS PASSED - Gemini Judge should work!")
    else:
        print("❌ SOME TESTS FAILED - See details above")
        print("\n💡 Common Issues:")
        if not results.get("cli_installed"):
            print("   1. Install gemini CLI: pip install google-generativeai-cli")
        if not results.get("oneshot_works"):
            print("   2. Check API key configuration")
            print("   3. Verify network connectivity")
        if not results.get("json_works"):
            print("   4. Gemini may work but needs JSON format tuning")

    print("=" * 60 + "\n")

    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
