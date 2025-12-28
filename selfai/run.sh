#!/bin/bash
# Wrapper to start SelfAI from the correct directory
cd "$(dirname "$0")/.."
python selfai/selfai.py "$@"
