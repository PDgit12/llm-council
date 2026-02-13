import asyncio
import os
import sys
import json
from pprint import pprint

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

from council import run_analogy_pipeline

async def test_full_flow():
    print("🚀 Starting End-to-End Council Test...")
    print("Query: 'Explain Kubernetes using an analogy of a busy restaurant kitchen.'")
    
    try:
        result = await run_analogy_pipeline(
            "Explain Kubernetes using an analogy of a busy restaurant kitchen.",
            history=[],
            target_domain="Culinary Management"
        )
        
        print("\n✅ Pipeline Completed!")
        
        print("\n--- Stage 1 (Exploration) ---")
        pprint(result.get("stage1", {}).keys())
        
        print("\n--- Stage 2 (Grounding) ---")
        pprint(result.get("stage2", {}).keys())
        
        print("\n--- Stage 6 (Final Answer) ---")
        print(result.get("final_answer")[:500] + "...\n")
        
        if result.get("final_answer") and "Safety Alert" not in result.get("final_answer"):
            print("✨ SUCCESS: Generated a safe, complete response.")
        else:
            print("⚠️ WARNING: Response was blocked or empty.")
            
    except Exception as e:
        print(f"❌ CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_full_flow())
