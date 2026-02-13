import re
from typing import Dict, Any, Optional

class InputSafetyGuard:
    """
    Guardrail for sanitizing and validating user input before it reaches the orchestration layer.
    """
    
    # Simple regex patterns for common jailbreak attempts
    JAILBREAK_PATTERNS = [
        r"ignore all previous instructions",
        r"ignore all instructions",
        r"you are now (?!a\s|the\s|an\s)", # careful with legitimate role setting
        r"system override",
        r"debug mode",
        r"developer mode",
        r"admin mode",
        r"god mode",
        r"unrestricted",
        r"jailbroken",
        r"DAN mode",
    ]
    
    PROHIBITED_TOPICS = [
        r"bomb",
        r"weapon",
        r"how to kill",
        r"generate malware",
        r"exploit vulnerability",
        r"steal credit card",
        r"hack into",
        r"suicide",
        r"self-harm",
    ]

    def __init__(self):
        self.jailbreak_regex = [re.compile(p, re.IGNORECASE) for p in self.JAILBREAK_PATTERNS]
        self.prohibited_regex = [re.compile(p, re.IGNORECASE) for p in self.PROHIBITED_TOPICS]

    def sanitize(self, text: str) -> str:
        """
        Sanitize input by removing known jailbreak triggers.
        """
        sanitized_text = text
        for pattern in self.jailbreak_regex:
            sanitized_text = pattern.sub("[REDACTED_SAFETY]", sanitized_text)
        return sanitized_text

    def check_policy(self, text: str) -> Dict[str, Any]:
        """
        Check if input violates strict content policies.
        Returns:
            {
                "safe": bool,
                "reason": str | None,
                "category": str | None
            }
        """
        for pattern in self.prohibited_regex:
            if pattern.search(text):
                return {
                    "safe": False,
                    "reason": "Content flagged as prohibited.",
                    "category": "Prohibited Content"
                }
        
        # Additional checks can be added here (e.g., PI detection)
        
        return {
            "safe": True,
            "reason": None,
            "category": "Safe"
        }

    def validate(self, text: str) -> Dict[str, Any]:
        """
        Full validation pipeline: Sanitize -> Policy Check.
        """
        sanitized_input = self.sanitize(text)
        policy_result = self.check_policy(sanitized_input)
        
        return {
            "original_input": text,
            "sanitized_input": sanitized_input,
            **policy_result
        }
