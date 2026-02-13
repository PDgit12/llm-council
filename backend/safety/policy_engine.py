from typing import Dict, Any, List

class PolicyEngine:
    """
    Enforces high-level policies and business logic constraints.
    """
    
    def __init__(self):
        # Define allowed/blocked categories or complex rules here
        self.blocked_categories = {"Violence", "Hate Speech", "Illegal Acts", "System Manipulation"}

    def check_input_policy(self, input_check_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate input guard results against policy.
        """
        if not input_check_result.get("safe", False):
            return {
                "allowed": False,
                "reason": input_check_result.get("reason", "Policy violation"),
                "action": "BLOCK"
            }
        
        # Additional complex logic can go here (e.g., user tiered access)
        
        return {
            "allowed": True,
            "reason": None,
            "action": "ALLOW"
        }

    def check_output_policy(self, output_check_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate output guard results against policy.
        """
        if not output_check_result.get("safe", False):
             return {
                "allowed": False,
                "reason": output_check_result.get("reason", "Safety violation in output"),
                "action": "BLOCK_OUTPUT"
            }
            
        return {
            "allowed": True,
            "reason": None,
            "action": "ALLOW"
        }
