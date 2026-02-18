"""Configuration for the Parallels — Cross-Domain Analogy Engine."""

import os
from dotenv import load_dotenv

load_dotenv()

# API keys
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# ── Council Model Tiers (Top Free Models) ──

# Domain 1: General Reasoning & Synthesis (Strongest instruction following)
# Domain 1: General Reasoning & Synthesis
MODELS_GENERAL = [
    "sophos-ai/qwen-2.5-72b-instruct:free",  # Strong free alternative to R1
    "google/gemini-2.0-pro-exp-02-05:free", # Reliable generalist
    "meta-llama/llama-3.3-70b-instruct:free",
    "mistralai/mistral-small-24b-instruct-2501:free",
    "google/gemma-2-9b-it:free",
    "nousresearch/hermes-3-llama-3.1-405b:free"
]

# Domain 2: Technical, Coding & Logic
MODELS_TECHNICAL = [
    "qwen/qwen-2.5-coder-32b-instruct:free", # Excellent free coder
    "google/gemini-2.0-flash-exp:free",
    "meta-llama/llama-3.3-70b-instruct:free",
    "arcee-ai/trinity-large-preview:free",
    "sophos-ai/qwen-2.5-72b-instruct:free"
]

# Domain 3: Research, Context & Specialist Analysis
MODELS_RESEARCH = [
    "microsoft/phi-4:free", # Very fast, good for research/summaries
    "nvidia/llama-3.1-nemotron-70b-instruct:free",
    "google/gemini-2.0-flash-lite-preview-02-05:free",
    "liquid/lfm-2.5-1.2b-thinking:free",
    "arcee-ai/trinity-mini:free"
]

# ── Council Roles (Mapped for default use) ──
MODEL_GENERAL_REASONER = MODELS_GENERAL[0]
MODEL_NICHE_SPECIALIST = MODELS_RESEARCH[0]
MODEL_TECHNICAL_SPECIALIST = MODELS_TECHNICAL[0]
MODEL_GROUNDING_VERIFIER = MODELS_TECHNICAL[2]
MODEL_INSTRUCTIONAL_ANALYST = MODELS_GENERAL[1]
MODEL_VALIDATOR = MODELS_GENERAL[2]

# Groupings for stages
STAGE1_MODELS = [
    MODELS_GENERAL[0], MODELS_GENERAL[1], MODELS_TECHNICAL[0], 
    MODELS_TECHNICAL[1], MODELS_RESEARCH[0]
] 
STAGE2_MODELS = [MODELS_GENERAL[2], MODELS_TECHNICAL[2]]
STAGE3_MODELS = [MODELS_TECHNICAL[0], MODELS_TECHNICAL[2]]
STAGE4_MODELS = [MODELS_RESEARCH[0], MODELS_GENERAL[3]]
STAGE5_MODELS = [MODELS_GENERAL[2], MODELS_GENERAL[4]]
STAGE6_MODEL = MODELS_GENERAL[0] # Qwen 72B for synthesis (stronger than Gemini Lite)
FAST_MODEL = "microsoft/phi-4:free" # Ultra-fast, no thinking, simple queries

# Title generation
TITLE_MODEL = MODELS_RESEARCH[0]

# ── Global Tiers for query_model fallback ──
MODEL_TIER_MAP = {
    **{m: "general" for m in MODELS_GENERAL},
    **{m: "technical" for m in MODELS_TECHNICAL},
    **{m: "research" for m in MODELS_RESEARCH}
}

# Legacy fallback structure
MODEL_FALLBACKS = {
    MODELS_GENERAL[0]: MODELS_GENERAL[1],
    MODELS_TECHNICAL[0]: MODELS_TECHNICAL[1],
    MODELS_RESEARCH[0]: MODELS_RESEARCH[1],
}

# Global timeout for any single model request (seconds)
MODEL_TIMEOUT = 30.0

# OpenRouter API endpoint
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

# Data directory for conversation storage
DATA_DIR = "data/conversations"

# Firebase Cloud Storage
FIREBASE_SERVICE_ACCOUNT = os.getenv("FIREBASE_SERVICE_ACCOUNT")
FIREBASE_PROJECT_ID = os.getenv("FIREBASE_PROJECT_ID")

# ── Security Limits ──
RATE_LIMIT_GLOBAL = 100          # requests per minute per IP
RATE_LIMIT_MESSAGE = 15          # Increased for better UX, still prevents deep automation abuse
RATE_LIMIT_UPLOAD = 20           # file uploads per minute per IP
MAX_MESSAGE_LENGTH = 4000       # characters
MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 5 MB
ALLOWED_UPLOAD_TYPES = {"image/png", "image/jpeg", "image/gif", "image/webp", "application/pdf"}
MAX_CONVERSATIONS = 50          # per user
