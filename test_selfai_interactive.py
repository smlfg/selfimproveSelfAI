#!/usr/bin/env python3
"""
Interactive SelfAI Test - Sends commands programmatically
"""

import subprocess
import time
import sys

def test_selfai_command(command, timeout=30):
    """
    Test SelfAI with a specific command
    """
    print("=" * 80)
    print(f"🧪 Testing: {command}")
    print("=" * 80)

    # Start SelfAI
    proc = subprocess.Popen(
        ["python", "selfai/selfai.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1
    )

    try:
        # Wait a bit for startup
        time.sleep(3)

        # Send command
        proc.stdin.write(command + "\n")
        proc.stdin.flush()

        # Wait for response
        time.sleep(timeout)

        # Send quit
        proc.stdin.write("quit\n")
        proc.stdin.flush()

        # Get output
        stdout, stderr = proc.communicate(timeout=5)

        print("\n📤 OUTPUT:")
        print("-" * 80)
        print(stdout[-2000:])  # Last 2000 chars

        if stderr:
            print("\n❌ ERRORS:")
            print("-" * 80)
            print(stderr[-1000:])

        print("\n" + "=" * 80)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        proc.kill()
    finally:
        proc.terminate()

if __name__ == "__main__":
    print("""
╔════════════════════════════════════════════════════════════════╗
║                                                                ║
║        🧪 SELFAI INTERACTIVE TEST SCRIPT 🧪                    ║
║                                                                ║
╚════════════════════════════════════════════════════════════════╝

This script tests SelfAI by sending commands programmatically.
""")

    # Test 1: Simple tool call
    test_selfai_command("Say hello!", timeout=20)

    # Test 2: List files
    # test_selfai_command("List Python files in selfai/core", timeout=20)

    print("\n✅ Tests completed!")
