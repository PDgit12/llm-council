import sys
import os
sys.path.append(os.getcwd())
try:
    from backend.config import COUNCIL_MODELS, CHAIRMAN_MODEL
    print("--- CURRENT BACKEND CONFIG ---")
    print(f"Chairman: {CHAIRMAN_MODEL}")
    print("Council Members:")
    for m in COUNCIL_MODELS:
        print(f" - {m}")
    
    expected = [
        "gemini-3-flash-preview",
        "gemini-2.5-flash",
        "gemini-2.5-flash-lite",
        "gemma-3-27b-it",
    ]
    
    missing = [m for m in expected if m not in COUNCIL_MODELS]
    if missing:
        print(f"\n[FAIL] Missing expected models: {missing}")
        print(f"Current models: {COUNCIL_MODELS}")
        sys.exit(1)
    else:
        print(f"\n[PASS] Configuration matches High-Quality Council.")
        
except ImportError as e:
    print(f"Error: Could not import config: {e}")
    print(f"Current sys.path: {sys.path}")
    print(f"Current directory: {os.getcwd()}")
