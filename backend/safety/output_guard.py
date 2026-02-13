import re
import math
from typing import Dict, Any, List

class OutputSafetyGuard:
    """
    Guardrail for verifying model outputs before they are presented to the user.
    """
    
    # Patterns indicating potential system prompt leakage
    PROMPT_LEAK_PATTERNS = [
        r"core problem deconstructor",
        r"cross-domain analogy explorer",
        r"analogy quality evaluator",
        r"synthesis engine",
        r"system prompt",
        r"initial instruction",
        r"developer mode",
    ]

    # Simple PII patterns (example - phone, email, SSN - replace with robust library in prod)
    PII_PATTERNS = [
        # Email
        r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
        # US Phone number
        r"\(\d{3}\)\s*\d{3}-\d{4}",
        # SSN
        r"\d{3}-\d{2}-\d{4}",
    ]

    def __init__(self):
        self.leak_regex = [re.compile(p, re.IGNORECASE) for p in self.PROMPT_LEAK_PATTERNS]
        self.pii_regex = [re.compile(p) for p in self.PII_PATTERNS]

    def check_output(self, text: str) -> Dict[str, Any]:
        """
        Check if output is safe to show to user.
        """
        # 1. Check for prompt leakage
        for pattern in self.leak_regex:
            if pattern.search(text):
                return {
                    "safe": False,
                    "reason": "Potential system prompt leakage detected.",
                    "category": "System Leak"
                }

        # 2. Check for PII
        for pattern in self.pii_regex:
            if pattern.search(text):
                 return {
                    "safe": False,
                    "reason": "Potential PII detected.",
                    "category": "PII Leak" # Consider redacting instead of blocking entirely
                }

        return {
            "safe": True,
            "reason": None,
            "category": "Safe"
        }
