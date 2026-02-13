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
    # Top Tier Free
    "google/gemini-2.0-flash-lite-preview-02-05:free",
    "meta-llama/llama-3.3-70b-instruct:free",
    
    # DeepSeek
    "deepseek/deepseek-r1:free", # Retrying
    "deepseek/deepseek-r1-distill-llama-70b:free",
    "deepseek/deepseek-chat:free",
    
    # Mid Tier
    "mistralai/mistral-7b-instruct:free",
    "mistralai/mistral-small-24b-instruct-2501:free",
    "microsoft/phi-3-mini-128k-instruct:free",
    
    # Coding
    "qwen/qwen-2.5-coder-32b-instruct:free",
    "meta-llama/codellama-70b-instruct:free",
    
    # Older/Other
    "meta-llama/llama-3-8b-instruct:free",
    "sophosympatheia/midnight-rose-70b-v2.0.3:free" 
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
