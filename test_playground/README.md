# Test Playground for SelfAI + Aider

This directory contains safe test files for testing SelfAI's Aider integration.

**Purpose**: Test Aider functionality WITHOUT risking SelfAI's own code.

## Files

- `calculator.py` - Simple calculator module for testing
- `data_processor.py` - (to be created) Data processing examples
- `api_client.py` - (to be created) API client skeleton

## Safety Rules

⚠️ **NEVER use SelfAI + Aider on these directories**:
- `selfai/` - SelfAI's own source code
- `selfai/core/` - Critical execution logic
- `selfai/tools/` - Tool implementations
- `config.yaml` - Configuration
- `.env` - Secrets

✅ **Safe for testing**:
- `test_playground/` - This directory (isolated)
- Any new files you create specifically for testing
- Files in temporary directories like `/tmp/`

## Test Status

- [ ] Test 1: Add divide function to calculator.py
- [ ] Test 2: Add type hints to all functions
- [ ] Test 3: Create new data_processor.py file
