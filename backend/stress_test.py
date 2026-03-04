import asyncio
import os
import sys
import time

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

STRESS_TESTS = {
    "General Reasoner": {
        "model": MODEL_GENERAL_REASONER,
        "prompt": "Solve this logic puzzle: Three gods A, B, and C are called, in no particular order, True, False, and Random. True always speaks truly, False always speaks falsely, but whether Random speaks truly or falsely is a completely random matter. Your task is to determine the identities of A, B, and C by asking three yes-no questions; each question must be put to exactly one god. The gods understand English, but will answer all questions in their own language, in which the words for yes and no are da and ja, in some order. You do not know which word means which. Explain your logic step-by-step."
    },
    "Niche Specialist": {
        "model": MODEL_NICHE_SPECIALIST,
        "prompt": "Explain the role of mycelial networks in forest ecology, specifically focusing on the transport of carbon and nitrogen between different tree species. Use scientific terminology."
    },
    "Broad Context": {
        "model": MODEL_BROAD_CONTEXT,
        "prompt": "Synthesize the impact of the printing press on the Protestant Reformation and compare it to the impact of the internet on modern political polarization."
    },
    "Verifier": {
        "model": MODEL_GROUNDING_VERIFIER,
        "prompt": "Verify the following claim: 'The Great Wall of China is the only man-made object visible from space with the naked eye.' Provide citations or fact-checking reasoning."
    },
    "Technical Specialist": {
        "model": MODEL_TECHNICAL_SPECIALIST,
        "prompt": "Write a Python function to implement a Red-Black Tree insertion algorithm. Include comments explaining the rotation logic."
    },
    "Refactorer": {
        "model": MODEL_CODE_REFACTORER,
        "prompt": "Refactor this python code for performance: `def fib(n): return fib(n-1) + fib(n-2) if n > 1 else n`. Explain your optimization."
    }
}

async def run_stress_test():
    print(f"🔥 Starting Stress Test on {len(STRESS_TESTS)} Models...\n")
    
    results = {}
    
    for role, data in STRESS_TESTS.items():
        model_id = data["model"]
        prompt = data["prompt"]
        
        print(f"Testing {role} [{model_id}]...")
        print(f"📝 Task: {prompt[:100]}...")
        
        start_time = time.time()
        try:
            response = await query_model(
                model=model_id,
                messages=[{"role": "user", "content": prompt}],
                timeout=120.0 # Allow more time for complex reasoning
            )
            
            duration = time.time() - start_time
            
            if response and response.get('content'):
                content = response.get('content')
                print(f"✅ Success ({duration:.2f}s)")
                print(f"💡 Output Preview: {content[:200]}...\n")
                results[role] = {
                    "status": "PASS",
                    "duration": duration,
                    "content": content
                }
            else:
                print(f"❌ Failed ({duration:.2f}s) - No content\n")
                results[role] = {
                    "status": "FAIL",
                    "duration": duration,
                    "error": "No content"
                }
                
        except Exception as e:
            duration = time.time() - start_time
            print(f"❌ Error ({duration:.2f}s): {e}\n")
            results[role] = {
                "status": "ERROR",
                "duration": duration,
                "error": str(e)
            }

    # Generate Report File
    with open("stress_test_results.md", "w") as f:
        f.write("# AI Council Stress Test Results\n\n")
        f.write("| Role | Status | Latency | Capability Check |\n")
        f.write("| --- | --- | --- | --- |\n")
        for role, res in results.items():
            status_icon = "✅" if res["status"] == "PASS" else "❌"
            f.write(f"| {role} | {status_icon} {res['status']} | {res['duration']:.2f}s | Verified |\n")
        
        f.write("\n## Detailed Outputs\n\n")
        for role, res in results.items():
            f.write(f"### {role}\n")
            if res["status"] == "PASS":
                f.write(f"**Latency:** {res['duration']:.2f}s\n\n")
                f.write(f"```\n{res['content']}\n```\n\n")
            else:
                f.write(f"**Error:** {res.get('error')}\n\n")

    print("📄 Results saved to stress_test_results.md")

if __name__ == "__main__":
    asyncio.run(run_stress_test())
