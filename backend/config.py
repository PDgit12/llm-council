"""Configuration for the Parallels — Cross-Domain Analogy Engine."""

import os
from dotenv import load_dotenv

load_dotenv()

# API keys
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# ── Council Member Models ──

# 1. General Reasoner & Synthesis Lead (Gemma 3 27B)
MODEL_GENERAL_REASONER = "google/gemma-3-27b-it:free"

# 2. Domain Explorer & Niche Specialist (DeepSeek R1)
MODEL_NICHE_SPECIALIST = "deepseek/deepseek-r1-0528:free"

# 3. Broad Context Research (Llama 3.3 70B - High IQ, may rate limit)
MODEL_BROAD_CONTEXT = "meta-llama/llama-3.3-70b-instruct:free"

# 4. Grounding & Verifier (Trinity Large)
MODEL_GROUNDING_VERIFIER = "arcee-ai/trinity-large-preview:free"

# 5. Instructional Analyst (Gemma 3 12B)
MODEL_INSTRUCTIONAL_ANALYST = "google/gemma-3-12b-it:free"

# 6. Technical Task Specialist (Qwen 3 Coder)
MODEL_TECHNICAL_SPECIALIST = "qwen/qwen3-coder:free"

# 7. Code Refactorer (Nemotron 30B)
MODEL_CODE_REFACTORER = "nvidia/nemotron-3-nano-30b-a3b:free"

# 8. Quick Validator (StepFun Flash)
MODEL_VALIDATOR = "stepfun/step-3.5-flash:free"

# Groupings for stages
STAGE1_MODELS = [MODEL_GENERAL_REASONER, MODEL_NICHE_SPECIALIST, MODEL_BROAD_CONTEXT]
STAGE2_MODELS = [MODEL_GROUNDING_VERIFIER, MODEL_INSTRUCTIONAL_ANALYST]
STAGE3_MODELS = [MODEL_TECHNICAL_SPECIALIST, MODEL_CODE_REFACTORER]
STAGE4_MODELS = [MODEL_BROAD_CONTEXT, MODEL_GENERAL_REASONER]
STAGE5_MODELS = [MODEL_VALIDATOR, MODEL_INSTRUCTIONAL_ANALYST]
STAGE6_MODEL = MODEL_GENERAL_REASONER

# Title generation
TITLE_MODEL = "stepfun/step-3.5-flash:free"

# ── Backup / Fallback Configuration ──
# Map primary models to their backups to handle rate limits or outages.
MODEL_FALLBACKS = {
    MODEL_BROAD_CONTEXT: "google/gemma-3-27b-it:free",  # Llama 3.3 -> Gemma 3 27B
    MODEL_TECHNICAL_SPECIALIST: "nvidia/nemotron-3-nano-30b-a3b:free", # Qwen Coder -> Nemotron
}

# Global timeout for any single model request (seconds)
MODEL_TIMEOUT = 50.0

# OpenRouter API endpoint
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

# Data directory for conversation storage
DATA_DIR = "data/conversations"

# Firebase Cloud Storage
FIREBASE_SERVICE_ACCOUNT = os.getenv("FIREBASE_SERVICE_ACCOUNT")
FIREBASE_PROJECT_ID = os.getenv("FIREBASE_PROJECT_ID")

# ── Security Limits ──
RATE_LIMIT_GLOBAL = 60          # requests per minute per IP
RATE_LIMIT_MESSAGE = 5          # AI message requests per minute per IP
RATE_LIMIT_UPLOAD = 10          # file uploads per minute per IP
MAX_MESSAGE_LENGTH = 4000       # characters
MAX_UPLOAD_SIZE = 5 * 1024 * 1024  # 5 MB
ALLOWED_UPLOAD_TYPES = {"image/png", "image/jpeg", "image/gif", "image/webp"}
MAX_CONVERSATIONS = 50          # per user

# ── Domain Pool ──
DOMAIN_POOL = [
    "Marine Biology", "Jazz Music Theory", "Urban Planning", "Immunology",
    "Mycology (Fungal Networks)", "Beekeeping", "Military Strategy",
    "Theatrical Improv", "Origami Engineering", "Fermentation Science",
    "Earthquake Seismology", "Ant Colony Behavior", "Traditional Weaving",
    "Orbital Mechanics", "Coral Reef Ecosystems", "Game Theory",
    "Renaissance Painting Techniques", "Epidemiology", "River Delta Formation",
    "Competitive Chess Strategy", "Whale Migration Patterns", "Sourdough Baking",
    "Forest Fire Ecology", "Watchmaking", "Neural Plasticity",
    "Supply Chain Logistics", "Parkour Movement", "Volcanic Geology",
    "Circus Acrobatics", "Cryptography", "Tidal Power Engineering",
    "Traditional Japanese Garden Design", "Swarm Robotics", "Wine Terroir",
    "Glacier Formation", "Stand-up Comedy Structure", "Symbiotic Relationships",
    "Bridge Engineering", "Perfumery", "Murmuration (Bird Flocking)",
]
