import asyncio
import os
import sys

# Ensure we can import from backend
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

from config import (
    MODEL_GENERAL_REASONER, MODEL_NICHE_SPECIALIST, MODEL_BROAD_CONTEXT,
    MODEL_GROUNDING_VERIFIER, MODEL_INSTRUCTIONAL_ANALYST,
    MODEL_TECHNICAL_SPECIALIST, MODEL_CODE_REFACTORER, MODEL_VALIDATOR
)
from openrouter import query_model

# Hardcoded IDs to ensure independent verification from config
MODELS = {
    "General Reasoner (Gemma 3 27B)": "google/gemma-3-27b-it:free",
    "Niche Specialist (DeepSeek R1)": "deepseek/deepseek-r1-0528:free",
    "Broad Context (Llama 3.3 70B)": "meta-llama/llama-3.3-70b-instruct:free",
    "Verifier (Trinity Large)": "arcee-ai/trinity-large-preview:free",
    "Instructional (Gemma 3 12B)": "google/gemma-3-12b-it:free",
    "Technical (Qwen 3 Coder)": "qwen/qwen3-coder:free",
    "Refactorer (Nemotron 30B)": "nvidia/nemotron-3-nano-30b-a3b:free",
    "Validator (StepFun Flash)": "stepfun/step-3.5-flash:free"
}

async def verify_all():
    print(f"🔍 Verifying {len(MODELS)} Council Models...\n")
    
    results = []
    
    for name, model_id in MODELS.items():
        print(f"Testing {name} [{model_id}]...", end=" ", flush=True)
        try:
            # Simple ping
            response = await query_model(
                model=model_id,
                messages=[{"role": "user", "content": "Hi"}],
                timeout=60.0 
            )
            
            if response and response.get('content'):
                print("✅ OK")
                results.append((name, True, "Responsive"))
            else:
                print("❌ FAILED (No valid response)")
                results.append((name, False, "No content returned/Error"))
                
        except Exception as e:
            print(f"❌ ERROR: {e}")
            results.append((name, False, str(e)))

    print("\n--- Summary ---")
    all_passed = True
    for name, passed, msg in results:
        status = "✅" if passed else "❌"
        print(f"{status} {name}: {msg}")
        if not passed:
            all_passed = False
            
    if all_passed:
        print("\n✨ All 8 Council Models are operational!")
    else:
        print("\n⚠️ Some models failed verification.")

if __name__ == "__main__":
    asyncio.run(verify_all())
