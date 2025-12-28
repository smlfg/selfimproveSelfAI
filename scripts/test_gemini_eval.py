#!/usr/bin/env python3
"""
Test Gemini Judge Evaluation with Sample Data

This simulates a real evaluation to see exactly where it fails.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from selfai.core.gemini_judge import GeminiJudge, format_score_for_terminal


def test_simple_evaluation():
    """Test with minimal sample data"""
    print("=" * 60)
    print("  TESTING GEMINI JUDGE EVALUATION")
    print("=" * 60)

    # Sample data (minimal)
    original_goal = "Create a hello world program"
    execution_output = """
### Subtask: Write hello.py
print('Hello World')

### MERGE RESULT (Final Output):
Successfully created hello.py with Hello World program.
    """

    print("\n📝 Test Data:")
    print(f"   Goal: {original_goal}")
    print(f"   Output length: {len(execution_output)} chars")

    # Initialize judge
    print("\n🤖 Initializing GeminiJudge...")
    try:
        judge = GeminiJudge()
        print("✅ Initialization successful")
    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        return False

    # Evaluate
    print("\n📊 Running Evaluation...")
    print("-" * 60)
    try:
        score = judge.evaluate_task(
            original_goal=original_goal,
            execution_output=execution_output,
            plan_data=None,
            execution_time=1.5,
            files_changed=["hello.py"]
        )

        print("-" * 60)
        print("\n✅ Evaluation completed successfully!\n")

        # Display score
        score_text = format_score_for_terminal(score)
        print(score_text)

        # Check if it's a fallback score
        if "Bewertung fehlgeschlagen" in score.summary:
            print("\n⚠️  WARNING: This is a FALLBACK score!")
            print(f"   Reason: {score.summary}")
            print("\n   The evaluation ran but Gemini failed to respond correctly.")
            return False
        else:
            print("\n✅ Real score received (not fallback)")
            return True

    except Exception as e:
        print(f"\n❌ Evaluation failed with exception:")
        print(f"   Type: {type(e).__name__}")
        print(f"   Message: {e}")
        import traceback
        print("\n   Full Traceback:")
        print(traceback.format_exc())
        return False


if __name__ == "__main__":
    print("\n" + "🧪" * 30)
    print("  GEMINI JUDGE EVALUATION TEST")
    print("🧪" * 30 + "\n")

    success = test_simple_evaluation()

    print("\n" + "=" * 60)
    if success:
        print("✅ TEST PASSED - Gemini Judge works correctly!")
    else:
        print("❌ TEST FAILED - Check debug output above for details")
    print("=" * 60 + "\n")

    sys.exit(0 if success else 1)
