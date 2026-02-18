import asyncio
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Manual .env loading
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
    # Proven Working (BaseLine)
    "google/gemma-3-27b-it:free",
    "google/gemma-3-12b-it:free",
    "nvidia/nemotron-3-nano-30b-a3b:free",
    "stepfun/step-3.5-flash:free",
    "arcee-ai/trinity-large-preview:free",

    # Potential Upgrades for Llama 3.3 (Broad Context)
    "microsoft/phi-3-medium-128k-instruct:free",
    "mistralai/mistral-7b-instruct-v0.3:free",
    "huggingfaceh4/zephyr-7b-beta:free",
    
    # Potential Upgrades for Qwen Coder (Coding)
    "codellama/codellama-34b-instruct:free",
    "google/gemini-2.0-pro-exp-02-05:free", # Trying experimental
    "meta-llama/llama-3-8b-instruct:free",  # Smaller llama might not rate limit
]

async def test_candidates():
    print(f"🔍 Testing {len(CANDIDATES)} Candidate Models...\n")
    
    working = []
    
    for model_id in CANDIDATES:
        print(f"Testing {model_id}...", end=" ", flush=True)
        try:
            response = await query_model(
                model=model_id,
                messages=[{"role": "user", "content": "Hi"}],
                timeout=15.0 
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
