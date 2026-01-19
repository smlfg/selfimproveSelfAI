#!/usr/bin/env python3
"""Test MiniMax API Connectivity with NEW API Key"""

import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get API key
api_key = os.getenv('MINIMAX_API_KEY')
if not api_key:
    print("❌ MINIMAX_API_KEY not set in .env")
    exit(1)

print(f"✅ NEW API Key loaded: {api_key[:20]}...")
print(f"   Key type: {'JWT' if api_key.startswith('eyJ') else 'sk-cp (new format)'}")

# Test API endpoint
api_base = "https://api.minimax.io/v1"
url = f"{api_base}/chat/completions"

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

# Test with correct model name
model_name = "MiniMax-M2"

print(f"\n{'='*60}")
print(f"🧪 Testing with model: {model_name}")
print(f"{'='*60}")

data = {
    "model": model_name,
    "messages": [
        {"role": "system", "content": "You are SelfAI, a helpful assistant."},
        {"role": "user", "content": "Say 'Hello! I am SelfAI powered by MiniMax!' and nothing else."}
    ],
    "max_tokens": 100,
    "temperature": 0.7
}

print(f"\n🔍 Sending request to {url}")

try:
    response = requests.post(url, headers=headers, json=data, timeout=30)
    print(f"\n📡 Response status: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        print(f"\n✅ ✅ ✅ SUCCESS! ✅ ✅ ✅")
        print(f"\n📝 Full response: {result}")

        if "choices" in result and len(result["choices"]) > 0:
            message = result["choices"][0]["message"]["content"]
            print(f"\n🎉 🎉 🎉 MiniMax Response:")
            print(f"    {message}")
            print(f"\n✅ Der neue API Key funktioniert perfekt!")
        else:
            print(f"⚠️ Unexpected response format: {result}")

    elif response.status_code == 429:
        print(f"\n❌ RATE LIMIT (429) - IMMER NOCH!")
        print(f"Response: {response.text}")
        print(f"\n⚠️ WARNUNG: Wenn der neue Key auch Rate Limit hat,")
        print(f"   ist möglicherweise Ihre IP-Adresse geblockt!")
        print(f"   Oder: Der alte Key wird noch verwendet.")

    elif response.status_code == 401:
        print(f"\n❌ AUTHENTICATION FAILED (401)")
        print(f"Response: {response.text}")
        print(f"\n⚠️ Der neue API Key ist ungültig oder falsch kopiert!")

    else:
        print(f"\n❌ FAILED!")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")

except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
