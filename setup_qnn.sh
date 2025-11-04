#!/bin/bash
# QNN SDK Setup Script
export QNN_SDK_ROOT="/mnt/c/Users/smlfl/Documents/AI_NPU_AGENT_Projekt/unpaked/qairt/2.38.0.250901"

# Add bin to PATH
if [ -d "$QNN_SDK_ROOT/bin/x86_64-linux-clang" ]; then
    export PATH="$QNN_SDK_ROOT/bin/x86_64-linux-clang:$PATH"
fi

# Add lib to LD_LIBRARY_PATH
if [ -d "$QNN_SDK_ROOT/lib/x86_64-linux-clang" ]; then
    export LD_LIBRARY_PATH="$QNN_SDK_ROOT/lib/x86_64-linux-clang:$LD_LIBRARY_PATH"
fi

echo "✅ QNN SDK environment configured."
echo "   QNN_SDK_ROOT is set to: $QNN_SDK_ROOT"
