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
    
    # Industry-standard PII detection (Simple regex baseline)
    PII_PATTERNS = {
        "Email Address": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
        "Phone Number": r"(\+\d{1,2}\s)?\(?\d{3}\)?[\s.-]\d{3}[\s.-]\d{4}",
        "Credit Card": r"\b(?:\d[ -]*?){13,16}\b",
        "SSN (US)": r"\b\d{3}-\d{2}-\d{4}\b",
    }

    def __init__(self):
        self.jailbreak_regex = [re.compile(p, re.IGNORECASE) for p in self.JAILBREAK_PATTERNS]
        self.prohibited_regex = [re.compile(p, re.IGNORECASE) for p in self.PROHIBITED_TOPICS]
        self.pii_regex = {name: re.compile(p) for name, p in self.PII_PATTERNS.items()}

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
        
        return {
            "safe": True,
            "reason": None,
            "category": "Safe"
        }
        
    def check_pii(self, text: str) -> Dict[str, Any]:
        """
        Detect PII in the text.
        """
        found_pii = []
        for name, regex in self.pii_regex.items():
            if regex.search(text):
                found_pii.append(name)
        
        if found_pii:
            return {
                "safe": False,
                "reason": f"Input contains potential PII: {', '.join(found_pii)}",
                "category": "PII Detected"
            }
        
        return {"safe": True}

    def validate(self, text: str) -> Dict[str, Any]:
        """
        Full validation pipeline: Sanitize -> Policy Check -> PII Check.
        """
        sanitized_input = self.sanitize(text)
        policy_result = self.check_policy(sanitized_input)
        
        if not policy_result["safe"]:
            return {
                "original_input": text,
                "sanitized_input": sanitized_input,
                **policy_result
            }
            
        pii_result = self.check_pii(sanitized_input)
        
        # Merge results, prioritizing the PII failure if it exists
        final_result = pii_result if not pii_result["safe"] else policy_result
        
        return {
            "original_input": text,
            "sanitized_input": sanitized_input,
            **final_result
        }
