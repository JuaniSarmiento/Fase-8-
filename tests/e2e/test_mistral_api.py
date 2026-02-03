"""
Quick test to verify Mistral API key works
"""
import os
from pathlib import Path

# Load .env
project_root = Path(__file__).parent.parent
env_file = project_root / ".env"

if env_file.exists():
    with open(env_file) as f:
        for line in f:
            if line.strip() and not line.startswith('#') and '=' in line:
                key, value = line.strip().split('=', 1)
                os.environ[key] = value

mistral_key = os.getenv("MISTRAL_API_KEY")
print(f"Mistral API Key: {mistral_key[:10]}...{mistral_key[-5:] if mistral_key else 'NOT FOUND'}")

if not mistral_key:
    print("❌ MISTRAL_API_KEY not found in .env")
    exit(1)

print("\nTesting Mistral API connection...")

try:
    from mistralai import Mistral
    
    client = Mistral(api_key=mistral_key)
    
    # Simple test call
    response = client.chat.complete(
        model="mistral-small-latest",
        messages=[
            {
                "role": "user",
                "content": "Say 'Hello from Mistral AI!' in exactly 5 words."
            }
        ],
        max_tokens=50
    )
    
    reply = response.choices[0].message.content
    
    print(f"✅ API Connection Successful!")
    print(f"   Model: mistral-small-latest")
    print(f"   Response: {reply}")
    print(f"\n🎉 Mistral AI is ready to use!")
    
except Exception as e:
    print(f"❌ API Connection Failed: {e}")
    exit(1)
