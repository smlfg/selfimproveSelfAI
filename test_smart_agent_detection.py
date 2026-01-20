#!/usr/bin/env python3
"""
Test Smart Agent Loop Detection
=================================

Tests verschiedene Queries um zu sehen ob die Smart Detection
korrekt zwischen Agent Loop und Simple Response unterscheidet.
"""

# Simuliere die requires_agent_loop Funktion
def requires_agent_loop(user_input: str) -> bool:
    """Kopie der Funktion aus selfai.py für Testing"""
    user_lower = user_input.lower().strip()

    # Commands aktivieren immer Agent (außer /switch, /memory)
    if user_input.startswith("/") and not user_input.startswith(("/switch", "/memory")):
        return True

    # Tool-Action Keywords
    tool_keywords = [
        "liste", "list", "zeige", "show",
        "suche", "search", "finde", "find",
        "erstelle", "create", "schreibe", "write",
        "führe aus", "execute", "run",
        "lese", "read", "öffne", "open",
        "analysiere", "analyze",
        "teste", "test"
    ]

    # Self-Introspection Keywords
    introspection_keywords = [
        "welche tools", "deine tools", "your tools",
        "dein code", "your code", "selfai code",
        "wie funktioniert", "how does", "how do you",
        "was kannst du", "what can you"
    ]

    # Multi-Step Indicators
    multi_step_indicators = [" und ", " and ", " dann ", " danach "]

    # Check für Action Keywords
    if any(keyword in user_lower for keyword in tool_keywords):
        return True

    # Check für Self-Introspection
    if any(keyword in user_lower for keyword in introspection_keywords):
        return True

    # Check für Multi-Step
    if any(indicator in user_lower for indicator in multi_step_indicators):
        return True

    # Einfache Wissensfragen (nicht Agent)
    simple_patterns = [
        "was ist", "what is",
        "erkläre", "explain",
        "wie geht", "how to",
        "warum", "why",
        "hallo", "hi", "hey"
    ]

    # Wenn kurz UND nur Wissensfrage → kein Agent
    word_count = len(user_input.split())
    if word_count < 8 and any(pattern in user_lower for pattern in simple_patterns):
        return False

    # Default: Bei Unsicherheit KEIN Agent (konservativ)
    return False


# Test Cases
test_cases = [
    # (query, expected_agent_mode, reason)

    # SHOULD USE AGENT (True)
    ("Liste alle Tools auf", True, "Tool-Action Keyword: 'liste'"),
    ("Suche nach Python-Dateien", True, "Tool-Action Keyword: 'suche'"),
    ("Erstelle eine neue Datei test.txt", True, "Tool-Action Keyword: 'erstelle'"),
    ("Welche Tools hast du?", True, "Self-Introspection"),
    ("Zeige mir deinen Code", True, "Self-Introspection + Action"),
    ("Analysiere das Projekt und erstelle Bericht", True, "Multi-Step + Action"),
    ("/plan create a hello world script", True, "Command"),
    ("/selfimprove optimize UI", True, "Command"),
    ("Finde alle Python-Dateien und liste sie", True, "Multi-Step + Action"),

    # SHOULD NOT USE AGENT (False)
    ("Was ist Python?", False, "Simple knowledge question"),
    ("Erkläre mir Objektorientierung", False, "Simple knowledge question"),
    ("Hallo", False, "Greeting"),
    ("Hi, wie geht's?", False, "Greeting + short"),
    ("Warum ist der Himmel blau?", False, "Simple 'why' question"),
    ("Was macht eine for-Schleife?", False, "Simple knowledge, < 8 words"),
    ("/switch code_helper", False, "Switch command (excluded)"),
    ("/memory", False, "Memory command (excluded)"),
]


def run_tests():
    """Run all test cases and show results"""
    print("=" * 70)
    print("SMART AGENT LOOP DETECTION - TEST RESULTS")
    print("=" * 70)
    print()

    passed = 0
    failed = 0

    for query, expected, reason in test_cases:
        result = requires_agent_loop(query)
        status = "✅ PASS" if result == expected else "❌ FAIL"

        if result == expected:
            passed += 1
        else:
            failed += 1

        mode = "🤖 AGENT" if result else "💬 SIMPLE"
        expected_mode = "🤖 AGENT" if expected else "💬 SIMPLE"

        print(f"{status} {mode} | Query: \"{query}\"")
        if result != expected:
            print(f"     Expected: {expected_mode} | Reason: {reason}")
        print()

    print("=" * 70)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 70)

    return failed == 0


if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)
