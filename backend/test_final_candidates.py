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

from openrouter import query_model

CANDIDATES = [
    "meta-llama/llama-3.2-3b-instruct:free",
    "cognitivecomputations/dolphin-mistral-24b-venice-edition:free",
    "arcee-ai/trinity-large-preview:free",
    "stepfun/step-3.5-flash:free"
]

async def test_candidates():
    print(f"🔍 Testing {len(CANDIDATES)} Final Candidates...\n")
    
    working = []
    
    for model_id in CANDIDATES:
        print(f"Testing {model_id}...", end=" ", flush=True)
        try:
            response = await query_model(
                model=model_id,
                messages=[{"role": "user", "content": "Hi"}],
                timeout=20.0 
            )
            
            if response and response.get('content'):
                print("✅ OK")
                working.append(model_id)
            else:
                print("❌ FAILED")
                
        except Exception as e:
            print(f"❌ ERROR: {e}")

    print("\n--- Working Models ---")
    for w in working:
        print(f"- {w}")

if __name__ == "__main__":
    asyncio.run(test_candidates())
