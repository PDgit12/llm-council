import asyncio
import sys
import os
from dotenv import load_dotenv

# Ensure we can import from backend
sys.path.append(os.getcwd())

from config import COUNCIL_MODELS, STAGE2_MODELS, CHAIRMAN_MODEL
from openrouter import query_model

load_dotenv()

async def test_models():
    print("--- TESTING COUNCIL MODELS ---")
    messages = [{"role": "user", "content": "Say 'ok' if you can hear me."}]
    
    all_models = list(set(COUNCIL_MODELS + STAGE2_MODELS + [CHAIRMAN_MODEL]))
    
    for model in all_models:
        print(f"Testing {model}...", end="", flush=True)
        try:
            response = await query_model(model, messages, timeout=10.0)
            if response:
                print(f" [OK] Response: {response['content'][:20]}...")
            else:
                print(" [FAIL] returned None")
        except Exception as e:
            print(f" [ERROR] {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_models())
