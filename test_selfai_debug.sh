#!/bin/bash
# Debug test - shows what happens when you send "hi"

echo "=== SELFAI DEBUG TEST ==="
echo ""
echo "Sending: hi"
echo ""

# Create input
echo "hi" > /tmp/test_input.txt
echo "quit" >> /tmp/test_input.txt

# Run with full output
timeout 30 python selfai/selfai.py < /tmp/test_input.txt 2>&1 | grep -A 20 "Du: hi"

echo ""
echo "=== END DEBUG ==="

rm -f /tmp/test_input.txt
