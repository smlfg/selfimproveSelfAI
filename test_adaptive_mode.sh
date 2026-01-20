#!/bin/bash
# Test Adaptive Agent Mode

echo "Testing Adaptive Agent Mode..."
echo "==============================="
echo ""

# Test input file
cat > /tmp/test_adaptive.txt << 'EOF'
Was ist Python?
quit
EOF

echo "Test 1: Simple Question (should be fast, no agent loop)"
echo "Input: 'Was ist Python?'"
echo ""

timeout 30 python selfai/selfai.py < /tmp/test_adaptive.txt 2>&1 | grep -A 5 "Was ist Python"

echo ""
echo "==============================="
echo "Check: Did it skip Agent Loop?"
echo "Expected: Direct response without '🤖 AGENT REASONING' block"
