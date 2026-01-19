#!/bin/bash
# Simple Test - SelfAI mit Echo-Tool

echo "Testing SelfAI with simple command..."
echo ""

# Create input file with command
echo "Say hello!" > /tmp/selfai_input.txt
echo "quit" >> /tmp/selfai_input.txt

# Run SelfAI with input redirection
echo "Starting SelfAI..."
timeout 60 python selfai/selfai.py < /tmp/selfai_input.txt 2>&1 | tee /tmp/selfai_output.txt

echo ""
echo "================================"
echo "Output saved to: /tmp/selfai_output.txt"
echo "Last 50 lines:"
echo "================================"
tail -50 /tmp/selfai_output.txt

# Cleanup
rm -f /tmp/selfai_input.txt
