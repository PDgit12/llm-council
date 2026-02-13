import asyncio
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Manual .env loading...
def load_env_manual():
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()

load_env_manual()

import config
from openrouter import query_model

async def test_fallback():
    print("🔍 Testing Model Fallback Logic...\n")
    
    # Inject a fake failure scenario
    FAKE_PRIMARY = "fake/model-that-fails"
    REAL_BACKUP = "google/gemma-3-12b-it:free"
    
    # Update config at runtime for testing
    config.MODEL_FALLBACKS[FAKE_PRIMARY] = REAL_BACKUP
    
    print(f"Primary (Fake): {FAKE_PRIMARY}")
    print(f"Backup (Real): {REAL_BACKUP}")
    print("Sending request to Primary...")
    
    try:
        response = await query_model(
            model=FAKE_PRIMARY,
            messages=[{"role": "user", "content": "Reply with 'Fallback Success'."}],
            timeout=10.0
        )
        
        if response and response.get('content'):
            print(f"✅ Result: {response['content']}")
            if "Fallback Success" in response['content'] or "Success" in response['content']:
                print("✨ Fallback mechanism verified!")
            else:
                print("⚠️ Received response but content differed (still likely success from LLM)")
        else:
            print("❌ FAILED: No response received")
            
    except Exception as e:
        print(f"❌ CRITICAL ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(test_fallback())
