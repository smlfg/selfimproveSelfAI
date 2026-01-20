#!/bin/bash
# Test /help and /status Commands

echo "Testing /help and /status Commands..."
echo "======================================="
echo ""

# Test /help
echo "Test 1: /help Command"
echo "---------------------"
cat > /tmp/test_help.txt << 'EOF'
/help
quit
EOF

timeout 10 python selfai/selfai.py < /tmp/test_help.txt 2>&1 | grep -A 30 "📖 SelfAI Command Reference"

echo ""
echo "======================================="
echo ""

# Test /status
echo "Test 2: /status Command"
echo "------------------------"
cat > /tmp/test_status.txt << 'EOF'
/status
quit
EOF

timeout 10 python selfai/selfai.py < /tmp/test_status.txt 2>&1 | grep -A 40 "📊 SelfAI System Status"

echo ""
echo "======================================="
echo "Tests completed!"
