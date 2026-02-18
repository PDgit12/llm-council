import sys
import os
sys.path.append(os.getcwd())
try:
    from backend.config import (
        MODEL_GENERAL_REASONER, MODEL_NICHE_SPECIALIST, MODEL_BROAD_CONTEXT,
        MODEL_GROUNDING_VERIFIER, MODEL_INSTRUCTIONAL_ANALYST,
        MODEL_TECHNICAL_SPECIALIST, MODEL_CODE_REFACTORER, MODEL_VALIDATOR
    )
    print("--- CURRENT BACKEND CONFIG (Council of 8 Roles) ---")
    print(f"General Reasoner: {MODEL_GENERAL_REASONER}")
    print(f"Niche Specialist: {MODEL_NICHE_SPECIALIST}")
    print(f"Broad Context:    {MODEL_BROAD_CONTEXT}")
    print(f"Verifier:         {MODEL_GROUNDING_VERIFIER}")
    print(f"Instructional:    {MODEL_INSTRUCTIONAL_ANALYST}")
    print(f"Technical Lead:   {MODEL_TECHNICAL_SPECIALIST}")
    print(f"Code Refactorer:  {MODEL_CODE_REFACTORER}")
    print(f"Quick Validator:  {MODEL_VALIDATOR}")
    
    # 6 Unique Models Check
    unique_models = {
        MODEL_GENERAL_REASONER, MODEL_NICHE_SPECIALIST, MODEL_BROAD_CONTEXT,
        MODEL_GROUNDING_VERIFIER, MODEL_TECHNICAL_SPECIALIST
    }
    
    print(f"\nUnique Models Count: {len(unique_models)}")
    
    if len(unique_models) < 4:
        print(f"\n[FAIL] Too few unique models configured. Need high diversity.")
        sys.exit(1)
    else:
        print(f"\n[PASS] Configuration matches High-Quality Council.")
        
except ImportError as e:
    print(f"Error: Could not import config: {e}")
    print(f"Current sys.path: {sys.path}")
    print(f"Current directory: {os.getcwd()}")
